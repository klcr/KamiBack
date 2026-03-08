"""テンプレート集約。

HTMLテンプレートのパース結果を保持し、マニフェストとの照合を提供する。
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.src.shared.entity_base import BaseEntity
from domain.src.template.template_types import Box, TemplateMetadata


@dataclass
class Template(BaseEntity):
    """テンプレート集約ルート。"""

    metadata: TemplateMetadata | None = None

    @property
    def page_count(self) -> int:
        self._ensure_loaded()
        assert self.metadata is not None
        return self.metadata.page_count

    def all_field_boxes(self) -> list[Box]:
        """全ページのフィールドボックスをフラットなリストで返す。"""
        self._ensure_loaded()
        assert self.metadata is not None
        boxes: list[Box] = []
        for page in self.metadata.pages:
            boxes.extend(page.field_boxes)
        return boxes

    def field_variable_names(self) -> list[str]:
        """全フィールドボックスの変数名を返す。"""
        return [
            b.variable_name
            for b in self.all_field_boxes()
            if b.variable_name is not None
        ]

    def get_box(self, box_id: str) -> Box | None:
        """ボックスIDで検索する。"""
        self._ensure_loaded()
        assert self.metadata is not None
        for page in self.metadata.pages:
            for box in page.boxes:
                if box.box_id == box_id:
                    return box
        return None

    def _ensure_loaded(self) -> None:
        if self.metadata is None:
            raise ValueError("Template metadata has not been loaded")
