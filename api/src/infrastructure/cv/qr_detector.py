"""pyzbarベースのQRコード検出。

帳票に埋め込まれたQRコードからテンプレートIDとページインデックスを読み取る。
QRコードのcontent形式: "{template_id}/{page_index}"
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray
from pyzbar import pyzbar
from pyzbar.pyzbar import Decoded

from domain.src.scan.qr_detector import QrDetectionResult, QrDetector


def _parse_qr_content(content: str) -> tuple[str, int] | None:
    """QRコードの内容をテンプレートIDとページインデックスにパースする。

    期待フォーマット: "{template_id}/{page_index}"
    """
    parts = content.rsplit("/", 1)
    if len(parts) != 2:
        return None
    template_id, page_index_str = parts
    if not template_id:
        return None
    try:
        page_index = int(page_index_str)
    except ValueError:
        return None
    if page_index < 0:
        return None
    return template_id, page_index


def _find_first_qr(decoded_objects: list[Decoded]) -> Decoded | None:
    """QRコードタイプのオブジェクトを最初の1つだけ返す。"""
    for obj in decoded_objects:
        if obj.type == "QRCODE":
            return obj
    return None


class PyzbarQrDetector(QrDetector):
    """pyzbarによるQRコード検出器。"""

    def detect(self, image: Any) -> QrDetectionResult:
        """画像からQRコードを検出する。

        Args:
            image: 入力画像（numpy ndarray、カラーまたはグレースケール）

        Returns:
            QRコード検出結果
        """
        img: NDArray[np.uint8] = image

        # グレースケール変換（カラーの場合）
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

        decoded_objects = pyzbar.decode(gray)
        qr = _find_first_qr(decoded_objects)

        if qr is None:
            return QrDetectionResult(detected=False)

        raw_content = qr.data.decode("utf-8", errors="replace")
        parsed = _parse_qr_content(raw_content)

        if parsed is None:
            return QrDetectionResult(
                detected=False,
                raw_content=raw_content,
            )

        template_id, page_index = parsed
        return QrDetectionResult(
            detected=True,
            template_id=template_id,
            page_index=page_index,
            raw_content=raw_content,
        )
