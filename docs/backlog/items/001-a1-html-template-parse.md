# Backlog 001: A-1: HTMLテンプレート読み込み

## 状態
完了

## 担当
—

## 対象パッケージ
api/, domain/

## 概要
HTML文字列をパースし、`<script id="template-manifest">`からマニフェストJSONを抽出。DOMとしてのページ構造・変数定義・座標情報をオブジェクトとして保持する。

## 未実装の理由
前提マイルストーンが未完了

## 前提条件
- [ ] M2（マニフェスト型定義）完了

## 実装チェックリスト
- [ ] HTMLパーサー実装
- [ ] マニフェスト抽出ロジック
- [ ] テスト

## 着手時の注意事項
Python側（api/）でBeautifulSoup等でパース。domain型に変換すること。マイルストーン: M3a。

## 関連ドキュメント
- docs/milestones.md
- docs/design-principles.md
