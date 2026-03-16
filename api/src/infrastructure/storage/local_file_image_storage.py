"""ローカルファイルシステムによるImageStorage実装。

一時ディレクトリに補正画像を保存する。
S3等への移行時はこのクラスを差し替えるだけで済む。
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from domain.src.scan.image_storage import ImageStorage


class LocalFileImageStorage(ImageStorage):
    """ローカルファイルシステムに画像を保存する。

    base_dir未指定時はtempfile.mkdtempで一時ディレクトリを作成する。
    cleanup()でbase_dir全体を削除できる。
    """

    def __init__(self, base_dir: str | None = None) -> None:
        if base_dir is not None:
            self._base_path = Path(base_dir)
            self._base_path.mkdir(parents=True, exist_ok=True)
        else:
            self._base_path = Path(tempfile.mkdtemp(prefix="kami_scan_"))

    @property
    def base_dir(self) -> str:
        """保存先ディレクトリのパスを返す。"""
        return str(self._base_path)

    def save(self, image_data: bytes, image_id: str) -> str:
        """画像をファイルとして保存する。"""
        file_path = self._base_path / f"{image_id}.png"
        file_path.write_bytes(image_data)
        return str(file_path)

    def load(self, image_id: str) -> bytes:
        """画像ファイルを読み込む。"""
        file_path = self._base_path / f"{image_id}.png"
        if not file_path.exists():
            raise FileNotFoundError(f"image not found: {image_id}")
        return file_path.read_bytes()

    def delete(self, image_id: str) -> None:
        """画像ファイルを削除する。"""
        file_path = self._base_path / f"{image_id}.png"
        if not file_path.exists():
            raise FileNotFoundError(f"image not found: {image_id}")
        file_path.unlink()

    def cleanup(self) -> None:
        """base_dir全体を削除する（セッション終了時に呼び出す）。"""
        if self._base_path.exists():
            shutil.rmtree(self._base_path)
