"""OpenCVベースの射影変換。

検出4点とマニフェスト上のトンボmm座標を対応づけ、
getPerspectiveTransform + warpPerspective で補正する。
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray

from domain.src.ocr_result.perspective_corrector import (
    PerspectiveCorrectionResult,
    PerspectiveCorrector,
)
from domain.src.shared.coordinate import Point


class CvPerspectiveCorrector(PerspectiveCorrector):
    """OpenCVによる射影変換実装。

    スケール係数（px/mm）でmm座標をピクセルに変換し、
    射影変換行列を算出して画像を補正する。
    """

    def __init__(self, default_scale_px_per_mm: float = 10.0) -> None:
        if default_scale_px_per_mm <= 0:
            raise ValueError("scale must be positive")
        self._scale = default_scale_px_per_mm

    def correct(
        self,
        image: Any,
        src_points: tuple[Point, ...],
        dst_points_mm: tuple[Point, ...],
        output_size_mm: tuple[float, float],
    ) -> PerspectiveCorrectionResult:
        """射影変換を適用して補正画像を返す。"""
        if len(src_points) != 4:
            raise ValueError(f"src_points must have exactly 4 points, got {len(src_points)}")
        if len(dst_points_mm) != 4:
            raise ValueError(f"dst_points_mm must have exactly 4 points, got {len(dst_points_mm)}")

        img = _to_ndarray(image)

        src = np.array(
            [[p.x_mm, p.y_mm] for p in src_points],
            dtype=np.float32,
        )
        dst = np.array(
            [[p.x_mm * self._scale, p.y_mm * self._scale] for p in dst_points_mm],
            dtype=np.float32,
        )

        output_w = int(output_size_mm[0] * self._scale)
        output_h = int(output_size_mm[1] * self._scale)

        matrix = cv2.getPerspectiveTransform(src, dst)
        corrected = cv2.warpPerspective(img, matrix, (output_w, output_h), flags=cv2.INTER_LINEAR)

        return PerspectiveCorrectionResult(
            corrected_image=corrected,
            scale_px_per_mm=self._scale,
            output_width_px=output_w,
            output_height_px=output_h,
        )


def _to_ndarray(image: object) -> NDArray[np.uint8]:
    """入力をnumpy ndarrayに変換する。"""
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected numpy ndarray, got {type(image).__name__}")
    return image
