"""A scripted streaming model: configurable time to first token, prefill cost, token pace and failure, with counters.

It writes its answer from the passages in the prompt (the first sentence of the best passage, with its citation), so a run
has real text and real citations. Its latencies are settings, not measurements of any provider. It is not a model.
"""

from __future__ import annotations

import asyncio
import hashlib
import math
import re
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

from streaming_assistant.application.ports import Chunk, StreamRequest, TextDelta, Usage
from streaming_assistant.domain.errors import ProviderError, RateLimitedError, RefusedError

_PASSAGE = re.compile(r"^\[(help-\d+#[a-z0-9-]+)\] [^:]+: (.+)$", re.MULTILINE)
_REVIEWER = re.compile(r"Reviewer-validated answer: (.+)", re.DOTALL)


@dataclass(frozen=True, slots=True)
class Pace:
    """Latency settings in milliseconds."""

    ttft_standard_ms: float = 1300.0
    ttft_fast_ms: float = 350.0
    prefill_ms_per_1k_tokens: float = 400.0
    token_ms: float = 15.0
    cached_prefix_chars: int = 400
    jitter: float = 0.15


class ScriptedStreamingModel:
    """Async streaming with counters: tokens produced (what would be billed), cancellations and their times."""

    name = "scripted-streaming-model"

    def __init__(self, pace: Pace | None = None, mode: str = "ok", hallucinate_every: int = 25) -> None:
        self._pace = pace or Pace()
        self._mode = mode
        self._hallucinate_every = hallucinate_every
        self._cached_prefixes: set[str] = set()
        self.produced_tokens = 0
        self.cancelled_at: list[float] = []
        self.started = 0
        self.prefix_cache_hits = 0

    def _ttft(self, request: StreamRequest) -> float:
        prefix = hashlib.sha1(request.system[: self._pace.cached_prefix_chars].encode()).hexdigest()
        cached = prefix in self._cached_prefixes
        self._cached_prefixes.add(prefix)
        if cached:
            self.prefix_cache_hits += 1
        prompt_tokens = len(request.system + request.user) / 4
        uncached = (len(request.user) / 4) if cached else prompt_tokens
        base = self._pace.ttft_fast_ms if request.tier == "fast" else self._pace.ttft_standard_ms
        spread = (int(hashlib.sha1(request.user.encode()).hexdigest(), 16) % 1000) / 1000 * 2 - 1
        return (base + self._pace.prefill_ms_per_1k_tokens * uncached / 1000) * (1 + self._pace.jitter * spread)

    def _answer(self, request: StreamRequest) -> str:
        reviewer = _REVIEWER.search(request.user)
        passages = _PASSAGE.findall(request.user)
        if reviewer:
            refs = " ".join(f"[{ref}]" for ref, _ in passages[:1])
            return f"{reviewer.group(1).strip()} {refs}".strip()
        if not passages:
            return "I do not have a passage for that."
        ref, text = passages[0]
        sentence = text.split(". ")[0].rstrip(".") + "."
        answer = f"{sentence} [{ref}]"
        if (
            self._hallucinate_every
            and int(hashlib.sha1(request.user.encode()).hexdigest(), 16) % self._hallucinate_every == 0
        ):
            answer += " See also [help-99#made-up]."
        return answer

    async def stream(self, request: StreamRequest) -> AsyncIterator[Chunk]:
        """Wait for the first token, then emit the answer a word at a time."""
        self.started += 1
        if self._mode == "provider_error":
            raise ProviderError("scripted provider failure")
        if self._mode == "rate_limited":
            raise RateLimitedError("scripted 429")
        if self._mode == "refusal":
            raise RefusedError("scripted refusal")
        produced = 0
        try:
            if self._mode == "timeout":
                await asyncio.sleep(3600)
            await asyncio.sleep(self._ttft(request) / 1000)
            words = self._answer(request).split(" ")
            for index, word in enumerate(words):
                if index:
                    await asyncio.sleep(self._pace.token_ms / 1000)
                self.produced_tokens += 1
                produced += 1
                yield TextDelta(word + (" " if index < len(words) - 1 else ""))
            yield Usage(math.ceil(len(request.system + request.user) / 4), produced)
        except (asyncio.CancelledError, GeneratorExit):
            self.cancelled_at.append(time.perf_counter())
            raise
