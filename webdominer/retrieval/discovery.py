from __future__ import annotations

import math
from collections import defaultdict

from webdominer.logging_utils import get_logger
from webdominer.models import DiscoveredUrl, FailedPage, SearchResult
from webdominer.retrieval.query_builder import SearchQuery
from webdominer.retrieval.search_clients import BaseSearchClient
from webdominer.retrieval.url_filters import (
    get_url_domain,
    is_probably_html_url,
    normalize_url,
)
from webdominer.settings import Settings


def tokenize_for_matching(text: str) -> list[str]:
    """
    Lightweight tokenizer for title/snippet/query relevance matching.
    """
    cleaned = []
    current = []

    for char in text.lower():
        if char.isalnum():
            current.append(char)
        else:
            if current:
                cleaned.append("".join(current))
                current = []

    if current:
        cleaned.append("".join(current))

    return cleaned


def compute_text_overlap_score(keyword: str, title: str, snippet: str, query: str) -> float:
    """
    Cheap lexical relevance score using overlap between keyword/query tokens
    and search-result title/snippet tokens.
    """
    keyword_tokens = set(tokenize_for_matching(keyword))
    query_tokens = set(tokenize_for_matching(query))
    result_tokens = set(tokenize_for_matching(f"{title} {snippet}"))

    if not result_tokens:
        return 0.0

    keyword_overlap = len(keyword_tokens & result_tokens)
    query_overlap = len(query_tokens & result_tokens)

    score = 0.0
    score += keyword_overlap * 3.0
    score += query_overlap * 1.2

    if keyword.lower() in f"{title} {snippet}".lower():
        score += 4.0

    return score


def compute_rank_bonus(search_rank: int) -> float:
    """
    Higher-ranked search results get a small bonus.
    """
    if search_rank <= 0:
        return 0.0
    return max(0.0, 2.5 - math.log2(search_rank + 1))


def compute_domain_diversity_penalty(position_within_domain: int) -> float:
    """
    Penalize too many results from the same domain to improve diversity.
    """
    if position_within_domain <= 1:
        return 0.0
    return min(1.5, 0.35 * (position_within_domain - 1))


class UrlDiscoveryService:
    """
    Discover, validate, deduplicate, and pre-rank URLs before scraping.
    """

    def __init__(self, settings: Settings, search_client: BaseSearchClient) -> None:
        self.settings = settings
        self.search_client = search_client
        self.logger = get_logger(__name__)

    def run_searches(
        self,
        queries: list[SearchQuery],
    ) -> tuple[list[SearchResult], list[FailedPage]]:
        """
        Execute all query searches and collect raw results.

        Search failures are captured and returned instead of aborting the whole stage.
        """
        all_results: list[SearchResult] = []
        failed_searches: list[FailedPage] = []

        for item in queries:
            try:
                results = self.search_client.search(
                    keyword=item.keyword,
                    query=item.query,
                    max_results=self.settings.top_urls_per_keyword,
                )
                all_results.extend(results)
            except Exception as exc:
                self.logger.warning(
                    "Search failed for query %r (keyword=%r): %s",
                    item.query,
                    item.keyword,
                    exc,
                )
                failed_searches.append(
                    FailedPage(
                        url="",
                        error=f"search_failure:{type(exc).__name__}: {exc}",
                        matched_keyword=item.keyword,
                        query=item.query,
                        title="",
                    )
                )

        return all_results, failed_searches

    def discover_urls(self, raw_results: list[SearchResult]) -> list[DiscoveredUrl]:
        """
        Convert raw search results into validated, deduplicated, pre-ranked URLs.
        """
        valid_results: list[SearchResult] = []

        for result in raw_results:
            if not is_probably_html_url(
                url=result.url,
                allowed_schemes=self.settings.allowed_schemes,
                bad_extensions=self.settings.bad_extensions,
                bad_url_patterns=self.settings.bad_url_patterns,
            ):
                continue
            valid_results.append(result)

        deduped_by_url: dict[str, SearchResult] = {}

        for result in valid_results:
            normalized_url = normalize_url(result.url)
            existing = deduped_by_url.get(normalized_url)

            if existing is None:
                deduped_by_url[normalized_url] = result
                continue

            existing_score = compute_text_overlap_score(
                keyword=existing.keyword,
                title=existing.title,
                snippet=existing.snippet,
                query=existing.query,
            ) + compute_rank_bonus(existing.rank)

            new_score = compute_text_overlap_score(
                keyword=result.keyword,
                title=result.title,
                snippet=result.snippet,
                query=result.query,
            ) + compute_rank_bonus(result.rank)

            if new_score > existing_score:
                deduped_by_url[normalized_url] = result

        grouped_by_domain: dict[str, list[tuple[str, SearchResult]]] = defaultdict(list)
        for normalized_url, result in deduped_by_url.items():
            domain = get_url_domain(normalized_url)
            grouped_by_domain[domain].append((normalized_url, result))

        discovered: list[DiscoveredUrl] = []

        for domain_items in grouped_by_domain.values():
            domain_items.sort(
                key=lambda item: (
                    -compute_text_overlap_score(
                        keyword=item[1].keyword,
                        title=item[1].title,
                        snippet=item[1].snippet,
                        query=item[1].query,
                    ),
                    item[1].rank,
                )
            )

            for index_within_domain, (normalized_url, result) in enumerate(
                domain_items,
                start=1,
            ):
                overlap_score = compute_text_overlap_score(
                    keyword=result.keyword,
                    title=result.title,
                    snippet=result.snippet,
                    query=result.query,
                )
                rank_bonus = compute_rank_bonus(result.rank)
                diversity_penalty = compute_domain_diversity_penalty(index_within_domain)
                final_score = overlap_score + rank_bonus - diversity_penalty

                discovered.append(
                    DiscoveredUrl(
                        url=normalized_url,
                        matched_keyword=result.keyword,
                        query=result.query,
                        title=result.title,
                        snippet=result.snippet,
                        source=result.source,
                        search_rank=result.rank,
                        discovery_score=round(final_score, 4),
                    )
                )

        discovered.sort(
            key=lambda item: (-item.discovery_score, item.search_rank, item.url)
        )

        return discovered

    def search_and_discover(
        self,
        queries: list[SearchQuery],
    ) -> tuple[list[SearchResult], list[DiscoveredUrl], list[FailedPage]]:
        """
        Run the full discovery stage and return raw results, discovered URLs,
        and captured search failures.
        """
        raw_results, failed_searches = self.run_searches(queries)
        discovered = self.discover_urls(raw_results)
        return raw_results, discovered, failed_searches