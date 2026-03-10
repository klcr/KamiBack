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
    _validate_centering_consistency(template, manifest, errors)
    _validate_paper_consistency(template, manifest, errors)

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


def _validate_centering_consistency(
    template: TemplateMetadata,
    manifest: ManifestData,
    errors: list[str],
) -> None:
    """centering の DOM属性とマニフェストの一致を確認。"""
    for t_page, m_page in zip(template.pages, manifest.pages, strict=False):
        if t_page.horizontal_centered != m_page.paper.centering.horizontal:
            errors.append(
                f"page {t_page.page_index}: horizontal centering mismatch "
                f"(HTML: {t_page.horizontal_centered}, manifest: {m_page.paper.centering.horizontal})"
            )
        if t_page.vertical_centered != m_page.paper.centering.vertical:
            errors.append(
                f"page {t_page.page_index}: vertical centering mismatch "
                f"(HTML: {t_page.vertical_centered}, manifest: {m_page.paper.centering.vertical})"
            )


def _validate_paper_consistency(
    template: TemplateMetadata,
    manifest: ManifestData,
    errors: list[str],
) -> None:
    """用紙属性の DOM属性とマニフェストの一致を確認。

    DOM属性が空文字列/0.0 の場合は未設定とみなしスキップする。
    """
    for t_page, m_page in zip(template.pages, manifest.pages, strict=False):
        paper = m_page.paper
        idx = t_page.page_index

        if t_page.paper_size and t_page.paper_size != paper.size.value:
            errors.append(
                f"page {idx}: paper size mismatch "
                f"(HTML: {t_page.paper_size}, manifest: {paper.size.value})"
            )
        if t_page.orientation and t_page.orientation != paper.orientation.value:
            errors.append(
                f"page {idx}: orientation mismatch "
                f"(HTML: {t_page.orientation}, manifest: {paper.orientation.value})"
            )
        if t_page.width_mm and t_page.width_mm != paper.width_mm:
            errors.append(
                f"page {idx}: width mismatch "
                f"(HTML: {t_page.width_mm}, manifest: {paper.width_mm})"
            )
        if t_page.height_mm and t_page.height_mm != paper.height_mm:
            errors.append(
                f"page {idx}: height mismatch "
                f"(HTML: {t_page.height_mm}, manifest: {paper.height_mm})"
            )
        if t_page.margin_top_mm and t_page.margin_top_mm != paper.margins.top:
            errors.append(
                f"page {idx}: margin-top mismatch "
                f"(HTML: {t_page.margin_top_mm}, manifest: {paper.margins.top})"
            )
        if t_page.margin_right_mm and t_page.margin_right_mm != paper.margins.right:
            errors.append(
                f"page {idx}: margin-right mismatch "
                f"(HTML: {t_page.margin_right_mm}, manifest: {paper.margins.right})"
            )
        if t_page.margin_bottom_mm and t_page.margin_bottom_mm != paper.margins.bottom:
            errors.append(
                f"page {idx}: margin-bottom mismatch "
                f"(HTML: {t_page.margin_bottom_mm}, manifest: {paper.margins.bottom})"
            )
        if t_page.margin_left_mm and t_page.margin_left_mm != paper.margins.left:
            errors.append(
                f"page {idx}: margin-left mismatch "
                f"(HTML: {t_page.margin_left_mm}, manifest: {paper.margins.left})"
            )
