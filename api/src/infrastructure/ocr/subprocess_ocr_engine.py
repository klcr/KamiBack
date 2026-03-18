"""サブプロセス呼出しによるOCRエンジン実装。

NDLOCR-Liteをサブプロセスとして呼び出す。
JSON入出力を標準化し、将来のHTTPマイクロサービス化を容易にする（DJ-3）。

環境変数:
    KAMI_OCR_ENGINE_PATH: OCRエンジンの実行パス
    KAMI_OCR_ENGINE_TIMEOUT: タイムアウト秒数（デフォルト: 30）
"""

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray

from domain.src.manifest.manifest_types import InputType
from domain.src.ocr_result.ocr_engine import OcrEngine
from domain.src.ocr_result.ocr_result_types import OcrEngineResult

logger = logging.getLogger(__name__)

# 環境変数キー
ENV_ENGINE_PATH = "KAMI_OCR_ENGINE_PATH"
ENV_ENGINE_TIMEOUT = "KAMI_OCR_ENGINE_TIMEOUT"

DEFAULT_TIMEOUT = 30


class OcrEngineError(Exception):
    """OCRエンジンの実行エラー。"""


class SubprocessOcrEngine(OcrEngine):
    """サブプロセスでOCRエンジンを呼び出す実装。

    プロトコル:
        1. 入力画像をPNGとして一時ファイルに書き出す
        2. JSONリクエストを標準入力に渡す:
           {"image_path": "/tmp/xxx.png", "input_type": "printed"}
        3. 標準出力からJSONレスポンスを受け取る:
           {"text": "認識結果", "confidence": 0.95}
    """

    def __init__(
        self,
        engine_path: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self._engine_path = engine_path or os.environ.get(ENV_ENGINE_PATH, "")
        self._timeout = timeout or int(os.environ.get(ENV_ENGINE_TIMEOUT, str(DEFAULT_TIMEOUT)))

    def recognize(self, image: Any, input_type: InputType) -> OcrEngineResult:
        """画像から文字列を認識する。

        Args:
            image: 切り出されたボックス画像（numpy ndarray）
            input_type: フィールドの入力種別

        Returns:
            認識結果（テキストと信頼度）

        Raises:
            OcrEngineError: エンジン未設定・実行失敗時
        """
        if not self._engine_path:
            raise OcrEngineError(
                f"OCRエンジンのパスが設定されていません。環境変数 {ENV_ENGINE_PATH} を設定してください。"
            )

        img = _to_ndarray(image)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_path = f.name
            cv2.imwrite(tmp_path, img)

        try:
            request = {
                "image_path": tmp_path,
                "input_type": input_type.value,
            }
            result = self._call_engine(json.dumps(request))
            return _parse_response(result)
        finally:
            _cleanup_temp(tmp_path)

    def _call_engine(self, stdin_data: str) -> str:
        """サブプロセスを実行してstdoutを返す。

        start_new_session=True でプロセスグループを分離し、
        タイムアウト時はグループ全体を kill する。
        NDLOCR-Lite が生成する子プロセス（PyTorch推論ワーカー等）が
        パイプを保持してハングする問題を防ぐ。
        """
        cmd = self._build_command()
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
        except FileNotFoundError as e:
            raise OcrEngineError(f"OCRエンジンが見つかりません: {self._engine_path}") from e

        try:
            stdout, stderr = proc.communicate(input=stdin_data, timeout=self._timeout)
        except subprocess.TimeoutExpired as e:
            _kill_process_group(proc)
            raise OcrEngineError(f"OCRエンジンがタイムアウトしました（{self._timeout}秒）") from e

        if proc.returncode != 0:
            logger.error("OCR engine stderr: %s", stderr)
            raise OcrEngineError(f"OCRエンジンがエラーで終了しました（code={proc.returncode}）: {stderr[:200]}")

        return stdout

    def _build_command(self) -> list[str]:
        """実行コマンドを組み立てる。

        Windowsではシバンが機能しないため、sys.executableで明示的に
        Pythonインタープリタを指定する。
        """
        if sys.platform == "win32":
            return [sys.executable, self._engine_path]
        return [self._engine_path]


def _kill_process_group(proc: subprocess.Popen[str]) -> None:
    """プロセスグループ全体を kill する。

    start_new_session=True で起動したプロセスとその子孫すべてを終了させる。
    """
    try:
        if sys.platform == "win32":
            proc.kill()
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, OSError):
        pass
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def _parse_response(stdout: str) -> OcrEngineResult:
    """エンジンの標準出力をパースする。"""
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as e:
        raise OcrEngineError(f"OCRエンジンの出力がJSONではありません: {e}") from e

    text = data.get("text", "")
    confidence = data.get("confidence", 0.0)

    if not isinstance(text, str):
        raise OcrEngineError(f"OCRエンジンの出力にtextがありません: {data}")
    if not isinstance(confidence, (int, float)):
        raise OcrEngineError(f"OCRエンジンの出力にconfidenceがありません: {data}")

    confidence = max(0.0, min(1.0, float(confidence)))

    return OcrEngineResult(text=text, confidence=confidence)


def _to_ndarray(image: object) -> NDArray[np.uint8]:
    """入力をnumpy ndarrayに変換する。"""
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected numpy ndarray, got {type(image).__name__}")
    return image


def _cleanup_temp(path: str) -> None:
    """一時ファイルを削除する。"""
    try:
        os.unlink(path)
    except OSError:
        logger.warning("Failed to delete temp file: %s", path)
