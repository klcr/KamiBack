---
description: Web UI に新しいフィーチャーを追加する (project)
---

## ガイドライン参照

作業前に必ず以下を読み込む:

- [CLAUDE.md](../../CLAUDE.md) — 設計原則・命名規約・ガードレール
- [web/CLAUDE.md](../../web/CLAUDE.md) — Web 層固有のルール
- 既存のフィーチャー（`web/src/features/`）を参考に構造を把握する

## 現在のフィーチャー構成

- 既存フィーチャー: !`ls web/src/features/`

## タスク

`$ARGUMENTS` を `web/src/features/` に新しいフィーチャーとして追加してください。

### 作成するファイル構成

```
web/src/features/{feature-name}/
├── {FeatureName}Page.tsx           # ページコンポーネント（ルートから参照）
├── {FeatureName}Page.test.tsx      # コンポーネントテスト（ガードレール③）
├── components/                      # フィーチャー専用コンポーネント
│   └── {ComponentName}.tsx
└── hooks/                           # フィーチャー専用カスタムフック ※必要な場合
    └── use{FeatureName}.ts
```

### 実装ルール（ガードレール遵守）

**依存方向（ガードレール②）:**

- 共通コンポーネント（`../../components/`）の使用: OK
- API 呼び出しは `../../lib/apiClient` 経由: OK
- API 層のソースコードへの直接 import: 禁止（HTTP 経由で呼ぶ）

**テスト原則（ガードレール③）:**

- ビジネスロジックは Domain / Application 層に置き、UI テストは表示・インタラクションに集中
- API 呼び出しはモック化する

**実装方針:**

1. ビジネスロジックを UI に書かない
2. データフェッチは `../../lib/apiClient` 経由
3. グローバルに使える UI は `../../components/common/` へ切り出す

### 完了確認

```bash
cd web && npx tsc --noEmit
cd web && npx vitest run
```
