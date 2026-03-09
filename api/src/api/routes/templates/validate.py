"""POST /api/templates/validate — テンプレート検証。"""

from __future__ import annotations

from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse, Response

from api.src.infrastructure.html_parser import HtmlParseError
from api.src.use_cases.validate_template import validate_template

router = APIRouter()

_ERROR_TRANSLATIONS: dict[str, str] = {
    "template_id is required": "テンプレートIDが設定されていません",
    "version is required": "バージョンが設定されていません",
    "at least one page is required": "少なくとも1ページ必要です",
}


def _translate_error(error: str) -> str:
    """エラーメッセージを日本語に変換する。"""
    for key, ja in _ERROR_TRANSLATIONS.items():
        if key in error:
            return ja
    if "exceeds paper width" in error:
        return f"用紙幅を超えています: {error}"
    if "exceeds paper height" in error:
        return f"用紙高さを超えています: {error}"
    if "duplicate variable_name" in error:
        return f"変数名が重複しています: {error}"
    if "not in template HTML" in error:
        return f"テンプレートHTML内に見つかりません: {error}"
    if "not in manifest" in error:
        return f"マニフェストに定義されていません: {error}"
    if "does not exist in template HTML" in error:
        return f"テンプレートHTML内にボックスが存在しません: {error}"
    return error


@router.post("/validate")
async def validate_template_endpoint(file: UploadFile) -> dict[str, object] | Response:
    """HTMLテンプレートのマニフェストとDOMの整合性を検証する。"""
    content = await file.read()
    html = content.decode("utf-8")

    try:
        result = validate_template(html)
    except HtmlParseError as e:
        return JSONResponse(
            status_code=400,
            content={"valid": False, "errors": [e.message]},
        )

    translated_errors = [_translate_error(e) for e in result.errors]

    return {
        "valid": result.valid,
        "errors": translated_errors,
        "variableCount": result.variable_count,
        "pageCount": result.page_count,
    }
