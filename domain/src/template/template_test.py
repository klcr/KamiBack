"""template集約のユニットテスト。"""

from __future__ import annotations

import pytest

from domain.src.manifest.manifest_types import (
    Centering,
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
from domain.src.shared.errors import ValidationError
from domain.src.template.template import Template
from domain.src.template.template_policy import validate_template_manifest_consistency
from domain.src.template.template_types import (
    Box,
    BoxRole,
    Line,
    PageTemplate,
    TemplateMetadata,
)


def _make_template_metadata(
    boxes: tuple[Box, ...] | None = None,
) -> TemplateMetadata:
    if boxes is None:
        boxes = (
            Box(
                box_id="p0-box-1",
                role=BoxRole.FIELD,
                region_mm=Region(x_mm=50, y_mm=5, width_mm=60, height_mm=8),
                text_content="{{invoiceNumber}}",
                variable_name="invoiceNumber",
                data_type="string",
            ),
            Box(
                box_id="p0-box-2",
                role=BoxRole.LABEL,
                region_mm=Region(x_mm=10, y_mm=5, width_mm=30, height_mm=8),
                text_content="請求番号",
            ),
            Box(
                box_id="p0-box-3",
                role=BoxRole.DECORATION,
                region_mm=Region(x_mm=0, y_mm=0, width_mm=190, height_mm=1),
            ),
        )
    return TemplateMetadata(
        source_html="<html>...</html>",
        page_count=1,
        pages=(
            PageTemplate(
                page_index=0,
                boxes=boxes,
                lines=(Line(line_id="p0-line-1", x1_mm=0, y1_mm=50, x2_mm=190, y2_mm=50),),
            ),
        ),
    )


def _make_manifest_data(
    variable_names: list[str] | None = None,
    box_ids: list[str] | None = None,
) -> ManifestData:
    if variable_names is None:
        variable_names = ["invoiceNumber"]
    if box_ids is None:
        box_ids = ["p0-box-1"] * len(variable_names)

    fields = tuple(
        Field(
            variable_id=f"var-{name}",
            variable_name=name,
            variable_type=VariableType.STRING,
            input_type=InputType.PRINTED,
            box_id=bid,
            region=Region(x_mm=50, y_mm=5, width_mm=60, height_mm=8),
            absolute_region=Region(x_mm=69.05, y_mm=30.4, width_mm=60, height_mm=8),
        )
        for name, bid in zip(variable_names, box_ids, strict=True)
    )
    return ManifestData(
        template_id="invoice-001",
        version="1.0.0",
        pages=(
            Page(
                page_index=0,
                paper=Paper(
                    size=PaperSize.A4,
                    orientation=Orientation.PORTRAIT,
                    width_mm=210,
                    height_mm=297,
                    margins=Margins(top=25.4, right=19.05, bottom=25.4, left=19.05),
                ),
                fields=fields,
            ),
        ),
    )


class TestTemplate:
    def test_all_field_boxes(self) -> None:
        t = Template(metadata=_make_template_metadata())
        fields = t.all_field_boxes()
        assert len(fields) == 1
        assert fields[0].variable_name == "invoiceNumber"

    def test_field_variable_names(self) -> None:
        t = Template(metadata=_make_template_metadata())
        assert t.field_variable_names() == ["invoiceNumber"]

    def test_get_box_found(self) -> None:
        t = Template(metadata=_make_template_metadata())
        box = t.get_box("p0-box-1")
        assert box is not None
        assert box.is_field

    def test_get_box_not_found(self) -> None:
        t = Template(metadata=_make_template_metadata())
        assert t.get_box("nonexistent") is None

    def test_page_count(self) -> None:
        t = Template(metadata=_make_template_metadata())
        assert t.page_count == 1

    def test_not_loaded_raises(self) -> None:
        t = Template()
        with pytest.raises(ValueError, match="not been loaded"):
            t.all_field_boxes()


class TestPageTemplate:
    def test_field_boxes(self) -> None:
        meta = _make_template_metadata()
        page = meta.pages[0]
        assert len(page.field_boxes) == 1

    def test_label_boxes(self) -> None:
        meta = _make_template_metadata()
        page = meta.pages[0]
        assert len(page.label_boxes) == 1
        assert page.label_boxes[0].text_content == "請求番号"


class TestTemplateManifestConsistency:
    def test_valid(self) -> None:
        template = _make_template_metadata()
        manifest = _make_manifest_data()
        validate_template_manifest_consistency(template, manifest)

    def test_page_count_mismatch(self) -> None:
        template = _make_template_metadata()
        manifest = ManifestData(
            template_id="test",
            version="1.0.0",
            pages=(),  # 0 pages vs 1 page in template
        )
        with pytest.raises(ValidationError, match="page count mismatch"):
            validate_template_manifest_consistency(template, manifest)

    def test_variable_in_manifest_not_in_template(self) -> None:
        template = _make_template_metadata()
        manifest = _make_manifest_data(
            variable_names=["invoiceNumber", "extra"],
            box_ids=["p0-box-1", "p0-box-1"],
        )
        with pytest.raises(ValidationError, match="'extra' is in manifest but not in template"):
            validate_template_manifest_consistency(template, manifest)

    def test_variable_in_template_not_in_manifest(self) -> None:
        template = _make_template_metadata()
        manifest = _make_manifest_data(variable_names=[], box_ids=[])
        with pytest.raises(ValidationError, match="'invoiceNumber' is in template HTML but not in manifest"):
            validate_template_manifest_consistency(template, manifest)

    def test_missing_box_id(self) -> None:
        template = _make_template_metadata()
        manifest = _make_manifest_data(
            variable_names=["invoiceNumber"],
            box_ids=["nonexistent-box"],
        )
        with pytest.raises(ValidationError, match="does not exist in template HTML"):
            validate_template_manifest_consistency(template, manifest)

    def test_centering_consistent(self) -> None:
        template = TemplateMetadata(
            source_html="<html>...</html>",
            page_count=1,
            pages=(
                PageTemplate(
                    page_index=0,
                    boxes=_make_template_metadata().pages[0].boxes,
                    lines=(),
                    horizontal_centered=True,
                    vertical_centered=False,
                ),
            ),
        )
        manifest = ManifestData(
            template_id="invoice-001",
            version="1.0.0",
            pages=(
                Page(
                    page_index=0,
                    paper=Paper(
                        size=PaperSize.A4,
                        orientation=Orientation.PORTRAIT,
                        width_mm=210,
                        height_mm=297,
                        margins=Margins(top=25.4, right=19.05, bottom=25.4, left=19.05),
                        centering=Centering(horizontal=True, vertical=False),
                    ),
                    fields=_make_manifest_data().pages[0].fields,
                ),
            ),
        )
        validate_template_manifest_consistency(template, manifest)  # should not raise

    def test_centering_horizontal_mismatch(self) -> None:
        template = TemplateMetadata(
            source_html="<html>...</html>",
            page_count=1,
            pages=(
                PageTemplate(
                    page_index=0,
                    boxes=_make_template_metadata().pages[0].boxes,
                    lines=(),
                    horizontal_centered=True,
                    vertical_centered=False,
                ),
            ),
        )
        manifest = ManifestData(
            template_id="invoice-001",
            version="1.0.0",
            pages=(
                Page(
                    page_index=0,
                    paper=Paper(
                        size=PaperSize.A4,
                        orientation=Orientation.PORTRAIT,
                        width_mm=210,
                        height_mm=297,
                        margins=Margins(top=25.4, right=19.05, bottom=25.4, left=19.05),
                        centering=Centering(horizontal=False, vertical=False),
                    ),
                    fields=_make_manifest_data().pages[0].fields,
                ),
            ),
        )
        with pytest.raises(ValidationError, match="horizontal centering mismatch"):
            validate_template_manifest_consistency(template, manifest)

    def test_centering_vertical_mismatch(self) -> None:
        template = TemplateMetadata(
            source_html="<html>...</html>",
            page_count=1,
            pages=(
                PageTemplate(
                    page_index=0,
                    boxes=_make_template_metadata().pages[0].boxes,
                    lines=(),
                    horizontal_centered=False,
                    vertical_centered=False,
                ),
            ),
        )
        manifest = ManifestData(
            template_id="invoice-001",
            version="1.0.0",
            pages=(
                Page(
                    page_index=0,
                    paper=Paper(
                        size=PaperSize.A4,
                        orientation=Orientation.PORTRAIT,
                        width_mm=210,
                        height_mm=297,
                        margins=Margins(top=25.4, right=19.05, bottom=25.4, left=19.05),
                        centering=Centering(horizontal=False, vertical=True),
                    ),
                    fields=_make_manifest_data().pages[0].fields,
                ),
            ),
        )
        with pytest.raises(ValidationError, match="vertical centering mismatch"):
            validate_template_manifest_consistency(template, manifest)
