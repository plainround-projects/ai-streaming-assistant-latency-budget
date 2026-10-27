"""Measurements that need a running server or the whole question set: the 200 questions, Stop, the budget under load."""

import asyncio
import json
import os
import socket
import statistics
import subprocess
import sys
import threading
import time
from dataclasses import replace

import httpx
import uvicorn

from streaming_assistant.application.assistant import Event
from streaming_assistant.domain.stats import percentile
from streaming_assistant.infrastructure.scripted_stream import Pace, ScriptedStreamingModel
from streaming_assistant.infrastructure.settings import Settings
from streaming_assistant.interfaces.http import create_app
from streaming_assistant.interfaces.wiring import Components, build_components

CUSTOMER = {"Authorization": "Bearer demo-customer-token"}


async def collect(
    components: Components, run_id: str, question: str, token: str = "demo-customer-token"
) -> tuple[list[Event], list[str]]:
    """Run one question in process; returns the events and the refs that were retrieved for it."""
    prepared = await components.assistant.prepare(run_id, question, token)
    return [event async for event in components.assistant.stream(prepared)], [hit.section.ref for hit in prepared.hits]


async def trace_one(components: Components, question: str) -> dict[str, float]:
    """One request's stage times from the real path."""
    events, _ = await collect(components, "run-trace", question)
    done = next(event.data for event in events if event.name == "done")
    return dict(done["timings"])


async def evaluate_questions(components: Components) -> dict[str, object]:
    """All 200 questions: pauses, false pauses, citations shown outside the retrieved set, dropped citations."""
    questions = [
        json.loads(line)
        for line in (components.settings.root / "data/questions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    paused_should = paused_other = outside = right_page = answered = 0
    for number, item in enumerate(questions):
        events, retrieved = await collect(components, f"run-q{number:03d}", item["question"])
        names = [event.name for event in events]
        if "paused" in names:
            paused_should += item["should_pause"]
            paused_other += not item["should_pause"]
            continue
        shown = [event.data for event in events if event.name == "citation"]
        outside += sum(f"{c['page_id']}#{c['anchor']}" not in retrieved for c in shown)
        if not item["should_pause"]:
            answered += "token" in names
            right_page += any(c["page_id"] == item["expected_page"] for c in shown)
    should = sum(q["should_pause"] for q in questions)
    return {
        "questions": len(questions),
        "should_pause": should,
        "paused_of_should": paused_should,
        "paused_of_others": paused_other,
        "others": len(questions) - should,
        "false_pause_rate": paused_other / (len(questions) - should),
        "answered": answered,
        "citation_on_expected_page": right_page,
        "citations_outside_retrieved": outside,
        "dropped_citations": components.assistant.stats["dropped_citations"],
    }


def free_port() -> int:
    """A port nothing is listening on (the measurements must not collide with services already on the machine)."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class RunningServer:
    """uvicorn in a thread, for tests of behavior over a real socket."""

    def __init__(self, components: Components, port: int) -> None:
        app = create_app(
            components.assistant, components.desk, components.catalog, components.authenticator, components.audit
        )
        self._server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self.base = f"http://127.0.0.1:{port}"

    def __enter__(self) -> "RunningServer":
        self._thread.start()
        for _ in range(100):
            try:
                if httpx.get(self.base + "/healthz", timeout=1).status_code == 200:
                    return self
            except httpx.HTTPError:
                time.sleep(0.05)
        raise RuntimeError("server did not start")

    def __exit__(self, *exc: object) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=10)


async def first_event(client: httpx.AsyncClient, question: str) -> float:
    """Seconds from sending the request until the first `token` event line arrives."""
    started = time.perf_counter()
    elapsed = float("nan")
    async with client.stream("POST", "/ask", json={"question": question}, headers=CUSTOMER) as response:
        async for line in response.aiter_lines():  # read to the end so the connection closes cleanly
            if line == "event: token" and elapsed != elapsed:  # NaN until the first token line
                elapsed = time.perf_counter() - started
    return elapsed


async def stop_test(settings: Settings) -> dict[str, object]:
    """Close the connection after 3 tokens and look at the upstream call; then time an unrelated request."""
    model = ScriptedStreamingModel(
        Pace(ttft_standard_ms=80, ttft_fast_ms=40, prefill_ms_per_1k_tokens=0, token_ms=120, jitter=0)
    )
    components = build_components(replace(settings, database=":memory:"), model=model, fresh=True)
    question = "A question about shipping times: standard delivery takes three to five business days after dispatch?"
    with RunningServer(components, free_port()) as server:
        async with httpx.AsyncClient(base_url=server.base, timeout=30) as client:
            baseline = [await first_event(client, question) for _ in range(5)]
            tokens = 0
            closed_at = 0.0
            async with client.stream("POST", "/ask", json={"question": question}, headers=CUSTOMER) as response:
                async for line in response.aiter_lines():
                    if line == "event: token":
                        tokens += 1
                    if tokens == 3:
                        closed_at = time.perf_counter()
                        break
            cancelled = 0.0
            for _ in range(100):
                await asyncio.sleep(0.01)
                if model.cancelled_at:
                    cancelled = model.cancelled_at[-1]
                    break
            produced_then = model.produced_tokens
            await asyncio.sleep(0.8)
            produced_later = model.produced_tokens
            fresh = await first_event(
                client, "A question about gift wrapping: gift wrap is a checkout option for a small fee?"
            )
    return {
        "tokens_before_close": tokens,
        "upstream_cancelled_after_ms": round((cancelled - closed_at) * 1000, 1) if cancelled else None,
        "billed_tokens_when_cancelled": produced_then,
        "billed_tokens_800ms_later": produced_later,
        "baseline_first_token_ms": round(statistics.median(baseline) * 1000, 1),
        "fresh_request_after_stop_ms": round(fresh * 1000, 1),
    }


CONFIGS: dict[str, dict[str, str]] = {
    "baseline": {
        "STABLE_PREFIX_FIRST": "off",
        "PARALLEL_PREP": "off",
        "CACHE_RETRIEVAL": "off",
        "ROUTE_EASY_TO_FAST": "off",
        "WARM_INDEX": "off",
    },
    "stable text first (prompt cache can apply)": {
        "STABLE_PREFIX_FIRST": "on",
        "PARALLEL_PREP": "off",
        "CACHE_RETRIEVAL": "off",
        "ROUTE_EASY_TO_FAST": "off",
        "WARM_INDEX": "off",
    },
    "+ parallel prep, cached retrieval, warm index": {
        "STABLE_PREFIX_FIRST": "on",
        "PARALLEL_PREP": "on",
        "CACHE_RETRIEVAL": "on",
        "ROUTE_EASY_TO_FAST": "off",
        "WARM_INDEX": "on",
    },
    "+ easy questions to the small model": {
        "STABLE_PREFIX_FIRST": "on",
        "PARALLEL_PREP": "on",
        "CACHE_RETRIEVAL": "on",
        "ROUTE_EASY_TO_FAST": "on",
        "WARM_INDEX": "on",
    },
}


async def drive(base: str, questions: list[str], rps: float, duration: float) -> tuple[list[float], list[float], int]:
    """Send requests at a steady rate; returns client first-token seconds, server first-token ms and the request count."""
    client_times: list[float] = []
    server_times: list[float] = []

    async def one(client: httpx.AsyncClient, question: str) -> None:
        started = time.perf_counter()
        async with client.stream("POST", "/ask", json={"question": question}, headers=CUSTOMER) as response:
            seen_first = False
            event = ""
            async for line in response.aiter_lines():
                if line.startswith("event: "):
                    event = line[7:]
                    if event == "token" and not seen_first:
                        client_times.append(time.perf_counter() - started)
                        seen_first = True
                elif line.startswith("data: ") and event == "done":
                    done = json.loads(line[6:])
                    if "first_token_ms" in done["timings"]:
                        server_times.append(done["timings"]["first_token_ms"])

    async with httpx.AsyncClient(base_url=base, timeout=60) as client:
        tasks = []
        total = int(rps * duration)
        started = time.perf_counter()
        for index in range(total):
            tasks.append(asyncio.create_task(one(client, questions[index % len(questions)])))
            delay = started + (index + 1) / rps - time.perf_counter()
            if delay > 0:
                await asyncio.sleep(delay)
        await asyncio.gather(*tasks)
    return client_times, server_times, total


def load_test(settings: Settings, rps: float, duration: float) -> list[dict[str, object]]:
    """Replay the answerable questions at `rps` for `duration` seconds against a server per configuration."""
    root = settings.root
    questions = [
        item["question"]
        for item in (
            json.loads(line) for line in (root / "data/questions.jsonl").read_text(encoding="utf-8").splitlines()
        )
        if not item["should_pause"]
    ]
    results = []
    for name, flags in CONFIGS.items():
        port = free_port()
        env = {
            **os.environ,
            **flags,
            "PROJECT_ROOT": str(root),
            "PORT": str(port),
            "DATABASE": ":memory:",
            "LOG_LEVEL": "WARNING",
        }
        server = subprocess.Popen(
            [sys.executable, "-m", "streaming_assistant.interfaces.cli", "serve"], env=env, cwd=root
        )
        try:
            for _ in range(200):
                try:
                    if httpx.get(f"http://127.0.0.1:{port}/healthz", timeout=1).status_code == 200:
                        break
                except httpx.HTTPError:
                    time.sleep(0.1)
            client_times, server_times, total = asyncio.run(drive(f"http://127.0.0.1:{port}", questions, rps, duration))
        finally:
            server.terminate()
            server.wait(timeout=20)
        results.append(
            {
                "config": name,
                "requests": total,
                "server_p50_ms": round(percentile(server_times, 0.5), 1),
                "server_p95_ms": round(percentile(server_times, 0.95), 1),
                "client_p50_ms": round(percentile(client_times, 0.5) * 1000, 1),
                "client_p95_ms": round(percentile(client_times, 0.95) * 1000, 1),
                "budget_ms": settings.first_token_budget_ms,
            }
        )
    return results
