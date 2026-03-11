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


# --- DOMからの変数自動検出テスト ---

_EMPTY_FIELDS_HTML = """<!DOCTYPE html>
<html><body>
<script id="template-manifest" type="application/json">
{
  "templateId": "test-a4-light",
  "version": "1.0.0",
  "pages": [{"pageIndex": 0, "paper": {
    "size": "A4", "orientation": "portrait", "widthMm": 210, "heightMm": 297,
    "margins": {"top": 15.24, "right": 12.7, "bottom": 12.7, "left": 12.7}
  }, "fields": []}]
}
</script>
<section class="sheet" data-page-index="0"
  style="position: relative; width: 184.6mm; height: 269.06mm;">
  <div class="box" data-box-id="p0-box-1" data-role="label"
       data-x-mm="0" data-y-mm="0" data-w-mm="145" data-h-mm="10">請求書</div>
  <div class="box" data-box-id="p0-box-3" data-role="label"
       data-x-mm="28.91" data-y-mm="15.08" data-w-mm="42.98" data-h-mm="6.74">{{invoiceDate}}</div>
  <div class="box" data-box-id="p0-box-5" data-role="label"
       data-x-mm="135.48" data-y-mm="15.08" data-w-mm="10.05" data-h-mm="6.74">{{invoiceNumber}}</div>
</section>
</body></html>"""


class TestExtendManifestDomVariables:
    """DOMの{{変数名}}パターンからフィールドを自動生成するテスト。"""

    def test_discovers_variables_from_mustache_pattern(self) -> None:
        result = extend_manifest_from_html(_EMPTY_FIELDS_HTML)
        fields = result.pages[0].fields
        assert len(fields) == 2
        var_names = {f.variable_name for f in fields}
        assert var_names == {"invoiceDate", "invoiceNumber"}

    def test_discovered_fields_have_correct_region(self) -> None:
        result = extend_manifest_from_html(_EMPTY_FIELDS_HTML)
        invoice_date = [f for f in result.pages[0].fields if f.variable_name == "invoiceDate"][0]
        assert invoice_date.region.x_mm == 28.91
        assert invoice_date.region.width_mm == 42.98

    def test_discovered_fields_have_absolute_region_with_margins(self) -> None:
        result = extend_manifest_from_html(_EMPTY_FIELDS_HTML)
        invoice_date = [f for f in result.pages[0].fields if f.variable_name == "invoiceDate"][0]
        # absolute = region + margins (left=12.7, top=15.24)
        assert invoice_date.absolute_region.x_mm == 28.91 + 12.7
        assert invoice_date.absolute_region.y_mm == 15.08 + 15.24

    def test_does_not_override_existing_fields(self) -> None:
        """既にfieldsが定義されているページはそのまま保持する。"""
        result = extend_manifest_from_html(_VALID_HTML)
        assert len(result.pages[0].fields) == 1
        assert result.pages[0].fields[0].variable_name == "name"


# --- センタリング有効時の absolute_region 補正テスト ---

_CENTERED_HTML = """<!DOCTYPE html>
<html><body>
<script id="template-manifest" type="application/json">
{
  "templateId": "centered-001",
  "version": "1.0.0",
  "pages": [{"pageIndex": 0, "paper": {
    "size": "A4", "orientation": "portrait", "widthMm": 210, "heightMm": 297,
    "margins": {"top": 30, "right": 10, "bottom": 20, "left": 20},
    "centering": {"horizontal": true, "vertical": true}
  }, "fields": []}]
}
</script>
<section class="sheet" data-page-index="0"
  data-horizontal-centered="true" data-vertical-centered="true"
  style="position: relative; width: 180mm; height: 247mm;">
  <div class="box" data-box-id="p0-box-1" data-role="field"
       data-x-mm="10" data-y-mm="5" data-w-mm="50" data-h-mm="8"
       data-variable="name" data-type="string">{{name}}</div>
</section>
</body></html>"""


class TestExtendManifestCentering:
    """センタリング有効時に absolute_region が均等化マージンで計算されることを検証。"""

    def test_absolute_region_uses_equalized_margins(self) -> None:
        result = extend_manifest_from_html(_CENTERED_HTML)
        field = result.pages[0].fields[0]
        # 均等化マージン: left = (20 + 10) / 2 = 15, top = (30 + 20) / 2 = 25
        assert field.absolute_region.x_mm == 10 + 15  # region.x + equalized left
        assert field.absolute_region.y_mm == 5 + 25  # region.y + equalized top
        # region（印刷可能領域内座標）は変化しない
        assert field.region.x_mm == 10
        assert field.region.y_mm == 5
