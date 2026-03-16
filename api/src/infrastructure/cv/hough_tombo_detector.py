"""ハフ変換ベースのトンボ検出。

古典的CV手法のみ使用（設計原則: 事前学習に依存しない）。
円検出 + 十字線交差点のサブピクセル特定でトンボ中心を求める。
"""

from __future__ import annotations

import math
from enum import Enum

import cv2
import numpy as np
from numpy.typing import NDArray

from domain.src.ocr_result.tombo_detector import TomboDetectionResult, TomboDetector
from domain.src.shared.coordinate import Point


class Corner(Enum):
    """用紙四隅の識別子。"""

    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


class HoughTomboDetector(TomboDetector):
    """ハフ変換によるトンボ（circle_cross型）検出器。

    アルゴリズム:
    1. グレースケール + ブラーでノイズ除去
    2. HoughCircles で円候補を検出
    3. 各円の近傍で HoughLinesP により十字線を検出
    4. 十字線の交差点をサブピクセル精度で算出
    5. 検出点を画像の四隅に分類
    """

    def __init__(
        self,
        paper_width_mm: float,
        paper_height_mm: float,
        tombo_radius_mm: float = 3.0,
        skew_threshold_deg: float = 5.0,
        aspect_ratio_threshold_pct: float = 10.0,
    ) -> None:
        self._paper_width_mm = paper_width_mm
        self._paper_height_mm = paper_height_mm
        self._tombo_radius_mm = tombo_radius_mm
        self._skew_threshold_deg = skew_threshold_deg
        self._aspect_ratio_threshold_pct = aspect_ratio_threshold_pct

    def detect(self, image: object) -> TomboDetectionResult:
        """画像からトンボ4点を検出する。"""
        img = _to_ndarray(image)
        gray = _to_grayscale(img)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        circles = _detect_circles(blurred)
        if len(circles) == 0:
            return TomboDetectionResult(detected_points=(), detection_count=0)

        tombo_centers: list[tuple[float, float]] = []
        for cx, cy, radius in circles:
            center = _detect_cross_center(blurred, cx, cy, radius)
            if center is not None:
                tombo_centers.append(center)

        if len(tombo_centers) == 0:
            return TomboDetectionResult(detected_points=(), detection_count=0)

        classified = _classify_corners(tombo_centers, img.shape[:2])
        detected_points = tuple(Point(x_mm=x, y_mm=y) for x, y in classified.values())
        detection_count = len(classified)

        if detection_count == 4:
            return TomboDetectionResult(
                detected_points=detected_points,
                detection_count=4,
            )

        if detection_count == 3:
            return self._handle_three_points(classified)

        return TomboDetectionResult(
            detected_points=detected_points,
            detection_count=detection_count,
        )

    def _handle_three_points(self, classified: dict[Corner, tuple[float, float]]) -> TomboDetectionResult:
        """3点検出時に4点目を幾何推定し、歪み判定する。"""
        all_corners = {Corner.TOP_LEFT, Corner.TOP_RIGHT, Corner.BOTTOM_LEFT, Corner.BOTTOM_RIGHT}
        missing = (all_corners - set(classified.keys())).pop()
        three_points = classified

        estimated_xy = _estimate_fourth_point(three_points, missing)
        all_four = dict(three_points)
        all_four[missing] = estimated_xy

        skew = _calculate_skew_degree(all_four)
        ar_error = _calculate_aspect_ratio_error(all_four, self._paper_width_mm / self._paper_height_mm)

        detected_points = tuple(Point(x_mm=x, y_mm=y) for x, y in three_points.values())
        ordered_four = _ordered_points(all_four)
        estimated_points = tuple(Point(x_mm=x, y_mm=y) for x, y in ordered_four)

        is_within_threshold = skew <= self._skew_threshold_deg and ar_error <= self._aspect_ratio_threshold_pct

        if not is_within_threshold:
            return TomboDetectionResult(
                detected_points=detected_points,
                detection_count=3,
                estimated_points=None,
                skew_degree=skew,
                aspect_ratio_error=ar_error,
            )

        return TomboDetectionResult(
            detected_points=detected_points,
            detection_count=3,
            estimated_points=estimated_points,
            skew_degree=skew,
            aspect_ratio_error=ar_error,
        )


def _to_ndarray(image: object) -> NDArray[np.uint8]:
    """入力をnumpy ndarrayに変換する。"""
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected numpy ndarray, got {type(image).__name__}")
    return image


def _to_grayscale(img: NDArray[np.uint8]) -> NDArray[np.uint8]:
    """グレースケールに変換する（既にグレーならそのまま）。"""
    if len(img.shape) == 2:
        return img
    result: NDArray[np.uint8] = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return result


def _detect_circles(
    gray: NDArray[np.uint8],
    dp: float = 1.2,
    min_dist: int = 50,
    param1: int = 100,
    param2: int = 30,
    min_radius: int = 10,
    max_radius: int = 80,
) -> list[tuple[float, float, float]]:
    """ハフ変換で円を検出する。"""
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=dp,
        minDist=min_dist,
        param1=param1,
        param2=param2,
        minRadius=min_radius,
        maxRadius=max_radius,
    )
    if circles is None:
        return []
    return [(float(c[0]), float(c[1]), float(c[2])) for c in circles[0]]


def _detect_cross_center(
    gray: NDArray[np.uint8],
    cx: float,
    cy: float,
    radius: float,
) -> tuple[float, float] | None:
    """円近傍で十字線の交差点を検出する。"""
    margin = int(radius * 1.5)
    h, w = gray.shape[:2]
    x1 = max(0, int(cx - margin))
    y1 = max(0, int(cy - margin))
    x2 = min(w, int(cx + margin))
    y2 = min(h, int(cy + margin))

    roi = gray[y1:y2, x1:x2]
    if roi.size == 0:
        return None

    edges = cv2.Canny(roi, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=20, minLineLength=int(radius * 0.8), maxLineGap=5)

    if lines is None or len(lines) < 2:
        return (cx, cy)

    horizontal: list[tuple[int, int, int, int]] = []
    vertical: list[tuple[int, int, int, int]] = []

    for line in lines:
        lx1, ly1, lx2, ly2 = line[0]
        angle = abs(math.atan2(ly2 - ly1, lx2 - lx1))
        if angle < math.pi / 6:
            horizontal.append((lx1, ly1, lx2, ly2))
        elif angle > math.pi / 3:
            vertical.append((lx1, ly1, lx2, ly2))

    if not horizontal or not vertical:
        return (cx, cy)

    h_line = horizontal[0]
    v_line = vertical[0]
    intersection = _line_intersection(h_line, v_line)
    if intersection is None:
        return (cx, cy)

    ix, iy = intersection
    return (ix + x1, iy + y1)


def _line_intersection(
    line1: tuple[int, int, int, int],
    line2: tuple[int, int, int, int],
) -> tuple[float, float] | None:
    """2直線の交点を算出する。"""
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    ix = x1 + t * (x2 - x1)
    iy = y1 + t * (y2 - y1)
    return (ix, iy)


def _classify_corners(
    points: list[tuple[float, float]],
    image_shape: tuple[int, ...],
) -> dict[Corner, tuple[float, float]]:
    """検出点を用紙四隅に分類する（画像の中心からの相対位置）。"""
    h, w = image_shape[0], image_shape[1]
    mid_x, mid_y = w / 2.0, h / 2.0

    result: dict[Corner, tuple[float, float]] = {}
    assigned: set[int] = set()

    corner_conditions: list[tuple[Corner, bool, bool]] = [
        (Corner.TOP_LEFT, False, False),
        (Corner.TOP_RIGHT, True, False),
        (Corner.BOTTOM_LEFT, False, True),
        (Corner.BOTTOM_RIGHT, True, True),
    ]

    for corner, is_right, is_bottom in corner_conditions:
        best_idx = -1
        best_dist = float("inf")
        target_x = w if is_right else 0.0
        target_y = h if is_bottom else 0.0

        for i, (px, py) in enumerate(points):
            if i in assigned:
                continue
            in_correct_half_x = (px >= mid_x) == is_right
            in_correct_half_y = (py >= mid_y) == is_bottom
            if in_correct_half_x and in_correct_half_y:
                dist = math.hypot(px - target_x, py - target_y)
                if dist < best_dist:
                    best_dist = dist
                    best_idx = i

        if best_idx >= 0:
            result[corner] = points[best_idx]
            assigned.add(best_idx)

    return result


def _estimate_fourth_point(
    three_points: dict[Corner, tuple[float, float]],
    missing: Corner,
) -> tuple[float, float]:
    """3点から欠落隅の座標を推定する。"""
    if missing == Corner.TOP_LEFT:
        tl_x = three_points[Corner.BOTTOM_LEFT][0]
        tl_y = three_points[Corner.TOP_RIGHT][1]
        return (tl_x, tl_y)
    if missing == Corner.TOP_RIGHT:
        tr_x = three_points[Corner.BOTTOM_RIGHT][0]
        tr_y = three_points[Corner.TOP_LEFT][1]
        return (tr_x, tr_y)
    if missing == Corner.BOTTOM_LEFT:
        bl_x = three_points[Corner.TOP_LEFT][0]
        bl_y = three_points[Corner.BOTTOM_RIGHT][1]
        return (bl_x, bl_y)
    # BOTTOM_RIGHT
    br_x = three_points[Corner.TOP_RIGHT][0]
    br_y = three_points[Corner.BOTTOM_LEFT][1]
    return (br_x, br_y)


def _calculate_skew_degree(four_points: dict[Corner, tuple[float, float]]) -> float:
    """4点から構成される角度の直角からの最大偏差（度数）を算出する。"""
    tl = four_points[Corner.TOP_LEFT]
    tr = four_points[Corner.TOP_RIGHT]
    bl = four_points[Corner.BOTTOM_LEFT]
    br = four_points[Corner.BOTTOM_RIGHT]

    corners_triplets = [
        (bl, tl, tr),  # TLでの角度
        (tl, tr, br),  # TRでの角度
        (tr, br, bl),  # BRでの角度
        (br, bl, tl),  # BLでの角度
    ]

    max_deviation = 0.0
    for p1, vertex, p2 in corners_triplets:
        v1 = (p1[0] - vertex[0], p1[1] - vertex[1])
        v2 = (p2[0] - vertex[0], p2[1] - vertex[1])
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        mag1 = math.hypot(v1[0], v1[1])
        mag2 = math.hypot(v2[0], v2[1])
        if mag1 < 1e-10 or mag2 < 1e-10:
            continue
        cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
        angle_deg = math.degrees(math.acos(cos_angle))
        deviation = abs(angle_deg - 90.0)
        max_deviation = max(max_deviation, deviation)

    return max_deviation


def _calculate_aspect_ratio_error(
    four_points: dict[Corner, tuple[float, float]],
    expected_ratio: float,
) -> float:
    """推定4点で構成される矩形のアスペクト比と期待値の誤差（%）。"""
    tl = four_points[Corner.TOP_LEFT]
    tr = four_points[Corner.TOP_RIGHT]
    bl = four_points[Corner.BOTTOM_LEFT]

    width = math.hypot(tr[0] - tl[0], tr[1] - tl[1])
    height = math.hypot(bl[0] - tl[0], bl[1] - tl[1])

    if height < 1e-10:
        return 100.0

    actual_ratio = width / height
    return abs(actual_ratio - expected_ratio) / expected_ratio * 100.0


def _ordered_points(
    four_points: dict[Corner, tuple[float, float]],
) -> list[tuple[float, float]]:
    """TL, TR, BL, BR の順に整列する。"""
    return [
        four_points[Corner.TOP_LEFT],
        four_points[Corner.TOP_RIGHT],
        four_points[Corner.BOTTOM_LEFT],
        four_points[Corner.BOTTOM_RIGHT],
    ]
