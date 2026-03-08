"""ドメインエンティティの基底クラス。"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class BaseEntity:
    """全エンティティの基底。IDによる等価性を提供する。"""

    id: UUID = field(default_factory=uuid4)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseEntity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
