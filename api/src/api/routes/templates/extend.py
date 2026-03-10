"""POST /api/templates/extend — 拡張マニフェスト生成。"""

from __future__ import annotations

from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse, Response

from api.src.api.routes.templates.serializers import serialize_manifest
from api.src.infrastructure.html_parser import HtmlParseError
from api.src.use_cases.extend_manifest import extend_manifest_from_html

router = APIRouter()


@router.post("/extend", response_model=None)
async def extend_template_endpoint(file: UploadFile) -> dict[str, object] | Response:
    """HTMLテンプレートをパースし、トンボ・ページ識別コード付きマニフェストを返す。"""
    content = await file.read()
    html = content.decode("utf-8")

    try:
        extended = extend_manifest_from_html(html)
    except HtmlParseError as e:
        return JSONResponse(
            status_code=400,
            content={"error": e.message},
        )

    return serialize_manifest(extended)
