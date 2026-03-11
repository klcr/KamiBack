# 事象 001: 印刷プレビューで水平センタリングが反映されない

## 起票日

2026-03-10

## 対象レイヤー

web（PrintPreviewPage）、api（html_parser）、domain（template_types / manifest_types）

## 事象の概要

`<section class="sheet" data-horizontal-centered="true">` を持つHTMLテンプレートを印刷プレビューで表示した際、シート（印刷可能領域）が用紙幅の中央に配置されず、左寄せのまま表示される。

## 発生状況

Excel Form Editor が生成した帳票HTMLをアップロードし、変数をバインドして印刷プレビュー（ステップ3）に進んだところ、期待されるレイアウト（水平中央寄せ）と実際の表示に差異がある。

**期待**: `<section class="sheet">` の幅（例: 184.6mm）が用紙幅（例: 210mm）の中央に配置され、左右に均等な余白（各12.7mm）が入る。

**実際**: シートが iframe 内で左端に寄っており、右側に余白が偏っている。

## 調査・対応の経緯

- 2026-03-10: 調査開始。`data-horizontal-centered` / `data-vertical-centered` 属性はパース・保存されているが、レンダリング時にCSSとして適用されていなかった。

- 2026-03-10（修正1）: `PrintPreviewPage` でマニフェストの `paper.centering` を参照し、`margin-left: auto; margin-right: auto;` を含む `<style>` タグを iframe 内HTMLに注入するよう変更。→ **解消せず**。

- 2026-03-10（修正1の問題特定）: マニフェストJSON に `centering` キーが存在しない場合、`paper.centering` がデフォルト `{horizontal: false, vertical: false}` となり CSS が注入されないことを発見。DOM属性 `data-horizontal-centered="true"` は `PageTemplate` にパースされるが、`PrintPreviewPage` がマニフェスト側しか参照していなかった。データソースの不整合。

- 2026-03-10（修正2）: マニフェストJSONへの依存を排除し、CSS属性セレクタ `section.sheet[data-horizontal-centered="true"]` でDOM属性を直接参照する方式に変更。併せて iframe 内の `body { margin: 0; }` も追加。→ **解消せず**。ハードリロード・キャッシュクリアも試行済み。

- 2026-03-10: ビルドエラー（テスト4ファイルで `Paper` に `centering` 必須プロパティ不足）を修正。

## 残っている仮説

以下のいずれかが原因の可能性があり、未検証。

### 仮説A: テンプレートHTMLに `data-horizontal-centered` 属性が付与されていない

Excel Form Editor が出力するHTMLに `data-horizontal-centered="true"` が含まれていない場合、CSS属性セレクタが一致せずセンタリングが適用されない。DevTools で iframe 内の `<section class="sheet">` 要素を直接確認し、属性の有無を検証する必要がある。

### 仮説B: CSS `margin: auto` がインラインスタイルとの競合で無効化されている → **原因の一部**

`<section class="sheet">` のインラインスタイル `style="position: relative; width: Xmm; height: Ymm;"` と注入CSSの相互作用で、期待通りのレイアウトにならない可能性。`position: relative` は `margin: auto` を阻害しないはずだが、iframe 内の特殊なレンダリングコンテキストで異なる挙動を示す可能性がある。

**検証結果**: 印刷時は名前付き `@page page0` ルール（テンプレートHTML内）がマージンを持ち、シートが印刷可能領域を正確に埋めるため `margin: auto` の効果がゼロになる。また、垂直方向は CSS 通常フローでは `margin-top/bottom: auto` が常に 0 に解決されるため根本的に機能しない。

### 仮説C: iframe の内部レイアウトの問題

iframe の `srcDoc` で注入された `<style>` が正しくパースされていない、または `</head>` への挿入位置が不適切で CSS が適用されない可能性。DevTools で iframe のドキュメントを展開し、注入された `<style>` タグと computed style を確認する必要がある。

### 仮説D: センタリングのセマンティクスが `margin: auto` ではない → **根本原因**

Excel のセンタリング設定は「印刷時のページ中央寄せ」であり、CSS的には `margin: auto` ではなく、ボックスの絶対座標自体をオフセットすべき可能性がある。`data-origin="printable-area"` との関連で、座標体系の原点とセンタリングの関係を再検討する必要がある。

**検証結果**: Excel の「ページ中央」はマージンの均等化（左右均等 / 上下均等）で実現される。`margin: auto` でシートコンテナを中央寄せするアプローチは根本的に誤り。正しくは `@page` ルールのマージン値を `(left + right) / 2` / `(top + bottom) / 2` に均等化すべき。

## 根本原因の分析（2026-03-11 追記）

3つの問題が重なっていた。

1. **垂直中央揃えが CSS 通常フローで不可能**: `margin-top: auto; margin-bottom: auto` はブロック要素の通常フローでは常に 0 に解決される（CSS仕様）。flexbox/grid 以外では機能しない。

2. **印刷時、名前付き `@page` ルールが無名 `@page` を上書き**: `@page { margin: 0; }` を注入しても、テンプレートHTML内の `@page page0 { margin: 25.4mm ... }` が優先される。結果、シートが印刷可能領域を正確に埋め、`margin: auto` が効くスペースがゼロ。

3. **セマンティクスの誤り**: Excel の「ページ中央」は `@page` マージンの均等化であり、シートコンテナの `margin: auto` ではない。

## 修正内容（2026-03-11）

`margin: auto` 方式を廃止し、マージン均等化方式に変更。

- `buildPrintHtml.ts`: `equalizeMargins()` 関数を追加。名前付き `@page page0` ルールに均等化マージンを注入し、テンプレートの元ルールを上書き。
- `PrintPreviewPage.tsx`: iframe 内のシートに均等化マージン位置を CSS `margin-left` / `margin-top` で直接指定。
- `buildPrintHtml.test.ts`: `equalizeMargins` のユニットテスト4件 + `buildPrintHtml` のセンタリング出力テスト4件を追加。

## 関連ドキュメント

- `docs/constraints/` — HTML仕様の制約条件（該当あれば追記）
- コミット: `be3411e` (修正2), `92090a9` (テスト修正)

## 解決

修正済み（ユーザー検証待ち）
