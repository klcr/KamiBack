"""OpenCVベースの画像前処理パイプライン。

グレースケール→ガウシアンブラー→適応的二値化の順で
照明ムラ・影・スマホ特有のノイズを吸収しOCR精度を底上げする。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray

from domain.src.ocr_result.image_preprocessor import ImagePreprocessor


@dataclass(frozen=True)
class PreprocessParams:
    """前処理パラメータ。"""

    blur_kernel_size: int = 5
    adaptive_block_size: int = 11
    adaptive_c: int = 2

    def __post_init__(self) -> None:
        if self.blur_kernel_size % 2 == 0 or self.blur_kernel_size < 1:
            raise ValueError("blur_kernel_size must be a positive odd number")
        if self.adaptive_block_size % 2 == 0 or self.adaptive_block_size < 3:
            raise ValueError("adaptive_block_size must be an odd number >= 3")


class CvImagePreprocessor(ImagePreprocessor):
    """OpenCVによる画像前処理パイプライン。

    1. グレースケール変換（既にグレーならスキップ）
    2. ガウシアンブラー（ノイズ除去）
    3. 適応的二値化（照明ムラ対応）
    """

    def __init__(self, params: PreprocessParams | None = None) -> None:
        self._params = params or PreprocessParams()

    def preprocess(self, image: Any) -> Any:
        """画像に前処理パイプラインを適用する。"""
        img = _to_ndarray(image)
        gray = _to_grayscale(img)
        blurred = cv2.GaussianBlur(
            gray,
            (self._params.blur_kernel_size, self._params.blur_kernel_size),
            0,
        )
        binary: NDArray[np.uint8] = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            self._params.adaptive_block_size,
            self._params.adaptive_c,
        )
        return binary


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
