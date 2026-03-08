# Backlog 012: B-4: 射影変換（台形補正）

## 状態
未着手

## 担当
—

## 対象パッケージ
api/

## 概要
検出したトンボ4点とマニフェストに記録されたトンボの既知座標（mm）を対応づけ、射影変換を適用する。斜め撮影による台形歪み・回転・縮尺ずれを一括補正する。

## 未実装の理由
前提マイルストーンが未完了

## 前提条件
- [ ] B-3（トンボ検出）完了

## 実装チェックリスト
- [ ] PerspectiveCorrector実装
- [ ] 変換行列算出
- [ ] 画像補正処理
- [ ] 補正精度テスト

## 着手時の注意事項
OpenCVのgetPerspectiveTransform + warpPerspectiveを使用する。ニューラルネット不要。

## 関連ドキュメント
- docs/milestones.md
- docs/design-principles.md
