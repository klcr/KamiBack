/**
 * QR検出失敗時の手動テンプレート選択。
 *
 * VG-1テストフローではマニフェストが既知のため、確認UIとして機能する。
 */

import { useState } from 'react';
import type { ExtendedManifest } from '../../lib/types/manifest';

interface Props {
  readonly manifest: ExtendedManifest;
  readonly errorMessage: string;
  readonly onConfirm: (templateId: string, pageIndex: number) => void;
  readonly onRetry: () => void;
}

export function QrFallbackSelector({ manifest, errorMessage, onConfirm, onRetry }: Props) {
  const [selectedPage, setSelectedPage] = useState(0);

  const handleConfirm = () => {
    onConfirm(manifest.templateId, selectedPage);
  };

  return (
    <div
      style={{
        padding: '16px',
        background: '#fff3e0',
        border: '1px solid #ffcc80',
        borderRadius: '4px',
      }}
    >
      <p style={{ fontSize: '14px', marginBottom: '12px', color: '#e65100' }}>{errorMessage}</p>

      <p style={{ fontSize: '14px', marginBottom: '12px' }}>
        このテンプレートの画像として処理しますか？
      </p>

      <div style={{ marginBottom: '12px' }}>
        <span style={{ fontSize: '13px', color: '#666' }}>テンプレート: </span>
        <strong style={{ fontSize: '14px' }}>{manifest.templateId}</strong>
      </div>

      {manifest.pages.length > 1 && (
        <div style={{ marginBottom: '12px' }}>
          <label htmlFor="page-select" style={{ fontSize: '13px', color: '#666' }}>
            ページ:{' '}
          </label>
          <select
            id="page-select"
            value={selectedPage}
            onChange={(e) => setSelectedPage(Number(e.target.value))}
            style={{ fontSize: '14px', padding: '4px' }}
          >
            {manifest.pages.map((page) => (
              <option key={page.pageIndex} value={page.pageIndex}>
                ページ {page.pageIndex + 1}
              </option>
            ))}
          </select>
        </div>
      )}

      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          type="button"
          onClick={handleConfirm}
          style={{
            padding: '8px 16px',
            fontSize: '14px',
            background: '#1a73e8',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          このテンプレートで続行
        </button>
        <button
          type="button"
          onClick={onRetry}
          style={{
            padding: '8px 16px',
            fontSize: '14px',
            background: 'white',
            border: '1px solid #ccc',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          撮り直す
        </button>
      </div>
    </div>
  );
}
