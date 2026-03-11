# KamiBack — 帳票OCRマッピングシステム

## プロジェクト概要

紙の帳票を「構造化データの一時的な入れ物」にするシステム。帳票HTMLにはボックスの座標と変数名が定義されている。このシステムは、そのmm座標を使って値を紙の上に配置し（往路）、同じmm座標を使って紙の上から値を読み取る（復路）。同一の座標定義が往復で使い回される。

- **Module A（往路）**: マニフェストJSONの座標定義に基づき、HTMLテンプレートに値を差し込んで帳票を印刷する
- **Module B（復路）**: 撮影画像からトンボを検出し、射影変換で歪みを補正し、マニフェストのmm座標でボックスを切り出してOCRを実行する

## 判断基準（要約）

迷ったときに立ち返る基準。優先度の高い順。詳細と実例は `docs/design-principles.md` を参照。

| # | 基準 | 要点 |
|---|------|------|
| 1 | **座標が嘘をつかないこと** | マニフェストのmm座標が印刷物・補正画像上の位置と一致すること。最優先 |
| 2 | **現場の人間が迷わないこと** | 技術的なエラーではなく、ユーザーが取るべき行動を伝える |
| 3 | **構造が既知である前提を最大限に使う** | 汎用OCRではなく、帳票構造の事前知識を活用する |
| 4 | **事前学習に依存しない** | トンボ検出はハフ変換、歪み補正は射影変換。古典的CV手法で動く |
| 5 | **片方のモジュールだけでも価値がある** | Module AだけでもModule Bだけでも単独で動く設計 |
| 6 | **誤差は隠さず、伝える** | 座標のずれ、OCR信頼度、画像品質判定をすべて呼び出し側に伝える |

## アーキテクチャ

- DDD（ドメイン駆動設計）+ レイヤードアーキテクチャ
- Python（Domain + API）+ TypeScript（Web）

### 技術スタック

| 項目 | 選択 |
|------|------|
| API | FastAPI |
| Web UI | React + Vite（レビューUI） |
| OCR | NDLOCR-Lite |
| CV | OpenCV（トンボ検出、射影変換、適応的二値化） |
| テスト | pytest / Vitest |
| Linter | Ruff / ESLint |
| Formatter | Ruff format / Prettier |
| 依存チェック | import-linter |

## パッケージ構成

- `domain/` — ドメイン層（型定義、エンティティ、ビジネスルール）。外部依存ゼロ。
- `api/` — FastAPI（アプリケーション層 + インフラ層）
- `web/` — React + Vite（レビューUI）

## ビルドコマンド

- `make build` — 全パッケージビルド
- `make test` — 全テスト実行
- `make lint` — 全パッケージ lint
- `make format` — コードフォーマット
- `make typecheck` — 型チェック（mypy）
- `lint-imports` — 依存方向違反の検出

## CI チェック項目

コミット前に以下のチェックをすべて通すこと。

### Python（domain / api）

```bash
ruff check domain/ api/          # lint（未使用変数、import順序等）
ruff format --check domain/ api/ # フォーマット整合性
mypy domain/src api/src          # 型チェック
pytest domain/ api/ -v           # テスト
```

### TypeScript（web）

```bash
cd web
npm run build                    # tsc -b && vite build（型チェック含む）
npx vitest run                   # テスト
npx biome check                  # フォーマット + lint（Biome）
```

### よくあるエラーと対処

| エラー | 原因 | 対処 |
|--------|------|------|
| `F841 Local variable assigned but never used` | 未使用変数 | 変数を削除 |
| `TS2741 Property 'X' is missing in type` | TS型に必須プロパティ追加後、テストのリテラルが未更新 | テストファイルのオブジェクトリテラルにプロパティを追加 |
| `mypy arg-type: Argument has incompatible type` | `Tag.get()` の戻り値 `str \| list[str] \| None` を直接 `int()` 等に渡している | `str()` でラップ |
| `ruff format` で差分が出る | フォーマット未適用 | `ruff format domain/ api/` を実行 |
| 印刷で `window.print()` を使うとアプリUI全体が印刷される | `window.print()` はページ全体が対象 | `openPrintWindow` で空ウィンドウを開き `document.write` でHTMLを書き込んで印刷する。blob URL 方式は `load` イベントがナビゲーションで失われるため不可 |
| 変数入力で空欄フィールドがあると `{{variableName}}` が空になる | `bindToHtml` が空値を空文字に変換していた | 空値の場合は変数名をフォールバックとして差し込む（`useVariableBinding.ts` の `bindToHtml`）|

## 設計原則

### コード原則

1. 1ファイル1責務。500行超は分割必須。
2. ディレクトリ構造が設計を語る。
3. 型定義を信頼の源とする。
4. テストは対象ファイルの隣に配置（`_test.py` / `.test.ts`）。
5. ドメイン層は外部依存ゼロ。

### アーキテクチャ原則

| # | 原則 | 要点 |
|---|------|------|
| 1 | **マニフェストJSONが唯一の真実** | 座標・変数・型の情報源はマニフェストJSONただ1つ |
| 2 | **単位変換は境界で1回だけ** | mm→ピクセルは画像受取直後に1回。mm→CSSはHTML生成時に1回 |
| 3 | **エンジンの差し替えを前提にする** | OCRエンジンは`inputType`に応じて切替。インターフェースは統一 |
| 4 | **責務の分離** | 一つの知識を複数モジュールが重複して持たない |
| 5 | **段階導入と独立動作** | 各モジュールは他が未導入でも単独で動く |

詳細と違反例は `docs/design-principles.md` を参照。

## ファイル命名規約

- Python モジュール: snake_case（`manifest.py`, `tombo_detector.py`）
- Python クラス: PascalCase（`Manifest`, `TomboDetector`）
- TypeScript コンポーネント: PascalCase（`ReviewPage.tsx`）
- API エンドポイント: snake_case（`ocr_result.py`）

## コミットメッセージ規約

```
{type}({scope}): {summary}
```

- `type`: `feat` / `fix` / `docs` / `chore` / `refactor` / `test`
- `scope`: 影響するパッケージ名（`domain` / `api` / `web` / `root` 等）
- `summary`: 変更内容の要約

---

## ガードレール

品質を機械的に担保するための仕組み。AIへのコンテキスト提供と自動チェックの両方で機能する。

### ガードレール①: slash command によるコンテキスト構造化

`.claude/commands/` にレイヤー × 機能単位の slash command を用意。
Claude に作業させる際は必ず対応する `/command` を起点にすること。

| コマンド | 用途 |
| --- | --- |
| `/project:add-domain-entity` | ドメイン層へのエンティティ追加 |
| `/project:add-usecase` | アプリケーション層へのユースケース追加 |
| `/project:add-api-endpoint` | API エンドポイント追加 |
| `/project:add-web-feature` | Web UI へのフィーチャー追加 |
| `/project:review` | 設計レビュー（ガイドライン違反チェック） |

### ガードレール②: 依存方向の制御

**許可される依存方向:**

- `web` → `domain`（型のみ）
- `api` → `domain`

**禁止される依存:**

- `domain` → 他の全レイヤー（外部依存ゼロ）
- `api` → UI 層（web）
- `web` → `api`（HTTP 経由でのみ通信）
- 循環依存: 禁止

確認コマンド: `lint-imports`

**データ境界:**

- 各ドメイン（境界づけられたコンテキスト）のデータは専用ストレージに格納する
- 他ドメインのストレージに直接書き込まない
- ドメイン横断のデータ取得はアプリケーション層で並列クエリして統合する

**モジュール間連携の手段（結合度順）:**

1. **ディープリンク**（低結合）— URL パターンによる画面遷移
2. **REST API**（中結合）— データ参照
3. **ドメインイベント**（低結合・非同期）— 結果整合性が許容される場合

### ガードレール③: レイヤーごとのテスト原則

**Domain 層 (`domain/`)**

- 原則: **全ロジックにユニットテストを書く**
- カバレッジ目標: 90% 以上
- テスト対象: エンティティのメソッド、ドメインルール（Policy）、バリデーション
- モック: 原則不要（外部依存ゼロのため）

**Application 層（ユースケース）**

- 原則: **全ユースケースにユニットテストを書く**
- インフラ層（Repository・外部サービス）はモック化
- テスト対象: ユースケースの処理フロー、エラーハンドリング

**Infrastructure 層**

- 原則: 統合テストで実際の接続先を検証
- ローカル開発ではエミュレーター使用を推奨

**Web UI 層 (`web/`)**

- 原則: コンポーネント単体テスト
- ビジネスロジックは Domain / Application 層に置き、UI テストを軽量に保つ

### ガードレール④: Git フックによる品質チェック

```
git commit → pre-commit: 変更ファイルのみ lint + format
git push   → pre-push:   全体 lint + 型チェック
CI         → 全チェック（lint / type-check / test / dep-check）
```

### ガードレール⑤: `/project:review` コマンドによるレビュー

コミット前に `/project:review` を実行し、設計ガイドライン違反がないか確認する。

**レビューの8次元:**

1. **アーキテクチャ/依存方向** — 禁止方向の import がないか
2. **レイヤー責務** — 正しいレイヤーに配置されているか
3. **知識の分離** — 責務境界を越えてデータを重複保持していないか
4. **テスト** — Domain 90%+、Application 全フロー、UI 軽量
5. **型定義** — domain パッケージの型が適切か
6. **命名規則** — プロジェクトの命名パターンに準拠しているか
7. **ファイルサイズ** — 500行以下
8. **制約ドキュメント** — 共通パッケージ変更時に記録したか

### ガードレール⑥: 制約条件の記録（`docs/constraints/`）

実装過程で発見・決定された制約条件は `docs/constraints/` に記録する。

**ルール:**

1. 新しい制約が生じたら `docs/constraints/{連番3桁}-{kebab-case}.md` を作成
2. テンプレート（`docs/constraints/README.md` 参照）に従い、背景・詳細・影響範囲・今後の対応を記述
3. `docs/constraints/README.md` の一覧テーブルにも追記
4. 制約が解消された場合は、ドキュメント内に「解消日」と「解消方法」を追記

### ガードレール⑦: 事象管理（`docs/issues/`）

実装中に発生したブロッカーや課題を `docs/issues/` に記録する。

**ルール:**

1. 新しい事象が発生したら `docs/issues/reports/{連番3桁}-{kebab-case}.md` を作成
2. テンプレート（`docs/issues/README.md` 参照）に従い、発生状況・調査経緯を記述
3. 事象が解決したかどうかはユーザーが判定する

### ガードレール⑧: クロスプラットフォーム開発環境の保護

**ルール:**

1. lockfile（poetry.lock / package-lock.json 等）を不必要に変更しない
2. パッケージの追加・削除時のみ lockfile を更新する
3. やむを得ず変更した場合は `git checkout -- <lockfile>` で復元する

### ガードレール⑨: 進捗管理（`PROGRESS.md`）

プロジェクトルートの `PROGRESS.md` がこのプロジェクトの進捗の正本である。

#### 読み出しルール

- プロジェクト進捗を聞かれたら、最初に `PROGRESS.md` を読む
- 「前回からの差分」を聞かれたら `## diff` セクションを提示する
- 詳細が必要なら `docs/milestones.md`、`docs/constraints/`、`docs/issues/`、`docs/adr/` を参照する

#### 書き込みルール

フェーズの状態・進捗が変わったら `PROGRESS.md` を更新する。

#### 迷走検知

| パターン | 条件 | アクション |
|---------|------|-----------|
| 停滞 | `active` で最終変動が 14日以上前 | スコープ縮小 or ブロッカー昇格を提案 |
| 長期ブロック | `blocked` で最終変動が 21日以上前 | 解消見込みの確認 or 迂回策を提案 |
| ブロッカー純増 | diff でブロッカーの追加 > 削除 | 純増している旨を報告 |
| 後退 | 進捗が前回より下がった | 手戻り原因の確認を促す |

### ガードレール⑩: 設計原則とエスカレーション（`docs/design-principles.md`）

プロジェクトのビジョン・判断基準・設計原則・並行開発ルール・コミット規約・エスカレーション基準を `docs/design-principles.md` に定義する。

### ガードレール⑪: 未実装項目管理（`docs/backlog/`）

実装予定だが未着手の項目を `docs/backlog/` で管理する。4状態（未着手→着手可能→進行中→完了）で追跡。

### ガードレール⑫: 環境固有の留意事項（`docs/environment-notes.md`）

OS・CI 環境・クラウドサービスに起因する問題と対策を `docs/environment-notes.md` に蓄積する。

### ガードレール⑬: ビジョン検証ゲート（`docs/vision-gates/`）

技術的な完了とは別に、ビジョンの具体化に寄与しているかを人間が検証する仕組み。

**3つの仮説と検証ゲート:**

| ゲート | 仮説 | 前提マイルストーン |
|--------|------|-------------------|
| VG-1 | 座標の往復一貫性で OCR 精度が出る | M3b + M4a |
| VG-2 | 撮影＋レビューで手入力より速い | M4b |
| VG-3 | 現場担当者が迷わず操作できる | M5 |

**ルール:**

1. ゲートの前提マイルストーン完了時に、ユーザーに検証実施を促す
2. ユーザーが「合格」「条件付合格」「不合格」を明示するまで、次フェーズに進まない
3. AI は検証結果の記録（事実の転記）を行えるが、合否判定は行えない
4. 不合格の場合は `docs/issues/reports/` に事象を起票し、対応方針をユーザーと協議する
5. 検証プロトコルの詳細は `docs/vision-gates/` の各ゲートドキュメントを参照
