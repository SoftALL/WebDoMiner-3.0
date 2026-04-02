from webdominer.retrieval.keywording import (
    contains_action_heaviness,
    contains_document_noise,
    contains_weak_context,
    count_tokens,
    is_strong_keyword_candidate,
    normalize_phrase,
)


def test_normalize_phrase_removes_basic_noise() -> None:
    phrase = "  Appointment-Scheduling / Platform!!  "
    assert normalize_phrase(phrase) == "appointment scheduling"


def test_normalize_phrase_rejects_document_title_noise() -> None:
    phrase = "ClinicFlow Requirements Specification"
    assert normalize_phrase(phrase) == ""


def test_strong_keyword_candidate_accepts_good_multiword_phrase() -> None:
    assert is_strong_keyword_candidate("appointment scheduling") is True


def test_strong_keyword_candidate_accepts_two_word_phrase() -> None:
    assert is_strong_keyword_candidate("route planning") is True


def test_strong_keyword_candidate_rejects_document_noise_phrase() -> None:
    assert is_strong_keyword_candidate("requirements specification") is False


def test_strong_keyword_candidate_rejects_awkward_action_middle_pattern() -> None:
    assert is_strong_keyword_candidate("appointment track patient") is False


def test_strong_keyword_candidate_rejects_awkward_weak_middle_pattern() -> None:
    assert is_strong_keyword_candidate("appointment priority clinic") is False


def test_strong_keyword_candidate_rejects_weak_heavy_phrase() -> None:
    assert is_strong_keyword_candidate("doctor utilization hours") is False


def test_strong_keyword_candidate_rejects_generic_single_word() -> None:
    assert is_strong_keyword_candidate("system") is False


def test_strong_keyword_candidate_accepts_meaningful_single_word() -> None:
    assert is_strong_keyword_candidate("logistics") is True


def test_strong_keyword_candidate_rejects_action_single_word_ing_form() -> None:
    assert is_strong_keyword_candidate("scheduling") is False


def test_contains_document_noise_counts_correctly() -> None:
    assert contains_document_noise("clinicflow requirements specification") == 3


def test_contains_weak_context_counts_correctly() -> None:
    assert contains_weak_context("doctor utilization hours") == 2


def test_contains_action_heaviness_counts_correctly() -> None:
    assert contains_action_heaviness("schedule tracking reporting") == 3


def test_count_tokens_counts_words() -> None:
    assert count_tokens("appointment scheduling") == 2