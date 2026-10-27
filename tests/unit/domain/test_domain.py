from datetime import UTC, datetime

import pytest

from streaming_assistant.domain.audit import GENESIS, make_entry, verify
from streaming_assistant.domain.citations import MarkerStripper, check_refs
from streaming_assistant.domain.retrieval import Bm25Index, Section, terms
from streaming_assistant.domain.routing import (
    ANSWER,
    LOW_CONFIDENCE,
    NO_EVIDENCE,
    PAUSE,
    Thresholds,
    days_since_delivery,
    decide_route,
    needs_a_person,
    words_to_number,
)
from streaming_assistant.domain.stats import percentile

NOW = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)


def chain(count: int = 4):
    entries, previous = [], None
    for number in range(count):
        entry = make_entry(
            previous, "run-1", ("received", "paused", "answered", "shown")[number % 4], "actor", NOW, f"step {number}"
        )
        entries.append(entry)
        previous = entry.hash
    return entries


def test_an_intact_chain_verifies_and_starts_from_the_genesis_marker():
    entries = chain()
    assert verify(entries) is None and entries[0].previous == GENESIS and verify([]) is None


def test_an_edited_entry_is_reported_at_its_own_index():
    from dataclasses import replace

    entries = chain()
    entries[2] = replace(entries[2], content="Approve a full refund")
    assert verify(entries) == 2


def test_a_removed_entry_is_reported_where_the_gap_is():
    entries = chain()
    del entries[1]
    assert verify(entries) == 1


def test_a_reordered_pair_is_reported_at_the_first_moved_entry():
    entries = chain()
    entries[1], entries[2] = entries[2], entries[1]
    assert verify(entries) == 1


def test_a_hash_recomputed_by_the_editor_still_breaks_the_next_link():
    from dataclasses import replace

    from streaming_assistant.domain.audit import digest

    entries = chain()
    edited = replace(entries[1], content="changed")
    edited = replace(edited, hash=digest(edited.previous, edited.run, edited.step, edited.actor, edited.at, "changed"))
    entries[1] = edited
    assert verify(entries) == 2


def section(ref="help-01#shipping-times", heading="Shipping times", text="Standard delivery takes three to five days."):
    page, anchor = ref.split("#")
    return Section(page, "Shipping", anchor, heading, text)


def test_markers_are_removed_even_when_split_across_pieces_and_their_refs_are_remembered():
    strip = MarkerStripper()
    shown = strip.feed("Delivery takes days [help-01#ship")
    shown += strip.feed("ping-times] and more.")
    assert shown == "Delivery takes days  and more." and strip.refs == ["help-01#shipping-times"]
    assert strip.feed("again [help-01#shipping-times]") == "again " and strip.refs == ["help-01#shipping-times"]


def test_brackets_that_are_not_citations_are_shown_and_unclosed_ones_are_held_then_released():
    strip = MarkerStripper()
    assert strip.feed("a [note] b") == "a [note] b" and strip.refs == []
    assert strip.feed("open [help-01") == "open "
    assert strip.finish() == "[help-01" and strip.finish() == ""
    long = "x [" + "y" * 60
    assert MarkerStripper().feed(long) == long


def test_only_refs_retrieved_for_the_request_may_be_shown_and_the_rest_are_counted():
    allowed = {"help-01#shipping-times": section()}
    shown, dropped = check_refs(["help-01#shipping-times", "help-99#made-up"], allowed)
    assert [s.ref for s in shown] == ["help-01#shipping-times"] and dropped == 1
    assert check_refs([], allowed) == ((), 0)


def test_terms_drop_stop_words_and_fold_plurals():
    assert terms("How do I track my parcels?") == ["track", "parcel"]


def make_index():
    return Bm25Index(
        [
            section(),
            section(
                "help-02#refund-timing", "Refund timing", "A refund appears on the card within five business days."
            ),
            section("help-03#gift-wrap", "Gift wrap", "Gift wrap is a checkout option for a small fee."),
        ]
    )


def test_search_ranks_the_covering_section_first_and_reports_its_coverage():
    hits = make_index().search("When does a refund appear on the card?")
    assert hits[0].section.ref == "help-02#refund-timing" and hits[0].coverage == pytest.approx(1.0)
    assert make_index().search("zebra") == []


def test_words_found_nowhere_count_against_coverage():
    covered = make_index().search("refund card")[0].coverage
    diluted = make_index().search("refund card zebra giraffe")[0].coverage
    assert covered == pytest.approx(1.0) and diluted < covered and diluted <= 0.55


@pytest.mark.parametrize(
    ("text", "number"),
    [
        ("75", 75),
        ("seventy five", 75),
        ("a hundred", 100),
        ("one hundred and five", 105),
        ("sixty-five", 65),
        ("banana", None),
        ("", None),
        ("and", None),
    ],
)
def test_small_numbers_are_read_from_digits_and_words(text, number):
    assert words_to_number(text) == number


@pytest.mark.parametrize(
    ("question", "days"),
    [
        ("I got it seventy five days ago", 75),
        ("it came a hundred days ago", 100),
        ("delivered 12 days since", 12),
        ("How do I get a refund?", None),
        ("a banana days ago", None),
    ],
)
def test_the_age_of_an_order_is_read_from_the_question(question, days):
    assert days_since_delivery(question) == days


@pytest.mark.parametrize(
    ("question", "pauses"),
    [
        ("I want a refund for something I received fifty days ago.", True),
        ("I received it ten days ago, refund please", False),
        ("Refund me, it arrived thirty days ago", False),
        ("How do I get a refund?", False),
        ("I will take legal action", True),
        ("The chargeback is filed", True),
        ("Sixty days ago I ordered a lamp", False),
    ],
)
def test_a_refund_after_the_window_or_a_legal_threat_needs_a_person(question, pauses):
    assert needs_a_person(question) is pauses


def hit(coverage):
    from streaming_assistant.domain.retrieval import Hit

    return Hit(section(), 1.0, coverage)


def test_routes_follow_the_thresholds():
    thresholds = Thresholds()
    assert decide_route("how long is delivery", [hit(0.9)], thresholds).kind == ANSWER
    assert decide_route("how long is delivery", [hit(0.5)], thresholds).kind == LOW_CONFIDENCE
    assert decide_route("how long is delivery", [hit(0.1)], thresholds).kind == PAUSE
    assert decide_route("how long is delivery", [], thresholds).kind == PAUSE
    assert decide_route("how long is delivery", [], thresholds, pause_enabled=False).kind == NO_EVIDENCE
    assert decide_route("refund from ninety days ago", [hit(0.9)], thresholds).kind == PAUSE
    assert decide_route("refund from ninety days ago", [hit(0.9)], thresholds, pause_enabled=False).kind == ANSWER


def test_percentile_is_nearest_rank_and_safe_on_nothing():
    assert percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.95) == 10
    assert percentile([5.0], 0.5) == 5.0 and percentile([], 0.5) == 0.0
    assert percentile([4, 1, 3, 2], 0.5) == 2
