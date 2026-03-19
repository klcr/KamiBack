"""POST /api/scan/correct エンドポイントのテスト。"""

from __future__ import annotations

from io import BytesIO
from typing import Any

import cv2
import numpy as np
from fastapi.testclient import TestClient

from api.src.api import app
from api.src.api.routes.scan.dependencies import get_scan_dependencies
from domain.src.manifest.manifest_types import (
    Field,
    InputType,
    ManifestData,
    Margins,
    Orientation,
    Page,
    Paper,
    PaperSize,
    RegistrationMarks,
    TomboShape,
    VariableType,
)
from domain.src.ocr_result.image_preprocessor import ImagePreprocessor
from domain.src.ocr_result.perspective_corrector import (
    PerspectiveCorrectionResult,
    PerspectiveCorrector,
)
from domain.src.ocr_result.tombo_detector import TomboDetectionResult, TomboDetector
from domain.src.scan.image_storage import ImageStorage
from domain.src.scan.qr_detector import QrDetectionResult, QrDetector
from domain.src.shared.coordinate import Point, Region

_FOUR_POINTS = (
    Point(x_mm=10.0, y_mm=10.0),
    Point(x_mm=200.0, y_mm=10.0),
    Point(x_mm=10.0, y_mm=287.0),
    Point(x_mm=200.0, y_mm=287.0),
)

_SAMPLE_MANIFEST = ManifestData(
    template_id="test-001",
    version="1.0",
    pages=(
        Page(
            page_index=0,
            paper=Paper(
                size=PaperSize.A4,
                orientation=Orientation.PORTRAIT,
                width_mm=210.0,
                height_mm=297.0,
                margins=Margins(top=10.0, right=10.0, bottom=10.0, left=10.0),
            ),
            fields=(
                Field(
                    variable_id="v-001",
                    variable_name="name",
                    variable_type=VariableType.STRING,
                    input_type=InputType.PRINTED,
                    box_id="box-001",
                    region=Region(x_mm=20.0, y_mm=20.0, width_mm=80.0, height_mm=8.0),
                    absolute_region=Region(x_mm=30.0, y_mm=30.0, width_mm=80.0, height_mm=8.0),
                ),
            ),
            registration_marks=RegistrationMarks(
                shape=TomboShape.CIRCLE_CROSS,
                radius_mm=3.0,
                positions=_FOUR_POINTS,
            ),
        ),
    ),
    extended=True,
)


class _StubQrDetector(QrDetector):
    def __init__(self, detected: bool = True) -> None:
        self._detected = detected

    def detect(self, image: Any) -> QrDetectionResult:
        if self._detected:
            return QrDetectionResult(detected=True, template_id="test-001", page_index=0, raw_content="test-001/0")
        return QrDetectionResult(detected=False)


class _StubTomboDetector(TomboDetector):
    def detect(self, image: Any) -> TomboDetectionResult:
        return TomboDetectionResult(detected_points=_FOUR_POINTS, detection_count=4)


class _StubPerspectiveCorrector(PerspectiveCorrector):
    def correct(
        self,
        image: Any,
        src_points: tuple[Point, ...],
        dst_points_mm: tuple[Point, ...],
        output_size_mm: tuple[float, float],
    ) -> PerspectiveCorrectionResult:
        w, h = 2100, 2970
        return PerspectiveCorrectionResult(
            corrected_image=np.zeros((h, w, 3), dtype=np.uint8),
            scale_px_per_mm=10.0,
            output_width_px=w,
            output_height_px=h,
        )


class _StubImagePreprocessor(ImagePreprocessor):
    def preprocess(self, image: Any) -> Any:
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image


class _StubImageStorage(ImageStorage):
    def __init__(self) -> None:
        self.saved: dict[str, bytes] = {}

    def save(self, image_data: bytes, image_id: str) -> str:
        self.saved[image_id] = image_data
        return f"/tmp/{image_id}.png"

    def load(self, image_id: str) -> bytes:
        return self.saved[image_id]

    def delete(self, image_id: str) -> None:
        del self.saved[image_id]


def _make_test_image_bytes() -> bytes:
    img = np.zeros((300, 210, 3), dtype=np.uint8)
    success, buf = cv2.imencode(".png", img)
    assert success
    return buf.tobytes()


def _override_deps(qr_detected: bool = True) -> dict[str, object]:
    return {
        "qr_detector": _StubQrDetector(detected=qr_detected),
        "tombo_detector": _StubTomboDetector(),
        "perspective_corrector": _StubPerspectiveCorrector(),
        "image_preprocessor": _StubImagePreprocessor(),
        "image_storage": _StubImageStorage(),
        "manifest_lookup": {"test-001": _SAMPLE_MANIFEST},
    }


class TestCorrectEndpoint:
    def setup_method(self) -> None:
        app.dependency_overrides[get_scan_dependencies] = _override_deps
        self.client = TestClient(app)

    def teardown_method(self) -> None:
        app.dependency_overrides.clear()

    def test_success(self) -> None:
        image_bytes = _make_test_image_bytes()
        response = self.client.post(
            "/api/scan/correct",
            files={"file": ("photo.png", BytesIO(image_bytes), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["templateId"] == "test-001"
        assert data["pageIndex"] == 0
        assert data["tombo"]["detectionCount"] == 4
        assert data["tombo"]["hasEstimation"] is False
        assert data["scalePxPerMm"] == 10.0
        assert "imageId" in data

    def test_qr_detection_failure_returns_400(self) -> None:
        app.dependency_overrides[get_scan_dependencies] = lambda: _override_deps(qr_detected=False)

        image_bytes = _make_test_image_bytes()
        response = self.client.post(
            "/api/scan/correct",
            files={"file": ("photo.png", BytesIO(image_bytes), "image/png")},
        )
        assert response.status_code == 400
        data = response.json()
        assert "QRコード" in data["error"]
        assert "userAction" in data

    def test_qr_fallback_with_template_override(self) -> None:
        """QR検出失敗でもtemplate_id/page_index指定で成功する。"""
        app.dependency_overrides[get_scan_dependencies] = lambda: _override_deps(qr_detected=False)

        image_bytes = _make_test_image_bytes()
        response = self.client.post(
            "/api/scan/correct?template_id=test-001&page_index=0",
            files={"file": ("photo.png", BytesIO(image_bytes), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["templateId"] == "test-001"
        assert data["pageIndex"] == 0

    def test_invalid_image_returns_400(self) -> None:
        response = self.client.post(
            "/api/scan/correct",
            files={"file": ("photo.png", BytesIO(b"not-an-image"), "image/png")},
        )
        assert response.status_code == 400
        data = response.json()
        assert "デコード" in data["error"]
