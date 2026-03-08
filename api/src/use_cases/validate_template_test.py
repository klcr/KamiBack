"""テンプレート検証ユースケースのテスト。"""

from __future__ import annotations

import pytest

from api.src.infrastructure.html_parser import HtmlParseError
from api.src.use_cases.validate_template import validate_template


def _make_html(
    template_id: str = "test-001",
    variable_name: str = "name",
    box_id: str = "box-001",
    dom_variable: str = "name",
    dom_box_id: str = "box-001",
) -> str:
    return f"""<!DOCTYPE html>
<html><body>
<script id="template-manifest" type="application/json">
{{
  "templateId": "{template_id}",
  "version": "1.0",
  "pages": [{{
    "pageIndex": 0,
    "paper": {{"size": "A4", "orientation": "portrait", "widthMm": 210, "heightMm": 297,
              "margins": {{"top": 10, "right": 10, "bottom": 10, "left": 10}}}},
    "fields": [{{
      "variableId": "v-001", "variableName": "{variable_name}", "variableType": "string",
      "inputType": "printed", "boxId": "{box_id}",
      "region": {{"x": 20, "y": 20, "width": 80, "height": 8}},
      "absoluteRegion": {{"x": 30, "y": 30, "width": 80, "height": 8}}
    }}]
  }}]
}}
</script>
<div class="page">
  <div class="box" id="{dom_box_id}" data-role="field" data-variable="{dom_variable}"
       data-x="20" data-y="20" data-width="80" data-height="8">{{{{{dom_variable}}}}}</div>
</div>
</body></html>"""


class TestValidateTemplate:
    def test_valid_template(self) -> None:
        result = validate_template(_make_html())
        assert result.valid is True
        assert result.errors == []
        assert result.variable_count == 1
        assert result.page_count == 1

    def test_missing_template_id(self) -> None:
        result = validate_template(_make_html(template_id=""))
        assert result.valid is False
        assert any("template_id is required" in e for e in result.errors)

    def test_box_id_mismatch(self) -> None:
        result = validate_template(_make_html(box_id="box-001", dom_box_id="box-999"))
        assert result.valid is False
        assert any("does not exist in template HTML" in e for e in result.errors)

    def test_variable_name_mismatch(self) -> None:
        result = validate_template(_make_html(variable_name="name", dom_variable="other"))
        assert result.valid is False
        assert any("not in template" in e or "not in manifest" in e for e in result.errors)

    def test_invalid_html_raises(self) -> None:
        with pytest.raises(HtmlParseError):
            validate_template("")
