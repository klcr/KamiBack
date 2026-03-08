"""OCRエンジンのインターフェース。

エンジンの差し替えを前提とする（設計原則）。
「画像を渡したら文字列と信頼度が返る」に統一する。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from domain.src.manifest.manifest_types import InputType
from domain.src.ocr_result.ocr_result_types import OcrEngineResult


class OcrEngine(ABC):
    """OCRエンジンの抽象基底クラス。

    inputTypeに応じて実装を切り替える。
    例: printed → NDLOCR-Lite PARSeq
        handwritten_number → 手書き数字認識モデル
    """

    @abstractmethod
    def recognize(self, image: Any, input_type: InputType) -> OcrEngineResult:
        """画像から文字列を認識する。

        Args:
            image: 切り出されたボックス画像（numpy ndarray等）
            input_type: フィールドの入力種別

        Returns:
            認識結果（テキストと信頼度）
        """
