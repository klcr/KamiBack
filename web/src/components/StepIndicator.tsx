/**
 * ステップインジケーター。現在のステップをハイライト表示するパンくず。
 */

export type AppStep = 'upload' | 'bind' | 'preview' | 'capture';

const STEPS: readonly { readonly key: AppStep; readonly label: string }[] = [
  { key: 'upload', label: '1. テンプレート' },
  { key: 'bind', label: '2. 変数入力' },
  { key: 'preview', label: '3. 印刷プレビュー' },
  { key: 'capture', label: '4. 撮影・結果' },
];

interface Props {
  readonly currentStep: AppStep;
}

export function StepIndicator({ currentStep }: Props) {
  const currentIndex = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <nav style={{ display: 'flex', gap: '8px', padding: '12px 0', fontSize: '14px' }}>
      {STEPS.map((step, i) => {
        const isCurrent = step.key === currentStep;
        const isPast = i < currentIndex;
        return (
          <span key={step.key} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {i > 0 && <span style={{ color: '#ccc' }}>&rarr;</span>}
            <span
              style={{
                fontWeight: isCurrent ? 'bold' : 'normal',
                color: isCurrent ? '#1a73e8' : isPast ? '#333' : '#999',
              }}
            >
              {step.label}
            </span>
          </span>
        );
      })}
    </nav>
  );
}
