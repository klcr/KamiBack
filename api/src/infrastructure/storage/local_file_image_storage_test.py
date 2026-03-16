"""LocalFileImageStorageのユニットテスト。"""

from __future__ import annotations

from pathlib import Path

import pytest

from api.src.infrastructure.storage.local_file_image_storage import (
    LocalFileImageStorage,
)


class TestLocalFileImageStorage:
    def test_save_and_load(self, tmp_path: Path) -> None:
        storage = LocalFileImageStorage(base_dir=str(tmp_path))
        data = b"\x89PNG\r\n\x1a\nfake-png-data"
        path = storage.save(data, "corrected-001")
        assert Path(path).exists()
        assert storage.load("corrected-001") == data

    def test_save_overwrites_existing(self, tmp_path: Path) -> None:
        storage = LocalFileImageStorage(base_dir=str(tmp_path))
        storage.save(b"v1", "img-001")
        storage.save(b"v2", "img-001")
        assert storage.load("img-001") == b"v2"

    def test_load_not_found(self, tmp_path: Path) -> None:
        storage = LocalFileImageStorage(base_dir=str(tmp_path))
        with pytest.raises(FileNotFoundError):
            storage.load("nonexistent")

    def test_delete(self, tmp_path: Path) -> None:
        storage = LocalFileImageStorage(base_dir=str(tmp_path))
        storage.save(b"data", "img-002")
        storage.delete("img-002")
        with pytest.raises(FileNotFoundError):
            storage.load("img-002")

    def test_delete_not_found(self, tmp_path: Path) -> None:
        storage = LocalFileImageStorage(base_dir=str(tmp_path))
        with pytest.raises(FileNotFoundError):
            storage.delete("nonexistent")

    def test_cleanup(self, tmp_path: Path) -> None:
        sub_dir = tmp_path / "session"
        storage = LocalFileImageStorage(base_dir=str(sub_dir))
        storage.save(b"data", "img-003")
        assert sub_dir.exists()
        storage.cleanup()
        assert not sub_dir.exists()

    def test_default_base_dir_uses_tempdir(self) -> None:
        storage = LocalFileImageStorage()
        assert Path(storage.base_dir).exists()
        storage.cleanup()

    def test_base_dir_property(self, tmp_path: Path) -> None:
        storage = LocalFileImageStorage(base_dir=str(tmp_path))
        assert storage.base_dir == str(tmp_path)
