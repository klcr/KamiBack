"""テンプレートのリポジトリインターフェース。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.src.template.template import Template


class TemplateRepository(ABC):
    """テンプレートの永続化インターフェース。"""

    @abstractmethod
    def save(self, template: Template) -> None:
        """テンプレートを保存する。"""

    @abstractmethod
    def find_by_id(self, template_id: UUID) -> Template | None:
        """IDでテンプレートを取得する。"""
