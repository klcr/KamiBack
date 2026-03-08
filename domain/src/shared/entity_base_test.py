"""entity_base.py のユニットテスト。"""

from __future__ import annotations

from uuid import UUID, uuid4

from domain.src.shared.entity_base import BaseEntity


class TestBaseEntity:
    def test_auto_id(self) -> None:
        entity = BaseEntity()
        assert isinstance(entity.id, UUID)

    def test_explicit_id(self) -> None:
        given_id = uuid4()
        entity = BaseEntity(id=given_id)
        assert entity.id == given_id

    def test_equality_same_id(self) -> None:
        shared_id = uuid4()
        a = BaseEntity(id=shared_id)
        b = BaseEntity(id=shared_id)
        assert a == b

    def test_inequality_different_id(self) -> None:
        a = BaseEntity()
        b = BaseEntity()
        assert a != b

    def test_hash_same_id(self) -> None:
        shared_id = uuid4()
        a = BaseEntity(id=shared_id)
        b = BaseEntity(id=shared_id)
        assert hash(a) == hash(b)

    def test_not_equal_to_non_entity(self) -> None:
        entity = BaseEntity()
        assert entity != "not an entity"
