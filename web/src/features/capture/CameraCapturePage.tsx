/**
 * カメラ撮影ページ。
 *
 * デバイスカメラを起動し、ガイドオーバーレイ付きで撮影→補正APIに送信する。
 * カメラ非対応時はファイルアップロードにフォールバックする。
 */

import { type ChangeEvent, useRef, useState } from 'react';
import type { ExtendedManifest } from '../../lib/types/manifest';
import { CaptureGuideOverlay } from './CaptureGuideOverlay';
import { QrFallbackSelector } from './QrFallbackSelector';
import { CaptureApiError, type CorrectionResult, correctImage } from './captureApi';
import { useCameraStream } from './useCameraStream';

type PageStatus = 'camera' | 'submitting' | 'qr-fallback' | 'file-fallback';

interface Props {
  readonly manifest: ExtendedManifest;
  readonly onCaptured: (result: CorrectionResult) => void;
}

export function CameraCapturePage({ manifest, onCaptured }: Props) {
  const { videoRef, status: cameraStatus, error: cameraError, capture, stop } = useCameraStream();
  const [pageStatus, setPageStatus] = useState<PageStatus>('camera');
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [pendingBlob, setPendingBlob] = useState<Blob | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const paper = manifest.pages[0].paper;

  const handleShutter = async () => {
    const blob = await capture();
    if (!blob) return;

    await submitImage(blob);
  };

  const submitImage = async (blob: Blob) => {
    setPageStatus('submitting');
    setSubmitError(null);

    try {
      const result = await correctImage(blob);
      stop();
      onCaptured(result);
    } catch (err) {
      if (err instanceof CaptureApiError) {
        setPendingBlob(blob);
        setSubmitError(err.userAction);
        setPageStatus('qr-fallback');
      } else {
        setSubmitError('画像の送信に失敗しました。通信環境を確認してください。');
        setPageStatus('camera');
      }
    }
  };

  const handleRetry = () => {
    setPageStatus('camera');
    setSubmitError(null);
    setPendingBlob(null);
  };

  const handleQrFallbackConfirm = async (_templateId: string, _pageIndex: number) => {
    if (!pendingBlob) return;
    // TODO: テンプレートID指定付きの再送信（API側の対応が必要）
    // 現時点では同じ画像を再送信
    await submitImage(pendingBlob);
  };

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    submitImage(file);
  };

  const handleSwitchToFile = () => {
    setPageStatus('file-fallback');
    stop();
  };

  // カメラエラー時: ファイルアップロードフォールバック
  if (cameraStatus === 'error' || pageStatus === 'file-fallback') {
    return (
      <div>
        <h2 style={{ fontSize: '16px', marginBottom: '12px' }}>帳票を撮影</h2>

        {cameraError && (
          <div
            style={{
              padding: '12px',
              background: '#fce4ec',
              border: '1px solid #ef9a9a',
              borderRadius: '4px',
              marginBottom: '16px',
              fontSize: '14px',
            }}
          >
            {cameraError}
          </div>
        )}

        <p style={{ fontSize: '14px', marginBottom: '12px' }}>
          撮影した画像ファイルを選択してください。
        </p>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleFileSelect}
        />

        {submitError && (
          <div
            style={{
              padding: '12px',
              background: '#fff3e0',
              border: '1px solid #ffcc80',
              borderRadius: '4px',
              marginTop: '12px',
              fontSize: '14px',
            }}
          >
            {submitError}
          </div>
        )}
      </div>
    );
  }

  // QRフォールバック
  if (pageStatus === 'qr-fallback') {
    return (
      <div>
        <h2 style={{ fontSize: '16px', marginBottom: '12px' }}>帳票を撮影</h2>
        <QrFallbackSelector
          manifest={manifest}
          errorMessage={submitError ?? ''}
          onConfirm={handleQrFallbackConfirm}
          onRetry={handleRetry}
        />
      </div>
    );
  }

  return (
    <div>
      <h2 style={{ fontSize: '16px', marginBottom: '12px' }}>帳票を撮影</h2>

      <div
        style={{
          position: 'relative',
          width: '100%',
          maxWidth: '640px',
          margin: '0 auto',
          background: '#000',
          borderRadius: '4px',
          overflow: 'hidden',
        }}
      >
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          style={{ width: '100%', display: 'block' }}
        />
        {cameraStatus === 'active' && <CaptureGuideOverlay paper={paper} />}

        {cameraStatus === 'initializing' && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: '14px',
            }}
          >
            カメラを起動中...
          </div>
        )}
      </div>

      <div style={{ textAlign: 'center', marginTop: '16px' }}>
        <button
          type="button"
          onClick={handleShutter}
          disabled={cameraStatus !== 'active' || pageStatus === 'submitting'}
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            border: '3px solid #1a73e8',
            background: pageStatus === 'submitting' ? '#ccc' : 'white',
            cursor: cameraStatus === 'active' ? 'pointer' : 'not-allowed',
            position: 'relative',
          }}
          aria-label="撮影"
        >
          {pageStatus === 'submitting' && (
            <span style={{ fontSize: '12px', color: '#666' }}>送信中</span>
          )}
        </button>
      </div>

      {submitError && (
        <div
          style={{
            padding: '12px',
            background: '#fff3e0',
            border: '1px solid #ffcc80',
            borderRadius: '4px',
            marginTop: '12px',
            fontSize: '14px',
            textAlign: 'center',
          }}
        >
          {submitError}
        </div>
      )}

      <div style={{ textAlign: 'center', marginTop: '12px' }}>
        <button
          type="button"
          onClick={handleSwitchToFile}
          style={{
            background: 'none',
            border: 'none',
            color: '#1a73e8',
            fontSize: '13px',
            cursor: 'pointer',
            textDecoration: 'underline',
          }}
        >
          ファイルから選択
        </button>
      </div>
    </div>
  );
}
