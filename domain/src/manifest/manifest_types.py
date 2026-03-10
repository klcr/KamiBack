"""マニフェストJSONの型定義。

マニフェストはこのシステムの「唯一の真実」。座標・変数・型の情報源は
マニフェストJSONただ1つ。HTMLのDOM属性やCSS座標は、すべてマニフェストに
書かれたmm座標から導出されるか、マニフェストと照合される。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from domain.src.shared.coordinate import Point, Region


class PaperSize(Enum):
    """用紙サイズ（A版のみ。B版は現在スコープ外）。"""

    A3 = "A3"
    A4 = "A4"
    A5 = "A5"


class Orientation(Enum):
    """用紙の向き。"""

    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class InputType(Enum):
    """フィールドの入力種別。OCRエンジンの切り替えに使用する。"""

    PRINTED = "printed"
    HANDWRITTEN_NUMBER = "handwritten_number"
    HANDWRITTEN_KANA = "handwritten_kana"
    CHECKBOX = "checkbox"


class VariableType(Enum):
    """変数の型。OCR後処理やバリデーションに使用する。"""

    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"


class TomboShape(Enum):
    """トンボの形状。"""

    CIRCLE_CROSS = "circle_cross"


class HorizontalAlignment(Enum):
    """横位置。"""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class VerticalAlignment(Enum):
    """縦位置。"""

    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


@dataclass(frozen=True)
class Margins:
    """用紙余白（mm単位）。"""

    top: float
    right: float
    bottom: float
    left: float


@dataclass(frozen=True)
class Paper:
    """用紙設定。"""

    size: PaperSize
    orientation: Orientation
    width_mm: float
    height_mm: float
    margins: Margins


@dataclass(frozen=True)
class Field:
    """マニフェスト上の1フィールド（変数バインディング対象のボックス）。"""

    variable_id: str
    variable_name: str
    variable_type: VariableType
    input_type: InputType
    box_id: str
    region: Region
    absolute_region: Region
    horizontal_alignment: HorizontalAlignment = HorizontalAlignment.LEFT
    vertical_alignment: VerticalAlignment = VerticalAlignment.TOP


@dataclass(frozen=True)
class RegistrationMarks:
    """トンボ（レジストレーションマーク）の定義。

    Module Aのテンプレート登録時にPython側で座標計算され、
    拡張マニフェストに追記される。Module Bのトンボ検出で照合先として使用。
    """

    shape: TomboShape
    radius_mm: float
    positions: tuple[Point, ...]


@dataclass(frozen=True)
class PageIdentifier:
    """ページ識別コード。

    テンプレートID＋ページインデックスをQR/DataMatrixとして
    用紙余白に埋め込む。Module Bのページ自動判定で使用。
    """

    type: str  # "qr" or "datamatrix"
    content: str  # e.g. "invoice-001/0"
    position: Point
    size_mm: float


@dataclass(frozen=True)
class Page:
    """マニフェストの1ページ分。"""

    page_index: int
    paper: Paper
    fields: tuple[Field, ...]
    registration_marks: RegistrationMarks | None = None
    page_identifier: PageIdentifier | None = None

    def get_field(self, variable_name: str) -> Field | None:
        """変数名でフィールドを検索する。"""
        for f in self.fields:
            if f.variable_name == variable_name:
                return f
        return None

    @property
    def variable_names(self) -> list[str]:
        """このページの全変数名を返す。"""
        return [f.variable_name for f in self.fields]


@dataclass(frozen=True)
class ManifestData:
    """マニフェストJSONの全データを保持する値オブジェクト。"""

    template_id: str
    version: str
    pages: tuple[Page, ...]
    interface: str = ""
    extended: bool = field(default=False)
