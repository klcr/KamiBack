"""POST /api/scan/ocr エンドポイントのテスト。"""

from __future__ import annotations

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
    VariableType,
)
from domain.src.ocr_result.ocr_engine import OcrEngine
from domain.src.ocr_result.ocr_result_types import OcrEngineResult
from domain.src.scan.image_storage import ImageStorage
from domain.src.shared.coordinate import Region

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
                    variable_name="company_name",
                    variable_type=VariableType.STRING,
                    input_type=InputType.PRINTED,
                    box_id="box-001",
                    region=Region(x_mm=20.0, y_mm=20.0, width_mm=60.0, height_mm=8.0),
                    absolute_region=Region(x_mm=30.0, y_mm=30.0, width_mm=60.0, height_mm=8.0),
                ),
                Field(
                    variable_id="v-002",
                    variable_name="amount",
                    variable_type=VariableType.NUMBER,
                    input_type=InputType.PRINTED,
                    box_id="box-002",
                    region=Region(x_mm=20.0, y_mm=40.0, width_mm=40.0, height_mm=8.0),
                    absolute_region=Region(x_mm=30.0, y_mm=50.0, width_mm=40.0, height_mm=8.0),
                ),
            ),
        ),
    ),
    extended=True,
)


def _make_corrected_image_bytes() -> bytes:
    """補正済み画像のPNGバイト列を作成する。"""
    img = np.zeros((1188, 840), dtype=np.uint8)  # A4 at 4px/mm
    success, buf = cv2.imencode(".png", img)
    assert success
    return buf.tobytes()


class _StubImageStorage(ImageStorage):
    def __init__(self) -> None:
        self._data: dict[str, bytes] = {"img-001": _make_corrected_image_bytes()}

    def save(self, image_data: bytes, image_id: str) -> str:
        self._data[image_id] = image_data
        return f"/tmp/{image_id}.png"

    def load(self, image_id: str) -> bytes:
        if image_id not in self._data:
            raise FileNotFoundError(f"not found: {image_id}")
        return self._data[image_id]

    def delete(self, image_id: str) -> None:
        del self._data[image_id]


class _StubOcrEngine(OcrEngine):
    def __init__(self) -> None:
        self._call_count = 0

    def recognize(self, image: Any, input_type: InputType) -> OcrEngineResult:
        self._call_count += 1
        if self._call_count == 1:
            return OcrEngineResult(text="株式会社テスト", confidence=0.92)
        return OcrEngineResult(text="12345", confidence=0.88)


def _override_deps() -> dict[str, object]:
    return {
        "qr_detector": None,
        "tombo_detector": None,
        "perspective_corrector": None,
        "image_preprocessor": None,
        "image_storage": _StubImageStorage(),
        "manifest_lookup": {"test-001": _SAMPLE_MANIFEST},
        "ocr_engine": _StubOcrEngine(),
    }


class TestOcrEndpoint:
    def setup_method(self) -> None:
        app.dependency_overrides[get_scan_dependencies] = _override_deps
        self.client = TestClient(app)

    def teardown_method(self) -> None:
        app.dependency_overrides.clear()

    def test_success(self) -> None:
        response = self.client.post(
            "/api/scan/ocr",
            json={
                "image_id": "img-001",
                "template_id": "test-001",
                "page_index": 0,
                "scale_px_per_mm": 4.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["templateId"] == "test-001"
        assert data["pageIndex"] == 0
        assert len(data["fieldResults"]) == 2

        fr0 = data["fieldResults"][0]
        assert fr0["variableName"] == "company_name"
        assert fr0["rawText"] == "株式会社テスト"
        assert fr0["confidence"] == 0.92
        assert fr0["status"] == "confirmed"

        fr1 = data["fieldResults"][1]
        assert fr1["variableName"] == "amount"
        assert fr1["rawText"] == "12345"
        assert fr1["value"] == 12345

    def test_manifest_not_found(self) -> None:
        response = self.client.post(
            "/api/scan/ocr",
            json={
                "image_id": "img-001",
                "template_id": "unknown",
                "page_index": 0,
                "scale_px_per_mm": 4.0,
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "テンプレート" in data["error"]

    def test_image_not_found(self) -> None:
        response = self.client.post(
            "/api/scan/ocr",
            json={
                "image_id": "nonexistent",
                "template_id": "test-001",
                "page_index": 0,
                "scale_px_per_mm": 4.0,
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "画像" in data["error"]
