import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { Field } from '../../lib/types/manifest';
import { useVariableBinding } from './useVariableBinding';

const makeField = (name: string, type: Field['variableType'] = 'string'): Field => ({
  variableId: `v-${name}`,
  variableName: name,
  variableType: type,
  inputType: 'printed',
  boxId: `box-${name}`,
  region: { x: 0, y: 0, width: 10, height: 5 },
  absoluteRegion: { x: 0, y: 0, width: 10, height: 5 },
});

describe('useVariableBinding', () => {
  it('initializes with empty values', () => {
    const { result } = renderHook(() => useVariableBinding([makeField('name')]));
    expect(result.current.bindings).toHaveLength(1);
    expect(result.current.bindings[0].value).toBe('');
    expect(result.current.isComplete).toBe(true);
  });

  it('sets a value', () => {
    const { result } = renderHook(() => useVariableBinding([makeField('name')]));
    act(() => result.current.setValue('name', 'テスト株式会社'));
    expect(result.current.bindings[0].value).toBe('テスト株式会社');
    expect(result.current.isComplete).toBe(true);
  });

  it('formats number with locale', () => {
    const { result } = renderHook(() => useVariableBinding([makeField('amount', 'number')]));
    act(() => result.current.setValue('amount', '1234567'));
    expect(result.current.getFormattedValue('amount')).toBe('1,234,567');
  });

  it('formats date as YYYY-MM-DD', () => {
    const { result } = renderHook(() => useVariableBinding([makeField('date', 'date')]));
    act(() => result.current.setValue('date', '2026-03-08'));
    expect(result.current.getFormattedValue('date')).toBe('2026-03-08');
  });

  it('binds values into HTML template', () => {
    const fields = [makeField('name'), makeField('amount', 'number')];
    const { result } = renderHook(() => useVariableBinding(fields));
    act(() => {
      result.current.setValue('name', 'テスト');
      result.current.setValue('amount', '5000');
    });
    const html = '<div>{{name}}</div><div>{{amount}}</div>';
    const bound = result.current.bindToHtml(html);
    expect(bound).toBe('<div>テスト</div><div>5,000</div>');
  });

  it('isComplete is true when fields exist regardless of values', () => {
    const fields = [makeField('a'), makeField('b')];
    const { result } = renderHook(() => useVariableBinding(fields));
    act(() => result.current.setValue('a', 'value'));
    expect(result.current.isComplete).toBe(true);
  });

  it('bindToHtml uses variable name for empty values', () => {
    const fields = [makeField('companyName'), makeField('amount', 'number')];
    const { result } = renderHook(() => useVariableBinding(fields));
    act(() => result.current.setValue('amount', '5000'));
    const html = '<div>{{companyName}}</div><div>{{amount}}</div>';
    const bound = result.current.bindToHtml(html);
    expect(bound).toBe('<div>companyName</div><div>5,000</div>');
  });
});
