"""スキャン関連APIの依存注入。

インフラ層の具象クラスをインスタンス化し、ユースケースに渡す。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from domain.src.manifest.manifest_types import ManifestData

if TYPE_CHECKING:
    from api.src.infrastructure.storage.local_file_image_storage import (
        LocalFileImageStorage,
    )

# TODO: ManifestRepositoryから取得するように変更する
_manifest_lookup: dict[str, ManifestData] = {}

# ImageStorageはリクエスト間で共有する必要がある（correctで保存→ocrで読込）
_image_storage: LocalFileImageStorage | None = None


def _get_image_storage() -> LocalFileImageStorage:
    """ImageStorageのシングルトンインスタンスを返す。"""
    global _image_storage  # noqa: PLW0603
    if _image_storage is None:
        from api.src.infrastructure.storage.local_file_image_storage import (
            LocalFileImageStorage,
        )

        _image_storage = LocalFileImageStorage()
    return _image_storage


def register_manifest(manifest: ManifestData) -> None:
    """マニフェストを登録する（テスト・セットアップ用）。"""
    _manifest_lookup[manifest.template_id] = manifest


def get_scan_dependencies() -> dict[str, object]:
    """スキャン関連ユースケースの依存を組み立てる。

    HoughTomboDetectorはpaper_width_mm/paper_height_mmが必要だが、
    リクエスト時点ではQR検出前でテンプレートが不明。
    デフォルトのA4サイズで初期化し、ユースケース内で適切に処理する。

    CV関連のインポートは遅延実行する。cv2等のネイティブ依存が
    インストールされていない環境でもアプリが起動できるようにするため。
    """
    from api.src.infrastructure.cv.hough_tombo_detector import HoughTomboDetector
    from api.src.infrastructure.cv.image_preprocessor import CvImagePreprocessor
    from api.src.infrastructure.cv.perspective_corrector import (
        CvPerspectiveCorrector,
    )
    from api.src.infrastructure.cv.qr_detector import PyzbarQrDetector
    from api.src.infrastructure.ocr.subprocess_ocr_engine import SubprocessOcrEngine

    return {
        "qr_detector": PyzbarQrDetector(),
        "tombo_detector": HoughTomboDetector(
            paper_width_mm=210.0,
            paper_height_mm=297.0,
        ),
        "perspective_corrector": CvPerspectiveCorrector(),
        "image_preprocessor": CvImagePreprocessor(),
        "image_storage": _get_image_storage(),
        "manifest_lookup": _manifest_lookup,
        "ocr_engine": SubprocessOcrEngine(),
    }
