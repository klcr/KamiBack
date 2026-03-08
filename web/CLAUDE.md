# web/

## このパッケージの役割

KamiBack のレビュー UI。React + Vite で構築。OCR結果の確認・修正を行う画面を提供する。

## ディレクトリ構成

- `src/features/` — 機能単位のディレクトリ
- `src/components/` — 汎用 UI コンポーネント（layout, common）
- `src/hooks/` — アプリ横断のカスタムフック
- `src/lib/` — ユーティリティ（apiClient, constants）

## 開発サーバー

```bash
npm run dev
```

## ルール

- 1 コンポーネント 1 ファイル
- ページコンポーネント: `{Name}Page.tsx`
- ビューコンポーネント: `{Name}View.tsx`
- カスタムフック: `use{Name}.ts`
- API 呼び出し: `{feature}Api.ts`
