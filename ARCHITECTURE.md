# Architecture: a streaming assistant inside a latency budget

The support assistant as a streaming endpoint (server-sent events) with a small chat page. Text renders as it arrives, Stop cancels the model call on the server, every answer cites help pages that open at the cited section, seven failure states each have their own design, and an uncertain run pauses for a human reviewer, survives a server restart, resumes with the validated answer in context, and leaves a hash-chained audit trail. The budget (1.5 s at p95 to the first token) is written first and measured in the load test.

## Components and what each owns

| Component | Where | Owns |
| --- | --- | --- |
| Retrieval | `domain/retrieval.py`, `infrastructure/catalog.py` | Help-page sections, a small BM25 scorer, and **coverage**: the share of the question's weight the best section holds. A word found nowhere counts against coverage. |
| Routing | `domain/routing.py` | One decision per question: answer, say it is thin (low confidence), say nothing was found, or pause. Two thresholds (0.4 and 0.6) and a policy rule (a refund asked for after the 30-day window, or a legal threat, needs a person). |
| Citations | `domain/citations.py` | Strips `[page#section]` markers from the stream even when split across pieces, remembers the refs, and drops any ref that was not retrieved for this request, counting it. |
| Assistant | `application/assistant.py` | `prepare` (authentication and retrieval, timed, optionally in parallel; routing; prompt assembly) and `stream` / `resume` (typed events, seven states, Stop, upstream cancel, audit entries). |
| Review desk | `application/review.py` | Lists waiting runs and validates a reviewer's answer: not empty, a reviewer id, and a real section cited or an explicit "no page covers this". |
| Audit | `domain/audit.py`, `infrastructure/sqlite_store.py` | Each entry carries the hash of the one before; `verify` returns the index of the first edited, removed or reordered entry. SQL triggers also refuse UPDATE and DELETE. |
| Models | `infrastructure/scripted_stream.py`, `recorded_stream.py`, `claude_stream.py` | A scripted streaming model with configurable latency and failure, a recorded replay keyed by a hash of the whole request, and the Claude adapter. All behind `StreamingModel`. |
| Server | `interfaces/http.py`, `interfaces/static/` | `POST /ask` (SSE), Stop, status, resume, the review endpoints, audit verification, help pages with anchors, the chat page and the review screen. |
| Measurements | `interfaces/measure.py`, `interfaces/cli.py` | The trace, the 200-question evaluation, the Stop test, the load test at four configurations. |

## Pattern: ports and adapters, one orchestrator, events as data

Domain holds the pure decisions (routing, citations, the chain). Application holds the orchestrator and the review desk and depends on ports (`StreamingModel`, `Retriever`, `RunStore`, `AuditLog`, `Authenticator`, `Catalog`, `Clock`). Infrastructure implements them; interfaces wire them. `make lint` enforces the direction with import-linter, and a second contract keeps `anthropic`, `fastapi`, `uvicorn` and `starlette` out of domain and application.

Every outcome is an event, not an exception: `token`, `citation`, `state`, `paused`, `done`. The server only encodes events as SSE. That is why every failure state can be tested without a server: force the model or the retriever, collect the events, and check the event and the text.

## Data flow

Drawn versions of this figure and of the walk-through: [the architecture](docs/diagrams/architecture.svg) and [one run](docs/diagrams/flow.svg).

```text
POST /ask --> authenticate || retrieve  (timed stages)
                   |
                decide route
        +----------+------------------+-----------------+
        v          v                  v                 v
     answer      pause           low_confidence      no_evidence
        |          |                  |                 |
   assemble     save run,           state event       state event
   prompt       audit, paused       + done            + done
        |        event + done
        v
 model.stream --> token events (markers stripped) --> citations checked --> done(usage, timings)
        |                                                    |
   Stop / close => aclose() cancels the upstream call        dropped citations counted
```

### One paused run, step by step

1. The question matches a policy rule (a refund 75 days after delivery) or no help section covers it, so the route is `pause`.
2. The run's question, the retrieved refs and the reason are saved in `paused_runs`; the audit log gets `received` and `paused`; the customer gets a `paused` event and `done`.
3. A reviewer opens `/review`, sees the waiting run, and answers. An empty answer, an unknown section, and an answer that cites nothing without saying "no page" are all refused with a reason. A valid answer is stored and audited as `answered` and `validated`.
4. The server can be restarted here: everything the run needs is in the database.
5. `GET /runs/{id}/resume` assembles the prompt again with the validated answer in context and streams the reply. The reviewer's cited sections are allowed as citations for this run. The audit log gets `resumed`, `citations` and `shown`.
6. Replaying the log reconstructs what the customer saw and who approved it; `verify` proves nobody edited it.

## Decisions and trade-offs

| Decision | Why | Cost |
| --- | --- | --- |
| Coverage counts unknown words against a section | Without it, "What will the weather be like next week?" looked fully covered by one matching word | Short questions with a typo pause more often |
| Thresholds 0.4 (pause) and 0.6 (confident) | The 200 questions have a wide gap: off-topic ones score under 0.4, normal ones 1.0 | Tuned on a synthetic set; a real set needs its own calibration (ADR 0002) |
| The stable prompt text goes first | A provider's prefix cache applies only to a shared start | Passages follow the instructions; the prompt reads in a fixed order |
| Stop is two things: connection close and a stop endpoint | A browser tab closing and a Stop button are different signals | Two code paths, both ending in `aclose()` on the upstream iterator |
| The audit hash chain plus SQL triggers | Triggers stop casual edits; the chain proves tampering by someone who drops them | Appends read the last hash, so they serialize |
| The scripted model's latencies are settings | The budget can be exercised without a key | The numbers show the shape of the fixes, not a provider's speed (ADR 0003) |

## Failure modes the lesson teaches, and where the code shows them

| Failure | Where | Evidence |
| --- | --- | --- |
| Model never answers | `assistant.py` first-token timeout | test: the `timeout` state, upstream cancelled |
| Provider error, rate limit, refusal | `assistant.py`, `claude_stream.py` | tests: three states with their own messages |
| Nothing found; thin match | `routing.py` | tests: `no_evidence` and `low_confidence` |
| User stops | `assistant.py`, stop endpoint | `make stop-test`: upstream cancelled in milliseconds, produced tokens stop growing |
| Invented citation | `citations.py` | `make evaluate`: 0 shown outside the retrieved set, 10 dropped |
| Edited audit log | `audit.py` | `make tamper-demo`: index 1 reported for an edit and for a deletion |
| Lost paused run on restart | `sqlite_store.py` | `make pause-demo`: a second server resumes the run |
| Slow first token | `measure.py` | `make load-test`: four configurations against the budget |

## Limits of the teaching build against a production one

- No model key was available, so every automated run uses a scripted streaming model whose latencies are settings. The Claude adapter and the live test exist and have not been run.
- The 200 questions quote the help pages, so retrieval and citation accuracy are optimistic. A real question set would be harder.
- Authentication is two fixed demo tokens in a table. A real service needs sessions and per-user rate limits.
- The audit log is a table in the same database as the data it audits; a production system would also anchor the latest hash somewhere the application cannot write.
- One process, SQLite behind a lock.

## How to extend it

- A real retriever (embeddings plus BM25) behind `Retriever`; the coverage rule needs recalibrating.
- A second reviewer (four eyes) before a run resumes: another status between `answered` and `resumed`.
- Anchor the audit head hash outside the database every minute.
- The Java twin on Spring AI (the lesson asks for both languages) is not built here.
