# ai-streaming-assistant-latency-budget

The support assistant as a streaming endpoint (server-sent events) with a small chat page. Text renders as it arrives, Stop cancels the model call on the server, every answer cites help pages that open at the cited section, seven failure states each have their own design, and an uncertain run pauses for a human reviewer, survives a server restart, resumes with the validated answer in context, and leaves a hash-chained audit trail. The budget (1.5 s at p95 to the first token) is written before anything is measured.

| | |
| --- | --- |
| **Lesson** | `/prep/ai/project-streaming-assistant-latency-budget`, "A streaming assistant inside a latency budget" (`data-structure-explainer/src/content/tracks/ai/109-project-streaming-assistant-latency-budget.md` in the Plainround app) |
| **Planned hours** | 14 |
| **Level** | Advanced |
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md), decisions: [docs/adr](docs/adr) |

**What the offline run is.** No model key was available to the build, so the default model is `ScriptedStreamingModel`: it writes its answer from the first retrieved passage (with a citation, and now and then an invented one), and its time to first token, prefill cost, token pace and failures are **settings, not measurements of any provider**. Every latency number below therefore shows how the budget is measured and which fix matters in that model of the world; it does not say what a real provider would do. The Claude adapter, the recording command (`make record`) and the live test exist and have not been run. The 200 questions are synthetic: the 180 ordinary ones quote the help pages, so retrieval and citation accuracy are optimistic.

## Prerequisites

| Tool | Version | Used for |
| --- | --- | --- |
| Python | 3.12 or 3.13 (tested with 3.13.12; CI uses 3.13) | the server and the measurements |
| GNU Make | 3.81 or newer | every command below |
| Python packages | `fastapi`, `uvicorn` and `anthropic` 2.3 or newer at run time; pytest, pytest-cov, ruff, mypy, import-linter, pip-audit, httpx for development. Hash-pinned in `requirements.lock` and `requirements-dev.lock`; `make` installs them into `.venv/` | everything |
| Docker | optional, 24 or newer, only for `make docker-build` | the server image (not built during this work: Docker's storage failed on the build machine, so the Dockerfile is untested) |
| uv | optional, only for `make lock` | regenerating the lock files |

No database server, no cloud account, no API key. The state is SQLite (`db/assistant.sqlite`), built from [sql/](sql).

## Setup, run, test, stop

```bash
make up              # .env, .venv from the lock file, db/assistant.sqlite from the SQL scripts
make run             # trace, the 200 questions, Stop, the pause/restart/resume demo, the tamper demo
make load-test       # 200 requests at 5 a second against four configurations (about 4 minutes)
make serve           # the server on PORT (8100): chat page at /, review screen at /review
make queries         # the SQL report over the paused runs and the audit log (after make run)
make test            # unit tests with coverage (the domain and application stay at 95% or more)
make lint            # ruff check, ruff format check, mypy (strict), import-linter
make audit           # known-vulnerability check of the locked dependencies
make down            # remove db/
```

`make help` lists every target; `trace`, `evaluate`, `stop-test`, `pause-demo`, `tamper-demo` and `verify-audit` run one piece each. Demo sign-in tokens are fixed strings in [sql/002_seed.sql](sql/002_seed.sql) (`demo-customer-token`, `demo-reviewer-token`), stored as hashes; they are demo values, not secrets.

## The data

| Item | What it is |
| --- | --- |
| [data/help_pages.json](data/help_pages.json) | 30 help pages with titled sections. Each section has an anchor, so a citation opens `/pages/help-04#a-refund-usually-appears` at the cited section. |
| [data/questions.jsonl](data/questions.jsonl) | 200 questions with the page they should cite and a `should_pause` flag: 20 should pause (10 refunds after the return window, written with digits and words, and 10 off-topic questions) and 180 should be answered. Written by [scripts/generate_data.py](scripts/generate_data.py). |
| [sql/001_schema.sql](sql/001_schema.sql) | DDL: `api_tokens`, `paused_runs`, the append-only `audit_log` with triggers that refuse UPDATE and DELETE. |
| [sql/002_seed.sql](sql/002_seed.sql) | The two demo tokens (as SHA-256 hashes). |
| [sql/003_queries.sql](sql/003_queries.sql) | Waiting runs, paused runs by status and reason, steps per kind, the trail of the latest paused run, who approved what, broken chain links (must be empty). |
| [prompts/answer.v1.md](prompts/answer.v1.md) | The versioned system prompt (cite exactly as shown, never invent a citation); [prompts/CHANGELOG.md](prompts/CHANGELOG.md). |
| [tests/fixtures/cassettes/stream-v1.json](tests/fixtures/cassettes/stream-v1.json) | Eight recorded-style streams keyed by a hash of the whole request. Authored from the scripted model, and labeled so in its `provenance` field. |

## Done when: the lesson's checklist and the proof for each line

| # | Done when (from the lesson) | Command | What proves it |
| --- | --- | --- | --- |
| 1 | One trace of a request shows every stage with its time, and the stage times add up to the measured first-token time within 50 ms. | `make trace` | Cold (the search index is built on the first request): stage sum 1438.6 ms against first token 1444.36 ms, difference 5.8 ms; warm: 1399.19 against 1418.69, difference 19.5 ms (auth 2.24, retrieval 0.36, assembly 1.69, model 1394.9). The stages are authentication, retrieval, prompt assembly and the model; with parallel preparation an `overlap_ms` term accounts for the time saved so the sum still adds up. The budget is written first in [Settings](src/streaming_assistant/infrastructure/settings.py) (`first_token_budget_ms`, 1500). The model stage here is the scripted model's configured time to first token. |
| 2 | Pressing Stop ends the upstream call within 500 ms (seen in the server log), and the output tokens billed for that request stop growing. | `make stop-test` | After 3 tokens the client closes the connection: `upstream_cancelled_after_ms: 5.5`, tokens produced when cancelled and 800 ms later are equal (58 and 58, a counter across the run's five warm-up requests and the stopped one), and an unrelated request right after takes 129.3 ms to its first token against 126.9 ms for the warm-up median: the next request is not left waiting behind the stopped one. Unit tests cover the Stop endpoint path and the closed-connection path, each audited. |
| 3 | Each of the seven states has a passing test that forces it and checks both the event sent and the text shown. | `make test` | `test_a_provider_failure_gets_its_own_state...` (provider error, rate limited, refusal), `test_a_model_that_never_answers...` (timeout), `test_a_stream_that_stalls...` (idle timeout), `test_nothing_found_with_pausing_off...` (no evidence), `test_a_thin_match...` (low confidence), `test_stop_ends_the_stream...` (stopped). Each checks the `state` event's name, message and offered action. |
| 4 | Across the 200 questions no displayed citation points outside that request's retrieved pages, and the number of dropped citations is reported. | `make evaluate` | `citations_outside_retrieved: 0`, `dropped_citations: 10` (the scripted model invents a citation in 1 of 25 answers on purpose), and 180 of 180 answered questions cite their expected page. Optimistic, because the questions quote the pages. |
| 5 | All 20 should-pause questions pause, a paused run survives a server restart and resumes, and the other 180 pause at no more than an agreed rate. | `make evaluate`, `make pause-demo` | `paused_of_should: 20` of 20, `paused_of_others: 0` of 180 (agreed rate: 5%). The demo: ask, pause, an empty answer gets 422, an answer citing nothing gets 422 ("cite a help section, or say that no page covers this question"), a valid answer gets 200; the first server is stopped with SIGTERM; a second server on the same database file reports the run as `answered`, resumes it, and streams the reviewer's answer with a citation. |
| 6 | Replaying the log of an approved run reconstructs exactly what the customer saw and who approved it, and a hand-edited line is reported as tampered at the right index. | `make pause-demo`, `make tamper-demo` | The replay shows `received`, `paused`, `answered` (by `ana`), `validated`, `resumed`, `citations`, `shown` with the text. `make tamper-demo`: chain intact `None`; after editing entry 1: `1`; after deleting entry 1: `1`. Tests also edit the stored rows after dropping the SQL triggers that normally refuse edits, and a reordered pair. |
| 7 | p50 and p95 first-token times meet the budget from step 1, reported with the request count, and the fix that bought the most time is named with its before and after. | `make load-test` | 200 requests at 5 a second per configuration (table below). The fix that bought the most is routing easy questions to the small model: server p95 from 1,567 ms to 497 ms; the other levers moved p95 by less than the jitter. |

Load test (budget 1,500 ms at p95; scripted model, so the shape matters, not the values; measured on a machine with a load average above 40):

| Configuration | Requests | Server p50 (ms) | Server p95 (ms) | Client p50 (ms) | Client p95 (ms) | Budget (ms) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 200 | 1365.4 | 1583.7 | 1376.1 | 1589.6 | 1500.0 |
| stable text first (prompt cache can apply) | 200 | 1388.3 | 1578.6 | 1422.0 | 1694.8 | 1500.0 |
| + parallel prep, cached retrieval, warm index | 200 | 1393.5 | 1567.0 | 1411.2 | 1575.3 | 1500.0 |
| + easy questions to the small model | 200 | 439.1 | 496.9 | 450.6 | 515.9 | 1500.0 |

Only the last configuration meets the budget at p95. Server time is measured inside the service from the request's arrival to the first `token` event; client time from the client's send to the first `token` line.

Lines that need a live key: none of the seven. What a key adds is the same measurements against a real provider (`MODEL_ADAPTER=claude`) and a real Stop (`make test-live` closes a real stream); neither has been run here.

## Stretch goals

| Stretch (from the lesson) | Built? |
| --- | --- |
| A second reviewer before a run resumes. | No. ARCHITECTURE.md, "How to extend it". |
| Anchor the audit head hash outside the database. | No. |
| A real retriever behind the `Retriever` port. | No; the port is there. |

## What is simplified for teaching

- The model is scripted (see the top of this file); its latencies are settings.
- The 200 questions are synthetic and easy; the pause thresholds (0.4 and 0.6 coverage) sit in a wide gap on this set and need recalibrating on real questions.
- Authentication is two fixed demo tokens; the audit log lives in the same database it audits.
- Under heavy machine load the stage sum drifts from the first-token time by tens of milliseconds; the unit test therefore allows 400 ms, while `make trace` is held to the lesson's 50 ms and met it here warm (19.5 ms) and cold (5.8 ms).
- The Java half of the lesson (Spring AI) is not built; this is the Python half.

## Project structure

```text
src/streaming_assistant/
  domain/            retrieval and coverage, routing and the refund-window rule, citations, the audit chain, statistics.
                     Standard library only.
  application/       the assistant (prepare, stream, resume), prompt assembly, the review desk, ports. Depends on domain.
  infrastructure/    SQLite store, help-page catalog and cached retriever, the scripted, recorded and Claude streaming
                     models, settings, logging. Depends on application and domain.
  interfaces/        the `streaming-assistant` command, the FastAPI app and the two static pages, the measurements.
                     Nothing depends on it.
sql/ data/ prompts/  the schema and demo tokens, the help pages and questions, the versioned prompt.
scripts/             generate_data.py, run_queries.py, pause_demo.py, record_streams.py.
tests/               unit (domain, application, infrastructure, interfaces), live (opt-in), fixtures (cassettes).
docs/adr/            decision records.
```

The dependency rule (domain depends on nothing; application on domain; infrastructure and interfaces on both; nothing on interfaces) is enforced by `make lint` through import-linter. A second contract keeps `anthropic`, `fastapi`, `uvicorn` and `starlette` out of domain and application.

## Live key

```bash
export ANTHROPIC_API_KEY=...                  # your own key; nothing in this repository stores one
MODEL_ADAPTER=claude make serve               # the same server over the real model
make record                                   # record eight real streams into tests/fixtures/cassettes/live-v1.json
make test-live                                # one real stream, and one closed early
```

## Author and license

Written by Sumit Srivastava. Released under the MIT License, see [LICENSE](LICENSE). Changes are in [CHANGELOG.md](CHANGELOG.md).
