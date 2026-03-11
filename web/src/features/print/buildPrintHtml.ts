/**
 * 印刷用HTML文字列を組み立てる純粋関数。
 *
 * boundHTML + トンボSVG + ページIDコード + 印刷用CSSを
 * 1つのHTML文書にまとめる。TomboOverlay / PageIdCode コンポーネントの
 * 描画ロジックを文字列生成として再実装している。
 */

import type {
  Centering,
  Margins,
  PageIdentifier,
  RegistrationMarks,
} from '../../lib/types/manifest';

interface BuildPrintHtmlParams {
  readonly boundHtml: string;
  readonly paper: { readonly widthMm: number; readonly heightMm: number };
  readonly margins: Margins;
  readonly centering: Centering;
  readonly registrationMarks: RegistrationMarks;
  readonly pageIdentifier: PageIdentifier;
}

function buildTomboSvg(marks: RegistrationMarks, widthMm: number, heightMm: number): string {
  const lineLen = marks.radiusMm * 2;
  const groups = marks.positions
    .map(
      (pos) => `<g>
      <circle cx="${pos.x}" cy="${pos.y}" r="${marks.radiusMm}" fill="none" stroke="black" stroke-width="0.3"/>
      <line x1="${pos.x - lineLen}" y1="${pos.y}" x2="${pos.x + lineLen}" y2="${pos.y}" stroke="black" stroke-width="0.3"/>
      <line x1="${pos.x}" y1="${pos.y - lineLen}" x2="${pos.x}" y2="${pos.y + lineLen}" stroke="black" stroke-width="0.3"/>
    </g>`,
    )
    .join('\n');

  return `<svg viewBox="0 0 ${widthMm} ${heightMm}" style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;" aria-label="トンボ">
${groups}
</svg>`;
}

function buildPageIdHtml(identifier: PageIdentifier): string {
  return `<div style="position:absolute;left:${identifier.position.x}mm;top:${identifier.position.y}mm;width:${identifier.sizeMm}mm;height:${identifier.sizeMm}mm;border:0.3mm solid black;display:flex;align-items:center;justify-content:center;font-size:1.5mm;font-family:monospace;overflow:hidden;" data-content="${identifier.content}">${identifier.content}</div>`;
}

/**
 * ページ中央揃え時のマージン均等化を計算する。
 *
 * Excel の「ページ中央」設定は、印刷可能領域の位置を用紙中央にシフトさせる。
 * 水平中央揃え: left と right を均等化 → (left + right) / 2
 * 垂直中央揃え: top と bottom を均等化 → (top + bottom) / 2
 * 印刷可能領域のサイズ（幅・高さ）は変化しない。
 */
export function equalizeMargins(margins: Margins, centering: Centering): Margins {
  const eqHorizontal = (margins.left + margins.right) / 2;
  const eqVertical = (margins.top + margins.bottom) / 2;
  return {
    top: centering.vertical ? eqVertical : margins.top,
    right: centering.horizontal ? eqHorizontal : margins.right,
    bottom: centering.vertical ? eqVertical : margins.bottom,
    left: centering.horizontal ? eqHorizontal : margins.left,
  };
}

export function buildPrintHtml({
  boundHtml,
  paper,
  margins,
  centering,
  registrationMarks,
  pageIdentifier,
}: BuildPrintHtmlParams): string {
  const tomboSvg = buildTomboSvg(registrationMarks, paper.widthMm, paper.heightMm);
  const pageIdHtml = buildPageIdHtml(pageIdentifier);

  const eq = equalizeMargins(margins, centering);

  const printStyle = `<style>
@page { size: ${paper.widthMm}mm ${paper.heightMm}mm; margin: 0; }
@page page0 { margin: ${eq.top}mm ${eq.right}mm ${eq.bottom}mm ${eq.left}mm; }
body { margin: 0; }
* { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
.print-page-wrapper {
  position: relative;
  width: ${paper.widthMm}mm;
  height: ${paper.heightMm}mm;
  overflow: hidden;
}
</style>`;

  // boundHtml に <head> がある場合はその中にスタイルを挿入
  let htmlWithStyle: string;
  if (boundHtml.includes('</head>')) {
    htmlWithStyle = boundHtml.replace('</head>', `${printStyle}</head>`);
  } else {
    htmlWithStyle = printStyle + boundHtml;
  }

  // トンボ・ページIDのオーバーレイ
  const overlays = `<div class="print-overlay" style="position:absolute;top:0;left:0;width:${paper.widthMm}mm;height:${paper.heightMm}mm;pointer-events:none;">
${tomboSvg}
${pageIdHtml}
</div>`;

  // body の中身全体を用紙サイズのラッパーで包み、オーバーレイを同一コンテキストに配置する。
  // ラッパーが position:relative の基準となり、overflow:hidden で1ページに収まる。
  const wrapperOpen = '<div class="print-page-wrapper">';
  const wrapperClose = `${overlays}</div>`;

  if (htmlWithStyle.includes('</body>')) {
    return htmlWithStyle
      .replace(/<body([^>]*)>/, `<body$1>${wrapperOpen}`)
      .replace('</body>', `${wrapperClose}</body>`);
  }
  return wrapperOpen + htmlWithStyle + wrapperClose;
}
