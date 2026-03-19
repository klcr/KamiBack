import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ExtendedManifest } from '../../lib/types/manifest';
import { QrFallbackSelector } from './QrFallbackSelector';

describe('QrFallbackSelector', () => {
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

  it('renders error message', () => {
    render(
      <QrFallbackSelector
        manifest={manifest}
        errorMessage="QRコードが検出できませんでした"
        onConfirm={vi.fn()}
        onRetry={vi.fn()}
      />,
    );
    expect(screen.getByText('QRコードが検出できませんでした')).toBeDefined();
  });

  it('displays template ID', () => {
    render(
      <QrFallbackSelector
        manifest={manifest}
        errorMessage="error"
        onConfirm={vi.fn()}
        onRetry={vi.fn()}
      />,
    );
    expect(screen.getByText('test-001')).toBeDefined();
  });

  it('calls onConfirm with templateId and pageIndex', () => {
    const onConfirm = vi.fn();
    render(
      <QrFallbackSelector
        manifest={manifest}
        errorMessage="error"
        onConfirm={onConfirm}
        onRetry={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByText('このテンプレートで続行'));
    expect(onConfirm).toHaveBeenCalledWith('test-001', 0);
  });

  it('calls onRetry when retry button clicked', () => {
    const onRetry = vi.fn();
    render(
      <QrFallbackSelector
        manifest={manifest}
        errorMessage="error"
        onConfirm={vi.fn()}
        onRetry={onRetry}
      />,
    );

    fireEvent.click(screen.getByText('撮り直す'));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it('does not show page selector for single-page manifest', () => {
    const { container } = render(
      <QrFallbackSelector
        manifest={manifest}
        errorMessage="error"
        onConfirm={vi.fn()}
        onRetry={vi.fn()}
      />,
    );
    expect(container.querySelector('select')).toBeNull();
  });

  it('shows page selector for multi-page manifest', () => {
    const multiPageManifest: ExtendedManifest = {
      ...manifest,
      pages: [
        manifest.pages[0],
        {
          ...manifest.pages[0],
          pageIndex: 1,
          pageIdentifier: { ...manifest.pages[0].pageIdentifier, content: 'test-001/1' },
        },
      ],
    };

    render(
      <QrFallbackSelector
        manifest={multiPageManifest}
        errorMessage="error"
        onConfirm={vi.fn()}
        onRetry={vi.fn()}
      />,
    );
    expect(screen.getByLabelText(/ページ/)).toBeDefined();
  });
});
