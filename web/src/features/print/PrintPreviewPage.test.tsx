import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { ExtendedManifest } from '../../lib/types/manifest';
import { PrintPreviewPage } from './PrintPreviewPage';

describe('PrintPreviewPage', () => {
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

  it('renders print button', () => {
    render(<PrintPreviewPage manifest={manifest} boundHtml="<p>test</p>" />);
    expect(screen.getByText('印刷')).toBeDefined();
  });

  it('renders preview heading', () => {
    render(<PrintPreviewPage manifest={manifest} boundHtml="<p>test</p>" />);
    expect(screen.getByText('印刷プレビュー')).toBeDefined();
  });

  it('renders @page CSS rule with correct paper size', () => {
    const { container } = render(<PrintPreviewPage manifest={manifest} boundHtml="<p>test</p>" />);
    const styles = container.querySelectorAll('style');
    const styleContent = Array.from(styles)
      .map((s) => s.textContent)
      .join('');
    expect(styleContent).toContain('210mm 297mm');
  });
});
