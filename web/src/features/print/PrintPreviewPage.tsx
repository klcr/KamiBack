/**
 * 印刷プレビューページ。
 *
 * iframe内で帳票をレンダリングし、実際の印刷結果に近いプレビューを表示する。
 */

import { useRef } from 'react';
import type { ExtendedManifest } from '../../lib/types/manifest';
import { PageIdCode } from '../template/PageIdCode';
import { TomboOverlay } from '../template/TomboOverlay';

interface Props {
  readonly manifest: ExtendedManifest;
  readonly boundHtml: string;
}

export function PrintPreviewPage({ manifest, boundHtml }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const page = manifest.pages[0];
  const paper = page.paper;

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
          srcDoc={boundHtml}
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
        <button type="button" onClick={() => window.print()}>
          印刷
        </button>
      </div>
      <style>{`
        @media print {
          .print-actions { display: none; }
          .print-preview > h2 { display: none; }
          .preview-container { border: none !important; }
          @page {
            size: ${paper.widthMm}mm ${paper.heightMm}mm;
            margin: 0;
          }
        }
      `}</style>
    </div>
  );
}
