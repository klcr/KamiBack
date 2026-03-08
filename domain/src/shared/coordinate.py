"""mm座標系の値オブジェクト。

全ての寸法値はmm単位。座標変換（mm→ピクセル、mm→CSS）は
アプリケーション層の境界で1回だけ行う（設計原則: 単位変換は境界で1回だけ）。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    """mm座標上の点。"""

    x_mm: float
    y_mm: float

    def __post_init__(self) -> None:
        if not isinstance(self.x_mm, (int, float)):
            raise TypeError(f"x_mm must be numeric, got {type(self.x_mm).__name__}")
        if not isinstance(self.y_mm, (int, float)):
            raise TypeError(f"y_mm must be numeric, got {type(self.y_mm).__name__}")


@dataclass(frozen=True)
class Size:
    """mm単位のサイズ（幅×高さ）。"""

    width_mm: float
    height_mm: float

    def __post_init__(self) -> None:
        if self.width_mm <= 0:
            raise ValueError(f"width_mm must be positive, got {self.width_mm}")
        if self.height_mm <= 0:
            raise ValueError(f"height_mm must be positive, got {self.height_mm}")


@dataclass(frozen=True)
class Region:
    """mm座標上の矩形領域（左上原点）。"""

    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float

    def __post_init__(self) -> None:
        if self.width_mm <= 0:
            raise ValueError(f"width_mm must be positive, got {self.width_mm}")
        if self.height_mm <= 0:
            raise ValueError(f"height_mm must be positive, got {self.height_mm}")

    @property
    def top_left(self) -> Point:
        return Point(x_mm=self.x_mm, y_mm=self.y_mm)

    @property
    def bottom_right(self) -> Point:
        return Point(
            x_mm=self.x_mm + self.width_mm,
            y_mm=self.y_mm + self.height_mm,
        )

    @property
    def size(self) -> Size:
        return Size(width_mm=self.width_mm, height_mm=self.height_mm)

    def contains(self, point: Point) -> bool:
        """指定した点がこの領域内にあるかを判定する。"""
        return (
            self.x_mm <= point.x_mm <= self.x_mm + self.width_mm
            and self.y_mm <= point.y_mm <= self.y_mm + self.height_mm
        )
