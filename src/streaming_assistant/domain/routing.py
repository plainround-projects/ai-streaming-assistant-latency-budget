"""What to do with a question: answer, say it is thin, say nothing was found, or pause for a person. Thresholds are explicit."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from streaming_assistant.domain.retrieval import Hit

ANSWER = "answer"
LOW_CONFIDENCE = "low_confidence"
NO_EVIDENCE = "no_evidence"
PAUSE = "pause"
RETURN_WINDOW_DAYS = 30
LEGAL = re.compile(r"\b(?:lawyer|legal action|sue|chargeback)\b", re.I)
REFUND = re.compile(r"\b(?:refund|money back|reimburse)", re.I)
_UNITS = {
    word: number
    for number, word in enumerate(
        [
            "zero",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "eleven",
            "twelve",
            "thirteen",
            "fourteen",
            "fifteen",
            "sixteen",
            "seventeen",
            "eighteen",
            "nineteen",
        ]
    )
}
_TENS = {
    word: 10 * number
    for number, word in enumerate(
        ["zero", "ten", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    )
    if number > 1
}
_DAYS_AGO = re.compile(r"\bdays? (?:ago|old|since)\b", re.I)


def words_to_number(text: str) -> int | None:
    """A small number written in digits or words ("75", "seventy five", "a hundred"); None when it is not one."""
    words = text.lower().replace("-", " ").split()
    if len(words) == 1 and words[0].isdigit():
        return int(words[0])
    total, seen = 0, False
    for word in words:
        if word in ("a", "one") and not seen:
            total, seen = 1, True
            continue
        if word == "hundred":
            total, seen = (total or 1) * 100, True
        elif word in _TENS:
            total, seen = total + _TENS[word], True
        elif word in _UNITS:
            total, seen = total + _UNITS[word], True
        elif word == "and":
            continue
        else:
            return None
    return total if seen else None


def days_since_delivery(question: str) -> int | None:
    """The age in days a question states ("sixty days ago", "75 days ago"), or None. The longest run of up to four
    words before "days ago" that reads as a number wins, so "seventy five" is 75, not 5."""
    for match in _DAYS_AGO.finditer(question):
        tokens = re.findall(r"[\w-]+", question[: match.start()])[-4:]
        for start in range(len(tokens)):
            number = words_to_number(" ".join(tokens[start:]))
            if number is not None:
                return number
    return None


def needs_a_person(question: str) -> bool:
    """A refund asked for after the 30-day window, or a legal threat: a policy exception only a person can grant."""
    age = days_since_delivery(question)
    return bool(LEGAL.search(question)) or (
        REFUND.search(question) is not None and age is not None and age > RETURN_WINDOW_DAYS
    )


@dataclass(frozen=True, slots=True)
class Thresholds:
    """Retrieval coverage at which a question is answered, called thin, or sent to a person."""

    confident: float = 0.6
    pause_below: float = 0.4


@dataclass(frozen=True, slots=True)
class Route:
    """The decision and why."""

    kind: str
    reason: str


def decide_route(question: str, hits: Sequence[Hit], thresholds: Thresholds, *, pause_enabled: bool = True) -> Route:
    """A question that matches a needs-a-person pattern pauses; so does one no page covers (when pausing is on)."""
    if pause_enabled and needs_a_person(question):
        return Route(PAUSE, "policy_exception")
    best = hits[0].coverage if hits else 0.0
    if best < thresholds.pause_below:
        return Route(PAUSE, "no_page_covers") if pause_enabled else Route(NO_EVIDENCE, "no_page_covers")
    if best < thresholds.confident:
        return Route(LOW_CONFIDENCE, f"best coverage {best:.2f} is below {thresholds.confident:.2f}")
    return Route(ANSWER, f"best coverage {best:.2f}")
