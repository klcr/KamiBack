"""CvImagePreprocessor のテスト。"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from api.src.infrastructure.cv.image_preprocessor import (
    CvImagePreprocessor,
    PreprocessParams,
)


class TestPreprocessParams:
    """パラメータバリデーション。"""

    def test_default_params(self) -> None:
        params = PreprocessParams()
        assert params.blur_kernel_size == 5
        assert params.adaptive_block_size == 11
        assert params.adaptive_c == 2

    def test_reject_even_blur_kernel(self) -> None:
        with pytest.raises(ValueError, match="blur_kernel_size"):
            PreprocessParams(blur_kernel_size=4)

    def test_reject_small_block_size(self) -> None:
        with pytest.raises(ValueError, match="adaptive_block_size"):
            PreprocessParams(adaptive_block_size=2)


class TestCvImagePreprocessor:
    """前処理パイプラインのテスト。"""

    def test_color_image_to_binary(self) -> None:
        """カラー画像 → 二値化出力。"""
        img = np.random.randint(0, 256, (200, 300, 3), dtype=np.uint8)
        preprocessor = CvImagePreprocessor()
        result = preprocessor.preprocess(img)

        assert result.shape == (200, 300)
        assert result.dtype == np.uint8
        unique_values = set(np.unique(result))
        assert unique_values.issubset({0, 255})

    def test_grayscale_image(self) -> None:
        """グレースケール入力でもエラーにならない。"""
        img = np.random.randint(0, 256, (200, 300), dtype=np.uint8)
        preprocessor = CvImagePreprocessor()
        result = preprocessor.preprocess(img)

        assert result.shape == (200, 300)

    def test_output_size_matches_input(self) -> None:
        """出力サイズが入力と同一。"""
        img = np.ones((400, 600, 3), dtype=np.uint8) * 128
        preprocessor = CvImagePreprocessor()
        result = preprocessor.preprocess(img)

        assert result.shape == (400, 600)

    def test_custom_params(self) -> None:
        """カスタムパラメータで動作する。"""
        params = PreprocessParams(blur_kernel_size=3, adaptive_block_size=15, adaptive_c=5)
        preprocessor = CvImagePreprocessor(params=params)
        img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        result = preprocessor.preprocess(img)

        assert result.shape == (100, 100)

    def test_reject_non_ndarray(self) -> None:
        preprocessor = CvImagePreprocessor()
        with pytest.raises(TypeError):
            preprocessor.preprocess("not an image")

    def test_white_image_stays_white(self) -> None:
        """白画像は二値化後も白。"""
        img = np.ones((100, 100), dtype=np.uint8) * 255
        preprocessor = CvImagePreprocessor()
        result = preprocessor.preprocess(img)
        assert np.all(result == 255)

    def test_preserves_text_like_pattern(self) -> None:
        """テキスト風パターン（暗い線 on 明るい背景）が保持される。"""
        img = np.ones((100, 200), dtype=np.uint8) * 220
        cv2.line(img, (20, 50), (180, 50), 30, 3)
        preprocessor = CvImagePreprocessor()
        result = preprocessor.preprocess(img)

        dark_pixels = np.sum(result == 0)
        assert dark_pixels > 0
