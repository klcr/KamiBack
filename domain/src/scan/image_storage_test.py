"""ImageStorageインターフェースのユニットテスト。"""

from __future__ import annotations

import pytest

from domain.src.scan.image_storage import ImageStorage


class TestImageStorageInterface:
    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            ImageStorage()  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self) -> None:
        class InMemoryImageStorage(ImageStorage):
            def __init__(self) -> None:
                self._store: dict[str, bytes] = {}

            def save(self, image_data: bytes, image_id: str) -> str:
                self._store[image_id] = image_data
                return f"mem://{image_id}"

            def load(self, image_id: str) -> bytes:
                if image_id not in self._store:
                    raise FileNotFoundError(image_id)
                return self._store[image_id]

            def delete(self, image_id: str) -> None:
                if image_id not in self._store:
                    raise FileNotFoundError(image_id)
                del self._store[image_id]

        storage = InMemoryImageStorage()
        path = storage.save(b"png-data", "img-001")
        assert path == "mem://img-001"
        assert storage.load("img-001") == b"png-data"
        storage.delete("img-001")
        with pytest.raises(FileNotFoundError):
            storage.load("img-001")
