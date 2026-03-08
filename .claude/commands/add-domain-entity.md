---
description: ドメイン層に新しいエンティティ（集約）を追加する (project)
---

## ガイドライン参照

作業前に必ず以下を読み込む:

- [CLAUDE.md](../../CLAUDE.md) — 設計原則・命名規約・ガードレール
- [domain/CLAUDE.md](../../domain/CLAUDE.md) — ドメイン層固有のルール
- 既存の集約（例: `domain/src/` 配下）を参考に構造を把握する

## 現在のドメイン構成

- 既存集約: !`ls domain/src/`

## タスク

`$ARGUMENTS` を `domain/src/` に新しい集約として追加してください。

### 作成するファイル構成

```
domain/src/{aggregate_name}/
├── __init__.py                    # 公開 API のエクスポート
├── {aggregate_name}.py            # エンティティ本体
├── {aggregate_name}_test.py       # ユニットテスト
├── {aggregate_name}_types.py      # 型定義・Value Object
├── {aggregate_name}_policy.py     # ドメインルール ※必要な場合
└── {aggregate_name}_repository.py # Repositoryインターフェース（ABC）
```

### 実装ルール（ガードレール遵守）

1. **外部依存ゼロ**: `domain/` 外のパッケージを import してはいけない
2. **基底型を継承/利用**: `shared/entity_base` を基底としてエンティティを定義する
3. **イミュータブル設計**: 状態変更はメソッドで新インスタンスを返す
4. **テスト必須**: 全ての public メソッドに対してテストを書く（ガードレール③）
5. **型安全**: `Any` は使用禁止。Value Object は専用の型定義ファイルに定義する

### exports の更新

`domain/src/__init__.py` に新しい集約のエクスポートを追加すること。

### 完了確認

```bash
make typecheck
make test
lint-imports
```
