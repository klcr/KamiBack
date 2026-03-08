# Backlog 015: B-7: OCR実行

## 状態
未着手

## 担当
—

## 対象パッケージ
api/, domain/

## 概要
切り出した各ボックス画像に対してOCRを実行する。`variableType`に応じてOCRエンジンまたは後処理を切り替える。活字・手書きの切り替えは`inputType`で制御する。

## 未実装の理由
前提マイルストーンが未完了

## 前提条件
- [ ] B-6（ボックス切出）完了
- [ ] NDLOCR-Lite統合

## 実装チェックリスト
- [ ] OcrEngine ABC実装(domain/)
- [ ] NDLOCR-Lite統合(api/infra)
- [ ] inputType別切替
- [ ] テスト

## 着手時の注意事項
エンジンの差し替えを前提にする。「画像→文字列と信頼度」の統一インターフェースとする。

## 関連ドキュメント
- docs/milestones.md
- docs/design-principles.md
