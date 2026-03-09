---
description: PR を作成し、CI 結果を監視して失敗時は自律的に修正ループを回す
---

## 現在の状況

- 現在のブランチ: !`git branch --show-current`
- origin/main との差分: !`git log origin/main..HEAD --oneline 2>/dev/null || echo "差分なし"`
- ワーキングツリー: !`git status --short`

## タスク

コードが検証待ち状態に達した際に、以下の手順で PR を作成し、GitHub Actions の CI 結果を自律的にフィードバックする。PRクローズは人間が行う。

### Step 1: ローカル事前検証（イテレーション消費なし）

PR 作成前に CI と同じチェックをローカルで実行する。失敗したら修正してから先に進む。

```bash
make lint && make typecheck && make test
```

この段階での失敗は3回制限にカウントしない。

### Step 2: PR 作成

1. ブランチをプッシュする
2. `gh pr create` で PR を作成する（ベースブランチは `main`）
3. PR の URL をユーザーに報告する

### Step 3: CI フィードバックループ（最大3イテレーション）

以下を最大3回繰り返す:

#### 3a. CI 完了を待機

```bash
timeout 600 gh pr checks --watch --interval 10 || true
```

#### 3b. 結果を確認

```bash
gh pr checks
```

全チェックが green なら成功を報告して終了。

#### 3c. 失敗時の診断

失敗したジョブのログを取得して原因を特定する:

```bash
# run ID を取得
RUN_ID=$(gh run list --branch "$(git branch --show-current)" --limit 1 --json databaseId --jq '.[0].databaseId')

# 失敗ジョブの ID を取得
gh run view $RUN_ID --json jobs --jq '.jobs[] | select(.conclusion == "failure") | {name, databaseId}'

# 失敗ジョブのログ末尾を取得（エラーは末尾に集約される）
gh run view --log --job <JOB_ID> 2>&1 | tail -80
```

#### 3d. ローカルで再現して修正

| CI ステップ | ローカル再現 | 自動修正 |
|---|---|---|
| ruff check | `ruff check domain/ api/` | `ruff check --fix domain/ api/` |
| ruff format | `ruff format --check domain/ api/` | `ruff format domain/ api/` |
| mypy | `mypy domain/src api/src` | 手動修正 |
| pytest | `pytest domain/ api/ -v` | 手動修正 |
| lint-imports | `lint-imports` | 手動修正 |
| biome check | `cd web && npx biome check ./src` | `cd web && npx biome check --apply ./src` |
| tsc | `cd web && npx tsc --noEmit` | 手動修正 |
| vitest | `cd web && npx vitest run` | 手動修正 |
| API smoke test | サーバー起動して curl | import/起動エラー修正 |

#### 3e. 修正をコミット・プッシュ

```bash
git add <対象ファイル>
git commit -m "fix(<scope>): <CI修正内容>"
git push
```

`concurrency: cancel-in-progress: true` により前回の run は自動キャンセルされる。

### Step 4: 最終報告

- **全 green**: 成功を報告。PR URL を提示し、人間にレビュー・マージ・クローズを委ねる。
- **3回失敗**: 「CI が3回失敗。手動対応が必要」と報告し、残っている失敗のログ抜粋を提示する。

## 注意事項

- `python-smoke` ジョブは `python` に依存（`needs: python`）。`python` が失敗すると skip される → upstream を先に修正すること
- pre-push フックが設定されている場合、push 自体がローカルで失敗する可能性あり（CI イテレーション消費なし）
- ログが大きい場合は `tail -80` で十分（エラーは末尾に集約される）
