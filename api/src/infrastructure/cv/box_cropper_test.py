"""BoxCropperのテスト。"""

from __future__ import annotations

import numpy as np
import pytest

from domain.src.shared.coordinate import Region

from .box_cropper import BoxCropper, CropResult


class TestBoxCropperInit:
    """コンストラクタのバリデーション。"""

    def test_valid_scale(self) -> None:
        cropper = BoxCropper(scale_px_per_mm=10.0)
        assert cropper._scale == 10.0

    def test_zero_scale_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            BoxCropper(scale_px_per_mm=0)

    def test_negative_scale_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            BoxCropper(scale_px_per_mm=-5.0)


class TestBoxCropperCrop:
    """単一フィールドの切出し。"""

    def _make_image(self, width: int, height: int) -> np.ndarray:
        """テスト画像を生成する。各ピクセルの値が座標から計算可能。"""
        img = np.zeros((height, width), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                img[y, x] = (x + y) % 256
        return img

    def test_basic_crop(self) -> None:
        """基本的な切出し（10px/mm、10x5mmの領域）。"""
        img = self._make_image(200, 300)
        cropper = BoxCropper(scale_px_per_mm=10.0)

        region = Region(x_mm=5.0, y_mm=10.0, width_mm=10.0, height_mm=5.0)
        result = cropper.crop(img, region)

        assert result.x_px == 50
        assert result.y_px == 100
        assert result.width_px == 100
        assert result.height_px == 50
        assert result.box_image.shape == (50, 100)

    def test_crop_content_matches_source(self) -> None:
        """切出し画像の内容がソース画像の対応領域と一致する。"""
        img = self._make_image(200, 300)
        cropper = BoxCropper(scale_px_per_mm=10.0)

        region = Region(x_mm=2.0, y_mm=3.0, width_mm=5.0, height_mm=4.0)
        result = cropper.crop(img, region)

        expected = img[30:70, 20:70]
        np.testing.assert_array_equal(result.box_image, expected)

    def test_crop_is_copy(self) -> None:
        """切出し画像はソースのコピー（元画像を変更しない）。"""
        img = self._make_image(100, 100)
        cropper = BoxCropper(scale_px_per_mm=10.0)

        region = Region(x_mm=0.0, y_mm=0.0, width_mm=5.0, height_mm=5.0)
        result = cropper.crop(img, region)

        result.box_image[0, 0] = 255
        assert img[0, 0] != 255 or img[0, 0] == 0  # 元画像は0のまま

    def test_crop_with_fractional_scale(self) -> None:
        """非整数スケールでの切出し。"""
        img = self._make_image(200, 200)
        cropper = BoxCropper(scale_px_per_mm=7.5)

        region = Region(x_mm=4.0, y_mm=4.0, width_mm=8.0, height_mm=6.0)
        result = cropper.crop(img, region)

        # 4.0mm * 7.5 = 30px, 8.0mm * 7.5 = 60px, 6.0mm * 7.5 = 45px
        assert result.x_px == 30
        assert result.y_px == 30
        assert result.width_px == 60
        assert result.height_px == 45

    def test_crop_clamps_to_image_boundary(self) -> None:
        """画像端で端数丸めにより1px程度はみ出す場合はクランプする。"""
        img = self._make_image(100, 100)
        cropper = BoxCropper(scale_px_per_mm=10.0)

        # 9mm + 2mm = 11mm → 110px > 100px → クランプ
        region = Region(x_mm=9.0, y_mm=9.0, width_mm=2.0, height_mm=2.0)
        result = cropper.crop(img, region)

        assert result.x_px == 90
        assert result.y_px == 90
        assert result.width_px == 10  # 100 - 90 = 10 (clamped)
        assert result.height_px == 10

    def test_empty_crop_raises(self) -> None:
        """完全に画像範囲外の場合はエラー。"""
        img = self._make_image(100, 100)
        cropper = BoxCropper(scale_px_per_mm=10.0)

        region = Region(x_mm=20.0, y_mm=20.0, width_mm=5.0, height_mm=5.0)
        with pytest.raises(ValueError, match="empty crop"):
            cropper.crop(img, region)

    def test_color_image(self) -> None:
        """3チャネル画像でも正しく切り出せる。"""
        img = np.ones((200, 300, 3), dtype=np.uint8) * 128
        cropper = BoxCropper(scale_px_per_mm=10.0)

        region = Region(x_mm=5.0, y_mm=5.0, width_mm=10.0, height_mm=10.0)
        result = cropper.crop(img, region)

        assert result.box_image.shape == (100, 100, 3)
        assert result.box_image[0, 0, 0] == 128

    def test_invalid_image_type_raises(self) -> None:
        with pytest.raises(TypeError, match="numpy ndarray"):
            BoxCropper(scale_px_per_mm=10.0).crop("not an image", Region(x_mm=0, y_mm=0, width_mm=1, height_mm=1))


class TestBoxCropperCropFields:
    """複数フィールドの一括切出し。"""

    def test_crop_multiple_fields(self) -> None:
        img = np.zeros((300, 200), dtype=np.uint8)
        cropper = BoxCropper(scale_px_per_mm=10.0)

        fields = [
            ("field_a", Region(x_mm=0.0, y_mm=0.0, width_mm=5.0, height_mm=3.0)),
            ("field_b", Region(x_mm=10.0, y_mm=15.0, width_mm=5.0, height_mm=3.0)),
        ]

        results = cropper.crop_fields(img, fields)

        assert len(results) == 2
        assert "field_a" in results
        assert "field_b" in results
        assert isinstance(results["field_a"], CropResult)
        assert results["field_a"].box_image.shape == (30, 50)
        assert results["field_b"].box_image.shape == (30, 50)

    def test_empty_fields_returns_empty(self) -> None:
        img = np.zeros((100, 100), dtype=np.uint8)
        cropper = BoxCropper(scale_px_per_mm=10.0)

        results = cropper.crop_fields(img, [])
        assert results == {}
