"""ocr_result集約のユニットテスト。"""

from __future__ import annotations

import pytest

from domain.src.manifest.manifest_types import VariableType
from domain.src.ocr_result.ocr_result import OcrResult
from domain.src.ocr_result.ocr_result_policy import (
    build_field_result,
    determine_reading_status,
    validate_value_for_type,
)
from domain.src.ocr_result.ocr_result_types import (
    Confidence,
    FieldResult,
    OcrEngineResult,
    ReadingStatus,
)
from domain.src.ocr_result.tombo_detector import TomboDetectionResult
from domain.src.shared.coordinate import Point


class TestConfidence:
    def test_valid_score(self) -> None:
        c = Confidence(score=0.85)
        assert c.score == 0.85

    def test_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError):
            Confidence(score=1.5)
        with pytest.raises(ValueError):
            Confidence(score=-0.1)

    def test_is_high(self) -> None:
        assert Confidence(0.95).is_high
        assert not Confidence(0.85).is_high

    def test_is_low(self) -> None:
        assert Confidence(0.5).is_low
        assert not Confidence(0.8).is_low


class TestFieldResult:
    def test_needs_review(self) -> None:
        r = FieldResult(
            variable_name="amount",
            variable_type=VariableType.NUMBER,
            value=1000,
            raw_text="1000",
            confidence=Confidence(0.5),
            status=ReadingStatus.NEEDS_REVIEW,
        )
        assert r.needs_review

    def test_with_corrected_value(self) -> None:
        r = FieldResult(
            variable_name="amount",
            variable_type=VariableType.NUMBER,
            value=1000,
            raw_text="1000",
            confidence=Confidence(0.5),
            status=ReadingStatus.NEEDS_REVIEW,
        )
        corrected = r.with_corrected_value(2000)
        assert corrected.value == 2000
        assert corrected.status == ReadingStatus.CORRECTED
        assert corrected.raw_text == "1000"  # raw_textは変わらない


class TestOcrResult:
    def _make_field_result(
        self,
        name: str = "amount",
        value: int = 1000,
        confidence: float = 0.9,
        status: ReadingStatus = ReadingStatus.CONFIRMED,
    ) -> FieldResult:
        return FieldResult(
            variable_name=name,
            variable_type=VariableType.NUMBER,
            value=value,
            raw_text=str(value),
            confidence=Confidence(confidence),
            status=status,
        )

    def test_add_and_get(self) -> None:
        result = OcrResult(template_id="invoice-001", page_index=0)
        fr = self._make_field_result()
        result.add_result(fr)
        assert result.get_result("amount") is not None
        assert result.get_result("nonexistent") is None

    def test_needs_review_fields(self) -> None:
        result = OcrResult(template_id="invoice-001", page_index=0)
        result.add_result(self._make_field_result("a", status=ReadingStatus.CONFIRMED))
        result.add_result(self._make_field_result("b", status=ReadingStatus.NEEDS_REVIEW))
        result.add_result(self._make_field_result("c", status=ReadingStatus.NEEDS_REVIEW))
        assert len(result.needs_review_fields) == 2

    def test_all_confirmed(self) -> None:
        result = OcrResult(template_id="invoice-001", page_index=0)
        result.add_result(self._make_field_result("a", status=ReadingStatus.CONFIRMED))
        result.add_result(self._make_field_result("b", status=ReadingStatus.CORRECTED))
        assert result.all_confirmed

    def test_not_all_confirmed(self) -> None:
        result = OcrResult(template_id="invoice-001", page_index=0)
        result.add_result(self._make_field_result("a", status=ReadingStatus.CONFIRMED))
        result.add_result(self._make_field_result("b", status=ReadingStatus.NEEDS_REVIEW))
        assert not result.all_confirmed

    def test_correct_field(self) -> None:
        result = OcrResult(template_id="invoice-001", page_index=0)
        result.add_result(self._make_field_result("amount", value=1000, status=ReadingStatus.NEEDS_REVIEW))
        result.correct_field("amount", 2000)
        fr = result.get_result("amount")
        assert fr is not None
        assert fr.value == 2000
        assert fr.status == ReadingStatus.CORRECTED

    def test_correct_field_not_found(self) -> None:
        result = OcrResult(template_id="invoice-001", page_index=0)
        with pytest.raises(KeyError):
            result.correct_field("nonexistent", 0)

    def test_to_simple_dict(self) -> None:
        result = OcrResult(template_id="invoice-001", page_index=0)
        result.add_result(self._make_field_result("amount", value=1000))
        result.add_result(self._make_field_result("tax", value=100))
        simple = result.to_simple_dict()
        assert simple == {"amount": 1000, "tax": 100}

    def test_to_detailed_dict(self) -> None:
        result = OcrResult(template_id="invoice-001", page_index=0)
        result.add_result(self._make_field_result("amount", value=1000, confidence=0.95))
        detailed = result.to_detailed_dict()
        assert "amount" in detailed
        assert detailed["amount"]["confidence"] == 0.95


class TestDetermineReadingStatus:
    def test_high_confidence_confirmed(self) -> None:
        assert determine_reading_status(Confidence(0.9)) == ReadingStatus.CONFIRMED

    def test_low_confidence_needs_review(self) -> None:
        assert determine_reading_status(Confidence(0.5)) == ReadingStatus.NEEDS_REVIEW

    def test_custom_threshold(self) -> None:
        assert determine_reading_status(Confidence(0.8), threshold=0.9) == ReadingStatus.NEEDS_REVIEW


class TestValidateValueForType:
    def test_string(self) -> None:
        assert validate_value_for_type("hello", VariableType.STRING) == "hello"

    def test_number_integer(self) -> None:
        assert validate_value_for_type("1000", VariableType.NUMBER) == 1000

    def test_number_float(self) -> None:
        assert validate_value_for_type("1000.5", VariableType.NUMBER) == 1000.5

    def test_number_with_comma(self) -> None:
        assert validate_value_for_type("1,000", VariableType.NUMBER) == 1000

    def test_number_invalid(self) -> None:
        assert validate_value_for_type("abc", VariableType.NUMBER) is None

    def test_date_slash(self) -> None:
        assert validate_value_for_type("2026/03/08", VariableType.DATE) == "2026/03/08"

    def test_date_hyphen(self) -> None:
        assert validate_value_for_type("2026-03-08", VariableType.DATE) == "2026-03-08"

    def test_date_japanese(self) -> None:
        assert validate_value_for_type("2026年3月8日", VariableType.DATE) == "2026年3月8日"

    def test_date_invalid(self) -> None:
        assert validate_value_for_type("not a date", VariableType.DATE) is None

    def test_boolean_true(self) -> None:
        assert validate_value_for_type("○", VariableType.BOOLEAN) is True
        assert validate_value_for_type("true", VariableType.BOOLEAN) is True

    def test_boolean_false(self) -> None:
        assert validate_value_for_type("×", VariableType.BOOLEAN) is False

    def test_empty_string(self) -> None:
        assert validate_value_for_type("", VariableType.STRING) is None
        assert validate_value_for_type("  ", VariableType.NUMBER) is None


class TestBuildFieldResult:
    def test_high_confidence_confirmed(self) -> None:
        result = build_field_result(
            variable_name="amount",
            variable_type=VariableType.NUMBER,
            engine_result=OcrEngineResult(text="1000", confidence=0.95),
        )
        assert result.value == 1000
        assert result.status == ReadingStatus.CONFIRMED

    def test_low_confidence_needs_review(self) -> None:
        result = build_field_result(
            variable_name="amount",
            variable_type=VariableType.NUMBER,
            engine_result=OcrEngineResult(text="1000", confidence=0.5),
        )
        assert result.status == ReadingStatus.NEEDS_REVIEW

    def test_type_conversion_failure_needs_review(self) -> None:
        result = build_field_result(
            variable_name="amount",
            variable_type=VariableType.NUMBER,
            engine_result=OcrEngineResult(text="abc", confidence=0.9),
        )
        assert result.value is None
        assert result.status == ReadingStatus.NEEDS_REVIEW


class TestTomboDetectionResult:
    def test_sufficient(self) -> None:
        r = TomboDetectionResult(
            detected_points=(Point(5, 5), Point(205, 5), Point(5, 292)),
            detection_count=3,
        )
        assert r.is_sufficient
        assert not r.all_four_detected

    def test_all_four(self) -> None:
        r = TomboDetectionResult(
            detected_points=(Point(5, 5), Point(205, 5), Point(5, 292), Point(205, 292)),
            detection_count=4,
        )
        assert r.all_four_detected

    def test_insufficient(self) -> None:
        r = TomboDetectionResult(
            detected_points=(Point(5, 5), Point(205, 5)),
            detection_count=2,
        )
        assert not r.is_sufficient
