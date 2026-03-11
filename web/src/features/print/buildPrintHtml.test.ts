import { describe, expect, it } from 'vitest';
import type { PageIdentifier, RegistrationMarks } from '../../lib/types/manifest';
import { buildPrintHtml, equalizeMargins } from './buildPrintHtml';

describe('equalizeMargins', () => {
  it('equalizes horizontal margins when horizontal centering is enabled', () => {
    const result = equalizeMargins(
      { top: 25.4, right: 19.1, bottom: 25.4, left: 12.7 },
      { horizontal: true, vertical: false },
    );
    expect(result.left).toBeCloseTo(15.9);
    expect(result.right).toBeCloseTo(15.9);
    expect(result.top).toBe(25.4);
    expect(result.bottom).toBe(25.4);
  });

  it('equalizes vertical margins when vertical centering is enabled', () => {
    const result = equalizeMargins(
      { top: 30, right: 19.1, bottom: 20, left: 19.1 },
      { horizontal: false, vertical: true },
    );
    expect(result.top).toBe(25);
    expect(result.bottom).toBe(25);
    expect(result.left).toBe(19.1);
    expect(result.right).toBe(19.1);
  });

  it('equalizes both when both centering flags are enabled', () => {
    const result = equalizeMargins(
      { top: 30, right: 10, bottom: 20, left: 20 },
      { horizontal: true, vertical: true },
    );
    expect(result.top).toBe(25);
    expect(result.bottom).toBe(25);
    expect(result.left).toBe(15);
    expect(result.right).toBe(15);
  });

  it('returns original margins when centering is disabled', () => {
    const margins = { top: 25.4, right: 19.1, bottom: 25.4, left: 12.7 };
    const result = equalizeMargins(margins, { horizontal: false, vertical: false });
    expect(result).toEqual(margins);
  });
});

describe('buildPrintHtml', () => {
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

  const identifier: PageIdentifier = {
    type: 'qr',
    content: 'test-001/0',
    position: { x: 197, y: 284 },
    sizeMm: 8,
  };

  const paper = { widthMm: 210, heightMm: 297 };
  const margins = { top: 25.4, right: 19.1, bottom: 25.4, left: 19.1 };
  const centering = { horizontal: false, vertical: false };

  const params = {
    boundHtml: '<div>Hello</div>',
    paper,
    margins,
    centering,
    registrationMarks: marks,
    pageIdentifier: identifier,
  };

  it('contains @page rule with correct paper size', () => {
    const html = buildPrintHtml(params);
    expect(html).toContain('210mm 297mm');
    expect(html).toContain('@page');
    expect(html).toContain('margin: 0');
  });

  it('contains tombo SVG markup', () => {
    const html = buildPrintHtml(params);
    expect(html).toContain('<svg');
    expect(html).toContain('<circle');
    expect(html).toContain('cx="5"');
    expect(html).toContain('cy="5"');
    expect(html).toContain('r="3"');
  });

  it('contains page identifier content', () => {
    const html = buildPrintHtml(params);
    expect(html).toContain('test-001/0');
    expect(html).toContain('data-content="test-001/0"');
  });

  it('embeds boundHtml in output', () => {
    const html = buildPrintHtml(params);
    expect(html).toContain('<div>Hello</div>');
  });

  it('injects style into existing <head> tag', () => {
    const htmlWithHead = '<html><head><title>Test</title></head><body><p>Content</p></body></html>';
    const html = buildPrintHtml({ ...params, boundHtml: htmlWithHead });
    expect(html).toContain('@page');
    expect(html).toContain('<title>Test</title>');
  });

  it('contains named @page rule with original margins when not centered', () => {
    const html = buildPrintHtml(params);
    expect(html).toContain('@page page0 { margin: 25.4mm 19.1mm 25.4mm 19.1mm; }');
  });

  it('contains named @page rule with equalized margins when horizontally centered', () => {
    const html = buildPrintHtml({
      ...params,
      margins: { top: 25.4, right: 10, bottom: 25.4, left: 20 },
      centering: { horizontal: true, vertical: false },
    });
    expect(html).toContain('@page page0 { margin: 25.4mm 15mm 25.4mm 15mm; }');
  });

  it('contains named @page rule with equalized margins when vertically centered', () => {
    const html = buildPrintHtml({
      ...params,
      margins: { top: 30, right: 19.1, bottom: 20, left: 19.1 },
      centering: { horizontal: false, vertical: true },
    });
    expect(html).toContain('@page page0 { margin: 25mm 19.1mm 25mm 19.1mm; }');
  });

  it('does not contain margin-left: auto CSS (removed broken approach)', () => {
    const html = buildPrintHtml({
      ...params,
      centering: { horizontal: true, vertical: true },
    });
    expect(html).not.toContain('margin-left: auto');
    expect(html).not.toContain('margin-top: auto');
  });
});
