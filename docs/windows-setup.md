# Windows 開発環境セットアップガイド

KamiBack を Windows 上で開発するための手順。

## 前提条件

| ツール | バージョン | 入手先 |
|--------|-----------|--------|
| Python | 3.11 以上 | https://www.python.org/downloads/ |
| Node.js | 20 LTS 以上 | https://nodejs.org/ |
| Git | 最新 | https://git-scm.com/download/win |

> Python インストール時に **「Add Python to PATH」にチェック** を入れること。

## 1. リポジトリのクローン

```powershell
git clone https://github.com/<org>/KamiBack.git
cd KamiBack
```

## 2. Python 環境（Domain + API）

```powershell
# 仮想環境の作成
python -m venv .venv

# 仮想環境の有効化（PowerShell）
.venv\Scripts\Activate.ps1

# 仮想環境の有効化（コマンドプロンプト）
# .venv\Scripts\activate.bat

# 依存パッケージのインストール（開発用含む）
pip install -e ".[dev]"
```

### PowerShell の実行ポリシーエラーが出る場合

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

を実行してから再度 `Activate.ps1` を試す。

## 3. Web 環境（React + Vite）

```powershell
cd web
npm install
cd ..
```

## 4. Git フックの設定

```powershell
git config core.hooksPath .githooks
```

## 5. 開発コマンド

このプロジェクトの Makefile は Unix シェル構文を使っている。Windows では以下のように個別コマンドを実行する。

### テスト

```powershell
# Python テスト（Domain + API）
pytest domain/ api/ -v --import-mode=importlib

# Web テスト
cd web
npx vitest run
cd ..
```

### Lint

```powershell
# Python lint
ruff check domain/ api/
ruff format --check domain/ api/

# Web lint
cd web
npx biome check ./src
cd ..
```

### 型チェック

```powershell
# Python 型チェック
mypy domain/src api/src

# Web 型チェック
cd web
npx tsc --noEmit
cd ..
```

### フォーマット

```powershell
# Python フォーマット
ruff format domain/ api/

# Web フォーマット
cd web
npx biome format --write ./src
cd ..
```

### 依存方向チェック

```powershell
lint-imports
```

### ビルド

```powershell
# Web ビルド
cd web
npm run build
cd ..
```

### 開発サーバー

```powershell
# API サーバー（ターミナル1）
uvicorn api.src.main:app --reload --port 8000

# Web 開発サーバー（ターミナル2）
cd web
npm run dev
```

Web 開発サーバーは `/api` へのリクエストを `http://localhost:8000` にプロキシする。

## 6. Make を使いたい場合（任意）

Windows で `make` コマンドを使いたい場合は以下のいずれかを導入する。

### 方法 A: WSL（推奨）

WSL 2 + Ubuntu をインストールし、Linux と同じ手順でセットアップする。最も互換性が高い。

```powershell
# WSL インストール（管理者権限の PowerShell）
wsl --install
```

WSL 内では README.md の手順がそのまま使える。

### 方法 B: GNU Make for Windows

[GnuWin32](https://gnuwin32.sourceforge.net/packages/make.htm) または [chocolatey](https://chocolatey.org/) 経由でインストール。

```powershell
# chocolatey を使う場合
choco install make
```

ただし Makefile 内のシェル構文（`[ -f ... ]`, `find`, `grep` 等）が動かない場合がある。

### 方法 C: Git Bash

Git for Windows に付属する Git Bash を使えば、Unix コマンドが利用でき `make` も追加インストール可能。

## トラブルシューティング

| 問題 | 原因 | 対策 |
|------|------|------|
| `Activate.ps1` が実行できない | PowerShell 実行ポリシー制限 | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `python` が見つからない | PATH 未設定 | Python を再インストールし「Add to PATH」にチェック。または `py` コマンドを使う |
| `pip install` で C 拡張のビルドエラー | Visual C++ Build Tools 未インストール | [Build Tools for Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/) をインストール |
| `make` が動かない | Windows 標準には make がない | 上記「Make を使いたい場合」を参照 |
| パスの `\` と `/` の混在エラー | Windows パス区切り文字 | PowerShell では `/` も使える。Git Bash の利用も検討 |
| テストでファイルパスが不一致 | OS 間のパス区切り差異 | `pathlib.Path` を使っていれば問題ない。ハードコードされた `/` パスがあれば報告 |
