"""CvPerspectiveCorrector のテスト。"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from api.src.infrastructure.cv.perspective_corrector import CvPerspectiveCorrector
from domain.src.shared.coordinate import Point


class TestCvPerspectiveCorrector:
    """射影変換のテスト。"""

    def test_correct_identity_transform(self) -> None:
        """ソースと宛先が同一スケールなら画像サイズが期待通り。"""
        img = np.ones((300, 200, 3), dtype=np.uint8) * 128

        corrector = CvPerspectiveCorrector(default_scale_px_per_mm=1.0)
        src = (
            Point(x_mm=0, y_mm=0),
            Point(x_mm=200, y_mm=0),
            Point(x_mm=0, y_mm=300),
            Point(x_mm=200, y_mm=300),
        )
        dst_mm = (
            Point(x_mm=0, y_mm=0),
            Point(x_mm=200, y_mm=0),
            Point(x_mm=0, y_mm=300),
            Point(x_mm=200, y_mm=300),
        )
        result = corrector.correct(img, src, dst_mm, (200.0, 300.0))

        assert result.output_width_px == 200
        assert result.output_height_px == 300
        assert result.scale_px_per_mm == 1.0
        assert result.corrected_image.shape[:2] == (300, 200)

    def test_correct_with_scale(self) -> None:
        """スケール係数でmm→pxが正しく変換される。"""
        img = np.ones((500, 400, 3), dtype=np.uint8) * 200

        corrector = CvPerspectiveCorrector(default_scale_px_per_mm=5.0)
        src = (
            Point(x_mm=0, y_mm=0),
            Point(x_mm=400, y_mm=0),
            Point(x_mm=0, y_mm=500),
            Point(x_mm=400, y_mm=500),
        )
        dst_mm = (
            Point(x_mm=0, y_mm=0),
            Point(x_mm=80, y_mm=0),
            Point(x_mm=0, y_mm=100),
            Point(x_mm=80, y_mm=100),
        )
        result = corrector.correct(img, src, dst_mm, (80.0, 100.0))

        assert result.output_width_px == 400
        assert result.output_height_px == 500
        assert result.scale_px_per_mm == 5.0

    def test_correct_trapezoid_to_rectangle(self) -> None:
        """台形画像を矩形に補正する。"""
        img = np.ones((600, 400, 3), dtype=np.uint8) * 255

        cv2.fillConvexPoly(
            img,
            np.array([[50, 50], [350, 30], [370, 550], [30, 570]], dtype=np.int32),
            (100, 100, 100),
        )

        corrector = CvPerspectiveCorrector(default_scale_px_per_mm=1.0)
        src = (
            Point(x_mm=50, y_mm=50),
            Point(x_mm=350, y_mm=30),
            Point(x_mm=30, y_mm=570),
            Point(x_mm=370, y_mm=550),
        )
        dst_mm = (
            Point(x_mm=0, y_mm=0),
            Point(x_mm=300, y_mm=0),
            Point(x_mm=0, y_mm=500),
            Point(x_mm=300, y_mm=500),
        )
        result = corrector.correct(img, src, dst_mm, (300.0, 500.0))

        assert result.corrected_image.shape[:2] == (500, 300)

    def test_reject_non_four_src_points(self) -> None:
        img = np.ones((100, 100), dtype=np.uint8)
        corrector = CvPerspectiveCorrector()
        dst = (Point(x_mm=0, y_mm=0),) * 4
        with pytest.raises(ValueError, match="src_points must have exactly 4"):
            corrector.correct(img, (Point(x_mm=0, y_mm=0),) * 3, dst, (100.0, 100.0))

    def test_reject_non_four_dst_points(self) -> None:
        img = np.ones((100, 100), dtype=np.uint8)
        corrector = CvPerspectiveCorrector()
        src = (Point(x_mm=0, y_mm=0),) * 4
        with pytest.raises(ValueError, match="dst_points_mm must have exactly 4"):
            corrector.correct(img, src, (Point(x_mm=0, y_mm=0),) * 2, (100.0, 100.0))

    def test_reject_non_ndarray(self) -> None:
        corrector = CvPerspectiveCorrector()
        src = (Point(x_mm=0, y_mm=0),) * 4
        dst = (Point(x_mm=0, y_mm=0),) * 4
        with pytest.raises(TypeError):
            corrector.correct("not an image", src, dst, (100.0, 100.0))

    def test_reject_negative_scale(self) -> None:
        with pytest.raises(ValueError, match="scale must be positive"):
            CvPerspectiveCorrector(default_scale_px_per_mm=-1.0)

    def test_grayscale_image(self) -> None:
        """グレースケール画像でも動作する。"""
        img = np.ones((300, 200), dtype=np.uint8) * 128
        corrector = CvPerspectiveCorrector(default_scale_px_per_mm=1.0)
        src = (
            Point(x_mm=0, y_mm=0),
            Point(x_mm=200, y_mm=0),
            Point(x_mm=0, y_mm=300),
            Point(x_mm=200, y_mm=300),
        )
        dst_mm = src
        result = corrector.correct(img, src, dst_mm, (200.0, 300.0))
        assert result.corrected_image.shape == (300, 200)
