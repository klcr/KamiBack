"""QrDetectorインターフェースのユニットテスト。"""

from __future__ import annotations

import pytest

from domain.src.scan.qr_detector import QrDetectionResult, QrDetector


class TestQrDetectionResult:
    def test_detected(self) -> None:
        r = QrDetectionResult(
            detected=True,
            template_id="invoice-001",
            page_index=0,
            raw_content="invoice-001/0",
        )
        assert r.detected
        assert r.template_id == "invoice-001"
        assert r.page_index == 0

    def test_not_detected(self) -> None:
        r = QrDetectionResult(detected=False)
        assert not r.detected
        assert r.template_id is None
        assert r.page_index is None

    def test_frozen(self) -> None:
        r = QrDetectionResult(detected=True, template_id="t", page_index=0)
        with pytest.raises(AttributeError):
            r.detected = False  # type: ignore[misc]


class TestQrDetectorInterface:
    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            QrDetector()  # type: ignore[abstract]
