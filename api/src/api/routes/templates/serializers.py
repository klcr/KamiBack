"""テンプレート関連のレスポンスシリアライザ。"""

from __future__ import annotations

from typing import Any

from domain.src.manifest.manifest_types import Field, ManifestData, Page
from domain.src.template.template_types import TemplateMetadata


def serialize_manifest(data: ManifestData) -> dict[str, Any]:
    """ManifestDataをAPIレスポンス形式にシリアライズする。"""
    return {
        "templateId": data.template_id,
        "version": data.version,
        "interface": data.interface,
        "extended": data.extended,
        "pages": [_serialize_page(p) for p in data.pages],
    }


def serialize_variables(data: ManifestData) -> list[dict[str, Any]]:
    """マニフェストから変数一覧をシリアライズする。"""
    variables: list[dict[str, Any]] = []
    for page in data.pages:
        for field in page.fields:
            variables.append(_serialize_variable(field))
    return variables


def serialize_template_metadata(meta: TemplateMetadata) -> dict[str, Any]:
    """TemplateMetadataをAPIレスポンス形式にシリアライズする。"""
    return {
        "pageCount": meta.page_count,
        "pages": [
            {
                "pageIndex": p.page_index,
                "boxes": [
                    {
                        "boxId": b.box_id,
                        "role": b.role.value,
                        "regionMm": {
                            "x": b.region_mm.x_mm,
                            "y": b.region_mm.y_mm,
                            "width": b.region_mm.width_mm,
                            "height": b.region_mm.height_mm,
                        },
                        "textContent": b.text_content,
                        "variableName": b.variable_name,
                        "dataType": b.data_type,
                    }
                    for b in p.boxes
                ],
                "lines": [
                    {
                        "lineId": li.line_id,
                        "x1Mm": li.x1_mm,
                        "y1Mm": li.y1_mm,
                        "x2Mm": li.x2_mm,
                        "y2Mm": li.y2_mm,
                    }
                    for li in p.lines
                ],
            }
            for p in meta.pages
        ],
    }


def _serialize_page(page: Page) -> dict[str, Any]:
    """1ページ分をシリアライズ。"""
    result: dict[str, Any] = {
        "pageIndex": page.page_index,
        "paper": {
            "size": page.paper.size.value,
            "orientation": page.paper.orientation.value,
            "widthMm": page.paper.width_mm,
            "heightMm": page.paper.height_mm,
            "margins": {
                "top": page.paper.margins.top,
                "right": page.paper.margins.right,
                "bottom": page.paper.margins.bottom,
                "left": page.paper.margins.left,
            },
        },
        "fields": [_serialize_variable(f) for f in page.fields],
    }
    if page.registration_marks is not None:
        result["registrationMarks"] = {
            "shape": page.registration_marks.shape.value,
            "radiusMm": page.registration_marks.radius_mm,
            "positions": [{"x": p.x_mm, "y": p.y_mm} for p in page.registration_marks.positions],
        }
    if page.page_identifier is not None:
        result["pageIdentifier"] = {
            "type": page.page_identifier.type,
            "content": page.page_identifier.content,
            "position": {"x": page.page_identifier.position.x_mm, "y": page.page_identifier.position.y_mm},
            "sizeMm": page.page_identifier.size_mm,
        }
    return result


def _serialize_variable(field: Field) -> dict[str, Any]:
    """フィールドを変数情報としてシリアライズ。"""
    return {
        "variableId": field.variable_id,
        "variableName": field.variable_name,
        "variableType": field.variable_type.value,
        "inputType": field.input_type.value,
        "boxId": field.box_id,
        "region": {
            "x": field.region.x_mm,
            "y": field.region.y_mm,
            "width": field.region.width_mm,
            "height": field.region.height_mm,
        },
        "absoluteRegion": {
            "x": field.absolute_region.x_mm,
            "y": field.absolute_region.y_mm,
            "width": field.absolute_region.width_mm,
            "height": field.absolute_region.height_mm,
        },
    }
