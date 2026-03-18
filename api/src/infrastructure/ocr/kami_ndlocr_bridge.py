#!/usr/bin/env python3
"""KamiBack ↔ NDLOCR-Lite ブリッジスクリプト。

SubprocessOcrEngine から呼び出され、NDLOCR-Lite の OCR 結果を
JSON プロトコルに変換して返す。

プロトコル:
    入力（stdin）: {"image_path": "/tmp/crop.png", "input_type": "printed"}
    出力（stdout）: {"text": "認識結果", "confidence": 0.95}

使い方:
    export KAMI_OCR_ENGINE_PATH=/path/to/kami_ndlocr_bridge.py
    export NDLOCR_LITE_DIR=/path/to/ndlocr-lite/src
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)

# NDLOCR-Lite の src ディレクトリ
NDLOCR_LITE_DIR = os.environ.get(
    "NDLOCR_LITE_DIR",
    os.path.expanduser("~/ndlocr-lite/src"),
)

# NDLOCR-Lite 実行用の Python パス（別 venv を使う場合）
NDLOCR_PYTHON = os.environ.get("NDLOCR_PYTHON", sys.executable)

# タイムアウト（秒）
NDLOCR_TIMEOUT = int(os.environ.get("NDLOCR_TIMEOUT", "60"))


@dataclass(frozen=True)
class LineResult:
    """NDLOCR-Lite の LINE 要素から抽出した認識結果。"""

    text: str
    confidence: float
    order: int


def run_ndlocr(image_path: str) -> tuple[str, float]:
    """NDLOCR-Lite を実行し、テキストと信頼度を返す。

    Returns:
        (text, confidence) — text は全 LINE の結合、confidence は加重平均
    """
    image_path_obj = Path(image_path)
    if not image_path_obj.exists():
        logger.error("Image not found: %s", image_path)
        return "", 0.0

    with tempfile.TemporaryDirectory(prefix="kami_ndlocr_") as tmpdir:
        ocr_script = os.path.join(NDLOCR_LITE_DIR, "ocr.py")
        if not os.path.exists(ocr_script):
            logger.error("NDLOCR-Lite ocr.py not found: %s", ocr_script)
            return "", 0.0

        cmd = [
            NDLOCR_PYTHON,
            ocr_script,
            "--sourceimg",
            image_path,
            "--output",
            tmpdir,
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=NDLOCR_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            logger.error("NDLOCR-Lite timed out after %ds", NDLOCR_TIMEOUT)
            return "", 0.0

        if proc.returncode != 0:
            logger.error(
                "NDLOCR-Lite failed (code=%d): %s",
                proc.returncode,
                proc.stderr[:500],
            )
            return "", 0.0

        return parse_ndlocr_output(tmpdir)


def parse_ndlocr_output(output_dir: str) -> tuple[str, float]:
    """NDLOCR-Lite の XML 出力からテキストと信頼度を抽出する。

    NDLOCR-Lite の出力 XML フォーマット:
        <OCRDATASET>
          <PAGE HEIGHT="..." WIDTH="..." IMAGENAME="...">
            <LINE TYPE="本文" STRING="テキスト" CONF="0.95" ORDER="1" .../>
          </PAGE>
        </OCRDATASET>

    Returns:
        (text, confidence) — LINE を ORDER 順に結合したテキストと加重平均信頼度
    """
    xml_path = _find_xml_file(output_dir)
    if xml_path is None:
        logger.warning("No XML output found in %s", output_dir)
        return "", 0.0

    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        logger.error("Failed to parse XML: %s", e)
        return "", 0.0

    root = tree.getroot()
    lines = _extract_lines(root)

    if not lines:
        return "", 0.0

    # ORDER 順にソート
    lines.sort(key=lambda ln: ln.order)

    # テキスト結合（改行なし。ボックス単位の切出画像なので通常1行）
    text = "".join(ln.text for ln in lines)

    # 信頼度: 文字数で加重平均
    total_chars = sum(len(ln.text) for ln in lines)
    if total_chars == 0:
        return "", 0.0

    weighted_conf = sum(ln.confidence * len(ln.text) for ln in lines) / total_chars

    return text, weighted_conf


def _find_xml_file(output_dir: str) -> str | None:
    """出力ディレクトリから XML ファイルを探す。

    NDLOCR-Lite は output_dir 直下または output_dir/*/xml/ に XML を出力する。
    """
    output_path = Path(output_dir)

    # パターン1: output_dir/*/xml/*.xml（標準的な出力構造）
    xml_files = list(output_path.glob("*/xml/*.xml"))

    # パターン2: output_dir/*.xml（フラット出力）
    if not xml_files:
        xml_files = list(output_path.glob("*.xml"))

    # パターン3: output_dir/**/*.xml（再帰検索）
    if not xml_files:
        xml_files = list(output_path.rglob("*.xml"))

    if not xml_files:
        return None

    return str(xml_files[0])


def _extract_lines(root: ET.Element) -> list[LineResult]:
    """XML ルートから LINE 要素を抽出する。"""
    lines: list[LineResult] = []

    for line_elem in root.iter("LINE"):
        text = line_elem.get("STRING", "")
        if not text:
            continue

        conf_str = line_elem.get("CONF", "0.0")
        try:
            confidence = float(conf_str)
        except ValueError:
            confidence = 0.0

        order_str = line_elem.get("ORDER", "0")
        try:
            order = int(order_str)
        except ValueError:
            order = 0

        lines.append(LineResult(text=text, confidence=confidence, order=order))

    return lines


def _respond(text: str, confidence: float) -> None:
    """JSON レスポンスを stdout に出力する。"""
    confidence = max(0.0, min(1.0, confidence))
    print(
        json.dumps({"text": text, "confidence": confidence}, ensure_ascii=False),
        flush=True,
    )


def main() -> None:
    """メインエントリーポイント。stdin から JSON を読み、OCR を実行して stdout に返す。"""
    try:
        raw = sys.stdin.read()
        request = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Invalid JSON input: %s", e)
        _respond("", 0.0)
        return

    image_path = request.get("image_path", "")
    if not image_path:
        logger.error("Missing image_path in request")
        _respond("", 0.0)
        return

    # input_type は将来のエンジン切替に使用
    # 現時点では NDLOCR-Lite は input_type を区別しない
    text, confidence = run_ndlocr(image_path)
    _respond(text, confidence)


if __name__ == "__main__":
    main()
