import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { RegistrationMarks } from '../../lib/types/manifest';
import { TomboOverlay } from './TomboOverlay';

describe('TomboOverlay', () => {
  const marks: RegistrationMarks = {
    shape: 'circle_cross',
    radiusMm: 3,
    positions: [
      { x: 5, y: 5 },
      { x: 205, y: 5 },
      { x: 5, y: 292 },
      { x: 205, y: 292 },
    ],
  };

  it('renders 4 registration mark groups', () => {
    const { container } = render(
      <TomboOverlay marks={marks} paperWidthMm={210} paperHeightMm={297} />,
    );
    const circles = container.querySelectorAll('circle');
    expect(circles).toHaveLength(4);
  });

  it('renders cross lines for each mark', () => {
    const { container } = render(
      <TomboOverlay marks={marks} paperWidthMm={210} paperHeightMm={297} />,
    );
    const lines = container.querySelectorAll('line');
    expect(lines).toHaveLength(8); // 2 lines per mark × 4 marks
  });

  it('sets correct viewBox', () => {
    const { container } = render(
      <TomboOverlay marks={marks} paperWidthMm={210} paperHeightMm={297} />,
    );
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('viewBox')).toBe('0 0 210 297');
  });
});
