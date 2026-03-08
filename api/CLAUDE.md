# api/

## このパッケージの役割

KamiBack のバックエンド API。FastAPI で構築。アプリケーション層（ユースケース）とインフラ層（リポジトリ実装、外部連携）を含む。

## ディレクトリ構成

- `src/api/routes/` — API エントリポイント（snake_case）
- `src/use_cases/` — アプリケーションサービス（ユースケース）
- `src/infrastructure/` — インフラ層（DB, Auth, External Services）

## 新しいエンドポイントを追加する手順

1. `src/api/routes/{feature}/{endpoint}.py` を作成
2. `src/use_cases/{集約名}/{動詞}_{名詞}_use_case.py` を作成
3. 必要に応じて `src/infrastructure/` にリポジトリ実装を追加

## ローカル実行

```bash
uvicorn src.main:app --reload
```
