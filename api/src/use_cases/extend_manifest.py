"""拡張マニフェスト生成ユースケース。

マニフェストにトンボ座標とページ識別コードを追記し、
DOM上の{{変数名}}パターンからフィールドを自動検出してマニフェストに追加する。
"""

from __future__ import annotations

from dataclasses import replace

from api.src.use_cases.parse_template import parse_template
from domain.src.manifest.manifest import Manifest
from domain.src.manifest.manifest_types import (
    Field,
    InputType,
    ManifestData,
    Page,
    VariableType,
)
from domain.src.shared.coordinate import Region
from domain.src.template.template_types import Box, PageTemplate


def extend_manifest_from_html(
    html: str,
    tombo_offset_mm: float = 5.0,
    tombo_radius_mm: float = 3.0,
) -> ManifestData:
    """HTMLテンプレートをパースし、拡張マニフェストを返す。"""
    result = parse_template(html)
    manifest_with_vars = _merge_dom_variables(result.manifest, result.template.pages)
    manifest_entity = Manifest(data=manifest_with_vars)
    extended = manifest_entity.extend(
        tombo_offset_mm=tombo_offset_mm,
        tombo_radius_mm=tombo_radius_mm,
    )
    assert extended.data is not None
    return extended.data


def _merge_dom_variables(
    manifest: ManifestData,
    template_pages: tuple[PageTemplate, ...],
) -> ManifestData:
    """DOM上の{{変数名}}パターンで発見した変数をマニフェストのfieldsに追加する。

    既にマニフェストにfieldsが定義されているページはスキップする。
    """
    updated_pages: list[Page] = []

    for page in manifest.pages:
        # 既にフィールドが定義されているページはそのまま
        if page.fields:
            updated_pages.append(page)
            continue

        # 対応するテンプレートページからフィールドボックスを検出
        tmpl_page = _find_template_page(template_pages, page.page_index)
        if tmpl_page is None:
            updated_pages.append(page)
            continue

        fields = _extract_fields_from_boxes(tmpl_page.field_boxes, page)
        if fields:
            updated_pages.append(replace(page, fields=tuple(fields)))
        else:
            updated_pages.append(page)

    return replace(manifest, pages=tuple(updated_pages))


def _find_template_page(
    template_pages: tuple[PageTemplate, ...],
    page_index: int,
) -> PageTemplate | None:
    """テンプレートページをpage_indexで検索する。"""
    for tp in template_pages:
        if tp.page_index == page_index:
            return tp
    return None


def _extract_fields_from_boxes(boxes: list[Box], page: Page) -> list[Field]:
    """フィールドボックスからFieldを生成する。"""
    fields: list[Field] = []
    for box in boxes:
        if box.variable_name is None:
            continue
        # 印刷可能領域内座標 → 絶対座標（実効マージン分を加算）
        # センタリング有効時はマージンが均等化されるため effective_margins を使用
        effective = page.paper.effective_margins
        absolute_region = Region(
            x_mm=box.region_mm.x_mm + effective.left,
            y_mm=box.region_mm.y_mm + effective.top,
            width_mm=box.region_mm.width_mm,
            height_mm=box.region_mm.height_mm,
        )
        fields.append(
            Field(
                variable_id=box.box_id,
                variable_name=box.variable_name,
                variable_type=VariableType.STRING,
                input_type=InputType.PRINTED,
                box_id=box.box_id,
                region=box.region_mm,
                absolute_region=absolute_region,
            )
        )
    return fields
