/**
 * 撮影結果ページ。
 *
 * 画像補正結果の表示 + OCR実行 + 結果の確認。
 */

import { type ChangeEvent, useState } from 'react';
import type { ExtendedManifest, Field } from '../../lib/types/manifest';
import {
  CaptureApiError,
  type CorrectionResult,
  type FieldResultDto,
  type OcrResult,
  executeOcr,
} from './captureApi';

interface Props {
  readonly manifest: ExtendedManifest;
  readonly testValues: Record<string, string>;
  readonly correctionResult?: CorrectionResult | null;
}

export function CaptureResultPage({ manifest, testValues, correctionResult }: Props) {
  const [images, setImages] = useState<{ name: string; url: string }[]>([]);
  const [ocrResult, setOcrResult] = useState<OcrResult | null>(null);
  const [ocrStatus, setOcrStatus] = useState<'idle' | 'running' | 'done' | 'error'>('idle');
  const [ocrError, setOcrError] = useState<string | null>(null);
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

  const handleExecuteOcr = async () => {
    if (!correctionResult) return;

    setOcrStatus('running');
    setOcrError(null);

    try {
      const result = await executeOcr({
        imageId: correctionResult.imageId,
        templateId: correctionResult.templateId,
        pageIndex: correctionResult.pageIndex,
        scalePxPerMm: correctionResult.scalePxPerMm,
      });
      setOcrResult(result);
      setOcrStatus('done');
    } catch (err) {
      if (err instanceof CaptureApiError) {
        setOcrError(err.userAction);
      } else {
        setOcrError('OCRの実行に失敗しました。通信環境を確認してください。');
      }
      setOcrStatus('error');
    }
  };

  const findFieldResult = (variableName: string): FieldResultDto | undefined => {
    return ocrResult?.fieldResults.find((fr) => fr.variableName === variableName);
  };

  const statusLabel = (status: string): string => {
    switch (status) {
      case 'confirmed':
        return 'OK';
      case 'needs_review':
        return '要確認';
      case 'failed':
        return '失敗';
      case 'corrected':
        return '修正済';
      default:
        return status;
    }
  };

  const statusColor = (status: string): string => {
    switch (status) {
      case 'confirmed':
        return '#2e7d32';
      case 'needs_review':
        return '#e65100';
      case 'failed':
        return '#c62828';
      case 'corrected':
        return '#1565c0';
      default:
        return '#666';
    }
  };

  const rowBackground = (fr: FieldResultDto | undefined, inputVal: string): string => {
    if (!fr) return 'transparent';
    if (inputVal === fr.rawText) return '#e8f5e9';
    if (fr.status === 'failed') return '#fce4ec';
    return '#fff3e0';
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
            <li>
              歪み角度:{' '}
              {correctionResult.tombo.skewDegree != null
                ? `${correctionResult.tombo.skewDegree.toFixed(1)}°`
                : '--'}
            </li>
            <li>
              アスペクト比誤差:{' '}
              {correctionResult.tombo.aspectRatioError != null
                ? `${correctionResult.tombo.aspectRatioError.toFixed(1)}%`
                : '--'}
            </li>
            <li>スケール: {correctionResult.scalePxPerMm.toFixed(2)} px/mm</li>
            {correctionResult.tombo.hasEstimation && (
              <li style={{ color: '#e65100' }}>※ 4点目は推定値です</li>
            )}
          </ul>
        </div>
      )}

      {/* OCR実行ボタン */}
      {correctionResult && ocrStatus !== 'done' && (
        <div style={{ marginBottom: '16px' }}>
          <button
            type="button"
            onClick={handleExecuteOcr}
            disabled={ocrStatus === 'running'}
            style={{
              padding: '10px 24px',
              background: ocrStatus === 'running' ? '#ccc' : '#1a73e8',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '14px',
              cursor: ocrStatus === 'running' ? 'not-allowed' : 'pointer',
            }}
          >
            {ocrStatus === 'running' ? 'OCR実行中...' : 'OCRを実行'}
          </button>
        </div>
      )}

      {ocrError && (
        <div
          style={{
            padding: '12px',
            background: '#fce4ec',
            border: '1px solid #ef9a9a',
            marginBottom: '16px',
            fontSize: '14px',
          }}
        >
          {ocrError}
        </div>
      )}

      {!correctionResult && (
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
                  <div style={{ fontSize: '11px', color: '#666', marginTop: '2px' }}>
                    {img.name}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      <section>
        <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>入力値と読取結果の比較</h3>
        <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: '14px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #333' }}>
              <th style={{ textAlign: 'left', padding: '4px 8px' }}>変数名</th>
              <th style={{ textAlign: 'left', padding: '4px 8px' }}>入力値</th>
              <th style={{ textAlign: 'left', padding: '4px 8px' }}>OCR結果</th>
              <th style={{ textAlign: 'right', padding: '4px 8px' }}>信頼度</th>
              <th style={{ textAlign: 'left', padding: '4px 8px' }}>ステータス</th>
            </tr>
          </thead>
          <tbody>
            {fields.map((field) => (
              <FieldRow
                key={field.variableId}
                field={field}
                inputVal={testValues[field.variableName] ?? ''}
                fr={findFieldResult(field.variableName)}
                rowBackground={rowBackground}
                statusLabel={statusLabel}
                statusColor={statusColor}
              />
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function FieldRow({
  field,
  inputVal,
  fr,
  rowBackground,
  statusLabel,
  statusColor,
}: {
  readonly field: Field;
  readonly inputVal: string;
  readonly fr: FieldResultDto | undefined;
  readonly rowBackground: (fr: FieldResultDto | undefined, inputVal: string) => string;
  readonly statusLabel: (status: string) => string;
  readonly statusColor: (status: string) => string;
}) {
  const ocrVal = fr?.rawText ?? '--';

  return (
    <tr
      style={{
        borderBottom: '1px solid #eee',
        background: rowBackground(fr, inputVal),
      }}
    >
      <td style={{ padding: '4px 8px' }}>{field.variableName}</td>
      <td style={{ padding: '4px 8px' }}>{inputVal}</td>
      <td style={{ padding: '4px 8px', fontWeight: fr ? 'bold' : 'normal' }}>{ocrVal}</td>
      <td style={{ padding: '4px 8px', textAlign: 'right' }}>
        {fr ? `${(fr.confidence * 100).toFixed(0)}%` : '--'}
      </td>
      <td
        style={{
          padding: '4px 8px',
          color: fr ? statusColor(fr.status) : '#999',
          fontWeight: fr ? 'bold' : 'normal',
        }}
      >
        {fr ? statusLabel(fr.status) : '未実行'}
      </td>
    </tr>
  );
}
