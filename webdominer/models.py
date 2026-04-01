from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class SearchResult:
    """
    Raw result returned by a search backend before full URL discovery scoring.
    """

    keyword: str
    query: str
    title: str
    snippet: str
    url: str
    rank: int
    source: str  # e.g. "ddg", "searxng"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DiscoveredUrl:
    """
    Candidate URL that passed URL-level validation and is ready for scraping.
    """

    url: str
    matched_keyword: str
    query: str
    title: str = ""
    snippet: str = ""
    source: str = ""
    search_rank: int = 0
    discovery_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ScrapedPage:
    """
    Scraped and cleaned page content before final semantic acceptance/rejection.
    """

    url: str
    matched_keyword: str
    query: str
    title: str = ""
    text: str = ""
    word_count: int = 0
    similarity_score: float = 0.0
    extraction_method: str = ""  # e.g. "trafilatura", "playwright+trafilatura"
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CorpusDocument:
    """
    Final accepted output record.

    This matches the project requirement for traceable JSONL output.
    """

    source_url: str
    matched_keyword: str
    similarity_score: float
    text: str
    title: str = ""
    query: str = ""
    extraction_method: str = ""
    timestamp: str = field(default_factory=utc_now_iso)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_url": self.source_url,
            "matched_keyword": self.matched_keyword,
            "similarity_score": self.similarity_score,
            "text": self.text,
            "title": self.title,
            "query": self.query,
            "extraction_method": self.extraction_method,
            "timestamp": self.timestamp,
        }


@dataclass(slots=True)
class RejectedPage:
    """
    Record for URLs/pages that were processed but rejected for a known reason.
    """

    url: str
    reason: str
    matched_keyword: str = ""
    query: str = ""
    title: str = ""
    snippet: str = ""
    similarity_score: Optional[float] = None
    extraction_method: str = ""
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FailedPage:
    """
    Record for URLs that failed during fetching or scraping due to an error.
    """

    url: str
    error: str
    matched_keyword: str = ""
    query: str = ""
    title: str = ""
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PipelineSummary:
    """
    High-level stats to report after a pipeline run.
    """

    keywords_extracted: int = 0
    raw_search_results: int = 0
    unique_urls_discovered: int = 0
    pages_scraped_successfully: int = 0
    pages_rejected: int = 0
    pages_failed: int = 0
    final_accepted_documents: int = 0
    started_at: str = field(default_factory=utc_now_iso)
    finished_at: Optional[str] = None

    def mark_finished(self) -> None:
        self.finished_at = utc_now_iso()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)