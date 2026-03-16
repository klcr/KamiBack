/**
 * カメラストリーム管理フック。
 *
 * MediaStream API で背面カメラを起動し、キャプチャ機能を提供する。
 */

import { useCallback, useEffect, useRef, useState } from 'react';

export type CameraStatus = 'initializing' | 'active' | 'error' | 'stopped';

export interface UseCameraStreamReturn {
  readonly videoRef: React.RefObject<HTMLVideoElement | null>;
  readonly status: CameraStatus;
  readonly error: string | null;
  readonly capture: () => Promise<Blob | null>;
  readonly stop: () => void;
}

function stopAllTracks(stream: MediaStream | null) {
  if (!stream) return;
  for (const track of stream.getTracks()) {
    track.stop();
  }
}

function toUserMessage(err: unknown): string {
  if (!(err instanceof DOMException)) {
    return 'カメラの起動に失敗しました。';
  }
  switch (err.name) {
    case 'NotAllowedError':
      return 'カメラへのアクセスが許可されていません。ブラウザの設定を確認してください。';
    case 'NotFoundError':
      return 'カメラが見つかりません。デバイスにカメラが接続されているか確認してください。';
    case 'NotReadableError':
      return 'カメラが他のアプリで使用中です。他のアプリを閉じてから再度お試しください。';
    default:
      return `カメラの起動に失敗しました: ${err.message}`;
  }
}

export function useCameraStream(): UseCameraStreamReturn {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [status, setStatus] = useState<CameraStatus>('initializing');
  const [error, setError] = useState<string | null>(null);

  const releaseStream = useCallback(() => {
    stopAllTracks(streamRef.current);
    streamRef.current = null;
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' } },
          audio: false,
        });

        if (cancelled) {
          stopAllTracks(stream);
          return;
        }

        streamRef.current = stream;

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }

        setStatus('active');
      } catch (err) {
        if (cancelled) return;
        setError(toUserMessage(err));
        setStatus('error');
      }
    }

    startCamera();

    return () => {
      cancelled = true;
      releaseStream();
    };
  }, [releaseStream]);

  const stop = useCallback(() => {
    releaseStream();
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setStatus('stopped');
  }, [releaseStream]);

  const capture = useCallback(async (): Promise<Blob | null> => {
    const video = videoRef.current;
    if (!video || status !== 'active') return null;

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0);

    return new Promise<Blob | null>((resolve) => {
      canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.9);
    });
  }, [status]);

  return { videoRef, status, error, capture, stop };
}
