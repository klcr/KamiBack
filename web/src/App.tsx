/**
 * VG-1 テスト用アプリケーションシェル。
 *
 * ステップベースのルーティングでテンプレート→変数入力→印刷→撮影のフローを管理する。
 */

import { useState } from 'react';
import { type AppStep, StepIndicator } from './components/StepIndicator';
import { CaptureResultPage } from './features/capture/CaptureResultPage';
import { PrintPreviewPage } from './features/print/PrintPreviewPage';
import { TemplateUploadPage } from './features/template/TemplateUploadPage';
import { VariableEntryPage } from './features/template/VariableEntryPage';
import type { ExtendedManifest } from './lib/types/manifest';

interface AppState {
  step: AppStep;
  manifest: ExtendedManifest | null;
  originalHtml: string;
  boundHtml: string;
  testValues: Record<string, string>;
}

const INITIAL_STATE: AppState = {
  step: 'upload',
  manifest: null,
  originalHtml: '',
  boundHtml: '',
  testValues: {},
};

export function App() {
  const [state, setState] = useState<AppState>(INITIAL_STATE);

  const handleParsed = (manifest: ExtendedManifest, html: string) => {
    setState((prev) => ({ ...prev, step: 'bind', manifest, originalHtml: html }));
  };

  const handleBound = (boundHtml: string, testValues: Record<string, string>) => {
    setState((prev) => ({ ...prev, step: 'preview', boundHtml, testValues }));
  };

  const handleToCapture = () => {
    setState((prev) => ({ ...prev, step: 'capture' }));
  };

  const handleReset = () => {
    setState(INITIAL_STATE);
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '16px' }}>
      <h1 style={{ fontSize: '20px', marginBottom: '8px' }}>KamiBack VG-1 テスト</h1>
      <StepIndicator currentStep={state.step} />
      <hr style={{ margin: '8px 0 16px' }} />

      {state.step === 'upload' && <TemplateUploadPage onParsed={handleParsed} />}

      {state.step === 'bind' && state.manifest && (
        <VariableEntryPage
          manifest={state.manifest}
          html={state.originalHtml}
          onBound={handleBound}
        />
      )}

      {state.step === 'preview' && state.manifest && (
        <div>
          <PrintPreviewPage manifest={state.manifest} boundHtml={state.boundHtml} />
          <div style={{ textAlign: 'center', marginTop: '16px' }}>
            <button type="button" onClick={handleToCapture} style={{ padding: '8px 24px' }}>
              撮影へ進む
            </button>
          </div>
        </div>
      )}

      {state.step === 'capture' && state.manifest && (
        <CaptureResultPage manifest={state.manifest} testValues={state.testValues} />
      )}

      {state.step !== 'upload' && (
        <div style={{ marginTop: '24px', textAlign: 'center' }}>
          <button
            type="button"
            onClick={handleReset}
            style={{ padding: '4px 12px', fontSize: '12px', color: '#666' }}
          >
            最初からやり直す
          </button>
        </div>
      )}
    </div>
  );
}
