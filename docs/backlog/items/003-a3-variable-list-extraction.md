# Backlog 003: A-3: 変数一覧の抽出

## 状態
未着手

## 担当
—

## 対象パッケージ
domain/

## 概要
マニフェストの`pages[].fields[]`を走査し、全ページの変数名・型・配置先ボックスIDの一覧を返す。TypeScript型定義（`interface`フィールド）もそのまま取得可能とする。

## 未実装の理由
前提マイルストーンが未完了

## 前提条件
- [ ] M2（マニフェスト型定義）完了

## 実装チェックリスト
- [ ] Manifest集約にメソッド追加
- [ ] テスト

## 着手時の注意事項
Manifest集約のメソッドとして実装すること。マイルストーン: M2/M3a。

## 関連ドキュメント
- docs/milestones.md
- docs/design-principles.md
