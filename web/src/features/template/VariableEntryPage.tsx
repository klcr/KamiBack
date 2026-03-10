/**
 * 変数入力ページ。
 *
 * マニフェストのフィールドに値を入力し、HTMLにバインドする。
 */

import type { ExtendedManifest } from '../../lib/types/manifest';
import { VariableBindingView } from './VariableBindingView';
import { useVariableBinding } from './useVariableBinding';

interface Props {
  readonly manifest: ExtendedManifest;
  readonly html: string;
  readonly onBound: (boundHtml: string, testValues: Record<string, string>) => void;
}

export function VariableEntryPage({ manifest, html, onBound }: Props) {
  const fields = manifest.pages[0].fields;
  const binding = useVariableBinding(fields);

  const handleNext = () => {
    const boundHtml = binding.bindToHtml(html);
    const testValues: Record<string, string> = {};
    for (const b of binding.bindings) {
      testValues[b.variableName] = b.value;
    }
    onBound(boundHtml, testValues);
  };

  return (
    <div>
      <h2 style={{ fontSize: '16px', marginBottom: '12px' }}>変数入力</h2>
      <p style={{ fontSize: '14px', color: '#666', marginBottom: '12px' }}>
        テスト用の値を入力してください。印刷後に同じ値がOCRで読み取れるか検証します。
      </p>

      <VariableBindingView fields={fields} binding={binding} />

      <div style={{ marginTop: '16px' }}>
        <button
          type="button"
          onClick={handleNext}
          disabled={!binding.isComplete}
          style={{ padding: '8px 24px' }}
        >
          プレビューへ
        </button>
        {!binding.isComplete && (
          <span style={{ marginLeft: '8px', fontSize: '12px', color: '#999' }}>
            全フィールドに値を入力してください
          </span>
        )}
      </div>
    </div>
  );
}
