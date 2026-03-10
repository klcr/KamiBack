/**
 * 印刷プレビューページ。
 *
 * iframe内で帳票をレンダリングし、実際の印刷結果に近いプレビューを表示する。
 */

import { useCallback, useMemo, useRef } from 'react';
import type { ExtendedManifest } from '../../lib/types/manifest';
import { PageIdCode } from '../template/PageIdCode';
import { TomboOverlay } from '../template/TomboOverlay';
import { buildPrintHtml } from './buildPrintHtml';
import { openPrintWindow } from './openPrintWindow';

interface Props {
  readonly manifest: ExtendedManifest;
  readonly boundHtml: string;
}

/**
 * iframe 内のシートに適用するベーススタイル。
 *
 * - body のデフォルト margin を除去し、用紙全体を正確に表現する
 * - data-horizontal-centered="true" / data-vertical-centered="true" 属性を
 *   CSS 属性セレクタで参照し、マニフェストJSONに依存せずDOM属性から直接センタリングを適用
 */
const IFRAME_BASE_STYLE = `<style>
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
</style>`;

export function PrintPreviewPage({ manifest, boundHtml }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const page = manifest.pages[0];
  const paper = page.paper;

  const handlePrint = useCallback(() => {
    const printHtml = buildPrintHtml({
      boundHtml,
      paper,
      registrationMarks: page.registrationMarks,
      pageIdentifier: page.pageIdentifier,
    });
    openPrintWindow(printHtml);
  }, [boundHtml, paper, page]);

  const htmlForIframe = useMemo(() => {
    // </head> の直前に挿入。<head> が無い場合は先頭に挿入
    if (boundHtml.includes('</head>')) {
      return boundHtml.replace('</head>', `${IFRAME_BASE_STYLE}</head>`);
    }
    return IFRAME_BASE_STYLE + boundHtml;
  }, [boundHtml]);

  return (
    <div className="print-preview">
      <h2>印刷プレビュー</h2>
      <div
        className="preview-container"
        style={{
          position: 'relative',
          width: `${paper.widthMm}mm`,
          height: `${paper.heightMm}mm`,
          border: '1px solid #ccc',
          overflow: 'hidden',
          margin: '0 auto',
        }}
      >
        <iframe
          ref={iframeRef}
          srcDoc={htmlForIframe}
          title="Print Preview"
          style={{ width: '100%', height: '100%', border: 'none' }}
        />
        <TomboOverlay
          marks={page.registrationMarks}
          paperWidthMm={paper.widthMm}
          paperHeightMm={paper.heightMm}
        />
        <PageIdCode identifier={page.pageIdentifier} />
      </div>
      <div className="print-actions" style={{ textAlign: 'center', marginTop: '16px' }}>
        <button type="button" onClick={handlePrint}>
          印刷
        </button>
      </div>
    </div>
  );
}
