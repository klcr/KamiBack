"""射影変換のインターフェース。

射影変換も差し替え可能にする（設計原則）。
「画像と4点の対応を渡したら補正画像が返る」に統一する。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from domain.src.shared.coordinate import Point


@dataclass(frozen=True)
class PerspectiveCorrectionResult:
    """射影変換結果。"""

    corrected_image: Any
    scale_px_per_mm: float
    output_width_px: int
    output_height_px: int


class PerspectiveCorrector(ABC):
    """射影変換の抽象基底クラス。

    デフォルト実装はOpenCVベース（CvPerspectiveCorrector）。
    """

    @abstractmethod
    def correct(
        self,
        image: Any,
        src_points: tuple[Point, ...],
        dst_points_mm: tuple[Point, ...],
        output_size_mm: tuple[float, float],
    ) -> PerspectiveCorrectionResult:
        """検出4点から射影変換を適用し、補正画像を返す。

        Args:
            image: 入力画像（numpy ndarray）
            src_points: 検出されたトンボ4点（ピクセル座標、Point.x_mm/y_mmをpx値として使用）
            dst_points_mm: 目標トンボ4点（mm座標）
            output_size_mm: 出力サイズ (width_mm, height_mm)

        Returns:
            補正結果（補正画像、スケール係数、出力サイズ）
        """
