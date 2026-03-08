# ADR 001: 技術スタック選定

## ステータス

承認

## コンテキスト

帳票OCRマッピングシステムの技術スタックを選定する必要がある。システムは以下の3レイヤーで構成される:

- **Domain + API**: 帳票の座標管理、OCR処理、画像処理
- **Web**: OCR結果のレビューUI

## 決定

| 項目 | 選択 |
|------|------|
| Domain + API 言語 | Python |
| Web 言語 | TypeScript |
| API フレームワーク | FastAPI |
| Web フレームワーク | React + Vite |
| OCR エンジン | NDLOCR-Lite（PARSeq） |
| 画像処理 | OpenCV |
| テスト | pytest / Vitest |
| Linter | Ruff / ESLint |
| Formatter | Ruff format / Prettier |
| 依存チェック | import-linter |

## 理由

### Python（Domain + API）

- OpenCV、NDLOCR-Lite 等のCV/OCRライブラリとの親和性が最も高い
- 科学計算・画像処理のエコシステムが充実（NumPy、Pillow等）
- FastAPI は非同期対応・自動ドキュメント生成を備え、APIサーバーとして十分

### TypeScript（Web）

- React + Vite はレビューUIのSPAとして軽量・高速
- 型安全性によりドメイン型との整合性を保ちやすい

### NDLOCR-Lite

- 国立国会図書館が公開するOCRツール
- PARSeq ベースの文字認識を含む
- 日本語帳票のOCRに適している

## 結果

- Python と TypeScript の2言語構成となるため、ドメイン型の定義を両言語で同期する必要がある
- マニフェストJSONがその同期手段となる（JSON Schema → 型生成の可能性）
