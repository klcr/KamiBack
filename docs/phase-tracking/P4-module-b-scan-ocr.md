# P4: Module B — 帳票読取エンジン フェーズ追跡

> 最終更新: 2026-03-16 (B-6, B-7 完了)

## 概要

撮影画像からトンボを検出し、射影変換で歪みを補正し、マニフェストのmm座標でボックスを切り出してOCRを実行する。

**設計判断の根拠**: `docs/adr/004-scan-ocr-pipeline.md`（DJ-1〜DJ-9）

## パイプライン全体像

```
撮影画像
  │
  ├─ [B-2] QRコード検出 → テンプレートID + ページインデックス
  │
  ├─ [B-3] トンボ検出（ハフ変換）→ 3〜4点
  │    └─ 3点時: 4点目幾何推定 + 歪み閾値判定 (DJ-2)
  │
  ├─ [B-4] 射影変換 → 補正画像
  │
  ├─ [B-5] 画像前処理（グレースケール→ブラー→適応的二値化）
  │
  │  ── UC-1: correct_image ここまで (DJ-9) ──
  │  ── 補正画像をファイルシステムに保存 (DJ-8) ──
  │
  ├─ [B-6] mm→pixel変換（トンボ間距離から逆算）(DJ-1)
  │    └─ ボックス切出（absoluteRegion → ピクセル → crop）
  │
  ├─ [B-7] OCR実行（サブプロセス呼出）(DJ-3)
  │    └─ inputType別エンジン切替
  │
  ├─ [B-9] 信頼度スコア付与（inputType別閾値）(DJ-7)
  │
  ├─ [B-8] 変数格納（型変換 + FieldResult構築）
  │
  │  ── UC-2: execute_ocr ここまで (DJ-9) ──
  │  ── SSEで逐次送信 (DJ-6) ──
  │
  ├─ [B-10] レビューUI（補正画像上にオーバーレイ）
  │
  └─ [B-11] 確定・出力（JSON）
```

## フェーズ分割

### Phase M4a: 画像補正パイプライン

| # | タスク | バックログ | 設計判断 | 状態 | 備考 |
|---|--------|-----------|---------|------|------|
| 1 | OpenCV + pyzbar 依存追加 | — | DJ-3, DJ-4 | 完了 | pyproject.toml |
| 2 | `ImageStorage`インターフェース定義 | — | DJ-8 | 未着手 | domain層 |
| 3 | `LocalFileImageStorage`実装 | — | DJ-8 | 未着手 | api/infrastructure |
| 4 | `HoughTomboDetector`実装 | B-3 (011) | DJ-2 | 完了 | api/infrastructure |
| 5 | 4点目幾何推定 + 歪み閾値判定 | B-3 (011) | DJ-2 | 完了 | api/infrastructure |
| 6 | `PerspectiveCorrector`実装 | B-4 (012) | DJ-1 | 完了 | api/infrastructure |
| 7 | 画像前処理パイプライン | B-5 (013) | — | 完了 | api/infrastructure |
| 8 | QRコード検出 | B-2 (010) | DJ-4, DJ-5 | 未着手 | api/infrastructure |
| 9 | `correct_image`ユースケース | — | DJ-9 | 未着手 | api/use_cases |
| 10 | `POST /api/scan/correct` API | — | DJ-9 | 未着手 | api/routes |
| 11 | カメラUI | B-1 (009) | — | 未着手 | web/ |

**完了条件**: スマホ撮影画像からトンボ検出→射影変換→補正画像保存が動作する

### Phase M4b: OCR実行パイプライン

| # | タスク | バックログ | 設計判断 | 状態 | 備考 |
|---|--------|-----------|---------|------|------|
| 1 | mm↔pixelスケール係数算出 | B-6 (014) | DJ-1 | 完了 | api/infrastructure/cv/box_cropper.py |
| 2 | ボックス切出ロジック | B-6 (014) | DJ-1 | 完了 | api/infrastructure/cv/box_cropper.py |
| 3 | `SubprocessOcrEngine`実装 | B-7 (015) | DJ-3 | 完了 | api/infrastructure/ocr/subprocess_ocr_engine.py |
| 4 | inputType別閾値テーブル | B-9 (017) | DJ-7 | 未着手 | domain/ |
| 5 | `determine_reading_status()`にinputType対応追加 | B-9 (017) | DJ-7 | 未着手 | domain/ |
| 6 | `execute_ocr`ユースケース | — | DJ-9 | 未着手 | api/use_cases |
| 7 | `POST /api/scan/ocr` API（SSE） | — | DJ-6 | 未着手 | api/routes |
| 8 | 変数格納・型変換 | B-8 (016) | — | 未着手 | domain policy既存 |
| 9 | レビューUI | B-10 (018) | — | 未着手 | web/ |
| 10 | 確定・出力 | B-11 (019) | — | 未着手 | domain/ + web/ |

**完了条件**: 補正画像+マニフェスト→フィールド単位OCR→信頼度つき結果のSSE送信が動作する

## 依存関係

```
M4a タスク依存:
  1 (依存追加) → 4 (トンボ検出) → 5 (4点目推定)
                                         ↓
  2 (ImageStorage IF) → 3 (LocalFile)    6 (射影変換) → 7 (前処理)
                                         ↓
                              8 (QR検出) → 9 (UC correct_image) → 10 (API)
                                                                      ↑
                                                        11 (カメラUI) ┘

M4b タスク依存:
  M4a完了 → 1 (スケール係数) → 2 (ボックス切出)
                                     ↓
            3 (SubprocessOCR) → 6 (UC execute_ocr) → 7 (SSE API)
                                     ↑                     ↓
            4,5 (閾値テーブル) ───────┘              9 (レビューUI) → 10 (出力)
            8 (変数格納) ────────────┘
```

## 設計判断と参照先の対応

| DJ# | 判断事項 | ADR参照 | 影響タスク |
|-----|---------|---------|-----------|
| DJ-1 | mm↔pixel変換: トンボ間距離逆算 | ADR-004 | M4a-6, M4b-1,2 |
| DJ-2 | 3点トンボ: 幾何推定+歪み閾値 | ADR-004 | M4a-4,5 |
| DJ-3 | OCRエンジン: サブプロセス→HTTP移行想定 | ADR-004 | M4b-3 |
| DJ-4 | ページ識別: QRコード | ADR-004 | M4a-8 |
| DJ-5 | QR失敗: リトライ3回→手動選択 | ADR-004 | M4a-8,11 |
| DJ-6 | レスポンス: SSE逐次送信 | ADR-004 | M4b-7 |
| DJ-7 | 閾値: inputType別テーブル | ADR-004 | M4b-4,5 |
| DJ-8 | 画像保持: ファイルシステム→S3移行想定 | ADR-004 | M4a-2,3 |
| DJ-9 | ユースケース: correct_image + execute_ocr | ADR-004 | M4a-9, M4b-6 |

## 新規ファイル一覧（予定）

### domain/

```
domain/src/scan/                          # 新規ドメイン（scan コンテキスト）
  ├── image_storage.py                    # ImageStorage ABC (DJ-8)
  └── image_storage_test.py
```

### api/

```
api/src/infrastructure/
  ├── cv/
  │   ├── hough_tombo_detector.py         # HoughTomboDetector (DJ-2)
  │   ├── hough_tombo_detector_test.py
  │   ├── perspective_corrector.py        # PerspectiveCorrector (DJ-1)
  │   ├── perspective_corrector_test.py
  │   ├── image_preprocessor.py           # グレースケール→ブラー→二値化
  │   ├── image_preprocessor_test.py
  │   ├── qr_detector.py                  # QRコード検出 (DJ-4)
  │   └── qr_detector_test.py
  ├── ocr/
  │   ├── subprocess_ocr_engine.py        # SubprocessOcrEngine (DJ-3)
  │   └── subprocess_ocr_engine_test.py
  └── storage/
      ├── local_file_image_storage.py     # LocalFileImageStorage (DJ-8)
      └── local_file_image_storage_test.py

api/src/use_cases/
  ├── correct_image.py                    # UC-1 (DJ-9)
  ├── correct_image_test.py
  ├── execute_ocr.py                      # UC-2 (DJ-9)
  └── execute_ocr_test.py

api/src/api/routes/scan/
  ├── __init__.py
  ├── correct.py                          # POST /api/scan/correct (DJ-9)
  └── ocr.py                              # POST /api/scan/ocr SSE (DJ-6, DJ-9)
```

### web/

```
web/src/features/capture/
  ├── CameraCapturePage.tsx               # カメラUI (B-1)
  ├── useCameraStream.ts                  # MediaStream hook
  ├── CaptureGuideOverlay.tsx             # 撮影ガイド
  └── QrFallbackSelector.tsx              # QR失敗時の手動選択 (DJ-5)

web/src/features/review/
  ├── ReviewPage.tsx                       # レビューUI (B-10)
  ├── useOcrStream.ts                      # SSE受信hook (DJ-6)
  ├── FieldOverlay.tsx                     # 補正画像上のオーバーレイ
  └── ConfidenceHighlight.tsx              # 信頼度ハイライト (DJ-7)
```

## ビジョン検証ゲートとの関係

| ゲート | 前提 | 本フェーズの関与 |
|--------|------|----------------|
| VG-1 | M3b + M4a | M4a完了時に検証実施を促す |
| VG-2 | M4b | M4b完了時に検証実施を促す |

> VG-1が「合格」または「条件付合格」になるまでM4bに進まない。
