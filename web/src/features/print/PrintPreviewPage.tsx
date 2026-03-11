/**
 * 印刷プレビューページ。
 *
 * iframe内で帳票をレンダリングし、実際の印刷結果に近いプレビューを表示する。
 */

import { useCallback, useMemo, useRef } from 'react';
import type { ExtendedManifest } from '../../lib/types/manifest';
import { PageIdCode } from '../template/PageIdCode';
import { TomboOverlay } from '../template/TomboOverlay';
import { buildPrintHtml, equalizeMargins } from './buildPrintHtml';
import { openPrintWindow } from './openPrintWindow';

interface Props {
  readonly manifest: ExtendedManifest;
  readonly boundHtml: string;
}

export function PrintPreviewPage({ manifest, boundHtml }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const page = manifest.pages[0];
  const paper = page.paper;

  const eq = useMemo(
    () => equalizeMargins(paper.margins, paper.centering),
    [paper.margins, paper.centering],
  );

  const handlePrint = useCallback(() => {
    const printHtml = buildPrintHtml({
      boundHtml,
      paper,
      margins: paper.margins,
      centering: paper.centering,
      registrationMarks: page.registrationMarks,
      pageIdentifier: page.pageIdentifier,
    });
    openPrintWindow(printHtml);
  }, [boundHtml, paper, page]);

  const htmlForIframe = useMemo(() => {
    // iframe ではシートを均等化マージン位置に配置する
    const iframeStyle = `<style>
body { margin: 0; }
section.sheet[data-page-index="0"],
div.page[data-page-index="0"] {
  margin-left: ${eq.left}mm;
  margin-top: ${eq.top}mm;
}
</style>`;
    if (boundHtml.includes('</head>')) {
      return boundHtml.replace('</head>', `${iframeStyle}</head>`);
    }
    return iframeStyle + boundHtml;
  }, [boundHtml, eq]);

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
