"""OCR結果のリポジトリインターフェース。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.src.ocr_result.ocr_result import OcrResult


class OcrResultRepository(ABC):
    """OCR結果の永続化インターフェース。"""

    @abstractmethod
    def save(self, result: OcrResult) -> None:
        """OCR結果を保存する。"""

    @abstractmethod
    def find_by_id(self, result_id: UUID) -> OcrResult | None:
        """IDでOCR結果を取得する。"""
