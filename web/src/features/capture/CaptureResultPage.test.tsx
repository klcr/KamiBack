import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { ExtendedManifest } from '../../lib/types/manifest';
import { CaptureResultPage } from './CaptureResultPage';

describe('CaptureResultPage', () => {
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
        fields: [
          {
            variableId: 'v1',
            variableName: 'name',
            variableType: 'string',
            inputType: 'printed',
            boxId: 'b1',
            region: { x: 10, y: 10, width: 50, height: 10 },
            absoluteRegion: { x: 20, y: 20, width: 50, height: 10 },
          },
        ],
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

  it('renders Module B not-implemented banner', () => {
    render(<CaptureResultPage manifest={manifest} testValues={{ name: 'test' }} />);
    expect(screen.getByText(/復路（Module B）は未実装です/)).toBeDefined();
  });

  it('renders comparison table with test values', () => {
    render(<CaptureResultPage manifest={manifest} testValues={{ name: 'test-value' }} />);
    expect(screen.getByText('name')).toBeDefined();
    expect(screen.getByText('test-value')).toBeDefined();
  });

  it('renders image upload input', () => {
    const { container } = render(
      <CaptureResultPage manifest={manifest} testValues={{ name: 'test' }} />,
    );
    const input = container.querySelector('input[type="file"]');
    expect(input).toBeDefined();
    expect(input?.getAttribute('accept')).toBe('image/*');
  });
});
