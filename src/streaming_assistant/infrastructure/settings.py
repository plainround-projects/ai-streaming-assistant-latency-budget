"""Configuration from the environment, validated once at startup (twelve-factor). Secrets only from here."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from streaming_assistant.infrastructure.environment import (
    read_choice,
    read_float,
    read_int,
    read_optional,
    read_text,
)


def _flag(environ: Mapping[str, str], name: str, default: bool) -> bool:
    return read_choice(environ, name, "on" if default else "off", frozenset({"on", "off"})) == "on"


@dataclass(frozen=True, slots=True)
class Settings:
    """Everything the programs read from the environment."""

    log_level: str
    root: Path
    database: str
    model_adapter: str
    model_ids: dict[str, str]
    anthropic_api_key: str | None
    cassette: Path
    host: str
    port: int
    first_token_timeout_seconds: float
    idle_timeout_seconds: float
    pause_enabled: bool
    stable_prefix_first: bool
    parallel_prep: bool
    cache_retrieval: bool
    route_easy_to_fast: bool
    warm_index: bool
    ttft_standard_ms: float
    ttft_fast_ms: float
    token_ms: float
    first_token_budget_ms: float

    @classmethod
    def from_environ(cls, environ: Mapping[str, str]) -> Settings:
        """Read and validate; raises `ConfigurationError` naming the first bad variable."""
        return cls(
            log_level=read_choice(environ, "LOG_LEVEL", "INFO", frozenset({"DEBUG", "INFO", "WARNING", "ERROR"})),
            root=Path(read_text(environ, "PROJECT_ROOT", ".")),
            database=read_text(environ, "DATABASE", "db/assistant.sqlite"),
            model_adapter=read_choice(
                environ, "MODEL_ADAPTER", "scripted", frozenset({"scripted", "recorded", "claude"})
            ),
            model_ids={
                "standard": read_text(environ, "MODEL_ID", "claude-sonnet-5-5"),
                "fast": read_text(environ, "FAST_MODEL_ID", "claude-haiku-5-5"),
            },
            anthropic_api_key=read_optional(environ, "ANTHROPIC_API_KEY"),
            cassette=Path(read_text(environ, "CASSETTE", "tests/fixtures/cassettes/stream-v1.json")),
            host=read_text(environ, "HOST", "127.0.0.1"),
            port=read_int(environ, "PORT", 8100),
            first_token_timeout_seconds=read_float(environ, "FIRST_TOKEN_TIMEOUT_SECONDS", 3.0, 0.05),
            idle_timeout_seconds=read_float(environ, "IDLE_TIMEOUT_SECONDS", 5.0, 0.05),
            pause_enabled=_flag(environ, "PAUSE", True),
            stable_prefix_first=_flag(environ, "STABLE_PREFIX_FIRST", True),
            parallel_prep=_flag(environ, "PARALLEL_PREP", True),
            cache_retrieval=_flag(environ, "CACHE_RETRIEVAL", True),
            route_easy_to_fast=_flag(environ, "ROUTE_EASY_TO_FAST", False),
            warm_index=_flag(environ, "WARM_INDEX", True),
            ttft_standard_ms=read_float(environ, "SCRIPTED_TTFT_STANDARD_MS", 300.0),
            ttft_fast_ms=read_float(environ, "SCRIPTED_TTFT_FAST_MS", 100.0),
            token_ms=read_float(environ, "SCRIPTED_TOKEN_MS", 15.0),
            first_token_budget_ms=read_float(environ, "FIRST_TOKEN_BUDGET_MS", 1500.0, 1.0),
        )
