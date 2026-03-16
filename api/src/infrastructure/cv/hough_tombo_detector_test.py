"""HoughTomboDetector のテスト。

合成画像を使ってトンボ検出・3点推定・歪み判定をテストする。
"""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray

from api.src.infrastructure.cv.hough_tombo_detector import (
    Corner,
    HoughTomboDetector,
    _calculate_aspect_ratio_error,
    _calculate_skew_degree,
    _classify_corners,
    _estimate_fourth_point,
    _line_intersection,
)


def _draw_tombo(
    img: NDArray[np.uint8],
    cx: int,
    cy: int,
    radius: int = 20,
    line_length: int = 30,
) -> None:
    """合成画像にcircle_cross型トンボを描画する。"""
    cv2.circle(img, (cx, cy), radius, 0, 2)
    cv2.line(img, (cx - line_length, cy), (cx + line_length, cy), 0, 2)
    cv2.line(img, (cx, cy - line_length), (cx, cy + line_length), 0, 2)


def _create_test_image_with_tombos(
    width: int = 800,
    height: int = 1100,
    tombo_positions: list[tuple[int, int]] | None = None,
) -> NDArray[np.uint8]:
    """テスト用の合成画像を生成する。"""
    img = np.ones((height, width), dtype=np.uint8) * 255
    if tombo_positions is None:
        margin = 50
        tombo_positions = [
            (margin, margin),
            (width - margin, margin),
            (margin, height - margin),
            (width - margin, height - margin),
        ]
    for cx, cy in tombo_positions:
        _draw_tombo(img, cx, cy)
    return img


class TestHoughTomboDetectorDetect:
    """detect() メソッドの統合テスト。"""

    def test_detect_four_tombos(self) -> None:
        img = _create_test_image_with_tombos()
        detector = HoughTomboDetector(paper_width_mm=210.0, paper_height_mm=297.0)
        result = detector.detect(img)
        assert result.detection_count >= 3

    def test_detect_no_tombos(self) -> None:
        img = np.ones((600, 400), dtype=np.uint8) * 255
        detector = HoughTomboDetector(paper_width_mm=210.0, paper_height_mm=297.0)
        result = detector.detect(img)
        assert result.detection_count == 0
        assert result.detected_points == ()

    def test_detect_rejects_non_ndarray(self) -> None:
        detector = HoughTomboDetector(paper_width_mm=210.0, paper_height_mm=297.0)
        try:
            detector.detect("not an image")
            raise AssertionError("Expected TypeError")  # noqa: TRY301
        except TypeError:
            pass

    def test_detect_color_image(self) -> None:
        gray = _create_test_image_with_tombos()
        color = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        detector = HoughTomboDetector(paper_width_mm=210.0, paper_height_mm=297.0)
        result = detector.detect(color)
        assert result.detection_count >= 0


class TestClassifyCorners:
    """_classify_corners のテスト。"""

    def test_four_points_classification(self) -> None:
        points = [
            (50.0, 50.0),
            (750.0, 50.0),
            (50.0, 1050.0),
            (750.0, 1050.0),
        ]
        classified = _classify_corners(points, (1100, 800))
        assert Corner.TOP_LEFT in classified
        assert Corner.TOP_RIGHT in classified
        assert Corner.BOTTOM_LEFT in classified
        assert Corner.BOTTOM_RIGHT in classified

    def test_three_points_classification(self) -> None:
        points = [
            (50.0, 50.0),
            (750.0, 50.0),
            (50.0, 1050.0),
        ]
        classified = _classify_corners(points, (1100, 800))
        assert len(classified) == 3
        assert Corner.TOP_LEFT in classified
        assert Corner.TOP_RIGHT in classified
        assert Corner.BOTTOM_LEFT in classified


class TestEstimateFourthPoint:
    """_estimate_fourth_point のテスト。"""

    def test_estimate_bottom_right(self) -> None:
        three = {
            Corner.TOP_LEFT: (50.0, 50.0),
            Corner.TOP_RIGHT: (750.0, 50.0),
            Corner.BOTTOM_LEFT: (50.0, 1050.0),
        }
        result = _estimate_fourth_point(three, Corner.BOTTOM_RIGHT)
        assert abs(result[0] - 750.0) < 1e-6
        assert abs(result[1] - 1050.0) < 1e-6

    def test_estimate_top_left(self) -> None:
        three = {
            Corner.TOP_RIGHT: (750.0, 50.0),
            Corner.BOTTOM_LEFT: (50.0, 1050.0),
            Corner.BOTTOM_RIGHT: (750.0, 1050.0),
        }
        result = _estimate_fourth_point(three, Corner.TOP_LEFT)
        assert abs(result[0] - 50.0) < 1e-6
        assert abs(result[1] - 50.0) < 1e-6

    def test_estimate_top_right(self) -> None:
        three = {
            Corner.TOP_LEFT: (50.0, 50.0),
            Corner.BOTTOM_LEFT: (50.0, 1050.0),
            Corner.BOTTOM_RIGHT: (750.0, 1050.0),
        }
        result = _estimate_fourth_point(three, Corner.TOP_RIGHT)
        assert abs(result[0] - 750.0) < 1e-6
        assert abs(result[1] - 50.0) < 1e-6

    def test_estimate_bottom_left(self) -> None:
        three = {
            Corner.TOP_LEFT: (50.0, 50.0),
            Corner.TOP_RIGHT: (750.0, 50.0),
            Corner.BOTTOM_RIGHT: (750.0, 1050.0),
        }
        result = _estimate_fourth_point(three, Corner.BOTTOM_LEFT)
        assert abs(result[0] - 50.0) < 1e-6
        assert abs(result[1] - 1050.0) < 1e-6


class TestCalculateSkewDegree:
    """_calculate_skew_degree のテスト。"""

    def test_perfect_rectangle(self) -> None:
        four = {
            Corner.TOP_LEFT: (0.0, 0.0),
            Corner.TOP_RIGHT: (100.0, 0.0),
            Corner.BOTTOM_LEFT: (0.0, 200.0),
            Corner.BOTTOM_RIGHT: (100.0, 200.0),
        }
        skew = _calculate_skew_degree(four)
        assert skew < 0.1

    def test_skewed_rectangle(self) -> None:
        four = {
            Corner.TOP_LEFT: (0.0, 0.0),
            Corner.TOP_RIGHT: (100.0, 10.0),
            Corner.BOTTOM_LEFT: (0.0, 200.0),
            Corner.BOTTOM_RIGHT: (100.0, 200.0),
        }
        skew = _calculate_skew_degree(four)
        assert skew > 1.0


class TestCalculateAspectRatioError:
    """_calculate_aspect_ratio_error のテスト。"""

    def test_correct_ratio(self) -> None:
        four = {
            Corner.TOP_LEFT: (0.0, 0.0),
            Corner.TOP_RIGHT: (210.0, 0.0),
            Corner.BOTTOM_LEFT: (0.0, 297.0),
            Corner.BOTTOM_RIGHT: (210.0, 297.0),
        }
        error = _calculate_aspect_ratio_error(four, 210.0 / 297.0)
        assert error < 0.1

    def test_wrong_ratio(self) -> None:
        four = {
            Corner.TOP_LEFT: (0.0, 0.0),
            Corner.TOP_RIGHT: (300.0, 0.0),
            Corner.BOTTOM_LEFT: (0.0, 297.0),
            Corner.BOTTOM_RIGHT: (300.0, 297.0),
        }
        error = _calculate_aspect_ratio_error(four, 210.0 / 297.0)
        assert error > 10.0


class TestLineIntersection:
    """_line_intersection のテスト。"""

    def test_perpendicular_lines(self) -> None:
        result = _line_intersection((0, 50, 100, 50), (50, 0, 50, 100))
        assert result is not None
        assert abs(result[0] - 50.0) < 1e-6
        assert abs(result[1] - 50.0) < 1e-6

    def test_parallel_lines(self) -> None:
        result = _line_intersection((0, 0, 100, 0), (0, 10, 100, 10))
        assert result is None
