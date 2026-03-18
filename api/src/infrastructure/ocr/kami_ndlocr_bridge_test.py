"""kami_ndlocr_bridge のテスト。

NDLOCR-Lite 本体は不要。JSON/XML パース・結合ロジックとエラーハンドリングを検証する。
"""

from __future__ import annotations

import json
import os
import stat
import tempfile

import pytest

from .kami_ndlocr_bridge import (
    LineResult,
    _combine_lines,
    _extract_lines_from_xml,
    _find_output_file,
    _parse_json_output,
    parse_ndlocr_output,
)


def _write_file(directory: str, content: str, filename: str) -> str:
    """テスト用ファイルを出力する。"""
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


class TestExtractLinesFromXml:
    """XML の LINE 要素抽出テスト。"""

    def test_single_line(self) -> None:
        import xml.etree.ElementTree as ET

        xml = '<OCRDATASET><PAGE><LINE STRING="テスト" CONF="0.92" ORDER="1"/></PAGE></OCRDATASET>'
        root = ET.fromstring(xml)
        lines = _extract_lines_from_xml(root)

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
        lines = _extract_lines_from_xml(root)

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
        lines = _extract_lines_from_xml(root)

        assert len(lines) == 1
        assert lines[0].text == "有効"

    def test_no_string_attribute_skipped(self) -> None:
        import xml.etree.ElementTree as ET

        xml = '<OCRDATASET><PAGE><LINE CONF="0.5" ORDER="1"/></PAGE></OCRDATASET>'
        root = ET.fromstring(xml)
        lines = _extract_lines_from_xml(root)

        assert len(lines) == 0

    def test_invalid_conf_defaults_to_zero(self) -> None:
        import xml.etree.ElementTree as ET

        xml = '<OCRDATASET><PAGE><LINE STRING="abc" CONF="invalid" ORDER="1"/></PAGE></OCRDATASET>'
        root = ET.fromstring(xml)
        lines = _extract_lines_from_xml(root)

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
        lines = _extract_lines_from_xml(root)

        assert len(lines) == 1
        assert lines[0].text == "ネスト"


class TestCombineLines:
    """行結合と加重平均信頼度のテスト。"""

    def test_single_line(self) -> None:
        lines = [LineResult(text="テスト", confidence=0.93, order=1)]
        text, conf = _combine_lines(lines)
        assert text == "テスト"
        assert conf == pytest.approx(0.93)

    def test_order_sorted(self) -> None:
        lines = [
            LineResult(text="世界", confidence=0.90, order=2),
            LineResult(text="こんにちは", confidence=0.95, order=1),
        ]
        text, conf = _combine_lines(lines)
        assert text == "こんにちは世界"

    def test_weighted_average(self) -> None:
        # "AB" (2文字, conf=1.0) + "CDEF" (4文字, conf=0.5)
        # 加重平均 = (2*1.0 + 4*0.5) / 6 = 4.0/6 ≈ 0.6667
        lines = [
            LineResult(text="AB", confidence=1.0, order=1),
            LineResult(text="CDEF", confidence=0.5, order=2),
        ]
        text, conf = _combine_lines(lines)
        assert text == "ABCDEF"
        assert conf == pytest.approx(2 / 3, abs=0.001)

    def test_empty_list(self) -> None:
        text, conf = _combine_lines([])
        assert text == ""
        assert conf == 0.0


class TestParseJsonOutput:
    """NDLOCR-Lite JSON 出力のパースト。"""

    def test_single_item(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                "contents": [
                    [
                        {
                            "text": "株式会社テスト",
                            "confidence": 0.93,
                            "id": 0,
                            "isVertical": "false",
                            "isTextline": "true",
                        }
                    ]
                ],
                "imginfo": {"img_width": 800, "img_height": 600},
            }
            _write_file(tmpdir, json.dumps(data), "result.json")
            result = _parse_json_output(tmpdir)

            assert result is not None
            text, conf = result
            assert text == "株式会社テスト"
            assert conf == pytest.approx(0.93)

    def test_multiple_items_ordered_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                "contents": [
                    [
                        {"text": "世界", "confidence": 0.88, "id": 1},
                        {"text": "こんにちは", "confidence": 0.95, "id": 0},
                    ]
                ],
            }
            _write_file(tmpdir, json.dumps(data), "result.json")
            result = _parse_json_output(tmpdir)

            assert result is not None
            text, _ = result
            assert text == "こんにちは世界"

    def test_empty_text_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                "contents": [
                    [
                        {"text": "", "confidence": 0.5, "id": 0},
                        {"text": "有効", "confidence": 0.9, "id": 1},
                    ]
                ],
            }
            _write_file(tmpdir, json.dumps(data), "result.json")
            result = _parse_json_output(tmpdir)

            assert result is not None
            text, _ = result
            assert text == "有効"

    def test_no_json_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _parse_json_output(tmpdir)
            assert result is None

    def test_invalid_json_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_file(tmpdir, "not json!", "result.json")
            result = _parse_json_output(tmpdir)
            assert result is None

    def test_empty_contents_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_file(tmpdir, json.dumps({"contents": []}), "result.json")
            result = _parse_json_output(tmpdir)
            # contents が空リスト → None（XML フォールバックへ）
            assert result is None


class TestFindOutputFile:
    """出力ファイル検索テスト。"""

    def test_flat_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_file(tmpdir, "<OCRDATASET/>", "output.xml")
            result = _find_output_file(tmpdir, "*.xml")
            assert result is not None
            assert result.endswith(".xml")

    def test_nested_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sub_dir = os.path.join(tmpdir, "subdir")
            os.makedirs(sub_dir)
            _write_file(sub_dir, "{}", "result.json")
            result = _find_output_file(tmpdir, "*.json")
            assert result is not None
            assert "result.json" in result

    def test_not_found_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _find_output_file(tmpdir, "*.xml")
            assert result is None


class TestParseNdlocrOutput:
    """parse_ndlocr_output の統合テスト（JSON 優先、XML フォールバック）。"""

    def test_json_preferred_over_xml(self) -> None:
        """JSON と XML の両方がある場合、JSON を優先する。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # JSON: "JSON結果"
            data = {"contents": [[{"text": "JSON結果", "confidence": 0.95, "id": 0}]]}
            _write_file(tmpdir, json.dumps(data), "result.json")

            # XML: "XML結果"（JSON 優先なので使われない）
            _write_file(
                tmpdir,
                '<OCRDATASET><PAGE><LINE STRING="XML結果" CONF="0.80" ORDER="1"/></PAGE></OCRDATASET>',
                "result.xml",
            )

            text, conf = parse_ndlocr_output(tmpdir)
            assert text == "JSON結果"
            assert conf == pytest.approx(0.95)

    def test_xml_fallback_when_no_json(self) -> None:
        """JSON がない場合は XML にフォールバックする。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_file(
                tmpdir,
                '<OCRDATASET><PAGE><LINE STRING="XML結果" CONF="0.85" ORDER="1"/></PAGE></OCRDATASET>',
                "result.xml",
            )
            text, conf = parse_ndlocr_output(tmpdir)
            assert text == "XML結果"
            assert conf == pytest.approx(0.85)

    def test_no_output_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            text, conf = parse_ndlocr_output(tmpdir)
            assert text == ""
            assert conf == 0.0

    def test_invalid_xml_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_file(tmpdir, "not xml at all <<<", "result.xml")
            text, conf = parse_ndlocr_output(tmpdir)
            assert text == ""
            assert conf == 0.0


class TestBridgeEndToEnd:
    """ブリッジスクリプトの E2E テスト（スタブスクリプトでNDLOCR-Liteを模擬）。"""

    @staticmethod
    def _create_stub_ndlocr_with_json(json_content: str) -> str:
        """スタブの NDLOCR-Lite ディレクトリを作成する（JSON 出力）。

        Returns:
            ndlocr_dir
        """
        ndlocr_dir = tempfile.mkdtemp(prefix="stub_ndlocr_")

        ocr_py = os.path.join(ndlocr_dir, "ocr.py")
        json_escaped = json_content.replace("\\", "\\\\").replace("'", "\\'")
        script = f"""#!/usr/bin/env python3
import argparse, os
parser = argparse.ArgumentParser()
parser.add_argument('--sourceimg')
parser.add_argument('--output')
args = parser.parse_args()
os.makedirs(args.output, exist_ok=True)
with open(os.path.join(args.output, 'result.json'), 'w') as f:
    f.write('{json_escaped}')
"""
        with open(ocr_py, "w") as f:
            f.write(script)
        os.chmod(ocr_py, stat.S_IRWXU)

        return ndlocr_dir

    @staticmethod
    def _create_stub_ndlocr_with_xml(xml_content: str) -> str:
        """スタブの NDLOCR-Lite ディレクトリを作成する（XML 出力）。"""
        ndlocr_dir = tempfile.mkdtemp(prefix="stub_ndlocr_")

        ocr_py = os.path.join(ndlocr_dir, "ocr.py")
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

        return ndlocr_dir

    def test_bridge_main_with_json_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """JSON 出力を使った正常系テスト。"""
        import io

        json_data = json.dumps({"contents": [[{"text": "12345", "confidence": 0.91, "id": 0}]]})
        ndlocr_dir = self._create_stub_ndlocr_with_json(json_data)

        monkeypatch.setattr(
            "api.src.infrastructure.ocr.kami_ndlocr_bridge.NDLOCR_LITE_DIR",
            ndlocr_dir,
        )

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG")
            img_path = f.name

        request = json.dumps({"image_path": img_path, "input_type": "printed"})
        monkeypatch.setattr("sys.stdin", io.StringIO(request))

        captured = io.StringIO()
        monkeypatch.setattr("sys.stdout", captured)

        from .kami_ndlocr_bridge import main

        main()

        os.unlink(img_path)

        output = json.loads(captured.getvalue())
        assert output["text"] == "12345"
        assert output["confidence"] == pytest.approx(0.91)

    def test_bridge_main_with_xml_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """XML フォールバックの正常系テスト。"""
        import io

        xml = '<OCRDATASET><PAGE><LINE STRING="67890" CONF="0.88" ORDER="1"/></PAGE></OCRDATASET>'
        ndlocr_dir = self._create_stub_ndlocr_with_xml(xml)

        monkeypatch.setattr(
            "api.src.infrastructure.ocr.kami_ndlocr_bridge.NDLOCR_LITE_DIR",
            ndlocr_dir,
        )

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG")
            img_path = f.name

        request = json.dumps({"image_path": img_path, "input_type": "printed"})
        monkeypatch.setattr("sys.stdin", io.StringIO(request))

        captured = io.StringIO()
        monkeypatch.setattr("sys.stdout", captured)

        from .kami_ndlocr_bridge import main

        main()

        os.unlink(img_path)

        output = json.loads(captured.getvalue())
        assert output["text"] == "67890"
        assert output["confidence"] == pytest.approx(0.88)

    def test_bridge_main_missing_image(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """存在しない画像パスで空結果を返す。"""
        import io

        ndlocr_dir = tempfile.mkdtemp(prefix="stub_ndlocr_")
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
