#!/usr/bin/env python3
"""KamiBack ↔ NDLOCR-Lite ブリッジスクリプト。

SubprocessOcrEngine から呼び出され、NDLOCR-Lite の OCR 結果を
JSON プロトコルに変換して返す。

プロトコル:
    入力（stdin）: {"image_path": "/tmp/crop.png", "input_type": "printed"}
    出力（stdout）: {"text": "認識結果", "confidence": 0.95}

出力の解析:
    NDLOCR-Lite は JSON と XML の両形式で結果を出力する。
    本スクリプトは JSON を優先し、見つからない場合は XML にフォールバックする。

信頼度について:
    NDLOCR-Lite の CONF はレイアウト検出（DEIMv2）の信頼度であり、
    文字認識（PARSeq）の信頼度ではない。PARSeq は argmax で文字を
    選択するため、認識信頼度を出力しない。このため CONF 値は
    「その領域にテキストが存在する確信度」として扱う。

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
    """NDLOCR-Lite の認識結果1行分。"""

    text: str
    confidence: float
    order: int


def run_ndlocr(image_path: str) -> tuple[str, float]:
    """NDLOCR-Lite を実行し、テキストと信頼度を返す。

    Returns:
        (text, confidence) — text は全行の結合、confidence は加重平均
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
    """NDLOCR-Lite の出力からテキストと信頼度を抽出する。

    JSON 出力を優先し、見つからない場合は XML にフォールバックする。

    Returns:
        (text, confidence) — 行を ORDER 順に結合したテキストと加重平均信頼度
    """
    # JSON を優先（パースが容易、構造が明確）
    json_result = _parse_json_output(output_dir)
    if json_result is not None:
        return json_result

    # XML にフォールバック
    return _parse_xml_output(output_dir)


def _parse_json_output(output_dir: str) -> tuple[str, float] | None:
    """NDLOCR-Lite の JSON 出力をパースする。

    JSON フォーマット:
        {
          "contents": [[
            {"text": "...", "confidence": 0.95, "id": 0, ...},
            ...
          ]],
          "imginfo": {...}
        }

    Returns:
        (text, confidence) or None（JSON が見つからない場合）
    """
    json_path = _find_output_file(output_dir, "*.json")
    if json_path is None:
        return None

    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to parse JSON: %s", e)
        return None

    contents = data.get("contents")
    if not contents or not isinstance(contents, list):
        return None

    lines: list[LineResult] = []
    for page in contents:
        if not isinstance(page, list):
            continue
        for item in page:
            text = item.get("text", "")
            if not text:
                continue
            confidence = float(item.get("confidence", 0.0))
            order = int(item.get("id", 0))
            lines.append(LineResult(text=text, confidence=confidence, order=order))

    return _combine_lines(lines)


def _parse_xml_output(output_dir: str) -> tuple[str, float]:
    """NDLOCR-Lite の XML 出力をパースする。

    XML フォーマット:
        <OCRDATASET>
          <PAGE HEIGHT="..." WIDTH="..." IMAGENAME="...">
            <TEXTBLOCK CONF="...">
              <LINE TYPE="本文" STRING="テキスト" CONF="0.95" ORDER="1" .../>
            </TEXTBLOCK>
          </PAGE>
        </OCRDATASET>

    Returns:
        (text, confidence)
    """
    xml_path = _find_output_file(output_dir, "*.xml")
    if xml_path is None:
        logger.warning("No output found in %s", output_dir)
        return "", 0.0

    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        logger.error("Failed to parse XML: %s", e)
        return "", 0.0

    root = tree.getroot()
    lines = _extract_lines_from_xml(root)

    return _combine_lines(lines)


def _combine_lines(lines: list[LineResult]) -> tuple[str, float]:
    """LineResult のリストからテキストと加重平均信頼度を算出する。"""
    if not lines:
        return "", 0.0

    # ORDER 順にソート
    lines.sort(key=lambda ln: ln.order)

    # テキスト結合（ボックス単位の切出画像なので通常1行）
    text = "".join(ln.text for ln in lines)

    # 信頼度: 文字数で加重平均
    total_chars = sum(len(ln.text) for ln in lines)
    if total_chars == 0:
        return "", 0.0

    weighted_conf = sum(ln.confidence * len(ln.text) for ln in lines) / total_chars

    return text, weighted_conf


def _find_output_file(output_dir: str, glob_pattern: str) -> str | None:
    """出力ディレクトリからファイルを探す。

    NDLOCR-Lite は output_dir 直下にフラットに出力する。
    """
    output_path = Path(output_dir)

    # パターン1: output_dir/*.ext（フラット出力 — NDLOCR-Lite の標準）
    files = list(output_path.glob(glob_pattern))

    # パターン2: output_dir/**/*.ext（再帰検索）
    if not files:
        files = list(output_path.rglob(glob_pattern))

    if not files:
        return None

    return str(files[0])


def _extract_lines_from_xml(root: ET.Element) -> list[LineResult]:
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
