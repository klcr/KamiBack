/**
 * 変数一覧表示 + 入力フォーム。
 */

import type { Field } from '../../lib/types/manifest';
import type { UseVariableBindingResult } from './useVariableBinding';

interface Props {
  readonly fields: readonly Field[];
  readonly binding: UseVariableBindingResult;
}

const TYPE_LABELS: Record<string, string> = {
  string: '文字列',
  number: '数値',
  date: '日付',
  boolean: 'チェック',
};

const INPUT_TYPE_MAP: Record<string, string> = {
  string: 'text',
  number: 'text',
  date: 'date',
  boolean: 'checkbox',
};

export function VariableBindingView({ fields, binding }: Props) {
  return (
    <div className="variable-binding">
      <h3>変数バインディング</h3>
      <table>
        <thead>
          <tr>
            <th>変数名</th>
            <th>型</th>
            <th>値</th>
            <th>フォーマット済み</th>
          </tr>
        </thead>
        <tbody>
          {fields.map((field) => (
            <tr key={field.variableId}>
              <td>{field.variableName}</td>
              <td>{TYPE_LABELS[field.variableType] ?? field.variableType}</td>
              <td>
                {field.variableType === 'boolean' ? (
                  <input
                    type="checkbox"
                    checked={
                      binding.bindings.find((b) => b.variableName === field.variableName)?.value ===
                      'true'
                    }
                    onChange={(e) => binding.setValue(field.variableName, String(e.target.checked))}
                  />
                ) : (
                  <input
                    type={INPUT_TYPE_MAP[field.variableType] ?? 'text'}
                    value={
                      binding.bindings.find((b) => b.variableName === field.variableName)?.value ??
                      ''
                    }
                    onChange={(e) => binding.setValue(field.variableName, e.target.value)}
                    placeholder={field.variableName}
                  />
                )}
              </td>
              <td>{binding.getFormattedValue(field.variableName)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
