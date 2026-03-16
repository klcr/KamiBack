"""TomboDetectionResult のテスト。"""

from __future__ import annotations

from domain.src.ocr_result.tombo_detector import TomboDetectionResult
from domain.src.shared.coordinate import Point


class TestTomboDetectionResult:
    """TomboDetectionResult の基本プロパティをテスト。"""

    def test_four_points_detected(self) -> None:
        points = (
            Point(x_mm=10, y_mm=10),
            Point(x_mm=200, y_mm=10),
            Point(x_mm=10, y_mm=287),
            Point(x_mm=200, y_mm=287),
        )
        result = TomboDetectionResult(
            detected_points=points,
            detection_count=4,
        )
        assert result.is_sufficient is True
        assert result.all_four_detected is True
        assert result.four_points == points

    def test_three_points_with_estimation(self) -> None:
        detected = (
            Point(x_mm=10, y_mm=10),
            Point(x_mm=200, y_mm=10),
            Point(x_mm=10, y_mm=287),
        )
        estimated = (
            Point(x_mm=10, y_mm=10),
            Point(x_mm=200, y_mm=10),
            Point(x_mm=10, y_mm=287),
            Point(x_mm=200, y_mm=287),
        )
        result = TomboDetectionResult(
            detected_points=detected,
            detection_count=3,
            estimated_points=estimated,
        )
        assert result.is_sufficient is True
        assert result.all_four_detected is False
        assert result.four_points == estimated

    def test_three_points_without_estimation(self) -> None:
        detected = (
            Point(x_mm=10, y_mm=10),
            Point(x_mm=200, y_mm=10),
            Point(x_mm=10, y_mm=287),
        )
        result = TomboDetectionResult(
            detected_points=detected,
            detection_count=3,
        )
        assert result.four_points == detected

    def test_insufficient_detection(self) -> None:
        result = TomboDetectionResult(
            detected_points=(Point(x_mm=10, y_mm=10),),
            detection_count=1,
        )
        assert result.is_sufficient is False
        assert result.all_four_detected is False

    def test_skew_degree_and_aspect_ratio_error(self) -> None:
        result = TomboDetectionResult(
            detected_points=(Point(x_mm=10, y_mm=10),),
            detection_count=3,
            skew_degree=2.5,
            aspect_ratio_error=3.1,
        )
        assert result.skew_degree == 2.5
        assert result.aspect_ratio_error == 3.1

    def test_skew_fields_default_none(self) -> None:
        result = TomboDetectionResult(
            detected_points=(),
            detection_count=0,
        )
        assert result.skew_degree is None
        assert result.aspect_ratio_error is None
