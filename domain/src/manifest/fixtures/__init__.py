"""マニフェストのサンプルデータ（テスト用ファクトリ）。"""

from __future__ import annotations

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


def make_a4_portrait_manifest() -> ManifestData:
    """A4縦、5フィールドのサンプルマニフェスト。"""
    paper = Paper(
        size=PaperSize.A4,
        orientation=Orientation.PORTRAIT,
        width_mm=210.0,
        height_mm=297.0,
        margins=Margins(top=15.0, right=10.0, bottom=15.0, left=10.0),
    )
    fields = (
        Field(
            variable_id="v-001",
            variable_name="company_name",
            variable_type=VariableType.STRING,
            input_type=InputType.PRINTED,
            box_id="box-001",
            region=Region(x_mm=20.0, y_mm=20.0, width_mm=80.0, height_mm=8.0),
            absolute_region=Region(x_mm=30.0, y_mm=35.0, width_mm=80.0, height_mm=8.0),
        ),
        Field(
            variable_id="v-002",
            variable_name="invoice_date",
            variable_type=VariableType.DATE,
            input_type=InputType.PRINTED,
            box_id="box-002",
            region=Region(x_mm=120.0, y_mm=20.0, width_mm=50.0, height_mm=8.0),
            absolute_region=Region(x_mm=130.0, y_mm=35.0, width_mm=50.0, height_mm=8.0),
        ),
        Field(
            variable_id="v-003",
            variable_name="total_amount",
            variable_type=VariableType.NUMBER,
            input_type=InputType.PRINTED,
            box_id="box-003",
            region=Region(x_mm=120.0, y_mm=100.0, width_mm=60.0, height_mm=10.0),
            absolute_region=Region(x_mm=130.0, y_mm=115.0, width_mm=60.0, height_mm=10.0),
        ),
        Field(
            variable_id="v-004",
            variable_name="customer_address",
            variable_type=VariableType.STRING,
            input_type=InputType.PRINTED,
            box_id="box-004",
            region=Region(x_mm=20.0, y_mm=40.0, width_mm=100.0, height_mm=8.0),
            absolute_region=Region(x_mm=30.0, y_mm=55.0, width_mm=100.0, height_mm=8.0),
        ),
        Field(
            variable_id="v-005",
            variable_name="approved",
            variable_type=VariableType.BOOLEAN,
            input_type=InputType.CHECKBOX,
            box_id="box-005",
            region=Region(x_mm=20.0, y_mm=250.0, width_mm=6.0, height_mm=6.0),
            absolute_region=Region(x_mm=30.0, y_mm=265.0, width_mm=6.0, height_mm=6.0),
        ),
    )
    return ManifestData(
        template_id="invoice-a4-001",
        version="1.0",
        pages=(Page(page_index=0, paper=paper, fields=fields),),
    )


def make_a3_landscape_manifest() -> ManifestData:
    """A3横、10フィールドのサンプルマニフェスト。"""
    paper = Paper(
        size=PaperSize.A3,
        orientation=Orientation.LANDSCAPE,
        width_mm=420.0,
        height_mm=297.0,
        margins=Margins(top=15.0, right=15.0, bottom=15.0, left=15.0),
    )
    fields: list[Field] = []
    y_positions = [30.0, 50.0, 70.0, 90.0, 110.0, 130.0, 150.0, 170.0, 190.0, 210.0]
    names = [
        ("item_name_1", VariableType.STRING, InputType.PRINTED),
        ("item_qty_1", VariableType.NUMBER, InputType.PRINTED),
        ("item_name_2", VariableType.STRING, InputType.PRINTED),
        ("item_qty_2", VariableType.NUMBER, InputType.PRINTED),
        ("item_name_3", VariableType.STRING, InputType.PRINTED),
        ("item_qty_3", VariableType.NUMBER, InputType.PRINTED),
        ("delivery_date", VariableType.DATE, InputType.PRINTED),
        ("warehouse_code", VariableType.STRING, InputType.PRINTED),
        ("inspector_name", VariableType.STRING, InputType.HANDWRITTEN_KANA),
        ("inspection_ok", VariableType.BOOLEAN, InputType.CHECKBOX),
    ]
    for i, (name, vtype, itype) in enumerate(names):
        fields.append(
            Field(
                variable_id=f"v-{i + 1:03d}",
                variable_name=name,
                variable_type=vtype,
                input_type=itype,
                box_id=f"box-{i + 1:03d}",
                region=Region(x_mm=30.0, y_mm=y_positions[i], width_mm=120.0, height_mm=8.0),
                absolute_region=Region(x_mm=45.0, y_mm=y_positions[i] + 15.0, width_mm=120.0, height_mm=8.0),
            )
        )
    return ManifestData(
        template_id="inspection-a3-001",
        version="1.0",
        pages=(Page(page_index=0, paper=paper, fields=tuple(fields)),),
    )
