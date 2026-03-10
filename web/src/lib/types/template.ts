/**
 * テンプレートの型定義（TypeScriptミラー）。
 *
 * Python domain/src/template/template_types.py と同期する。
 */

import type { HorizontalAlignment, Region, VerticalAlignment } from './manifest';

// --- Enums ---

export type BoxRole = 'field' | 'label' | 'decoration';

// --- Template Structures ---

export interface Box {
  readonly boxId: string;
  readonly role: BoxRole;
  readonly regionMm: Region;
  readonly textContent?: string;
  readonly variableName?: string;
  readonly dataType?: string;
  readonly horizontalAlignment?: HorizontalAlignment;
  readonly verticalAlignment?: VerticalAlignment;
}

export interface Line {
  readonly lineId: string;
  readonly x1Mm: number;
  readonly y1Mm: number;
  readonly x2Mm: number;
  readonly y2Mm: number;
}

export interface PageTemplate {
  readonly pageIndex: number;
  readonly boxes: readonly Box[];
  readonly lines: readonly Line[];
}

export interface TemplateMetadata {
  readonly sourceHtml: string;
  readonly pageCount: number;
  readonly pages: readonly PageTemplate[];
}
