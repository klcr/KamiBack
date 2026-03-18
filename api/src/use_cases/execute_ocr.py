"""OCR実行ユースケース（UC-2: execute_ocr）。

補正済み画像を読み込み、マニフェストの座標定義に基づいてフィールドを切り出し、
OCRエンジンで認識してFieldResultのリストを返す。

ADR-004 DJ-9 に基づく2段階パイプラインの第2段階。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

from domain.src.manifest.manifest_types import ManifestData, Page
from domain.src.ocr_result.ocr_engine import OcrEngine
from domain.src.ocr_result.ocr_result_policy import build_field_result
from domain.src.ocr_result.ocr_result_types import FieldResult, ReadingStatus
from domain.src.scan.image_storage import ImageStorage

logger = logging.getLogger(__name__)


class ExecuteOcrError(Exception):
    """OCR実行処理で発生するエラー。"""

    def __init__(self, message: str, user_action: str) -> None:
        self.message = message
        self.user_action = user_action
        super().__init__(message)


@dataclass(frozen=True)
class ExecuteOcrResult:
    """OCR実行結果。"""

    template_id: str
    page_index: int
    field_results: list[FieldResult]


def execute_ocr(
    image_id: str,
    template_id: str,
    page_index: int,
    *,
    image_storage: ImageStorage,
    manifest_lookup: dict[str, ManifestData],
    ocr_engine: OcrEngine,
    scale_px_per_mm: float,
) -> ExecuteOcrResult:
    """補正済み画像に対してOCRを実行する。

    Args:
        image_id: 補正済み画像のID（correct_imageの出力）
        template_id: テンプレートID
        page_index: ページインデックス
        image_storage: 画像ストレージ
        manifest_lookup: テンプレートID → ManifestData のマッピング
        ocr_engine: OCRエンジン
        scale_px_per_mm: mm→ピクセル変換係数（correct_imageの出力）

    Returns:
        OCR実行結果（全フィールドの認識結果）

    Raises:
        ExecuteOcrError: 画像未発見、マニフェスト未発見等
    """
    # 1. マニフェスト取得
    manifest = manifest_lookup.get(template_id)
    if manifest is None:
        raise ExecuteOcrError(
            message=f"テンプレートが見つかりません: {template_id}",
            user_action="登録済みのテンプレートで印刷した帳票を使用してください",
        )

    page = _find_page(manifest, page_index)
    if page is None:
        raise ExecuteOcrError(
            message=f"ページが見つかりません: page_index={page_index}",
            user_action="正しいページを撮影してください",
        )

    # 2. 補正済み画像を読み込み
    try:
        image_data = image_storage.load(image_id)
    except FileNotFoundError as e:
        raise ExecuteOcrError(
            message=f"補正済み画像が見つかりません: {image_id}",
            user_action="もう一度撮影してください",
        ) from e

    image = _decode_image(image_data)

    # 3. BoxCropperで各フィールドを切り出してOCR実行
    from api.src.infrastructure.cv.box_cropper import BoxCropper

    cropper = BoxCropper(scale_px_per_mm=scale_px_per_mm)
    field_results: list[FieldResult] = []

    total_fields = len(page.fields)
    for i, field_def in enumerate(page.fields, 1):
        from domain.src.manifest.manifest_types import Field

        assert isinstance(field_def, Field)
        logger.info("OCR field %d/%d: %s", i, total_fields, field_def.variable_name)
        field_result = _process_field(
            field_def=field_def,
            image=image,
            cropper=cropper,
            ocr_engine=ocr_engine,
        )
        field_results.append(field_result)
        logger.info(
            "OCR field %d/%d done: %s (status=%s)",
            i,
            total_fields,
            field_def.variable_name,
            field_result.status.value,
        )

    return ExecuteOcrResult(
        template_id=template_id,
        page_index=page_index,
        field_results=field_results,
    )


def _process_field(
    *,
    field_def: object,
    image: np.ndarray,
    cropper: object,
    ocr_engine: OcrEngine,
) -> FieldResult:
    """1フィールドの切出し→OCR→FieldResult構築。"""
    from api.src.infrastructure.cv.box_cropper import BoxCropper
    from domain.src.manifest.manifest_types import Field

    assert isinstance(field_def, Field)
    assert isinstance(cropper, BoxCropper)

    try:
        crop_result = cropper.crop(image, field_def.absolute_region)
    except ValueError:
        logger.warning(
            "Field %s: crop failed (region=%s)",
            field_def.variable_name,
            field_def.absolute_region,
        )
        from domain.src.ocr_result.ocr_result_types import Confidence

        return FieldResult(
            variable_name=field_def.variable_name,
            variable_type=field_def.variable_type,
            value=None,
            raw_text="",
            confidence=Confidence(score=0.0),
            status=ReadingStatus.FAILED,
        )

    try:
        engine_result = ocr_engine.recognize(crop_result.box_image, field_def.input_type)
    except Exception:
        logger.exception("Field %s: OCR engine error", field_def.variable_name)
        from domain.src.ocr_result.ocr_result_types import Confidence

        return FieldResult(
            variable_name=field_def.variable_name,
            variable_type=field_def.variable_type,
            value=None,
            raw_text="",
            confidence=Confidence(score=0.0),
            status=ReadingStatus.FAILED,
        )

    return build_field_result(
        variable_name=field_def.variable_name,
        variable_type=field_def.variable_type,
        engine_result=engine_result,
        input_type=field_def.input_type,
    )


def _find_page(manifest: ManifestData, page_index: int) -> Page | None:
    """マニフェストからページインデックスで検索する。"""
    for page in manifest.pages:
        if page.page_index == page_index:
            return page
    return None


def _decode_image(image_data: bytes) -> np.ndarray:
    """バイト列をOpenCV画像に変換する。"""
    import cv2
    import numpy as np

    arr = np.frombuffer(image_data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ExecuteOcrError(
            message="補正済み画像のデコードに失敗しました",
            user_action="もう一度撮影してください",
        )
    return img
