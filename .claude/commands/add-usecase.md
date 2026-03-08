---
description: アプリケーション層に新しいユースケースを追加する (project)
---

## ガイドライン参照

作業前に必ず以下を読み込む:

- [CLAUDE.md](../../CLAUDE.md) — 設計原則・命名規約・ガードレール
- [api/CLAUDE.md](../../api/CLAUDE.md) — API 層固有のルール
- 既存のユースケース（`api/src/use_cases/`）を参考に構造を把握する

## 現在のユースケース構成

- 既存ユースケース: !`find api/src/use_cases -name "*.py" ! -name "*.test.*" ! -name "__*" 2>/dev/null | head -20`

## タスク

`$ARGUMENTS` を `api/src/use_cases/` に新しいユースケースとして追加してください。

### 作成するファイル構成

```
api/src/use_cases/{feature}/
├── {use_case_name}_use_case.py      # ユースケースクラス/関数
└── {use_case_name}_use_case_test.py # ユニットテスト（ガードレール③: 全フローをテスト）
```

### 実装ルール（ガードレール遵守）

**依存方向（ガードレール②）:**

- ドメイン層（`domain`）への依存: OK
- インフラ層のインターフェース（Repository ABC）への依存: OK
- UI 層（web）への依存: 禁止
- インフラ実装（DB 等）の直接 import: 禁止（インターフェース経由で）

**テスト原則（ガードレール③）:**

- Repository などのインフラ依存はモックに置き換える
- 正常系・異常系・境界値をテストする
- テストはユースケースファイルの隣に `_test.py` で配置する

**実装方針:**

1. コンストラクタインジェクション（または関数引数）で Repository インターフェースを受け取る
2. ドメインロジックはドメイン層に委譲する
3. ユースケース自体は「何をするか」のオーケストレーションのみ担う

### 完了確認

```bash
make typecheck
make test
make lint
ruff format --check domain/ api/
lint-imports
```
