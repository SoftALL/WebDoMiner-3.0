from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass
from typing import Iterable

from keybert import KeyBERT


@dataclass(slots=True)
class KeywordCandidate:
    """
    Represents a cleaned keyword candidate extracted from the RS document.
    """

    phrase: str
    score: float
    source: str  # e.g. "keybert", "fallback"
    token_count: int

    def to_dict(self) -> dict:
        return {
            "phrase": self.phrase,
            "score": self.score,
            "source": self.source,
            "token_count": self.token_count,
        }


_RS_FILLER_WORDS = {
    "shall",
    "must",
    "should",
    "may",
    "can",
    "could",
    "will",
    "would",
    "needs",
    "need",
    "required",
    "require",
    "requires",
    "able",
    "allow",
    "allows",
    "allowed",
    "provide",
    "provides",
    "provided",
    "support",
    "supports",
    "supported",
    "system",
    "application",
    "software",
    "platform",
    "solution",
    "module",
    "service",
    "services",
    "feature",
    "features",
    "function",
    "functions",
    "user",
    "users",
    "admin",
    "administrator",
    "client",
    "clients",
    "customer",
    "customers",
    "actor",
    "actors",
    "data",
    "information",
    "record",
    "records",
    "process",
    "processing",
    "manage",
    "management",
    "using",
    "used",
    "use",
    "within",
    "through",
    "based",
    "including",
    "include",
    "such",
    "ensure",
    "perform",
    "performed",
    "implementation",
    "implement",
    "implemented",
    "interface",
    "interfaces",
    "page",
    "pages",
    "screen",
    "screens",
    "workflow",
}

_GENERIC_BAD_SINGLE_WORDS = {
    "system",
    "software",
    "platform",
    "application",
    "service",
    "services",
    "feature",
    "features",
    "user",
    "users",
    "admin",
    "data",
    "record",
    "records",
    "information",
    "page",
    "pages",
    "module",
    "process",
    "management",
    "functionality",
    "support",
    "access",
    "create",
    "update",
    "delete",
    "view",
    "workflow",
}

_STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "for",
    "to",
    "of",
    "in",
    "on",
    "at",
    "by",
    "with",
    "from",
    "into",
    "over",
    "under",
    "between",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "that",
    "this",
    "these",
    "those",
    "it",
    "its",
    "their",
    "them",
    "there",
    "here",
    "which",
    "who",
    "whom",
    "whose",
    "not",
}

_DOCUMENT_NOISE_WORDS = {
    "requirement",
    "requirements",
    "specification",
    "specifications",
    "document",
    "documents",
    "proposal",
    "overview",
    "introduction",
    "project",
    "projects",
    "solution",
    "clinicflow",
}

_DOMAIN_NOUN_HINTS = {
    "appointment",
    "appointments",
    "patient",
    "patients",
    "doctor",
    "doctors",
    "hospital",
    "clinic",
    "medical",
    "medication",
    "prescription",
    "diagnosis",
    "schedule",
    "schedules",
    "inventory",
    "resource",
    "resources",
    "booking",
    "payment",
    "invoice",
    "shipment",
    "delivery",
    "route",
    "vehicle",
    "fleet",
    "warehouse",
    "driver",
    "demand",
    "forecast",
    "optimization",
    "attendance",
    "student",
    "teacher",
    "course",
    "enrollment",
    "security",
    "authentication",
    "authorization",
    "audit",
    "logistics",
    "tracking",
    "sensor",
    "telemetry",
    "maintenance",
    "availability",
    "calendar",
    "room",
    "rooms",
    "staff",
    "billing",
    "insurance",
    "ehr",
    "emr",
    "reminder",
    "reminders",
    "checkin",
    "checkout",
    "waitlist",
    "visit",
    "visits",
}

_ACTION_WORDS = {
    "schedule",
    "scheduling",
    "reschedule",
    "rescheduling",
    "book",
    "booking",
    "cancel",
    "cancellation",
    "confirm",
    "confirmation",
    "track",
    "tracking",
    "manage",
    "managing",
    "optimize",
    "optimization",
    "forecast",
    "forecasting",
}

_WEAK_CONTEXT_WORDS = {
    "priority",
    "utilization",
    "room",
    "rooms",
    "availability",
    "hours",
}


class KeywordExtractor:
    """
    Extract and clean domain-oriented keyword phrases from an RS document.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.model = KeyBERT(model=model_name)

    def extract_keywords(self, text: str, top_n: int = 20) -> list[KeywordCandidate]:
        """
        Extract cleaned keyword candidates from the RS text.
        """
        raw_candidates = self.model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            top_n=max(top_n * 2, 20),
            use_maxsum=False,
            nr_candidates=max(top_n * 3, 30),
        )

        cleaned: list[KeywordCandidate] = []
        seen_phrases: set[str] = set()

        for phrase, score in raw_candidates:
            normalized = normalize_phrase(phrase)
            if not normalized:
                continue

            if not is_strong_keyword_candidate(normalized):
                continue

            if normalized in seen_phrases:
                continue

            seen_phrases.add(normalized)
            cleaned.append(
                KeywordCandidate(
                    phrase=normalized,
                    score=float(score),
                    source="keybert",
                    token_count=count_tokens(normalized),
                )
            )

        if len(cleaned) < top_n:
            fallback_candidates = extract_fallback_phrases(text)
            for phrase in fallback_candidates:
                normalized = normalize_phrase(phrase)
                if not normalized:
                    continue
                if not is_strong_keyword_candidate(normalized):
                    continue
                if normalized in seen_phrases:
                    continue

                seen_phrases.add(normalized)
                cleaned.append(
                    KeywordCandidate(
                        phrase=normalized,
                        score=0.0,
                        source="fallback",
                        token_count=count_tokens(normalized),
                    )
                )

        ranked = rank_keyword_candidates(cleaned)
        return ranked[:top_n]


def normalize_phrase(phrase: str) -> str:
    """
    Normalize a raw extracted phrase into a clean lowercase keyword phrase.
    """
    phrase = phrase.lower().strip()
    phrase = phrase.replace("/", " ")
    phrase = phrase.replace("_", " ")
    phrase = phrase.replace("-", " ")
    phrase = re.sub(r"[^a-z0-9\s]", " ", phrase)
    phrase = re.sub(r"\s+", " ", phrase).strip()

    if not phrase:
        return ""

    tokens = phrase.split()

    while tokens and tokens[0] in _RS_FILLER_WORDS.union(_STOPWORDS):
        tokens.pop(0)
    while tokens and tokens[-1] in _RS_FILLER_WORDS.union(_STOPWORDS):
        tokens.pop()

    if not tokens:
        return ""

    deduped_tokens: list[str] = []
    for token in tokens:
        if not deduped_tokens or deduped_tokens[-1] != token:
            deduped_tokens.append(token)

    tokens = deduped_tokens

    if not tokens:
        return ""

    noise_count = sum(token in _DOCUMENT_NOISE_WORDS for token in tokens)
    if noise_count >= 2:
        return ""

    return " ".join(tokens)


def is_strong_keyword_candidate(phrase: str) -> bool:
    """
    Decide whether a phrase is strong enough to use for search discovery.
    """
    tokens = phrase.split()
    token_count = len(tokens)

    if token_count == 0 or token_count > 4:
        return False

    noise_count = sum(token in _DOCUMENT_NOISE_WORDS for token in tokens)
    if noise_count >= 2:
        return False

    if token_count == 1 and tokens[0] in _GENERIC_BAD_SINGLE_WORDS:
        return False

    if token_count == 1:
        token = tokens[0]
        if len(token) < 4:
            return False
        if token in _RS_FILLER_WORDS or token in _STOPWORDS or token in _DOCUMENT_NOISE_WORDS:
            return False
        if token.endswith("ing") and token not in _DOMAIN_NOUN_HINTS:
            return False
        return token in _DOMAIN_NOUN_HINTS

    meaningful_tokens = [
        token
        for token in tokens
        if token not in _RS_FILLER_WORDS
        and token not in _STOPWORDS
        and token not in _DOCUMENT_NOISE_WORDS
    ]

    if len(meaningful_tokens) < 2:
        return False

    filler_ratio = 1.0 - (len(meaningful_tokens) / len(tokens))
    if filler_ratio > 0.4:
        return False

    domain_tokens = [token for token in meaningful_tokens if token in _DOMAIN_NOUN_HINTS]
    action_tokens = [token for token in meaningful_tokens if token in _ACTION_WORDS]

    if len(domain_tokens) == 0:
        return False

    # Reject awkward 3-token patterns that are likely extraction artifacts.
    if token_count == 3:
        # domain-action-domain like "appointment track patient"
        if len(domain_tokens) >= 2 and len(action_tokens) == 1:
            action_position = next(
                (idx for idx, token in enumerate(tokens) if token in _ACTION_WORDS),
                -1,
            )
            if action_position == 1:
                return False

        # domain-weak-domain like "appointment priority clinic"
        if (
            tokens[0] in _DOMAIN_NOUN_HINTS
            and tokens[1] in _WEAK_CONTEXT_WORDS
            and tokens[2] in _DOMAIN_NOUN_HINTS
        ):
            return False

        # domain-weak-weak like "doctor utilization room"
        if (
            tokens[0] in _DOMAIN_NOUN_HINTS
            and tokens[1] in _WEAK_CONTEXT_WORDS
            and tokens[2] in _WEAK_CONTEXT_WORDS
        ):
            return False

    # Prefer phrases with clearer semantics:
    # - domain + domain
    # - action + domain
    # - domain + action
    if token_count == 2:
        return True

    if token_count == 3:
        return True

    if token_count == 4:
        return len(domain_tokens) >= 2

    return False


def extract_fallback_phrases(text: str) -> list[str]:
    """
    Lightweight fallback phrase extraction from the RS text.
    """
    normalized_text = text.lower()
    normalized_text = re.sub(r"[^a-z0-9\s]", " ", normalized_text)
    normalized_text = re.sub(r"\s+", " ", normalized_text).strip()

    tokens = normalized_text.split()
    phrases: list[str] = []

    for n in (2, 3):
        for i in range(len(tokens) - n + 1):
            phrase = " ".join(tokens[i : i + n])
            if is_strong_keyword_candidate(normalize_phrase(phrase)):
                phrases.append(phrase)

    unique_phrases = list(OrderedDict.fromkeys(phrases))
    return unique_phrases[:50]


def rank_keyword_candidates(
    candidates: Iterable[KeywordCandidate],
) -> list[KeywordCandidate]:
    """
    Rank candidates with a bias toward strong multi-word domain phrases.
    """
    return sorted(
        candidates,
        key=lambda c: (
            c.source != "keybert",
            c.token_count == 1,
            contains_weak_context(c.phrase),
            -min(c.token_count, 3),
            -contains_domain_hint(c.phrase),
            contains_document_noise(c.phrase),
            -c.score,
            c.phrase,
        ),
    )


def contains_domain_hint(phrase: str) -> int:
    """Return 1 if the phrase contains at least one domain noun hint, else 0."""
    return int(any(token in _DOMAIN_NOUN_HINTS for token in phrase.split()))


def contains_document_noise(phrase: str) -> int:
    """Return the number of document-noise words in the phrase."""
    return sum(token in _DOCUMENT_NOISE_WORDS for token in phrase.split())


def contains_weak_context(phrase: str) -> int:
    """Return the number of weak-context words in the phrase."""
    return sum(token in _WEAK_CONTEXT_WORDS for token in phrase.split())


def count_tokens(phrase: str) -> int:
    """Count whitespace-separated tokens in a phrase."""
    return len(phrase.split())