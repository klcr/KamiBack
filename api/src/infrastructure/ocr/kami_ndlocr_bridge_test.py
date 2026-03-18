"""kami_ndlocr_bridge のテスト。

NDLOCR-Lite 本体は不要。XML パース・結合ロジックとエラーハンドリングを検証する。
"""

from __future__ import annotations

import json
import os
import stat
import tempfile

import pytest

from .kami_ndlocr_bridge import (
    LineResult,
    _extract_lines,
    _find_xml_file,
    parse_ndlocr_output,
)


def _write_xml(directory: str, xml_content: str, filename: str = "result.xml") -> str:
    """テスト用 XML ファイルを出力する。"""
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    return path


class TestExtractLines:
    """LINE 要素の抽出テスト。"""

    def test_single_line(self) -> None:
        import xml.etree.ElementTree as ET

        xml = '<OCRDATASET><PAGE><LINE STRING="テスト" CONF="0.92" ORDER="1"/></PAGE></OCRDATASET>'
        root = ET.fromstring(xml)
        lines = _extract_lines(root)

        assert len(lines) == 1
        assert lines[0] == LineResult(text="テスト", confidence=0.92, order=1)

    def test_multiple_lines_with_order(self) -> None:
        import xml.etree.ElementTree as ET

        xml = (
            "<OCRDATASET><PAGE>"
            '<LINE STRING="世界" CONF="0.88" ORDER="2"/>'
            '<LINE STRING="こんにちは" CONF="0.95" ORDER="1"/>'
            "</PAGE></OCRDATASET>"
        )
        root = ET.fromstring(xml)
        lines = _extract_lines(root)

        assert len(lines) == 2
        assert lines[0].text == "世界"
        assert lines[1].text == "こんにちは"

    def test_empty_string_skipped(self) -> None:
        import xml.etree.ElementTree as ET

        xml = (
            "<OCRDATASET><PAGE>"
            '<LINE STRING="" CONF="0.5" ORDER="1"/>'
            '<LINE STRING="有効" CONF="0.9" ORDER="2"/>'
            "</PAGE></OCRDATASET>"
        )
        root = ET.fromstring(xml)
        lines = _extract_lines(root)

        assert len(lines) == 1
        assert lines[0].text == "有効"

    def test_no_string_attribute_skipped(self) -> None:
        import xml.etree.ElementTree as ET

        xml = '<OCRDATASET><PAGE><LINE CONF="0.5" ORDER="1"/></PAGE></OCRDATASET>'
        root = ET.fromstring(xml)
        lines = _extract_lines(root)

        assert len(lines) == 0

    def test_invalid_conf_defaults_to_zero(self) -> None:
        import xml.etree.ElementTree as ET

        xml = '<OCRDATASET><PAGE><LINE STRING="abc" CONF="invalid" ORDER="1"/></PAGE></OCRDATASET>'
        root = ET.fromstring(xml)
        lines = _extract_lines(root)

        assert lines[0].confidence == 0.0

    def test_nested_in_textblock(self) -> None:
        """TEXTBLOCK > LINE の構造でも抽出できる。"""
        import xml.etree.ElementTree as ET

        xml = (
            "<OCRDATASET><PAGE>"
            '<TEXTBLOCK CONF="0.9">'
            '<LINE STRING="ネスト" CONF="0.85" ORDER="1"/>'
            "</TEXTBLOCK>"
            "</PAGE></OCRDATASET>"
        )
        root = ET.fromstring(xml)
        lines = _extract_lines(root)

        assert len(lines) == 1
        assert lines[0].text == "ネスト"


class TestFindXmlFile:
    """XML ファイル検索テスト。"""

    def test_flat_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_xml(tmpdir, "<OCRDATASET/>", "output.xml")
            result = _find_xml_file(tmpdir)
            assert result is not None
            assert result.endswith(".xml")

    def test_nested_structure(self) -> None:
        """output_dir/pid/xml/pid.xml の構造。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_dir = os.path.join(tmpdir, "pid001", "xml")
            os.makedirs(xml_dir)
            _write_xml(xml_dir, "<OCRDATASET/>", "pid001.xml")
            result = _find_xml_file(tmpdir)
            assert result is not None
            assert "pid001.xml" in result

    def test_no_xml_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _find_xml_file(tmpdir)
            assert result is None


class TestParseNdlocrOutput:
    """XML パース→テキスト結合のテスト。"""

    def test_single_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_xml(
                tmpdir,
                '<OCRDATASET><PAGE><LINE STRING="株式会社テスト" CONF="0.93" ORDER="1"/></PAGE></OCRDATASET>',
            )
            text, conf = parse_ndlocr_output(tmpdir)

            assert text == "株式会社テスト"
            assert conf == pytest.approx(0.93)

    def test_multiple_lines_concatenated_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_xml(
                tmpdir,
                "<OCRDATASET><PAGE>"
                '<LINE STRING="世界" CONF="0.90" ORDER="2"/>'
                '<LINE STRING="こんにちは" CONF="0.95" ORDER="1"/>'
                "</PAGE></OCRDATASET>",
            )
            text, conf = parse_ndlocr_output(tmpdir)

            # ORDER 順: 1→"こんにちは", 2→"世界"
            assert text == "こんにちは世界"

    def test_weighted_average_confidence(self) -> None:
        """信頼度は文字数で加重平均される。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # "AB" (2文字, conf=1.0) + "CDEF" (4文字, conf=0.5)
            # 加重平均 = (2*1.0 + 4*0.5) / 6 = 4.0/6 ≈ 0.6667
            _write_xml(
                tmpdir,
                "<OCRDATASET><PAGE>"
                '<LINE STRING="AB" CONF="1.0" ORDER="1"/>'
                '<LINE STRING="CDEF" CONF="0.5" ORDER="2"/>'
                "</PAGE></OCRDATASET>",
            )
            text, conf = parse_ndlocr_output(tmpdir)

            assert text == "ABCDEF"
            assert conf == pytest.approx(2 / 3, abs=0.001)

    def test_no_xml_file_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            text, conf = parse_ndlocr_output(tmpdir)
            assert text == ""
            assert conf == 0.0

    def test_empty_xml_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_xml(tmpdir, "<OCRDATASET><PAGE/></OCRDATASET>")
            text, conf = parse_ndlocr_output(tmpdir)
            assert text == ""
            assert conf == 0.0

    def test_invalid_xml_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_xml(tmpdir, "not xml at all <<<")
            text, conf = parse_ndlocr_output(tmpdir)
            assert text == ""
            assert conf == 0.0


class TestBridgeEndToEnd:
    """ブリッジスクリプトの E2E テスト（スタブスクリプトでNDLOCR-Liteを模擬）。"""

    @staticmethod
    def _create_bridge_with_stub_ndlocr(xml_content: str) -> tuple[str, str]:
        """スタブの NDLOCR-Lite ディレクトリと ocr.py を作成する。

        Returns:
            (ndlocr_dir, bridge_script_path)
        """
        ndlocr_dir = tempfile.mkdtemp(prefix="stub_ndlocr_")

        # スタブ ocr.py: 受け取った --output ディレクトリに XML を書き出す
        ocr_py = os.path.join(ndlocr_dir, "ocr.py")
        # XML 内容は Python 文字列として埋め込む
        xml_escaped = xml_content.replace("\\", "\\\\").replace("'", "\\'")
        script = f"""#!/usr/bin/env python3
import argparse, os
parser = argparse.ArgumentParser()
parser.add_argument('--sourceimg')
parser.add_argument('--output')
args = parser.parse_args()
os.makedirs(args.output, exist_ok=True)
with open(os.path.join(args.output, 'result.xml'), 'w') as f:
    f.write('{xml_escaped}')
"""
        with open(ocr_py, "w") as f:
            f.write(script)
        os.chmod(ocr_py, stat.S_IRWXU)

        return ndlocr_dir, ocr_py

    def test_bridge_main_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """メインエントリーポイントの正常系テスト。"""
        import io

        xml = '<OCRDATASET><PAGE><LINE STRING="12345" CONF="0.91" ORDER="1"/></PAGE></OCRDATASET>'
        ndlocr_dir, _ = self._create_bridge_with_stub_ndlocr(xml)

        monkeypatch.setattr(
            "api.src.infrastructure.ocr.kami_ndlocr_bridge.NDLOCR_LITE_DIR",
            ndlocr_dir,
        )

        # テスト用画像ファイル（空でよい）
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG")
            img_path = f.name

        request = json.dumps({"image_path": img_path, "input_type": "printed"})
        monkeypatch.setattr("sys.stdin", io.StringIO(request))

        # stdout をキャプチャ
        captured = io.StringIO()
        monkeypatch.setattr("sys.stdout", captured)

        from .kami_ndlocr_bridge import main

        main()

        os.unlink(img_path)

        output = json.loads(captured.getvalue())
        assert output["text"] == "12345"
        assert output["confidence"] == pytest.approx(0.91)

    def test_bridge_main_missing_image(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """存在しない画像パスで空結果を返す。"""
        import io

        ndlocr_dir = tempfile.mkdtemp(prefix="stub_ndlocr_")
        # ocr.py が存在するだけでよい（呼ばれないので）
        monkeypatch.setattr(
            "api.src.infrastructure.ocr.kami_ndlocr_bridge.NDLOCR_LITE_DIR",
            ndlocr_dir,
        )

        request = json.dumps({"image_path": "/nonexistent/image.png", "input_type": "printed"})
        monkeypatch.setattr("sys.stdin", io.StringIO(request))

        captured = io.StringIO()
        monkeypatch.setattr("sys.stdout", captured)

        from .kami_ndlocr_bridge import main

        main()

        output = json.loads(captured.getvalue())
        assert output["text"] == ""
        assert output["confidence"] == 0.0

    def test_bridge_main_invalid_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """不正な JSON 入力で空結果を返す。"""
        import io

        monkeypatch.setattr("sys.stdin", io.StringIO("not json"))

        captured = io.StringIO()
        monkeypatch.setattr("sys.stdout", captured)

        from .kami_ndlocr_bridge import main

        main()

        output = json.loads(captured.getvalue())
        assert output["text"] == ""
        assert output["confidence"] == 0.0
