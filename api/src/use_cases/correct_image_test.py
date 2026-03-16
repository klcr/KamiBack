"""correct_image ユースケースのテスト。"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np
import pytest

from api.src.use_cases.correct_image import CorrectImageError, correct_image
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

# --- Stub implementations ---


class StubQrDetector(QrDetector):
    def __init__(self, result: QrDetectionResult) -> None:
        self._result = result

    def detect(self, image: Any) -> QrDetectionResult:
        return self._result


class StubTomboDetector(TomboDetector):
    def __init__(self, result: TomboDetectionResult) -> None:
        self._result = result

    def detect(self, image: Any) -> TomboDetectionResult:
        return self._result


class StubPerspectiveCorrector(PerspectiveCorrector):
    def __init__(self, scale: float = 10.0) -> None:
        self._scale = scale

    def correct(
        self,
        image: Any,
        src_points: tuple[Point, ...],
        dst_points_mm: tuple[Point, ...],
        output_size_mm: tuple[float, float],
    ) -> PerspectiveCorrectionResult:
        w = int(output_size_mm[0] * self._scale)
        h = int(output_size_mm[1] * self._scale)
        corrected = np.zeros((h, w, 3), dtype=np.uint8)
        return PerspectiveCorrectionResult(
            corrected_image=corrected,
            scale_px_per_mm=self._scale,
            output_width_px=w,
            output_height_px=h,
        )


class StubImagePreprocessor(ImagePreprocessor):
    def preprocess(self, image: Any) -> Any:
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image


class StubImageStorage(ImageStorage):
    def __init__(self) -> None:
        self.saved: dict[str, bytes] = {}

    def save(self, image_data: bytes, image_id: str) -> str:
        self.saved[image_id] = image_data
        return f"/tmp/{image_id}.png"

    def load(self, image_id: str) -> bytes:
        if image_id not in self.saved:
            raise FileNotFoundError(f"not found: {image_id}")
        return self.saved[image_id]

    def delete(self, image_id: str) -> None:
        if image_id not in self.saved:
            raise FileNotFoundError(f"not found: {image_id}")
        del self.saved[image_id]


# --- Fixtures ---

_FOUR_POINTS = (
    Point(x_mm=10.0, y_mm=10.0),
    Point(x_mm=200.0, y_mm=10.0),
    Point(x_mm=10.0, y_mm=287.0),
    Point(x_mm=200.0, y_mm=287.0),
)

_TOMBO_4_DETECTED = TomboDetectionResult(
    detected_points=_FOUR_POINTS,
    detection_count=4,
)

_TOMBO_3_DETECTED = TomboDetectionResult(
    detected_points=_FOUR_POINTS[:3],
    detection_count=3,
    estimated_points=_FOUR_POINTS,
    skew_degree=1.5,
    aspect_ratio_error=2.0,
)

_TOMBO_INSUFFICIENT = TomboDetectionResult(
    detected_points=_FOUR_POINTS[:2],
    detection_count=2,
)

_QR_SUCCESS = QrDetectionResult(
    detected=True,
    template_id="test-001",
    page_index=0,
    raw_content="test-001/0",
)

_QR_FAILED = QrDetectionResult(detected=False)

_SAMPLE_PAGE = Page(
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
)

_SAMPLE_MANIFEST = ManifestData(
    template_id="test-001",
    version="1.0",
    pages=(_SAMPLE_PAGE,),
    extended=True,
)


def _make_test_image() -> bytes:
    """テスト用の画像バイト列を生成する。"""
    img = np.zeros((300, 210, 3), dtype=np.uint8)
    success, buf = cv2.imencode(".png", img)
    assert success
    return buf.tobytes()


# --- Tests ---


class TestCorrectImage:
    def test_success_4_points(self) -> None:
        storage = StubImageStorage()
        result = correct_image(
            _make_test_image(),
            qr_detector=StubQrDetector(_QR_SUCCESS),
            tombo_detector=StubTomboDetector(_TOMBO_4_DETECTED),
            perspective_corrector=StubPerspectiveCorrector(),
            image_preprocessor=StubImagePreprocessor(),
            image_storage=storage,
            manifest_lookup={"test-001": _SAMPLE_MANIFEST},
        )

        assert result.template_id == "test-001"
        assert result.page_index == 0
        assert result.detection_count == 4
        assert result.has_estimation is False
        assert result.skew_degree is None
        assert result.scale_px_per_mm == 10.0
        assert result.image_id in storage.saved

    def test_success_3_points_with_estimation(self) -> None:
        storage = StubImageStorage()
        result = correct_image(
            _make_test_image(),
            qr_detector=StubQrDetector(_QR_SUCCESS),
            tombo_detector=StubTomboDetector(_TOMBO_3_DETECTED),
            perspective_corrector=StubPerspectiveCorrector(),
            image_preprocessor=StubImagePreprocessor(),
            image_storage=storage,
            manifest_lookup={"test-001": _SAMPLE_MANIFEST},
        )

        assert result.detection_count == 3
        assert result.has_estimation is True
        assert result.skew_degree == 1.5
        assert result.aspect_ratio_error == 2.0

    def test_qr_detection_failed(self) -> None:
        with pytest.raises(CorrectImageError, match="QRコード"):
            correct_image(
                _make_test_image(),
                qr_detector=StubQrDetector(_QR_FAILED),
                tombo_detector=StubTomboDetector(_TOMBO_4_DETECTED),
                perspective_corrector=StubPerspectiveCorrector(),
                image_preprocessor=StubImagePreprocessor(),
                image_storage=StubImageStorage(),
                manifest_lookup={"test-001": _SAMPLE_MANIFEST},
            )

    def test_manifest_not_found(self) -> None:
        with pytest.raises(CorrectImageError, match="テンプレートが見つかりません"):
            correct_image(
                _make_test_image(),
                qr_detector=StubQrDetector(_QR_SUCCESS),
                tombo_detector=StubTomboDetector(_TOMBO_4_DETECTED),
                perspective_corrector=StubPerspectiveCorrector(),
                image_preprocessor=StubImagePreprocessor(),
                image_storage=StubImageStorage(),
                manifest_lookup={},  # empty
            )

    def test_page_not_found(self) -> None:
        qr_page1 = QrDetectionResult(
            detected=True,
            template_id="test-001",
            page_index=99,  # non-existent
            raw_content="test-001/99",
        )
        with pytest.raises(CorrectImageError, match="ページが見つかりません"):
            correct_image(
                _make_test_image(),
                qr_detector=StubQrDetector(qr_page1),
                tombo_detector=StubTomboDetector(_TOMBO_4_DETECTED),
                perspective_corrector=StubPerspectiveCorrector(),
                image_preprocessor=StubImagePreprocessor(),
                image_storage=StubImageStorage(),
                manifest_lookup={"test-001": _SAMPLE_MANIFEST},
            )

    def test_tombo_insufficient(self) -> None:
        with pytest.raises(CorrectImageError, match="トンボの検出数が不足"):
            correct_image(
                _make_test_image(),
                qr_detector=StubQrDetector(_QR_SUCCESS),
                tombo_detector=StubTomboDetector(_TOMBO_INSUFFICIENT),
                perspective_corrector=StubPerspectiveCorrector(),
                image_preprocessor=StubImagePreprocessor(),
                image_storage=StubImageStorage(),
                manifest_lookup={"test-001": _SAMPLE_MANIFEST},
            )

    def test_invalid_image_bytes(self) -> None:
        with pytest.raises(CorrectImageError, match="デコード"):
            correct_image(
                b"not-an-image",
                qr_detector=StubQrDetector(_QR_SUCCESS),
                tombo_detector=StubTomboDetector(_TOMBO_4_DETECTED),
                perspective_corrector=StubPerspectiveCorrector(),
                image_preprocessor=StubImagePreprocessor(),
                image_storage=StubImageStorage(),
                manifest_lookup={"test-001": _SAMPLE_MANIFEST},
            )

    def test_fallback_dst_points_when_no_registration_marks(self) -> None:
        """registration_marks がない場合は用紙四隅をフォールバックする。"""
        page_no_marks = Page(
            page_index=0,
            paper=Paper(
                size=PaperSize.A4,
                orientation=Orientation.PORTRAIT,
                width_mm=210.0,
                height_mm=297.0,
                margins=Margins(top=10.0, right=10.0, bottom=10.0, left=10.0),
            ),
            fields=(),
        )
        manifest_no_marks = ManifestData(
            template_id="test-001",
            version="1.0",
            pages=(page_no_marks,),
        )
        storage = StubImageStorage()
        result = correct_image(
            _make_test_image(),
            qr_detector=StubQrDetector(_QR_SUCCESS),
            tombo_detector=StubTomboDetector(_TOMBO_4_DETECTED),
            perspective_corrector=StubPerspectiveCorrector(),
            image_preprocessor=StubImagePreprocessor(),
            image_storage=storage,
            manifest_lookup={"test-001": manifest_no_marks},
        )
        assert result.template_id == "test-001"
        assert result.image_id in storage.saved

    def test_image_saved_to_storage(self) -> None:
        """補正画像がストレージに保存されることを確認する。"""
        storage = StubImageStorage()
        result = correct_image(
            _make_test_image(),
            qr_detector=StubQrDetector(_QR_SUCCESS),
            tombo_detector=StubTomboDetector(_TOMBO_4_DETECTED),
            perspective_corrector=StubPerspectiveCorrector(),
            image_preprocessor=StubImagePreprocessor(),
            image_storage=storage,
            manifest_lookup={"test-001": _SAMPLE_MANIFEST},
        )
        # 保存されたデータがPNG画像であることを確認
        saved_data = storage.saved[result.image_id]
        assert saved_data[:4] == b"\x89PNG"
