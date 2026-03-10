/**
 * マニフェストJSONの型定義（TypeScriptミラー）。
 *
 * Python domain/src/manifest/manifest_types.py と同期する。
 * マニフェストJSONがPython↔TypeScript間の型同期手段となる。
 */

// --- Enums ---

export type PaperSize = 'A3' | 'A4' | 'A5';

export type Orientation = 'portrait' | 'landscape';

export type InputType = 'printed' | 'handwritten_number' | 'handwritten_kana' | 'checkbox';

export type VariableType = 'string' | 'number' | 'date' | 'boolean';

export type TomboShape = 'circle_cross';

// --- Value Objects ---

export interface Point {
  readonly x: number;
  readonly y: number;
}

export interface Region {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
}

export interface Margins {
  readonly top: number;
  readonly right: number;
  readonly bottom: number;
  readonly left: number;
}

export interface Centering {
  readonly horizontal: boolean;
  readonly vertical: boolean;
}

export interface HeaderFooterSections {
  readonly left: string;
  readonly center: string;
  readonly right: string;
}

export interface HeaderFooterEntry {
  readonly raw: string;
  readonly sections: HeaderFooterSections;
}

export interface HeaderFooter {
  readonly oddHeader?: HeaderFooterEntry;
  readonly oddFooter?: HeaderFooterEntry;
  readonly evenHeader?: HeaderFooterEntry;
  readonly evenFooter?: HeaderFooterEntry;
  readonly firstHeader?: HeaderFooterEntry;
  readonly firstFooter?: HeaderFooterEntry;
}

// --- Manifest Structures ---

export interface Paper {
  readonly size: PaperSize;
  readonly orientation: Orientation;
  readonly widthMm: number;
  readonly heightMm: number;
  readonly margins: Margins;
  readonly centering: Centering;
}

export interface Field {
  readonly variableId: string;
  readonly variableName: string;
  readonly variableType: VariableType;
  readonly inputType: InputType;
  readonly boxId: string;
  readonly region: Region;
  readonly absoluteRegion: Region;
}

export interface RegistrationMarks {
  readonly shape: TomboShape;
  readonly radiusMm: number;
  readonly positions: readonly Point[];
}

export interface PageIdentifier {
  readonly type: string;
  readonly content: string;
  readonly position: Point;
  readonly sizeMm: number;
}

export interface Page {
  readonly pageIndex: number;
  readonly paper: Paper;
  readonly fields: readonly Field[];
  readonly registrationMarks?: RegistrationMarks;
  readonly pageIdentifier?: PageIdentifier;
  readonly headerFooter?: HeaderFooter;
}

export interface Manifest {
  readonly templateId: string;
  readonly version: string;
  readonly pages: readonly Page[];
  readonly interface?: string;
}

/**
 * 拡張マニフェスト（トンボ・ページ識別コード追記済み）。
 * 全ページにregistrationMarksとpageIdentifierが含まれる。
 */
export interface ExtendedManifest extends Manifest {
  readonly pages: readonly (Page & Required<Pick<Page, 'registrationMarks' | 'pageIdentifier'>>)[];
}
