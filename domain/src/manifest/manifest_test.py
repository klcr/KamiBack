"""manifest集約のユニットテスト。"""

from __future__ import annotations

import pytest

from domain.src.manifest.manifest import Manifest
from domain.src.manifest.manifest_policy import validate_manifest
from domain.src.manifest.manifest_types import (
    Centering,
    Field,
    HeaderFooter,
    HeaderFooterEntry,
    HeaderFooterSections,
    InputType,
    ManifestData,
    Margins,
    Orientation,
    Page,
    Paper,
    PaperSize,
    VariableType,
)
from domain.src.shared.coordinate import Point, Region
from domain.src.shared.errors import ValidationError


def _make_paper_a4_portrait() -> Paper:
    return Paper(
        size=PaperSize.A4,
        orientation=Orientation.PORTRAIT,
        width_mm=210.0,
        height_mm=297.0,
        margins=Margins(top=25.4, right=19.05, bottom=25.4, left=19.05),
    )


def _make_field(
    name: str = "invoiceNumber",
    var_type: VariableType = VariableType.STRING,
    x: float = 50.0,
    y: float = 5.0,
    w: float = 60.0,
    h: float = 8.0,
) -> Field:
    return Field(
        variable_id=f"var-{name}",
        variable_name=name,
        variable_type=var_type,
        input_type=InputType.PRINTED,
        box_id=f"p0-box-{name}",
        region=Region(x_mm=x, y_mm=y, width_mm=w, height_mm=h),
        absolute_region=Region(x_mm=x + 19.05, y_mm=y + 25.4, width_mm=w, height_mm=h),
    )


def _make_manifest_data(
    fields: tuple[Field, ...] | None = None,
    template_id: str = "invoice-001",
) -> ManifestData:
    if fields is None:
        fields = (
            _make_field("invoiceNumber"),
            _make_field("amount", VariableType.NUMBER, x=50.0, y=20.0),
            _make_field("issueDate", VariableType.DATE, x=50.0, y=35.0),
        )
    return ManifestData(
        template_id=template_id,
        version="1.0.0",
        pages=(
            Page(
                page_index=0,
                paper=_make_paper_a4_portrait(),
                fields=fields,
            ),
        ),
        interface="interface TemplateData { invoiceNumber: string; amount: number; }",
    )


class TestManifest:
    def test_all_variable_names(self) -> None:
        m = Manifest(data=_make_manifest_data())
        names = m.all_variable_names()
        assert names == ["invoiceNumber", "amount", "issueDate"]

    def test_all_fields(self) -> None:
        m = Manifest(data=_make_manifest_data())
        fields = m.all_fields()
        assert len(fields) == 3
        assert fields[0].variable_name == "invoiceNumber"

    def test_get_field_found(self) -> None:
        m = Manifest(data=_make_manifest_data())
        field = m.get_field("amount")
        assert field is not None
        assert field.variable_type == VariableType.NUMBER

    def test_get_field_not_found(self) -> None:
        m = Manifest(data=_make_manifest_data())
        assert m.get_field("nonexistent") is None

    def test_get_page(self) -> None:
        m = Manifest(data=_make_manifest_data())
        page = m.get_page(0)
        assert page is not None
        assert page.page_index == 0

    def test_get_page_not_found(self) -> None:
        m = Manifest(data=_make_manifest_data())
        assert m.get_page(99) is None

    def test_variable_type_map(self) -> None:
        m = Manifest(data=_make_manifest_data())
        type_map = m.variable_type_map()
        assert type_map["invoiceNumber"] == VariableType.STRING
        assert type_map["amount"] == VariableType.NUMBER
        assert type_map["issueDate"] == VariableType.DATE

    def test_not_loaded_raises(self) -> None:
        m = Manifest()
        with pytest.raises(ValueError, match="not been loaded"):
            m.all_variable_names()

    def test_is_extended_false(self) -> None:
        m = Manifest(data=_make_manifest_data())
        assert not m.is_extended

    def test_template_id(self) -> None:
        m = Manifest(data=_make_manifest_data())
        assert m.template_id == "invoice-001"


class TestManifestExtend:
    def test_extend_adds_registration_marks(self) -> None:
        m = Manifest(data=_make_manifest_data())
        extended = m.extend()

        assert extended.is_extended
        page = extended.get_page(0)
        assert page is not None
        assert page.registration_marks is not None
        assert len(page.registration_marks.positions) == 4

    def test_extend_preserves_original(self) -> None:
        m = Manifest(data=_make_manifest_data())
        _extended = m.extend()

        assert not m.is_extended
        page = m.get_page(0)
        assert page is not None
        assert page.registration_marks is None

    def test_extend_tombo_positions(self) -> None:
        m = Manifest(data=_make_manifest_data())
        extended = m.extend(tombo_offset_mm=5.0)

        page = extended.get_page(0)
        assert page is not None
        assert page.registration_marks is not None
        positions = page.registration_marks.positions
        # 左上
        assert positions[0] == Point(x_mm=5.0, y_mm=5.0)
        # 右上
        assert positions[1] == Point(x_mm=205.0, y_mm=5.0)
        # 左下
        assert positions[2] == Point(x_mm=5.0, y_mm=292.0)
        # 右下
        assert positions[3] == Point(x_mm=205.0, y_mm=292.0)

    def test_extend_adds_page_identifier(self) -> None:
        m = Manifest(data=_make_manifest_data())
        extended = m.extend()

        page = extended.get_page(0)
        assert page is not None
        assert page.page_identifier is not None
        assert page.page_identifier.content == "invoice-001/0"
        assert page.page_identifier.type == "qr"

    def test_extend_preserves_fields(self) -> None:
        m = Manifest(data=_make_manifest_data())
        extended = m.extend()
        assert extended.all_variable_names() == m.all_variable_names()

    def test_extend_same_id(self) -> None:
        m = Manifest(data=_make_manifest_data())
        extended = m.extend()
        assert extended.id == m.id


class TestManifestPolicy:
    def test_valid_manifest(self) -> None:
        data = _make_manifest_data()
        validate_manifest(data)  # should not raise

    def test_missing_template_id(self) -> None:
        data = _make_manifest_data(template_id="")
        with pytest.raises(ValidationError, match="template_id is required"):
            validate_manifest(data)

    def test_no_pages(self) -> None:
        data = ManifestData(
            template_id="test",
            version="1.0.0",
            pages=(),
        )
        with pytest.raises(ValidationError, match="at least one page"):
            validate_manifest(data)

    def test_field_exceeds_paper_width(self) -> None:
        field = Field(
            variable_id="var-1",
            variable_name="wide",
            variable_type=VariableType.STRING,
            input_type=InputType.PRINTED,
            box_id="p0-box-wide",
            region=Region(x_mm=0, y_mm=0, width_mm=200, height_mm=8),
            absolute_region=Region(x_mm=180, y_mm=10, width_mm=50, height_mm=8),
        )
        data = _make_manifest_data(fields=(field,))
        with pytest.raises(ValidationError, match="exceeds paper width"):
            validate_manifest(data)

    def test_duplicate_variable_name(self) -> None:
        f1 = _make_field("duplicate")
        f2 = _make_field("duplicate")
        data = _make_manifest_data(fields=(f1, f2))
        with pytest.raises(ValidationError, match="duplicate variable_name"):
            validate_manifest(data)

    def test_multiple_errors(self) -> None:
        data = ManifestData(
            template_id="",
            version="",
            pages=(),
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_manifest(data)
        assert len(exc_info.value.errors) >= 2


class TestSampleManifests:
    """サンプルマニフェストの構造検証テスト。"""

    def test_a4_portrait_validates(self) -> None:
        from domain.src.manifest.fixtures import make_a4_portrait_manifest

        data = make_a4_portrait_manifest()
        validate_manifest(data)  # should not raise

    def test_a3_landscape_validates(self) -> None:
        from domain.src.manifest.fixtures import make_a3_landscape_manifest

        data = make_a3_landscape_manifest()
        validate_manifest(data)  # should not raise

    def test_a4_portrait_structure(self) -> None:
        from domain.src.manifest.fixtures import make_a4_portrait_manifest

        data = make_a4_portrait_manifest()
        m = Manifest(data=data)
        assert m.template_id == "invoice-a4-001"
        assert len(m.pages) == 1
        assert len(m.all_fields()) == 5
        assert "company_name" in m.all_variable_names()
        assert "total_amount" in m.all_variable_names()
        type_map = m.variable_type_map()
        assert type_map["invoice_date"] == VariableType.DATE
        assert type_map["total_amount"] == VariableType.NUMBER
        assert type_map["approved"] == VariableType.BOOLEAN

    def test_a3_landscape_structure(self) -> None:
        from domain.src.manifest.fixtures import make_a3_landscape_manifest

        data = make_a3_landscape_manifest()
        m = Manifest(data=data)
        assert m.template_id == "inspection-a3-001"
        assert len(m.all_fields()) == 10
        assert m.get_field("inspector_name") is not None
        inspector = m.get_field("inspector_name")
        assert inspector is not None
        assert inspector.input_type == InputType.HANDWRITTEN_KANA

    def test_a4_portrait_extend(self) -> None:
        from domain.src.manifest.fixtures import make_a4_portrait_manifest

        data = make_a4_portrait_manifest()
        m = Manifest(data=data)
        extended = m.extend()
        assert extended.is_extended
        page = extended.get_page(0)
        assert page is not None
        assert page.registration_marks is not None
        assert page.page_identifier is not None
        assert page.page_identifier.content == "invoice-a4-001/0"

    def test_a3_landscape_coordinates_within_paper(self) -> None:
        from domain.src.manifest.fixtures import make_a3_landscape_manifest

        data = make_a3_landscape_manifest()
        for page in data.pages:
            for field in page.fields:
                ar = field.absolute_region
                assert ar.x_mm + ar.width_mm <= page.paper.width_mm
                assert ar.y_mm + ar.height_mm <= page.paper.height_mm


class TestCentering:
    def test_defaults(self) -> None:
        c = Centering()
        assert c.horizontal is False
        assert c.vertical is False

    def test_paper_with_centering(self) -> None:
        paper = Paper(
            size=PaperSize.A4,
            orientation=Orientation.PORTRAIT,
            width_mm=210.0,
            height_mm=297.0,
            margins=Margins(top=25.4, right=19.05, bottom=25.4, left=19.05),
            centering=Centering(horizontal=True, vertical=False),
        )
        assert paper.centering.horizontal is True
        assert paper.centering.vertical is False

    def test_paper_centering_defaults(self) -> None:
        paper = _make_paper_a4_portrait()
        assert paper.centering.horizontal is False
        assert paper.centering.vertical is False


class TestHeaderFooter:
    def test_page_with_header_footer(self) -> None:
        hf = HeaderFooter(
            odd_footer=HeaderFooterEntry(
                raw="&Cページ &P / &N",
                sections=HeaderFooterSections(left="", center="ページ &P / &N", right=""),
            ),
        )
        page = Page(
            page_index=0,
            paper=_make_paper_a4_portrait(),
            fields=(),
            header_footer=hf,
        )
        assert page.header_footer is not None
        assert page.header_footer.odd_footer is not None
        assert page.header_footer.odd_footer.sections.center == "ページ &P / &N"
        assert page.header_footer.odd_header is None

    def test_page_header_footer_defaults_to_none(self) -> None:
        page = Page(
            page_index=0,
            paper=_make_paper_a4_portrait(),
            fields=(),
        )
        assert page.header_footer is None

    def test_extend_preserves_header_footer(self) -> None:
        hf = HeaderFooter(
            odd_footer=HeaderFooterEntry(
                raw="&Cページ &P",
                sections=HeaderFooterSections(center="ページ &P"),
            ),
        )
        data = ManifestData(
            template_id="test-hf",
            version="1.0.0",
            pages=(
                Page(
                    page_index=0,
                    paper=_make_paper_a4_portrait(),
                    fields=(_make_field(),),
                    header_footer=hf,
                ),
            ),
        )
        m = Manifest(data=data)
        extended = m.extend()
        page = extended.get_page(0)
        assert page is not None
        assert page.header_footer is not None
        assert page.header_footer.odd_footer is not None
        assert page.header_footer.odd_footer.raw == "&Cページ &P"

    def test_extend_preserves_centering(self) -> None:
        data = ManifestData(
            template_id="test-centering",
            version="1.0.0",
            pages=(
                Page(
                    page_index=0,
                    paper=Paper(
                        size=PaperSize.A4,
                        orientation=Orientation.PORTRAIT,
                        width_mm=210.0,
                        height_mm=297.0,
                        margins=Margins(top=25.4, right=19.05, bottom=25.4, left=19.05),
                        centering=Centering(horizontal=True, vertical=True),
                    ),
                    fields=(_make_field(),),
                ),
            ),
        )
        m = Manifest(data=data)
        extended = m.extend()
        page = extended.get_page(0)
        assert page is not None
        assert page.paper.centering.horizontal is True
        assert page.paper.centering.vertical is True
