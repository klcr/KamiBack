# Backlog 011: B-3: トンボ検出

## 状態
未着手

## 担当
—

## 対象パッケージ
api/, domain/

## 概要
撮影画像から四隅のレジストレーションマークを検出する。ハフ変換による円検出＋十字交差点のサブピクセル特定。4点中3点の検出で動作可能とし、残り1点は用紙アスペクト比から推定する。

## 未実装の理由
前提マイルストーンが未完了

## 前提条件
- [ ] M2完了
- [ ] OpenCV依存の追加

## 実装チェックリスト
- [ ] HoughTomboDetector実装
- [ ] TomboDetector ABCのinfra実装
- [ ] 3点検出フォールバック
- [ ] テスト

## 着手時の注意事項
判断基準4「事前学習に依存しない」。古典的CV手法のみ使用。domain/にABC、api/infraに実装する。

## 関連ドキュメント
- docs/milestones.md
- docs/design-principles.md
