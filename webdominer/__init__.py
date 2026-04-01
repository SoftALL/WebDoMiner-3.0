"""
WebDoMiner package.

WebDoMiner builds a domain-specific corpus from the open web using
a natural-language requirements specification (RS) document.
"""

from .settings import Settings
from .models import (
    CorpusDocument,
    SearchResult,
    DiscoveredUrl,
    ScrapedPage,
    RejectedPage,
    PipelineSummary,
)

__all__ = [
    "Settings",
    "CorpusDocument",
    "SearchResult",
    "DiscoveredUrl",
    "ScrapedPage",
    "RejectedPage",
    "PipelineSummary",
]

__version__ = "1.0.0"