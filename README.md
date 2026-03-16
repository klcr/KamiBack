# KamiBack — 帳票OCRマッピングシステム

紙の帳票を「構造化データの一時的な入れ物」にするシステム。帳票HTMLに定義されたmm座標を使って値を紙の上に配置し（往路）、同じmm座標を使って紙の上から値を読み取る（復路）。

## アーキテクチャ

DDD（ドメイン駆動設計）+ レイヤードアーキテクチャで構築。

| レイヤー | ディレクトリ | 役割 |
|---------|------------|------|
| Domain | `domain/` | 型定義・エンティティ・ビジネスルール（外部依存ゼロ） |
| API | `api/` | FastAPI バックエンド API |
| Web | `web/` | React + Vite レビュー UI |

## セットアップ

### Python（Domain + API）

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### TypeScript（Web）

```bash
cd web
npm install
```

## 外部ツールのセットアップ

| ツール | 用途 | ガイド |
|--------|------|--------|
| NDLOCR-Lite | Module B の OCR エンジン | [docs/setup/ndlocr-lite.md](docs/setup/ndlocr-lite.md) |

## 開発コマンド

| コマンド | 説明 |
|---------|------|
| `make build` | ビルド |
| `make test` | テスト実行 |
| `make lint` | Lint |
| `make typecheck` | 型チェック |
| `make format` | フォーマット |
| `lint-imports` | 依存方向チェック |

## Claude Code との協業

このプロジェクトは Claude Code との協業を前提に設計されています。

- `CLAUDE.md` — プロジェクト全体のガイドライン
- `.claude/commands/` — 定型操作の slash command
- `docs/design-principles.md` — ビジョン・判断基準・設計原則
- `docs/constraints/` — 制約条件の記録
- `docs/issues/` — 事象管理

主な slash command:

| コマンド | 用途 |
|---------|------|
| `/project:add-domain-entity <名前>` | ドメインエンティティを追加 |
| `/project:add-usecase <名前>` | ユースケースを追加 |
| `/project:add-api-endpoint <名前>` | API エンドポイントを追加 |
| `/project:add-web-feature <名前>` | Web フィーチャーを追加 |
| `/project:review` | 設計レビューを実行 |
