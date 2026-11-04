# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Drawn architecture and flow figures in `docs/diagrams/`, light and dark, shown in the README.

## [0.1.0] - 2026-10-27

### Added

- A streaming endpoint with typed events (`token`, `citation`, `state`, `paused`, `done`), a chat page with a Stop button, and a review screen.
- A BM25 retriever over 30 help pages with a coverage measure, routing with explicit thresholds and a refund-window rule, and citations that are checked against the retrieved sections, with dropped ones counted.
- Seven designed failure states (timeout, provider error, rate limited, refusal, no evidence, low confidence, stopped) and Stop that cancels the upstream model call.
- A pause-for-approval path with durable state in SQLite, answer validation, resume after a restart and a hash-chained, append-only audit log with a replay command and a tamper demonstration.
- A scripted streaming model with configurable latency and failure, a recorded adapter with an authored cassette, a Claude adapter and an opt-in live test.
- Stage-timed traces, a 200-question evaluation, a Stop test and a load test at four configurations against the written budget.
- Layered package with the dependency rule enforced by import-linter, unit tests, ruff, mypy, hash-pinned lock files, a Dockerfile and a CI workflow.
