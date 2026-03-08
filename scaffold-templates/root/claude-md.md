# ルート CLAUDE.md テンプレート

以下のテンプレートを `{{PROJECT_NAME}}/CLAUDE.md` として生成してください。
条件ブロック（`<!-- IF: ... -->`）はヒアリング結果に基づいて含める/除外してください。

---

```markdown
# {{PROJECT_NAME}}

## プロジェクト概要

{{PROJECT_DESCRIPTION}}

## アーキテクチャ

- DDD（ドメイン駆動設計）+ レイヤードアーキテクチャ
<!-- IF: HAS_MONOREPO -->
- モノレポ（{{MONOREPO_TOOL}}）
<!-- ENDIF -->

## パッケージ構成

- `{{DOMAIN_DIR}}/` — ドメイン層（型定義、エンティティ、ビジネスルール）。外部依存ゼロ。
<!-- IF: HAS_API_LAYER -->
- `{{API_DIR}}/` — {{API_FRAMEWORK}}（アプリケーション層 + インフラ層）
<!-- ENDIF -->
<!-- IF: HAS_WEB_LAYER -->
- `{{WEB_DIR}}/` — {{WEB_FRAMEWORK}}（デスクトップ UI）
<!-- ENDIF -->
<!-- IF: HAS_MOBILE_LAYER -->
- `{{MOBILE_DIR}}/` — {{MOBILE_FRAMEWORK}}（モバイル UI）
<!-- ENDIF -->

## ビルドコマンド

- `{{BUILD_CMD}}` — 全パッケージビルド
- `{{TEST_CMD}}` — 全テスト実行
- `{{LINT_CMD}}` — 全パッケージ lint
<!-- IF: IS_TYPESCRIPT -->
- `{{TYPE_CHECK_CMD}}` — 型チェック
<!-- ENDIF -->
<!-- IF: HAS_FORMATTER -->
- `{{FORMAT_CMD}}` — コードフォーマット
<!-- ENDIF -->
<!-- IF: HAS_DEP_CHECK -->
- `{{DEP_CHECK_CMD}}` — 依存方向違反の検出
<!-- ENDIF -->
<!-- IF: HAS_DEAD_CODE_CHECK -->
- `{{DEAD_CODE_CMD}}` — 未使用コードの検出
<!-- ENDIF -->

## 設計原則

### コード原則

1. 1ファイル1責務。500行超は分割必須。
2. ディレクトリ構造が設計を語る。
3. 型定義を信頼の源とする。
4. テストは対象ファイルの隣に配置（`.test.{{FILE_EXT}}`）。
5. ドメイン層は外部依存ゼロ。

### アーキテクチャ原則

| # | 原則 | 要点 |
|---|------|------|
| 1 | **責務の分離** | 一つの知識を複数モジュールが重複して持たない |
| 2 | **参照はするが書き戻さない** | 他コンテキストのデータはスナップショット取得のみ |
| 3 | **段階導入と独立動作** | 各モジュールは他が未導入でも単独で動く |
| 4 | **ワンファクト・マルチビュー** | データは発生元で1度だけ記録。各モジュールは異なる視座で表示 |
| 5 | **共通識別子による横断** | 全モジュール共通の識別子で横断参照の基盤を作る |

詳細と違反例は `docs/design-principles.md` を参照。

## ファイル命名規約

<!-- IF: IS_TYPESCRIPT -->
- ドメイン層: PascalCase（`Case.ts`, `Event.ts`）
- API エンドポイント: kebab-case（`post-resource-create.ts`）
- React コンポーネント: PascalCase（`DetailView.tsx`）
<!-- ENDIF -->
<!-- IF: IS_PYTHON -->
- モジュール: snake_case（`case.py`, `event.py`）
- クラス: PascalCase（`Case`, `Event`）
<!-- ENDIF -->
<!-- IF: IS_GO -->
- パッケージ: lowercase（`case/`, `event/`）
- ファイル: snake_case（`case.go`, `event_test.go`）
<!-- ENDIF -->

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
<!-- IF: HAS_API_LAYER -->
| `/project:add-usecase` | アプリケーション層へのユースケース追加 |
| `/project:add-api-endpoint` | API エンドポイント追加 |
<!-- ENDIF -->
<!-- IF: HAS_WEB_LAYER -->
| `/project:add-web-feature` | Web UI へのフィーチャー追加 |
<!-- ENDIF -->
<!-- IF: HAS_MOBILE_LAYER -->
| `/project:add-mobile-feature` | Mobile UI へのフィーチャー追加 |
<!-- ENDIF -->
| `/project:review` | 設計レビュー（ガイドライン違反チェック） |

### ガードレール②: 依存方向の制御

**許可される依存方向:**

<!-- IF: HAS_WEB_LAYER -->
- `{{WEB_DIR}}` → `{{DOMAIN_DIR}}`（型のみ）
<!-- ENDIF -->
<!-- IF: HAS_MOBILE_LAYER -->
- `{{MOBILE_DIR}}` → `{{DOMAIN_DIR}}`
<!-- ENDIF -->
<!-- IF: HAS_API_LAYER -->
- `{{API_DIR}}` → `{{DOMAIN_DIR}}`
<!-- ENDIF -->

**禁止される依存:**

- `{{DOMAIN_DIR}}` → 他の全レイヤー（外部依存ゼロ）
<!-- IF: HAS_API_LAYER -->
- `{{API_DIR}}` → UI 層（web / mobile）
<!-- ENDIF -->
<!-- IF: HAS_WEB_LAYER -->
- `{{WEB_DIR}}` → `{{API_DIR}}`（HTTP 経由でのみ通信）
<!-- ENDIF -->
<!-- IF: HAS_MOBILE_LAYER -->
- `{{MOBILE_DIR}}` → `{{API_DIR}}`（HTTP 経由でのみ通信）
<!-- ENDIF -->
- 循環依存: 禁止

<!-- IF: HAS_DEP_CHECK -->
確認コマンド: `{{DEP_CHECK_CMD}}`
<!-- ENDIF -->

**データ境界:**

- 各ドメイン（境界づけられたコンテキスト）のデータは専用ストレージに格納する
- 他ドメインのストレージに直接書き込まない
- ドメイン横断のデータ取得はアプリケーション層で並列クエリして統合する

**モジュール間連携の手段（結合度順）:**

1. **ディープリンク**（低結合）— URL パターンによる画面遷移
2. **REST API**（中結合）— データ参照
3. **ドメインイベント**（低結合・非同期）— 結果整合性が許容される場合

### ガードレール③: レイヤーごとのテスト原則

**Domain 層 (`{{DOMAIN_DIR}}/`)**

- 原則: **全ロジックにユニットテストを書く**
- カバレッジ目標: 90% 以上
- テスト対象: エンティティのメソッド、ドメインルール（Policy）、バリデーション
- モック: 原則不要（外部依存ゼロのため）

<!-- IF: HAS_API_LAYER -->
**Application 層（ユースケース）**

- 原則: **全ユースケースにユニットテストを書く**
- インフラ層（Repository・外部サービス）はモック化
- テスト対象: ユースケースの処理フロー、エラーハンドリング

**Infrastructure 層**

- 原則: 統合テストで実際の接続先を検証
- ローカル開発ではエミュレーター使用を推奨
<!-- ENDIF -->

<!-- IF: HAS_WEB_LAYER -->
**Web UI 層 (`{{WEB_DIR}}/`)**

- 原則: コンポーネント単体テスト
- ビジネスロジックは Domain / Application 層に置き、UI テストを軽量に保つ
<!-- ENDIF -->

<!-- IF: HAS_MOBILE_LAYER -->
**Mobile UI 層 (`{{MOBILE_DIR}}/`)**

- 原則: コンポーネント単体テスト
- ビジネスロジックは Domain / Application 層に置き、UI テストを軽量に保つ
<!-- ENDIF -->

### ガードレール④: Git フックによる品質チェック

```
git commit → pre-commit: 変更ファイルのみ lint + format
git push   → pre-push:   全体 lint + 型チェック
CI         → 全チェック（lint / type-check / test / dep-check / dead-code）
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

**対象:**

- 暫定措置（後で解消が必要な技術的制約）
- 設計判断により生じた制約（トレードオフの選択）
- レイヤー間の結合に関する取り決め
- 外部依存・インフラに起因する制限

**ルール:**

1. 新しい制約が生じたら `docs/constraints/{連番3桁}-{kebab-case}.md` を作成
2. テンプレート（`docs/constraints/README.md` 参照）に従い、背景・詳細・影響範囲・今後の対応を記述
3. `docs/constraints/README.md` の一覧テーブルにも追記
4. 制約が解消された場合は、ドキュメント内に「解消日」と「解消方法」を追記し、一覧テーブルの状態を「解消」に変更

### ガードレール⑦: 事象管理（`docs/issues/`）

実装中に発生したブロッカーや課題を `docs/issues/` に記録する。

**対象:**

- 実装の詰まり（技術的なブロッカー）
- 原因調査中の不具合
- 外部要因による作業停滞

**ルール:**

1. 新しい事象が発生したら `docs/issues/reports/{連番3桁}-{kebab-case}.md` を作成
2. テンプレート（`docs/issues/README.md` 参照）に従い、発生状況・調査経緯を記述
3. `docs/issues/README.md` の一覧テーブルにも追記
4. 事象が解決したかどうかはユーザーが判定する。解決確認後、レポートに「解決日」と「解決方法」を追記し、一覧テーブルの状態を「解決済」に変更

### ガードレール⑧: クロスプラットフォーム開発環境の保護

Claude Code は Linux 上で動作する。ユーザーの開発環境（Windows/macOS）との差異により問題が発生しうる。

**ルール:**

1. lockfile（package-lock.json / poetry.lock / go.sum 等）を不必要に変更しない
2. パッケージの追加・削除時のみ lockfile を更新する
3. やむを得ず変更した場合は `git checkout -- <lockfile>` で復元する
4. lockfile の変更は原則コミットしない（例外: ユーザーが明示的にパッケージ操作を指示した場合のみ）

### ガードレール⑨: 進捗管理（`PROGRESS.md`）

プロジェクトルートの `PROGRESS.md` がこのプロジェクトの進捗の正本である。

#### 読み出しルール

- プロジェクト進捗を聞かれたら、最初に `PROGRESS.md` を読む
- 「前回からの差分」を聞かれたら `## diff` セクションを提示する
- ダッシュボード生成時はサマリーとフェーズテーブルをデータソースとする
- 詳細が必要なら `docs/milestones.md`、`docs/constraints/`、`docs/issues/`、`docs/adr/` を参照する

#### 書き込みルール

フェーズの状態・進捗が変わったら `PROGRESS.md` を更新する。手順:

1. 現在の diff を `<details>` に退避（前の `<details>` は上書き）
2. スナップショット部を書き換える（サマリー再計算、フェーズ行更新、最終変動日更新、ブロッカー・次のアクション見直し）
3. 書き換え前後から新しい diff ブロックを作成する（unified diff 記法、変更行のみ）
4. ヘッダーの日付を更新する

#### 更新するタイミング

以下のいずれかが発生したとき:

- フェーズの状態が変わった
- フェーズの進捗が 10% 以上変動した
- ブロッカーが増減した
- 新しいフェーズが追加された

#### 迷走検知

PROGRESS.md を読んだ際、以下に該当するフェーズがあれば進捗報告の冒頭で警告する。

| パターン | 条件 | アクション |
|---------|------|-----------|
| 停滞 | `active` で最終変動が 14日以上前 | スコープ縮小 or ブロッカー昇格を提案 |
| 長期ブロック | `blocked` で最終変動が 21日以上前 | 解消見込みの確認 or 迂回策を提案 |
| ブロッカー純増 | diff でブロッカーの追加 > 削除 | 純増している旨を報告 |
| 後退 | 進捗が前回より下がった | 手戻り原因の確認を促す |

#### 既存ドキュメントとの関係

```
PROGRESS.md          ← 全体の状態と差分（これだけで概況がわかる）
  ↓ 詳しく知りたいとき
docs/milestones.md   ← マイルストーン定義と完了条件
docs/constraints/    ← 設計判断の記録
docs/issues/         ← ブロッカー・課題の詳細
docs/adr/            ← アーキテクチャ決定記録
```

### ガードレール⑩: 設計原則とエスカレーション（`docs/design-principles.md`）

プロジェクトの設計原則・並行開発ルール・コミット規約・エスカレーション基準を `docs/design-principles.md` に定義する。

Issue/PR の起票時に「この変更はどの原則に基づくか」を明示させる。

### ガードレール⑪: 未実装項目管理（`docs/backlog/`）

実装予定だが未着手の項目を `docs/backlog/` で管理する。4状態（未着手→着手可能→進行中→完了）で追跡し、前提条件の充足状況と担当を明記する。

### ガードレール⑫: 環境固有の留意事項（`docs/environment-notes.md`）

OS・CI 環境・クラウドサービスに起因する問題と対策を `docs/environment-notes.md` に蓄積する。
```
