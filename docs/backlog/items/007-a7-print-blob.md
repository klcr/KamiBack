# Backlog 007: A-7: 印刷用blob生成

## 状態
完了

## 担当
—

## 対象パッケージ
web/

## 概要
変数差し替え済み・トンボ挿入済みのHTMLからblob URLを生成し、`window.print()`またはiframe経由での印刷を可能とする。`@page`ルールによる用紙サイズ指定と`page-break-after`による改ページ制御をそのまま活かす。

## 未実装の理由
前提マイルストーンが未完了

## 前提条件
- [ ] M3b.1（トンボ描画）完了
- [ ] M3b.2（ページ識別コード）完了

## 実装チェックリスト
- [ ] blob URL生成
- [ ] iframe印刷
- [ ] @pageルール検証
- [ ] 100%スケーリング確認

## 着手時の注意事項
印刷は`@page`CSS + `window.print()`が最短・最正確パス（ADR-002参照）。マイルストーン: M3b。

## 関連ドキュメント
- docs/milestones.md
- docs/design-principles.md
- docs/adr/002-*.md
