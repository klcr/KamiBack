"""マニフェスト集約ルート。

マニフェストJSONを保持し、ページ走査・フィールド検索・変数一覧取得・
拡張マニフェスト生成（トンボ座標計算・ページ識別コード追記）を提供する。
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from domain.src.manifest.manifest_types import (
    Field,
    ManifestData,
    Page,
    PageIdentifier,
    RegistrationMarks,
    TomboShape,
    VariableType,
)
from domain.src.shared.coordinate import Point
from domain.src.shared.entity_base import BaseEntity

# トンボのデフォルト設定
_DEFAULT_TOMBO_OFFSET_MM = 5.0
_DEFAULT_TOMBO_RADIUS_MM = 3.0


@dataclass
class Manifest(BaseEntity):
    """マニフェスト集約ルート。"""

    data: ManifestData | None = None

    @property
    def template_id(self) -> str:
        self._ensure_loaded()
        assert self.data is not None
        return self.data.template_id

    @property
    def version(self) -> str:
        self._ensure_loaded()
        assert self.data is not None
        return self.data.version

    @property
    def pages(self) -> tuple[Page, ...]:
        self._ensure_loaded()
        assert self.data is not None
        return self.data.pages

    @property
    def is_extended(self) -> bool:
        """拡張マニフェスト（トンボ・ページ識別コード追記済み）かどうか。"""
        return self.data is not None and self.data.extended

    def all_variable_names(self) -> list[str]:
        """全ページの変数名一覧を返す。"""
        self._ensure_loaded()
        assert self.data is not None
        names: list[str] = []
        for page in self.data.pages:
            names.extend(page.variable_names)
        return names

    def all_fields(self) -> list[Field]:
        """全ページの全フィールドをフラットなリストで返す。"""
        self._ensure_loaded()
        assert self.data is not None
        fields: list[Field] = []
        for page in self.data.pages:
            fields.extend(page.fields)
        return fields

    def get_field(self, variable_name: str) -> Field | None:
        """変数名でフィールドを検索する（全ページ横断）。"""
        self._ensure_loaded()
        assert self.data is not None
        for page in self.data.pages:
            field = page.get_field(variable_name)
            if field is not None:
                return field
        return None

    def get_page(self, page_index: int) -> Page | None:
        """ページインデックスでページを取得する。"""
        self._ensure_loaded()
        assert self.data is not None
        for page in self.data.pages:
            if page.page_index == page_index:
                return page
        return None

    def variable_type_map(self) -> dict[str, VariableType]:
        """変数名→型のマッピングを返す。"""
        return {f.variable_name: f.variable_type for f in self.all_fields()}

    def extend(
        self,
        tombo_offset_mm: float = _DEFAULT_TOMBO_OFFSET_MM,
        tombo_radius_mm: float = _DEFAULT_TOMBO_RADIUS_MM,
    ) -> Manifest:
        """拡張マニフェストを生成する。

        各ページにトンボ座標とページ識別コードを追記した新しいManifestを返す。
        元のManifestは変更しない（イミュータブル操作）。

        Args:
            tombo_offset_mm: トンボの用紙端からのオフセット（mm）
            tombo_radius_mm: トンボの半径（mm）
        """
        self._ensure_loaded()
        assert self.data is not None

        extended_pages: list[Page] = []
        for page in self.data.pages:
            marks = _calculate_registration_marks(
                paper_width_mm=page.paper.width_mm,
                paper_height_mm=page.paper.height_mm,
                offset_mm=tombo_offset_mm,
                radius_mm=tombo_radius_mm,
            )
            page_id = PageIdentifier(
                type="qr",
                content=f"{self.data.template_id}/{page.page_index}",
                position=Point(
                    x_mm=page.paper.width_mm - tombo_offset_mm - 8.0,
                    y_mm=page.paper.height_mm - tombo_offset_mm - 8.0,
                ),
                size_mm=8.0,
            )
            extended_pages.append(
                replace(
                    page,
                    registration_marks=marks,
                    page_identifier=page_id,
                )
            )

        extended_data = replace(
            self.data,
            pages=tuple(extended_pages),
            extended=True,
        )
        return Manifest(id=self.id, data=extended_data)

    def _ensure_loaded(self) -> None:
        if self.data is None:
            raise ValueError("Manifest data has not been loaded")


def _calculate_registration_marks(
    paper_width_mm: float,
    paper_height_mm: float,
    offset_mm: float,
    radius_mm: float,
) -> RegistrationMarks:
    """用紙サイズからトンボの四隅座標を計算する。

    トンボは用紙物理端からoffset_mmの位置に配置される。
    """
    return RegistrationMarks(
        shape=TomboShape.CIRCLE_CROSS,
        radius_mm=radius_mm,
        positions=(
            Point(x_mm=offset_mm, y_mm=offset_mm),
            Point(x_mm=paper_width_mm - offset_mm, y_mm=offset_mm),
            Point(x_mm=offset_mm, y_mm=paper_height_mm - offset_mm),
            Point(x_mm=paper_width_mm - offset_mm, y_mm=paper_height_mm - offset_mm),
        ),
    )
