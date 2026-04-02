from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass(slots=True)
class SearchQuery:
    """
    A search-ready query built from a cleaned keyword phrase.
    """

    keyword: str
    query: str
    strategy: str

    def to_dict(self) -> dict:
        return {
            "keyword": self.keyword,
            "query": self.query,
            "strategy": self.strategy,
        }


_GENERIC_CONTEXT_STOPWORDS = {
    "system",
    "software",
    "platform",
    "application",
    "service",
    "services",
    "module",
    "feature",
    "features",
    "process",
    "workflow",
    "management",
    "user",
    "users",
    "admin",
    "administrator",
    "data",
    "information",
    "record",
    "records",
    "page",
    "pages",
}

_PROCESS_HINTS = {
    "schedule",
    "scheduling",
    "reschedule",
    "rescheduling",
    "book",
    "booking",
    "track",
    "tracking",
    "manage",
    "managing",
    "monitor",
    "monitoring",
    "forecast",
    "forecasting",
    "optimize",
    "optimization",
    "plan",
    "planning",
    "assign",
    "assignment",
    "dispatch",
    "dispatching",
    "audit",
    "auditing",
    "billing",
    "payment",
    "notification",
    "notifications",
    "report",
    "reporting",
}


def _tokenize(text: str) -> list[str]:
    return [token.strip().lower() for token in text.split() if token.strip()]


def _looks_process_or_feature(tokens: list[str]) -> bool:
    return any(
        token in _PROCESS_HINTS
        or token.endswith("ing")
        or token.endswith("tion")
        or token.endswith("ment")
        for token in tokens
    )


def _build_global_context_tokens(keywords: list[str], limit: int = 8) -> list[str]:
    counts: Counter[str] = Counter()

    for keyword in keywords:
        for token in _tokenize(keyword):
            if token in _GENERIC_CONTEXT_STOPWORDS:
                continue
            if len(token) < 3:
                continue
            counts[token] += 1

    ranked = sorted(
        counts.items(),
        key=lambda item: (-item[1], -len(item[0]), item[0]),
    )

    return [token for token, _ in ranked[:limit]]


class QueryBuilder:
    """
    Build search-engine-friendly queries from cleaned keyword phrases.

    Design goal:
    - fully domain-neutral
    - driven by the RS-derived keywords
    - avoids hardcoded healthcare or other fixed-domain expansions
    """

    def build_queries_for_keyword(
        self,
        keyword: str,
        global_context_tokens: list[str] | None = None,
    ) -> list[SearchQuery]:
        keyword = keyword.strip()
        if not keyword:
            return []

        queries: list[SearchQuery] = []
        seen: set[str] = set()

        def add(query: str, strategy: str) -> None:
            normalized = query.strip()
            if not normalized or normalized in seen:
                return
            seen.add(normalized)
            queries.append(
                SearchQuery(
                    keyword=keyword,
                    query=normalized,
                    strategy=strategy,
                )
            )

        tokens = _tokenize(keyword)
        global_context_tokens = global_context_tokens or []

        # 1) Precision query
        add(f'"{keyword}"', "exact_phrase")

        # 2) RS-derived context query
        context_tokens = [
            token
            for token in global_context_tokens
            if token not in tokens
        ][:2]

        if context_tokens:
            add(
                f'{keyword} {" ".join(context_tokens)}',
                "rs_context",
            )

        # 3) Generic neutral expansion
        if _looks_process_or_feature(tokens):
            add(
                f"{keyword} workflow system",
                "process_context",
            )
        else:
            add(
                f"{keyword} software system",
                "system_context",
            )

        return queries

    def build_queries(self, keywords: list[str]) -> list[SearchQuery]:
        all_queries: list[SearchQuery] = []
        seen: set[tuple[str, str]] = set()

        global_context_tokens = _build_global_context_tokens(keywords)

        for keyword in keywords:
            for item in self.build_queries_for_keyword(
                keyword,
                global_context_tokens=global_context_tokens,
            ):
                key = (item.keyword, item.query)
                if key in seen:
                    continue
                seen.add(key)
                all_queries.append(item)

        return all_queries