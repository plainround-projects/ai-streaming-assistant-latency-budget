import asyncio
import io
import json
import logging
import random
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from streaming_assistant.application.ports import PausedRun, StreamRequest, TextDelta, Usage
from streaming_assistant.domain.audit import verify
from streaming_assistant.domain.errors import ProviderError, RateLimitedError, RefusedError
from streaming_assistant.infrastructure.catalog import CachingRetriever, LazyBm25Retriever, PageCatalog
from streaming_assistant.infrastructure.claude_stream import ClaudeStreamingModel
from streaming_assistant.infrastructure.environment import (
    ConfigurationError,
    read_choice,
    read_float,
    read_int,
    read_optional,
    read_text,
)
from streaming_assistant.infrastructure.logging import LogfmtFormatter, configure_logging, fields
from streaming_assistant.infrastructure.recorded_stream import (
    MissingRecordingError,
    RecordedStreamingModel,
    RecordingStreamingModel,
)
from streaming_assistant.infrastructure.retry import retry
from streaming_assistant.infrastructure.scripted_stream import Pace, ScriptedStreamingModel
from streaming_assistant.infrastructure.settings import Settings
from streaming_assistant.infrastructure.shutdown import ShutdownSignal
from streaming_assistant.infrastructure.sqlite_store import (
    Database,
    SqliteAudit,
    SqliteAuthenticator,
    SqliteRunStore,
    token_hash,
)

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)


@pytest.fixture
def db():
    database = Database(":memory:")
    database.apply_scripts(ROOT / "sql")
    return database


def test_demo_tokens_are_stored_as_hashes_and_map_to_roles(db):
    auth = SqliteAuthenticator(db)
    assert auth.role_of("demo-customer-token") == "customer" and auth.role_of("demo-reviewer-token") == "reviewer"
    assert auth.role_of("nope") is None and auth.role_of("") is None
    assert token_hash("demo-customer-token") in {row[0] for row in db.execute("SELECT token_hash FROM api_tokens")}
    assert "demo-customer-token" not in json.dumps(db.execute("SELECT * FROM api_tokens"))


def test_applying_the_scripts_twice_leaves_one_clean_database(db):
    SqliteAudit(db).append("run-1", "received", "customer", "hello")
    db.apply_scripts(ROOT / "sql")
    assert db.execute("SELECT COUNT(*) FROM audit_log") == [(0,)] and db.execute("SELECT COUNT(*) FROM api_tokens") == [
        (2,)
    ]


def test_a_failed_statement_rolls_back_and_the_database_stays_usable(db):
    with pytest.raises(Exception, match="no such table"):
        db.execute("SELECT * FROM missing_table")
    assert db.execute("SELECT 1") == [(1,)]


def test_paused_runs_survive_a_reopen_of_the_same_file(tmp_path):
    path = tmp_path / "assistant.sqlite"
    first = Database(path)
    first.apply_scripts(ROOT / "sql")
    SqliteRunStore(first).save_pause(PausedRun("run-1", "q?", ("help-01#a",), "no_page_covers", "waiting"), NOW)
    SqliteAudit(first).append("run-1", "paused", "assistant", "no_page_covers")
    first.close()
    second = Database(path)
    runs = SqliteRunStore(second)
    saved = runs.get("run-1")
    assert saved is not None and saved.retrieved == ("help-01#a",) and saved.status == "waiting"
    runs.record_answer("run-1", "ana", "Answer.", ["help-01#a"], False, NOW)
    runs.mark_resumed("run-1", NOW)
    done = runs.get("run-1")
    assert done is not None and (done.status, done.reviewer_id, done.cited, done.no_page) == (
        "resumed",
        "ana",
        ("help-01#a",),
        False,
    )
    assert runs.waiting(10) == [] and runs.get("nope") is None
    assert verify(SqliteAudit(second).entries()) is None


def test_the_audit_chain_in_the_database_breaks_at_an_edited_row_and_a_deleted_row(db):
    audit = SqliteAudit(db)
    for step in ("received", "paused", "answered", "shown"):
        audit.append("run-1", step, "actor", f"content of {step}")
    audit.append("run-2", "received", "actor", "another run")
    assert verify(audit.entries()) is None and len(audit.entries("run-1")) == 4
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("UPDATE audit_log SET content = 'Approve a full refund' WHERE seq = 2")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("DELETE FROM audit_log WHERE seq = 2")
    # someone with raw access drops the guards and edits anyway: the chain still shows where
    db.execute("DROP TRIGGER audit_log_no_update")
    db.execute("DROP TRIGGER audit_log_no_delete")
    db.execute("UPDATE audit_log SET content = 'Approve a full refund' WHERE seq = 2")
    assert verify(audit.entries()) == 1
    db.apply_scripts(ROOT / "sql")
    for step in ("received", "paused", "answered"):
        audit.append("run-1", step, "actor", step)
    db.execute("DROP TRIGGER audit_log_no_delete")
    db.execute("DELETE FROM audit_log WHERE seq = 2")
    assert verify(audit.entries()) == 1


def test_the_catalog_serves_pages_with_an_anchor_per_section_and_escapes_text():
    catalog = PageCatalog(ROOT / "data/help_pages.json")
    assert len(catalog.sections) > 30 and catalog.section("help-99#nope") is None
    first = catalog.sections[0]
    page = catalog.page_html(first.page_id)
    assert page is not None and f'id="{first.anchor}"' in page and ":target" in page
    assert catalog.page_html("help-99") is None and catalog.section(first.ref) == first


def test_the_cold_retriever_builds_its_index_on_the_first_search_and_a_warm_one_does_not():
    catalog = PageCatalog(ROOT / "data/help_pages.json")
    cold = LazyBm25Retriever(catalog)
    assert cold.build_seconds is None
    cold.search("shipping times")
    assert cold.build_seconds is not None
    warm = LazyBm25Retriever(catalog)
    warm.warm()
    built = warm.build_seconds
    warm.search("shipping times")
    assert warm.build_seconds == built


def test_the_retrieval_cache_counts_hits_misses_and_evicts_the_oldest():
    cache = CachingRetriever(LazyBm25Retriever(PageCatalog(ROOT / "data/help_pages.json")), size=2)
    cache.search("shipping times")
    cache.search("  Shipping   TIMES ")
    cache.search("refund timing")
    cache.search("gift wrap")
    cache.search("shipping times")
    assert (cache.hits, cache.misses) == (1, 4)


def request(text="Question: hi"):
    return StreamRequest("system text", text, "answer.v1", "standard")


async def collect(model, req):
    return [chunk async for chunk in model.stream(req)]


def test_the_scripted_model_cites_the_first_passage_and_counts_cached_prefixes():
    model = ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0), hallucinate_every=0)
    req = StreamRequest(
        "stable " * 100,
        "Passages:\n[help-01#shipping-times] Shipping times: Standard delivery takes three days. Extra.\nQuestion: how long?",
        "answer.v1",
    )
    chunks = asyncio.run(collect(model, req))
    text = "".join(c.text for c in chunks if isinstance(c, TextDelta))
    assert text.strip() == "Standard delivery takes three days. [help-01#shipping-times]" and isinstance(
        chunks[-1], Usage
    )
    asyncio.run(collect(model, req))
    assert model.prefix_cache_hits == 1 and model.produced_tokens > 0 and model.started == 2
    no_passage = asyncio.run(collect(model, StreamRequest("s", "Question: x", "answer.v1")))
    assert "do not have a passage" in "".join(c.text for c in no_passage if isinstance(c, TextDelta))


def test_the_scripted_model_hallucinates_a_citation_now_and_then_when_asked_to():
    model = ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0), hallucinate_every=1)
    text = "".join(
        c.text
        for c in asyncio.run(collect(model, request("Passages:\n[help-01#a] H: T.\nQuestion: q")))
        if isinstance(c, TextDelta)
    )
    assert "[help-99#made-up]" in text


def test_a_recording_replays_and_a_missing_one_says_how_to_record(tmp_path):
    path = tmp_path / "cassette.json"
    inner = ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0), hallucinate_every=0)
    recorder = RecordingStreamingModel(inner, path, "m", "authored")
    req = request("Passages:\n[help-01#a] H: Text here.\nQuestion: q")
    original = asyncio.run(collect(recorder, req))
    replay = RecordedStreamingModel(path)
    assert asyncio.run(collect(replay, req)) == original and replay.provenance == "authored" and replay.model_id == "m"
    with pytest.raises(MissingRecordingError, match="make record"):
        asyncio.run(collect(replay, request("Question: something else")))
    with pytest.raises(MissingRecordingError):
        asyncio.run(collect(replay, StreamRequest(req.system, req.user, "answer.v2")))


def test_the_committed_cassette_replays_its_samples_and_says_it_is_not_a_model_recording():
    replay = RecordedStreamingModel(ROOT / "tests/fixtures/cassettes/stream-v1.json")
    assert "not a model recording" in replay.provenance


class FakeStream:
    def __init__(self, texts, stop_reason="end_turn", error=None):
        self.text_stream = self._texts(texts, error)
        self._stop = stop_reason

    @staticmethod
    async def _texts(texts, error):
        for text in texts:
            yield text
        if error:
            raise error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get_final_message(self):
        return SimpleNamespace(stop_reason=self._stop, usage=SimpleNamespace(input_tokens=11, output_tokens=7))


class FakeClient:
    def __init__(self, stream):
        self.calls = []
        self.messages = SimpleNamespace(stream=self._stream)
        self._next = stream

    def _stream(self, **kwargs):
        self.calls.append(kwargs)
        return self._next


def claude(stream):
    client = FakeClient(stream)
    return ClaudeStreamingModel(
        {"standard": "claude-sonnet-5-5", "fast": "claude-haiku-5-5"}, "key", client=client
    ), client


def test_the_claude_adapter_streams_text_then_usage_and_picks_the_model_by_tier():
    model, client = claude(FakeStream(["Hel", "lo"]))
    chunks = asyncio.run(collect(model, StreamRequest("sys", "usr", "answer.v1", "fast")))
    assert [c.text for c in chunks[:2]] == ["Hel", "lo"] and chunks[2] == Usage(11, 7)
    call = client.calls[0]
    assert (
        call["model"] == "claude-haiku-5-5"
        and call["system"] == "sys"
        and call["messages"] == [{"role": "user", "content": "usr"}]
    )
    assert "temperature" not in call


def response(status):
    return httpx.Response(status, request=httpx.Request("POST", "https://api.example"))


def test_the_claude_adapter_maps_provider_failures_to_the_assistants_named_errors():
    limited = anthropic.RateLimitError("slow down", response=response(429), body=None)
    broken = anthropic.APIStatusError("boom", response=response(500), body=None)
    refused = FakeStream(["I"], stop_reason="refusal")
    for stream, expected in (
        (FakeStream([], error=limited), RateLimitedError),
        (FakeStream([], error=broken), ProviderError),
        (refused, RefusedError),
    ):
        model, _ = claude(stream)
        with pytest.raises(expected):
            asyncio.run(collect(model, request()))


def test_the_claude_adapter_needs_a_key():
    with pytest.raises(ConfigurationError):
        ClaudeStreamingModel({"standard": "m"}, None)


def test_environment_readers_name_the_bad_variable():
    env = {"A": " x ", "N": "5", "F": "0.5", "C": "on", "E": ""}
    assert read_text(env, "A") == "x" and read_int(env, "N", 1) == 5 and read_float(env, "F", 1.0) == 0.5
    assert read_choice(env, "C", "off", frozenset({"on", "off"})) == "on" and read_optional(env, "E") is None
    for call in (
        lambda: read_text(env, "E"),
        lambda: read_int({"N": "x"}, "N", 1),
        lambda: read_int({"N": "0"}, "N", 1),
        lambda: read_float({"F": "x"}, "F", 1.0),
        lambda: read_float({"F": "-1"}, "F", 1.0),
        lambda: read_choice({"C": "maybe"}, "C", "on", frozenset({"on", "off"})),
    ):
        with pytest.raises(ConfigurationError):
            call()


def test_settings_have_safe_defaults_and_reject_bad_values():
    settings = Settings.from_environ({})
    assert settings.model_adapter == "scripted" and settings.pause_enabled and settings.port == 8100
    assert settings.first_token_budget_ms > 0
    with pytest.raises(ConfigurationError, match="MODEL_ADAPTER"):
        Settings.from_environ({"MODEL_ADAPTER": "gpt"})


def test_retry_backs_off_with_full_jitter_and_raises_the_last_failure():
    pauses: list[float] = []
    attempts: list[int] = []

    def flaky():
        attempts.append(1)
        if len(attempts) < 3:
            raise ConnectionError("x")
        return "ok"

    assert (
        retry(
            flaky,
            attempts=4,
            base_delay_seconds=1.0,
            retry_on=(ConnectionError,),
            sleep=pauses.append,
            rng=random.Random(1),
        )
        == "ok"
    )
    assert len(pauses) == 2 and 0 <= pauses[0] <= 1.0 and 0 <= pauses[1] <= 2.0
    with pytest.raises(ConnectionError):
        retry(
            lambda: (_ for _ in ()).throw(ConnectionError("always")),
            attempts=2,
            base_delay_seconds=0,
            retry_on=(ConnectionError,),
            sleep=lambda s: None,
        )
    with pytest.raises(ValueError, match="at least 1"):
        retry(lambda: 1, attempts=0, base_delay_seconds=0, retry_on=())


def test_shutdown_signal_wakes_waiters_and_logfmt_quotes_values():
    shutdown = ShutdownSignal()
    assert not shutdown.requested and shutdown.wait(0.01) is False
    shutdown.request()
    assert shutdown.requested and shutdown.wait(0.01) is True
    stream = io.StringIO()
    configure_logging("INFO", stream)
    logging.getLogger("t").info("hello world", extra=fields(run_id="r 1", n=3))
    line = stream.getvalue()
    assert 'msg="hello world"' in line and 'run_id="r 1"' in line and "n=3" in line
    assert isinstance(LogfmtFormatter(), logging.Formatter)
