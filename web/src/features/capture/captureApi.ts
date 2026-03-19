/**
 * スキャン API クライアント。
 *
 * POST /api/scan/correct — 撮影画像の補正
 * POST /api/scan/ocr    — OCR実行
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export interface CorrectionResult {
  readonly imageId: string;
  readonly imagePath: string;
  readonly templateId: string;
  readonly pageIndex: number;
  readonly tombo: {
    readonly detectionCount: number;
    readonly hasEstimation: boolean;
    readonly skewDegree: number | null;
    readonly aspectRatioError: number | null;
  };
  readonly scalePxPerMm: number;
}

export interface CorrectionError {
  readonly error: string;
  readonly userAction: string;
}

export class CaptureApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly userAction: string,
  ) {
    super(message);
    this.name = 'CaptureApiError';
  }
}

export interface CorrectImageOptions {
  readonly templateId?: string;
  readonly pageIndex?: number;
}

export async function correctImage(
  file: Blob,
  options?: CorrectImageOptions,
): Promise<CorrectionResult> {
  const form = new FormData();
  form.append('file', file, 'capture.jpg');

  const params = new URLSearchParams();
  if (options?.templateId != null) {
    params.set('template_id', options.templateId);
  }
  if (options?.pageIndex != null) {
    params.set('page_index', String(options.pageIndex));
  }
  const query = params.toString();
  const url = `${BASE_URL}/scan/correct${query ? `?${query}` : ''}`;

  const res = await fetch(url, {
    method: 'POST',
    body: form,
  });

  if (!res.ok) {
    const body = (await res.json()) as CorrectionError;
    throw new CaptureApiError(res.status, body.error, body.userAction);
  }

  return res.json() as Promise<CorrectionResult>;
}

/** OCR実行リクエスト。 */
export interface OcrRequest {
  readonly imageId: string;
  readonly templateId: string;
  readonly pageIndex: number;
  readonly scalePxPerMm: number;
}

/** 1フィールドのOCR結果。 */
export interface FieldResultDto {
  readonly variableName: string;
  readonly variableType: string;
  readonly value: string | number | boolean | null;
  readonly rawText: string;
  readonly confidence: number;
  readonly status: 'confirmed' | 'needs_review' | 'failed' | 'corrected';
}

/** OCR実行結果。 */
export interface OcrResult {
  readonly templateId: string;
  readonly pageIndex: number;
  readonly fieldResults: readonly FieldResultDto[];
}

/** OCRを実行する。 */
export async function executeOcr(request: OcrRequest): Promise<OcrResult> {
  const url = `${BASE_URL}/scan/ocr`;

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image_id: request.imageId,
      template_id: request.templateId,
      page_index: request.pageIndex,
      scale_px_per_mm: request.scalePxPerMm,
    }),
  });

  if (!res.ok) {
    const body = (await res.json()) as CorrectionError;
    throw new CaptureApiError(res.status, body.error, body.userAction);
  }

  return res.json() as Promise<OcrResult>;
}
