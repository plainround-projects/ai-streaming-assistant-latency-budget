"""Compose the database, retriever, model and assistant the settings ask for."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from streaming_assistant.application.assistant import Assistant, AssistantConfig, StopRegistry
from streaming_assistant.application.ports import Retriever, StreamingModel
from streaming_assistant.application.prompts import parse_prompt_file
from streaming_assistant.application.review import ReviewDesk
from streaming_assistant.domain.routing import Thresholds
from streaming_assistant.infrastructure.catalog import CachingRetriever, LazyBm25Retriever, PageCatalog
from streaming_assistant.infrastructure.claude_stream import ClaudeStreamingModel
from streaming_assistant.infrastructure.clock import SystemClock
from streaming_assistant.infrastructure.recorded_stream import RecordedStreamingModel
from streaming_assistant.infrastructure.scripted_stream import Pace, ScriptedStreamingModel
from streaming_assistant.infrastructure.settings import Settings
from streaming_assistant.infrastructure.sqlite_store import Database, SqliteAudit, SqliteAuthenticator, SqliteRunStore


@dataclass(frozen=True, slots=True)
class Components:
    """Everything a command needs."""

    settings: Settings
    database: Database
    catalog: PageCatalog
    retriever: Retriever
    lazy: LazyBm25Retriever
    model: StreamingModel
    assistant: Assistant
    desk: ReviewDesk
    audit: SqliteAudit
    authenticator: SqliteAuthenticator
    runs: SqliteRunStore


def build_model(settings: Settings) -> StreamingModel:
    """The scripted model (offline, with the pace from the settings), the recorded one, or Claude."""
    if settings.model_adapter == "claude":
        return ClaudeStreamingModel(settings.model_ids, settings.anthropic_api_key)
    if settings.model_adapter == "recorded":
        return RecordedStreamingModel(settings.root / settings.cassette)
    return ScriptedStreamingModel(Pace(settings.ttft_standard_ms, settings.ttft_fast_ms, token_ms=settings.token_ms))


def build_components(
    settings: Settings, *, database: Database | None = None, model: StreamingModel | None = None, fresh: bool = False
) -> Components:
    """Wire everything. `fresh` rebuilds the database from the SQL scripts (a new file or `:memory:`)."""
    root = settings.root
    db = database or Database(root / settings.database if settings.database != ":memory:" else ":memory:")
    if fresh:
        db.apply_scripts(root / "sql")
    catalog = PageCatalog(root / "data/help_pages.json")
    lazy = LazyBm25Retriever(catalog)
    if settings.warm_index:
        lazy.warm()
    retriever: Retriever = CachingRetriever(lazy) if settings.cache_retrieval else lazy
    chosen = model or build_model(settings)
    clock, audit, runs = SystemClock(), SqliteAudit(db), SqliteRunStore(db)
    authenticator = SqliteAuthenticator(db)
    prompt = parse_prompt_file("answer", (root / "prompts/answer.v1.md").read_text(encoding="utf-8"))
    config = AssistantConfig(
        stable_prompt=prompt.text,
        thresholds=Thresholds(),
        first_token_timeout_seconds=settings.first_token_timeout_seconds,
        idle_timeout_seconds=settings.idle_timeout_seconds,
        pause_enabled=settings.pause_enabled,
        stable_prefix_first=settings.stable_prefix_first,
        parallel_prep=settings.parallel_prep,
        route_easy_to_fast=settings.route_easy_to_fast,
    )
    assistant = Assistant(
        retriever,
        {"standard": chosen, "fast": chosen},
        runs,
        audit,
        authenticator,
        clock,
        config,
        catalog,
        StopRegistry(),
    )
    return Components(
        settings,
        db,
        catalog,
        retriever,
        lazy,
        chosen,
        assistant,
        ReviewDesk(runs, audit, catalog, clock),
        audit,
        authenticator,
        runs,
    )


def database_exists(settings: Settings) -> bool:
    """True when the database file is already there (an in-memory database never is: it starts empty)."""
    return settings.database != ":memory:" and Path(settings.root / settings.database).exists()
