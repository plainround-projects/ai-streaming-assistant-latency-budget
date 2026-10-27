"""The boundaries the assistant talks through: the streaming model, the retriever, the stores, the clock."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from streaming_assistant.domain.audit import AuditEntry
from streaming_assistant.domain.retrieval import Hit, Section


@dataclass(frozen=True, slots=True)
class TextDelta:
    """A piece of the answer."""

    text: str


@dataclass(frozen=True, slots=True)
class Usage:
    """Token counts, sent when the stream ends normally."""

    input_tokens: int
    output_tokens: int


Chunk = TextDelta | Usage


@dataclass(frozen=True, slots=True)
class StreamRequest:
    """One streamed completion. `tier` lets a router send easy questions to a faster model."""

    system: str
    user: str
    prompt_version: str
    tier: str = "standard"


class StreamingModel(Protocol):
    """A model that streams. Raises `ProviderError`, `RateLimitedError` or `RefusedError`; closing the iterator cancels
    the upstream call."""

    def stream(self, request: StreamRequest) -> AsyncIterator[Chunk]:
        """Stream the answer."""
        ...


class Retriever(Protocol):
    """Finds the help sections for a question."""

    def search(self, query: str, limit: int = 3) -> list[Hit]:
        """Best sections first."""
        ...


@dataclass(frozen=True, slots=True)
class PausedRun:
    """A run waiting for, or past, a reviewer."""

    run_id: str
    question: str
    retrieved: tuple[str, ...]
    reason: str
    status: str
    reviewer_id: str | None = None
    answer: str | None = None
    cited: tuple[str, ...] = ()
    no_page: bool = False


class RunStore(Protocol):
    """Durable state of paused runs: it must survive a restart."""

    def save_pause(self, run: PausedRun, at: datetime) -> None:
        """Store a new paused run."""
        ...

    def get(self, run_id: str) -> PausedRun | None:
        """One run, or None."""
        ...

    def waiting(self, limit: int) -> Sequence[PausedRun]:
        """Runs waiting for a reviewer, oldest first."""
        ...

    def record_answer(
        self, run_id: str, reviewer_id: str, answer: str, cited: Sequence[str], no_page: bool, at: datetime
    ) -> None:
        """Store a validated reviewer answer and move the run to `answered`."""
        ...

    def mark_resumed(self, run_id: str, at: datetime) -> None:
        """Move the run to `resumed`."""
        ...


class AuditLog(Protocol):
    """An append-only, hash-chained log."""

    def append(self, run: str, step: str, actor: str, content: str) -> AuditEntry:
        """Add one step."""
        ...

    def entries(self, run: str | None = None) -> Sequence[AuditEntry]:
        """The whole chain, or the steps of one run (in chain order)."""
        ...


class Authenticator(Protocol):
    """Checks a bearer token."""

    def role_of(self, token: str) -> str | None:
        """'customer', 'reviewer', or None for an unknown token."""
        ...


class Catalog(Protocol):
    """The help pages by id: a reviewer can only cite what exists, and a citation opens the page at its section."""

    def section(self, ref: str) -> Section | None:
        """The section a `page#anchor` ref names, or None."""
        ...


class Clock(Protocol):
    """The current time."""

    def now(self) -> datetime:
        """Now, timezone-aware."""
        ...
