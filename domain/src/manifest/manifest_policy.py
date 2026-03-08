"""マニフェストのバリデーションポリシー。

マニフェストJSONの構造検証を行う。必須フィールドの欠落、座標範囲の逸脱、
変数名の重複を検出し、ValidationErrorとして報告する。
"""

from __future__ import annotations

from domain.src.manifest.manifest_types import ManifestData
from domain.src.shared.errors import ValidationError


def validate_manifest(data: ManifestData) -> None:
    """マニフェストのバリデーションを実行する。

    Raises:
        ValidationError: バリデーション違反がある場合
    """
    errors: list[str] = []

    _validate_required_fields(data, errors)
    _validate_coordinate_ranges(data, errors)
    _validate_variable_uniqueness(data, errors)

    if errors:
        raise ValidationError(errors)


def _validate_required_fields(data: ManifestData, errors: list[str]) -> None:
    """必須フィールドの存在チェック。"""
    if not data.template_id:
        errors.append("template_id is required")
    if not data.version:
        errors.append("version is required")
    if not data.pages:
        errors.append("at least one page is required")

    for page in data.pages:
        if page.page_index < 0:
            errors.append(f"page_index must be non-negative, got {page.page_index}")

        for field in page.fields:
            if not field.variable_name:
                errors.append(f"variable_name is required for box {field.box_id}")
            if not field.box_id:
                errors.append(
                    f"box_id is required for variable {field.variable_name}"
                )


def _validate_coordinate_ranges(data: ManifestData, errors: list[str]) -> None:
    """フィールド座標が用紙範囲内にあるかチェック。"""
    for page in data.pages:
        paper = page.paper
        for field in page.fields:
            ar = field.absolute_region
            # フィールドの右端が用紙幅を超えていないか
            if ar.x_mm + ar.width_mm > paper.width_mm:
                errors.append(
                    f"field '{field.variable_name}' absolute_region exceeds "
                    f"paper width ({ar.x_mm + ar.width_mm:.1f}mm > {paper.width_mm:.1f}mm)"
                )
            # フィールドの下端が用紙高さを超えていないか
            if ar.y_mm + ar.height_mm > paper.height_mm:
                errors.append(
                    f"field '{field.variable_name}' absolute_region exceeds "
                    f"paper height ({ar.y_mm + ar.height_mm:.1f}mm > {paper.height_mm:.1f}mm)"
                )
            # 座標が負でないか
            if ar.x_mm < 0 or ar.y_mm < 0:
                errors.append(
                    f"field '{field.variable_name}' absolute_region has negative coordinates"
                )


def _validate_variable_uniqueness(data: ManifestData, errors: list[str]) -> None:
    """変数名の一意性チェック（全ページ横断）。"""
    seen: dict[str, int] = {}
    for page in data.pages:
        for field in page.fields:
            name = field.variable_name
            if name in seen:
                errors.append(
                    f"duplicate variable_name '{name}' "
                    f"(pages {seen[name]} and {page.page_index})"
                )
            else:
                seen[name] = page.page_index
