# NDLOCR-Lite セットアップガイド

KamiBack の Module B（帳票読取エンジン）が使用する OCR エンジン。
国立国会図書館が開発・公開している軽量 OCR で、GPU なしで動作する。

## 概要

| 項目 | 内容 |
|------|------|
| 開発元 | 国立国会図書館（NDL） |
| ライセンス | CC BY 4.0（商用利用可） |
| 動作環境 | Windows 11 / macOS (Apple Silicon) / Linux (Ubuntu 22.04) |
| Python | 3.10 以上 |
| GPU | 不要（CUDA はベータ対応） |
| 技術構成 | レイアウト認識（DEIMv2） + 文字列認識（PARSeq） + 読み順整序 |

## リンク

| リソース | URL |
|----------|-----|
| GitHub リポジトリ | https://github.com/ndl-lab/ndlocr-lite |
| NDLラボ公式ページ | https://lab.ndl.go.jp/news/2025/2026-02-24/ |
| 使い方ガイド | https://lab.ndl.go.jp/data_set/ndlocrlite-usage/ |
| NDLOCR-Lite Web（ブラウザ版） | https://ndlocr-liteweb.netlify.app/ |

## インストール

### 方法 1: pip（推奨）

```bash
git clone https://github.com/ndl-lab/ndlocr-lite.git
cd ndlocr-lite
pip install -r requirements.txt
```

### 方法 2: uv

```bash
git clone https://github.com/ndl-lab/ndlocr-lite.git
cd ndlocr-lite
uv tool install .
```

### 方法 3: GUIアプリ

[Releases ページ](https://github.com/ndl-lab/ndlocr-lite/releases) からプラットフォーム別のアーカイブをダウンロードして展開する。

> **注意**: アプリケーションのパスに全角文字が含まれると起動に失敗する場合がある。

## 動作確認

```bash
cd ndlocr-lite/src

# 単一画像
python3 ocr.py --sourceimg /path/to/image.jpg --output /tmp/ocr_out

# ディレクトリ（JPG/PNG/TIFF/JP2/BMP を一括処理）
python3 ocr.py --sourcedir /path/to/images/ --output /tmp/ocr_out

# 認識結果を可視化（青枠付き画像を出力）
python3 ocr.py --sourceimg /path/to/image.jpg --output /tmp/ocr_out --viz True
```

出力は `--output` ディレクトリに XML 形式で生成される。

## KamiBack との接続

KamiBack の `SubprocessOcrEngine` は以下の JSON プロトコルで OCR エンジンを呼び出す。
NDLOCR-Lite はこのプロトコルに直接対応していないため、**ラッパースクリプト**が必要。

### プロトコル仕様

**入力**（stdin に JSON）:

```json
{"image_path": "/tmp/crop_xxx.png", "input_type": "printed"}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `image_path` | string | 切り出されたボックス画像のパス（PNG） |
| `input_type` | string | `printed` / `handwritten_number` / `handwritten_kana` / `checkbox` |

**出力**（stdout に JSON）:

```json
{"text": "認識結果", "confidence": 0.95}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `text` | string | OCR 認識テキスト |
| `confidence` | float | 信頼度スコア（0.0〜1.0） |

### ラッパースクリプトの例

以下は NDLOCR-Lite を KamiBack のプロトコルに接続するラッパースクリプトのテンプレート。
実際の実装は NDLOCR-Lite の出力フォーマット（XML）に合わせて調整が必要。

```python
#!/usr/bin/env python3
"""KamiBack ↔ NDLOCR-Lite ブリッジスクリプト。

SubprocessOcrEngine から呼び出され、NDLOCR-Lite の OCR 結果を
JSON プロトコルに変換して返す。

使い方:
    export KAMI_OCR_ENGINE_PATH=/path/to/kami_ndlocr_bridge.py
"""

import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

# NDLOCR-Lite の ocr.py のパス
NDLOCR_LITE_DIR = os.environ.get(
    "NDLOCR_LITE_DIR",
    os.path.expanduser("~/ndlocr-lite/src"),
)


def run_ndlocr(image_path: str) -> tuple[str, float]:
    """NDLOCR-Lite を実行し、テキストと信頼度を返す。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        proc = subprocess.run(
            [
                sys.executable,
                os.path.join(NDLOCR_LITE_DIR, "ocr.py"),
                "--sourceimg", image_path,
                "--output", tmpdir,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if proc.returncode != 0:
            print(
                json.dumps({"text": "", "confidence": 0.0}),
                flush=True,
            )
            return "", 0.0

        # NDLOCR-Lite の出力 XML をパースしてテキストを抽出
        text, confidence = parse_ndlocr_output(tmpdir)
        return text, confidence


def parse_ndlocr_output(output_dir: str) -> tuple[str, float]:
    """NDLOCR-Lite の XML 出力からテキストと信頼度を抽出する。

    TODO: NDLOCR-Lite の実際の XML スキーマに合わせて実装する。
    以下はプレースホルダー実装。
    """
    # output_dir 内の XML ファイルを探す
    xml_files = [
        f for f in os.listdir(output_dir)
        if f.endswith(".xml")
    ]

    if not xml_files:
        return "", 0.0

    # 最初の XML を読む
    tree = ET.parse(os.path.join(output_dir, xml_files[0]))
    root = tree.getroot()

    # テキストを結合（実際の要素名は NDLOCR-Lite の出力に合わせて調整）
    texts = []
    for elem in root.iter():
        if elem.text and elem.text.strip():
            texts.append(elem.text.strip())

    text = " ".join(texts)

    # NDLOCR-Lite は信頼度スコアを直接出力しない場合がある
    # その場合はテキストの有無で暫定的にスコアを設定する
    confidence = 0.8 if text else 0.0

    return text, confidence


def main() -> None:
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
```

### 環境変数の設定

```bash
# ラッパースクリプトのパスを設定
export KAMI_OCR_ENGINE_PATH=/path/to/kami_ndlocr_bridge.py

# NDLOCR-Lite の src ディレクトリ
export NDLOCR_LITE_DIR=/path/to/ndlocr-lite/src

# タイムアウト（秒、デフォルト: 30）
export KAMI_OCR_ENGINE_TIMEOUT=60
```

## 依存関係の分離

NDLOCR-Lite は PyTorch + ONNX Runtime 等の大規模パッケージに依存する。
KamiBack 本体の venv とは別の環境にインストールすることを推奨する。

```
KamiBack venv           NDLOCR-Lite venv（または conda 環境）
  │                       │
  └─ SubprocessOcrEngine ─┘  ← サブプロセス呼出しなので venv が別でも動作
```

ラッパースクリプトの shebang を NDLOCR-Lite 側の Python に向ければよい:

```python
#!/path/to/ndlocr-lite-venv/bin/python3
```

## inputType 別の対応状況

| inputType | NDLOCR-Lite 対応 | 備考 |
|-----------|-----------------|------|
| `printed`（活字） | 対応 | メインの用途 |
| `handwritten_number`（手書き数字） | 実験的対応 | 精度要検証 |
| `handwritten_kana`（手書き仮名） | 実験的対応 | 精度要検証 |
| `checkbox`（チェックマーク） | 非対応 | 画像処理ベースの判定を別途実装予定 |

> checkbox の判定は OCR エンジンではなく、画像の黒画素比率等で判定する方式を検討中。
> この場合は `SubprocessOcrEngine` とは別の `CheckboxDetector` 実装が必要になる。

## トラブルシューティング

| 症状 | 原因 | 対策 |
|------|------|------|
| `OcrEngineError: パスが設定されていません` | `KAMI_OCR_ENGINE_PATH` 未設定 | 環境変数を設定する |
| `OcrEngineError: 見つかりません` | パスが不正、または実行権限なし | `chmod +x` と パスの確認 |
| `OcrEngineError: タイムアウト` | 初回起動でモデル読込に時間がかかる | `KAMI_OCR_ENGINE_TIMEOUT=120` に延長 |
| `OcrEngineError: エラーで終了` | NDLOCR-Lite 側のエラー | ラッパースクリプトの stderr を確認 |
| 認識精度が低い | 画像前処理が不適切 | 二値化パラメータの調整（`PreprocessParams`） |

## 設計判断との関係

- **DJ-3**: サブプロセス呼出し → 将来 HTTP 化（`HttpOcrEngine` に差替え）
- **DJ-7**: inputType 別閾値テーブル（B-9 で実装予定）
- **設計原則 #3**: エンジンの差し替えを前提にする
