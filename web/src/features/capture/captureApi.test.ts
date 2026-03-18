import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  CaptureApiError,
  type CorrectionResult,
  type OcrResult,
  correctImage,
  executeOcr,
} from './captureApi';

describe('correctImage', () => {
  const mockResult: CorrectionResult = {
    imageId: 'img-001',
    imagePath: '/tmp/corrected/img-001.png',
    templateId: 'test-001',
    pageIndex: 0,
    tombo: {
      detectionCount: 4,
      hasEstimation: false,
      skewDegree: 1.2,
      aspectRatioError: 0.5,
    },
    scalePxPerMm: 10.0,
  };

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('sends image as FormData and returns result on success', async () => {
    const blob = new Blob(['fake-image'], { type: 'image/jpeg' });

    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResult),
    } as Response);

    const result = await correctImage(blob);

    expect(fetch).toHaveBeenCalledOnce();
    const [url, options] = vi.mocked(fetch).mock.calls[0];
    expect(url).toBe('/api/scan/correct');
    expect(options?.method).toBe('POST');
    expect(options?.body).toBeInstanceOf(FormData);

    const form = options?.body as FormData;
    expect(form.get('file')).toBeInstanceOf(Blob);

    expect(result).toEqual(mockResult);
  });

  it('appends template_id and page_index as query params when options provided', async () => {
    const blob = new Blob(['fake-image'], { type: 'image/jpeg' });

    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResult),
    } as Response);

    await correctImage(blob, { templateId: 'tmpl-abc', pageIndex: 2 });

    expect(fetch).toHaveBeenCalledOnce();
    const [url] = vi.mocked(fetch).mock.calls[0];
    expect(url).toBe('/api/scan/correct?template_id=tmpl-abc&page_index=2');
  });

  it('does not append query params when options are omitted', async () => {
    const blob = new Blob(['fake-image'], { type: 'image/jpeg' });

    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResult),
    } as Response);

    await correctImage(blob);

    const [url] = vi.mocked(fetch).mock.calls[0];
    expect(url).toBe('/api/scan/correct');
  });

  it('throws CaptureApiError with userAction on failure', async () => {
    const blob = new Blob(['fake-image'], { type: 'image/jpeg' });

    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 400,
      json: () =>
        Promise.resolve({
          error: 'QRコードが検出できませんでした',
          userAction: '帳票全体が写るように撮り直してください',
        }),
    } as Response);

    await expect(correctImage(blob)).rejects.toThrow(CaptureApiError);

    try {
      await correctImage(blob);
    } catch (e) {
      const err = e as CaptureApiError;
      expect(err.status).toBe(400);
      expect(err.message).toBe('QRコードが検出できませんでした');
      expect(err.userAction).toBe('帳票全体が写るように撮り直してください');
    }
  });
});

describe('executeOcr', () => {
  const mockOcrResult: OcrResult = {
    templateId: 'test-001',
    pageIndex: 0,
    fieldResults: [
      {
        variableName: 'company_name',
        variableType: 'string',
        value: '株式会社テスト',
        rawText: '株式会社テスト',
        confidence: 0.92,
        status: 'confirmed',
      },
    ],
  };

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('sends JSON request and returns OCR result', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockOcrResult),
    } as Response);

    const result = await executeOcr({
      imageId: 'img-001',
      templateId: 'test-001',
      pageIndex: 0,
      scalePxPerMm: 10.0,
    });

    expect(fetch).toHaveBeenCalledOnce();
    const [url, options] = vi.mocked(fetch).mock.calls[0];
    expect(url).toBe('/api/scan/ocr');
    expect(options?.method).toBe('POST');
    expect(options?.headers).toEqual({ 'Content-Type': 'application/json' });

    const body = JSON.parse(options?.body as string);
    expect(body.image_id).toBe('img-001');
    expect(body.template_id).toBe('test-001');
    expect(body.scale_px_per_mm).toBe(10.0);

    expect(result).toEqual(mockOcrResult);
  });

  it('throws CaptureApiError on failure', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 400,
      json: () =>
        Promise.resolve({
          error: 'テンプレートが見つかりません',
          userAction: '登録済みのテンプレートで印刷した帳票を使用してください',
        }),
    } as Response);

    await expect(
      executeOcr({
        imageId: 'img-001',
        templateId: 'unknown',
        pageIndex: 0,
        scalePxPerMm: 10.0,
      }),
    ).rejects.toThrow(CaptureApiError);
  });
});
