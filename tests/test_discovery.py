from webdominer.models import SearchResult
from webdominer.retrieval.discovery import (
    UrlDiscoveryService,
    compute_domain_diversity_penalty,
    compute_rank_bonus,
    compute_text_overlap_score,
)
from webdominer.settings import Settings


class DummySearchClient:
    def search(self, keyword: str, query: str, max_results: int):
        return []


def test_compute_text_overlap_score_rewards_keyword_match() -> None:
    strong_score = compute_text_overlap_score(
        keyword="appointment scheduling",
        title="Appointment scheduling workflow for service teams",
        snippet="This article explains appointment scheduling and calendar workflows.",
        query='"appointment scheduling"',
    )
    weak_score = compute_text_overlap_score(
        keyword="appointment scheduling",
        title="Random article about gardening",
        snippet="Plants, watering, and soil.",
        query='"appointment scheduling"',
    )

    assert strong_score > weak_score


def test_compute_rank_bonus_prefers_better_rank() -> None:
    assert compute_rank_bonus(1) > compute_rank_bonus(5)
    assert compute_rank_bonus(5) >= compute_rank_bonus(20)


def test_compute_domain_diversity_penalty_increases_for_later_domain_results() -> None:
    assert compute_domain_diversity_penalty(1) == 0.0
    assert compute_domain_diversity_penalty(2) > 0.0
    assert compute_domain_diversity_penalty(4) >= compute_domain_diversity_penalty(2)


def test_discover_urls_deduplicates_same_normalized_url() -> None:
    settings = Settings()
    service = UrlDiscoveryService(settings, DummySearchClient())

    raw_results = [
        SearchResult(
            keyword="appointment scheduling",
            query='"appointment scheduling"',
            title="Appointment scheduling workflow",
            snippet="A useful article on appointment scheduling workflow.",
            url="https://example.com/article?utm_source=google",
            rank=2,
            source="ddg",
        ),
        SearchResult(
            keyword="appointment scheduling",
            query="appointment scheduling calendar service",
            title="Appointment scheduling workflow guide",
            snippet="An even better article on appointment scheduling.",
            url="https://example.com/article",
            rank=1,
            source="ddg",
        ),
    ]

    discovered = service.discover_urls(raw_results)

    assert len(discovered) == 1
    assert discovered[0].url == "https://example.com/article"


def test_discover_urls_filters_low_value_domain() -> None:
    settings = Settings()
    service = UrlDiscoveryService(settings, DummySearchClient())

    raw_results = [
        SearchResult(
            keyword="appointment scheduling",
            query='"appointment scheduling"',
            title="Zhihu result",
            snippet="Noise result",
            url="https://www.zhihu.com/question/123",
            rank=1,
            source="ddg",
        ),
        SearchResult(
            keyword="appointment scheduling",
            query='"appointment scheduling"',
            title="Useful scheduling article",
            snippet="Strong appointment scheduling article",
            url="https://example.com/scheduling-workflow",
            rank=2,
            source="ddg",
        ),
    ]

    discovered = service.discover_urls(raw_results)

    assert len(discovered) == 1
    assert discovered[0].url == "https://example.com/scheduling-workflow"


def test_discover_urls_prefers_better_scored_duplicate() -> None:
    settings = Settings()
    service = UrlDiscoveryService(settings, DummySearchClient())

    raw_results = [
        SearchResult(
            keyword="route planning",
            query='"route planning"',
            title="Weak result",
            snippet="Short generic snippet.",
            url="https://example.com/planning",
            rank=5,
            source="ddg",
        ),
        SearchResult(
            keyword="route planning",
            query="route planning delivery optimization",
            title="Route planning workflow for delivery operations",
            snippet="Detailed route planning, scheduling, and delivery optimization guide.",
            url="https://example.com/planning",
            rank=1,
            source="ddg",
        ),
    ]

    discovered = service.discover_urls(raw_results)

    assert len(discovered) == 1
    assert discovered[0].title == "Route planning workflow for delivery operations"
    assert discovered[0].search_rank == 1