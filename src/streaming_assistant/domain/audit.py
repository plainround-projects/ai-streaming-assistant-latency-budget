"""The audit log as a hash chain: each entry carries the hash of the one before, so an edit, removal or reorder is found."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

GENESIS = "start"
SEPARATOR = "\x1f"


@dataclass(frozen=True, slots=True)
class AuditEntry:
    """One step of a run, with its place in the chain."""

    previous: str
    run: str
    step: str
    actor: str
    at: str
    content: str
    hash: str


def digest(previous: str, run: str, step: str, actor: str, at: str, content: str) -> str:
    """SHA-256 over the six fields, in a fixed order, joined by a separator that text does not contain."""
    return hashlib.sha256(SEPARATOR.join((previous, run, step, actor, at, content)).encode()).hexdigest()


def make_entry(previous_hash: str | None, run: str, step: str, actor: str, at: datetime, content: str) -> AuditEntry:
    """The next entry in the chain."""
    previous = previous_hash or GENESIS
    stamp = at.isoformat()
    return AuditEntry(previous, run, step, actor, stamp, content, digest(previous, run, step, actor, stamp, content))


def verify(entries: Sequence[AuditEntry]) -> int | None:
    """Index of the first entry that was edited, removed or reordered; None when the chain holds."""
    previous = GENESIS
    for index, entry in enumerate(entries):
        expected = digest(entry.previous, entry.run, entry.step, entry.actor, entry.at, entry.content)
        if entry.previous != previous or entry.hash != expected:
            return index
        previous = entry.hash
    return None
