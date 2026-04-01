from __future__ import annotations

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


_HEALTHCARE_HINTS = {
    "patient",
    "patients",
    "doctor",
    "doctors",
    "clinic",
    "medical",
    "ehr",
    "emr",
    "appointment",
    "appointments",
    "billing",
    "insurance",
    "schedule",
    "scheduling",
    "availability",
    "visit",
    "visits",
    "reminder",
    "reminders",
}


class QueryBuilder:
    """
    Build search-engine-friendly queries from cleaned keyword phrases.

    The main design goal is to avoid over-generic expansions that attract
    dictionary pages, help-center pages, or language-usage pages.
    """

    def build_queries_for_keyword(self, keyword: str) -> list[SearchQuery]:
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

        tokens = keyword.split()
        is_healthcare = any(token in _HEALTHCARE_HINTS for token in tokens)

        # Keep exact phrase for precision.
        add(f'"{keyword}"', "exact_phrase")

        # Stronger domain query instead of generic "guide overview best practices".
        if is_healthcare:
            add(
                f'{keyword} healthcare clinic software workflow',
                "healthcare_domain",
            )
            add(
                f'{keyword} ehr scheduling system',
                "ehr_domain",
            )
        else:
            add(
                f'{keyword} software workflow system',
                "domain_context",
            )

        # Add a process-oriented query only when the keyword already looks operational.
        if any(token.endswith("ing") for token in tokens) or "schedule" in tokens or "appointments" in tokens:
            if is_healthcare:
                add(
                    f'{keyword} patient scheduling workflow clinic',
                    "process_context",
                )
            else:
                add(
                    f'{keyword} workflow process',
                    "process_context",
                )

        return queries

    def build_queries(self, keywords: list[str]) -> list[SearchQuery]:
        all_queries: list[SearchQuery] = []
        seen: set[tuple[str, str]] = set()

        for keyword in keywords:
            for item in self.build_queries_for_keyword(keyword):
                key = (item.keyword, item.query)
                if key in seen:
                    continue
                seen.add(key)
                all_queries.append(item)

        return all_queries