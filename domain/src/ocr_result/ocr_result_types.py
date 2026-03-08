"""OCR結果の型定義。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.src.manifest.manifest_types import VariableType


class ReadingStatus(Enum):
    """フィールドの読取状態。"""

    CONFIRMED = "confirmed"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"
    CORRECTED = "corrected"


@dataclass(frozen=True)
class Confidence:
    """OCR信頼度スコア（0.0〜1.0）。"""

    score: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"confidence score must be 0.0-1.0, got {self.score}")

    @property
    def is_high(self) -> bool:
        """高信頼度（0.9以上）。"""
        return self.score >= 0.9

    @property
    def is_low(self) -> bool:
        """低信頼度（0.7未満）。"""
        return self.score < 0.7


@dataclass(frozen=True)
class FieldResult:
    """1フィールドのOCR読取結果。"""

    variable_name: str
    variable_type: VariableType
    value: str | int | float | bool | None
    raw_text: str
    confidence: Confidence
    status: ReadingStatus

    @property
    def needs_review(self) -> bool:
        return self.status == ReadingStatus.NEEDS_REVIEW

    def with_corrected_value(self, new_value: str | int | float | bool) -> FieldResult:
        """手動修正後の新しいFieldResultを返す。"""
        return FieldResult(
            variable_name=self.variable_name,
            variable_type=self.variable_type,
            value=new_value,
            raw_text=self.raw_text,
            confidence=self.confidence,
            status=ReadingStatus.CORRECTED,
        )


@dataclass(frozen=True)
class OcrEngineResult:
    """OCRエンジンの生の出力。"""

    text: str
    confidence: float
