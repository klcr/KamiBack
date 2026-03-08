"""パースユースケースのテスト。"""

from __future__ import annotations

import pytest

from api.src.infrastructure.html_parser import HtmlParseError
from api.src.use_cases.parse_template import parse_template

_VALID_HTML = """<!DOCTYPE html>
<html><body>
<script id="template-manifest" type="application/json">
{
  "templateId": "test-001",
  "version": "1.0",
  "pages": [{
    "pageIndex": 0,
    "paper": {"size": "A4", "orientation": "portrait", "widthMm": 210, "heightMm": 297,
              "margins": {"top": 10, "right": 10, "bottom": 10, "left": 10}},
    "fields": [{
      "variableId": "v-001", "variableName": "name", "variableType": "string",
      "inputType": "printed", "boxId": "box-001",
      "region": {"x": 20, "y": 20, "width": 80, "height": 8},
      "absoluteRegion": {"x": 30, "y": 30, "width": 80, "height": 8}
    }]
  }]
}
</script>
<div class="page">
  <div class="box" id="box-001" data-role="field" data-variable="name"
       data-x="20" data-y="20" data-width="80" data-height="8">{{name}}</div>
</div>
</body></html>"""


class TestParseTemplate:
    def test_normal_parse(self) -> None:
        result = parse_template(_VALID_HTML)
        assert result.manifest.template_id == "test-001"
        assert result.template.page_count == 1
        assert len(result.manifest.pages[0].fields) == 1

    def test_empty_html_raises(self) -> None:
        with pytest.raises(HtmlParseError, match="空"):
            parse_template("")

    def test_missing_manifest_raises(self) -> None:
        html = "<html><body><p>No manifest</p></body></html>"
        with pytest.raises(HtmlParseError, match="template-manifest"):
            parse_template(html)

    def test_returns_template_metadata(self) -> None:
        result = parse_template(_VALID_HTML)
        boxes = result.template.pages[0].boxes
        assert len(boxes) == 1
        assert boxes[0].variable_name == "name"
