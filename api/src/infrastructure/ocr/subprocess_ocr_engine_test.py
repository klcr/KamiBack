"""SubprocessOcrEngineのテスト。

実際のOCRエンジンは使わず、サブプロセス呼出し・JSON解析ロジックをテストする。
"""

from __future__ import annotations

import json
import os
import stat
import tempfile

import numpy as np
import pytest

from domain.src.manifest.manifest_types import InputType
from domain.src.ocr_result.ocr_result_types import OcrEngineResult

from .subprocess_ocr_engine import (
    ENV_ENGINE_PATH,
    OcrEngineError,
    SubprocessOcrEngine,
    _parse_response,
)


class TestParseResponse:
    """エンジン出力のJSON解析。"""

    def test_valid_response(self) -> None:
        result = _parse_response('{"text": "12345", "confidence": 0.95}')
        assert result == OcrEngineResult(text="12345", confidence=0.95)

    def test_empty_text(self) -> None:
        result = _parse_response('{"text": "", "confidence": 0.0}')
        assert result == OcrEngineResult(text="", confidence=0.0)

    def test_confidence_clamped_above_1(self) -> None:
        result = _parse_response('{"text": "abc", "confidence": 1.5}')
        assert result.confidence == 1.0

    def test_confidence_clamped_below_0(self) -> None:
        result = _parse_response('{"text": "abc", "confidence": -0.5}')
        assert result.confidence == 0.0

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(OcrEngineError, match="JSON"):
            _parse_response("not json")

    def test_missing_text_field_still_works(self) -> None:
        """textフィールドが省略された場合はデフォルト空文字列。"""
        result = _parse_response('{"confidence": 0.5}')
        assert result.text == ""

    def test_non_string_text_raises(self) -> None:
        with pytest.raises(OcrEngineError, match="text"):
            _parse_response('{"text": 123, "confidence": 0.5}')

    def test_non_numeric_confidence_raises(self) -> None:
        with pytest.raises(OcrEngineError, match="confidence"):
            _parse_response('{"text": "abc", "confidence": "high"}')


class TestSubprocessOcrEngineInit:
    """コンストラクタ。"""

    def test_engine_path_from_arg(self) -> None:
        engine = SubprocessOcrEngine(engine_path="/usr/bin/ocr")
        assert engine._engine_path == "/usr/bin/ocr"

    def test_engine_path_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ENV_ENGINE_PATH, "/env/path/ocr")
        engine = SubprocessOcrEngine()
        assert engine._engine_path == "/env/path/ocr"

    def test_timeout_from_arg(self) -> None:
        engine = SubprocessOcrEngine(engine_path="/usr/bin/ocr", timeout=60)
        assert engine._timeout == 60


class TestSubprocessOcrEngineRecognize:
    """実際のサブプロセス呼出しテスト（スタブスクリプトを使用）。"""

    @staticmethod
    def _create_stub_script(response: dict) -> str:
        """JSONを標準出力に返すスタブスクリプトを作成する。"""
        fd, path = tempfile.mkstemp(suffix=".sh")
        response_json = json.dumps(response)
        script = f"""#!/bin/sh
cat <<'RESPONSE'
{response_json}
RESPONSE
"""
        os.write(fd, script.encode())
        os.close(fd)
        os.chmod(path, stat.S_IRWXU)
        return path

    @staticmethod
    def _create_failing_script(exit_code: int = 1, stderr: str = "error") -> str:
        """非ゼロ終了コードで終了するスタブスクリプトを作成する。"""
        fd, path = tempfile.mkstemp(suffix=".sh")
        script = f"""#!/bin/sh
echo "{stderr}" >&2
exit {exit_code}
"""
        os.write(fd, script.encode())
        os.close(fd)
        os.chmod(path, stat.S_IRWXU)
        return path

    def test_recognize_with_stub(self) -> None:
        """スタブスクリプトでの正常系テスト。"""
        stub = self._create_stub_script({"text": "テスト", "confidence": 0.88})
        try:
            engine = SubprocessOcrEngine(engine_path=stub)
            img = np.zeros((50, 100), dtype=np.uint8)
            result = engine.recognize(img, InputType.PRINTED)

            assert result.text == "テスト"
            assert result.confidence == 0.88
        finally:
            os.unlink(stub)

    def test_recognize_handwritten(self) -> None:
        """inputType=handwritten_numberでも動作する。"""
        stub = self._create_stub_script({"text": "42", "confidence": 0.65})
        try:
            engine = SubprocessOcrEngine(engine_path=stub)
            img = np.zeros((30, 60), dtype=np.uint8)
            result = engine.recognize(img, InputType.HANDWRITTEN_NUMBER)

            assert result.text == "42"
            assert result.confidence == 0.65
        finally:
            os.unlink(stub)

    def test_engine_not_configured_raises(self) -> None:
        """エンジンパス未設定時はエラー。"""
        engine = SubprocessOcrEngine(engine_path="")
        img = np.zeros((10, 10), dtype=np.uint8)
        with pytest.raises(OcrEngineError, match="パスが設定されていません"):
            engine.recognize(img, InputType.PRINTED)

    def test_engine_not_found_raises(self) -> None:
        """存在しないパスでエラー。"""
        engine = SubprocessOcrEngine(engine_path="/nonexistent/ocr")
        img = np.zeros((10, 10), dtype=np.uint8)
        with pytest.raises(OcrEngineError, match="見つかりません"):
            engine.recognize(img, InputType.PRINTED)

    def test_engine_failure_raises(self) -> None:
        """エンジンが非ゼロで終了した場合はエラー。"""
        stub = self._create_failing_script(exit_code=1, stderr="segfault")
        try:
            engine = SubprocessOcrEngine(engine_path=stub)
            img = np.zeros((10, 10), dtype=np.uint8)
            with pytest.raises(OcrEngineError, match="エラーで終了"):
                engine.recognize(img, InputType.PRINTED)
        finally:
            os.unlink(stub)

    def test_engine_timeout_raises(self) -> None:
        """タイムアウト時はエラー。"""
        fd, path = tempfile.mkstemp(suffix=".sh")
        script = "#!/bin/sh\nsleep 10\n"
        os.write(fd, script.encode())
        os.close(fd)
        os.chmod(path, stat.S_IRWXU)

        try:
            engine = SubprocessOcrEngine(engine_path=path, timeout=1)
            img = np.zeros((10, 10), dtype=np.uint8)
            with pytest.raises(OcrEngineError, match="タイムアウト"):
                engine.recognize(img, InputType.PRINTED)
        finally:
            os.unlink(path)

    def test_invalid_image_type_raises(self) -> None:
        """numpy ndarray以外はTypeError。"""
        engine = SubprocessOcrEngine(engine_path="/some/path")
        with pytest.raises(TypeError, match="numpy ndarray"):
            engine.recognize("not an image", InputType.PRINTED)
