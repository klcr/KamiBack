"""HTMLテンプレートパーサー。

BeautifulSoupを使用してHTMLテンプレートからマニフェストJSONとDOM要素を抽出する。
"""

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup, Tag

from domain.src.manifest.manifest_types import (
    Field,
    InputType,
    ManifestData,
    Margins,
    Orientation,
    Page,
    Paper,
    PaperSize,
    VariableType,
)
from domain.src.shared.coordinate import Region
from domain.src.template.template_types import (
    Box,
    BoxRole,
    Line,
    PageTemplate,
    TemplateMetadata,
)


class HtmlParseError(Exception):
    """HTMLパース時のエラー。"""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def parse_manifest_from_html(html: str) -> ManifestData:
    """HTMLテンプレートの<script id="template-manifest">からマニフェストJSONを抽出する。"""
    soup = BeautifulSoup(html, "html.parser")
    script_tag = soup.find("script", id="template-manifest")
    if script_tag is None or not isinstance(script_tag, Tag):
        raise HtmlParseError('HTMLに <script id="template-manifest"> が見つかりません')

    text = script_tag.string
    if not text:
        raise HtmlParseError('<script id="template-manifest"> の内容が空です')

    try:
        raw = json.loads(text)
    except json.JSONDecodeError as e:
        raise HtmlParseError(f"マニフェストJSONのパースに失敗しました: {e}") from e

    return _build_manifest_data(raw)


def parse_template_metadata(html: str) -> TemplateMetadata:
    """HTMLテンプレートのDOM要素をパースしてTemplateMetadataを生成する。"""
    soup = BeautifulSoup(html, "html.parser")
    page_divs: list[Tag] = [t for t in soup.find_all("div", class_="page") if isinstance(t, Tag)]
    if not page_divs:
        page_divs = [soup]

    pages: list[PageTemplate] = []
    for i, page_div in enumerate(page_divs):
        if not isinstance(page_div, Tag):
            continue
        boxes = _parse_boxes(page_div)
        lines = _parse_lines(page_div)
        pages.append(PageTemplate(page_index=i, boxes=tuple(boxes), lines=tuple(lines)))

    return TemplateMetadata(
        source_html=html,
        page_count=len(pages),
        pages=tuple(pages),
    )


def _build_manifest_data(raw: dict[str, Any]) -> ManifestData:
    """生のJSONオブジェクトからManifestDataを構築する。"""
    pages: list[Page] = []
    for i, raw_page in enumerate(raw.get("pages", [])):
        raw_paper = raw_page.get("paper", {})
        paper = Paper(
            size=PaperSize(raw_paper.get("size", "A4")),
            orientation=Orientation(raw_paper.get("orientation", "portrait")),
            width_mm=float(raw_paper.get("widthMm", 210.0)),
            height_mm=float(raw_paper.get("heightMm", 297.0)),
            margins=Margins(
                top=float(raw_paper.get("margins", {}).get("top", 0)),
                right=float(raw_paper.get("margins", {}).get("right", 0)),
                bottom=float(raw_paper.get("margins", {}).get("bottom", 0)),
                left=float(raw_paper.get("margins", {}).get("left", 0)),
            ),
        )
        fields: list[Field] = []
        for raw_field in raw_page.get("fields", []):
            raw_region = raw_field.get("region", {})
            raw_abs = raw_field.get("absoluteRegion", {})
            fields.append(
                Field(
                    variable_id=raw_field.get("variableId", ""),
                    variable_name=raw_field.get("variableName", ""),
                    variable_type=VariableType(raw_field.get("variableType", "string")),
                    input_type=InputType(raw_field.get("inputType", "printed")),
                    box_id=raw_field.get("boxId", ""),
                    region=Region(
                        x_mm=float(raw_region.get("x", 0)),
                        y_mm=float(raw_region.get("y", 0)),
                        width_mm=float(raw_region.get("width", 1)),
                        height_mm=float(raw_region.get("height", 1)),
                    ),
                    absolute_region=Region(
                        x_mm=float(raw_abs.get("x", 0)),
                        y_mm=float(raw_abs.get("y", 0)),
                        width_mm=float(raw_abs.get("width", 1)),
                        height_mm=float(raw_abs.get("height", 1)),
                    ),
                )
            )
        pages.append(
            Page(
                page_index=raw_page.get("pageIndex", i),
                paper=paper,
                fields=tuple(fields),
            )
        )
    return ManifestData(
        template_id=raw.get("templateId", ""),
        version=raw.get("version", ""),
        pages=tuple(pages),
        interface=raw.get("interface", ""),
    )


def _parse_boxes(container: Tag) -> list[Box]:
    """コンテナからボックス要素をパースする。"""
    boxes: list[Box] = []
    for el in container.find_all("div", class_="box"):
        if not isinstance(el, Tag):
            continue
        box_id = el.get("id", "") or el.get("data-box-id", "")
        role_str = el.get("data-role", "decoration")
        role = BoxRole(role_str) if role_str in ("field", "label", "decoration") else BoxRole.DECORATION

        region = _parse_region_from_style(el)
        variable_name = el.get("data-variable") or None
        data_type = el.get("data-type") or None

        boxes.append(
            Box(
                box_id=str(box_id),
                role=role,
                region_mm=region,
                text_content=el.get_text(strip=True),
                variable_name=str(variable_name) if variable_name else None,
                data_type=str(data_type) if data_type else None,
            )
        )
    return boxes


def _parse_lines(container: Tag) -> list[Line]:
    """コンテナからライン要素をパースする。"""
    lines: list[Line] = []
    for el in container.find_all("div", class_="line"):
        if not isinstance(el, Tag):
            continue
        line_id = el.get("id", "") or el.get("data-line-id", "")
        lines.append(
            Line(
                line_id=str(line_id),
                x1_mm=_parse_mm(el.get("data-x1", "0")),
                y1_mm=_parse_mm(el.get("data-y1", "0")),
                x2_mm=_parse_mm(el.get("data-x2", "0")),
                y2_mm=_parse_mm(el.get("data-y2", "0")),
            )
        )
    return lines


def _parse_region_from_style(el: Tag) -> Region:
    """要素のdata属性またはstyleからmm座標のRegionを取得する。"""
    x = _parse_mm(el.get("data-x", "0"))
    y = _parse_mm(el.get("data-y", "0"))
    w = _parse_mm(el.get("data-width", "1"))
    h = _parse_mm(el.get("data-height", "1"))
    return Region(x_mm=x, y_mm=y, width_mm=w, height_mm=h)


def _parse_mm(value: Any) -> float:
    """文字列やリストからmm値をパースする。"""
    if isinstance(value, list):
        value = value[0] if value else "0"
    try:
        return float(str(value).replace("mm", "").strip())
    except (ValueError, TypeError):
        return 0.0
