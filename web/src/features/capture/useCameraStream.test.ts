import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useCameraStream } from './useCameraStream';

describe('useCameraStream', () => {
  const mockTrack = { stop: vi.fn() };
  const mockStream = {
    getTracks: () => [mockTrack],
  } as unknown as MediaStream;

  let getUserMediaMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockTrack.stop.mockClear();
    getUserMediaMock = vi.fn();

    Object.defineProperty(globalThis, 'navigator', {
      value: {
        mediaDevices: {
          getUserMedia: getUserMediaMock,
        },
      },
      writable: true,
      configurable: true,
    });

    // Mock HTMLVideoElement.play
    vi.spyOn(HTMLVideoElement.prototype, 'play').mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('starts in initializing status', () => {
    getUserMediaMock.mockReturnValue(new Promise(() => {})); // never resolves

    const { result } = renderHook(() => useCameraStream());
    expect(result.current.status).toBe('initializing');
    expect(result.current.error).toBeNull();
  });

  it('transitions to active on successful camera start', async () => {
    getUserMediaMock.mockResolvedValue(mockStream);

    const { result } = renderHook(() => useCameraStream());

    await waitFor(() => {
      expect(result.current.status).toBe('active');
    });

    expect(result.current.error).toBeNull();
  });

  it('transitions to error when camera access is denied', async () => {
    getUserMediaMock.mockRejectedValue(new DOMException('Permission denied', 'NotAllowedError'));

    const { result } = renderHook(() => useCameraStream());

    await waitFor(() => {
      expect(result.current.status).toBe('error');
    });

    expect(result.current.error).toBe(
      'カメラへのアクセスが許可されていません。ブラウザの設定を確認してください。',
    );
  });

  it('transitions to error when no camera found', async () => {
    getUserMediaMock.mockRejectedValue(new DOMException('No camera', 'NotFoundError'));

    const { result } = renderHook(() => useCameraStream());

    await waitFor(() => {
      expect(result.current.status).toBe('error');
    });

    expect(result.current.error).toContain('カメラが見つかりません');
  });

  it('stop() stops tracks and sets status to stopped', async () => {
    getUserMediaMock.mockResolvedValue(mockStream);

    const { result } = renderHook(() => useCameraStream());

    await waitFor(() => {
      expect(result.current.status).toBe('active');
    });

    act(() => {
      result.current.stop();
    });

    expect(mockTrack.stop).toHaveBeenCalled();
    expect(result.current.status).toBe('stopped');
  });

  it('stops tracks on unmount', async () => {
    getUserMediaMock.mockResolvedValue(mockStream);

    const { result, unmount } = renderHook(() => useCameraStream());

    await waitFor(() => {
      expect(result.current.status).toBe('active');
    });

    unmount();
    expect(mockTrack.stop).toHaveBeenCalled();
  });
});
