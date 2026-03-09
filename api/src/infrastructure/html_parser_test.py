"""HTMLパーサーの統合テスト。"""

from __future__ import annotations

import pytest

from api.src.infrastructure.html_parser import (
    HtmlParseError,
    parse_manifest_from_html,
    parse_template_metadata,
)

_SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head><title>Test Invoice</title></head>
<body>
<script id="template-manifest" type="application/json">
{
  "templateId": "invoice-001",
  "version": "1.0",
  "pages": [{
    "pageIndex": 0,
    "paper": {
      "size": "A4",
      "orientation": "portrait",
      "widthMm": 210,
      "heightMm": 297,
      "margins": {"top": 15, "right": 10, "bottom": 15, "left": 10}
    },
    "fields": [
      {
        "variableId": "v-001",
        "variableName": "company_name",
        "variableType": "string",
        "inputType": "printed",
        "boxId": "box-001",
        "region": {"x": 20, "y": 20, "width": 80, "height": 8},
        "absoluteRegion": {"x": 30, "y": 35, "width": 80, "height": 8}
      },
      {
        "variableId": "v-002",
        "variableName": "total_amount",
        "variableType": "number",
        "inputType": "printed",
        "boxId": "box-002",
        "region": {"x": 120, "y": 100, "width": 60, "height": 10},
        "absoluteRegion": {"x": 130, "y": 115, "width": 60, "height": 10}
      }
    ]
  }]
}
</script>
<div class="page">
  <div class="box" id="box-001" data-role="field" data-variable="company_name"
       data-x="20" data-y="20" data-width="80" data-height="8">{{company_name}}</div>
  <div class="box" id="box-002" data-role="field" data-variable="total_amount"
       data-x="120" data-y="100" data-width="60" data-height="10">{{total_amount}}</div>
  <div class="box" id="label-001" data-role="label"
       data-x="20" data-y="12" data-width="40" data-height="6">会社名</div>
  <div class="line" id="line-001" data-x1="10" data-y1="50" data-x2="200" data-y2="50"></div>
</div>
</body>
</html>"""


class TestParseManifestFromHtml:
    def test_parses_template_id(self) -> None:
        result = parse_manifest_from_html(_SAMPLE_HTML)
        assert result.template_id == "invoice-001"

    def test_parses_version(self) -> None:
        result = parse_manifest_from_html(_SAMPLE_HTML)
        assert result.version == "1.0"

    def test_parses_pages(self) -> None:
        result = parse_manifest_from_html(_SAMPLE_HTML)
        assert len(result.pages) == 1

    def test_parses_fields(self) -> None:
        result = parse_manifest_from_html(_SAMPLE_HTML)
        fields = result.pages[0].fields
        assert len(fields) == 2
        assert fields[0].variable_name == "company_name"
        assert fields[1].variable_name == "total_amount"

    def test_parses_paper(self) -> None:
        result = parse_manifest_from_html(_SAMPLE_HTML)
        paper = result.pages[0].paper
        assert paper.width_mm == 210.0
        assert paper.height_mm == 297.0

    def test_missing_script_tag(self) -> None:
        html = "<html><body>No manifest here</body></html>"
        with pytest.raises(HtmlParseError, match="template-manifest"):
            parse_manifest_from_html(html)

    def test_empty_script_tag(self) -> None:
        html = '<html><body><script id="template-manifest"></script></body></html>'
        with pytest.raises(HtmlParseError, match="空です"):
            parse_manifest_from_html(html)

    def test_invalid_json(self) -> None:
        html = '<html><body><script id="template-manifest">not json</script></body></html>'
        with pytest.raises(HtmlParseError, match="パースに失敗"):
            parse_manifest_from_html(html)


class TestParseTemplateMetadata:
    def test_parses_page_count(self) -> None:
        result = parse_template_metadata(_SAMPLE_HTML)
        assert result.page_count == 1

    def test_parses_boxes(self) -> None:
        result = parse_template_metadata(_SAMPLE_HTML)
        boxes = result.pages[0].boxes
        assert len(boxes) == 3  # 2 fields + 1 label

    def test_parses_field_boxes(self) -> None:
        result = parse_template_metadata(_SAMPLE_HTML)
        field_boxes = result.pages[0].field_boxes
        assert len(field_boxes) == 2
        assert field_boxes[0].variable_name == "company_name"

    def test_parses_label_boxes(self) -> None:
        result = parse_template_metadata(_SAMPLE_HTML)
        labels = result.pages[0].label_boxes
        assert len(labels) == 1
        assert labels[0].text_content == "会社名"

    def test_parses_lines(self) -> None:
        result = parse_template_metadata(_SAMPLE_HTML)
        lines = result.pages[0].lines
        assert len(lines) == 1
        assert lines[0].x1_mm == 10.0
        assert lines[0].x2_mm == 200.0

    def test_parses_box_region(self) -> None:
        result = parse_template_metadata(_SAMPLE_HTML)
        box = result.pages[0].boxes[0]
        assert box.region_mm.x_mm == 20.0
        assert box.region_mm.width_mm == 80.0
