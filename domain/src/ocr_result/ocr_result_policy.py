"""OCR結果のバリデーションポリシー。

信頼度閾値の判定と、variableTypeに基づく値の妥当性チェックを行う。
"""

from __future__ import annotations

import re

from domain.src.manifest.manifest_types import VariableType
from domain.src.ocr_result.ocr_result_types import (
    Confidence,
    FieldResult,
    OcrEngineResult,
    ReadingStatus,
)

# デフォルトの信頼度閾値
DEFAULT_CONFIDENCE_THRESHOLD = 0.7


def determine_reading_status(
    confidence: Confidence,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> ReadingStatus:
    """信頼度から読取状態を判定する。"""
    if confidence.score >= threshold:
        return ReadingStatus.CONFIRMED
    return ReadingStatus.NEEDS_REVIEW


def validate_value_for_type(
    raw_text: str, variable_type: VariableType
) -> str | int | float | bool | None:
    """OCR生テキストをvariableTypeに基づいて型変換する。

    変換できない場合はNoneを返す（エラーにしない。信頼度で判断する）。
    """
    if not raw_text.strip():
        return None

    text = raw_text.strip()

    if variable_type == VariableType.STRING:
        return text

    if variable_type == VariableType.NUMBER:
        # カンマ区切りの数値にも対応
        cleaned = text.replace(",", "").replace("，", "")
        try:
            if "." in cleaned:
                return float(cleaned)
            return int(cleaned)
        except ValueError:
            return None

    if variable_type == VariableType.DATE:
        # 日付パターンの基本チェック（YYYY/MM/DD, YYYY-MM-DD, YYYY年MM月DD日）
        date_patterns = [
            r"\d{4}[/\-年]\d{1,2}[/\-月]\d{1,2}日?",
            r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}",
        ]
        for pattern in date_patterns:
            if re.match(pattern, text):
                return text
        return None

    if variable_type == VariableType.BOOLEAN:
        if text.lower() in ("true", "1", "yes", "○", "✓", "✔"):
            return True
        if text.lower() in ("false", "0", "no", "×", ""):
            return False
        return None

    return text


def build_field_result(
    variable_name: str,
    variable_type: VariableType,
    engine_result: OcrEngineResult,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> FieldResult:
    """OCRエンジンの出力からFieldResultを構築する。"""
    confidence = Confidence(score=engine_result.confidence)
    value = validate_value_for_type(engine_result.text, variable_type)
    status = determine_reading_status(confidence, confidence_threshold)

    # 型変換に失敗した場合はレビュー必須
    if value is None and engine_result.text.strip():
        status = ReadingStatus.NEEDS_REVIEW

    return FieldResult(
        variable_name=variable_name,
        variable_type=variable_type,
        value=value,
        raw_text=engine_result.text,
        confidence=confidence,
        status=status,
    )
