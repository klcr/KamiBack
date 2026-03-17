"""画像補正ユースケース（UC-1: correct_image）。

撮影画像を受け取り、QR検出→トンボ検出→射影変換→前処理→保存を行う。
ADR-004 DJ-9 に基づく2段階パイプラインの第1段階。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

from domain.src.manifest.manifest_types import ManifestData, Page
from domain.src.ocr_result.image_preprocessor import ImagePreprocessor
from domain.src.ocr_result.perspective_corrector import PerspectiveCorrector
from domain.src.ocr_result.tombo_detector import TomboDetector
from domain.src.scan.image_storage import ImageStorage
from domain.src.scan.qr_detector import QrDetector
from domain.src.shared.coordinate import Point


class CorrectImageError(Exception):
    """画像補正処理で発生するエラー。"""

    def __init__(self, message: str, user_action: str) -> None:
        self.message = message
        self.user_action = user_action
        super().__init__(message)


@dataclass(frozen=True)
class CorrectImageResult:
    """画像補正結果。"""

    image_id: str
    image_path: str
    template_id: str
    page_index: int
    detection_count: int
    has_estimation: bool
    skew_degree: float | None
    aspect_ratio_error: float | None
    scale_px_per_mm: float


def correct_image(
    image_bytes: bytes,
    *,
    qr_detector: QrDetector,
    tombo_detector: TomboDetector,
    perspective_corrector: PerspectiveCorrector,
    image_preprocessor: ImagePreprocessor,
    image_storage: ImageStorage,
    manifest_lookup: dict[str, ManifestData],
) -> CorrectImageResult:
    """撮影画像を補正して保存する。

    Args:
        image_bytes: 撮影画像のバイナリデータ（JPEG/PNG）
        qr_detector: QRコード検出器
        tombo_detector: トンボ検出器
        perspective_corrector: 射影変換器
        image_preprocessor: 画像前処理器
        image_storage: 画像ストレージ
        manifest_lookup: テンプレートID → ManifestData のマッピング

    Returns:
        補正結果（画像ID、テンプレートID、ページインデックス、トンボ検出情報）

    Raises:
        CorrectImageError: QR検出失敗、トンボ不足、マニフェスト未発見等
    """
    # 1. バイト列を画像に変換
    image = _decode_image(image_bytes)

    # 2. QRコード検出 → テンプレートID + ページインデックス
    qr_result = qr_detector.detect(image)
    if not qr_result.detected:
        raise CorrectImageError(
            message="QRコードを検出できませんでした",
            user_action="QRコードが写るように撮影し直してください",
        )
    assert qr_result.template_id is not None
    assert qr_result.page_index is not None

    # 3. マニフェスト取得
    manifest = manifest_lookup.get(qr_result.template_id)
    if manifest is None:
        raise CorrectImageError(
            message=f"テンプレートが見つかりません: {qr_result.template_id}",
            user_action="登録済みのテンプレートで印刷した帳票を使用してください",
        )

    page = _find_page(manifest, qr_result.page_index)
    if page is None:
        raise CorrectImageError(
            message=f"ページが見つかりません: page_index={qr_result.page_index}",
            user_action="正しいページを撮影してください",
        )

    # 4. トンボ検出
    tombo_result = tombo_detector.detect(image)
    if not tombo_result.is_sufficient:
        raise CorrectImageError(
            message=f"トンボの検出数が不足しています（{tombo_result.detection_count}点）",
            user_action="帳票の四隅が写るように撮影し直してください",
        )

    four_points = tombo_result.four_points
    if len(four_points) < 4:
        raise CorrectImageError(
            message="トンボ4点を確定できませんでした",
            user_action="帳票の四隅が写るように撮影し直してください",
        )

    # 5. 射影変換
    dst_points_mm, output_size_mm = _build_dst_points(page)
    correction_result = perspective_corrector.correct(
        image=image,
        src_points=four_points,
        dst_points_mm=dst_points_mm,
        output_size_mm=output_size_mm,
    )

    # 6. 画像前処理（グレースケール→ブラー→適応的二値化）
    preprocessed = image_preprocessor.preprocess(correction_result.corrected_image)

    # 7. 補正画像を保存
    image_id = str(uuid.uuid4())
    encoded = _encode_image(preprocessed)
    image_path = image_storage.save(encoded, image_id)

    return CorrectImageResult(
        image_id=image_id,
        image_path=image_path,
        template_id=qr_result.template_id,
        page_index=qr_result.page_index,
        detection_count=tombo_result.detection_count,
        has_estimation=tombo_result.estimated_points is not None,
        skew_degree=tombo_result.skew_degree,
        aspect_ratio_error=tombo_result.aspect_ratio_error,
        scale_px_per_mm=correction_result.scale_px_per_mm,
    )


def _decode_image(image_bytes: bytes) -> np.ndarray:
    """バイト列をOpenCV画像に変換する。"""
    import cv2
    import numpy as np

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise CorrectImageError(
            message="画像のデコードに失敗しました",
            user_action="JPEG または PNG 形式の画像を送信してください",
        )
    return img


def _encode_image(image: np.ndarray) -> bytes:
    """OpenCV画像をPNGバイト列にエンコードする。"""
    import cv2

    success, buf = cv2.imencode(".png", image)
    if not success:
        raise CorrectImageError(
            message="補正画像のエンコードに失敗しました",
            user_action="もう一度撮影してください",
        )
    result: bytes = buf.tobytes()
    return result


def _find_page(manifest: ManifestData, page_index: int) -> Page | None:
    """マニフェストからページインデックスで検索する。"""
    for page in manifest.pages:
        if page.page_index == page_index:
            return page
    return None


def _build_dst_points(page: Page) -> tuple[tuple[Point, ...], tuple[float, float]]:
    """マニフェストのトンボ位置から射影変換の目標点と出力サイズを構築する。

    Returns:
        (dst_points_mm, output_size_mm)
    """
    paper = page.paper
    if page.registration_marks is not None and len(page.registration_marks.positions) == 4:
        dst_points = page.registration_marks.positions
    else:
        # トンボ位置がマニフェストにない場合は用紙四隅をフォールバック
        dst_points = (
            Point(x_mm=0.0, y_mm=0.0),
            Point(x_mm=paper.width_mm, y_mm=0.0),
            Point(x_mm=0.0, y_mm=paper.height_mm),
            Point(x_mm=paper.width_mm, y_mm=paper.height_mm),
        )
    output_size_mm = (paper.width_mm, paper.height_mm)
    return dst_points, output_size_mm
