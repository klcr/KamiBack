/**
 * テンプレートアップロードページ。
 *
 * HTML帳票テンプレートをアップロードし、拡張マニフェストを取得する。
 */

import { type ChangeEvent, useState } from 'react';
import { ApiError, extendTemplate } from '../../lib/apiClient';
import type { ExtendedManifest } from '../../lib/types/manifest';

interface Props {
  readonly onParsed: (manifest: ExtendedManifest, html: string) => void;
}

export function TemplateUploadPage({ onParsed }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<{
    manifest: ExtendedManifest;
    html: string;
  } | null>(null);

  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setPreview(null);

    try {
      const html = await file.text();
      const manifest = (await extendTemplate(file)) as ExtendedManifest;
      setPreview({ manifest, html });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('テンプレートの読み込みに失敗しました');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    if (preview) {
      onParsed(preview.manifest, preview.html);
    }
  };

  const page = preview?.manifest.pages[0];

  return (
    <div>
      <h2 style={{ fontSize: '16px', marginBottom: '12px' }}>テンプレートアップロード</h2>

      <label style={{ display: 'block', marginBottom: '12px' }}>
        HTML テンプレートファイル:
        <input
          type="file"
          accept=".html"
          onChange={handleFileChange}
          disabled={loading}
          style={{ display: 'block', marginTop: '4px' }}
        />
      </label>

      {loading && <p>読み込み中...</p>}

      {error && (
        <p role="alert" style={{ color: '#d32f2f', padding: '8px', background: '#fce4ec' }}>
          {error}
        </p>
      )}

      {preview && page && (
        <div style={{ marginTop: '12px' }}>
          <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>テンプレート情報</h3>
          <table style={{ borderCollapse: 'collapse', fontSize: '14px' }}>
            <tbody>
              <tr>
                <td style={{ padding: '4px 12px 4px 0', fontWeight: 'bold' }}>テンプレートID</td>
                <td>{preview.manifest.templateId}</td>
              </tr>
              <tr>
                <td style={{ padding: '4px 12px 4px 0', fontWeight: 'bold' }}>用紙サイズ</td>
                <td>
                  {page.paper.size} {page.paper.orientation}
                </td>
              </tr>
              <tr>
                <td style={{ padding: '4px 12px 4px 0', fontWeight: 'bold' }}>用紙寸法</td>
                <td>
                  {page.paper.widthMm}mm x {page.paper.heightMm}mm
                </td>
              </tr>
              <tr>
                <td style={{ padding: '4px 12px 4px 0', fontWeight: 'bold' }}>フィールド数</td>
                <td>{page.fields.length}</td>
              </tr>
              <tr>
                <td style={{ padding: '4px 12px 4px 0', fontWeight: 'bold' }}>トンボ</td>
                <td>{page.registrationMarks.positions.length} 点</td>
              </tr>
            </tbody>
          </table>

          <button
            type="button"
            onClick={handleNext}
            style={{ marginTop: '16px', padding: '8px 24px' }}
          >
            次へ（変数入力）
          </button>
        </div>
      )}
    </div>
  );
}
