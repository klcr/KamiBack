import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CaptureApiError, type CorrectionResult, correctImage } from './captureApi';

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
