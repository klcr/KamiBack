# PROGRESS — KamiBack

> 最終更新: 2026-03-16
> 前回更新: 2026-03-08

## サマリー

| 指標 | 値 |
|------|-----|
| 全体進捗 | 45% |
| 完了フェーズ | 2/6 (P1, P2) |
| ブロッカー | 0 件 |
| 直近の完了 | P4設計判断9件確定（ADR-004）、フェーズ追跡ドキュメント作成 |

## フェーズ

| ID | 名前 | 状態 | 進捗 | 最終変動 | 備考 |
|----|------|------|------|----------|------|
| P1 | プロジェクト基盤構築 | done | 100% | 03-08 | Vitest/tsconfig strict/Biome lint 全セットアップ完了 |
| P2 | マニフェストJSON仕様策定 | done | 100% | 03-08 | サンプルJSON2種+TS型ミラー+バリデーションテスト完了 |
| P3 | Module A: 帳票出力エンジン | active | 100% | 03-08 | A-1〜A-8 全実装完了。VG-1検証待ち |
| P4 | Module B: 帳票読取エンジン | active | 5% | 03-16 | 設計判断確定。M4a実装準備中 |
| P5 | レビューUI | not-started | 0% | 03-08 | OCR結果の確認・修正画面 |
| P6 | 統合テスト・E2E | not-started | 0% | 03-08 | 往復の結合検証 |

## ビジョン検証ゲート

| ゲート | 仮説 | 前提 | 状態 | 判定日 | 備考 |
|--------|------|------|------|--------|------|
| VG-1 | 座標の往復一貫性 | M3b + M4a | 未検証 | — | 人間による実プリンタ出力の実測が必要 |
| VG-2 | 手入力よりスループット向上 | M4b | 未検証 | — | 業務担当者による時間計測が必要 |
| VG-3 | 現場担当者が迷わず操作可能 | M5 | 未検証 | — | 非IT担当者3名以上の操作テストが必要 |

> ゲートが `未検証` の間は、そのゲートの前提マイルストーンの次フェーズに進行しない。
> 判定は人間のみが行う。詳細は `docs/vision-gates/README.md` を参照。

## ブロッカー

（なし）

## 次のアクション

1. VG-1: 座標の往復一貫性を実プリンタ出力で検証する（人間による判定）
2. P4/M4a: OpenCV + pyzbar 依存追加 → HoughTomboDetector 実装（B-3）
3. P4/M4a: ImageStorage IF定義 + LocalFileImageStorage 実装
4. P4/M4a: PerspectiveCorrector + 画像前処理パイプライン（B-4, B-5）
5. P4/M4a: correct_image ユースケース + API エンドポイント

## diff

> 2026-03-16（5回目）

- P4（Module B）設計判断9件を確定し ADR-004 に記録:
  - DJ-1: mm↔pixel変換はトンボ間距離から逆算
  - DJ-2: 3点トンボ時は幾何推定＋歪み閾値判定
  - DJ-3: OCRエンジンはサブプロセス呼出（HTTP移行想定）
  - DJ-4: ページ識別コードはQRコード
  - DJ-5: QR読取失敗時はリトライ3回→手動選択
  - DJ-6: OCR結果はSSEで逐次送信
  - DJ-7: 信頼度閾値はinputType別テーブル
  - DJ-8: 補正画像はファイルシステム保持（S3移行想定）
  - DJ-9: ユースケースは2段階（correct_image + execute_ocr）
- フェーズ追跡ドキュメント作成: `docs/phase-tracking/P4-module-b-scan-ocr.md`
- P4状態: not-started → active (5%)

> 2026-03-08（4回目）

- P1完了: Vitest + testing-library + jsdom セットアップ、tsconfig strict: true
- P2完了: サンプルマニフェストJSON 2種（A4縦5フィールド、A3横10フィールド）、TS型ミラー追加
- P3(Module A) 全タスク実装完了:
  - A-1: HTMLパースAPI（BeautifulSoup DOM解析 + マニフェストJSON抽出）
  - A-2: マニフェスト検証API（日本語エラーメッセージ）
  - A-3: 変数一覧抽出シリアライザ
  - A-4: useVariableBinding フック + VariableBindingView
  - A-5: トンボ自動挿入API + TomboOverlay SVG描画
  - A-6: PageIdCode ページ識別コード
  - A-7/A-8: PrintPreviewPage（iframe + @media print）
- テスト: 125 Python + 13 Web = 138件全パス
- mypy strict: エラー0（37ファイル）
- ruff/biome: 全パス
- import-linter: 2 contracts kept, 0 broken
- 全体進捗: 20% → 45%

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
