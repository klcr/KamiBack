"""QRコード検出のインターフェース。

ページ識別コード（QRコード）からテンプレートIDとページインデックスを取得する。
検出ライブラリの差し替えを前提とする（設計原則）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QrDetectionResult:
    """QRコード検出結果。

    QRコードのcontent形式: "{template_id}/{page_index}"
    （PageIdentifier.content と同一フォーマット）
    """

    detected: bool
    template_id: str | None = None
    page_index: int | None = None
    raw_content: str | None = None


class QrDetector(ABC):
    """QRコード検出の抽象基底クラス。

    デフォルト実装はpyzbarベース（PyzbarQrDetector）。
    """

    @abstractmethod
    def detect(self, image: Any) -> QrDetectionResult:
        """画像からQRコードを検出し、テンプレートIDとページインデックスを返す。

        Args:
            image: 撮影画像（numpy ndarray等）

        Returns:
            検出結果（検出有無、テンプレートID、ページインデックス）
        """
