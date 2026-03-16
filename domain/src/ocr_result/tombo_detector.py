"""トンボ検出のインターフェース。

トンボ検出も差し替え可能にする（設計原則）。
「画像を渡したら4点の座標が返る」に統一する。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from domain.src.shared.coordinate import Point


@dataclass(frozen=True)
class TomboDetectionResult:
    """トンボ検出結果。"""

    detected_points: tuple[Point, ...]
    detection_count: int
    estimated_points: tuple[Point, ...] | None = None
    skew_degree: float | None = None
    aspect_ratio_error: float | None = None

    @property
    def is_sufficient(self) -> bool:
        """十分な検出数（3点以上）があるか。"""
        return self.detection_count >= 3

    @property
    def all_four_detected(self) -> bool:
        """4点すべて検出できたか。"""
        return self.detection_count == 4

    @property
    def four_points(self) -> tuple[Point, ...]:
        """射影変換に使う4点を返す（検出4点 or 推定込み4点）。"""
        if self.all_four_detected:
            return self.detected_points
        if self.estimated_points is not None:
            return self.estimated_points
        return self.detected_points


class TomboDetector(ABC):
    """トンボ検出の抽象基底クラス。

    デフォルト実装はハフ変換ベース（HoughTomboDetector）。
    将来的に他の手法に差し替えても、呼び出し側は変更不要。
    """

    @abstractmethod
    def detect(self, image: Any) -> TomboDetectionResult:
        """画像からトンボ4点の座標を検出する。

        Args:
            image: 撮影画像（numpy ndarray等）

        Returns:
            検出結果（検出座標、検出数、推定座標）
        """
