/**
 * トンボ（レジストレーションマーク）描画コンポーネント。
 *
 * SVGでトンボを描画し、帳票上に重ねて表示する。
 */

import type { RegistrationMarks } from '../../lib/types/manifest';

interface Props {
  readonly marks: RegistrationMarks;
  readonly paperWidthMm: number;
  readonly paperHeightMm: number;
}

export function TomboOverlay({ marks, paperWidthMm, paperHeightMm }: Props) {
  const lineLen = marks.radiusMm * 2;

  return (
    <svg
      className="tombo-overlay"
      viewBox={`0 0 ${paperWidthMm} ${paperHeightMm}`}
      role="img"
      aria-label="トンボ（レジストレーションマーク）"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
      }}
    >
      {marks.positions.map((pos) => (
        <g key={`tombo-${pos.x}-${pos.y}`}>
          <circle
            cx={pos.x}
            cy={pos.y}
            r={marks.radiusMm}
            fill="none"
            stroke="black"
            strokeWidth={0.3}
          />
          <line
            x1={pos.x - lineLen}
            y1={pos.y}
            x2={pos.x + lineLen}
            y2={pos.y}
            stroke="black"
            strokeWidth={0.3}
          />
          <line
            x1={pos.x}
            y1={pos.y - lineLen}
            x2={pos.x}
            y2={pos.y + lineLen}
            stroke="black"
            strokeWidth={0.3}
          />
        </g>
      ))}
    </svg>
  );
}
