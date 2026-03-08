"""テンプレートとマニフェストの整合性チェックポリシー。

HTMLテンプレートのDOM構造とマニフェストJSONの間に不整合がないかを検証する。
"""

from __future__ import annotations

from domain.src.manifest.manifest_types import ManifestData
from domain.src.shared.errors import ValidationError
from domain.src.template.template_types import TemplateMetadata


def validate_template_manifest_consistency(
    template: TemplateMetadata,
    manifest: ManifestData,
) -> None:
    """テンプレートとマニフェストの整合性を検証する。

    Raises:
        ValidationError: 整合性違反がある場合
    """
    errors: list[str] = []

    _validate_page_count(template, manifest, errors)
    _validate_variable_names(template, manifest, errors)
    _validate_box_ids(template, manifest, errors)

    if errors:
        raise ValidationError(errors)


def _validate_page_count(
    template: TemplateMetadata,
    manifest: ManifestData,
    errors: list[str],
) -> None:
    """ページ数の一致を確認。"""
    if template.page_count != len(manifest.pages):
        errors.append(
            f"page count mismatch: template has {template.page_count} pages, manifest has {len(manifest.pages)} pages"
        )


def _validate_variable_names(
    template: TemplateMetadata,
    manifest: ManifestData,
    errors: list[str],
) -> None:
    """変数名の一致を確認。

    マニフェストで定義されている変数名が、テンプレートのフィールドボックスに
    存在するかを確認する。
    """
    template_vars: set[str] = set()
    for page in template.pages:
        for box in page.field_boxes:
            if box.variable_name:
                template_vars.add(box.variable_name)

    manifest_vars: set[str] = set()
    for manifest_page in manifest.pages:
        for field in manifest_page.fields:
            manifest_vars.add(field.variable_name)

    # マニフェストにあるがテンプレートにない変数
    only_in_manifest = manifest_vars - template_vars
    for var in sorted(only_in_manifest):
        errors.append(f"variable '{var}' is in manifest but not in template HTML")

    # テンプレートにあるがマニフェストにない変数
    only_in_template = template_vars - manifest_vars
    for var in sorted(only_in_template):
        errors.append(f"variable '{var}' is in template HTML but not in manifest")


def _validate_box_ids(
    template: TemplateMetadata,
    manifest: ManifestData,
    errors: list[str],
) -> None:
    """box_idの一致を確認。"""
    template_box_ids: set[str] = set()
    for page in template.pages:
        for box in page.boxes:
            template_box_ids.add(box.box_id)

    for manifest_page in manifest.pages:
        for field in manifest_page.fields:
            if field.box_id not in template_box_ids:
                errors.append(
                    f"manifest field '{field.variable_name}' references "
                    f"box_id '{field.box_id}' which does not exist in template HTML"
                )
