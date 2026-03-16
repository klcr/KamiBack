/**
 * 撮影ガイドオーバーレイ。
 *
 * カメラプレビュー上に用紙枠と四隅のマーカーを表示し、撮影品質を底上げする。
 */

import type { Paper } from '../../lib/types/manifest';

interface Props {
  readonly paper: Paper;
}

const CORNER_LENGTH = 24;
const CORNER_THICKNESS = 3;
const GUIDE_COLOR = 'rgba(255, 255, 255, 0.8)';
const PADDING = 32;

export function CaptureGuideOverlay({ paper }: Props) {
  const aspectRatio = paper.widthMm / paper.heightMm;
  const isLandscape = paper.orientation === 'landscape';

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          position: 'relative',
          width: `calc(100% - ${PADDING * 2}px)`,
          maxWidth: '480px',
          aspectRatio: isLandscape ? `${aspectRatio}` : `${1 / aspectRatio}`,
          maxHeight: `calc(100% - ${PADDING * 2}px)`,
        }}
      >
        {/* 四隅マーカー */}
        <Corner position="top-left" />
        <Corner position="top-right" />
        <Corner position="bottom-left" />
        <Corner position="bottom-right" />
      </div>

      <p
        style={{
          color: 'white',
          fontSize: '14px',
          textAlign: 'center',
          marginTop: '12px',
          textShadow: '0 1px 4px rgba(0,0,0,0.8)',
          padding: '0 16px',
        }}
      >
        四隅のマークが枠内に入るように撮影してください
      </p>
    </div>
  );
}

type CornerPosition = 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';

function Corner({ position }: { readonly position: CornerPosition }) {
  const isTop = position.startsWith('top');
  const isLeft = position.endsWith('left');

  return (
    <div
      style={{
        position: 'absolute',
        top: isTop ? 0 : undefined,
        bottom: isTop ? undefined : 0,
        left: isLeft ? 0 : undefined,
        right: isLeft ? undefined : 0,
        width: `${CORNER_LENGTH}px`,
        height: `${CORNER_LENGTH}px`,
      }}
    >
      {/* 水平線 */}
      <div
        style={{
          position: 'absolute',
          top: isTop ? 0 : undefined,
          bottom: isTop ? undefined : 0,
          left: isLeft ? 0 : undefined,
          right: isLeft ? undefined : 0,
          width: `${CORNER_LENGTH}px`,
          height: `${CORNER_THICKNESS}px`,
          backgroundColor: GUIDE_COLOR,
        }}
      />
      {/* 垂直線 */}
      <div
        style={{
          position: 'absolute',
          top: isTop ? 0 : undefined,
          bottom: isTop ? undefined : 0,
          left: isLeft ? 0 : undefined,
          right: isLeft ? undefined : 0,
          width: `${CORNER_THICKNESS}px`,
          height: `${CORNER_LENGTH}px`,
          backgroundColor: GUIDE_COLOR,
        }}
      />
    </div>
  );
}
