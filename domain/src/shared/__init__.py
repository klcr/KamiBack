"""共通ドメイン基盤。"""

from domain.src.shared.coordinate import Point, Region, Size
from domain.src.shared.entity_base import BaseEntity
from domain.src.shared.errors import DomainError, ValidationError

__all__ = [
    "BaseEntity",
    "DomainError",
    "Point",
    "Region",
    "Size",
    "ValidationError",
]
