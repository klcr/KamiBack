# domain/

## このパッケージの役割

KamiBack のドメイン層。型定義、エンティティ、ビジネスルール、リポジトリインターフェース。

## 外部依存は禁止

このパッケージは外部ライブラリへの runtime dependency を持ってはならない。

## ディレクトリ構成

```
src/
├── {aggregate_name}/              # 集約単位のサブディレクトリ
│   ├── {aggregate_name}.py        # エンティティ本体
│   ├── {aggregate_name}_test.py   # ユニットテスト
│   ├── {aggregate_name}_types.py  # 型定義・Value Object
│   ├── {aggregate_name}_policy.py # ドメインルール（必要な場合）
│   └── {aggregate_name}_repository.py # Repositoryインターフェース（ABC）
└── shared/                        # 集約横断の共通要素
    ├── entity_base.py             # エンティティ基底型
    ├── domain_event.py            # ドメインイベント基底型
    └── errors.py                  # ドメイン固有エラー型
```

## ファイル配置ルール

- 新しい集約: `src/{集約名}/` ディレクトリを作成
- 型定義: `{集約名}_types.py`
- ビジネスルール: `{集約名}_policy.py`
- リポジトリIF: `{集約名}_repository.py`（ABC で定義）
- テスト: 対象ファイルの隣に `_test.py`

## 命名規約

- ファイル名: snake_case（`manifest.py`）
- クラス名: PascalCase（`Manifest`）

## 既存の集約

（プロジェクト初期化時は空）
