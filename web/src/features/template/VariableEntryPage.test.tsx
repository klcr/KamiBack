import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ExtendedManifest } from '../../lib/types/manifest';
import { VariableEntryPage } from './VariableEntryPage';

describe('VariableEntryPage', () => {
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

  it('renders heading and instructions', () => {
    render(<VariableEntryPage manifest={manifest} html="<p>test</p>" onBound={vi.fn()} />);
    expect(screen.getByText('変数入力')).toBeDefined();
  });

  it('renders preview button as disabled when fields are empty', () => {
    render(<VariableEntryPage manifest={manifest} html="<p>test</p>" onBound={vi.fn()} />);
    const button = screen.getByText('プレビューへ');
    expect(button).toBeDefined();
    expect((button as HTMLButtonElement).disabled).toBe(true);
  });
});
