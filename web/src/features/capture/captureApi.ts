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
    readonly skewDegree: number;
    readonly aspectRatioError: number;
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

export async function correctImage(file: Blob): Promise<CorrectionResult> {
  const form = new FormData();
  form.append('file', file, 'capture.jpg');

  const res = await fetch(`${BASE_URL}/scan/correct`, {
    method: 'POST',
    body: form,
  });

  if (!res.ok) {
    const body = (await res.json()) as CorrectionError;
    throw new CaptureApiError(res.status, body.error, body.userAction);
  }

  return res.json() as Promise<CorrectionResult>;
}
