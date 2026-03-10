/**
 * 印刷用HTML文字列を組み立てる純粋関数。
 *
 * boundHTML + トンボSVG + ページIDコード + 印刷用CSSを
 * 1つのHTML文書にまとめる。TomboOverlay / PageIdCode コンポーネントの
 * 描画ロジックを文字列生成として再実装している。
 */

import type { PageIdentifier, RegistrationMarks } from '../../lib/types/manifest';

interface BuildPrintHtmlParams {
  readonly boundHtml: string;
  readonly paper: { readonly widthMm: number; readonly heightMm: number };
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

export function buildPrintHtml({
  boundHtml,
  paper,
  registrationMarks,
  pageIdentifier,
}: BuildPrintHtmlParams): string {
  const tomboSvg = buildTomboSvg(registrationMarks, paper.widthMm, paper.heightMm);
  const pageIdHtml = buildPageIdHtml(pageIdentifier);

  const printStyle = `<style>
@page { size: ${paper.widthMm}mm ${paper.heightMm}mm; margin: 0; }
body { margin: 0; }
section.sheet[data-horizontal-centered="true"],
div.page[data-horizontal-centered="true"] {
  margin-left: auto;
  margin-right: auto;
}
section.sheet[data-vertical-centered="true"],
div.page[data-vertical-centered="true"] {
  margin-top: auto;
  margin-bottom: auto;
}
.print-container {
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

  // boundHtml の </body> 前にオーバーレイを挿入、なければ末尾に追加
  const overlays = `<div class="print-container" style="position:relative;width:${paper.widthMm}mm;height:${paper.heightMm}mm;">
${tomboSvg}
${pageIdHtml}
</div>`;

  if (htmlWithStyle.includes('</body>')) {
    return htmlWithStyle.replace('</body>', `${overlays}</body>`);
  }
  return htmlWithStyle + overlays;
}
