import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { ExtendedManifest } from '../../lib/types/manifest';
import { CameraCapturePage } from './CameraCapturePage';

// Mock useCameraStream
const mockCapture = vi.fn();
const mockStop = vi.fn();
let mockCameraStatus: string;
let mockCameraError: string | null;

vi.mock('./useCameraStream', () => ({
  useCameraStream: () => ({
    videoRef: { current: null },
    status: mockCameraStatus,
    error: mockCameraError,
    capture: mockCapture,
    stop: mockStop,
  }),
}));

// Mock captureApi
vi.mock('./captureApi', () => ({
  CaptureApiError: class CaptureApiError extends Error {
    status: number;
    userAction: string;
    constructor(status: number, message: string, userAction: string) {
      super(message);
      this.name = 'CaptureApiError';
      this.status = status;
      this.userAction = userAction;
    }
  },
  correctImage: vi.fn(),
}));

describe('CameraCapturePage', () => {
  const manifest: ExtendedManifest = {
    templateId: 'test-001',
    version: '1.0',
    pages: [
      {
        pageIndex: 0,
        paper: {
          size: 'A4',
          orientation: 'portrait',
          widthMm: 210,
          heightMm: 297,
          margins: { top: 10, right: 10, bottom: 10, left: 10 },
          centering: { horizontal: false, vertical: false },
        },
        fields: [],
        registrationMarks: {
          shape: 'circle_cross',
          radiusMm: 3,
          positions: [
            { x: 5, y: 5 },
            { x: 205, y: 5 },
            { x: 5, y: 292 },
            { x: 205, y: 292 },
          ],
        },
        pageIdentifier: {
          type: 'qr',
          content: 'test-001/0',
          position: { x: 197, y: 284 },
          sizeMm: 8,
        },
      },
    ],
  };

  beforeEach(() => {
    mockCameraStatus = 'active';
    mockCameraError = null;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders camera view with shutter button when active', () => {
    render(<CameraCapturePage manifest={manifest} onCaptured={vi.fn()} />);
    expect(screen.getByLabelText('撮影')).toBeDefined();
    expect(screen.getByText('帳票を撮影')).toBeDefined();
  });

  it('shows initializing message when camera is starting', () => {
    mockCameraStatus = 'initializing';
    render(<CameraCapturePage manifest={manifest} onCaptured={vi.fn()} />);
    expect(screen.getByText('カメラを起動中...')).toBeDefined();
  });

  it('disables shutter button when camera is not active', () => {
    mockCameraStatus = 'initializing';
    render(<CameraCapturePage manifest={manifest} onCaptured={vi.fn()} />);
    const button = screen.getByLabelText('撮影');
    expect(button).toHaveProperty('disabled', true);
  });

  it('shows file fallback when camera has error', () => {
    mockCameraStatus = 'error';
    mockCameraError = 'カメラへのアクセスが許可されていません。';
    render(<CameraCapturePage manifest={manifest} onCaptured={vi.fn()} />);
    expect(screen.getByText('カメラへのアクセスが許可されていません。')).toBeDefined();
    expect(screen.getByText('撮影した画像ファイルを選択してください。')).toBeDefined();
  });

  it('shows file select link', () => {
    render(<CameraCapturePage manifest={manifest} onCaptured={vi.fn()} />);
    expect(screen.getByText('ファイルから選択')).toBeDefined();
  });

  it('switches to file mode when file select link is clicked', () => {
    render(<CameraCapturePage manifest={manifest} onCaptured={vi.fn()} />);
    fireEvent.click(screen.getByText('ファイルから選択'));
    expect(mockStop).toHaveBeenCalled();
    expect(screen.getByText('撮影した画像ファイルを選択してください。')).toBeDefined();
  });

  it('renders guide overlay when camera is active', () => {
    render(<CameraCapturePage manifest={manifest} onCaptured={vi.fn()} />);
    expect(screen.getByText('四隅のマークが枠内に入るように撮影してください')).toBeDefined();
  });
});
