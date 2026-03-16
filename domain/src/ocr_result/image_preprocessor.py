"""画像前処理のインターフェース。

前処理パイプラインも差し替え可能にする（設計原則）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ImagePreprocessor(ABC):
    """画像前処理の抽象基底クラス。

    デフォルト実装はOpenCVベース（CvImagePreprocessor）。
    グレースケール→ブラー→適応的二値化のパイプラインを適用する。
    """

    @abstractmethod
    def preprocess(self, image: Any) -> Any:
        """補正画像に前処理を適用する。

        Args:
            image: 入力画像（numpy ndarray）

        Returns:
            前処理済み画像（numpy ndarray）
        """
