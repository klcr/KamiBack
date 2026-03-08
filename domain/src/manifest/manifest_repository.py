"""マニフェストのリポジトリインターフェース。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.src.manifest.manifest import Manifest


class ManifestRepository(ABC):
    """マニフェストの永続化インターフェース。"""

    @abstractmethod
    def save(self, manifest: Manifest) -> None:
        """マニフェストを保存する。"""

    @abstractmethod
    def find_by_id(self, manifest_id: UUID) -> Manifest | None:
        """IDでマニフェストを取得する。"""

    @abstractmethod
    def find_by_template_id(self, template_id: str) -> Manifest | None:
        """テンプレートIDでマニフェストを取得する。"""
