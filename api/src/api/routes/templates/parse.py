"""POST /api/templates/parse — HTMLテンプレートパース。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse

from api.src.api.routes.templates.serializers import (
    serialize_manifest,
    serialize_template_metadata,
    serialize_variables,
)
from api.src.infrastructure.html_parser import HtmlParseError
from api.src.use_cases.parse_template import parse_template

router = APIRouter()


@router.post("/parse")
async def parse_template_endpoint(file: UploadFile) -> Any:
    """HTMLテンプレートをパースし、マニフェストとメタデータを返す。"""
    content = await file.read()
    html = content.decode("utf-8")

    try:
        result = parse_template(html)
    except HtmlParseError as e:
        return JSONResponse(
            status_code=400,
            content={"error": e.message},
        )

    return {
        "manifest": serialize_manifest(result.manifest),
        "template": serialize_template_metadata(result.template),
        "variables": serialize_variables(result.manifest),
    }
