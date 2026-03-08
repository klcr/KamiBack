# PROGRESS — KamiBack

> 最終更新: 2026-03-08
> 前回更新: 2026-03-08

## サマリー

| 指標 | 値 |
|------|-----|
| 全体進捗 | 20% |
| 完了フェーズ | 0/6 |
| ブロッカー | 0 件 |
| 直近の完了 | Python開発環境セットアップ、ドメインテスト全93件パス、型チェック・lint全パス |

## フェーズ

| ID | 名前 | 状態 | 進捗 | 最終変動 | 備考 |
|----|------|------|------|----------|------|
| P1 | プロジェクト基盤構築 | active | 80% | 03-08 | 開発環境セットアップ完了。Web側のテスト・lint設定が残る |
| P2 | マニフェストJSON仕様策定 | active | 80% | 03-08 | ドメイン型定義＋テスト＋TS型ミラー完了。検証パス済み |
| P3 | Module A: 帳票出力エンジン | not-started | 0% | 03-08 | HTML→印刷の往路 |
| P4 | Module B: 帳票読取エンジン | not-started | 0% | 03-08 | 撮影→OCRの復路 |
| P5 | レビューUI | not-started | 0% | 03-08 | OCR結果の確認・修正画面 |
| P6 | 統合テスト・E2E | not-started | 0% | 03-08 | 往復の結合検証 |

## ブロッカー

（なし）

## 次のアクション

1. P1: Web側のテスト・lint環境を整備する（Vitest, ESLint/Biome設定）
2. P2: サンプルマニフェストJSONを作成してバリデーション動作を確認する
3. P3: Module A の HTMLパースAPI（A-1）から着手する

## diff

> 2026-03-08（3回目）

- `pyproject.toml`: `[tool.setuptools.packages.find]`を追加（editable install対応）
- Python開発環境セットアップ完了（pytest, mypy, ruff, import-linter）
- ドメインテスト全93件パス（manifest: 22, ocr_result: 35, template: 12, shared: 24）
- mypy strict: エラー0（24ファイル）
- ruff: 全チェックパス
- import-linter: 2 contracts kept, 0 broken
- P1進捗: 50% → 80%
- P2進捗: 20% → 80%

> 2026-03-08（2回目）

- `docs/milestones.md`: M1〜M6をサブマイルストーン（M1.1〜M6.4）に詳細化
- `docs/backlog/items/`: 機能番号ベースのバックログアイテム19件（A-1〜A-8, B-1〜B-11）を作成
- `docs/adr/002-module-a-processing-split.md`: Module AのPython/ブラウザ処理分担の設計判断を記録
- `docs/adr/003-manifest-flow.md`: マニフェストの生成→拡張→照合フローを記録
- P2を `active` に変更（ドメイン型定義の実装開始）
