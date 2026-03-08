# ADR 003: マニフェストの生成・拡張・照合フロー

## ステータス

承認

## コンテキスト

マニフェストJSONはシステム全体の「唯一の真実」として、Module A（帳票出力）とModule B（帳票読取）の両方で使用される。マニフェストが生成されてから最終的にOCR座標照合に使われるまでの流れを明確に定義する必要がある。

## 決定

マニフェストは以下の3段階を経て使用される。

### Stage 1: 元マニフェスト（HTMLテンプレートに埋め込み）

Excel Form Editorが出力するHTMLテンプレートの `<script type="application/json" id="template-manifest">` に含まれるJSON。以下の情報を持つ:

- `templateId`, `version`
- `pages[].paper`（用紙サイズ、向き、余白）
- `pages[].fields[]`（`variableName`, `variableType`, `boxId`, `region`, `absoluteRegion`）
- `interface`（TypeScript型定義文字列）

### Stage 2: 拡張マニフェスト（Python側で生成）

テンプレート登録API（`POST /api/templates/parse`）が元マニフェストを受け取り、以下を追記して返す:

| 追加フィールド | 計算元 | 用途 |
|---------------|--------|------|
| `pages[].registrationMarks` | 用紙サイズと余白から算術計算 | Module Bのトンボ検出で照合先として使用 |
| `pages[].pageIdentifier` | テンプレートID＋ページインデックス | Module Bのページ自動判定で使用 |

拡張マニフェストは保存され、以降の全処理で使用される。

### Stage 3: OCR座標照合（Python側で使用）

Module Bの画像処理パイプラインが拡張マニフェストの座標を使用:

1. `registrationMarks.positions` → トンボ検出結果との照合、射影変換行列の算出
2. `fields[].absoluteRegion` → mm→ピクセル変換、ボックス切り出し
3. `fields[].variableType` / `inputType` → OCRエンジン選択、後処理切替

### フロー図

```
Excel Form Editor
       │
       ▼
HTMLテンプレート
  └─ <script id="template-manifest">
       │
       │ Stage 1: 元マニフェスト
       ▼
  ┌─────────────────────────────┐
  │  Python (api/)              │
  │  POST /api/templates/parse  │
  │                             │
  │  + registrationMarks 追記   │
  │  + pageIdentifier 追記      │
  │  + 整合性検証               │
  └──────────┬──────────────────┘
             │
             │ Stage 2: 拡張マニフェスト
             ▼
  ┌──────────┴──────────┐
  │                     │
  ▼                     ▼
Module A (web/)    Module B (api/)
印刷時の座標参照    OCR座標照合
  │                     │
  ▼                     ▼
印刷帳票            読取結果JSON
```

## 理由

### マニフェストを拡張するのはPython側のみ

- 座標の真実を一箇所に集約するため
- Module Bがマニフェストだけを入力として受け取る設計にするため
- ブラウザ側で計算してマニフェストに書き戻すのは流れとして不自然

### 元HTMLは拡張マニフェストとは別に保持する

- ブラウザ側で印刷時にDOMを展開するために元HTMLが必要
- マニフェストだけでは印刷用のCSS・レイアウト情報が失われる
- ただし、元HTMLはModule Bでは不要（マニフェストの座標だけで動作）

### `absoluteRegion` をOCR座標照合に使用する

- `region` はCSS座標系（印刷可能領域原点）
- `absoluteRegion` は用紙物理端原点の座標
- トンボは用紙物理端基準で配置されるため、射影変換後の座標は `absoluteRegion` と対応する

## 結果

- マニフェストの変更権限はPython側（テンプレート登録API）のみが持つ
- ブラウザ側はマニフェストを読み取り専用で参照する
- Module Bは拡張マニフェストJSONだけあれば動作する（Module Aが未導入でも可）
