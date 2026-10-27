import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from streaming_assistant.application.assistant import STATES, Assistant, AssistantConfig, UnauthorizedError
from streaming_assistant.application.ports import Chunk, StreamRequest, TextDelta, Usage
from streaming_assistant.application.prompt import PROMPT_VERSION, assemble
from streaming_assistant.application.prompts import PromptFileError, parse_prompt_file
from streaming_assistant.application.review import ReviewDesk
from streaming_assistant.domain.audit import verify
from streaming_assistant.domain.errors import ProviderError, ReviewRejectedError, UnknownRunError
from streaming_assistant.domain.routing import Thresholds
from streaming_assistant.infrastructure.catalog import LazyBm25Retriever, PageCatalog
from streaming_assistant.infrastructure.clock import SystemClock
from streaming_assistant.infrastructure.scripted_stream import Pace, ScriptedStreamingModel
from streaming_assistant.infrastructure.sqlite_store import (
    Database,
    SqliteAudit,
    SqliteAuthenticator,
    SqliteRunStore,
)

ROOT = Path(__file__).resolve().parents[3]
SHIPPING = "A question about shipping times: standard delivery takes three to five business days after dispatch?"
OFF_TOPIC = "How do I tune a guitar string?"
REFUND_LATE = "Can I get a refund on an order from seventy five days ago?"
FAST = Pace(0, 0, 0, 0, jitter=0)
CUSTOMER = "demo-customer-token"
# `make trace` holds the sum to the lesson's 50 ms on a quiet machine; a unit test must not fail when the machine is busy.
TRACE_TOLERANCE_MS = 400


class Rig:
    """The assistant over real in-memory collaborators and a model the test chooses."""

    def __init__(self, model=None, **config):
        self.db = Database(":memory:")
        self.db.apply_scripts(ROOT / "sql")
        self.catalog = PageCatalog(ROOT / "data/help_pages.json")
        self.audit, self.runs = SqliteAudit(self.db), SqliteRunStore(self.db)
        self.model = model or ScriptedStreamingModel(FAST, hallucinate_every=0)
        stable = parse_prompt_file("answer", (ROOT / "prompts/answer.v1.md").read_text(encoding="utf-8")).text
        self.assistant = Assistant(
            LazyBm25Retriever(self.catalog),
            {"standard": self.model, "fast": self.model},
            self.runs,
            self.audit,
            SqliteAuthenticator(self.db),
            SystemClock(),
            AssistantConfig(stable_prompt=stable, **config),
            self.catalog,
        )
        self.desk = ReviewDesk(self.runs, self.audit, self.catalog, SystemClock())

    async def ask(self, question, run_id="run-1", token=CUSTOMER):
        prepared = await self.assistant.prepare(run_id, question, token)
        return [event async for event in self.assistant.stream(prepared)]


def names(events):
    return [event.name for event in events]


def state_of(events):
    return next(event.data for event in events if event.name == "state")


def test_an_answerable_question_streams_tokens_then_citations_then_done_with_usage_and_timings():
    events = asyncio.run(Rig().ask(SHIPPING))
    assert names(events)[0] == "token" and names(events)[-1] == "done"
    assert "citation" in names(events) and "[" not in "".join(e.data["text"] for e in events if e.name == "token")
    done = events[-1].data
    assert done["outcome"] == "answered" and done["usage"]["output_tokens"] > 0 and done["dropped_citations"] == 0
    timings = done["timings"]
    assert abs(timings["first_token_ms"] - timings["stage_sum_ms"]) < TRACE_TOLERANCE_MS


def test_the_stage_times_add_up_to_the_first_token_time_with_and_without_parallel_prep():
    for parallel in (True, False):
        done = asyncio.run(Rig(parallel_prep=parallel).ask(SHIPPING))[-1].data["timings"]
        assert abs(done["first_token_ms"] - done["stage_sum_ms"]) < TRACE_TOLERANCE_MS
        assert set(done) >= {"auth_ms", "retrieval_ms", "assembly_ms", "overlap_ms", "model_ms"}


@pytest.mark.parametrize(
    ("mode", "state"), [("provider_error", "provider_error"), ("rate_limited", "rate_limited"), ("refusal", "refusal")]
)
def test_a_provider_failure_gets_its_own_state_with_the_designed_message(mode, state):
    events = asyncio.run(Rig(ScriptedStreamingModel(FAST, mode=mode)).ask(SHIPPING))
    shown = state_of(events)
    assert shown["name"] == state and shown["message"] == STATES[state][0] and shown["action"] == STATES[state][1]
    assert "token" not in names(events) and events[-1].data["outcome"] == state


def test_a_model_that_never_answers_gets_the_timeout_state_at_the_first_token_deadline():
    rig = Rig(ScriptedStreamingModel(FAST, mode="timeout"), first_token_timeout_seconds=0.05)
    events = asyncio.run(rig.ask(SHIPPING))
    assert state_of(events)["name"] == "timeout" and rig.model.cancelled_at


def test_a_stream_that_stalls_after_the_first_token_hits_the_idle_timeout():
    class Stalls:
        async def stream(self, request: StreamRequest):
            yield TextDelta("Hello ")
            await asyncio.sleep(3600)
            yield Usage(1, 1)

    events = asyncio.run(Rig(Stalls(), idle_timeout_seconds=0.05).ask(SHIPPING))
    assert names(events)[0] == "token" and state_of(events)["name"] == "timeout"


def test_nothing_found_with_pausing_off_gets_the_no_evidence_state():
    events = asyncio.run(Rig(pause_enabled=False).ask(OFF_TOPIC))
    assert state_of(events)["name"] == "no_evidence" and "token" not in names(events)


def test_a_thin_match_gets_the_low_confidence_state_that_offers_a_rephrase():
    rig = Rig(thresholds=Thresholds(confident=1.5, pause_below=0.1))
    events = asyncio.run(rig.ask(SHIPPING))
    shown = state_of(events)
    assert shown["name"] == "low_confidence" and shown["action"] == "rephrase" and "token" not in names(events)


def test_stop_ends_the_stream_cancels_the_upstream_call_and_is_audited():
    slow = ScriptedStreamingModel(Pace(0, 0, 0, 30, jitter=0), hallucinate_every=0)
    rig = Rig(slow)

    async def go():
        rig.assistant.stops.request("run-1")
        return await rig.ask(SHIPPING)

    events = asyncio.run(go())
    assert state_of(events)["name"] == "stopped" and events[-1].data["outcome"] == "stopped"
    assert slow.cancelled_at and ("stopped", "customer") in [(e.step, e.actor) for e in rig.audit.entries("run-1")]
    assert not rig.assistant.stops.is_requested("run-1")


def test_a_closed_connection_cancels_the_upstream_call_and_is_audited_as_the_clients_doing():
    slow = ScriptedStreamingModel(Pace(0, 0, 0, 200, jitter=0), hallucinate_every=0)
    rig = Rig(slow)

    async def go():
        prepared = await rig.assistant.prepare("run-1", SHIPPING, CUSTOMER)

        async def consume():
            async for _ in rig.assistant.stream(prepared):
                pass

        task = asyncio.create_task(consume())
        await asyncio.sleep(0.15)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(go())
    assert slow.cancelled_at and ("stopped", "client") in [(e.step, e.actor) for e in rig.audit.entries("run-1")]
    assert rig.assistant.stats["disconnected"] == 1


def test_a_citation_to_a_page_that_was_not_retrieved_is_dropped_and_counted():
    rig = Rig(ScriptedStreamingModel(FAST, hallucinate_every=1))
    events = asyncio.run(rig.ask(SHIPPING))
    cited = [e.data["page_id"] for e in events if e.name == "citation"]
    assert "help-99" not in cited and cited and events[-1].data["dropped_citations"] == 1
    assert rig.assistant.stats["dropped_citations"] == 1


def test_a_should_pause_question_pauses_with_a_saved_run_and_an_audit_entry():
    rig = Rig()
    events = asyncio.run(rig.ask(REFUND_LATE))
    assert names(events) == ["paused", "done"] and events[0].data["reason"] == "policy_exception"
    saved = rig.runs.get("run-1")
    assert saved is not None and saved.status == "waiting" and saved.retrieved
    assert [e.step for e in rig.audit.entries("run-1")] == ["received", "paused"]


def test_off_topic_questions_pause_for_no_page_covers():
    events = asyncio.run(Rig().ask(OFF_TOPIC))
    assert names(events) == ["paused", "done"] and events[0].data["reason"] == "no_page_covers"


def test_a_reviewer_answer_is_validated_then_the_run_resumes_with_it_in_context_and_the_trail_verifies():
    rig = Rig()
    asyncio.run(rig.ask(REFUND_LATE))
    saved = rig.runs.get("run-1")
    assert saved is not None
    ref = saved.retrieved[0]
    for text, cited, message in (
        (" ", [ref], "empty"),
        ("Sure.", [], "cite a help section"),
        ("Sure.", ["help-99#nope"], "unknown section"),
    ):
        with pytest.raises(ReviewRejectedError, match=message):
            rig.desk.answer("run-1", "ana", text, cited, False)
    with pytest.raises(ReviewRejectedError, match="reviewer id"):
        rig.desk.answer("run-1", " ", "Sure.", [ref], False)
    assert rig.desk.status("run-1") == "waiting"
    answered = rig.desk.answer("run-1", "ana", "Store credit approved for the late return.", [ref], False)
    assert answered.status == "answered" and rig.desk.status("run-1") == "answered"
    with pytest.raises(ReviewRejectedError, match="not waiting"):
        rig.desk.answer("run-1", "ana", "Again.", [ref], False)

    async def resume():
        return [event async for event in rig.assistant.resume("run-1")]

    events = asyncio.run(resume())
    text = "".join(e.data["text"] for e in events if e.name == "token")
    assert "Store credit approved for the late return." in text and events[-1].data["outcome"] == "answered"
    assert [e.data["page_id"] for e in events if e.name == "citation"]
    assert rig.desk.status("run-1") == "resumed"
    steps = [e.step for e in rig.audit.entries("run-1")]
    assert steps == ["received", "paused", "answered", "validated", "resumed", "citations", "shown"]
    assert verify(rig.audit.entries()) is None


def test_a_reviewer_may_say_that_no_page_covers_the_question():
    rig = Rig()
    asyncio.run(rig.ask(OFF_TOPIC))
    assert rig.desk.answer("run-1", "ana", "We do not sell guitars.", [], True).no_page


def test_resuming_a_run_that_is_unknown_or_not_answered_is_refused():
    rig = Rig()
    asyncio.run(rig.ask(REFUND_LATE))

    async def resume(run_id):
        return [event async for event in rig.assistant.resume(run_id)]

    with pytest.raises(UnknownRunError):
        asyncio.run(resume("nope"))
    with pytest.raises(UnknownRunError, match="not answered"):
        asyncio.run(resume("run-1"))
    with pytest.raises(UnknownRunError):
        rig.desk.status("nope")
    with pytest.raises(UnknownRunError):
        rig.desk.answer("nope", "ana", "x", [], True)
    assert [run.run_id for run in rig.desk.waiting()] == ["run-1"]


def test_an_unknown_token_is_refused_on_both_prepare_paths():
    for parallel in (True, False):
        with pytest.raises(UnauthorizedError):
            asyncio.run(Rig(parallel_prep=parallel).ask(SHIPPING, token="wrong"))


def test_easy_questions_go_to_the_fast_tier_when_routing_is_on():
    seen = []

    class Spy(ScriptedStreamingModel):
        async def stream(self, request):
            seen.append(request.tier)
            async for chunk in super().stream(request):
                yield chunk

    asyncio.run(Rig(Spy(FAST, hallucinate_every=0), route_easy_to_fast=True).ask(SHIPPING))
    asyncio.run(Rig(Spy(FAST, hallucinate_every=0), route_easy_to_fast=False).ask(SHIPPING))
    assert seen == ["fast", "standard"]


def test_stable_text_goes_first_so_a_prefix_cache_can_apply():
    rig = Rig()
    hits = rig.assistant._retriever.search(SHIPPING, 3)
    stable_first = assemble("STABLE", hits, SHIPPING, stable_first=True, tier="standard")
    stable_last = assemble("STABLE", hits, SHIPPING, stable_first=False, tier="fast", reviewer_answer="Yes.")
    assert (
        stable_first.system == "STABLE"
        and SHIPPING in stable_first.user
        and stable_first.prompt_version == PROMPT_VERSION
    )
    assert stable_last.system.startswith("Passages:") and stable_last.tier == "fast" and "STABLE" in stable_last.system
    other = assemble("STABLE", hits[:1], "another question", stable_first=True, tier="standard")
    assert other.system == stable_first.system


def test_the_prompt_file_needs_both_fences_and_a_version_and_an_owner():
    ok = parse_prompt_file("answer", "---\nversion: v1\nowner: me\n---\nText.")
    assert (ok.version, ok.owner, ok.text) == ("v1", "me", "Text.")
    for bad in ("no fences", "---\nversion: v1\n---\nText.", "---\nowner: me\n---\nText."):
        with pytest.raises(PromptFileError):
            parse_prompt_file("answer", bad)


def test_a_failure_in_the_provider_before_any_token_is_mapped_by_the_assistant_not_leaked():
    class Boom:
        async def stream(self, request) -> AsyncIterator[Chunk]:
            raise ProviderError("down")
            yield  # pragma: no cover

    events = asyncio.run(Rig(Boom()).ask(SHIPPING))
    assert state_of(events)["name"] == "provider_error"


def test_the_questions_file_has_200_questions_and_20_should_pause():
    rows = [json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 200 and sum(row["should_pause"] for row in rows) == 20
