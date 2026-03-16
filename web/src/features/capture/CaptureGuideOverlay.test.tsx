import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { Paper } from '../../lib/types/manifest';
import { CaptureGuideOverlay } from './CaptureGuideOverlay';

describe('CaptureGuideOverlay', () => {
  const paper: Paper = {
    size: 'A4',
    orientation: 'portrait',
    widthMm: 210,
    heightMm: 297,
    margins: { top: 10, right: 10, bottom: 10, left: 10 },
    centering: { horizontal: false, vertical: false },
  };

  it('renders guide text', () => {
    render(<CaptureGuideOverlay paper={paper} />);
    expect(screen.getByText('四隅のマークが枠内に入るように撮影してください')).toBeDefined();
  });

  it('renders corner markers', () => {
    const { container } = render(<CaptureGuideOverlay paper={paper} />);
    // Each corner has a wrapper with 2 lines (horizontal + vertical)
    // Look for elements with absolute positioning (corner wrappers + lines)
    const absoluteElements = container.querySelectorAll('div[style*="position: absolute"]');
    // At least 4 corner wrappers should exist
    expect(absoluteElements.length).toBeGreaterThanOrEqual(4);
  });

  it('renders with landscape paper without error', () => {
    const landscapePaper: Paper = { ...paper, orientation: 'landscape' };
    const { container } = render(<CaptureGuideOverlay paper={landscapePaper} />);
    expect(container.firstChild).toBeDefined();
  });
});
