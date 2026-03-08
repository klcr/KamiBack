# Backlog 016: B-8: 変数格納

## 状態
未着手

## 担当
—

## 対象パッケージ
api/, domain/

## 概要
OCR結果をマニフェストの`variableName`をキーとするオブジェクトに格納する。TypeScript型定義に基づく型変換（文字列→数値、文字列→日付など）を適用する。

## 未実装の理由
前提マイルストーンが未完了

## 前提条件
- [ ] B-7（OCR実行）完了

## 実装チェックリスト
- [ ] OcrResult集約実装
- [ ] 型変換ロジック
- [ ] テスト

## 着手時の注意事項
型変換はdomain層のポリシーとして実装する。

## 関連ドキュメント
- docs/milestones.md
- docs/design-principles.md
