"""The streaming assistant: prepare a request stage by stage (timed), then stream typed events with seven failure states,
a pause-for-approval path, real citations and an audit trail."""

from __future__ import annotations

import asyncio
import hashlib
import threading
import time
from collections import Counter
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from streaming_assistant.application.ports import (
    AuditLog,
    Authenticator,
    Catalog,
    Clock,
    PausedRun,
    Retriever,
    RunStore,
    StreamingModel,
    StreamRequest,
    TextDelta,
    Usage,
)
from streaming_assistant.application.prompt import assemble
from streaming_assistant.domain.citations import MarkerStripper, check_refs
from streaming_assistant.domain.errors import ProviderError, RateLimitedError, RefusedError, UnknownRunError
from streaming_assistant.domain.retrieval import Hit
from streaming_assistant.domain.routing import (
    ANSWER,
    LOW_CONFIDENCE,
    NO_EVIDENCE,
    PAUSE,
    Route,
    Thresholds,
    decide_route,
)

STATES: Mapping[str, tuple[str, str]] = {
    "timeout": ("The assistant took too long to start answering.", "retry"),
    "provider_error": ("Something went wrong on our side while answering.", "retry"),
    "rate_limited": ("We are getting a lot of questions right now. Please try again in a moment.", "retry"),
    "refusal": ("I can't help with that here. A person on the team can.", "contact"),
    "no_evidence": ("I could not find anything in the help center about that.", "contact"),
    "low_confidence": (
        "I found something related, but I am not sure it answers your question. Try rephrasing it.",
        "rephrase",
    ),
    "stopped": ("Stopped. Nothing more will be shown.", "retry"),
}


class UnauthorizedError(Exception):
    """The bearer token is missing or unknown."""


@dataclass(frozen=True, slots=True)
class Event:
    """One server-sent event: a type name and its data."""

    name: str
    data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class AssistantConfig:
    """Behavior switches. The last four are the load test's levers (each one is a fix measured against the baseline)."""

    stable_prompt: str
    thresholds: Thresholds = field(default_factory=Thresholds)
    first_token_timeout_seconds: float = 3.0
    idle_timeout_seconds: float = 5.0
    pause_enabled: bool = True
    retrieval_limit: int = 3
    stable_prefix_first: bool = True
    parallel_prep: bool = True
    route_easy_to_fast: bool = False
    easy_coverage: float = 0.8


class StopRegistry:
    """Run ids a user asked to stop, safe to use from any thread."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stopped: set[str] = set()

    def request(self, run_id: str) -> None:
        """Ask for a run to stop."""
        with self._lock:
            self._stopped.add(run_id)

    def is_requested(self, run_id: str) -> bool:
        """True once a stop was asked for."""
        with self._lock:
            return run_id in self._stopped

    def clear(self, run_id: str) -> None:
        """Forget a run."""
        with self._lock:
            self._stopped.discard(run_id)


@dataclass
class Prepared:
    """Everything decided before the first byte: who, what was retrieved, the route, the prompt and the stage times."""

    run_id: str
    question: str
    hits: list[Hit]
    route: Route
    request: StreamRequest | None
    timings: dict[str, float]
    started: float
    extra_refs: tuple[str, ...] = ()
    reviewer_answer: str | None = None


def _timed[T](function: Callable[[], T]) -> tuple[T, float]:
    started = time.perf_counter()
    result = function()
    return result, (time.perf_counter() - started) * 1000


class Assistant:
    """Orchestrates one request. Collaborators arrive through ports so tests can force every state."""

    def __init__(
        self,
        retriever: Retriever,
        models: Mapping[str, StreamingModel],
        runs: RunStore,
        audit: AuditLog,
        authenticator: Authenticator,
        clock: Clock,
        config: AssistantConfig,
        catalog: Catalog,
        stops: StopRegistry | None = None,
    ) -> None:
        self._retriever = retriever
        self._models = models
        self._runs = runs
        self._audit = audit
        self._auth = authenticator
        self._clock = clock
        self._config = config
        self._catalog = catalog
        self._stops = stops or StopRegistry()
        self.stats: Counter[str] = Counter()

    @property
    def stops(self) -> StopRegistry:
        """The registry the stop endpoint writes to."""
        return self._stops

    async def prepare(self, run_id: str, question: str, token: str) -> Prepared:
        """Authenticate, retrieve, assemble and route; each stage is timed inside the real path.

        With `parallel_prep` the authentication and the retrieval run at the same time; `overlap_ms` is the time that
        saved, so the stage times still add up to the measured total.
        """
        started = time.perf_counter()
        limit = self._config.retrieval_limit
        if self._config.parallel_prep:
            (role, auth_ms), (hits, retrieval_ms) = await asyncio.gather(
                asyncio.to_thread(_timed, lambda: self._auth.role_of(token)),
                asyncio.to_thread(_timed, lambda: self._retriever.search(question, limit)),
            )
        else:
            role, auth_ms = await asyncio.to_thread(_timed, lambda: self._auth.role_of(token))
            if role is None:
                raise UnauthorizedError
            hits, retrieval_ms = await asyncio.to_thread(_timed, lambda: self._retriever.search(question, limit))
        if role is None:
            raise UnauthorizedError
        wall_ms = (time.perf_counter() - started) * 1000
        overlap_ms = max(0.0, auth_ms + retrieval_ms - wall_ms)
        route = decide_route(question, hits, self._config.thresholds, pause_enabled=self._config.pause_enabled)
        request, assembly_ms = None, 0.0
        if route.kind == ANSWER:
            tier = (
                "fast"
                if self._config.route_easy_to_fast and hits[0].coverage >= self._config.easy_coverage
                else "standard"
            )
            request, assembly_ms = _timed(
                lambda: assemble(
                    self._config.stable_prompt, hits, question, stable_first=self._config.stable_prefix_first, tier=tier
                )
            )
        timings = {
            "auth_ms": auth_ms,
            "retrieval_ms": retrieval_ms,
            "assembly_ms": assembly_ms,
            "overlap_ms": overlap_ms,
        }
        return Prepared(run_id, question, hits, route, request, timings, started)

    async def stream(self, prepared: Prepared) -> AsyncIterator[Event]:
        """Typed events for one run. The stream always ends with `done`, `paused` or a `state` followed by `done`."""
        run_id = prepared.run_id
        self._audit.append(
            run_id,
            "received",
            "customer",
            "question sha256:" + hashlib.sha256(prepared.question.encode()).hexdigest()[:12],
        )
        route = prepared.route
        if route.kind == PAUSE:
            self._runs.save_pause(
                PausedRun(
                    run_id, prepared.question, tuple(hit.section.ref for hit in prepared.hits), route.reason, "waiting"
                ),
                self._clock.now(),
            )
            self._audit.append(run_id, "paused", "assistant", route.reason)
            self.stats["paused"] += 1
            yield Event(
                "paused",
                {
                    "run_id": run_id,
                    "reason": route.reason,
                    "message": "A person on the team will check this and the answer will appear here.",
                },
            )
            yield self._done(prepared, None, 0, "paused")
            return
        if route.kind in (LOW_CONFIDENCE, NO_EVIDENCE):
            self._audit.append(run_id, "state", "assistant", route.kind)
            self.stats[route.kind] += 1
            yield self._state(route.kind)
            yield self._done(prepared, None, 0, route.kind)
            return
        async for event in self._answer(prepared):
            yield event

    async def resume(self, run_id: str) -> AsyncIterator[Event]:
        """Continue a paused run whose reviewer answer was validated; the answer goes into the model's context."""
        run = self._runs.get(run_id)
        if run is None:
            raise UnknownRunError(run_id)
        if run.status != "answered" or run.answer is None:
            raise UnknownRunError(f"{run_id} is {run.status}, not answered")
        started = time.perf_counter()
        hits, retrieval_ms = await asyncio.to_thread(
            _timed, lambda: self._retriever.search(run.question, self._config.retrieval_limit)
        )
        request = assemble(
            self._config.stable_prompt,
            hits,
            run.question,
            stable_first=True,
            tier="standard",
            reviewer_answer=run.answer,
        )
        prepared = Prepared(
            run_id,
            run.question,
            hits,
            Route(ANSWER, "reviewer answer"),
            request,
            {"auth_ms": 0.0, "retrieval_ms": retrieval_ms, "assembly_ms": 0.0, "overlap_ms": 0.0},
            started,
            run.cited,
            run.answer,
        )
        self._audit.append(run_id, "resumed", "assistant", f"reviewer {run.reviewer_id}")
        self._runs.mark_resumed(run_id, self._clock.now())
        async for event in self._answer(prepared):
            yield event

    async def _answer(self, prepared: Prepared) -> AsyncIterator[Event]:
        run_id, request = prepared.run_id, prepared.request
        assert request is not None
        model = self._models[request.tier]
        strip, parts = MarkerStripper(), []
        usage: Usage | None = None
        first_token_ms = None
        call_started = time.perf_counter()
        upstream = model.stream(request).__aiter__()
        failure: str | None = None
        try:
            while True:
                timeout = (
                    self._config.first_token_timeout_seconds
                    if first_token_ms is None
                    else self._config.idle_timeout_seconds
                )
                try:
                    chunk = await asyncio.wait_for(upstream.__anext__(), timeout)
                except StopAsyncIteration:
                    break
                except TimeoutError:
                    failure = "timeout"
                    break
                except RateLimitedError:
                    failure = "rate_limited"
                    break
                except RefusedError:
                    failure = "refusal"
                    break
                except ProviderError:
                    failure = "provider_error"
                    break
                if isinstance(chunk, Usage):
                    usage = chunk
                    continue
                assert isinstance(chunk, TextDelta)
                visible = strip.feed(chunk.text)
                if visible:
                    if first_token_ms is None:
                        first_token_ms = (time.perf_counter() - prepared.started) * 1000
                        prepared.timings["model_ms"] = (time.perf_counter() - call_started) * 1000
                    parts.append(visible)
                    yield Event("token", {"text": visible})
                if self._stops.is_requested(run_id):
                    await self._close(upstream)
                    self._audit.append(run_id, "stopped", "customer", "stop requested")
                    self.stats["stopped"] += 1
                    yield self._state("stopped")
                    yield self._done(prepared, usage, len("".join(parts).split()), "stopped", first_token_ms)
                    return
        except asyncio.CancelledError:
            self._audit.append(run_id, "stopped", "client", "connection closed")
            self.stats["disconnected"] += 1
            raise
        finally:
            await self._close(upstream)
            self._stops.clear(run_id)
        if failure is not None:
            self._audit.append(run_id, "state", "assistant", failure)
            self.stats[failure] += 1
            yield self._state(failure)
            yield self._done(prepared, usage, 0, failure, first_token_ms)
            return
        tail = strip.finish()
        if tail:
            parts.append(tail)
            yield Event("token", {"text": tail})
        allowed = {hit.section.ref: hit.section for hit in prepared.hits}
        for ref in prepared.extra_refs:
            section = self._catalog.section(ref)
            if section is not None:
                allowed[ref] = section
        shown, dropped = check_refs(strip.refs, allowed)
        for section in shown:
            yield Event(
                "citation",
                {
                    "page_id": section.page_id,
                    "title": section.page_title,
                    "section": section.heading,
                    "anchor": section.anchor,
                    "url": f"/pages/{section.page_id}#{section.anchor}",
                },
            )
        self.stats["dropped_citations"] += dropped
        self.stats["answered"] += 1
        self._audit.append(run_id, "citations", "assistant", f"shown={len(shown)} dropped={dropped}")
        self._audit.append(run_id, "shown", "assistant", "".join(parts))
        yield self._done(prepared, usage, len("".join(parts).split()), "answered", first_token_ms, dropped)

    @staticmethod
    async def _close(upstream: Any) -> None:
        close = getattr(upstream, "aclose", None)
        if close is not None:
            await asyncio.shield(close())

    @staticmethod
    def _state(name: str) -> Event:
        message, action = STATES[name]
        return Event("state", {"name": name, "message": message, "action": action})

    @staticmethod
    def _done(
        prepared: Prepared,
        usage: Usage | None,
        words: int,
        outcome: str,
        first_token_ms: float | None = None,
        dropped: int = 0,
    ) -> Event:
        timings = {key: round(value, 2) for key, value in prepared.timings.items()}
        if first_token_ms is not None:
            timings["first_token_ms"] = round(first_token_ms, 2)
            timings["stage_sum_ms"] = round(
                timings["auth_ms"]
                + timings["retrieval_ms"]
                - timings["overlap_ms"]
                + timings["assembly_ms"]
                + timings.get("model_ms", 0.0),
                2,
            )
        return Event(
            "done",
            {
                "run_id": prepared.run_id,
                "outcome": outcome,
                "dropped_citations": dropped,
                "words": words,
                "usage": {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens} if usage else None,
                "timings": timings,
            },
        )
