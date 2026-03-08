/**
 * OCR結果の型定義（TypeScriptミラー）。
 *
 * Python domain/src/ocr_result/ocr_result_types.py と同期する。
 */

import type { VariableType } from './manifest';

// --- Enums ---

export type ReadingStatus = 'confirmed' | 'needs_review' | 'failed' | 'corrected';

// --- Value Objects ---

export interface Confidence {
  readonly score: number;
}

export interface FieldResult {
  readonly variableName: string;
  readonly variableType: VariableType;
  readonly value: string | number | boolean | null;
  readonly rawText: string;
  readonly confidence: Confidence;
  readonly status: ReadingStatus;
}

// --- OCR Result ---

export interface OcrResult {
  readonly templateId: string;
  readonly pageIndex: number;
  readonly fieldResults: readonly FieldResult[];
}

/** { variableName: value } のシンプルな出力形式。 */
export type SimpleResult = Record<string, string | number | boolean | null>;

/** 信頼度付きの詳細出力形式。 */
export interface DetailedFieldResult {
  readonly value: string | null;
  readonly confidence: number;
  readonly rawText: string;
  readonly status: ReadingStatus;
}

export type DetailedResult = Record<string, DetailedFieldResult>;
