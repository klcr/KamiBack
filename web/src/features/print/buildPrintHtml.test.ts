import { describe, expect, it } from 'vitest';
import type { PageIdentifier, RegistrationMarks } from '../../lib/types/manifest';
import { buildPrintHtml } from './buildPrintHtml';

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

  const params = {
    boundHtml: '<div>Hello</div>',
    paper,
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
});
