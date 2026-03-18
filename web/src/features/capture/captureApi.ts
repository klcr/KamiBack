/**
 * 撮影画像の補正 API クライアント。
 *
 * POST /api/scan/correct に画像を送信し、補正結果を返す。
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
