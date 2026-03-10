import { describe, expect, it } from 'vitest';
import type { Field, Manifest, Page, Paper } from './manifest';

describe('manifest types', () => {
  it('can construct a valid Manifest object', () => {
    const paper: Paper = {
      size: 'A4',
      orientation: 'portrait',
      widthMm: 210,
      heightMm: 297,
      margins: { top: 10, right: 10, bottom: 10, left: 10 },
      centering: { horizontal: false, vertical: false },
    };

    const field: Field = {
      variableId: 'f-001',
      variableName: 'company_name',
      variableType: 'string',
      inputType: 'printed',
      boxId: 'box-001',
      region: { x: 20, y: 30, width: 60, height: 10 },
      absoluteRegion: { x: 30, y: 40, width: 60, height: 10 },
    };

    const page: Page = {
      pageIndex: 0,
      paper,
      fields: [field],
    };

    const manifest: Manifest = {
      templateId: 'invoice-001',
      version: '1.0',
      pages: [page],
    };

    expect(manifest.templateId).toBe('invoice-001');
    expect(manifest.pages).toHaveLength(1);
    expect(manifest.pages[0].fields[0].variableName).toBe('company_name');
  });
});
