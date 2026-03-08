"""OCR結果集約。

帳票1枚分の全フィールドの読取結果を管理する。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.src.ocr_result.ocr_result_types import (
    FieldResult,
    ReadingStatus,
)
from domain.src.shared.entity_base import BaseEntity


@dataclass
class OcrResult(BaseEntity):
    """OCR結果集約ルート。1回の読取（1ページ分）の結果を保持する。"""

    template_id: str = ""
    page_index: int = 0
    field_results: list[FieldResult] = field(default_factory=list)

    def add_result(self, result: FieldResult) -> None:
        """フィールド結果を追加する。"""
        self.field_results.append(result)

    def get_result(self, variable_name: str) -> FieldResult | None:
        """変数名でフィールド結果を取得する。"""
        for r in self.field_results:
            if r.variable_name == variable_name:
                return r
        return None

    def correct_field(self, variable_name: str, new_value: str | int | float | bool) -> None:
        """フィールドの値を手動修正する。"""
        for i, r in enumerate(self.field_results):
            if r.variable_name == variable_name:
                self.field_results[i] = r.with_corrected_value(new_value)
                return
        raise KeyError(f"field '{variable_name}' not found in results")

    @property
    def needs_review_fields(self) -> list[FieldResult]:
        """レビューが必要なフィールドのみ返す。"""
        return [r for r in self.field_results if r.needs_review]

    @property
    def all_confirmed(self) -> bool:
        """全フィールドが確認済み（confirmed or corrected）かどうか。"""
        return all(r.status in (ReadingStatus.CONFIRMED, ReadingStatus.CORRECTED) for r in self.field_results)

    def to_simple_dict(self) -> dict[str, str | int | float | bool | None]:
        """{ variableName: value } のシンプルなオブジェクトとして出力する。"""
        return {r.variable_name: r.value for r in self.field_results}

    def to_detailed_dict(
        self,
    ) -> dict[str, dict[str, str | float | None]]:
        """信頼度付きの詳細結果を出力する。"""
        return {
            r.variable_name: {
                "value": str(r.value) if r.value is not None else None,
                "confidence": r.confidence.score,
                "raw_text": r.raw_text,
                "status": r.status.value,
            }
            for r in self.field_results
        }
