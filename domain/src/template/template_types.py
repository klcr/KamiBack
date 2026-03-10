"""テンプレートの型定義。

HTMLテンプレートのパース結果を保持する値オブジェクト群。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.src.shared.coordinate import Region


class BoxRole(Enum):
    """ボックスの役割。"""

    FIELD = "field"
    LABEL = "label"
    DECORATION = "decoration"


@dataclass(frozen=True)
class Box:
    """HTML上の1ボックス（`<div class="box">`）。"""

    box_id: str
    role: BoxRole
    region_mm: Region
    text_content: str = ""
    variable_name: str | None = None
    data_type: str | None = None

    @property
    def is_field(self) -> bool:
        return self.role == BoxRole.FIELD

    @property
    def is_label(self) -> bool:
        return self.role == BoxRole.LABEL


@dataclass(frozen=True)
class Line:
    """HTML上の線分（`<div class="line">`）。"""

    line_id: str
    x1_mm: float
    y1_mm: float
    x2_mm: float
    y2_mm: float


@dataclass(frozen=True)
class PageTemplate:
    """HTMLテンプレートの1ページ分のパース結果。"""

    page_index: int
    boxes: tuple[Box, ...]
    lines: tuple[Line, ...]
    horizontal_centered: bool = False
    vertical_centered: bool = False

    @property
    def field_boxes(self) -> list[Box]:
        """data-role="field" のボックスのみ返す。"""
        return [b for b in self.boxes if b.is_field]

    @property
    def label_boxes(self) -> list[Box]:
        """data-role="label" のボックスのみ返す。"""
        return [b for b in self.boxes if b.is_label]


@dataclass(frozen=True)
class TemplateMetadata:
    """テンプレート全体のメタデータ。"""

    source_html: str
    page_count: int
    pages: tuple[PageTemplate, ...]
