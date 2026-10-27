"""Help-page sections and a small BM25-style scorer whose score is the share of the question the section covers."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

_WORD = re.compile(r"[a-z0-9]+")
STOP = frozenset(
    [
        "a",
        "an",
        "the",
        "i",
        "my",
        "me",
        "we",
        "you",
        "your",
        "is",
        "are",
        "was",
        "were",
        "be",
        "do",
        "does",
        "did",
        "can",
        "could",
        "would",
        "should",
        "how",
        "what",
        "when",
        "where",
        "why",
        "who",
        "which",
        "to",
        "of",
        "for",
        "in",
        "on",
        "at",
        "it",
        "this",
        "that",
        "and",
        "or",
        "if",
        "not",
        "no",
        "there",
        "any",
        "have",
        "has",
        "had",
        "with",
        "from",
        "by",
        "about",
        "as",
        "so",
        "than",
        "then",
        "please",
    ]
)
K1 = 1.4
B = 0.7


@dataclass(frozen=True, slots=True)
class Section:
    """One section of a help page; `anchor` is where a citation opens the page."""

    page_id: str
    page_title: str
    anchor: str
    heading: str
    text: str

    @property
    def ref(self) -> str:
        """The citation form: `page-07#refund-timing`."""
        return f"{self.page_id}#{self.anchor}"


@dataclass(frozen=True, slots=True)
class Hit:
    """A section the retriever returned, with its raw score and the share of the question's weight it covers."""

    section: Section
    score: float
    coverage: float


def terms(text: str) -> list[str]:
    """Lower-case content words (no stop words), with a crude plural fold."""
    return [
        word[:-1] if len(word) > 4 and word.endswith("s") else word
        for word in _WORD.findall(text.lower())
        if word not in STOP
    ]


class Bm25Index:
    """Built once from the sections. `search` returns the best sections; `coverage` is the idf weight of the query terms the
    section contains over the idf weight of all the query's terms. A term found nowhere in the help center weighs as much
    as the rarest known term, so a question about the weather does not look covered because one word matched."""

    def __init__(self, sections: Sequence[Section]) -> None:
        self._sections = list(sections)
        self._tf = [Counter(terms(f"{s.heading} {s.heading} {s.page_title} {s.text}")) for s in self._sections]
        self._lengths = [sum(tf.values()) for tf in self._tf]
        self._average = sum(self._lengths) / len(self._lengths) if self._lengths else 1.0
        document_frequency: Counter[str] = Counter()
        for tf in self._tf:
            document_frequency.update(tf.keys())
        count = len(self._sections)
        self._idf: Mapping[str, float] = {
            term: math.log(1 + (count - freq + 0.5) / (freq + 0.5)) for term, freq in document_frequency.items()
        }
        self._unknown_idf = max(self._idf.values(), default=1.0)

    def search(self, query: str, limit: int = 3) -> list[Hit]:
        """Best sections for the query, best first; sections sharing no term are left out."""
        wanted = terms(query)
        total = sum(self._idf.get(term, self._unknown_idf) for term in set(wanted)) or 1.0
        hits = []
        for index, section in enumerate(self._sections):
            tf, length = self._tf[index], self._lengths[index]
            score = coverage = 0.0
            for term in set(wanted):
                if term in tf:
                    idf = self._idf[term]
                    score += idf * tf[term] * (K1 + 1) / (tf[term] + K1 * (1 - B + B * length / self._average))
                    coverage += idf
            if score > 0:
                hits.append(Hit(section, score, coverage / total))
        hits.sort(key=lambda hit: (-hit.score, hit.section.ref))
        return hits[:limit]
