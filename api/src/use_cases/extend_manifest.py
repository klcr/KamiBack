"""拡張マニフェスト生成ユースケース。

マニフェストにトンボ座標とページ識別コードを追記する。
"""

from __future__ import annotations

from api.src.use_cases.parse_template import parse_template
from domain.src.manifest.manifest import Manifest
from domain.src.manifest.manifest_types import ManifestData


def extend_manifest_from_html(
    html: str,
    tombo_offset_mm: float = 5.0,
    tombo_radius_mm: float = 3.0,
) -> ManifestData:
    """HTMLテンプレートをパースし、拡張マニフェストを返す。"""
    result = parse_template(html)
    manifest_entity = Manifest(data=result.manifest)
    extended = manifest_entity.extend(
        tombo_offset_mm=tombo_offset_mm,
        tombo_radius_mm=tombo_radius_mm,
    )
    assert extended.data is not None
    return extended.data
