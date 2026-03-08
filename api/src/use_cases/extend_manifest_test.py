"""拡張マニフェスト生成ユースケースのテスト。"""

from __future__ import annotations

from api.src.use_cases.extend_manifest import extend_manifest_from_html

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


class TestExtendManifest:
    def test_extended_has_registration_marks(self) -> None:
        result = extend_manifest_from_html(_VALID_HTML)
        assert result.extended is True
        page = result.pages[0]
        assert page.registration_marks is not None
        assert len(page.registration_marks.positions) == 4

    def test_extended_has_page_identifier(self) -> None:
        result = extend_manifest_from_html(_VALID_HTML)
        page = result.pages[0]
        assert page.page_identifier is not None
        assert page.page_identifier.content == "test-001/0"

    def test_extended_preserves_fields(self) -> None:
        result = extend_manifest_from_html(_VALID_HTML)
        assert len(result.pages[0].fields) == 1
        assert result.pages[0].fields[0].variable_name == "name"
