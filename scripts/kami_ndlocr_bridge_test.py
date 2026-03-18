"""kami_ndlocr_bridge の XML パースロジックのテスト。"""

from __future__ import annotations

import os
import tempfile

import pytest
from kami_ndlocr_bridge import find_xml_file, parse_ndlocr_xml


def _write_xml(content: str) -> str:
    """XML 文字列を一時ファイルに書き出してパスを返す。"""
    fd, path = tempfile.mkstemp(suffix=".xml")
    os.write(fd, content.encode("utf-8"))
    os.close(fd)
    return path


class TestParseNdlocrXml:
    """parse_ndlocr_xml のテスト。"""

    def test_single_line(self) -> None:
        xml = """<?xml version='1.0' encoding='utf-8'?>
<OCRDATASET>
  <PAGE HEIGHT="100" WIDTH="200" IMAGENAME="test.png">
    <TEXTBLOCK CONF="0.90">
      <LINE TYPE="本文" X="10" Y="20" WIDTH="80" HEIGHT="30"
            CONF="0.95" STRING="テスト文字列" ORDER="0"
            TITLE="FALSE" AUTHOR="FALSE" />
    </TEXTBLOCK>
  </PAGE>
</OCRDATASET>"""
        path = _write_xml(xml)
        try:
            text, conf = parse_ndlocr_xml(path)
            assert text == "テスト文字列"
            assert conf == pytest.approx(0.95)
        finally:
            os.unlink(path)

    def test_multiple_lines_ordered(self) -> None:
        """複数 LINE が ORDER 順に結合される。"""
        xml = """<?xml version='1.0' encoding='utf-8'?>
<OCRDATASET>
  <PAGE HEIGHT="500" WIDTH="300" IMAGENAME="test.png">
    <TEXTBLOCK CONF="0.85">
      <LINE TYPE="本文" X="10" Y="100" WIDTH="50" HEIGHT="20"
            CONF="0.90" STRING="世界" ORDER="1"
            TITLE="FALSE" AUTHOR="FALSE" />
      <LINE TYPE="本文" X="10" Y="50" WIDTH="50" HEIGHT="20"
            CONF="0.80" STRING="こんにちは" ORDER="0"
            TITLE="FALSE" AUTHOR="FALSE" />
    </TEXTBLOCK>
  </PAGE>
</OCRDATASET>"""
        path = _write_xml(xml)
        try:
            text, conf = parse_ndlocr_xml(path)
            assert text == "こんにちは世界"
            assert conf == pytest.approx(0.85)
        finally:
            os.unlink(path)

    def test_block_with_string_no_child_lines(self) -> None:
        """LINE を持たない BLOCK の STRING も取得される。"""
        xml = """<?xml version='1.0' encoding='utf-8'?>
<OCRDATASET>
  <PAGE HEIGHT="500" WIDTH="300" IMAGENAME="test.png">
    <TEXTBLOCK CONF="0.90">
      <LINE TYPE="本文" X="10" Y="50" WIDTH="50" HEIGHT="20"
            CONF="0.90" STRING="本文" ORDER="0"
            TITLE="FALSE" AUTHOR="FALSE" />
    </TEXTBLOCK>
    <BLOCK TYPE="ノンブル" X="100" Y="10" WIDTH="30" HEIGHT="20"
           CONF="0.99" STRING="42" />
  </PAGE>
</OCRDATASET>"""
        path = _write_xml(xml)
        try:
            text, conf = parse_ndlocr_xml(path)
            assert text == "本文42"
            assert conf == pytest.approx((0.90 + 0.99) / 2)
        finally:
            os.unlink(path)

    def test_block_with_child_lines_ignores_block_string(self) -> None:
        """LINE を持つ BLOCK の STRING は無視される（LINE から取得済み）。"""
        xml = """<?xml version='1.0' encoding='utf-8'?>
<OCRDATASET>
  <PAGE HEIGHT="500" WIDTH="300" IMAGENAME="test.png">
    <BLOCK TYPE="広告" X="10" Y="50" WIDTH="200" HEIGHT="100"
           CONF="0.80" STRING="広告テキスト">
      <LINE TYPE="広告文字" X="20" Y="60" WIDTH="100" HEIGHT="20"
            CONF="0.85" STRING="広告内の文字" ORDER="0"
            TITLE="FALSE" AUTHOR="FALSE" />
    </BLOCK>
  </PAGE>
</OCRDATASET>"""
        path = _write_xml(xml)
        try:
            text, conf = parse_ndlocr_xml(path)
            assert text == "広告内の文字"
            assert conf == pytest.approx(0.85)
        finally:
            os.unlink(path)

    def test_empty_page(self) -> None:
        """認識結果がない場合は空文字列と信頼度 0.0。"""
        xml = """<?xml version='1.0' encoding='utf-8'?>
<OCRDATASET>
  <PAGE HEIGHT="100" WIDTH="200" IMAGENAME="blank.png">
  </PAGE>
</OCRDATASET>"""
        path = _write_xml(xml)
        try:
            text, conf = parse_ndlocr_xml(path)
            assert text == ""
            assert conf == 0.0
        finally:
            os.unlink(path)

    def test_multiple_textblocks(self) -> None:
        """複数 TEXTBLOCK にまたがる LINE も ORDER 順で結合される。"""
        xml = """<?xml version='1.0' encoding='utf-8'?>
<OCRDATASET>
  <PAGE HEIGHT="500" WIDTH="300" IMAGENAME="test.png">
    <TEXTBLOCK CONF="0.90">
      <LINE TYPE="本文" X="10" Y="50" WIDTH="50" HEIGHT="20"
            CONF="0.95" STRING="最初の" ORDER="0"
            TITLE="FALSE" AUTHOR="FALSE" />
    </TEXTBLOCK>
    <TEXTBLOCK CONF="0.85">
      <LINE TYPE="本文" X="10" Y="150" WIDTH="50" HEIGHT="20"
            CONF="0.80" STRING="段落" ORDER="1"
            TITLE="FALSE" AUTHOR="FALSE" />
    </TEXTBLOCK>
  </PAGE>
</OCRDATASET>"""
        path = _write_xml(xml)
        try:
            text, conf = parse_ndlocr_xml(path)
            assert text == "最初の段落"
            assert conf == pytest.approx((0.95 + 0.80) / 2)
        finally:
            os.unlink(path)

    def test_line_with_empty_string(self) -> None:
        """STRING が空の LINE は結果に含まれるが空文字列。"""
        xml = """<?xml version='1.0' encoding='utf-8'?>
<OCRDATASET>
  <PAGE HEIGHT="100" WIDTH="200" IMAGENAME="test.png">
    <TEXTBLOCK CONF="0.50">
      <LINE TYPE="本文" X="10" Y="20" WIDTH="80" HEIGHT="30"
            CONF="0.50" STRING="" ORDER="0"
            TITLE="FALSE" AUTHOR="FALSE" />
    </TEXTBLOCK>
  </PAGE>
</OCRDATASET>"""
        path = _write_xml(xml)
        try:
            text, conf = parse_ndlocr_xml(path)
            assert text == ""
            assert conf == pytest.approx(0.50)
        finally:
            os.unlink(path)


class TestFindXmlFile:
    """find_xml_file のテスト。"""

    def test_finds_xml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = os.path.join(tmpdir, "result.xml")
            with open(xml_path, "w") as f:
                f.write("<root/>")
            assert find_xml_file(tmpdir) == xml_path

    def test_returns_none_when_no_xml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = os.path.join(tmpdir, "result.txt")
            with open(txt_path, "w") as f:
                f.write("not xml")
            assert find_xml_file(tmpdir) is None

    def test_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            assert find_xml_file(tmpdir) is None
