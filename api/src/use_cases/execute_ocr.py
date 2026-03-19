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

from domain.src.manifest.manifest_types import Field, ManifestData, Page
from domain.src.ocr_result.ocr_engine import OcrEngine
from domain.src.ocr_result.ocr_result_policy import build_field_result
from domain.src.ocr_result.ocr_result_types import (
    Confidence,
    FieldResult,
    OcrEngineResult,
    ReadingStatus,
)
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

    全フィールドを先に切り出し、1回のバッチ呼び出しでOCRを実行する。
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

    # 3. 全フィールドを切り出し
    from api.src.infrastructure.cv.box_cropper import BoxCropper

    cropper = BoxCropper(scale_px_per_mm=scale_px_per_mm)
    fields = [f for f in page.fields if isinstance(f, Field)]

    crop_results: list[tuple[int, np.ndarray]] = []
    failed_indices: set[int] = set()

    for i, field_def in enumerate(fields):
        try:
            crop_result = cropper.crop(image, field_def.absolute_region)
            crop_results.append((i, crop_result.box_image))
        except ValueError:
            logger.warning(
                "Field %s: crop failed (region=%s)",
                field_def.variable_name,
                field_def.absolute_region,
            )
            failed_indices.add(i)

    # 4. バッチOCR（1回のサブプロセス呼び出しで全フィールドを処理）
    batch_input = [(img, fields[idx].input_type) for idx, img in crop_results]

    logger.info("OCR batch: %d fields (%d crop failed)", len(batch_input), len(failed_indices))

    try:
        engine_results = ocr_engine.recognize_batch(batch_input)
    except Exception:
        logger.exception("OCR batch failed")
        engine_results = [OcrEngineResult(text="", confidence=0.0) for _ in batch_input]

    # 5. 結果をフィールド順に組み立て
    engine_result_map: dict[int, OcrEngineResult] = {}
    for result_idx, (field_idx, _) in enumerate(crop_results):
        engine_result_map[field_idx] = engine_results[result_idx]

    field_results: list[FieldResult] = []
    for i, field_def in enumerate(fields):
        if i in failed_indices:
            field_results.append(
                FieldResult(
                    variable_name=field_def.variable_name,
                    variable_type=field_def.variable_type,
                    value=None,
                    raw_text="",
                    confidence=Confidence(score=0.0),
                    status=ReadingStatus.FAILED,
                )
            )
            continue

        engine_result = engine_result_map[i]
        field_results.append(
            build_field_result(
                variable_name=field_def.variable_name,
                variable_type=field_def.variable_type,
                engine_result=engine_result,
                input_type=field_def.input_type,
            )
        )

    logger.info("OCR complete: %d fields processed", len(field_results))

    return ExecuteOcrResult(
        template_id=template_id,
        page_index=page_index,
        field_results=field_results,
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
