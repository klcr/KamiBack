"""テンプレート検証ユースケース。

HTMLテンプレート内のマニフェストとDOMの整合性を検証する。
"""

from __future__ import annotations

from dataclasses import dataclass

from api.src.use_cases.parse_template import parse_template
from domain.src.manifest.manifest_policy import validate_manifest
from domain.src.template.template_policy import validate_template_manifest_consistency


@dataclass(frozen=True)
class ValidateTemplateResult:
    """検証結果。"""

    valid: bool
    errors: list[str]
    variable_count: int
    page_count: int


def validate_template(html: str) -> ValidateTemplateResult:
    """HTMLテンプレートのマニフェストとDOMの整合性を検証する。"""
    result = parse_template(html)
    errors: list[str] = []

    try:
        validate_manifest(result.manifest)
    except Exception as e:
        if hasattr(e, "errors"):
            errors.extend(e.errors)
        else:
            errors.append(str(e))

    try:
        validate_template_manifest_consistency(result.template, result.manifest)
    except Exception as e:
        if hasattr(e, "errors"):
            errors.extend(e.errors)
        else:
            errors.append(str(e))

    variable_count = sum(len(p.fields) for p in result.manifest.pages)

    return ValidateTemplateResult(
        valid=len(errors) == 0,
        errors=errors,
        variable_count=variable_count,
        page_count=len(result.manifest.pages),
    )
