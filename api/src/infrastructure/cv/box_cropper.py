"""ボックス切出し。

マニフェストのabsoluteRegion（mm座標）をピクセルに変換し、
補正済み画像から各フィールドの矩形領域を切り出す。

単位変換は境界で1回だけ（設計原則）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from domain.src.shared.coordinate import Region


@dataclass(frozen=True)
class CropResult:
    """1フィールドの切出結果。"""

    box_image: NDArray[np.uint8]
    x_px: int
    y_px: int
    width_px: int
    height_px: int


class BoxCropper:
    """mm座標→ピクセル変換してボックスを切り出す。

    scale_px_per_mm は PerspectiveCorrectionResult から取得した値を使う（DJ-1）。
    """

    def __init__(self, scale_px_per_mm: float) -> None:
        if scale_px_per_mm <= 0:
            raise ValueError(f"scale_px_per_mm must be positive, got {scale_px_per_mm}")
        self._scale = scale_px_per_mm

    def crop(self, image: Any, region_mm: Region) -> CropResult:
        """補正画像からmm座標領域を切り出す。

        Args:
            image: 補正済み画像（numpy ndarray）
            region_mm: 切出領域（mm座標、absoluteRegion）

        Returns:
            切出結果（画像 + ピクセル座標）

        Raises:
            ValueError: 切出領域が画像範囲外の場合
        """
        img = _to_ndarray(image)
        img_h, img_w = img.shape[:2]

        x_px = int(round(region_mm.x_mm * self._scale))
        y_px = int(round(region_mm.y_mm * self._scale))
        w_px = int(round(region_mm.width_mm * self._scale))
        h_px = int(round(region_mm.height_mm * self._scale))

        # 画像範囲内にクランプ（端数丸めで1px程度はみ出す場合を許容）
        x_end = min(x_px + w_px, img_w)
        y_end = min(y_px + h_px, img_h)
        x_px = max(x_px, 0)
        y_px = max(y_px, 0)

        actual_w = x_end - x_px
        actual_h = y_end - y_px

        if actual_w <= 0 or actual_h <= 0:
            raise ValueError(
                f"Region {region_mm} at scale {self._scale} px/mm "
                f"results in empty crop (image: {img_w}x{img_h}px, "
                f"crop: x={x_px}, y={y_px}, w={actual_w}, h={actual_h})"
            )

        box_image = img[y_px:y_end, x_px:x_end].copy()

        return CropResult(
            box_image=box_image,
            x_px=x_px,
            y_px=y_px,
            width_px=actual_w,
            height_px=actual_h,
        )

    def crop_fields(self, image: Any, fields: list[tuple[str, Region]]) -> dict[str, CropResult]:
        """複数フィールドを一括で切り出す。

        Args:
            image: 補正済み画像
            fields: [(variable_name, absolute_region), ...]

        Returns:
            {variable_name: CropResult, ...}

        Raises:
            ValueError: いずれかのフィールドが画像範囲外の場合
        """
        results: dict[str, CropResult] = {}
        for variable_name, region_mm in fields:
            results[variable_name] = self.crop(image, region_mm)
        return results


def _to_ndarray(image: object) -> NDArray[np.uint8]:
    """入力をnumpy ndarrayに変換する。"""
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected numpy ndarray, got {type(image).__name__}")
    return image
