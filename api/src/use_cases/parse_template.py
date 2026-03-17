"""HTMLテンプレートパースユースケース。

HTMLテンプレートを受け取り、マニフェストJSONとテンプレートメタデータを抽出する。
"""

from __future__ import annotations

from dataclasses import dataclass

from api.src.infrastructure.html_parser import (
    HtmlParseError,
    parse_html,
)
from domain.src.manifest.manifest_types import ManifestData
from domain.src.template.template_types import TemplateMetadata


@dataclass(frozen=True)
class ParseTemplateResult:
    """パース結果。"""

    manifest: ManifestData
    template: TemplateMetadata


def parse_template(html: str) -> ParseTemplateResult:
    """HTMLテンプレートをパースし、マニフェストとテンプレートメタデータを返す。

    Raises:
        HtmlParseError: パースに失敗した場合
    """
    if not html.strip():
        raise HtmlParseError("HTMLが空です")

    manifest, template = parse_html(html)

    return ParseTemplateResult(manifest=manifest, template=template)
