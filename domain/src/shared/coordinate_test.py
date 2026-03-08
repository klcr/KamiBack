"""coordinate.py のユニットテスト。"""

from __future__ import annotations

import pytest

from domain.src.shared.coordinate import Point, Region, Size


class TestPoint:
    def test_creation(self) -> None:
        p = Point(x_mm=10.0, y_mm=20.0)
        assert p.x_mm == 10.0
        assert p.y_mm == 20.0

    def test_immutable(self) -> None:
        p = Point(x_mm=10.0, y_mm=20.0)
        with pytest.raises(AttributeError):
            p.x_mm = 30.0  # type: ignore[misc]

    def test_equality(self) -> None:
        assert Point(1.0, 2.0) == Point(1.0, 2.0)
        assert Point(1.0, 2.0) != Point(1.0, 3.0)

    def test_zero_coordinates(self) -> None:
        p = Point(x_mm=0.0, y_mm=0.0)
        assert p.x_mm == 0.0
        assert p.y_mm == 0.0

    def test_negative_coordinates(self) -> None:
        p = Point(x_mm=-5.0, y_mm=-10.0)
        assert p.x_mm == -5.0

    def test_type_error(self) -> None:
        with pytest.raises(TypeError):
            Point(x_mm="10", y_mm=20.0)  # type: ignore[arg-type]


class TestSize:
    def test_creation(self) -> None:
        s = Size(width_mm=100.0, height_mm=50.0)
        assert s.width_mm == 100.0
        assert s.height_mm == 50.0

    def test_zero_width_raises(self) -> None:
        with pytest.raises(ValueError, match="width_mm must be positive"):
            Size(width_mm=0, height_mm=50.0)

    def test_negative_height_raises(self) -> None:
        with pytest.raises(ValueError, match="height_mm must be positive"):
            Size(width_mm=100.0, height_mm=-1.0)


class TestRegion:
    def test_creation(self) -> None:
        r = Region(x_mm=10.0, y_mm=20.0, width_mm=60.0, height_mm=8.0)
        assert r.x_mm == 10.0
        assert r.width_mm == 60.0

    def test_top_left(self) -> None:
        r = Region(x_mm=10.0, y_mm=20.0, width_mm=60.0, height_mm=8.0)
        assert r.top_left == Point(10.0, 20.0)

    def test_bottom_right(self) -> None:
        r = Region(x_mm=10.0, y_mm=20.0, width_mm=60.0, height_mm=8.0)
        assert r.bottom_right == Point(70.0, 28.0)

    def test_size(self) -> None:
        r = Region(x_mm=10.0, y_mm=20.0, width_mm=60.0, height_mm=8.0)
        assert r.size == Size(60.0, 8.0)

    def test_contains_inside(self) -> None:
        r = Region(x_mm=10.0, y_mm=20.0, width_mm=60.0, height_mm=8.0)
        assert r.contains(Point(30.0, 24.0))

    def test_contains_on_edge(self) -> None:
        r = Region(x_mm=10.0, y_mm=20.0, width_mm=60.0, height_mm=8.0)
        assert r.contains(Point(10.0, 20.0))
        assert r.contains(Point(70.0, 28.0))

    def test_contains_outside(self) -> None:
        r = Region(x_mm=10.0, y_mm=20.0, width_mm=60.0, height_mm=8.0)
        assert not r.contains(Point(5.0, 24.0))
        assert not r.contains(Point(30.0, 30.0))

    def test_negative_width_raises(self) -> None:
        with pytest.raises(ValueError):
            Region(x_mm=10.0, y_mm=20.0, width_mm=-1.0, height_mm=8.0)
