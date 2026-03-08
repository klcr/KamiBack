---
description: API に新しいエンドポイントを追加する (project)
---

## ガイドライン参照

作業前に必ず以下を読み込む:

- [CLAUDE.md](../../CLAUDE.md) — 設計原則・命名規約・ガードレール
- [api/CLAUDE.md](../../api/CLAUDE.md) — API 層固有のルール
- 既存のエンドポイント（`api/src/api/routes/`）を参考に構造を把握する

## 現在のエンドポイント構成

- 既存エンドポイント: !`ls api/src/api/routes/`

## タスク

`$ARGUMENTS` を `api/src/api/routes/` に新しいエンドポイントとして追加してください。

### 作成するファイル

```
api/src/api/routes/{feature}/
└── {endpoint}.py   # snake_case
```

### 実装ルール（ガードレール遵守）

**ファイル命名（CLAUDE.md 規約）:**

- エンドポイントファイルは snake_case で命名

**依存方向（ガードレール②）:**

- ユースケース層（`../use_cases/`）への依存: OK（ユースケース経由でドメインロジックを呼ぶ）
- ドメイン層への直接依存: 最小限に（型のみ使用可）
- UI 層（web）への依存: 禁止

**実装方針:**

1. リクエストのバリデーションを行う（Pydantic モデル）
2. ビジネスロジックはユースケース層に委譲する（エンドポイントは薄く保つ）
3. レスポンスは統一フォーマットにする
4. エラーは統一的に処理する

### 完了確認

```bash
make typecheck
make test
make lint
ruff format --check domain/ api/
lint-imports
```
