#!/usr/bin/env python3
"""KamiBack ↔ NDLOCR-Lite ブリッジスクリプト。

SubprocessOcrEngine から呼び出され、NDLOCR-Lite を実行し、
XML 出力をパースして JSON プロトコルに変換して返す。

プロトコル:
    入力（stdin）: {"image_path": "/tmp/crop_xxx.png", "input_type": "printed"}
    出力（stdout）: {"text": "認識結果", "confidence": 0.95}

環境変数:
    NDLOCR_LITE_DIR: NDLOCR-Lite の src ディレクトリパス

使い方:
    export KAMI_OCR_ENGINE_PATH=/path/to/kami_ndlocr_bridge.py
    export NDLOCR_LITE_DIR=/path/to/ndlocr-lite/src
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

NDLOCR_LITE_DIR = os.environ.get(
    "NDLOCR_LITE_DIR",
    os.path.expanduser("~/ndlocr-lite/src"),
)


def parse_ndlocr_xml(xml_path: str) -> tuple[str, float]:
    """NDLOCR-Lite の XML 出力からテキストと信頼度を抽出する。

    NDLOCR-Lite の XML 構造:
        <OCRDATASET>
          <PAGE HEIGHT="..." WIDTH="..." IMAGENAME="...">
            <TEXTBLOCK CONF="...">
              <LINE TYPE="本文" X="..." Y="..." WIDTH="..." HEIGHT="..."
                    CONF="0.95" STRING="テキスト" ORDER="0" ... />
            </TEXTBLOCK>
            <BLOCK TYPE="ノンブル" ... STRING="29" CONF="0.99" />
          </PAGE>
        </OCRDATASET>

    テキストは LINE 要素の STRING 属性に、信頼度は CONF 属性に格納される。
    BLOCK 要素にも STRING 属性を持つものがある（ノンブル等）。

    Args:
        xml_path: NDLOCR-Lite が出力した XML ファイルのパス

    Returns:
        (認識テキスト, 平均信頼度) のタプル
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    lines: list[tuple[int, str, float]] = []

    for line_elem in root.iter("LINE"):
        order = int(line_elem.get("ORDER", "0"))
        text = line_elem.get("STRING", "")
        conf = float(line_elem.get("CONF", "0.0"))
        lines.append((order, text, conf))

    # BLOCK 要素で STRING を持つもの（ノンブル等）も取得
    for block_elem in root.iter("BLOCK"):
        block_string = block_elem.get("STRING", "")
        if block_string:
            block_conf = float(block_elem.get("CONF", "0.0"))
            # BLOCK 内の LINE は既に上で取得済みなので、
            # BLOCK 自身の STRING は LINE を持たない場合のみ使う
            has_child_lines = any(True for _ in block_elem.iter("LINE"))
            if not has_child_lines:
                # ORDER 属性がないので末尾に追加
                max_order = max((o for o, _, _ in lines), default=-1)
                lines.append((max_order + 1, block_string, block_conf))

    if not lines:
        return "", 0.0

    lines.sort(key=lambda x: x[0])

    full_text = "".join(t for _, t, _ in lines)
    avg_confidence = sum(c for _, _, c in lines) / len(lines)

    return full_text, avg_confidence


def find_xml_file(output_dir: str) -> str | None:
    """出力ディレクトリから XML ファイルを探す。"""
    for f in os.listdir(output_dir):
        if f.endswith(".xml"):
            return os.path.join(output_dir, f)
    return None


def run_ndlocr(image_path: str) -> tuple[str, float]:
    """NDLOCR-Lite を実行し、テキストと信頼度を返す。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        proc = subprocess.run(
            [
                sys.executable,
                os.path.join(NDLOCR_LITE_DIR, "ocr.py"),
                "--sourceimg",
                image_path,
                "--output",
                tmpdir,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if proc.returncode != 0:
            print(f"NDLOCR-Lite error: {proc.stderr[:500]}", file=sys.stderr)
            return "", 0.0

        xml_path = find_xml_file(tmpdir)
        if xml_path is None:
            print("NDLOCR-Lite produced no XML output", file=sys.stderr)
            return "", 0.0

        return parse_ndlocr_xml(xml_path)


def main() -> None:
    """stdin から JSON リクエストを読み、OCR 結果を stdout に返す。"""
    request = json.loads(sys.stdin.read())
    image_path = request["image_path"]
    # input_type は将来のエンジン切替に使用（現時点では未使用）
    # input_type = request.get("input_type", "printed")

    text, confidence = run_ndlocr(image_path)

    print(
        json.dumps({"text": text, "confidence": confidence}, ensure_ascii=False),
        flush=True,
    )


if __name__ == "__main__":
    main()
