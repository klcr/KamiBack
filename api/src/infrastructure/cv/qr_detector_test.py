"""PyzbarQrDetectorのユニットテスト。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from api.src.infrastructure.cv.qr_detector import (
    PyzbarQrDetector,
    _parse_qr_content,
)


class TestParseQrContent:
    def test_valid_format(self) -> None:
        result = _parse_qr_content("invoice-001/0")
        assert result == ("invoice-001", 0)

    def test_valid_with_nested_slashes(self) -> None:
        result = _parse_qr_content("org/template-001/2")
        assert result == ("org/template-001", 2)

    def test_no_slash(self) -> None:
        assert _parse_qr_content("no-slash") is None

    def test_empty_template_id(self) -> None:
        assert _parse_qr_content("/0") is None

    def test_non_numeric_page_index(self) -> None:
        assert _parse_qr_content("template/abc") is None

    def test_negative_page_index(self) -> None:
        assert _parse_qr_content("template/-1") is None

    def test_empty_string(self) -> None:
        assert _parse_qr_content("") is None


class TestPyzbarQrDetector:
    def _make_gray_image(self) -> np.ndarray:
        return np.zeros((100, 100), dtype=np.uint8)

    def _make_color_image(self) -> np.ndarray:
        return np.zeros((100, 100, 3), dtype=np.uint8)

    def _make_decoded(self, data: str, qr_type: str = "QRCODE") -> MagicMock:
        decoded = MagicMock()
        decoded.data = data.encode("utf-8")
        decoded.type = qr_type
        return decoded

    @patch("api.src.infrastructure.cv.qr_detector.pyzbar.decode")
    def test_detect_valid_qr(self, mock_decode: MagicMock) -> None:
        mock_decode.return_value = [self._make_decoded("invoice-001/0")]
        detector = PyzbarQrDetector()
        result = detector.detect(self._make_gray_image())
        assert result.detected
        assert result.template_id == "invoice-001"
        assert result.page_index == 0
        assert result.raw_content == "invoice-001/0"

    @patch("api.src.infrastructure.cv.qr_detector.pyzbar.decode")
    def test_detect_no_qr(self, mock_decode: MagicMock) -> None:
        mock_decode.return_value = []
        detector = PyzbarQrDetector()
        result = detector.detect(self._make_gray_image())
        assert not result.detected
        assert result.template_id is None

    @patch("api.src.infrastructure.cv.qr_detector.pyzbar.decode")
    def test_detect_invalid_content(self, mock_decode: MagicMock) -> None:
        mock_decode.return_value = [self._make_decoded("invalid-no-slash")]
        detector = PyzbarQrDetector()
        result = detector.detect(self._make_gray_image())
        assert not result.detected
        assert result.raw_content == "invalid-no-slash"

    @patch("api.src.infrastructure.cv.qr_detector.pyzbar.decode")
    def test_detect_skips_non_qr(self, mock_decode: MagicMock) -> None:
        barcode = self._make_decoded("some-barcode", qr_type="EAN13")
        qr = self._make_decoded("template/1")
        mock_decode.return_value = [barcode, qr]
        detector = PyzbarQrDetector()
        result = detector.detect(self._make_gray_image())
        assert result.detected
        assert result.template_id == "template"
        assert result.page_index == 1

    @patch("api.src.infrastructure.cv.qr_detector.pyzbar.decode")
    def test_detect_color_image(self, mock_decode: MagicMock) -> None:
        mock_decode.return_value = [self._make_decoded("tmpl/0")]
        detector = PyzbarQrDetector()
        result = detector.detect(self._make_color_image())
        assert result.detected
        assert result.template_id == "tmpl"
