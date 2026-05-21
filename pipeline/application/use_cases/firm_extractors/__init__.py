"""Firm-specific extractors registry.

To add a new firm: implement :class:`FirmExtractor`, add the
``FirmName`` value, register it here. CrawlFirmSite looks the extractor up
by firm name — no other layer is involved.
"""

from __future__ import annotations

from pipeline.application.use_cases.firm_extractors.a16z import A16zExtractor
from pipeline.application.use_cases.firm_extractors.protocol import (
    FirmExtractor,
    FirmSubgraph,
)
from pipeline.application.use_cases.firm_extractors.sequoia import SequoiaExtractor
from pipeline.application.use_cases.firm_extractors.yc import YCExtractor
from pipeline.entities.value_objects import FirmName

EXTRACTORS: dict[FirmName, FirmExtractor] = {
    FirmName.SEQUOIA: SequoiaExtractor(),
    FirmName.A16Z: A16zExtractor(),
    FirmName.YCOMBINATOR: YCExtractor(),
}

__all__ = [
    "EXTRACTORS",
    "FirmExtractor",
    "FirmSubgraph",
    "SequoiaExtractor",
    "A16zExtractor",
    "YCExtractor",
]
