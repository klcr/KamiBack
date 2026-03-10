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


# --- section.sheet 形式 + data-*-mm 属性 + {{変数}} パターンのテスト ---

_SHEET_HTML = """<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>test-a4-light</title></head>
<body>
<section class="sheet"
  data-page-index="0"
  data-template-id="test-a4-light"
  data-width-mm="210"
  data-height-mm="297"
  style="position: relative; width: 184.6mm; height: 269.06mm;">
  <div class="box"
       data-box-id="p0-box-1"
       data-role="label"
       data-x-mm="0" data-y-mm="0"
       data-w-mm="145.53" data-h-mm="10.05"
       style="position: absolute;">請　求　書</div>
  <div class="box"
       data-box-id="p0-box-2"
       data-role="label"
       data-x-mm="0" data-y-mm="15.08"
       data-w-mm="28.91" data-h-mm="6.74"
       style="position: absolute;">請求日:</div>
  <div class="box"
       data-box-id="p0-box-3"
       data-role="label"
       data-x-mm="28.91" data-y-mm="15.08"
       data-w-mm="42.98" data-h-mm="6.74"
       style="position: absolute;">{{invoiceDate}}</div>
  <div class="box"
       data-box-id="p0-box-5"
       data-role="label"
       data-x-mm="135.48" data-y-mm="15.08"
       data-w-mm="10.05" data-h-mm="6.74"
       style="position: absolute;">{{invoiceNumber}}</div>
  <div class="line"
       data-line-id="p0-line-1"
       data-x1-mm="0" data-y1-mm="10.05"
       data-x2-mm="145.53" data-y2-mm="10.05"></div>
</section>
<script type="application/json" id="template-manifest">
{
  "templateId": "test-a4-light",
  "version": "1.0.0",
  "pages": [{"pageIndex": 0, "paper": {
    "size": "A4", "orientation": "portrait",
    "widthMm": 210, "heightMm": 297,
    "margins": {"top": 15.24, "right": 12.7, "bottom": 12.7, "left": 12.7}
  }, "fields": []}],
  "interface": "interface TemplateData {}"
}
</script>
</body>
</html>"""


class TestSheetFormatParsing:
    """section.sheet 形式のHTMLテンプレートのパーステスト。"""

    def test_detects_section_sheet_as_page(self) -> None:
        result = parse_template_metadata(_SHEET_HTML)
        assert result.page_count == 1

    def test_parses_data_mm_attributes(self) -> None:
        result = parse_template_metadata(_SHEET_HTML)
        box3 = [b for b in result.pages[0].boxes if b.box_id == "p0-box-3"][0]
        assert box3.region_mm.x_mm == pytest.approx(28.91)
        assert box3.region_mm.y_mm == pytest.approx(15.08)
        assert box3.region_mm.width_mm == pytest.approx(42.98)
        assert box3.region_mm.height_mm == pytest.approx(6.74)

    def test_extracts_mustache_variable_name(self) -> None:
        result = parse_template_metadata(_SHEET_HTML)
        box3 = [b for b in result.pages[0].boxes if b.box_id == "p0-box-3"][0]
        assert box3.variable_name == "invoiceDate"

    def test_mustache_box_becomes_field_role(self) -> None:
        result = parse_template_metadata(_SHEET_HTML)
        box3 = [b for b in result.pages[0].boxes if b.box_id == "p0-box-3"][0]
        from domain.src.template.template_types import BoxRole
        assert box3.role == BoxRole.FIELD

    def test_all_mustache_variables_detected(self) -> None:
        result = parse_template_metadata(_SHEET_HTML)
        field_boxes = result.pages[0].field_boxes
        var_names = {b.variable_name for b in field_boxes}
        assert var_names == {"invoiceDate", "invoiceNumber"}

    def test_label_without_mustache_stays_label(self) -> None:
        result = parse_template_metadata(_SHEET_HTML)
        title_box = [b for b in result.pages[0].boxes if b.box_id == "p0-box-1"][0]
        from domain.src.template.template_types import BoxRole
        assert title_box.role == BoxRole.LABEL
        assert title_box.variable_name is None

    def test_parses_line_with_mm_attributes(self) -> None:
        result = parse_template_metadata(_SHEET_HTML)
        lines = result.pages[0].lines
        assert len(lines) == 1
        assert lines[0].x1_mm == pytest.approx(0.0)
        assert lines[0].x2_mm == pytest.approx(145.53)

    def test_page_index_from_data_attribute(self) -> None:
        result = parse_template_metadata(_SHEET_HTML)
        assert result.pages[0].page_index == 0
