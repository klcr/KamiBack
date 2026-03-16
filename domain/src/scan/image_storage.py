"""補正画像のストレージインターフェース。

ストレージの差し替えを前提とする（設計原則）。
ローカルファイル → S3 等への移行パスを確保する。
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ImageStorage(ABC):
    """補正画像の保存・取得・削除を行う抽象基底クラス。

    初期実装はローカルファイルシステム（LocalFileImageStorage）。
    本番環境ではS3等のオブジェクトストレージに差し替える。
    """

    @abstractmethod
    def save(self, image_data: bytes, image_id: str) -> str:
        """画像を保存し、パスまたはURLを返す。

        Args:
            image_data: 画像のバイナリデータ（PNG等）
            image_id: 画像の一意識別子

        Returns:
            保存先のパスまたはURL
        """

    @abstractmethod
    def load(self, image_id: str) -> bytes:
        """画像IDから画像データを取得する。

        Args:
            image_id: 画像の一意識別子

        Returns:
            画像のバイナリデータ

        Raises:
            FileNotFoundError: 指定IDの画像が見つからない場合
        """

    @abstractmethod
    def delete(self, image_id: str) -> None:
        """画像を削除する。

        Args:
            image_id: 画像の一意識別子

        Raises:
            FileNotFoundError: 指定IDの画像が見つからない場合
        """
