"""execute_ocrユースケースのテスト。"""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

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
from domain.src.ocr_result.ocr_result_types import (
    OcrEngineResult,
    ReadingStatus,
)
from domain.src.shared.coordinate import Region

from .execute_ocr import ExecuteOcrError, execute_ocr


def _make_manifest(template_id: str = "test-001", fields: tuple[Field, ...] = ()) -> ManifestData:
    page = Page(
        page_index=0,
        paper=Paper(
            size=PaperSize.A4,
            orientation=Orientation.PORTRAIT,
            width_mm=210.0,
            height_mm=297.0,
            margins=Margins(top=10, right=10, bottom=10, left=10),
        ),
        fields=fields,
    )
    return ManifestData(
        template_id=template_id,
        version="1.0",
        pages=(page,),
    )


def _make_field(
    name: str = "field1",
    x_mm: float = 10.0,
    y_mm: float = 10.0,
    w_mm: float = 40.0,
    h_mm: float = 10.0,
) -> Field:
    return Field(
        variable_id=f"var-{name}",
        variable_name=name,
        variable_type=VariableType.STRING,
        input_type=InputType.PRINTED,
        box_id=f"box-{name}",
        region=Region(x_mm=x_mm, y_mm=y_mm, width_mm=w_mm, height_mm=h_mm),
        absolute_region=Region(x_mm=x_mm, y_mm=y_mm, width_mm=w_mm, height_mm=h_mm),
    )


def _make_image(width: int = 800, height: int = 1100) -> bytes:
    """PNGバイト列を作成する。"""
    import cv2

    img = np.zeros((height, width), dtype=np.uint8)
    _, buf = cv2.imencode(".png", img)
    return buf.tobytes()


class TestExecuteOcr:
    """正常系テスト。"""

    def test_single_field(self) -> None:
        field = _make_field("company_name")
        manifest = _make_manifest(fields=(field,))

        storage = MagicMock()
        storage.load.return_value = _make_image()

        engine = MagicMock()
        engine.recognize_batch.return_value = [
            OcrEngineResult(text="株式会社テスト", confidence=0.92),
        ]

        result = execute_ocr(
            image_id="img-001",
            template_id="test-001",
            page_index=0,
            image_storage=storage,
            manifest_lookup={"test-001": manifest},
            ocr_engine=engine,
            scale_px_per_mm=4.0,
        )

        assert result.template_id == "test-001"
        assert result.page_index == 0
        assert len(result.field_results) == 1
        assert result.field_results[0].variable_name == "company_name"
        assert result.field_results[0].raw_text == "株式会社テスト"
        assert result.field_results[0].status == ReadingStatus.CONFIRMED

        # バッチで1回だけ呼ばれることを確認
        engine.recognize_batch.assert_called_once()
        engine.recognize.assert_not_called()

    def test_multiple_fields(self) -> None:
        fields = (
            _make_field("field_a", x_mm=10, y_mm=10),
            _make_field("field_b", x_mm=10, y_mm=30),
        )
        manifest = _make_manifest(fields=fields)

        storage = MagicMock()
        storage.load.return_value = _make_image()

        engine = MagicMock()
        engine.recognize_batch.return_value = [
            OcrEngineResult(text="AAA", confidence=0.95),
            OcrEngineResult(text="BBB", confidence=0.55),
        ]

        result = execute_ocr(
            image_id="img-001",
            template_id="test-001",
            page_index=0,
            image_storage=storage,
            manifest_lookup={"test-001": manifest},
            ocr_engine=engine,
            scale_px_per_mm=4.0,
        )

        assert len(result.field_results) == 2
        assert result.field_results[0].raw_text == "AAA"
        assert result.field_results[0].status == ReadingStatus.CONFIRMED
        assert result.field_results[1].raw_text == "BBB"
        assert result.field_results[1].status == ReadingStatus.NEEDS_REVIEW

        # バッチで1回だけ呼ばれることを確認
        engine.recognize_batch.assert_called_once()

    def test_ocr_engine_error_returns_failed(self) -> None:
        """OCRエンジンがバッチ全体でエラーの場合、全フィールドFAILED相当。"""
        field = _make_field("broken_field")
        manifest = _make_manifest(fields=(field,))

        storage = MagicMock()
        storage.load.return_value = _make_image()

        engine = MagicMock()
        engine.recognize_batch.side_effect = RuntimeError("engine crash")

        result = execute_ocr(
            image_id="img-001",
            template_id="test-001",
            page_index=0,
            image_storage=storage,
            manifest_lookup={"test-001": manifest},
            ocr_engine=engine,
            scale_px_per_mm=4.0,
        )

        assert len(result.field_results) == 1
        assert result.field_results[0].confidence.score == 0.0

    def test_empty_page_no_fields(self) -> None:
        manifest = _make_manifest(fields=())

        storage = MagicMock()
        storage.load.return_value = _make_image()

        engine = MagicMock()

        result = execute_ocr(
            image_id="img-001",
            template_id="test-001",
            page_index=0,
            image_storage=storage,
            manifest_lookup={"test-001": manifest},
            ocr_engine=engine,
            scale_px_per_mm=4.0,
        )

        assert len(result.field_results) == 0
        engine.recognize_batch.assert_not_called()
        engine.recognize.assert_not_called()


class TestExecuteOcrErrors:
    """エラー系テスト。"""

    def test_manifest_not_found(self) -> None:
        storage = MagicMock()
        engine = MagicMock()

        with pytest.raises(ExecuteOcrError, match="テンプレートが見つかりません"):
            execute_ocr(
                image_id="img-001",
                template_id="unknown",
                page_index=0,
                image_storage=storage,
                manifest_lookup={},
                ocr_engine=engine,
                scale_px_per_mm=4.0,
            )

    def test_page_not_found(self) -> None:
        manifest = _make_manifest()
        storage = MagicMock()
        engine = MagicMock()

        with pytest.raises(ExecuteOcrError, match="ページが見つかりません"):
            execute_ocr(
                image_id="img-001",
                template_id="test-001",
                page_index=99,
                image_storage=storage,
                manifest_lookup={"test-001": manifest},
                ocr_engine=engine,
                scale_px_per_mm=4.0,
            )

    def test_image_not_found(self) -> None:
        manifest = _make_manifest()

        storage = MagicMock()
        storage.load.side_effect = FileNotFoundError("not found")

        engine = MagicMock()

        with pytest.raises(ExecuteOcrError, match="補正済み画像が見つかりません"):
            execute_ocr(
                image_id="img-missing",
                template_id="test-001",
                page_index=0,
                image_storage=storage,
                manifest_lookup={"test-001": manifest},
                ocr_engine=engine,
                scale_px_per_mm=4.0,
            )
