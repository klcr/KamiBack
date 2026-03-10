/**
 * 変数バインディングのステート管理フック。
 *
 * マニフェストのフィールド定義に基づき、変数名→値のバインディングを管理する。
 */

import { useCallback, useMemo, useState } from 'react';
import type { Field, VariableType } from '../../lib/types/manifest';

export interface VariableBinding {
  readonly variableName: string;
  readonly variableType: VariableType;
  readonly value: string;
}

export interface UseVariableBindingResult {
  readonly bindings: readonly VariableBinding[];
  readonly setValue: (variableName: string, value: string) => void;
  readonly getFormattedValue: (variableName: string) => string;
  readonly bindToHtml: (html: string) => string;
  readonly isComplete: boolean;
}

function formatValue(value: string, variableType: VariableType): string {
  if (!value) return '';

  switch (variableType) {
    case 'date': {
      const d = new Date(value);
      if (Number.isNaN(d.getTime())) return value;
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    }
    case 'number': {
      const n = Number(value.replace(/,/g, ''));
      if (Number.isNaN(n)) return value;
      return n.toLocaleString('ja-JP');
    }
    default:
      return value;
  }
}

export function useVariableBinding(fields: readonly Field[]): UseVariableBindingResult {
  const [values, setValues] = useState<Record<string, string>>({});

  const bindings = useMemo(
    () =>
      fields.map((f) => ({
        variableName: f.variableName,
        variableType: f.variableType,
        value: values[f.variableName] ?? '',
      })),
    [fields, values],
  );

  const setValue = useCallback((variableName: string, value: string) => {
    setValues((prev) => ({ ...prev, [variableName]: value }));
  }, []);

  const getFormattedValue = useCallback(
    (variableName: string) => {
      const field = fields.find((f) => f.variableName === variableName);
      if (!field) return '';
      return formatValue(values[variableName] ?? '', field.variableType);
    },
    [fields, values],
  );

  const bindToHtml = useCallback(
    (html: string) => {
      let result = html;
      for (const field of fields) {
        const raw = values[field.variableName] ?? '';
        const formatted = raw ? formatValue(raw, field.variableType) : field.variableName;
        result = result.replace(new RegExp(`\\{\\{${field.variableName}\\}\\}`, 'g'), formatted);
      }
      return result;
    },
    [fields, values],
  );

  const isComplete = useMemo(() => fields.length > 0, [fields]);

  return { bindings, setValue, getFormattedValue, bindToHtml, isComplete };
}
