"""The `streaming-assistant` command: serve, db, trace, evaluate, stop-test, load-test, audit verification and replay."""

import argparse
import asyncio
import json
import logging
import os
import sys
from collections.abc import Sequence
from dataclasses import replace

from streaming_assistant.domain.audit import verify
from streaming_assistant.infrastructure.environment import ConfigurationError
from streaming_assistant.infrastructure.logging import configure_logging
from streaming_assistant.infrastructure.recorded_stream import MissingRecordingError
from streaming_assistant.infrastructure.settings import Settings
from streaming_assistant.interfaces.measure import evaluate_questions, load_test, stop_test, trace_one
from streaming_assistant.interfaces.wiring import build_components, database_exists

LOGGER = logging.getLogger("streaming_assistant")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="streaming-assistant", description="A streaming support assistant inside a latency budget."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        ("serve", "start the HTTP server"),
        ("db", "rebuild the SQLite database from sql/001_schema.sql and sql/002_seed.sql"),
        ("evaluate", "the 200 sample questions: pauses, false pauses, citations"),
        ("stop-test", "close the stream after 3 tokens and look at the upstream call"),
        ("verify-audit", "check the hash chain of the audit log"),
        ("tamper-demo", "edit and delete entries in a copy of the chain and verify"),
    ):
        commands.add_parser(name, help=text)
    trace = commands.add_parser("trace", help="one request's stage times, cold and warm")
    trace.add_argument(
        "--question",
        default="A question about shipping times: standard delivery takes three to five business days after dispatch?",
    )
    load = commands.add_parser("load-test", help="replay the questions at a steady rate against four configurations")
    load.add_argument("--rps", type=float, default=5.0)
    load.add_argument("--duration", type=float, default=40.0)
    replay = commands.add_parser("replay", help="what the customer saw and who approved it, from the audit log")
    replay.add_argument("run_id")
    return parser


def _tamper(components: object) -> int:
    from streaming_assistant.interfaces.wiring import Components

    assert isinstance(components, Components)
    entries = list(components.audit.entries())
    if len(entries) < 3:
        for step in ("paused", "answered", "resumed"):
            components.audit.append("run-demo", step, "demo", f"content of {step}")
        entries = list(components.audit.entries())
    print("chain intact:", verify(entries))
    edited = [
        replace(entry, content="Approve a full refund") if index == 1 else entry for index, entry in enumerate(entries)
    ]
    print("after tampering entry 1:", verify(edited))
    removed = [entry for index, entry in enumerate(entries) if index != 1]
    print("after deleting entry 1:", verify(removed))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run one subcommand; returns the process exit code."""
    arguments = _parser().parse_args(argv)
    try:
        settings = Settings.from_environ(os.environ)
    except ConfigurationError as error:
        print(f"configuration error: {error}", file=sys.stderr)
        return 2
    configure_logging(settings.log_level)
    try:
        if arguments.command == "load-test":
            print(
                "| Configuration | Requests | Server p50 (ms) | Server p95 (ms) | Client p50 (ms) | Client p95 (ms) | Budget (ms) |"
            )
            print("| --- | --- | --- | --- | --- | --- | --- |")
            for row in load_test(settings, arguments.rps, arguments.duration):
                print(
                    f"| {row['config']} | {row['requests']} | {row['server_p50_ms']} | {row['server_p95_ms']} | {row['client_p50_ms']} | {row['client_p95_ms']} | {row['budget_ms']} |"
                )
            return 0
        if arguments.command == "stop-test":
            print(json.dumps(asyncio.run(stop_test(settings)), indent=1))
            return 0
        fresh = arguments.command == "db" or not database_exists(settings)
        components = build_components(settings, fresh=fresh)
        if arguments.command == "db":
            print("applied 001_schema.sql, 002_seed.sql to", settings.root / settings.database)
        elif arguments.command == "serve":
            import uvicorn

            from streaming_assistant.interfaces.http import create_app

            app = create_app(
                components.assistant, components.desk, components.catalog, components.authenticator, components.audit
            )
            uvicorn.run(
                app,
                host=settings.host,
                port=settings.port,
                log_level=settings.log_level.lower(),
                timeout_graceful_shutdown=10,
            )
        elif arguments.command == "trace":
            cold_settings = replace(settings, warm_index=False, database=":memory:")
            cold = asyncio.run(trace_one(build_components(cold_settings, fresh=True), arguments.question))
            warm_components = build_components(replace(settings, database=":memory:"), fresh=True)
            asyncio.run(trace_one(warm_components, arguments.question))
            warm = asyncio.run(trace_one(warm_components, arguments.question))
            print("cold (index built on the first request):", cold)
            print("warm:", warm)
            for label, timings in (("cold", cold), ("warm", warm)):
                gap = abs(timings["first_token_ms"] - timings["stage_sum_ms"])
                print(
                    f"{label}: stage sum {timings['stage_sum_ms']} ms vs first token {timings['first_token_ms']} ms (difference {gap:.1f} ms)"
                )
        elif arguments.command == "evaluate":
            print(
                json.dumps(
                    asyncio.run(
                        evaluate_questions(build_components(replace(settings, database=":memory:"), fresh=True))
                    ),
                    indent=1,
                )
            )
        elif arguments.command == "verify-audit":
            entries = components.audit.entries()
            broken = verify(entries)
            print(f"{len(entries)} entries; first broken index: {broken}")
            return 0 if broken is None else 1
        elif arguments.command == "tamper-demo":
            return _tamper(components)
        elif arguments.command == "replay":
            for entry in components.audit.entries(arguments.run_id):
                print(f"{entry.at} {entry.step:10} {entry.actor:14} {entry.content}")
        return 0
    except MissingRecordingError as error:
        LOGGER.error("%s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
