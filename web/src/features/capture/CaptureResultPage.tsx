/**
 * 撮影結果ページ。
 *
 * 撮影画像のアップロードとOCR結果の確認（Module B未実装のためプレースホルダー）。
 */

import { type ChangeEvent, useState } from 'react';
import type { ExtendedManifest } from '../../lib/types/manifest';
import type { CorrectionResult } from './captureApi';

interface Props {
  readonly manifest: ExtendedManifest;
  readonly testValues: Record<string, string>;
  readonly correctionResult?: CorrectionResult | null;
}

export function CaptureResultPage({ manifest, testValues, correctionResult }: Props) {
  const [images, setImages] = useState<{ name: string; url: string }[]>([]);
  const fields = manifest.pages[0].fields;

  const handleImageChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newImages: { name: string; url: string }[] = [];
    for (const file of files) {
      newImages.push({ name: file.name, url: URL.createObjectURL(file) });
    }
    setImages((prev) => [...prev, ...newImages]);
  };

  return (
    <div>
      <h2 style={{ fontSize: '16px', marginBottom: '12px' }}>撮影結果</h2>

      {correctionResult && (
        <div
          style={{
            padding: '12px',
            background: '#e8f5e9',
            border: '1px solid #a5d6a7',
            marginBottom: '16px',
            fontSize: '14px',
          }}
        >
          <strong>画像補正完了</strong>
          <ul style={{ margin: '8px 0 0', paddingLeft: '20px' }}>
            <li>トンボ検出: {correctionResult.tombo.detectionCount}点</li>
            <li>歪み角度: {correctionResult.tombo.skewDegree != null ? `${correctionResult.tombo.skewDegree.toFixed(1)}°` : '--'}</li>
            <li>アスペクト比誤差: {correctionResult.tombo.aspectRatioError != null ? `${correctionResult.tombo.aspectRatioError.toFixed(1)}%` : '--'}</li>
            {correctionResult.tombo.hasEstimation && (
              <li style={{ color: '#e65100' }}>※ 4点目は推定値です</li>
            )}
          </ul>
        </div>
      )}

      <div
        style={{
          padding: '12px',
          background: '#fff3e0',
          border: '1px solid #ffcc80',
          marginBottom: '16px',
          fontSize: '14px',
        }}
      >
        OCR機能（Module B 後半）は未実装です。画像補正結果の確認のみ行えます。
      </div>

      <section style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>画像アップロード</h3>
        <p style={{ fontSize: '13px', color: '#666', marginBottom: '8px' }}>
          印刷した帳票の写真をアップロードしてください（正対、やや斜め、照明ムラの3枚）
        </p>
        <input type="file" accept="image/*" multiple onChange={handleImageChange} />

        {images.length > 0 && (
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '12px' }}>
            {images.map((img) => (
              <div key={img.name} style={{ textAlign: 'center' }}>
                <img
                  src={img.url}
                  alt={img.name}
                  style={{
                    width: '160px',
                    height: '120px',
                    objectFit: 'cover',
                    border: '1px solid #ccc',
                  }}
                />
                <div style={{ fontSize: '11px', color: '#666', marginTop: '2px' }}>{img.name}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>入力値と読取結果の比較</h3>
        <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: '14px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #333' }}>
              <th style={{ textAlign: 'left', padding: '4px 8px' }}>変数名</th>
              <th style={{ textAlign: 'left', padding: '4px 8px' }}>入力値</th>
              <th style={{ textAlign: 'left', padding: '4px 8px' }}>OCR結果</th>
              <th style={{ textAlign: 'left', padding: '4px 8px' }}>ステータス</th>
            </tr>
          </thead>
          <tbody>
            {fields.map((field) => (
              <tr key={field.variableId} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '4px 8px' }}>{field.variableName}</td>
                <td style={{ padding: '4px 8px' }}>{testValues[field.variableName] ?? ''}</td>
                <td style={{ padding: '4px 8px', color: '#999' }}>--</td>
                <td style={{ padding: '4px 8px', color: '#999' }}>未実装</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
