"""The review desk: a human support agent answers a paused run, and the answer is validated before it can be used."""

from __future__ import annotations

from collections.abc import Sequence

from streaming_assistant.application.ports import AuditLog, Catalog, Clock, PausedRun, RunStore
from streaming_assistant.domain.errors import ReviewRejectedError, UnknownRunError


class ReviewDesk:
    """Lists waiting runs and validates a reviewer's answer: not empty, and either citing a real section or saying that
    no page covers the question. An unvalidated answer must never reach the model's context."""

    def __init__(self, runs: RunStore, audit: AuditLog, catalog: Catalog, clock: Clock) -> None:
        self._runs = runs
        self._audit = audit
        self._catalog = catalog
        self._clock = clock

    def waiting(self, limit: int = 50) -> Sequence[PausedRun]:
        """Runs waiting for a reviewer, oldest first."""
        return self._runs.waiting(limit)

    def status(self, run_id: str) -> str:
        """The run's status: waiting, answered or resumed."""
        run = self._runs.get(run_id)
        if run is None:
            raise UnknownRunError(run_id)
        return run.status

    def answer(self, run_id: str, reviewer_id: str, answer: str, cited: Sequence[str], no_page: bool) -> PausedRun:
        """Validate and store the reviewer's answer; raises `ReviewRejectedError` with the reason when it is not allowed."""
        run = self._runs.get(run_id)
        if run is None:
            raise UnknownRunError(run_id)
        if run.status != "waiting":
            raise ReviewRejectedError(f"run {run_id} is {run.status}, not waiting for a reviewer")
        if not reviewer_id.strip():
            raise ReviewRejectedError("a reviewer id is required")
        if not answer.strip():
            raise ReviewRejectedError("the answer must not be empty")
        unknown = [ref for ref in cited if self._catalog.section(ref) is None]
        if unknown:
            raise ReviewRejectedError(f"unknown section(s): {', '.join(unknown)}")
        if not cited and not no_page:
            raise ReviewRejectedError("cite a help section, or say that no page covers this question")
        self._audit.append(run_id, "answered", reviewer_id.strip(), answer.strip())
        self._runs.record_answer(run_id, reviewer_id.strip(), answer.strip(), tuple(cited), no_page, self._clock.now())
        self._audit.append(run_id, "validated", "system", f"cited={','.join(cited) or 'none'} no_page={no_page}")
        stored = self._runs.get(run_id)
        assert stored is not None
        return stored
