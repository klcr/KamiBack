"""POST /api/scan/ocr — OCR実行。

補正済み画像に対してOCRを実行し、フィールドごとの認識結果を返す。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from api.src.api.routes.scan.dependencies import get_scan_dependencies
from api.src.use_cases.execute_ocr import ExecuteOcrError, execute_ocr

router = APIRouter()


class OcrRequest(BaseModel):
    """OCR実行リクエスト。"""

    image_id: str
    template_id: str
    page_index: int
    scale_px_per_mm: float


@router.post("/ocr", response_model=None)
def execute_ocr_endpoint(
    body: OcrRequest,
    deps: dict[str, object] = Depends(get_scan_dependencies),  # noqa: B008
) -> dict[str, object] | Response:
    """補正済み画像に対してOCRを実行する。"""
    try:
        result = execute_ocr(
            image_id=body.image_id,
            template_id=body.template_id,
            page_index=body.page_index,
            image_storage=deps["image_storage"],  # type: ignore[arg-type]
            manifest_lookup=deps["manifest_lookup"],  # type: ignore[arg-type]
            ocr_engine=deps["ocr_engine"],  # type: ignore[arg-type]
            scale_px_per_mm=body.scale_px_per_mm,
        )
    except ExecuteOcrError as e:
        return JSONResponse(
            status_code=400,
            content={
                "error": e.message,
                "userAction": e.user_action,
            },
        )

    return {
        "templateId": result.template_id,
        "pageIndex": result.page_index,
        "fieldResults": [
            {
                "variableName": fr.variable_name,
                "variableType": fr.variable_type.value,
                "value": fr.value,
                "rawText": fr.raw_text,
                "confidence": fr.confidence.score,
                "status": fr.status.value,
            }
            for fr in result.field_results
        ],
    }
