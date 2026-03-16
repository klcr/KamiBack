"""POST /api/scan/correct — 撮影画像の補正。

撮影画像を受け取り、QR検出→トンボ検出→射影変換→前処理→保存を行う。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import JSONResponse, Response

from api.src.api.routes.scan.dependencies import get_scan_dependencies
from api.src.use_cases.correct_image import CorrectImageError, correct_image

router = APIRouter()


@router.post("/correct", response_model=None)
async def correct_image_endpoint(
    file: UploadFile,
    deps: dict[str, object] = Depends(get_scan_dependencies),  # noqa: B008
) -> dict[str, object] | Response:
    """撮影画像を補正して保存する。"""
    image_bytes = await file.read()

    try:
        result = correct_image(
            image_bytes,
            qr_detector=deps["qr_detector"],  # type: ignore[arg-type]
            tombo_detector=deps["tombo_detector"],  # type: ignore[arg-type]
            perspective_corrector=deps["perspective_corrector"],  # type: ignore[arg-type]
            image_preprocessor=deps["image_preprocessor"],  # type: ignore[arg-type]
            image_storage=deps["image_storage"],  # type: ignore[arg-type]
            manifest_lookup=deps["manifest_lookup"],  # type: ignore[arg-type]
        )
    except CorrectImageError as e:
        return JSONResponse(
            status_code=400,
            content={
                "error": e.message,
                "userAction": e.user_action,
            },
        )

    return {
        "imageId": result.image_id,
        "imagePath": result.image_path,
        "templateId": result.template_id,
        "pageIndex": result.page_index,
        "tombo": {
            "detectionCount": result.detection_count,
            "hasEstimation": result.has_estimation,
            "skewDegree": result.skew_degree,
            "aspectRatioError": result.aspect_ratio_error,
        },
        "scalePxPerMm": result.scale_px_per_mm,
    }
