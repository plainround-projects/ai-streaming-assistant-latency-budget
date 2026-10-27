# Python 3.12

## What it is

Python is a programming language: a way to write instructions that a computer follows. A program is a text file of those instructions; a program called the *interpreter* reads the file and carries the instructions out one after another. This repository is written in Python and needs version 3.12 or newer (the file `pyproject.toml` says `requires-python = ">=3.12"`).

## Why this repository uses it

The whole repository is Python: 31 modules under `src/streaming_assistant/`, 5 test files and 4 helper scripts. It was chosen because the lesson's job — a streaming assistant with Stop, real citations, designed failure states, a pause-for-approval path and a first-token budget proven under load — is mostly reading, checking and routing data, which Python does in short readable code, and because every library the lesson needs (the model SDK, web framework, database driver) has a first-class Python version.

## Where it appears

| File | What it does with Python 3.12 |
| --- | --- |
| `src/streaming_assistant/domain/` | 7 modules: pure rules and data, standard library only |
| `src/streaming_assistant/application/` | 6 modules: the use cases and the ports (interfaces) they need |
| `src/streaming_assistant/infrastructure/` | 12 modules: adapters: files, databases, models, the clock, settings |
| `src/streaming_assistant/interfaces/` | 5 modules: the command line, the web server, the wiring |
| `tests/` | 5 test files |
| `scripts/` | helper programs run with `python scripts/NAME.py` |
| `pyproject.toml` | names the minimum version and the package |

## How it works underneath

When you run `python something.py`, the operating system starts one *process*: a running copy of the interpreter with its own memory. The interpreter turns your text into a simpler form called *bytecode* and runs it. Every value in memory is an *object* with a type: a number, a piece of text (a `str`), a list, a dictionary (`dict`, a set of key-and-value pairs).

Code is organised in *modules*. A module is one `.py` file. A *package* is a folder of modules that has an `__init__.py` file. `import x` finds the module or package called `x` and runs it once; `from x import y` brings one name out of it. Python looks for modules in a list of folders (`sys.path`): first the folder of the script, then the places where packages were installed.

A *function* is a named block of code that takes inputs and gives back a value. A *class* is a blueprint for objects that bundle data with functions (called methods). An *exception* is an error object that stops the normal flow; `try` / `except` catches it, and `raise` makes one.

*Type hints* are optional labels such as `def area(width: int) -> int`. Python itself ignores them when running. A separate tool (here `mypy`) reads them and finds mistakes before the program runs.

Python 3.12 added things this repository relies on: the shorter generic syntax `def first[T](items: list[T]) -> T`, and better error messages. Older Pythons would not run the code.

## Walkthrough of this repository's use

The code is organised in four *layers*, each a folder of modules. Imports only go downward (the `import-linter` note shows the rule):

| Layer | Role |
| --- | --- |
| `src/streaming_assistant/domain/` | 7 modules: pure rules and data, standard library only |
| `src/streaming_assistant/application/` | 6 modules: the use cases and the ports (interfaces) they need |
| `src/streaming_assistant/infrastructure/` | 12 modules: adapters: files, databases, models, the clock, settings |
| `src/streaming_assistant/interfaces/` | 5 modules: the command line, the web server, the wiring |

### Every module and what it is for

| Module | What it is for (its docstring's first sentence) |
| --- | --- |
| `src/streaming_assistant/__init__.py` | A streaming support assistant with Stop, real citations, seven failure states, a pause-for-approval path with a hash-chained audit log, and a first-token budget proven under load. |
| `src/streaming_assistant/application/__init__.py` | The application layer. |
| `src/streaming_assistant/application/assistant.py` | The streaming assistant: prepare a request stage by stage (timed), then stream typed events with seven failure states, a pause-for-approval path, real citations and an audit trail. |
| `src/streaming_assistant/application/ports.py` | The boundaries the assistant talks through: the streaming model, the retriever, the stores, the clock. |
| `src/streaming_assistant/application/prompt.py` | Prompt assembly: where the stable text goes decides whether a provider's prefix cache can help. |
| `src/streaming_assistant/application/prompts.py` | Prompts as files: a two-fence header (version, owner), then the prompt text. |
| `src/streaming_assistant/application/review.py` | The review desk: a human support agent answers a paused run, and the answer is validated before it can be used. |
| `src/streaming_assistant/domain/__init__.py` | The domain layer. |
| `src/streaming_assistant/domain/audit.py` | The audit log as a hash chain: each entry carries the hash of the one before, so an edit, removal or reorder is found. |
| `src/streaming_assistant/domain/citations.py` | Citations: a citation is a section that was retrieved for this request. |
| `src/streaming_assistant/domain/errors.py` | Named errors of the streaming assistant. |
| `src/streaming_assistant/domain/retrieval.py` | Help-page sections and a small BM25-style scorer whose score is the share of the question the section covers. |
| `src/streaming_assistant/domain/routing.py` | What to do with a question: answer, say it is thin, say nothing was found, or pause for a person. |
| `src/streaming_assistant/domain/stats.py` | Small statistics for the load test. |
| `src/streaming_assistant/infrastructure/__init__.py` | The infrastructure layer. |
| `src/streaming_assistant/infrastructure/catalog.py` | The help center on disk: page catalog, a lazily built BM25 index (so the cold start is real) and a query cache. |
| `src/streaming_assistant/infrastructure/claude_stream.py` | The real adapter: Claude streaming through the official SDK. |
| `src/streaming_assistant/infrastructure/clock.py` | The system clock. |
| `src/streaming_assistant/infrastructure/environment.py` | Configuration helpers: read and validate environment variables once at startup (twelve-factor). |
| `src/streaming_assistant/infrastructure/logging.py` | Structured logging: one logfmt line per event. |
| `src/streaming_assistant/infrastructure/recorded_stream.py` | Recorded streams: a cassette maps a hash of the whole request to the text pieces and usage, so tests run offline. |
| `src/streaming_assistant/infrastructure/retry.py` | Retry with exponential backoff and full jitter for calls that cross the network. |
| `src/streaming_assistant/infrastructure/scripted_stream.py` | A scripted streaming model: configurable time to first token, prefill cost, token pace and failure, with counters. |
| `src/streaming_assistant/infrastructure/settings.py` | Configuration from the environment, validated once at startup (twelve-factor). |
| `src/streaming_assistant/infrastructure/shutdown.py` | Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work. |
| `src/streaming_assistant/infrastructure/sqlite_store.py` | SQLite adapters: API tokens, paused runs (durable across a restart) and the hash-chained audit log. |
| `src/streaming_assistant/interfaces/__init__.py` | The interfaces layer. |
| `src/streaming_assistant/interfaces/cli.py` | The `streaming-assistant` command: serve, db, trace, evaluate, stop-test, load-test, audit verification and replay. |
| `src/streaming_assistant/interfaces/http.py` | The HTTP interface: POST /ask streams typed server-sent events, Stop cancels the upstream call, reviewers answer paused runs. |
| `src/streaming_assistant/interfaces/measure.py` | Measurements that need a running server or the whole question set: the 200 questions, Stop, the budget under load. |
| `src/streaming_assistant/interfaces/wiring.py` | Compose the database, retriever, model and assistant the settings ask for. |

### The language features this code uses, with this repository's own examples

### Module docstring and `from __future__ import annotations`

Every module starts with a *docstring*: text in triple quotes that says what the module is for (the repository's linter requires it). The line `from __future__ import annotations` makes Python store type hints as text and evaluate them later, so a hint may mention a class defined further down the file.

In this repository, from `src/streaming_assistant/domain/__init__.py` (The domain layer):

```python
"""The domain layer."""
```

### Type hints

After each parameter, `: type` says what is expected. After the closing parenthesis, `-> type` says what the function returns. `int | None` means 'an integer or nothing'. `list[str]`, `dict[str, int]`, `tuple[int, ...]` describe containers and what is inside them. Python ignores hints when running; `mypy` reads them.

In this repository, from `src/streaming_assistant/domain/audit.py` (The audit log as a hash chain: each entry carries the hash of the one before, so an edit, removal or reorder is found):

```python
def digest(previous: str, run: str, step: str, actor: str, at: str, content: str) -> str:
    """SHA-256 over the six fields, in a fixed order, joined by a separator that text does not contain."""
    return hashlib.sha256(SEPARATOR.join((previous, run, step, actor, at, content)).encode()).hexdigest()
```

### Dataclasses

`@dataclass` (a *decorator*, a line starting with `@` that modifies the class below it) writes the boring parts of a data-holding class for you: the constructor, the printed form, and equality. `frozen=True` makes instances unchangeable after creation, so a value cannot be altered by accident. `slots=True` stores fields compactly and forbids stray attributes. Each `name: type` line is one field; `= value` gives a default.

In this repository, from `src/streaming_assistant/domain/audit.py` (The audit log as a hash chain: each entry carries the hash of the one before, so an edit, removal or reorder is found):

```python
@dataclass(frozen=True, slots=True)
class AuditEntry:
    """One step of a run, with its place in the chain."""

    previous: str
    run: str
    step: str
    actor: str
    at: str
    content: str
    hash: str
```

### Protocols (interfaces between layers)

A `Protocol` describes what an object must be able to do, without saying how. The application layer defines protocols (called *ports*), for example 'a model that can complete a request'. The infrastructure layer supplies classes that fit them (called *adapters*). The `...` body means 'no code here; this is only the shape'. Because a test can supply a fake that fits the same shape, the rest of the code never needs the real model, database or clock.

In this repository, from `src/streaming_assistant/application/ports.py` (The boundaries the assistant talks through: the streaming model, the retriever, the stores, the clock):

```python
class StreamingModel(Protocol):
    """A model that streams. Raises `ProviderError`, `RateLimitedError` or `RefusedError`; closing the iterator cancels
    the upstream call."""

    def stream(self, request: StreamRequest) -> AsyncIterator[Chunk]:
        """Stream the answer."""
        ...
```

### Custom exceptions

An exception class is a named kind of error. Inheriting from a built-in one (`ValueError`, `RuntimeError`) makes it catchable by code that handles the parent. A specific name lets callers handle one failure differently from another.

In this repository, from `src/streaming_assistant/domain/errors.py` (Named errors of the streaming assistant):

```python
class ProviderError(RuntimeError):
    """The model provider failed (a server error or a dropped connection)."""
```

### try / except / raise

Code in `try:` runs normally. If it raises an error of the type named after `except`, the matching `except` block runs instead of the program stopping. `raise` (alone) re-raises the current error; `raise X(...) from error` raises a new error and records the old one as its cause.

In this repository, from `src/streaming_assistant/application/assistant.py` (The streaming assistant: prepare a request stage by stage (timed), then stream typed events with seven failure states, a pause-for-approval path, real citations and an audit trail):

```python
        try:
            while True:
                timeout = (
                    self._config.first_token_timeout_seconds
                    if first_token_ms is None
                    else self._config.idle_timeout_seconds
                )
                try:
                    chunk = await asyncio.wait_for(upstream.__anext__(), timeout)
```

### Context managers (`with`)

`with thing:` runs a block and guarantees clean-up when it ends, even on an error: a file is closed, a lock is released, a transaction is committed or rolled back. `as name` gives the block a name for what `with` produced.

In this repository, from `src/streaming_assistant/infrastructure/catalog.py` (The help center on disk: page catalog, a lazily built BM25 index (so the cold start is real) and a query cache):

```python
        with self._lock:
            if self._index is None:
                started = time.perf_counter()
                self._index = Bm25Index(self._catalog.sections)
                self.build_seconds = time.perf_counter() - started
```

### Comprehensions and generator expressions

`[f(x) for x in items if test(x)]` builds a list by looping in one line: for each `x` in `items` that passes the test, add `f(x)`. With round brackets (or inside `sum(...)`, `any(...)`, `all(...)`) it is a *generator expression*: the values are produced one at a time and not stored.

In this repository, from `src/streaming_assistant/domain/retrieval.py` (Help-page sections and a small BM25-style scorer whose score is the share of the question the section covers):

```python
        self._tf = [Counter(terms(f"{s.heading} {s.heading} {s.page_title} {s.text}")) for s in self._sections]
        self._lengths = [sum(tf.values()) for tf in self._tf]
        self._average = sum(self._lengths) / len(self._lengths) if self._lengths else 1.0
        document_frequency: Counter[str] = Counter()
```

### f-strings

An f-string is text with a leading `f` whose `{...}` holes are filled with values: `f"{name} must be set"`. `{value!r}` shows the value as code would write it (with quotes), and `{number:.1f}` formats to one decimal place.

In this repository, from `src/streaming_assistant/domain/retrieval.py` (Help-page sections and a small BM25-style scorer whose score is the share of the question the section covers):

```python
        return f"{self.page_id}#{self.anchor}"
```

### Generic functions with `[T]`

`def retry[T](...) -> T` declares a *type parameter*: whatever type the passed-in function returns is the type `retry` returns, and `mypy` tracks that. This syntax is new in Python 3.12.

In this repository, from `src/streaming_assistant/infrastructure/retry.py` (Retry with exponential backoff and full jitter for calls that cross the network):

```python
def retry[T](
    operation: Callable[[], T],
    *,
    attempts: int,
    base_delay_seconds: float,
    retry_on: tuple[type[BaseException], ...],
```

### async def and await

An `async def` function can pause at `await` (for example while waiting for the network) so other work can run meanwhile. Only the event loop (see `asyncio.md`) runs these functions.

In this repository, from `src/streaming_assistant/application/assistant.py` (The streaming assistant: prepare a request stage by stage (timed), then stream typed events with seven failure states, a pause-for-approval path, real citations and an audit trail):

```python
    async def prepare(self, run_id: str, question: str, token: str) -> Prepared:
        """Authenticate, retrieve, assemble and route; each stage is timed inside the real path.

        With `parallel_prep` the authentication and the retrieval run at the same time; `overlap_ms` is the time that
        saved, so the stage times still add up to the measured total.
        """
        started = time.perf_counter()
        limit = self._config.retrieval_limit
```

### Properties

`@property` lets a method be read like an attribute (`thing.requested`, no parentheses), so callers see a value while the class keeps the freedom to compute it.

In this repository, from `src/streaming_assistant/domain/retrieval.py` (Help-page sections and a small BM25-style scorer whose score is the share of the question the section covers):

```python
    @property
    def ref(self) -> str:
        """The citation form: `page-07#refund-timing`."""
        return f"{self.page_id}#{self.anchor}"
```

### The entry-point guard

A module's `__name__` is `"__main__"` only when the file is run directly (for example `python -m package.module`), and its package-qualified name when imported. The guard lets the same file be both importable and runnable. `raise SystemExit(main())` ends the process with the exit code `main` returned.

In this repository, from `src/streaming_assistant/interfaces/cli.py` (The `streaming-assistant` command: serve, db, trace, evaluate, stop-test, load-test, audit verification and replay):

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

### The infrastructure helpers shared by the repository

The lesson's logic is in `application/assistant.py` (prepare a request, stream typed events, seven failure states, Stop, pause and resume), `domain/routing.py` (the route decision), `domain/retrieval.py` (search and coverage), `domain/citations.py` (marker stripping and the citation check) and `domain/audit.py` (the hash chain).

A reading guide to the central modules: every class and function, with its signature and the docstring that says what it is for.

#### `src/streaming_assistant/application/assistant.py`

The module's docstring says: *The streaming assistant: prepare a request stage by stage (timed), then stream typed events with seven failure states, a pause-for-approval path, real citations and an audit trail.*

- `class UnauthorizedError(Exception):` (class): The bearer token is missing or unknown.
- `class Event:` (class): One server-sent event: a type name and its data.
- `class AssistantConfig:` (class): Behavior switches. The last four are the load test's levers (each one is a fix measured against the baseline).
- `class StopRegistry:` (class): Run ids a user asked to stop, safe to use from any thread.
  - `def __init__(self) -> None:`
  - `def request(self, run_id: str) -> None:`: Ask for a run to stop.
  - `def is_requested(self, run_id: str) -> bool:`: True once a stop was asked for.
  - `def clear(self, run_id: str) -> None:`: Forget a run.
- `class Prepared:` (class): Everything decided before the first byte: who, what was retrieved, the route, the prompt and the stage times.
- `def _timed[T](function: Callable[[], T]) -> tuple[T, float]:`
- `class Assistant:` (class): Orchestrates one request. Collaborators arrive through ports so tests can force every state.
  - `def __init__( self, retriever: Retriever, models: Mapping[str, StreamingModel], runs: RunStore, audit: AuditLog, authenticator: Authenticator, clock: Clock, config: AssistantConfig, catalog: Catalog, stops: StopRegistry | None = None, ) -> None:`
  - `def stops(self) -> StopRegistry:`: The registry the stop endpoint writes to.
  - `async def prepare(self, run_id: str, question: str, token: str) -> Prepared:`: Authenticate, retrieve, assemble and route; each stage is timed inside the real path. With `parallel_prep` the authentication and the retrieval run at the same time; `overlap_ms` is the time that saved, so the stage times still add up to the measured total.
  - `async def stream(self, prepared: Prepared) -> AsyncIterator[Event]:`: Typed events for one run. The stream always ends with `done`, `paused` or a `state` followed by `done`.
  - `async def resume(self, run_id: str) -> AsyncIterator[Event]:`: Continue a paused run whose reviewer answer was validated; the answer goes into the model's context.
  - `async def _answer(self, prepared: Prepared) -> AsyncIterator[Event]:`
  - `async def _close(upstream: Any) -> None:`
  - `def _state(name: str) -> Event:`
  - `def _done( prepared: Prepared, usage: Usage | None, words: int, outcome: str, first_token_ms: float | None = None, dropped: int = 0, ) -> Event:`

#### `src/streaming_assistant/domain/routing.py`

The module's docstring says: *What to do with a question: answer, say it is thin, say nothing was found, or pause for a person. Thresholds are explicit.*

- `def words_to_number(text: str) -> int | None:`: A small number written in digits or words ("75", "seventy five", "a hundred"); None when it is not one.
- `def days_since_delivery(question: str) -> int | None:`: The age in days a question states ("sixty days ago", "75 days ago"), or None. The longest run of up to four words before "days ago" that reads as a number wins, so "seventy five" is 75, not 5.
- `def needs_a_person(question: str) -> bool:`: A refund asked for after the 30-day window, or a legal threat: a policy exception only a person can grant.
- `class Thresholds:` (class): Retrieval coverage at which a question is answered, called thin, or sent to a person.
- `class Route:` (class): The decision and why.
- `def decide_route(question: str, hits: Sequence[Hit], thresholds: Thresholds, *, pause_enabled: bool = True) -> Route:`: A question that matches a needs-a-person pattern pauses; so does one no page covers (when pausing is on).

#### `src/streaming_assistant/domain/retrieval.py`

The module's docstring says: *Help-page sections and a small BM25-style scorer whose score is the share of the question the section covers.*

- `class Section:` (class): One section of a help page; `anchor` is where a citation opens the page.
  - `def ref(self) -> str:`: The citation form: `page-07#refund-timing`.
- `class Hit:` (class): A section the retriever returned, with its raw score and the share of the question's weight it covers.
- `def terms(text: str) -> list[str]:`: Lower-case content words (no stop words), with a crude plural fold.
- `class Bm25Index:` (class): Built once from the sections. `search` returns the best sections; `coverage` is the idf weight of the query terms the section contains over the idf weight of all the query's terms. A term found nowhere in the help center weighs as much as the rarest known term, so a question about the weather does not look covered because one word matched.
  - `def __init__(self, sections: Sequence[Section]) -> None:`
  - `def search(self, query: str, limit: int = 3) -> list[Hit]:`: Best sections for the query, best first; sections sharing no term are left out.

#### `src/streaming_assistant/domain/citations.py`

The module's docstring says: *Citations: a citation is a section that was retrieved for this request. Anything else is dropped and counted.*

- `class MarkerStripper:` (class): Removes `[page#section]` markers from a stream of text pieces, even when a marker is split across pieces, and remembers the refs it saw. A bracket that never closes within 40 characters is released as ordinary text.
  - `def __init__(self) -> None:`
  - `def feed(self, piece: str) -> str:`: Text that is safe to show now.
  - `def finish(self) -> str:`: Whatever was held back at the end of the stream.
- `def check_refs(refs: Sequence[str], allowed: Mapping[str, Section]) -> tuple[tuple[Section, ...], int]:`: (sections that may be shown, number dropped). A ref counts only when it is one of the sections allowed for this request: the ones retrieved for it, plus the ones a reviewer cited.

#### `src/streaming_assistant/domain/audit.py`

The module's docstring says: *The audit log as a hash chain: each entry carries the hash of the one before, so an edit, removal or reorder is found.*

- `class AuditEntry:` (class): One step of a run, with its place in the chain.
- `def digest(previous: str, run: str, step: str, actor: str, at: str, content: str) -> str:`: SHA-256 over the six fields, in a fixed order, joined by a separator that text does not contain.
- `def make_entry(previous_hash: str | None, run: str, step: str, actor: str, at: datetime, content: str) -> AuditEntry:`: The next entry in the chain.
- `def verify(entries: Sequence[AuditEntry]) -> int | None:`: Index of the first entry that was edited, removed or reordered; None when the chain holds.

#### `src/streaming_assistant/application/review.py`

The module's docstring says: *The review desk: a human support agent answers a paused run, and the answer is validated before it can be used.*

- `class ReviewDesk:` (class): Lists waiting runs and validates a reviewer's answer: not empty, and either citing a real section or saying that no page covers the question. An unvalidated answer must never reach the model's context.
  - `def __init__(self, runs: RunStore, audit: AuditLog, catalog: Catalog, clock: Clock) -> None:`
  - `def waiting(self, limit: int = 50) -> Sequence[PausedRun]:`: Runs waiting for a reviewer, oldest first.
  - `def status(self, run_id: str) -> str:`: The run's status: waiting, answered or resumed.
  - `def answer(self, run_id: str, reviewer_id: str, answer: str, cited: Sequence[str], no_page: bool) -> PausedRun:`: Validate and store the reviewer's answer; raises `ReviewRejectedError` with the reason when it is not allowed.

#### `src/streaming_assistant/infrastructure/scripted_stream.py`

The module's docstring says: *A scripted streaming model: configurable time to first token, prefill cost, token pace and failure, with counters. It writes its answer from the passages in the prompt (the first sentence of the best passage, with its citation), so a run has real text and real citations. Its latencies are settings, not measurements of any provider. It is not a model.*

- `class Pace:` (class): Latency settings in milliseconds.
- `class ScriptedStreamingModel:` (class): Async streaming with counters: tokens produced (what would be billed), cancellations and their times.
  - `def __init__(self, pace: Pace | None = None, mode: str = "ok", hallucinate_every: int = 25) -> None:`
  - `def _ttft(self, request: StreamRequest) -> float:`
  - `def _answer(self, request: StreamRequest) -> str:`
  - `async def stream(self, request: StreamRequest) -> AsyncIterator[Chunk]:`: Wait for the first token, then emit the answer a word at a time.

#### `src/streaming_assistant/interfaces/measure.py`

The module's docstring says: *Measurements that need a running server or the whole question set: the 200 questions, Stop, the budget under load.*

- `async def collect( components: Components, run_id: str, question: str, token: str = "demo-customer-token" ) -> tuple[list[Event], list[str]]:`: Run one question in process; returns the events and the refs that were retrieved for it.
- `async def trace_one(components: Components, question: str) -> dict[str, float]:`: One request's stage times from the real path.
- `async def evaluate_questions(components: Components) -> dict[str, object]:`: All 200 questions: pauses, false pauses, citations shown outside the retrieved set, dropped citations.
- `def free_port() -> int:`: A port nothing is listening on (the measurements must not collide with services already on the machine).
- `class RunningServer:` (class): uvicorn in a thread, for tests of behavior over a real socket.
  - `def __init__(self, components: Components, port: int) -> None:`
- `async def first_event(client: httpx.AsyncClient, question: str) -> float:`: Seconds from sending the request until the first `token` event line arrives.
- `async def stop_test(settings: Settings) -> dict[str, object]:`: Close the connection after 3 tokens and look at the upstream call; then time an unrelated request.
- `async def drive(base: str, questions: list[str], rps: float, duration: float) -> tuple[list[float], list[float], int]:`: Send requests at a steady rate; returns client first-token seconds, server first-token ms and the request count.
- `def load_test(settings: Settings, rps: float, duration: float) -> list[dict[str, object]]:`: Replay the answerable questions at `rps` for `duration` seconds against a server per configuration.


<!-- fullwalk -->
### Every Python file of the program, statement by statement

This part quotes every Python file under `src/` and `scripts/`, in the order they are listed by git, and says in plain words what each statement does. Each quoted block is the file's own text; the bullets underneath explain it. A grey note (a block starting with `>`) explains a Python idea the first time it appears.

#### `scripts/generate_data.py`

```python
"""Write data/help_pages.json (30 pages) and data/questions.jsonl (200 questions with known answers, 20 that should pause).

Deterministic for a seed. Every answerable question is written from the section it should find, so the expected page and
section are known when the question is made.
"""
```

- The docstring (documentation kept with the code) says: *Write data/help_pages.json (30 pages) and data/questions.jsonl (200 questions with known answers, 20 that should pause). Deterministic for a seed. Every answerable question is written from the section it should find, so the expected page and section are known when the question is made.*

> **A Python file is a module.** When another file writes `import` or `from ... import`, Python runs this file once and hands over the names it defines. A docstring is a string that sits first in a module, class or function; Python keeps it as the documentation of that thing.

```python
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import random`: makes the module `random` available (random numbers (a seeded generator gives the same numbers every run)).
- `import sys`: makes the module `sys` available (facts about the running Python program: arguments, exit, standard streams).
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `ROOT = Path(__file__).resolve().parents[1]`: stores the item `Path(__file__).resolve().parents[1]` in `ROOT`.

> **`if __name__ == "__main__":`.** Python sets `__name__` to `"__main__"` only when the file is run directly (`python file.py`), not when another file imports it. So the block runs only for a direct start.

> **`import` and `from ... import`.** `import x` makes the module `x` available under that name. `from x import y` fetches only the name `y` from `x` so it can be used without the prefix. `as` renames what you import. Imports at the top mean: this file needs those things from elsewhere.

> **`from __future__ import annotations`.** The type hints written after a colon or an arrow are saved as text and only looked at by type checkers, so a hint may name a class that is defined later in the file.

> **A name is a label for a value.** `x = 5` makes the name `x` point to the value 5. Names are not boxes with a fixed type; Python looks at the value at run time. A name written in CAPITALS by habit marks a constant: nobody should change it.

> **Indexing and slicing.** `items[0]` is the first item; `items[-1]` the last; `items[a:b]` is a new list from position `a` up to but not including `b`; `d['key']` looks a key up in a dict (and raises `KeyError` if it is missing).

```python
TOPICS = (
    (
        "Shipping times",
        "delivery",
        [
            "Standard delivery takes three to five business days after dispatch",
            "Express delivery arrives within two business days where available",
            "Orders placed after the cutoff hour ship on the next business day",
        ],
    ),
    (
        "Tracking a parcel",
        "tracking",
        [
            "A tracking link is emailed once the parcel leaves the warehouse",
            "The tracking page shows the carrier hub the parcel last passed",
            "A parcel marked delivered but not received should be reported within five days",
        ],
    ),
    (
        "Return policy",
        "returns",
        [
            "Items can be returned within thirty days of delivery",
            "Returned items must be unused and in the original packaging",
            "Sale items follow the same thirty day return window",
        ],
    ),
    (
        "Refund timing",
        "refunds",
        [
            "Refunds are issued to the original payment method after the parcel is checked",
            "A refund usually appears on the card within five business days",
            "Store credit refunds are available immediately",
        ],
    ),
    (
        "Exchanges",
        "exchange",
        [
            "An exchange for another size is free within thirty days",
            "The exchange parcel ships once the first item scans at the warehouse",
            "Colour exchanges depend on current stock",
        ],
    ),
    (
        "Damaged items",
        "damage",
        [
            "Report a damaged item within fourteen days with a photo",
            "A replacement ships at no cost once the photo is reviewed",
            "Damaged parcels can be refused at the door",
        ],
    ),
    (
        "Missing items",
        "missing",
        [
            "A missing item should be reported within seven days of delivery",
            "Multi item orders can arrive in separate boxes",
            "The packing slip lists every item that left the warehouse",
        ],
    ),
    (
        "Changing an address",
        "address",
        [
            "The delivery address can change until the order ships",
            "Saved addresses live under account settings",
            "A parcel already with the carrier cannot be redirected by the shop",
        ],
    ),
    (
        "Cancelling an order",
        "cancel",
        [
            "An order can be cancelled until it has been dispatched",
            "A cancelled order releases the payment within three business days",
            "Cancelled gift card payments return to the card balance",
        ],
    ),
    (
        "Payment methods",
        "payment",
        [
            "Cards, bank transfer and store credit are accepted",
            "Payment is taken when the order ships",
            "A declined payment keeps the basket for twenty four hours",
        ],
    ),
    (
        "Promo codes",
        "promo",
        [
            "Each promo code works once per account",
            "Codes apply to full price items only",
            "Expired codes cannot be extended by support",
        ],
    ),
    (
        "Gift cards",
        "giftcard",
        [
            "Gift cards never expire and can be used across several orders",
            "The balance is shown on the gift card page",
            "Lost gift cards can be blocked and reissued with proof of purchase",
        ],
    ),
    (
        "Resetting a password",
        "password",
        [
            "Use the reset link on the sign in page",
            "The reset link expires after one hour",
            "Support cannot read or set a password for you",
        ],
    ),
    (
        "Deleting an account",
        "account",
        [
            "Account deletion is available under privacy settings",
            "Order history is kept for tax records after deletion",
            "Deletion finishes within thirty days",
        ],
    ),
    (
        "Privacy and data",
        "privacy",
        [
            "Personal data is used only to run orders and support",
            "A copy of your data can be requested from privacy settings",
            "Marketing email can be switched off at any time",
        ],
    ),
    (
        "Warranty",
        "warranty",
        [
            "Products carry a one year warranty against defects",
            "Warranty claims need the order number and a photo",
            "Normal wear is not covered by the warranty",
        ],
    ),
    (
        "Size guide",
        "sizing",
        [
            "Every product page links a size guide below the size picker",
            "Jackets run true to size while shoes run half a size small",
            "Measurements are given in centimetres and inches",
        ],
    ),
    (
        "Stock alerts",
        "stockalert",
        [
            "Use notify me on a sold out product to get an email on restock",
            "Restock dates are estimates and can move",
            "Alerts expire after ninety days",
        ],
    ),
    (
        "International shipping",
        "abroad",
        [
            "The shop ships to the countries listed on the shipping page",
            "Duties and taxes are shown before payment",
            "Delivery abroad takes seven to ten business days",
        ],
    ),
    (
        "Express delivery",
        "express",
        [
            "Express delivery is offered at checkout when the address qualifies",
            "Express orders must be placed before noon",
            "Express delivery is not available on bank holidays",
        ],
    ),
    (
        "Pickup points",
        "pickup",
        [
            "Choose a pickup point at checkout from the map",
            "Parcels wait at a pickup point for seven days",
            "A photo identity document is needed to collect",
        ],
    ),
    (
        "Customs and duties",
        "customs",
        [
            "Duties are calculated at checkout for supported countries",
            "Nothing is payable on delivery for prepaid duties",
            "Returns from abroad use the prepaid label",
        ],
    ),
    (
        "Invoices and receipts",
        "invoice",
        [
            "Invoices are attached to each order in your account",
            "A company name can be added before the order ships",
            "Corrected invoices are issued within two business days",
        ],
    ),
    (
        "Loyalty points",
        "loyalty",
        [
            "One point is earned for every currency unit spent",
            "Points can be applied at checkout as a discount",
            "Points expire after twenty four months",
        ],
    ),
    (
        "Student discount",
        "student",
        [
            "Students get ten percent off with a verified student email",
            "Verification lasts one year",
            "The discount cannot be combined with promo codes",
        ],
    ),
    (
        "Bulk orders",
        "bulk",
        [
            "Orders above twenty units receive a team quote",
            "Quotes are valid for fourteen days",
            "Bulk orders ship in consolidated pallets",
        ],
    ),
    (
        "Gift wrapping",
        "giftwrap",
        [
            "Gift wrap is a checkout option for a small fee",
            "A printed card carries your message",
            "Gift wrapped items are packed with no price slip",
        ],
    ),
    (
        "Store hours",
        "hours",
        [
            "Chat support is open every day from eight to eight",
            "Phone support is closed on bank holidays",
            "Email replies arrive within one business day",
        ],
    ),
    (
        "Contacting support",
        "contact",
        [
            "Use chat for the fastest answer",
            "Include the order number in every message",
            "Escalations are answered by a senior agent within one day",
        ],
    ),
    (
        "Product care",
        "care",
        [
            "Wool items are hand washed cold",
            "Leather bags are wiped with a damp cloth",
            "Canvas can be machine washed gently",
        ],
    ),
)
```

- `TOPICS = ( ( "Shipping times", "delivery", [ "Standard delivery tak...`: stores a tuple of 30 items in `TOPICS`.

> **Tuples and unpacking.** `(a, b)` is a fixed-length group. `x, y = pair` unpacks the two items into two names at once.

```python
UNCOVERED = (
    "Who won the football match yesterday",
    "What is the capital of Australia",
    "Can you recommend a good pasta recipe",
    "How tall is the tallest mountain in the world",
    "What will the weather be like next week",
    "Which planet is closest to the sun",
    "Can you help me write a poem about autumn",
    "What is the best programming language to learn",
    "How do I tune a guitar string",
    "When did the first airplane fly",
)
```

- `UNCOVERED = ( "Who won the football match yesterday", "What is the ...`: stores a tuple of 10 items in `UNCOVERED`.

```python
REFUND_LATE = (
    "I bought this sixty days ago, can I still get a refund?",
    "It was delivered ninety days ago and I want a refund now.",
    "Can I get a refund on an order from seventy five days ago?",
    "I want a refund for something I received fifty days ago.",
    "My order arrived eighty days ago, is a refund still possible?",
    "Refund request after the window: the parcel came a hundred days ago.",
    "I received it forty five days ago and would like my money back, a refund please.",
    "Please refund the order I got sixty five days ago.",
    "Is a refund possible for a purchase from ninety five days ago?",
    "Can you refund an order delivered seventy days ago?",
)
```

- `REFUND_LATE = ( "I bought this sixty days ago, can I still get a re...`: stores a tuple of 10 items in `REFUND_LATE`.

```python
def anchor(heading: str) -> str:
```

- Defines the function `anchor`.
- Parameters:
  - `heading`, type `str`.
- Gives back a value of type `str`.

> **A function.** `def name(parameters):` defines a reusable block of code. The indented lines below it are the body; they run each time the function is called. `return` ends the call and hands a value back. A function that reaches its end without `return` hands back `None`, Python's 'nothing'.

> **Parameters.** A parameter with `= value` is optional: if the caller gives nothing, the default is used. A bare `*` in the list means everything after it must be passed by name (`f(x=1)`). `*args` collects extra positional arguments in a tuple and `**kwargs` collects extra named ones in a dict. `->` followed by a type says what the function gives back.

```python
"""URL anchor of a heading."""
```

- The docstring (documentation kept with the code) says: *URL anchor of a heading.*

```python
return "-".join(heading.lower().replace(",", "").split()[:4])
```

- `return "-".join(heading.lower().replace(",", "").split()[:4])`: ends the function and gives back the result of calling `"-".join(heading.lower().replace(",", "").split()[:4])`, which glues the items of `heading.lower().replace(",", "").split()[:4]` together with `"-"` between them.

```python
def build_pages() -> list[dict[str, object]]:
```

- Defines the function `build_pages`.
- Gives back a value of type `list[dict[str, object]]`.

```python
"""Thirty pages of three sections each."""
```

- The docstring (documentation kept with the code) says: *Thirty pages of three sections each.*

```python
pages = []
```

- `pages = []`: stores a new list (empty) in `pages`.

```python
for number, (title, keyword, sentences) in enumerate(TOPICS, start=1):
```

- Repeats the indented lines once for each item of `enumerate(TOPICS, start=1)`, naming the current item the names `number`, `(title, keyword, sentences)`.

> **`for`.** `for item in things:` runs the indented lines once per item, giving the name `item` the next value each time. `break` leaves the loop early; `continue` jumps to the next item.

```python
sections = []
```

- `sections = []`: stores a new list (empty) in `sections`.

```python
for sentence in sentences:
```

- Repeats the indented lines once for each item of `sentences`, naming the current item `sentence`.

```python
heading = " ".join(sentence.split()[:5])
body = f"{sentence}. This applies to {keyword} questions about orders from the shop and is explained in the {title.lower()} page."
sections.append({"anchor": anchor(heading), "heading": heading, "text": body})
```

- `heading = " ".join(sentence.split()[:5])`: stores the result of calling `" ".join(sentence.split()[:5])`, which glues the items of `sentence.split()[:5]` together with `" "` between them in `heading`.
- `body = f"{sentence}. This applies to {keyword} questions about orde...`: stores the text built by the f-string `f"{sentence}. This applies to {keyword} questions about orders from the shop and is exp...` in `body`.
- `sections.append({"anchor": anchor(heading), "heading": heading, "te...`: calling `sections.append({"anchor": anchor(heading), "heading": heading, "text": body})`, which adds `{"anchor": anchor(heading), "heading": heading, "text": body}` to the end of `sections`.

> **f-strings.** A string starting with `f` can hold `{expression}` marks; Python evaluates each and puts the result into the text. After a colon you can give a format, such as `{x:.2f}` for two decimals or `{n:>5}` for right-aligned in 5 characters.

```python
pages.append({"page_id": f"help-{number:02d}", "title": title, "sections": sections})
```

- `pages.append({"page_id": f"help-{number:02d}", "title": title, "sec...`: calling `pages.append({"page_id": f"help-{number:02d}", "title": title, "sections": sections})`, which adds `{"page_id": f"help-{number:02d}", "title": title, "sections": sections}` to the end of `pages`.

```python
return pages
```

- `return pages`: ends the function and gives back the value of `pages`.

```python
def build_questions(pages: list[dict[str, object]], rng: random.Random) -> list[dict[str, object]]:
```

- Defines the function `build_questions`.
- Parameters:
  - `pages`, type `list[dict[str, object]]`.
  - `rng`, type `random.Random`.
- Gives back a value of type `list[dict[str, object]]`.

```python
"""180 answerable questions written from a section's own words, 20 that should pause."""
```

- The docstring (documentation kept with the code) says: *180 answerable questions written from a section's own words, 20 that should pause.*

```python
questions = []
```

- `questions = []`: stores a new list (empty) in `questions`.

```python
for index in range(180):
```

- Repeats the indented lines once for each item of `range(180)`, naming the current item `index`.

```python
page = pages[index % len(pages)]
section = page["sections"][(index // len(pages)) % 3]  # type: ignore[index]
words = str(section["text"]).split(". ")[0].lower().split()
keep = words[: max(5, len(words) - rng.randint(0, 2))]
questions.append(
    {
        "id": f"q-{index + 1:03d}",
        "question": f"A question about {str(page['title']).lower()}: {' '.join(keep)}?",
        "expected_page": page["page_id"],
        "expected_anchor": section["anchor"],
        "should_pause": False,
    }
)
```

- `page = pages[index % len(pages)]`: stores the item `pages[index % len(pages)]` in `page`.
- `section = page["sections"][(index // len(pages)) % 3]`: stores the item `page["sections"][(index // len(pages)) % 3]` in `section`.
- `words = str(section["text"]).split(". ")[0].lower().split()`: stores the result of calling `str(section["text"]).split(". ")[0].lower().split()`, which cuts `str(section["text"]).split(". ")[0].lower()` into pieces at its argument (whitespace if nothing is given) in `words`.
- `keep = words[: max(5, len(words) - rng.randint(0, 2))]`: stores the item `words[: max(5, len(words) - rng.randint(0, 2))]` in `keep`.
- `questions.append( { "id": f"q-{index + 1:03d}", "question": f"A que...`: calling `questions.append( { "id": f"q-{index + 1:03d}", "question": f"A question about {str(pag...`, which adds `{ "id": f"q-{index + 1:03d}", "question": f"A question about {str(page['title']).lower(...` to the end of `questions`.

```python
for index, text in enumerate(REFUND_LATE):
```

- Repeats the indented lines once for each item of `enumerate(REFUND_LATE)`, naming the current item the names `index`, `text`.

```python
questions.append(
    {
        "id": f"q-{181 + index:03d}",
        "question": text,
        "expected_page": None,
        "expected_anchor": None,
        "should_pause": True,
    }
)
```

- `questions.append( { "id": f"q-{181 + index:03d}", "question": text,...`: calling `questions.append( { "id": f"q-{181 + index:03d}", "question": text, "expected_page": No...`, which adds `{ "id": f"q-{181 + index:03d}", "question": text, "expected_page": None, "expected_anch...` to the end of `questions`.

```python
for index, text in enumerate(UNCOVERED):
```

- Repeats the indented lines once for each item of `enumerate(UNCOVERED)`, naming the current item the names `index`, `text`.

```python
questions.append(
    {
        "id": f"q-{191 + index:03d}",
        "question": f"{text}?",
        "expected_page": None,
        "expected_anchor": None,
        "should_pause": True,
    }
)
```

- `questions.append( { "id": f"q-{191 + index:03d}", "question": f"{te...`: calling `questions.append( { "id": f"q-{191 + index:03d}", "question": f"{text}?", "expected_pag...`, which adds `{ "id": f"q-{191 + index:03d}", "question": f"{text}?", "expected_page": None, "expecte...` to the end of `questions`.

```python
rng.shuffle(questions)
return questions
```

- `rng.shuffle(questions)`: calling `rng.shuffle(questions)`, which mixes the order of a list in place.
- `return questions`: ends the function and gives back the value of `questions`.

```python
def main() -> int:
```

- Defines the function `main`.
- Gives back a value of type `int`.

```python
"""Write both files."""
```

- The docstring (documentation kept with the code) says: *Write both files.*

```python
rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 2610)
pages = build_pages()
(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data/help_pages.json").write_text(json.dumps(pages, indent=1) + "\n", encoding="utf-8")
questions = build_questions(pages, rng)
(ROOT / "data/questions.jsonl").write_text("".join(json.dumps(q) + "\n" for q in questions), encoding="utf-8")
```

- `rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 2610)`: stores the result of calling `random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 2610)`, which makes a random number generator; the same seed gives the same sequence in `rng`.
- `pages = build_pages()`: stores the result of calling `build_pages()`, which is this repository's own `build_pages` (in `scripts/generate_data.py`): thirty pages of three sections each in `pages`.
- `(ROOT / "data").mkdir(exist_ok=True)`: calling `(ROOT / "data").mkdir(exist_ok=True)`, which creates the folder `ROOT / "data"` The named values are `exist_ok`..
- `(ROOT / "data/help_pages.json").write_text(json.dumps(pages, indent...`: calling `(ROOT / "data/help_pages.json").write_text(json.dumps(pages, indent=1) + "\n", encoding...`, which writes text to the file `ROOT / "data/help_pages.json"`, replacing it The named values are `encoding`..
- `questions = build_questions(pages, rng)`: stores the result of calling `build_questions(pages, rng)`, which is this repository's own `build_questions` (in `scripts/generate_data.py`): 180 answerable questions written from a section's own words, 20 that should pause in `questions`.
- `(ROOT / "data/questions.jsonl").write_text("".join(json.dumps(q) + ...`: calling `(ROOT / "data/questions.jsonl").write_text("".join(json.dumps(q) + "\n" for q in questi...`, which writes text to the file `ROOT / "data/questions.jsonl"`, replacing it The named values are `encoding`..

```python
print(
    f"wrote data/help_pages.json ({len(pages)} pages) and data/questions.jsonl ({len(questions)} questions, {sum(q['should_pause'] for q in questions)} should pause)"
)
return 0
```

- `print( f"wrote data/help_pages.json ({len(pages)} pages) and data/q...`: calling `print( f"wrote data/help_pages.json ({len(pages)} pages) and data/questions.jsonl ({len...`, which writes `f"wrote data/help_pages.json ({len(pages)} pages) and data/questions.jsonl ({len(questi...` to the screen (standard output).
- `return 0`: ends the function and gives back the number `0`.

```python
if __name__ == "__main__":
```

- Checks whether `__name__` equals `"__main__"`. If so, the indented lines run.

> **`if`.** `if condition:` runs the indented lines only when the condition is true. `elif` adds another condition to try, `else` runs when none held. 'Truthy' values count as true; 'falsy' ones are `False`, `None`, zero and anything empty (`''`, `[]`, `{}`).

> **Operators.** `//` divides and rounds down; `%` is the remainder; `**` is the power; `a and b` / `a or b` / `not a` combine conditions and stop at the first answer that decides the result; `x in items` asks whether `x` is among them; `x is None` asks whether it is exactly `None`.

```python
sys.exit(main())
```

- `sys.exit(main())`: calling `sys.exit(main())`, which ends the program with the given exit code.

#### `scripts/pause_demo.py`

```python
"""A paused run, answered by a reviewer, survives a server restart and resumes; then the audit trail is replayed.

Pass --local to use db/assistant.sqlite (rebuilt first) instead of a temporary file.

Two server processes share one database file: the first pauses the run and takes the reviewer's answer (an empty answer
and an answer that cites no page are refused first); it is stopped with SIGTERM; the second finds the run in the database
and resumes it with the validated answer in the model's context. This is what `make pause-demo` shows.
"""
```

- The docstring (documentation kept with the code) says: *A paused run, answered by a reviewer, survives a server restart and resumes; then the audit trail is replayed. Pass --local to use db/assistant.sqlite (rebuilt first) instead of a temporary file. Two server processes share one database file: the first pauses the run and takes the reviewer's answer (an empty answer and an answer that cites no page are refused first); it is stopped with SIGTERM; ...*

```python
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import os`: makes the module `os` available (operating-system services: environment variables, paths, processes).
- `import signal`: makes the module `signal` available (operating-system signals such as SIGTERM).
- `import socket`: makes the module `socket` available (network connections at the lowest level).
- `import subprocess`: makes the module `subprocess` available (starting other programs).

```python
import sys
import tempfile
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
```

- `import sys`: makes the module `sys` available (facts about the running Python program: arguments, exit, standard streams).
- `import tempfile`: makes the module `tempfile` available (temporary files and folders).
- `import time`: makes the module `time` available (clocks and sleeping).
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `import httpx`: makes the module `httpx` available (an HTTP client library).
- `ROOT = Path(__file__).resolve().parents[1]`: stores the item `Path(__file__).resolve().parents[1]` in `ROOT`.

```python
CUSTOMER = {"Authorization": "Bearer demo-customer-token"}
REVIEWER = {"Authorization": "Bearer demo-reviewer-token"}
QUESTION = "Can I get a refund on an order from seventy five days ago?"
```

- `CUSTOMER = {"Authorization": "Bearer demo-customer-token"}`: stores a new dict with 1 entries in `CUSTOMER`.
- `REVIEWER = {"Authorization": "Bearer demo-reviewer-token"}`: stores a new dict with 1 entries in `REVIEWER`.
- `QUESTION = "Can I get a refund on an order from seventy five days a...`: stores the text `'Can I get a refund on an order from seventy five days ago?'` in `QUESTION`.

```python
def free_port() -> int:
```

- Defines the function `free_port`.
- Gives back a value of type `int`.

```python
"""A port nothing is listening on."""
```

- The docstring (documentation kept with the code) says: *A port nothing is listening on.*

```python
with socket.socket() as probe:
```

- Opens `socket.socket()` as `probe` for the indented lines, and cleans it up when they end (even after an error).

> **`with`.** `with thing as name:` uses a resource for the indented lines and then cleans it up, even if an error happens: a file is closed, a lock is released, a database transaction is committed or rolled back.

```python
probe.bind(("127.0.0.1", 0))
return int(probe.getsockname()[1])
```

- `probe.bind(("127.0.0.1", 0))`: calling `probe.bind(("127.0.0.1", 0))`, which attaches a socket to an address and port.
- `return int(probe.getsockname()[1])`: ends the function and gives back the result of calling `int(probe.getsockname()[1])`, which turns `probe.getsockname()[1]` into a whole number.

```python
def start(database: Path) -> tuple[subprocess.Popen[bytes], str]:
```

- Defines the function `start`.
- Parameters:
  - `database`, type `Path`.
- Gives back a value of type `tuple[subprocess.Popen[bytes], str]`.

```python
"""Start the server on a free port over the given database file and wait for /healthz."""
```

- The docstring (documentation kept with the code) says: *Start the server on a free port over the given database file and wait for /healthz.*

```python
port = free_port()
env = {
    **os.environ,
    "PROJECT_ROOT": str(ROOT),
    "PORT": str(port),
    "DATABASE": str(database),
    "LOG_LEVEL": "WARNING",
}
```

- `port = free_port()`: stores the result of calling `free_port()` in `port`.
- `env = { **os.environ, "PROJECT_ROOT": str(ROOT), "PORT": str(port),...`: stores a new dict with 5 entries in `env`.

```python
process = subprocess.Popen([sys.executable, "-m", "streaming_assistant.interfaces.cli", "serve"], env=env, cwd=ROOT)
base = f"http://127.0.0.1:{port}"
```

- `process = subprocess.Popen([sys.executable, "-m", "streaming_assist...`: stores the result of calling `subprocess.Popen([sys.executable, "-m", "streaming_assistant.interfaces.cli", "serve"],...`, which makes a `Popen` object from `[sys.executable, "-m", "streaming_assistant.interfaces.cli", "serve"]` with the named values `env`, `cwd` in `process`.
- `base = f"http://127.0.0.1:{port}"`: stores the text built by the f-string `f"http://127.0.0.1:{port}"` in `base`.

```python
for _ in range(300):
```

- Repeats the indented lines once for each item of `range(300)`, naming the current item `_`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

> **`try` / `except` / `finally`.** Code in `try` runs; if it raises an error of the kind named in `except`, that block runs instead of the program stopping. `else` runs only if there was no error. `finally` always runs last. `raise` makes an error on purpose; `raise ... from other` records the earlier error as its cause.

```python
if httpx.get(base + "/healthz", timeout=1).status_code == 200:
```

- Checks whether `httpx.get(base + "/healthz", timeout=1).status_code` equals `200`. If so, the indented lines run.

```python
return process, base
```

- `return process, base`: ends the function and gives back a tuple of 2 items.

```python
except httpx.HTTPError:
```

- If an error of kind `httpx.HTTPError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
time.sleep(0.1)
```

- `time.sleep(0.1)`: calling `time.sleep(0.1)`, which waits `0.1` seconds.

```python
process.kill()
raise SystemExit("the server did not start")
```

- `process.kill()`: calling `process.kill()`, which sends a signal to a process.
- `raise SystemExit("the server did not start")`: stops with an error of kind `SystemExit` with the message `"the server did not start"`. Whoever called this code must handle it or the program stops.

```python
def events(response: httpx.Response) -> list[tuple[str, dict[str, object]]]:
```

- Defines the function `events`.
- Parameters:
  - `response`, type `httpx.Response`.
- Gives back a value of type `list[tuple[str, dict[str, object]]]`.

```python
"""Parse a finished server-sent-event body into (name, data) pairs."""
```

- The docstring (documentation kept with the code) says: *Parse a finished server-sent-event body into (name, data) pairs.*

```python
parsed, name = [], ""
```

- `parsed, name = [], ""`: unpacks a tuple of 2 items into the names `parsed`, `name`, one item each.

```python
for line in response.text.splitlines():
```

- Repeats the indented lines once for each item of `response.text.splitlines()`, naming the current item `line`.

```python
if line.startswith("event: "):
```

- Checks whether `line.startswith("event: ")` is true (the call asks whether `line` begins with `"event: "`). If so, the indented lines run.

```python
name = line.removeprefix("event: ")
```

- `name = line.removeprefix("event: ")`: stores the result of calling `line.removeprefix("event: ")`, which cuts `"event: "` off the start of `line` in `name`.

```python
elif line.startswith("data: "):
```

- Otherwise, checks whether `line.startswith("data: ")` is true (the call asks whether `line` begins with `"data: "`). If so, the indented lines run.

```python
parsed.append((name, json.loads(line.removeprefix("data: "))))
```

- `parsed.append((name, json.loads(line.removeprefix("data: "))))`: calling `parsed.append((name, json.loads(line.removeprefix("data: "))))`, which adds `(name, json.loads(line.removeprefix("data: ")))` to the end of `parsed`.

```python
return parsed
```

- `return parsed`: ends the function and gives back the value of `parsed`.

```python
def main() -> int:
```

- Defines the function `main`.
- Gives back a value of type `int`.

```python
"""Run the demonstration; returns 0 when every expected step happened."""
```

- The docstring (documentation kept with the code) says: *Run the demonstration; returns 0 when every expected step happened.*

```python
local = "--local" in sys.argv
database = (
    ROOT / "db/assistant.sqlite" if local else Path(tempfile.mkdtemp(prefix="pause-demo-")) / "assistant.sqlite"
)
subprocess.run(
    [sys.executable, "-m", "streaming_assistant.interfaces.cli", "db"],
    env={**os.environ, "PROJECT_ROOT": str(ROOT), "DATABASE": str(database)},
    cwd=ROOT,
    check=True,
    stdout=subprocess.DEVNULL,
)
```

- `local = "--local" in sys.argv`: stores whether `"--local"` is among `sys.argv` in `local`.
- `database = ( ROOT / "db/assistant.sqlite" if local else Path(tempfi...`: stores `ROOT / "db/assistant.sqlite"` when `local` is truthy (not `None`, `False`, zero or empty), otherwise `Path(tempfile.mkdtemp(prefix="pause-demo-")) / "assistant.sqlite"` in `database`.
- `subprocess.run( [sys.executable, "-m", "streaming_assistant.interfa...`: calling `subprocess.run( [sys.executable, "-m", "streaming_assistant.interfaces.cli", "db"], env...`, which runs a program or a coroutine The named values are `env`, `cwd`, `check`, `stdout`..

> **`a if cond else b`.** An expression that gives `a` when the condition holds and `b` otherwise.

```python
first, base = start(database)
```

- `first, base = start(database)`: unpacks the result of calling `start(database)`, which starts  into the names `first`, `base`, one item each.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
asked = httpx.post(base + "/ask", json={"question": QUESTION}, headers=CUSTOMER, timeout=30)
run_id = asked.headers["x-run-id"]
names = [name for name, _ in events(asked)]
print(f"asked: {QUESTION}\n  events: {names}")
waiting = httpx.get(base + "/reviews", headers=REVIEWER).json()
retrieved = waiting[0]["retrieved"]
```

- `asked = httpx.post(base + "/ask", json={"question": QUESTION}, head...`: stores the result of calling `httpx.post(base + "/ask", json={"question": QUESTION}, headers=CUSTOMER, timeout=30)`, which sends an HTTP POST request The named values are `json`, `headers`, `timeout`. in `asked`.
- `run_id = asked.headers["x-run-id"]`: stores the item `asked.headers["x-run-id"]` in `run_id`.
- `names = [name for name, _ in events(asked)]`: stores a list built by running `name` for each `name, _` in `events(asked)` in `names`.
- `print(f"asked: {QUESTION}\n events: {names}")`: calling `print(f"asked: {QUESTION}\n events: {names}")`, which writes `f"asked: {QUESTION}\n events: {names}"` to the screen (standard output).
- `waiting = httpx.get(base + "/reviews", headers=REVIEWER).json()`: stores the result of calling `httpx.get(base + "/reviews", headers=REVIEWER).json()` in `waiting`.
- `retrieved = waiting[0]["retrieved"]`: stores the item `waiting[0]["retrieved"]` in `retrieved`.

> **Comprehensions.** `[f(x) for x in items if test(x)]` builds a new list: run `f` on every item that passes the test. With `{k: v for ...}` it builds a dict, with `{x for ...}` a set. With round brackets it is a generator expression: the values are produced one at a time, only when something asks for the next one.

```python
print(f"reviewer screen shows {len(waiting)} waiting run(s): {waiting[0]['reason']}, retrieved {retrieved}")
empty = httpx.post(
    base + f"/reviews/{run_id}/answer", headers=REVIEWER, json={"reviewer_id": "ana", "answer": " "}
)
no_cite = httpx.post(
    base + f"/reviews/{run_id}/answer", headers=REVIEWER, json={"reviewer_id": "ana", "answer": "Sure."}
)
print(
    f"empty answer -> {empty.status_code}; answer citing no page -> {no_cite.status_code}: {no_cite.json()['detail']}"
)
```

- `print(f"reviewer screen shows {len(waiting)} waiting run(s): {waiti...`: calling `print(f"reviewer screen shows {len(waiting)} waiting run(s): {waiting[0]['reason']}, re...`, which writes `f"reviewer screen shows {len(waiting)} waiting run(s): {waiting[0]['reason']}, retrieve...` to the screen (standard output).
- `empty = httpx.post( base + f"/reviews/{run_id}/answer", headers=REV...`: stores the result of calling `httpx.post( base + f"/reviews/{run_id}/answer", headers=REVIEWER, json={"reviewer_id": ...`, which sends an HTTP POST request The named values are `headers`, `json`. in `empty`.
- `no_cite = httpx.post( base + f"/reviews/{run_id}/answer", headers=R...`: stores the result of calling `httpx.post( base + f"/reviews/{run_id}/answer", headers=REVIEWER, json={"reviewer_id": ...`, which sends an HTTP POST request The named values are `headers`, `json`. in `no_cite`.
- `print( f"empty answer -> {empty.status_code}; answer citing no page...`: calling `print( f"empty answer -> {empty.status_code}; answer citing no page -> {no_cite.status_...`, which writes `f"empty answer -> {empty.status_code}; answer citing no page -> {no_cite.status_code}: ...` to the screen (standard output).

```python
accepted = httpx.post(
    base + f"/reviews/{run_id}/answer",
    headers=REVIEWER,
    json={
        "reviewer_id": "ana",
        "answer": "Your order is outside the 30 day window, so I approved a store credit instead of a refund.",
        "cited": retrieved[:1],
    },
)
```

- `accepted = httpx.post( base + f"/reviews/{run_id}/answer", headers=...`: stores the result of calling `httpx.post( base + f"/reviews/{run_id}/answer", headers=REVIEWER, json={ "reviewer_id":...`, which sends an HTTP POST request The named values are `headers`, `json`. in `accepted`.

```python
print(f"valid answer -> {accepted.status_code} {accepted.json()}")
```

- `print(f"valid answer -> {accepted.status_code} {accepted.json()}")`: calling `print(f"valid answer -> {accepted.status_code} {accepted.json()}")`, which writes `f"valid answer -> {accepted.status_code} {accepted.json()}"` to the screen (standard output).

```python
finally:
```

- Always runs last, whether or not an error happened. It is used to clean up.

```python
first.send_signal(signal.SIGTERM)
first.wait(timeout=20)
```

- `first.send_signal(signal.SIGTERM)`: calling `first.send_signal(signal.SIGTERM)`.
- `first.wait(timeout=20)`: calling `first.wait(timeout=20)`, which waits for `first` The named values are `timeout`..

```python
print("server stopped; starting a second server on the same database file")
second, base = start(database)
```

- `print("server stopped; starting a second server on the same databas...`: calling `print("server stopped; starting a second server on the same database file")`, which writes `"server stopped; starting a second server on the same database file"` to the screen (standard output).
- `second, base = start(database)`: unpacks the result of calling `start(database)`, which starts  into the names `second`, `base`, one item each.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
status = httpx.get(base + f"/runs/{run_id}/status", headers=CUSTOMER).json()["status"]
resumed = httpx.get(base + f"/runs/{run_id}/resume", headers=CUSTOMER, timeout=30)
parsed = events(resumed)
text = "".join(str(data["text"]) for name, data in parsed if name == "token")
print(f"after restart the run is '{status}'; resumed events: {[name for name, _ in parsed]}")
print(f"customer saw: {text}")
```

- `status = httpx.get(base + f"/runs/{run_id}/status", headers=CUSTOME...`: stores the item `httpx.get(base + f"/runs/{run_id}/status", headers=CUSTOMER).json()["status"]` in `status`.
- `resumed = httpx.get(base + f"/runs/{run_id}/resume", headers=CUSTOM...`: stores the result of calling `httpx.get(base + f"/runs/{run_id}/resume", headers=CUSTOMER, timeout=30)`, which looks up `base + f"/runs/{run_id}/resume"` in `httpx`; a second value is the answer when the key is missing The named values are `headers`, `timeout`. in `resumed`.
- `parsed = events(resumed)`: stores the result of calling `events(resumed)`, which is this repository's own `events` (in `scripts/pause_demo.py`): parse a finished server-sent-event body into (name, data) pairs in `parsed`.
- `text = "".join(str(data["text"]) for name, data in parsed if name =...`: stores the result of calling `"".join(str(data["text"]) for name, data in parsed if name == "token")`, which glues the items of `(str(data["text"]) for name, data in parsed if name == "token")` together with `""` between them in `text`.
- `print(f"after restart the run is '{status}'; resumed events: {[name...`: calling `print(f"after restart the run is '{status}'; resumed events: {[name for name, _ in pars...`, which writes `f"after restart the run is '{status}'; resumed events: {[name for name, _ in parsed]}"` to the screen (standard output).
- `print(f"customer saw: {text}")`: calling `print(f"customer saw: {text}")`, which writes `f"customer saw: {text}"` to the screen (standard output).

```python
verified = httpx.get(base + "/audit/verify", headers=REVIEWER).json()
print(f"audit chain: {verified}")
```

- `verified = httpx.get(base + "/audit/verify", headers=REVIEWER).json()`: stores the result of calling `httpx.get(base + "/audit/verify", headers=REVIEWER).json()` in `verified`.
- `print(f"audit chain: {verified}")`: calling `print(f"audit chain: {verified}")`, which writes `f"audit chain: {verified}"` to the screen (standard output).

```python
finally:
```

- Always runs last, whether or not an error happened. It is used to clean up.

```python
second.send_signal(signal.SIGTERM)
second.wait(timeout=20)
```

- `second.send_signal(signal.SIGTERM)`: calling `second.send_signal(signal.SIGTERM)`.
- `second.wait(timeout=20)`: calling `second.wait(timeout=20)`, which waits for `second` The named values are `timeout`..

```python
print("replay of the audit trail:")
replay = subprocess.run(
    [sys.executable, "-m", "streaming_assistant.interfaces.cli", "replay", run_id],
    env={**os.environ, "PROJECT_ROOT": str(ROOT), "DATABASE": str(database)},
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=True,
).stdout
```

- `print("replay of the audit trail:")`: calling `print("replay of the audit trail:")`, which writes `"replay of the audit trail:"` to the screen (standard output).
- `replay = subprocess.run( [sys.executable, "-m", "streaming_assistan...`: stores `subprocess.run( [sys.executable, "-m", "streaming_assistant.interfaces.cli", "replay", ...` in `replay`.

```python
print(replay.rstrip())
steps = [line.split()[1] for line in replay.splitlines()]
ok = (
    names[-2:] == ["paused", "done"]
    and accepted.status_code == 200
    and empty.status_code == 422
    and status == "answered"
    and [name for name, _ in parsed][-1] == "done"
    and verified["first_broken_index"] is None
    and steps[:4] == ["received", "paused", "answered", "validated"]
    and "resumed" in steps
    and steps[-1] == "shown"
)
```

- `print(replay.rstrip())`: calling `print(replay.rstrip())`, which writes `replay.rstrip()` to the screen (standard output).
- `steps = [line.split()[1] for line in replay.splitlines()]`: stores a list built by running `line.split()[1]` for each `line` in `replay.splitlines()` in `steps`.
- `ok = ( names[-2:] == ["paused", "done"] and accepted.status_code ==...`: stores `names[-2:] == ["paused", "done"] and accepted.status_code == 200 and empty.status_code ...` (the first operand that decides the and) in `ok`.

```python
print("ok" if ok else "NOT OK")
return 0 if ok else 1
```

- `print("ok" if ok else "NOT OK")`: calling `print("ok" if ok else "NOT OK")`, which writes `"ok" if ok else "NOT OK"` to the screen (standard output).
- `return 0 if ok else 1`: ends the function and gives back `0` when `ok` is truthy (not `None`, `False`, zero or empty), otherwise `1`.

```python
if __name__ == "__main__":
```

- Checks whether `__name__` equals `"__main__"`. If so, the indented lines run.

```python
sys.exit(main())
```

- `sys.exit(main())`: calling `sys.exit(main())`, which ends the program with the given exit code.

#### `scripts/record_streams.py`

```python
"""Record the streams for eight sample questions into a cassette that the recorded adapter replays offline.

python scripts/record_streams.py --author   # write tests/fixtures/cassettes/stream-v1.json from the scripted model (not a model recording)
python scripts/record_streams.py            # MODEL_ADAPTER=claude: call the real model, write tests/fixtures/cassettes/live-v1.json (needs a key)
"""
```

- The docstring (documentation kept with the code) says: *Record the streams for eight sample questions into a cassette that the recorded adapter replays offline. python scripts/record_streams.py --author # write tests/fixtures/cassettes/stream-v1.json from the scripted model (not a model recording) python scripts/record_streams.py # MODEL_ADAPTER=claude: call the real model, write tests/fixtures/cassettes/live-v1.json (needs a key)*

```python
from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import replace
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import asyncio`: makes the module `asyncio` available (the standard library's tools for asynchronous code (many waits interleaved on one thread)).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import os`: makes the module `os` available (operating-system services: environment variables, paths, processes).
- `import sys`: makes the module `sys` available (facts about the running Python program: arguments, exit, standard streams).
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`replace`: a name provided by that module.)

```python
from pathlib import Path

from streaming_assistant.infrastructure.recorded_stream import RecordingStreamingModel
from streaming_assistant.infrastructure.scripted_stream import Pace, ScriptedStreamingModel
from streaming_assistant.infrastructure.settings import Settings
from streaming_assistant.interfaces.measure import collect
from streaming_assistant.interfaces.wiring import build_components, build_model
```

- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from streaming_assistant.infrastructure.recorded_stream import ...`: takes names from `streaming_assistant.infrastructure.recorded_stream`, this repository's own code. (`RecordingStreamingModel`: Wraps a model and writes every stream it returns to a cassette.)
- `from streaming_assistant.infrastructure.scripted_stream import ...`: takes names from `streaming_assistant.infrastructure.scripted_stream`, this repository's own code. (`Pace`: Latency settings in milliseconds.) (`ScriptedStreamingModel`: Async streaming with counters: tokens produced (what would be billed), cancellations and their times.)
- `from streaming_assistant.infrastructure.settings import ...`: takes names from `streaming_assistant.infrastructure.settings`, this repository's own code. (`Settings`: Everything the programs read from the environment.)
- `from streaming_assistant.interfaces.measure import ...`: takes names from `streaming_assistant.interfaces.measure`, this repository's own code. (`collect`: Run one question in process; returns the events and the refs that were retrieved for it.)
- `from streaming_assistant.interfaces.wiring import ...`: takes names from `streaming_assistant.interfaces.wiring`, this repository's own code. (`build_components`: Wire everything.) (`build_model`: The scripted model (offline, with the pace from the settings), the recorded one, or Claude.)

```python
ROOT = Path(__file__).resolve().parents[1]
SAMPLE = 8
```

- `ROOT = Path(__file__).resolve().parents[1]`: stores the item `Path(__file__).resolve().parents[1]` in `ROOT`.
- `SAMPLE = 8`: stores the number `8` in `SAMPLE`.

```python
def questions() -> list[str]:
```

- Defines the function `questions`.
- Gives back a value of type `list[str]`.

```python
"""The first eight questions that should be answered, in file order."""
```

- The docstring (documentation kept with the code) says: *The first eight questions that should be answered, in file order.*

```python
rows = (json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines())
return [row["question"] for row in rows if not row["should_pause"]][:SAMPLE]
```

- `rows = (json.loads(line) for line in (ROOT / "data/questions.jsonl"...`: stores a stream of values (computed one at a time) built by running `json.loads(line)` for each `line` in `(ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines()` in `rows`.
- `return [row["question"] for row in rows if not row["should_pause"]]...`: ends the function and gives back the item `[row["question"] for row in rows if not row["should_pause"]][:SAMPLE]`.

```python
async def record(settings: Settings, author: bool) -> Path:
```

- Defines the async function `record` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `settings`, type `Settings`.
  - `author`, type `bool`.
- Gives back a value of type `Path`.

> **`async def` and `await`.** An `async def` function is a coroutine: calling it does not run the body but makes an object that the event loop runs. `await` inside it pauses this function until the awaited thing is ready, and lets the loop run other work meanwhile, all on one thread.

```python
"""Run the questions through the real path with the wrapped model and return the cassette path."""
```

- The docstring (documentation kept with the code) says: *Run the questions through the real path with the wrapped model and return the cassette path.*

```python
if author:
```

- Checks whether `author` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
inner = ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0))
path = ROOT / "tests/fixtures/cassettes/stream-v1.json"
provenance = "authored by scripts/record_streams.py --author from the scripted streaming model; not a model recording. Replace with `make record`."
model_id = "authored-scripted-stream"
```

- `inner = ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0))`: stores the result of calling `ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0))`, which is this repository's own `ScriptedStreamingModel` (in `src/streaming_assistant/infrastructure/scripted_stream.py`): async streaming with counters: tokens produced (what would be billed), cancellations and their times in `inner`.
- `path = ROOT / "tests/fixtures/cassettes/stream-v1.json"`: stores the path `ROOT / "tests/fixtures/cassettes/stream-v1.json"` (`/` joins path parts) in `path`.
- `provenance = "authored by scripts/record_streams.py --author from t...`: stores the text `'authored by scripts/record_streams.py --author from the scripted streaming model; not ...` in `provenance`.
- `model_id = "authored-scripted-stream"`: stores the text `'authored-scripted-stream'` in `model_id`.

```python
else:
```

- Runs when none of the conditions above held.

```python
inner = build_model(settings)
path = ROOT / "tests/fixtures/cassettes/live-v1.json"
provenance = f"recorded from {settings.model_ids['standard']} through scripts/record_streams.py"
model_id = settings.model_ids["standard"]
```

- `inner = build_model(settings)`: stores the result of calling `build_model(settings)`, which is this repository's own `build_model` (in `src/streaming_assistant/interfaces/wiring.py`): the scripted model (offline, with the pace from the settings), the recorded one, or Claude in `inner`.
- `path = ROOT / "tests/fixtures/cassettes/live-v1.json"`: stores the path `ROOT / "tests/fixtures/cassettes/live-v1.json"` (`/` joins path parts) in `path`.
- `provenance = f"recorded from {settings.model_ids['standard']} throu...`: stores the text built by the f-string `f"recorded from {settings.model_ids['standard']} through scripts/record_streams.py"` in `provenance`.
- `model_id = settings.model_ids["standard"]`: stores the item `settings.model_ids["standard"]` in `model_id`.

```python
recorder = RecordingStreamingModel(inner, path, model_id, provenance)
components = build_components(replace(settings, database=":memory:"), model=recorder, fresh=True)
```

- `recorder = RecordingStreamingModel(inner, path, model_id, provenance)`: stores the result of calling `RecordingStreamingModel(inner, path, model_id, provenance)`, which is this repository's own `RecordingStreamingModel` (in `src/streaming_assistant/infrastructure/recorded_stream.py`): wraps a model and writes every stream it returns to a cassette in `recorder`.
- `components = build_components(replace(settings, database=":memory:"...`: stores the result of calling `build_components(replace(settings, database=":memory:"), model=recorder, fresh=True)`, which is this repository's own `build_components` (in `src/streaming_assistant/interfaces/wiring.py`): wire everything The named values are `model`, `fresh`. in `components`.

```python
for number, question in enumerate(questions()):
```

- Repeats the indented lines once for each item of `enumerate(questions())`, naming the current item the names `number`, `question`.

```python
await collect(components, f"record-{number}", question)
```

- `await collect(components, f"record-{number}", question)`: waits for the result of calling `collect(components, f"record-{number}", question)`, which is this repository's own `collect` (in `src/streaming_assistant/interfaces/measure.py`): run one question in process; returns the events and the refs that were retrieved for it to finish.

```python
return path
```

- `return path`: ends the function and gives back the value of `path`.

```python
def main() -> int:
```

- Defines the function `main`.
- Gives back a value of type `int`.

```python
"""Entry point."""
```

- The docstring (documentation kept with the code) says: *Entry point.*

```python
author = "--author" in sys.argv
settings = Settings.from_environ({**os.environ, "PROJECT_ROOT": str(ROOT)})
```

- `author = "--author" in sys.argv`: stores whether `"--author"` is among `sys.argv` in `author`.
- `settings = Settings.from_environ({**os.environ, "PROJECT_ROOT": str...`: stores the result of calling `Settings.from_environ({**os.environ, "PROJECT_ROOT": str(ROOT)})`, which is this repository's own `from_environ` (in `src/streaming_assistant/infrastructure/settings.py`): read and validate; raises `ConfigurationError` naming the first bad variable in `settings`.

```python
if not author and settings.model_adapter != "claude":
```

- Checks whether it is not the case that `author` is truthy (not `None`, `False`, zero or empty) and `settings.model_adapter` is different from `"claude"`. If so, the indented lines run.

```python
print(
    "set MODEL_ADAPTER=claude and ANTHROPIC_API_KEY to record from the real model, or pass --author",
    file=sys.stderr,
)
return 2
```

- `print( "set MODEL_ADAPTER=claude and ANTHROPIC_API_KEY to record fr...`: calling `print( "set MODEL_ADAPTER=claude and ANTHROPIC_API_KEY to record from the real model, o...`, which writes `"set MODEL_ADAPTER=claude and ANTHROPIC_API_KEY to record from the real model, or pass ...` to the screen (standard output) The named values are `file`..
- `return 2`: ends the function and gives back the number `2`.

```python
path = asyncio.run(record(settings, author))
print(f"wrote {path.relative_to(ROOT)}")
return 0
```

- `path = asyncio.run(record(settings, author))`: stores the result of calling `asyncio.run(record(settings, author))`, which runs a program or a coroutine in `path`.
- `print(f"wrote {path.relative_to(ROOT)}")`: calling `print(f"wrote {path.relative_to(ROOT)}")`, which writes `f"wrote {path.relative_to(ROOT)}"` to the screen (standard output).
- `return 0`: ends the function and gives back the number `0`.

```python
if __name__ == "__main__":
```

- Checks whether `__name__` equals `"__main__"`. If so, the indented lines run.

```python
sys.exit(main())
```

- `sys.exit(main())`: calling `sys.exit(main())`, which ends the program with the given exit code.

#### `scripts/run_queries.py`

```python
"""Run sql/003_queries.sql against the local database and print each result: what `make queries` shows."""
```

- The docstring (documentation kept with the code) says: *Run sql/003_queries.sql against the local database and print each result: what `make queries` shows.*

```python
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import sqlite3`: makes the module `sqlite3` available (the standard library's SQLite database driver).
- `import sys`: makes the module `sys` available (facts about the running Python program: arguments, exit, standard streams).
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `ROOT = Path(__file__).resolve().parents[1]`: stores the item `Path(__file__).resolve().parents[1]` in `ROOT`.

```python
def main() -> int:
```

- Defines the function `main`.
- Gives back a value of type `int`.

```python
"""Each statement is preceded by a `-- name` comment."""
```

- The docstring (documentation kept with the code) says: *Each statement is preceded by a `-- name` comment.*

```python
database = ROOT / "db/assistant.sqlite"
```

- `database = ROOT / "db/assistant.sqlite"`: stores the path `ROOT / "db/assistant.sqlite"` (`/` joins path parts) in `database`.

```python
if not database.exists():
```

- Checks whether it is not the case that `database.exists()` is true (the call asks whether `database` exists on disk). If so, the indented lines run.

```python
print("no database yet: run `make up` first", file=sys.stderr)
return 1
```

- ``print("no database yet: run `make up` first", file=sys.stderr)``: calling ``print("no database yet: run `make up` first", file=sys.stderr)``, which writes ``"no database yet: run `make up` first"`` to the screen (standard output) The named values are `file`..
- `return 1`: ends the function and gives back the number `1`.

```python
connection = sqlite3.connect(database)
name, statement = "", []
```

- `connection = sqlite3.connect(database)`: stores the result of calling `sqlite3.connect(database)`, which opens a connection in `connection`.
- `name, statement = "", []`: unpacks a tuple of 2 items into the names `name`, `statement`, one item each.

```python
for line in (ROOT / "sql/003_queries.sql").read_text(encoding="utf-8").splitlines():
```

- Repeats the indented lines once for each item of `(ROOT / "sql/003_queries.sql").read_text(encoding="utf-8").splitlines()`, naming the current item `line`.

```python
if line.startswith("--"):
```

- Checks whether `line.startswith("--")` is true (the call asks whether `line` begins with `"--"`). If so, the indented lines run.

```python
name = line.removeprefix("--").strip() or name
continue
```

- `name = line.removeprefix("--").strip() or name`: stores `line.removeprefix("--").strip() or name` (the first operand that decides the or) in `name`.
- `continue`: skips to the next round of the loop.

```python
statement.append(line)
```

- `statement.append(line)`: calling `statement.append(line)`, which adds `line` to the end of `statement`.

```python
if line.rstrip().endswith(";"):
```

- Checks whether `line.rstrip().endswith(";")` is true (the call asks whether `line.rstrip()` ends with `";"`). If so, the indented lines run.

```python
cursor = connection.execute("\n".join(statement))
columns = [column[0] for column in cursor.description or ()]
rows = cursor.fetchall()
print(f"== {name}")
print("  " + " | ".join(columns))
```

- `cursor = connection.execute("\n".join(statement))`: stores the result of calling `connection.execute("\n".join(statement))`, which sends the SQL statement `"\n".join(statement)` to the database in `cursor`.
- `columns = [column[0] for column in cursor.description or ()]`: stores a list built by running `column[0]` for each `column` in `cursor.description or ()` in `columns`.
- `rows = cursor.fetchall()`: stores the result of calling `cursor.fetchall()`, which takes all remaining rows of the result in `rows`.
- `print(f"== {name}")`: calling `print(f"== {name}")`, which writes `f"== {name}"` to the screen (standard output).
- `print(" " + " | ".join(columns))`: calling `print(" " + " | ".join(columns))`, which writes `" " + " | ".join(columns)` to the screen (standard output).

```python
for row in rows:
```

- Repeats the indented lines once for each item of `rows`, naming the current item `row`.

```python
print("  " + " | ".join(str(value) for value in row))
```

- `print(" " + " | ".join(str(value) for value in row))`: calling `print(" " + " | ".join(str(value) for value in row))`, which writes `" " + " | ".join(str(value) for value in row)` to the screen (standard output).

```python
if not rows:
```

- Checks whether it is not the case that `rows` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
print("  (no rows)")
```

- `print(" (no rows)")`: calling `print(" (no rows)")`, which writes `" (no rows)"` to the screen (standard output).

```python
statement = []
```

- `statement = []`: stores a new list (empty) in `statement`.

```python
connection.close()
return 0
```

- `connection.close()`: calling `connection.close()`, which closes `connection`.
- `return 0`: ends the function and gives back the number `0`.

```python
if __name__ == "__main__":
```

- Checks whether `__name__` equals `"__main__"`. If so, the indented lines run.

```python
sys.exit(main())
```

- `sys.exit(main())`: calling `sys.exit(main())`, which ends the program with the given exit code.

#### `src/streaming_assistant/__init__.py`

```python
"""A streaming support assistant with Stop, real citations, seven failure states, a pause-for-approval path with a hash-chained audit log, and a first-token budget proven under load."""
```

- The docstring (documentation kept with the code) says: *A streaming support assistant with Stop, real citations, seven failure states, a pause-for-approval path with a hash-chained audit log, and a first-token budget proven under load.*

#### `src/streaming_assistant/application/__init__.py`

```python
"""The application layer."""
```

- The docstring (documentation kept with the code) says: *The application layer.*

#### `src/streaming_assistant/application/assistant.py`

```python
"""The streaming assistant: prepare a request stage by stage (timed), then stream typed events with seven failure states,
a pause-for-approval path, real citations and an audit trail."""
```

- The docstring (documentation kept with the code) says: *The streaming assistant: prepare a request stage by stage (timed), then stream typed events with seven failure states, a pause-for-approval path, real citations and an audit trail.*

```python
from __future__ import annotations

import asyncio
import hashlib
import threading
import time
from collections import Counter
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import asyncio`: makes the module `asyncio` available (the standard library's tools for asynchronous code (many waits interleaved on one thread)).
- `import hashlib`: makes the module `hashlib` available (hash functions such as SHA-256).
- `import threading`: makes the module `threading` available (threads, locks and events).
- `import time`: makes the module `time` available (clocks and sleeping).
- `from collections import ...`: takes names from `collections` (the standard library's extra container types (Counter, defaultdict, deque)). (`Counter`: a dict that counts: `counter[x] += 1`.)

```python
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any
```

- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`AsyncIterator`: a name provided by that module.) (`Callable`: the type hint for a function value.) (`Mapping`: the type hint for a read-only dict-like collection.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.) (`field`: describes one dataclass field in more detail (its default, or how to build the default).)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`Any`: the type hint meaning 'anything'.)

```python
from streaming_assistant.application.ports import (
    AuditLog,
    Authenticator,
    Catalog,
    Clock,
    PausedRun,
    Retriever,
    RunStore,
    StreamingModel,
    StreamRequest,
    TextDelta,
    Usage,
)
```

- `from streaming_assistant.application.ports import ...`: takes names from `streaming_assistant.application.ports`, this repository's own code. (`AuditLog`: An append-only, hash-chained log.) (`Authenticator`: Checks a bearer token.) (`Catalog`: The help pages by id: a reviewer can only cite what exists, and a citation opens the page at its section.) (`Clock`: The current time.) (`PausedRun`: A run waiting for, or past, a reviewer.) (`Retriever`: Finds the help sections for a question.) (`RunStore`: Durable state of paused runs: it must survive a restart.) (`StreamingModel`: A model that streams.) (`StreamRequest`: One streamed completion.) (`TextDelta`: A piece of the answer.) (`Usage`: Token counts, sent when the stream ends normally.)

```python
from streaming_assistant.application.prompt import assemble
from streaming_assistant.domain.citations import MarkerStripper, check_refs
from streaming_assistant.domain.errors import ProviderError, RateLimitedError, RefusedError, UnknownRunError
from streaming_assistant.domain.retrieval import Hit
from streaming_assistant.domain.routing import (
    ANSWER,
    LOW_CONFIDENCE,
    NO_EVIDENCE,
    PAUSE,
    Route,
    Thresholds,
    decide_route,
)
```

- `from streaming_assistant.application.prompt import ...`: takes names from `streaming_assistant.application.prompt`, this repository's own code. (`assemble`: Stable instructions first (cacheable, the same for every request), then the passages and the question.)
- `from streaming_assistant.domain.citations import ...`: takes names from `streaming_assistant.domain.citations`, this repository's own code. (`MarkerStripper`: Removes `[page#section]` markers from a stream of text pieces, even when a marker is split across pieces, and remembers the refs it saw.) (`check_refs`: (sections that may be shown, number dropped).)
- `from streaming_assistant.domain.errors import ...`: takes names from `streaming_assistant.domain.errors`, this repository's own code. (`ProviderError`: The model provider failed (a server error or a dropped connection).) (`RateLimitedError`: The model provider answered 429.) (`RefusedError`: The model declined to answer.) (`UnknownRunError`: No run with this id.)
- `from streaming_assistant.domain.retrieval import ...`: takes names from `streaming_assistant.domain.retrieval`, this repository's own code. (`Hit`: A section the retriever returned, with its raw score and the share of the question's weight it covers.)
- `from streaming_assistant.domain.routing import ...`: takes names from `streaming_assistant.domain.routing`, this repository's own code. (`ANSWER`: a name defined in this repository.) (`LOW_CONFIDENCE`: a name defined in this repository.) (`NO_EVIDENCE`: a name defined in this repository.) (`PAUSE`: a name defined in this repository.) (`Route`: The decision and why.) (`Thresholds`: Retrieval coverage at which a question is answered, called thin, or sent to a person.) (`decide_route`: A question that matches a needs-a-person pattern pauses; so does one no page covers (when pausing is on).)

```python
STATES: Mapping[str, tuple[str, str]] = {
    "timeout": ("The assistant took too long to start answering.", "retry"),
    "provider_error": ("Something went wrong on our side while answering.", "retry"),
    "rate_limited": ("We are getting a lot of questions right now. Please try again in a moment.", "retry"),
    "refusal": ("I can't help with that here. A person on the team can.", "contact"),
    "no_evidence": ("I could not find anything in the help center about that.", "contact"),
    "low_confidence": (
        "I found something related, but I am not sure it answers your question. Try rephrasing it.",
        "rephrase",
    ),
    "stopped": ("Stopped. Nothing more will be shown.", "retry"),
}
```

- `STATES: Mapping[str, tuple[str, str]] = { "timeout": ("The assistan...`: stores a new dict with 7 entries in `STATES`, whose type is declared as `Mapping[str, tuple[str, str]]`.

> **A type hint.** `x: int = 5` stores 5 in `x` and records that `x` is meant to hold an `int`. Python itself does not enforce the hint; the type checker `mypy` reads it before the program runs and complains if the code disagrees.

```python
class UnauthorizedError(Exception):
```

- Defines the class `UnauthorizedError`.
- It extends `Exception`: it is a kind of error that can be raised and caught.

> **A class.** `class Name:` defines a new kind of object. The functions inside it are methods; the first parameter, called `self` by habit, is the object the method was called on. `__init__` runs when an object is made. `Name(...)` makes an object (an instance) of the class. A class listed in brackets after the name is a base class: the new class inherits its methods.

```python
"""The bearer token is missing or unknown."""
```

- The docstring (documentation kept with the code) says: *The bearer token is missing or unknown.*

```python
@dataclass(frozen=True, slots=True)
class Event:
```

- Defines the class `Event`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

> **Decorators.** A line `@something` above a function or class passes the definition through `something`, and the name then refers to what comes back.

> **`@dataclass`.** A decorator is a line starting with `@` that wraps the definition below it. `@dataclass` reads the annotated fields in the class body and writes `__init__`, `__repr__` and `__eq__` for the class. `frozen=True` makes the objects read-only after creation, so an accidental change raises an error. `slots=True` stores attributes more compactly.

```python
"""One server-sent event: a type name and its data."""
```

- The docstring (documentation kept with the code) says: *One server-sent event: a type name and its data.*

```python
name: str
data: dict[str, Any]
```

- `name: str`: a field named `name` of type `str`, no default (must be given).
- `data: dict[str, Any]`: a field named `data` of type `dict[str, Any]`, no default (must be given).

```python
@dataclass(frozen=True, slots=True)
class AssistantConfig:
```

- Defines the class `AssistantConfig`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""Behavior switches. The last four are the load test's levers (each one is a fix measured against the baseline)."""
```

- The docstring (documentation kept with the code) says: *Behavior switches. The last four are the load test's levers (each one is a fix measured against the baseline).*

```python
stable_prompt: str
thresholds: Thresholds = field(default_factory=Thresholds)
first_token_timeout_seconds: float = 3.0
idle_timeout_seconds: float = 5.0
pause_enabled: bool = True
retrieval_limit: int = 3
stable_prefix_first: bool = True
parallel_prep: bool = True
```

- `stable_prompt: str`: a field named `stable_prompt` of type `str`, no default (must be given).
- `thresholds: Thresholds = field(default_factory=Thresholds)`: a field named `thresholds` of type `Thresholds`, default `field(default_factory=Thresholds)`.
- `first_token_timeout_seconds: float = 3.0`: a field named `first_token_timeout_seconds` of type `float`, default `3.0`.
- `idle_timeout_seconds: float = 5.0`: a field named `idle_timeout_seconds` of type `float`, default `5.0`.
- `pause_enabled: bool = True`: a field named `pause_enabled` of type `bool`, default `True`.
- `retrieval_limit: int = 3`: a field named `retrieval_limit` of type `int`, default `3`.
- `stable_prefix_first: bool = True`: a field named `stable_prefix_first` of type `bool`, default `True`.
- `parallel_prep: bool = True`: a field named `parallel_prep` of type `bool`, default `True`.

```python
route_easy_to_fast: bool = False
easy_coverage: float = 0.8
```

- `route_easy_to_fast: bool = False`: a field named `route_easy_to_fast` of type `bool`, default `False`.
- `easy_coverage: float = 0.8`: a field named `easy_coverage` of type `float`, default `0.8`.

```python
class StopRegistry:
```

- Defines the class `StopRegistry`.

```python
"""Run ids a user asked to stop, safe to use from any thread."""
```

- The docstring (documentation kept with the code) says: *Run ids a user asked to stop, safe to use from any thread.*

```python
def __init__(self) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `None`.

```python
self._lock = threading.Lock()
self._stopped: set[str] = set()
```

- `self._lock = threading.Lock()`: stores the result of calling `threading.Lock()`, which makes a `Lock` object in `self._lock`.
- `self._stopped: set[str] = set()`: stores the result of calling `set()`, which sets  in `self._stopped`, whose type is declared as `set[str]`.

```python
def request(self, run_id: str) -> None:
```

- Defines the method `request`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run_id`, type `str`.
- Gives back a value of type `None`.

```python
"""Ask for a run to stop."""
```

- The docstring (documentation kept with the code) says: *Ask for a run to stop.*

```python
with self._lock:
```

- Opens `self._lock` for the indented lines, and releases it when they end (even after an error).

```python
self._stopped.add(run_id)
```

- `self._stopped.add(run_id)`: calling `self._stopped.add(run_id)`, which puts `run_id` into the set `self._stopped`.

```python
def is_requested(self, run_id: str) -> bool:
```

- Defines the method `is_requested`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run_id`, type `str`.
- Gives back a value of type `bool`.

```python
"""True once a stop was asked for."""
```

- The docstring (documentation kept with the code) says: *True once a stop was asked for.*

```python
with self._lock:
```

- Opens `self._lock` for the indented lines, and releases it when they end (even after an error).

```python
return run_id in self._stopped
```

- `return run_id in self._stopped`: ends the function and gives back whether `run_id` is among `self._stopped`.

```python
def clear(self, run_id: str) -> None:
```

- Defines the method `clear`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run_id`, type `str`.
- Gives back a value of type `None`.

```python
"""Forget a run."""
```

- The docstring (documentation kept with the code) says: *Forget a run.*

```python
with self._lock:
```

- Opens `self._lock` for the indented lines, and releases it when they end (even after an error).

```python
self._stopped.discard(run_id)
```

- `self._stopped.discard(run_id)`: calling `self._stopped.discard(run_id)`, which removes `run_id` from the set `self._stopped` if it is there.

```python
@dataclass
class Prepared:
```

- Defines the class `Prepared`.
- `@dataclass`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields.

```python
"""Everything decided before the first byte: who, what was retrieved, the route, the prompt and the stage times."""
```

- The docstring (documentation kept with the code) says: *Everything decided before the first byte: who, what was retrieved, the route, the prompt and the stage times.*

```python
run_id: str
question: str
hits: list[Hit]
route: Route
request: StreamRequest | None
timings: dict[str, float]
started: float
extra_refs: tuple[str, ...] = ()
```

- `run_id: str`: a field named `run_id` of type `str`, no default (must be given).
- `question: str`: a field named `question` of type `str`, no default (must be given).
- `hits: list[Hit]`: a field named `hits` of type `list[Hit]`, no default (must be given).
- `route: Route`: a field named `route` of type `Route`, no default (must be given).
- `request: StreamRequest | None`: a field named `request` of type `StreamRequest | None`, no default (must be given).
- `timings: dict[str, float]`: a field named `timings` of type `dict[str, float]`, no default (must be given).
- `started: float`: a field named `started` of type `float`, no default (must be given).
- `extra_refs: tuple[str, ...] = ()`: a field named `extra_refs` of type `tuple[str, ...]`, default `()`.

```python
reviewer_answer: str | None = None
```

- `reviewer_answer: str | None = None`: a field named `reviewer_answer` of type `str | None`, default `None`.

```python
def _timed[T](function: Callable[[], T]) -> tuple[T, float]:
```

- Defines the function `_timed`.
- Parameters:
  - `function`, type `Callable[[], T]`.
- Gives back a value of type `tuple[T, float]`.

```python
started = time.perf_counter()
result = function()
return result, (time.perf_counter() - started) * 1000
```

- `started = time.perf_counter()`: stores the result of calling `time.perf_counter()`, which reads the high-resolution timer in seconds in `started`.
- `result = function()`: stores the result of calling `function()` in `result`.
- `return result, (time.perf_counter() - started) * 1000`: ends the function and gives back a tuple of 2 items.

```python
class Assistant:
```

- Defines the class `Assistant`.

```python
"""Orchestrates one request. Collaborators arrive through ports so tests can force every state."""
```

- The docstring (documentation kept with the code) says: *Orchestrates one request. Collaborators arrive through ports so tests can force every state.*

```python
def __init__(
    self,
    retriever: Retriever,
    models: Mapping[str, StreamingModel],
    runs: RunStore,
    audit: AuditLog,
    authenticator: Authenticator,
    clock: Clock,
    config: AssistantConfig,
    catalog: Catalog,
    stops: StopRegistry | None = None,
) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `retriever`, type `Retriever`.
  - `models`, type `Mapping[str, StreamingModel]`.
  - `runs`, type `RunStore`.
  - `audit`, type `AuditLog`.
  - `authenticator`, type `Authenticator`.
  - `clock`, type `Clock`.
  - `config`, type `AssistantConfig`.
  - `catalog`, type `Catalog`.
  - `stops`, type `StopRegistry | None`, optional (default `None`).
- Gives back a value of type `None`.

```python
self._retriever = retriever
self._models = models
self._runs = runs
self._audit = audit
self._auth = authenticator
self._clock = clock
```

- `self._retriever = retriever`: stores the value of `retriever` in `self._retriever`.
- `self._models = models`: stores the value of `models` in `self._models`.
- `self._runs = runs`: stores the value of `runs` in `self._runs`.
- `self._audit = audit`: stores the value of `audit` in `self._audit`.
- `self._auth = authenticator`: stores the value of `authenticator` in `self._auth`.
- `self._clock = clock`: stores the value of `clock` in `self._clock`.

```python
self._config = config
self._catalog = catalog
self._stops = stops or StopRegistry()
self.stats: Counter[str] = Counter()
```

- `self._config = config`: stores the value of `config` in `self._config`.
- `self._catalog = catalog`: stores the value of `catalog` in `self._catalog`.
- `self._stops = stops or StopRegistry()`: stores `stops or StopRegistry()` (the first operand that decides the or) in `self._stops`.
- `self.stats: Counter[str] = Counter()`: stores the result of calling `Counter()`, which makes a `Counter` object in `self.stats`, whose type is declared as `Counter[str]`.

```python
@property
def stops(self) -> StopRegistry:
```

- Defines the method `stops`.
- `@property`: the method is read like an attribute.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `StopRegistry`.

> **`@property`, `@staticmethod`, `@classmethod`.** `@property` lets a method be read like an attribute (`obj.size` instead of `obj.size()`). `@staticmethod` is a function that lives in the class but needs no object. `@classmethod` receives the class itself (named `cls`) instead of an object, often to build objects in another way.

```python
"""The registry the stop endpoint writes to."""
```

- The docstring (documentation kept with the code) says: *The registry the stop endpoint writes to.*

```python
return self._stops
```

- `return self._stops`: ends the function and gives back `self._stops`.

```python
async def prepare(self, run_id: str, question: str, token: str) -> Prepared:
```

- Defines the async method `prepare` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run_id`, type `str`.
  - `question`, type `str`.
  - `token`, type `str`.
- Gives back a value of type `Prepared`.

```python
"""Authenticate, retrieve, assemble and route; each stage is timed inside the real path.

With `parallel_prep` the authentication and the retrieval run at the same time; `overlap_ms` is the time that
saved, so the stage times still add up to the measured total.
"""
```

- The docstring (documentation kept with the code) says: *Authenticate, retrieve, assemble and route; each stage is timed inside the real path. With `parallel_prep` the authentication and the retrieval run at the same time; `overlap_ms` is the time that saved, so the stage times still add up to the measured total.*

```python
started = time.perf_counter()
limit = self._config.retrieval_limit
```

- `started = time.perf_counter()`: stores the result of calling `time.perf_counter()`, which reads the high-resolution timer in seconds in `started`.
- `limit = self._config.retrieval_limit`: stores `self._config.retrieval_limit` in `limit`.

```python
if self._config.parallel_prep:
```

- Checks whether `self._config.parallel_prep` is truthy. If so, the indented lines run.

```python
(role, auth_ms), (hits, retrieval_ms) = await asyncio.gather(
    asyncio.to_thread(_timed, lambda: self._auth.role_of(token)),
    asyncio.to_thread(_timed, lambda: self._retriever.search(question, limit)),
)
```

- `(role, auth_ms), (hits, retrieval_ms) = await asyncio.gather( async...`: unpacks the answer of the result of calling `asyncio.gather( asyncio.to_thread(_timed, lambda: self._auth.role_of(token)), asyncio.t...`, which runs several coroutines at once and collects their answers once the wait is over into the names `(role, auth_ms)`, `(hits, retrieval_ms)`, one item each.

```python
else:
```

- Runs when none of the conditions above held.

```python
role, auth_ms = await asyncio.to_thread(_timed, lambda: self._auth.role_of(token))
```

- `role, auth_ms = await asyncio.to_thread(_timed, lambda: self._auth....`: unpacks the answer of the result of calling `asyncio.to_thread(_timed, lambda: self._auth.role_of(token))`, which runs a blocking function on a separate thread once the wait is over into the names `role`, `auth_ms`, one item each.

```python
if role is None:
```

- Checks whether `role` is nothing (`None`). If so, the indented lines run.

```python
raise UnauthorizedError
```

- `raise UnauthorizedError`: raises the error `UnauthorizedError`.

```python
hits, retrieval_ms = await asyncio.to_thread(_timed, lambda: self._retriever.search(question, limit))
```

- `hits, retrieval_ms = await asyncio.to_thread(_timed, lambda: self._...`: unpacks the answer of the result of calling `asyncio.to_thread(_timed, lambda: self._retriever.search(question, limit))`, which runs a blocking function on a separate thread once the wait is over into the names `hits`, `retrieval_ms`, one item each.

```python
if role is None:
```

- Checks whether `role` is nothing (`None`). If so, the indented lines run.

```python
raise UnauthorizedError
```

- `raise UnauthorizedError`: raises the error `UnauthorizedError`.

```python
wall_ms = (time.perf_counter() - started) * 1000
overlap_ms = max(0.0, auth_ms + retrieval_ms - wall_ms)
route = decide_route(question, hits, self._config.thresholds, pause_enabled=self._config.pause_enabled)
request, assembly_ms = None, 0.0
```

- `wall_ms = (time.perf_counter() - started) * 1000`: stores `(time.perf_counter() - started) * 1000`, which multiplies `time.perf_counter() - started` and `1000` in `wall_ms`.
- `overlap_ms = max(0.0, auth_ms + retrieval_ms - wall_ms)`: stores the result of calling `max(0.0, auth_ms + retrieval_ms - wall_ms)`, which picks the largest of `0.0`, `auth_ms + retrieval_ms - wall_ms` in `overlap_ms`.
- `route = decide_route(question, hits, self._config.thresholds, pause...`: stores the result of calling `decide_route(question, hits, self._config.thresholds, pause_enabled=self._config.pause_...`, which is this repository's own `decide_route` (in `src/streaming_assistant/domain/routing.py`): a question that matches a needs-a-person pattern pauses; so does one no page covers (when pausing is on) The named values are `pause_enabled`. in `route`.
- `request, assembly_ms = None, 0.0`: unpacks a tuple of 2 items into the names `request`, `assembly_ms`, one item each.

```python
if route.kind == ANSWER:
```

- Checks whether `route.kind` equals `ANSWER`. If so, the indented lines run.

```python
tier = (
    "fast"
    if self._config.route_easy_to_fast and hits[0].coverage >= self._config.easy_coverage
    else "standard"
)
request, assembly_ms = _timed(
    lambda: assemble(
        self._config.stable_prompt, hits, question, stable_first=self._config.stable_prefix_first, tier=tier
    )
)
```

- `tier = ( "fast" if self._config.route_easy_to_fast and hits[0].cove...`: stores `"fast"` when `self._config.route_easy_to_fast` is truthy and `hits[0].coverage` is greater than or equal to `self._config.easy_coverage`, otherwise `"standard"` in `tier`.
- `request, assembly_ms = _timed( lambda: assemble( self._config.stabl...`: unpacks the result of calling `_timed( lambda: assemble( self._config.stable_prompt, hits, question, stable_first=self...` into the names `request`, `assembly_ms`, one item each.

```python
timings = {
    "auth_ms": auth_ms,
    "retrieval_ms": retrieval_ms,
    "assembly_ms": assembly_ms,
    "overlap_ms": overlap_ms,
}
return Prepared(run_id, question, hits, route, request, timings, started)
```

- `timings = { "auth_ms": auth_ms, "retrieval_ms": retrieval_ms, "asse...`: stores a new dict with 4 entries in `timings`.
- `return Prepared(run_id, question, hits, route, request, timings, st...`: ends the function and gives back the result of calling `Prepared(run_id, question, hits, route, request, timings, started)`, which is this repository's own `Prepared` (in `src/streaming_assistant/application/assistant.py`): everything decided before the first byte: who, what was retrieved, the route, the prompt and the stage times.

```python
async def stream(self, prepared: Prepared) -> AsyncIterator[Event]:
```

- Defines the async method `stream` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `prepared`, type `Prepared`.
- Gives back a value of type `AsyncIterator[Event]`.

```python
"""Typed events for one run. The stream always ends with `done`, `paused` or a `state` followed by `done`."""
```

- The docstring (documentation kept with the code) says: *Typed events for one run. The stream always ends with `done`, `paused` or a `state` followed by `done`.*

```python
run_id = prepared.run_id
self._audit.append(
    run_id,
    "received",
    "customer",
    "question sha256:" + hashlib.sha256(prepared.question.encode()).hexdigest()[:12],
)
route = prepared.route
```

- `run_id = prepared.run_id`: stores `prepared.run_id` in `run_id`.
- `self._audit.append( run_id, "received", "customer", "question sha25...`: calling `self._audit.append( run_id, "received", "customer", "question sha256:" + hashlib.sha256...`, which adds `run_id` to the end of `self._audit`.
- `route = prepared.route`: stores `prepared.route` in `route`.

> **`yield`.** A function with `yield` is a generator: calling it does not run the body at once; each time the caller asks for the next value, the body runs up to the next `yield`, gives that value out, and waits.

```python
if route.kind == PAUSE:
```

- Checks whether `route.kind` equals `PAUSE`. If so, the indented lines run.

```python
self._runs.save_pause(
    PausedRun(
        run_id, prepared.question, tuple(hit.section.ref for hit in prepared.hits), route.reason, "waiting"
    ),
    self._clock.now(),
)
self._audit.append(run_id, "paused", "assistant", route.reason)
self.stats["paused"] += 1
```

- `self._runs.save_pause( PausedRun( run_id, prepared.question, tuple(...`: calling `self._runs.save_pause( PausedRun( run_id, prepared.question, tuple(hit.section.ref for ...`.
- `self._audit.append(run_id, "paused", "assistant", route.reason)`: calling `self._audit.append(run_id, "paused", "assistant", route.reason)`, which adds `run_id` to the end of `self._audit`.
- `self.stats["paused"] += 1`: adds `1` to `self.stats["paused"]` and keeps the result there.

```python
yield Event(
    "paused",
    {
        "run_id": run_id,
        "reason": route.reason,
        "message": "A person on the team will check this and the answer will appear here.",
    },
)
```

- `yield Event( "paused", { "run_id": run_id, "reason": route.reason, ...`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
yield self._done(prepared, None, 0, "paused")
return
```

- `yield self._done(prepared, None, 0, "paused")`: hands a value to whoever is looping over this generator, then waits to be asked for the next.
- `return`: ends the function, giving back nothing (`None`).

```python
if route.kind in (LOW_CONFIDENCE, NO_EVIDENCE):
```

- Checks whether `route.kind` is among `(LOW_CONFIDENCE, NO_EVIDENCE)`. If so, the indented lines run.

```python
self._audit.append(run_id, "state", "assistant", route.kind)
self.stats[route.kind] += 1
yield self._state(route.kind)
yield self._done(prepared, None, 0, route.kind)
return
```

- `self._audit.append(run_id, "state", "assistant", route.kind)`: calling `self._audit.append(run_id, "state", "assistant", route.kind)`, which adds `run_id` to the end of `self._audit`.
- `self.stats[route.kind] += 1`: adds `1` to `self.stats[route.kind]` and keeps the result there.
- `yield self._state(route.kind)`: hands a value to whoever is looping over this generator, then waits to be asked for the next.
- `yield self._done(prepared, None, 0, route.kind)`: hands a value to whoever is looping over this generator, then waits to be asked for the next.
- `return`: ends the function, giving back nothing (`None`).

```python
async for event in self._answer(prepared):
```

- Repeats the indented lines once for each item of `self._answer(prepared)`, naming the current item `event`. (`async for` waits for each item.)

```python
yield event
```

- `yield event`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
async def resume(self, run_id: str) -> AsyncIterator[Event]:
```

- Defines the async method `resume` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run_id`, type `str`.
- Gives back a value of type `AsyncIterator[Event]`.

```python
"""Continue a paused run whose reviewer answer was validated; the answer goes into the model's context."""
```

- The docstring (documentation kept with the code) says: *Continue a paused run whose reviewer answer was validated; the answer goes into the model's context.*

```python
run = self._runs.get(run_id)
```

- `run = self._runs.get(run_id)`: stores the result of calling `self._runs.get(run_id)`, which is this repository's own `get` (in `src/streaming_assistant/application/ports.py`): one run, or None in `run`.

```python
if run is None:
```

- Checks whether `run` is nothing (`None`). If so, the indented lines run.

```python
raise UnknownRunError(run_id)
```

- `raise UnknownRunError(run_id)`: stops with an error of kind `UnknownRunError` with the message `run_id`. Whoever called this code must handle it or the program stops.

```python
if run.status != "answered" or run.answer is None:
```

- Checks whether `run.status` is different from `"answered"` or `run.answer` is nothing (`None`). If so, the indented lines run.

```python
raise UnknownRunError(f"{run_id} is {run.status}, not answered")
```

- `raise UnknownRunError(f"{run_id} is {run.status}, not answered")`: stops with an error of kind `UnknownRunError` with the message `f"{run_id} is {run.status}, not answered"`. Whoever called this code must handle it or the program stops.

```python
started = time.perf_counter()
hits, retrieval_ms = await asyncio.to_thread(
    _timed, lambda: self._retriever.search(run.question, self._config.retrieval_limit)
)
request = assemble(
    self._config.stable_prompt,
    hits,
    run.question,
    stable_first=True,
    tier="standard",
    reviewer_answer=run.answer,
)
```

- `started = time.perf_counter()`: stores the result of calling `time.perf_counter()`, which reads the high-resolution timer in seconds in `started`.
- `hits, retrieval_ms = await asyncio.to_thread( _timed, lambda: self....`: unpacks the answer of the result of calling `asyncio.to_thread( _timed, lambda: self._retriever.search(run.question, self._config.re...`, which runs a blocking function on a separate thread once the wait is over into the names `hits`, `retrieval_ms`, one item each.
- `request = assemble( self._config.stable_prompt, hits, run.question,...`: stores the result of calling `assemble( self._config.stable_prompt, hits, run.question, stable_first=True, tier="stan...`, which is this repository's own `assemble` (in `src/streaming_assistant/application/prompt.py`): stable instructions first (cacheable, the same for every request), then the passages and the question The named values are `stable_first`, `tier`, `reviewer_answer`. in `request`.

```python
prepared = Prepared(
    run_id,
    run.question,
    hits,
    Route(ANSWER, "reviewer answer"),
    request,
    {"auth_ms": 0.0, "retrieval_ms": retrieval_ms, "assembly_ms": 0.0, "overlap_ms": 0.0},
    started,
    run.cited,
    run.answer,
)
```

- `prepared = Prepared( run_id, run.question, hits, Route(ANSWER, "rev...`: stores the result of calling `Prepared( run_id, run.question, hits, Route(ANSWER, "reviewer answer"), request, {"auth...`, which is this repository's own `Prepared` (in `src/streaming_assistant/application/assistant.py`): everything decided before the first byte: who, what was retrieved, the route, the prompt and the stage times in `prepared`.

```python
self._audit.append(run_id, "resumed", "assistant", f"reviewer {run.reviewer_id}")
self._runs.mark_resumed(run_id, self._clock.now())
```

- `self._audit.append(run_id, "resumed", "assistant", f"reviewer {run....`: calling `self._audit.append(run_id, "resumed", "assistant", f"reviewer {run.reviewer_id}")`, which adds `run_id` to the end of `self._audit`.
- `self._runs.mark_resumed(run_id, self._clock.now())`: calling `self._runs.mark_resumed(run_id, self._clock.now())`, which is this repository's own `mark_resumed` (in `src/streaming_assistant/application/ports.py`): move the run to `resumed`.

```python
async for event in self._answer(prepared):
```

- Repeats the indented lines once for each item of `self._answer(prepared)`, naming the current item `event`. (`async for` waits for each item.)

```python
yield event
```

- `yield event`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
async def _answer(self, prepared: Prepared) -> AsyncIterator[Event]:
```

- Defines the async method `_answer` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `prepared`, type `Prepared`.
- Gives back a value of type `AsyncIterator[Event]`.

```python
run_id, request = prepared.run_id, prepared.request
assert request is not None
model = self._models[request.tier]
strip, parts = MarkerStripper(), []
usage: Usage | None = None
first_token_ms = None
```

- `run_id, request = prepared.run_id, prepared.request`: unpacks a tuple of 2 items into the names `run_id`, `request`, one item each.
- `assert request is not None`: checks that `request` is something (not `None`). A false check stops the test as failed.
- `model = self._models[request.tier]`: stores the item `self._models[request.tier]` in `model`.
- `strip, parts = MarkerStripper(), []`: unpacks a tuple of 2 items into the names `strip`, `parts`, one item each.
- `usage: Usage | None = None`: stores nothing (`None`) in `usage`, whose type is declared as `Usage | None`.
- `first_token_ms = None`: stores nothing (`None`) in `first_token_ms`.

> **`assert`.** `assert condition` does nothing when the condition is true and stops with an `AssertionError` when it is false. In a test file, a failing assert is how a test fails. `pytest` rewrites assert lines so its failure message shows the values involved.

```python
call_started = time.perf_counter()
upstream = model.stream(request).__aiter__()
failure: str | None = None
```

- `call_started = time.perf_counter()`: stores the result of calling `time.perf_counter()`, which reads the high-resolution timer in seconds in `call_started`.
- `upstream = model.stream(request).__aiter__()`: stores the result of calling `model.stream(request).__aiter__()` in `upstream`.
- `failure: str | None = None`: stores nothing (`None`) in `failure`, whose type is declared as `str | None`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
while True:
```

- Repeats the indented lines for as long as `True` is true.

> **`while`.** `while condition:` repeats the indented lines for as long as the condition stays true.

```python
timeout = (
    self._config.first_token_timeout_seconds
    if first_token_ms is None
    else self._config.idle_timeout_seconds
)
```

- `timeout = ( self._config.first_token_timeout_seconds if first_token...`: stores `self._config.first_token_timeout_seconds` when `first_token_ms` is nothing (`None`), otherwise `self._config.idle_timeout_seconds` in `timeout`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
chunk = await asyncio.wait_for(upstream.__anext__(), timeout)
```

- `chunk = await asyncio.wait_for(upstream.__anext__(), timeout)`: stores the answer of the result of calling `asyncio.wait_for(upstream.__anext__(), timeout)` once the wait is over in `chunk`.

```python
except StopAsyncIteration:
```

- If an error of kind `StopAsyncIteration` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
break
```

- `break`: leaves the loop now.

```python
except TimeoutError:
```

- If an error of kind `TimeoutError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
failure = "timeout"
break
```

- `failure = "timeout"`: stores the text `'timeout'` in `failure`.
- `break`: leaves the loop now.

```python
except RateLimitedError:
```

- If an error of kind `RateLimitedError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
failure = "rate_limited"
break
```

- `failure = "rate_limited"`: stores the text `'rate_limited'` in `failure`.
- `break`: leaves the loop now.

```python
except RefusedError:
```

- If an error of kind `RefusedError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
failure = "refusal"
break
```

- `failure = "refusal"`: stores the text `'refusal'` in `failure`.
- `break`: leaves the loop now.

```python
except ProviderError:
```

- If an error of kind `ProviderError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
failure = "provider_error"
break
```

- `failure = "provider_error"`: stores the text `'provider_error'` in `failure`.
- `break`: leaves the loop now.

```python
if isinstance(chunk, Usage):
```

- Checks whether `isinstance(chunk, Usage)` is true (the call asks whether `chunk` is a `Usage`). If so, the indented lines run.

```python
usage = chunk
continue
```

- `usage = chunk`: stores the value of `chunk` in `usage`.
- `continue`: skips to the next round of the loop.

```python
assert isinstance(chunk, TextDelta)
visible = strip.feed(chunk.text)
```

- `assert isinstance(chunk, TextDelta)`: checks that `isinstance(chunk, TextDelta)` is true (the call asks whether `chunk` is a `TextDelta`). A false check stops the test as failed.
- `visible = strip.feed(chunk.text)`: stores the result of calling `strip.feed(chunk.text)`, which is this repository's own `feed` (in `src/streaming_assistant/domain/citations.py`): text that is safe to show now in `visible`.

```python
if visible:
```

- Checks whether `visible` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
if first_token_ms is None:
```

- Checks whether `first_token_ms` is nothing (`None`). If so, the indented lines run.

```python
first_token_ms = (time.perf_counter() - prepared.started) * 1000
prepared.timings["model_ms"] = (time.perf_counter() - call_started) * 1000
```

- `first_token_ms = (time.perf_counter() - prepared.started) * 1000`: stores `(time.perf_counter() - prepared.started) * 1000`, which multiplies `time.perf_counter() - prepared.started` and `1000` in `first_token_ms`.
- `prepared.timings["model_ms"] = (time.perf_counter() - call_started)...`: stores `(time.perf_counter() - call_started) * 1000`, which multiplies `time.perf_counter() - call_started` and `1000` in the slot `prepared.timings["model_ms"]`.

```python
parts.append(visible)
yield Event("token", {"text": visible})
```

- `parts.append(visible)`: calling `parts.append(visible)`, which adds `visible` to the end of `parts`.
- `yield Event("token", {"text": visible})`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
if self._stops.is_requested(run_id):
```

- Checks whether `self._stops.is_requested(run_id)` is true (the call is this repository's own `is_requested` (in `src/streaming_assistant/application/assistant.py`): true once a stop was asked for). If so, the indented lines run.

```python
await self._close(upstream)
self._audit.append(run_id, "stopped", "customer", "stop requested")
self.stats["stopped"] += 1
yield self._state("stopped")
yield self._done(prepared, usage, len("".join(parts).split()), "stopped", first_token_ms)
return
```

- `await self._close(upstream)`: waits for the result of calling `self._close(upstream)` to finish.
- `self._audit.append(run_id, "stopped", "customer", "stop requested")`: calling `self._audit.append(run_id, "stopped", "customer", "stop requested")`, which adds `run_id` to the end of `self._audit`.
- `self.stats["stopped"] += 1`: adds `1` to `self.stats["stopped"]` and keeps the result there.
- `yield self._state("stopped")`: hands a value to whoever is looping over this generator, then waits to be asked for the next.
- `yield self._done(prepared, usage, len("".join(parts).split()), "sto...`: hands a value to whoever is looping over this generator, then waits to be asked for the next.
- `return`: ends the function, giving back nothing (`None`).

```python
except asyncio.CancelledError:
```

- If an error of kind `asyncio.CancelledError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
self._audit.append(run_id, "stopped", "client", "connection closed")
self.stats["disconnected"] += 1
raise
```

- `self._audit.append(run_id, "stopped", "client", "connection closed")`: calling `self._audit.append(run_id, "stopped", "client", "connection closed")`, which adds `run_id` to the end of `self._audit`.
- `self.stats["disconnected"] += 1`: adds `1` to `self.stats["disconnected"]` and keeps the result there.
- `raise`: raises the error again.

```python
finally:
```

- Always runs last, whether or not an error happened. It is used to clean up.

```python
await self._close(upstream)
self._stops.clear(run_id)
```

- `await self._close(upstream)`: waits for the result of calling `self._close(upstream)` to finish.
- `self._stops.clear(run_id)`: calling `self._stops.clear(run_id)`, which is this repository's own `clear` (in `src/streaming_assistant/application/assistant.py`): forget a run.

```python
if failure is not None:
```

- Checks whether `failure` is something (not `None`). If so, the indented lines run.

```python
self._audit.append(run_id, "state", "assistant", failure)
self.stats[failure] += 1
yield self._state(failure)
yield self._done(prepared, usage, 0, failure, first_token_ms)
return
```

- `self._audit.append(run_id, "state", "assistant", failure)`: calling `self._audit.append(run_id, "state", "assistant", failure)`, which adds `run_id` to the end of `self._audit`.
- `self.stats[failure] += 1`: adds `1` to `self.stats[failure]` and keeps the result there.
- `yield self._state(failure)`: hands a value to whoever is looping over this generator, then waits to be asked for the next.
- `yield self._done(prepared, usage, 0, failure, first_token_ms)`: hands a value to whoever is looping over this generator, then waits to be asked for the next.
- `return`: ends the function, giving back nothing (`None`).

```python
tail = strip.finish()
```

- `tail = strip.finish()`: stores the result of calling `strip.finish()`, which is this repository's own `finish` (in `src/streaming_assistant/domain/citations.py`): whatever was held back at the end of the stream in `tail`.

```python
if tail:
```

- Checks whether `tail` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
parts.append(tail)
yield Event("token", {"text": tail})
```

- `parts.append(tail)`: calling `parts.append(tail)`, which adds `tail` to the end of `parts`.
- `yield Event("token", {"text": tail})`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
allowed = {hit.section.ref: hit.section for hit in prepared.hits}
```

- `allowed = {hit.section.ref: hit.section for hit in prepared.hits}`: stores a dict built by running `hit.section.ref` for each `hit` in `prepared.hits` in `allowed`.

```python
for ref in prepared.extra_refs:
```

- Repeats the indented lines once for each item of `prepared.extra_refs`, naming the current item `ref`.

```python
section = self._catalog.section(ref)
```

- `section = self._catalog.section(ref)`: stores the result of calling `self._catalog.section(ref)`, which is this repository's own `section` (in `src/streaming_assistant/application/ports.py`): the section a `page#anchor` ref names, or None in `section`.

```python
if section is not None:
```

- Checks whether `section` is something (not `None`). If so, the indented lines run.

```python
allowed[ref] = section
```

- `allowed[ref] = section`: stores the value of `section` in the slot `allowed[ref]`.

```python
shown, dropped = check_refs(strip.refs, allowed)
```

- `shown, dropped = check_refs(strip.refs, allowed)`: unpacks the result of calling `check_refs(strip.refs, allowed)`, which is this repository's own `check_refs` (in `src/streaming_assistant/domain/citations.py`): (sections that may be shown, number dropped) into the names `shown`, `dropped`, one item each.

```python
for section in shown:
```

- Repeats the indented lines once for each item of `shown`, naming the current item `section`.

```python
yield Event(
    "citation",
    {
        "page_id": section.page_id,
        "title": section.page_title,
        "section": section.heading,
        "anchor": section.anchor,
        "url": f"/pages/{section.page_id}#{section.anchor}",
    },
)
```

- `yield Event( "citation", { "page_id": section.page_id, "title": sec...`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
self.stats["dropped_citations"] += dropped
self.stats["answered"] += 1
self._audit.append(run_id, "citations", "assistant", f"shown={len(shown)} dropped={dropped}")
self._audit.append(run_id, "shown", "assistant", "".join(parts))
yield self._done(prepared, usage, len("".join(parts).split()), "answered", first_token_ms, dropped)
```

- `self.stats["dropped_citations"] += dropped`: adds `dropped` to `self.stats["dropped_citations"]` and keeps the result there.
- `self.stats["answered"] += 1`: adds `1` to `self.stats["answered"]` and keeps the result there.
- `self._audit.append(run_id, "citations", "assistant", f"shown={len(s...`: calling `self._audit.append(run_id, "citations", "assistant", f"shown={len(shown)} dropped={drop...`, which adds `run_id` to the end of `self._audit`.
- `self._audit.append(run_id, "shown", "assistant", "".join(parts))`: calling `self._audit.append(run_id, "shown", "assistant", "".join(parts))`, which adds `run_id` to the end of `self._audit`.
- `yield self._done(prepared, usage, len("".join(parts).split()), "ans...`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
@staticmethod
async def _close(upstream: Any) -> None:
```

- Defines the async method `_close` (a coroutine: calling it makes a job for the event loop to run).
- `@staticmethod`: a method of the class that does not receive an object
- Parameters:
  - `upstream`, type `Any`.
- Gives back a value of type `None`.

```python
close = getattr(upstream, "aclose", None)
```

- `close = getattr(upstream, "aclose", None)`: stores the result of calling `getattr(upstream, "aclose", None)`, which reads the attribute named `"aclose"` from `upstream` in `close`.

```python
if close is not None:
```

- Checks whether `close` is something (not `None`). If so, the indented lines run.

```python
await asyncio.shield(close())
```

- `await asyncio.shield(close())`: waits for the result of calling `asyncio.shield(close())` to finish.

```python
@staticmethod
def _state(name: str) -> Event:
```

- Defines the method `_state`.
- `@staticmethod`: a method of the class that does not receive an object
- Parameters:
  - `name`, type `str`.
- Gives back a value of type `Event`.

```python
message, action = STATES[name]
return Event("state", {"name": name, "message": message, "action": action})
```

- `message, action = STATES[name]`: unpacks the item `STATES[name]` into the names `message`, `action`, one item each.
- `return Event("state", {"name": name, "message": message, "action": ...`: ends the function and gives back the result of calling `Event("state", {"name": name, "message": message, "action": action})`, which is this repository's own `Event` (in `src/streaming_assistant/application/assistant.py`): one server-sent event: a type name and its data.

```python
@staticmethod
def _done(
    prepared: Prepared,
    usage: Usage | None,
    words: int,
    outcome: str,
    first_token_ms: float | None = None,
    dropped: int = 0,
) -> Event:
```

- Defines the method `_done`.
- `@staticmethod`: a method of the class that does not receive an object
- Parameters:
  - `prepared`, type `Prepared`.
  - `usage`, type `Usage | None`.
  - `words`, type `int`.
  - `outcome`, type `str`.
  - `first_token_ms`, type `float | None`, optional (default `None`).
  - `dropped`, type `int`, optional (default `0`).
- Gives back a value of type `Event`.

```python
timings = {key: round(value, 2) for key, value in prepared.timings.items()}
```

- `timings = {key: round(value, 2) for key, value in prepared.timings....`: stores a dict built by running `key` for each `key, value` in `prepared.timings.items()` in `timings`.

```python
if first_token_ms is not None:
```

- Checks whether `first_token_ms` is something (not `None`). If so, the indented lines run.

```python
timings["first_token_ms"] = round(first_token_ms, 2)
timings["stage_sum_ms"] = round(
    timings["auth_ms"]
    + timings["retrieval_ms"]
    - timings["overlap_ms"]
    + timings["assembly_ms"]
    + timings.get("model_ms", 0.0),
    2,
)
```

- `timings["first_token_ms"] = round(first_token_ms, 2)`: stores the result of calling `round(first_token_ms, 2)`, which rounds `first_token_ms` in the slot `timings["first_token_ms"]`.
- `timings["stage_sum_ms"] = round( timings["auth_ms"] + timings["retr...`: stores the result of calling `round( timings["auth_ms"] + timings["retrieval_ms"] - timings["overlap_ms"] + timings["...`, which rounds `timings["auth_ms"] + timings["retrieval_ms"] - timings["overlap_ms"] + timings["assembl...` in the slot `timings["stage_sum_ms"]`.

```python
return Event(
    "done",
    {
        "run_id": prepared.run_id,
        "outcome": outcome,
        "dropped_citations": dropped,
        "words": words,
        "usage": {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens} if usage else None,
        "timings": timings,
    },
)
```

- `return Event( "done", { "run_id": prepared.run_id, "outcome": outco...`: ends the function and gives back the result of calling `Event( "done", { "run_id": prepared.run_id, "outcome": outcome, "dropped_citations": dr...`, which is this repository's own `Event` (in `src/streaming_assistant/application/assistant.py`): one server-sent event: a type name and its data.

#### `src/streaming_assistant/application/ports.py`

```python
"""The boundaries the assistant talks through: the streaming model, the retriever, the stores, the clock."""
```

- The docstring (documentation kept with the code) says: *The boundaries the assistant talks through: the streaming model, the retriever, the stores, the clock.*

```python
from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from streaming_assistant.domain.audit import AuditEntry
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`AsyncIterator`: a name provided by that module.) (`Sequence`: the type hint for an ordered, indexable collection.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)
- `from datetime import ...`: takes names from `datetime` (dates, times and time spans). (`datetime`: the date-and-time type.)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`Protocol`: the base class for an interface: a list of methods something must have.)
- `from streaming_assistant.domain.audit import ...`: takes names from `streaming_assistant.domain.audit`, this repository's own code. (`AuditEntry`: One step of a run, with its place in the chain.)

```python
from streaming_assistant.domain.retrieval import Hit, Section
```

- `from streaming_assistant.domain.retrieval import ...`: takes names from `streaming_assistant.domain.retrieval`, this repository's own code. (`Hit`: A section the retriever returned, with its raw score and the share of the question's weight it covers.) (`Section`: One section of a help page; `anchor` is where a citation opens the page.)

```python
@dataclass(frozen=True, slots=True)
class TextDelta:
```

- Defines the class `TextDelta`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""A piece of the answer."""
```

- The docstring (documentation kept with the code) says: *A piece of the answer.*

```python
text: str
```

- `text: str`: a field named `text` of type `str`, no default (must be given).

```python
@dataclass(frozen=True, slots=True)
class Usage:
```

- Defines the class `Usage`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""Token counts, sent when the stream ends normally."""
```

- The docstring (documentation kept with the code) says: *Token counts, sent when the stream ends normally.*

```python
input_tokens: int
output_tokens: int
```

- `input_tokens: int`: a field named `input_tokens` of type `int`, no default (must be given).
- `output_tokens: int`: a field named `output_tokens` of type `int`, no default (must be given).

```python
Chunk = TextDelta | Usage
```

- `Chunk = TextDelta | Usage`: stores `TextDelta | Usage`, which combines (or) `TextDelta` and `Usage` in `Chunk`.

```python
@dataclass(frozen=True, slots=True)
class StreamRequest:
```

- Defines the class `StreamRequest`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""One streamed completion. `tier` lets a router send easy questions to a faster model."""
```

- The docstring (documentation kept with the code) says: *One streamed completion. `tier` lets a router send easy questions to a faster model.*

```python
system: str
user: str
prompt_version: str
tier: str = "standard"
```

- `system: str`: a field named `system` of type `str`, no default (must be given).
- `user: str`: a field named `user` of type `str`, no default (must be given).
- `prompt_version: str`: a field named `prompt_version` of type `str`, no default (must be given).
- `tier: str = "standard"`: a field named `tier` of type `str`, default `"standard"`.

```python
class StreamingModel(Protocol):
```

- Defines the class `StreamingModel`.
- It extends `Protocol`: it only lists the methods something must have (an interface), with no behavior of its own.

> **`Protocol`.** A class that lists methods without an implementation. It describes the shape something must have (an interface); any class with those methods fits, without naming the Protocol. The type checker enforces the match.

```python
"""A model that streams. Raises `ProviderError`, `RateLimitedError` or `RefusedError`; closing the iterator cancels
the upstream call."""
```

- The docstring (documentation kept with the code) says: *A model that streams. Raises `ProviderError`, `RateLimitedError` or `RefusedError`; closing the iterator cancels the upstream call.*

```python
def stream(self, request: StreamRequest) -> AsyncIterator[Chunk]:
```

- Defines the method `stream`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `request`, type `StreamRequest`.
- Gives back a value of type `AsyncIterator[Chunk]`.

```python
"""Stream the answer."""
```

- The docstring (documentation kept with the code) says: *Stream the answer.*

```python
...
```

- `...`: evaluates `...`.

```python
class Retriever(Protocol):
```

- Defines the class `Retriever`.
- It extends `Protocol`: it only lists the methods something must have (an interface), with no behavior of its own.

```python
"""Finds the help sections for a question."""
```

- The docstring (documentation kept with the code) says: *Finds the help sections for a question.*

```python
def search(self, query: str, limit: int = 3) -> list[Hit]:
```

- Defines the method `search`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `query`, type `str`.
  - `limit`, type `int`, optional (default `3`).
- Gives back a value of type `list[Hit]`.

```python
"""Best sections first."""
```

- The docstring (documentation kept with the code) says: *Best sections first.*

```python
...
```

- `...`: evaluates `...`.

```python
@dataclass(frozen=True, slots=True)
class PausedRun:
```

- Defines the class `PausedRun`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""A run waiting for, or past, a reviewer."""
```

- The docstring (documentation kept with the code) says: *A run waiting for, or past, a reviewer.*

```python
run_id: str
question: str
retrieved: tuple[str, ...]
reason: str
status: str
reviewer_id: str | None = None
answer: str | None = None
cited: tuple[str, ...] = ()
```

- `run_id: str`: a field named `run_id` of type `str`, no default (must be given).
- `question: str`: a field named `question` of type `str`, no default (must be given).
- `retrieved: tuple[str, ...]`: a field named `retrieved` of type `tuple[str, ...]`, no default (must be given).
- `reason: str`: a field named `reason` of type `str`, no default (must be given).
- `status: str`: a field named `status` of type `str`, no default (must be given).
- `reviewer_id: str | None = None`: a field named `reviewer_id` of type `str | None`, default `None`.
- `answer: str | None = None`: a field named `answer` of type `str | None`, default `None`.
- `cited: tuple[str, ...] = ()`: a field named `cited` of type `tuple[str, ...]`, default `()`.

```python
no_page: bool = False
```

- `no_page: bool = False`: a field named `no_page` of type `bool`, default `False`.

```python
class RunStore(Protocol):
```

- Defines the class `RunStore`.
- It extends `Protocol`: it only lists the methods something must have (an interface), with no behavior of its own.

```python
"""Durable state of paused runs: it must survive a restart."""
```

- The docstring (documentation kept with the code) says: *Durable state of paused runs: it must survive a restart.*

```python
def save_pause(self, run: PausedRun, at: datetime) -> None:
```

- Defines the method `save_pause`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run`, type `PausedRun`.
  - `at`, type `datetime`.
- Gives back a value of type `None`.

```python
"""Store a new paused run."""
```

- The docstring (documentation kept with the code) says: *Store a new paused run.*

```python
...
```

- `...`: evaluates `...`.

```python
def get(self, run_id: str) -> PausedRun | None:
```

- Defines the method `get`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run_id`, type `str`.
- Gives back a value of type `PausedRun | None`.

```python
"""One run, or None."""
```

- The docstring (documentation kept with the code) says: *One run, or None.*

```python
...
```

- `...`: evaluates `...`.

```python
def waiting(self, limit: int) -> Sequence[PausedRun]:
```

- Defines the method `waiting`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `limit`, type `int`.
- Gives back a value of type `Sequence[PausedRun]`.

```python
"""Runs waiting for a reviewer, oldest first."""
```

- The docstring (documentation kept with the code) says: *Runs waiting for a reviewer, oldest first.*

```python
...
```

- `...`: evaluates `...`.

```python
def record_answer(
    self, run_id: str, reviewer_id: str, answer: str, cited: Sequence[str], no_page: bool, at: datetime
) -> None:
```

- Defines the method `record_answer`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run_id`, type `str`.
  - `reviewer_id`, type `str`.
  - `answer`, type `str`.
  - `cited`, type `Sequence[str]`.
  - `no_page`, type `bool`.
  - `at`, type `datetime`.
- Gives back a value of type `None`.

```python
"""Store a validated reviewer answer and move the run to `answered`."""
```

- The docstring (documentation kept with the code) says: *Store a validated reviewer answer and move the run to `answered`.*

```python
...
```

- `...`: evaluates `...`.

```python
def mark_resumed(self, run_id: str, at: datetime) -> None:
```

- Defines the method `mark_resumed`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run_id`, type `str`.
  - `at`, type `datetime`.
- Gives back a value of type `None`.

```python
"""Move the run to `resumed`."""
```

- The docstring (documentation kept with the code) says: *Move the run to `resumed`.*

```python
...
```

- `...`: evaluates `...`.

```python
class AuditLog(Protocol):
```

- Defines the class `AuditLog`.
- It extends `Protocol`: it only lists the methods something must have (an interface), with no behavior of its own.

```python
"""An append-only, hash-chained log."""
```

- The docstring (documentation kept with the code) says: *An append-only, hash-chained log.*

```python
def append(self, run: str, step: str, actor: str, content: str) -> AuditEntry:
```

- Defines the method `append`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run`, type `str`.
  - `step`, type `str`.
  - `actor`, type `str`.
  - `content`, type `str`.
- Gives back a value of type `AuditEntry`.

```python
"""Add one step."""
```

- The docstring (documentation kept with the code) says: *Add one step.*

```python
...
```

- `...`: evaluates `...`.

```python
def entries(self, run: str | None = None) -> Sequence[AuditEntry]:
```

- Defines the method `entries`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run`, type `str | None`, optional (default `None`).
- Gives back a value of type `Sequence[AuditEntry]`.

```python
"""The whole chain, or the steps of one run (in chain order)."""
```

- The docstring (documentation kept with the code) says: *The whole chain, or the steps of one run (in chain order).*

```python
...
```

- `...`: evaluates `...`.

```python
class Authenticator(Protocol):
```

- Defines the class `Authenticator`.
- It extends `Protocol`: it only lists the methods something must have (an interface), with no behavior of its own.

```python
"""Checks a bearer token."""
```

- The docstring (documentation kept with the code) says: *Checks a bearer token.*

```python
def role_of(self, token: str) -> str | None:
```

- Defines the method `role_of`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `token`, type `str`.
- Gives back a value of type `str | None`.

```python
"""'customer', 'reviewer', or None for an unknown token."""
```

- The docstring (documentation kept with the code) says: *'customer', 'reviewer', or None for an unknown token.*

```python
...
```

- `...`: evaluates `...`.

```python
class Catalog(Protocol):
```

- Defines the class `Catalog`.
- It extends `Protocol`: it only lists the methods something must have (an interface), with no behavior of its own.

```python
"""The help pages by id: a reviewer can only cite what exists, and a citation opens the page at its section."""
```

- The docstring (documentation kept with the code) says: *The help pages by id: a reviewer can only cite what exists, and a citation opens the page at its section.*

```python
def section(self, ref: str) -> Section | None:
```

- Defines the method `section`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `ref`, type `str`.
- Gives back a value of type `Section | None`.

```python
"""The section a `page#anchor` ref names, or None."""
```

- The docstring (documentation kept with the code) says: *The section a `page#anchor` ref names, or None.*

```python
...
```

- `...`: evaluates `...`.

```python
class Clock(Protocol):
```

- Defines the class `Clock`.
- It extends `Protocol`: it only lists the methods something must have (an interface), with no behavior of its own.

```python
"""The current time."""
```

- The docstring (documentation kept with the code) says: *The current time.*

```python
def now(self) -> datetime:
```

- Defines the method `now`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `datetime`.

```python
"""Now, timezone-aware."""
```

- The docstring (documentation kept with the code) says: *Now, timezone-aware.*

```python
...
```

- `...`: evaluates `...`.

#### `src/streaming_assistant/application/prompt.py`

```python
"""Prompt assembly: where the stable text goes decides whether a provider's prefix cache can help."""
```

- The docstring (documentation kept with the code) says: *Prompt assembly: where the stable text goes decides whether a provider's prefix cache can help.*

```python
from __future__ import annotations

from collections.abc import Sequence

from streaming_assistant.application.ports import StreamRequest
from streaming_assistant.domain.retrieval import Hit

PROMPT_VERSION = "answer.v1"
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Sequence`: the type hint for an ordered, indexable collection.)
- `from streaming_assistant.application.ports import ...`: takes names from `streaming_assistant.application.ports`, this repository's own code. (`StreamRequest`: One streamed completion.)
- `from streaming_assistant.domain.retrieval import ...`: takes names from `streaming_assistant.domain.retrieval`, this repository's own code. (`Hit`: A section the retriever returned, with its raw score and the share of the question's weight it covers.)
- `PROMPT_VERSION = "answer.v1"`: stores the text `'answer.v1'` in `PROMPT_VERSION`.

```python
def passages(hits: Sequence[Hit]) -> str:
```

- Defines the function `passages`.
- Parameters:
  - `hits`, type `Sequence[Hit]`.
- Gives back a value of type `str`.

```python
"""The retrieved sections as numbered passages that carry their citation refs."""
```

- The docstring (documentation kept with the code) says: *The retrieved sections as numbered passages that carry their citation refs.*

```python
return "\n".join(f"[{hit.section.ref}] {hit.section.heading}: {hit.section.text}" for hit in hits)
```

- `return "\n".join(f"[{hit.section.ref}] {hit.section.heading}: {hit....`: ends the function and gives back the result of calling `"\n".join(f"[{hit.section.ref}] {hit.section.heading}: {hit.section.text}" for hit in h...`, which glues the items of `(f"[{hit.section.ref}] {hit.section.heading}: {hit.section.text}" for hit in hits)` together with `"\n"` between them.

```python
def assemble(
    stable: str,
    hits: Sequence[Hit],
    question: str,
    *,
    stable_first: bool,
    tier: str,
    reviewer_answer: str | None = None,
) -> StreamRequest:
```

- Defines the function `assemble`.
- Parameters:
  - `stable`, type `str`.
  - `hits`, type `Sequence[Hit]`.
  - `question`, type `str`.
  - `stable_first`, type `bool`. Must be passed by name.
  - `tier`, type `str`. Must be passed by name.
  - `reviewer_answer`, type `str | None`, optional (default `None`). Must be passed by name.
- Gives back a value of type `StreamRequest`.

```python
"""Stable instructions first (cacheable, the same for every request), then the passages and the question.

With `stable_first=False` the passages come before the instructions, so the start of the prompt differs on every
request and no prefix cache can apply (the baseline the load test compares against).
"""
```

- The docstring (documentation kept with the code) says: *Stable instructions first (cacheable, the same for every request), then the passages and the question. With `stable_first=False` the passages come before the instructions, so the start of the prompt differs on every request and no prefix cache can apply (the baseline the load test compares against).*

```python
tail = f"Passages:\n{passages(hits)}\nQuestion: {question}"
```

- `tail = f"Passages:\n{passages(hits)}\nQuestion: {question}"`: stores the text built by the f-string `f"Passages:\n{passages(hits)}\nQuestion: {question}"` in `tail`.

```python
if reviewer_answer is not None:
```

- Checks whether `reviewer_answer` is something (not `None`). If so, the indented lines run.

```python
tail += f"\nReviewer-validated answer: {reviewer_answer}"
```

- `tail += f"\nReviewer-validated answer: {reviewer_answer}"`: adds `f"\nReviewer-validated answer: {reviewer_answer}"` to `tail` and keeps the result there.

```python
if stable_first:
```

- Checks whether `stable_first` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
return StreamRequest(stable, tail, PROMPT_VERSION, tier)
```

- `return StreamRequest(stable, tail, PROMPT_VERSION, tier)`: ends the function and gives back the result of calling `StreamRequest(stable, tail, PROMPT_VERSION, tier)`, which is this repository's own `StreamRequest` (in `src/streaming_assistant/application/ports.py`): one streamed completion.

```python
return StreamRequest(f"Passages:\n{passages(hits)}\n\n{stable}", f"Question: {question}", PROMPT_VERSION, tier)
```

- `return StreamRequest(f"Passages:\n{passages(hits)}\n\n{stable}", f"...`: ends the function and gives back the result of calling `StreamRequest(f"Passages:\n{passages(hits)}\n\n{stable}", f"Question: {question}", PROM...`, which is this repository's own `StreamRequest` (in `src/streaming_assistant/application/ports.py`): one streamed completion.

#### `src/streaming_assistant/application/prompts.py`

```python
"""Prompts as files: a two-fence header (version, owner), then the prompt text."""
```

- The docstring (documentation kept with the code) says: *Prompts as files: a two-fence header (version, owner), then the prompt text.*

```python
from __future__ import annotations

from dataclasses import dataclass
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)

```python
class PromptFileError(ValueError):
```

- Defines the class `PromptFileError`.
- It extends `ValueError`: it is a kind of error that can be raised and caught.

```python
"""A prompt file does not have the two-fence header with a version and an owner."""
```

- The docstring (documentation kept with the code) says: *A prompt file does not have the two-fence header with a version and an owner.*

```python
@dataclass(frozen=True, slots=True)
class PromptFile:
```

- Defines the class `PromptFile`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""A versioned prompt."""
```

- The docstring (documentation kept with the code) says: *A versioned prompt.*

```python
name: str
version: str
owner: str
text: str
```

- `name: str`: a field named `name` of type `str`, no default (must be given).
- `version: str`: a field named `version` of type `str`, no default (must be given).
- `owner: str`: a field named `owner` of type `str`, no default (must be given).
- `text: str`: a field named `text` of type `str`, no default (must be given).

```python
def parse_prompt_file(name: str, content: str) -> PromptFile:
```

- Defines the function `parse_prompt_file`.
- Parameters:
  - `name`, type `str`.
  - `content`, type `str`.
- Gives back a value of type `PromptFile`.

```python
"""Split `---`, header lines, `---`, then the prompt text; both fences are required."""
```

- The docstring (documentation kept with the code) says: *Split `---`, header lines, `---`, then the prompt text; both fences are required.*

```python
parts = content.split("---\n", 2)
```

- `parts = content.split("---\n", 2)`: stores the result of calling `content.split("---\n", 2)`, which cuts `content` into pieces at `"---\n"` (whitespace if nothing is given) in `parts`.

```python
if len(parts) != 3 or parts[0].strip():
```

- Checks whether `len(parts)` is different from `3` or `parts[0].strip()` is true (the call removes spaces and line breaks from both ends of `parts[0]` (or the characters its argument)). If so, the indented lines run.

```python
raise PromptFileError(f"{name}: expected a leading '---' fence, a header and a closing '---' fence")
```

- `raise PromptFileError(f"{name}: expected a leading '---' fence, a h...`: stops with an error of kind `PromptFileError` with the message `f"{name}: expected a leading '---' fence, a header and a closing '---' fence"`. Whoever called this code must handle it or the program stops.

```python
fields = dict(line.split(": ", 1) for line in parts[1].strip().splitlines() if ": " in line)
```

- `fields = dict(line.split(": ", 1) for line in parts[1].strip().spli...`: stores the result of calling `dict(line.split(": ", 1) for line in parts[1].strip().splitlines() if ": " in line)`, which builds a dict in `fields`.

```python
for required in ("version", "owner"):
```

- Repeats the indented lines once for each item of `("version", "owner")`, naming the current item `required`.

```python
if required not in fields:
```

- Checks whether `required` is not among `fields`. If so, the indented lines run.

```python
raise PromptFileError(f"{name}: header lacks {required}")
```

- `raise PromptFileError(f"{name}: header lacks {required}")`: stops with an error of kind `PromptFileError` with the message `f"{name}: header lacks {required}"`. Whoever called this code must handle it or the program stops.

```python
return PromptFile(name, fields["version"], fields["owner"], parts[2].strip())
```

- `return PromptFile(name, fields["version"], fields["owner"], parts[2...`: ends the function and gives back the result of calling `PromptFile(name, fields["version"], fields["owner"], parts[2].strip())`, which is this repository's own `PromptFile` (in `src/streaming_assistant/application/prompts.py`): a versioned prompt.

#### `src/streaming_assistant/application/review.py`

```python
"""The review desk: a human support agent answers a paused run, and the answer is validated before it can be used."""
```

- The docstring (documentation kept with the code) says: *The review desk: a human support agent answers a paused run, and the answer is validated before it can be used.*

```python
from __future__ import annotations

from collections.abc import Sequence

from streaming_assistant.application.ports import AuditLog, Catalog, Clock, PausedRun, RunStore
from streaming_assistant.domain.errors import ReviewRejectedError, UnknownRunError
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Sequence`: the type hint for an ordered, indexable collection.)
- `from streaming_assistant.application.ports import ...`: takes names from `streaming_assistant.application.ports`, this repository's own code. (`AuditLog`: An append-only, hash-chained log.) (`Catalog`: The help pages by id: a reviewer can only cite what exists, and a citation opens the page at its section.) (`Clock`: The current time.) (`PausedRun`: A run waiting for, or past, a reviewer.) (`RunStore`: Durable state of paused runs: it must survive a restart.)
- `from streaming_assistant.domain.errors import ...`: takes names from `streaming_assistant.domain.errors`, this repository's own code. (`ReviewRejectedError`: A reviewer's answer is not allowed (empty, ungrounded, or the run is not waiting).) (`UnknownRunError`: No run with this id.)

```python
class ReviewDesk:
```

- Defines the class `ReviewDesk`.

```python
"""Lists waiting runs and validates a reviewer's answer: not empty, and either citing a real section or saying that
no page covers the question. An unvalidated answer must never reach the model's context."""
```

- The docstring (documentation kept with the code) says: *Lists waiting runs and validates a reviewer's answer: not empty, and either citing a real section or saying that no page covers the question. An unvalidated answer must never reach the model's context.*

```python
def __init__(self, runs: RunStore, audit: AuditLog, catalog: Catalog, clock: Clock) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `runs`, type `RunStore`.
  - `audit`, type `AuditLog`.
  - `catalog`, type `Catalog`.
  - `clock`, type `Clock`.
- Gives back a value of type `None`.

```python
self._runs = runs
self._audit = audit
self._catalog = catalog
self._clock = clock
```

- `self._runs = runs`: stores the value of `runs` in `self._runs`.
- `self._audit = audit`: stores the value of `audit` in `self._audit`.
- `self._catalog = catalog`: stores the value of `catalog` in `self._catalog`.
- `self._clock = clock`: stores the value of `clock` in `self._clock`.

```python
def waiting(self, limit: int = 50) -> Sequence[PausedRun]:
```

- Defines the method `waiting`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `limit`, type `int`, optional (default `50`).
- Gives back a value of type `Sequence[PausedRun]`.

```python
"""Runs waiting for a reviewer, oldest first."""
```

- The docstring (documentation kept with the code) says: *Runs waiting for a reviewer, oldest first.*

```python
return self._runs.waiting(limit)
```

- `return self._runs.waiting(limit)`: ends the function and gives back the result of calling `self._runs.waiting(limit)`, which is this repository's own `waiting` (in `src/streaming_assistant/application/ports.py`): runs waiting for a reviewer, oldest first.

```python
def status(self, run_id: str) -> str:
```

- Defines the method `status`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run_id`, type `str`.
- Gives back a value of type `str`.

```python
"""The run's status: waiting, answered or resumed."""
```

- The docstring (documentation kept with the code) says: *The run's status: waiting, answered or resumed.*

```python
run = self._runs.get(run_id)
```

- `run = self._runs.get(run_id)`: stores the result of calling `self._runs.get(run_id)`, which is this repository's own `get` (in `src/streaming_assistant/application/ports.py`): one run, or None in `run`.

```python
if run is None:
```

- Checks whether `run` is nothing (`None`). If so, the indented lines run.

```python
raise UnknownRunError(run_id)
```

- `raise UnknownRunError(run_id)`: stops with an error of kind `UnknownRunError` with the message `run_id`. Whoever called this code must handle it or the program stops.

```python
return run.status
```

- `return run.status`: ends the function and gives back `run.status`.

```python
def answer(self, run_id: str, reviewer_id: str, answer: str, cited: Sequence[str], no_page: bool) -> PausedRun:
```

- Defines the method `answer`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run_id`, type `str`.
  - `reviewer_id`, type `str`.
  - `answer`, type `str`.
  - `cited`, type `Sequence[str]`.
  - `no_page`, type `bool`.
- Gives back a value of type `PausedRun`.

```python
"""Validate and store the reviewer's answer; raises `ReviewRejectedError` with the reason when it is not allowed."""
```

- The docstring (documentation kept with the code) says: *Validate and store the reviewer's answer; raises `ReviewRejectedError` with the reason when it is not allowed.*

```python
run = self._runs.get(run_id)
```

- `run = self._runs.get(run_id)`: stores the result of calling `self._runs.get(run_id)`, which is this repository's own `get` (in `src/streaming_assistant/application/ports.py`): one run, or None in `run`.

```python
if run is None:
```

- Checks whether `run` is nothing (`None`). If so, the indented lines run.

```python
raise UnknownRunError(run_id)
```

- `raise UnknownRunError(run_id)`: stops with an error of kind `UnknownRunError` with the message `run_id`. Whoever called this code must handle it or the program stops.

```python
if run.status != "waiting":
```

- Checks whether `run.status` is different from `"waiting"`. If so, the indented lines run.

```python
raise ReviewRejectedError(f"run {run_id} is {run.status}, not waiting for a reviewer")
```

- `raise ReviewRejectedError(f"run {run_id} is {run.status}, not waiti...`: stops with an error of kind `ReviewRejectedError` with the message `f"run {run_id} is {run.status}, not waiting for a reviewer"`. Whoever called this code must handle it or the program stops.

```python
if not reviewer_id.strip():
```

- Checks whether it is not the case that `reviewer_id.strip()` is true (the call removes spaces and line breaks from both ends of `reviewer_id` (or the characters its argument)). If so, the indented lines run.

```python
raise ReviewRejectedError("a reviewer id is required")
```

- `raise ReviewRejectedError("a reviewer id is required")`: stops with an error of kind `ReviewRejectedError` with the message `"a reviewer id is required"`. Whoever called this code must handle it or the program stops.

```python
if not answer.strip():
```

- Checks whether it is not the case that `answer.strip()` is true (the call removes spaces and line breaks from both ends of `answer` (or the characters its argument)). If so, the indented lines run.

```python
raise ReviewRejectedError("the answer must not be empty")
```

- `raise ReviewRejectedError("the answer must not be empty")`: stops with an error of kind `ReviewRejectedError` with the message `"the answer must not be empty"`. Whoever called this code must handle it or the program stops.

```python
unknown = [ref for ref in cited if self._catalog.section(ref) is None]
```

- `unknown = [ref for ref in cited if self._catalog.section(ref) is None]`: stores a list built by running `ref` for each `ref` in `cited` keeping only those where `self._catalog.section(ref)` is nothing (`None`) in `unknown`.

```python
if unknown:
```

- Checks whether `unknown` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
raise ReviewRejectedError(f"unknown section(s): {', '.join(unknown)}")
```

- `raise ReviewRejectedError(f"unknown section(s): {', '.join(unknown)}")`: stops with an error of kind `ReviewRejectedError` with the message `f"unknown section(s): {', '.join(unknown)}"`. Whoever called this code must handle it or the program stops.

```python
if not cited and not no_page:
```

- Checks whether it is not the case that `cited` is truthy (not `None`, `False`, zero or empty) and it is not the case that `no_page` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
raise ReviewRejectedError("cite a help section, or say that no page covers this question")
```

- `raise ReviewRejectedError("cite a help section, or say that no page...`: stops with an error of kind `ReviewRejectedError` with the message `"cite a help section, or say that no page covers this question"`. Whoever called this code must handle it or the program stops.

```python
self._audit.append(run_id, "answered", reviewer_id.strip(), answer.strip())
self._runs.record_answer(run_id, reviewer_id.strip(), answer.strip(), tuple(cited), no_page, self._clock.now())
self._audit.append(run_id, "validated", "system", f"cited={','.join(cited) or 'none'} no_page={no_page}")
stored = self._runs.get(run_id)
assert stored is not None
return stored
```

- `self._audit.append(run_id, "answered", reviewer_id.strip(), answer....`: calling `self._audit.append(run_id, "answered", reviewer_id.strip(), answer.strip())`, which adds `run_id` to the end of `self._audit`.
- `self._runs.record_answer(run_id, reviewer_id.strip(), answer.strip(...`: calling `self._runs.record_answer(run_id, reviewer_id.strip(), answer.strip(), tuple(cited), no_...`.
- `self._audit.append(run_id, "validated", "system", f"cited={','.join...`: calling `self._audit.append(run_id, "validated", "system", f"cited={','.join(cited) or 'none'} n...`, which adds `run_id` to the end of `self._audit`.
- `stored = self._runs.get(run_id)`: stores the result of calling `self._runs.get(run_id)`, which is this repository's own `get` (in `src/streaming_assistant/application/ports.py`): one run, or None in `stored`.
- `assert stored is not None`: checks that `stored` is something (not `None`). A false check stops the test as failed.
- `return stored`: ends the function and gives back the value of `stored`.

#### `src/streaming_assistant/domain/__init__.py`

```python
"""The domain layer."""
```

- The docstring (documentation kept with the code) says: *The domain layer.*

#### `src/streaming_assistant/domain/audit.py`

```python
"""The audit log as a hash chain: each entry carries the hash of the one before, so an edit, removal or reorder is found."""
```

- The docstring (documentation kept with the code) says: *The audit log as a hash chain: each entry carries the hash of the one before, so an edit, removal or reorder is found.*

```python
from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

GENESIS = "start"
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import hashlib`: makes the module `hashlib` available (hash functions such as SHA-256).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Sequence`: the type hint for an ordered, indexable collection.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)
- `from datetime import ...`: takes names from `datetime` (dates, times and time spans). (`datetime`: the date-and-time type.)
- `GENESIS = "start"`: stores the text `'start'` in `GENESIS`.

```python
SEPARATOR = "\x1f"
```

- `SEPARATOR = "\x1f"`: stores the text `'\x1f'` in `SEPARATOR`.

```python
@dataclass(frozen=True, slots=True)
class AuditEntry:
```

- Defines the class `AuditEntry`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""One step of a run, with its place in the chain."""
```

- The docstring (documentation kept with the code) says: *One step of a run, with its place in the chain.*

```python
previous: str
run: str
step: str
actor: str
at: str
content: str
hash: str
```

- `previous: str`: a field named `previous` of type `str`, no default (must be given).
- `run: str`: a field named `run` of type `str`, no default (must be given).
- `step: str`: a field named `step` of type `str`, no default (must be given).
- `actor: str`: a field named `actor` of type `str`, no default (must be given).
- `at: str`: a field named `at` of type `str`, no default (must be given).
- `content: str`: a field named `content` of type `str`, no default (must be given).
- `hash: str`: a field named `hash` of type `str`, no default (must be given).

```python
def digest(previous: str, run: str, step: str, actor: str, at: str, content: str) -> str:
```

- Defines the function `digest`.
- Parameters:
  - `previous`, type `str`.
  - `run`, type `str`.
  - `step`, type `str`.
  - `actor`, type `str`.
  - `at`, type `str`.
  - `content`, type `str`.
- Gives back a value of type `str`.

```python
"""SHA-256 over the six fields, in a fixed order, joined by a separator that text does not contain."""
```

- The docstring (documentation kept with the code) says: *SHA-256 over the six fields, in a fixed order, joined by a separator that text does not contain.*

```python
return hashlib.sha256(SEPARATOR.join((previous, run, step, actor, at, content)).encode()).hexdigest()
```

- `return hashlib.sha256(SEPARATOR.join((previous, run, step, actor, a...`: ends the function and gives back the result of calling `hashlib.sha256(SEPARATOR.join((previous, run, step, actor, at, content)).encode()).hexd...`, which writes the hash as hexadecimal text.

```python
def make_entry(previous_hash: str | None, run: str, step: str, actor: str, at: datetime, content: str) -> AuditEntry:
```

- Defines the function `make_entry`.
- Parameters:
  - `previous_hash`, type `str | None`.
  - `run`, type `str`.
  - `step`, type `str`.
  - `actor`, type `str`.
  - `at`, type `datetime`.
  - `content`, type `str`.
- Gives back a value of type `AuditEntry`.

```python
"""The next entry in the chain."""
```

- The docstring (documentation kept with the code) says: *The next entry in the chain.*

```python
previous = previous_hash or GENESIS
stamp = at.isoformat()
return AuditEntry(previous, run, step, actor, stamp, content, digest(previous, run, step, actor, stamp, content))
```

- `previous = previous_hash or GENESIS`: stores `previous_hash or GENESIS` (the first operand that decides the or) in `previous`.
- `stamp = at.isoformat()`: stores the result of calling `at.isoformat()`, which writes the date or time as ISO text in `stamp`.
- `return AuditEntry(previous, run, step, actor, stamp, content, diges...`: ends the function and gives back the result of calling `AuditEntry(previous, run, step, actor, stamp, content, digest(previous, run, step, acto...`, which is this repository's own `AuditEntry` (in `src/streaming_assistant/domain/audit.py`): one step of a run, with its place in the chain.

```python
def verify(entries: Sequence[AuditEntry]) -> int | None:
```

- Defines the function `verify`.
- Parameters:
  - `entries`, type `Sequence[AuditEntry]`.
- Gives back a value of type `int | None`.

```python
"""Index of the first entry that was edited, removed or reordered; None when the chain holds."""
```

- The docstring (documentation kept with the code) says: *Index of the first entry that was edited, removed or reordered; None when the chain holds.*

```python
previous = GENESIS
```

- `previous = GENESIS`: stores the value of `GENESIS` in `previous`.

```python
for index, entry in enumerate(entries):
```

- Repeats the indented lines once for each item of `enumerate(entries)`, naming the current item the names `index`, `entry`.

```python
expected = digest(entry.previous, entry.run, entry.step, entry.actor, entry.at, entry.content)
```

- `expected = digest(entry.previous, entry.run, entry.step, entry.acto...`: stores the result of calling `digest(entry.previous, entry.run, entry.step, entry.actor, entry.at, entry.content)`, which returns the hash as bytes in `expected`.

```python
if entry.previous != previous or entry.hash != expected:
```

- Checks whether `entry.previous` is different from `previous` or `entry.hash` is different from `expected`. If so, the indented lines run.

```python
return index
```

- `return index`: ends the function and gives back the value of `index`.

```python
previous = entry.hash
```

- `previous = entry.hash`: stores `entry.hash` in `previous`.

```python
return None
```

- `return None`: ends the function and gives back nothing (`None`).

#### `src/streaming_assistant/domain/citations.py`

```python
"""Citations: a citation is a section that was retrieved for this request. Anything else is dropped and counted."""
```

- The docstring (documentation kept with the code) says: *Citations: a citation is a section that was retrieved for this request. Anything else is dropped and counted.*

```python
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from streaming_assistant.domain.retrieval import Section

_CITATION = re.compile(r"\[(help-\d+#[a-z0-9-]+)\]")
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import re`: makes the module `re` available (regular expressions: patterns that match text).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Mapping`: the type hint for a read-only dict-like collection.) (`Sequence`: the type hint for an ordered, indexable collection.)
- `from streaming_assistant.domain.retrieval import ...`: takes names from `streaming_assistant.domain.retrieval`, this repository's own code. (`Section`: One section of a help page; `anchor` is where a citation opens the page.)
- `_CITATION = re.compile(r"\[(help-\d+#[a-z0-9-]+)\]")`: stores the result of calling `re.compile(r"\[(help-\d+#[a-z0-9-]+)\]")`, which compiles the pattern `r"\[(help-\d+#[a-z0-9-]+)\]"` so it can be matched many times in `_CITATION`.

```python
class MarkerStripper:
```

- Defines the class `MarkerStripper`.

```python
"""Removes `[page#section]` markers from a stream of text pieces, even when a marker is split across pieces, and
remembers the refs it saw. A bracket that never closes within 40 characters is released as ordinary text."""
```

- The docstring (documentation kept with the code) says: *Removes `[page#section]` markers from a stream of text pieces, even when a marker is split across pieces, and remembers the refs it saw. A bracket that never closes within 40 characters is released as ordinary text.*

```python
def __init__(self) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `None`.

```python
self._held = ""
self.refs: list[str] = []
```

- `self._held = ""`: stores the empty text in `self._held`.
- `self.refs: list[str] = []`: stores a new list (empty) in `self.refs`, whose type is declared as `list[str]`.

```python
def feed(self, piece: str) -> str:
```

- Defines the method `feed`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `piece`, type `str`.
- Gives back a value of type `str`.

```python
"""Text that is safe to show now."""
```

- The docstring (documentation kept with the code) says: *Text that is safe to show now.*

```python
text = self._held + piece
self._held = ""
out: list[str] = []
```

- `text = self._held + piece`: stores `self._held + piece`, which adds `self._held` and `piece` in `text`.
- `self._held = ""`: stores the empty text in `self._held`.
- `out: list[str] = []`: stores a new list (empty) in `out`, whose type is declared as `list[str]`.

```python
while text:
```

- Repeats the indented lines for as long as `text` is truthy (not `None`, `False`, zero or empty).

```python
start = text.find("[")
```

- `start = text.find("[")`: stores the result of calling `text.find("[")`, which finds where `"["` first appears in `text` (-1 if it does not) in `start`.

```python
if start < 0:
```

- Checks whether `start` is less than `0`. If so, the indented lines run.

```python
out.append(text)
break
```

- `out.append(text)`: calling `out.append(text)`, which adds `text` to the end of `out`.
- `break`: leaves the loop now.

```python
out.append(text[:start])
end = text.find("]", start)
```

- `out.append(text[:start])`: calling `out.append(text[:start])`, which adds `text[:start]` to the end of `out`.
- `end = text.find("]", start)`: stores the result of calling `text.find("]", start)`, which finds where `"]"` first appears in `text` (-1 if it does not) in `end`.

```python
if end < 0:
```

- Checks whether `end` is less than `0`. If so, the indented lines run.

```python
if len(text) - start > 40:
```

- Checks whether `len(text) - start` is greater than `40`. If so, the indented lines run.

```python
out.append(text[start])
text = text[start + 1 :]
continue
```

- `out.append(text[start])`: calling `out.append(text[start])`, which adds `text[start]` to the end of `out`.
- `text = text[start + 1 :]`: stores the item `text[start + 1 :]` in `text`.
- `continue`: skips to the next round of the loop.

```python
self._held = text[start:]
break
```

- `self._held = text[start:]`: stores the item `text[start:]` in `self._held`.
- `break`: leaves the loop now.

```python
marker = text[start : end + 1]
ref = marker[1:-1]
```

- `marker = text[start : end + 1]`: stores the item `text[start : end + 1]` in `marker`.
- `ref = marker[1:-1]`: stores the item `marker[1:-1]` in `ref`.

```python
if _CITATION.fullmatch(marker):
```

- Checks whether `_CITATION.fullmatch(marker)` is true (the call tries to match the pattern against the whole text). If so, the indented lines run.

```python
if ref not in self.refs:
```

- Checks whether `ref` is not among `self.refs`. If so, the indented lines run.

```python
self.refs.append(ref)
```

- `self.refs.append(ref)`: calling `self.refs.append(ref)`, which adds `ref` to the end of `self.refs`.

```python
else:
```

- Runs when none of the conditions above held.

```python
out.append(marker)
```

- `out.append(marker)`: calling `out.append(marker)`, which adds `marker` to the end of `out`.

```python
text = text[end + 1 :]
```

- `text = text[end + 1 :]`: stores the item `text[end + 1 :]` in `text`.

```python
return "".join(out)
```

- `return "".join(out)`: ends the function and gives back the result of calling `"".join(out)`, which glues the items of `out` together with `""` between them.

```python
def finish(self) -> str:
```

- Defines the method `finish`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `str`.

```python
"""Whatever was held back at the end of the stream."""
```

- The docstring (documentation kept with the code) says: *Whatever was held back at the end of the stream.*

```python
held, self._held = self._held, ""
return held
```

- `held, self._held = self._held, ""`: unpacks a tuple of 2 items into the names `held`, `self._held`, one item each.
- `return held`: ends the function and gives back the value of `held`.

```python
def check_refs(refs: Sequence[str], allowed: Mapping[str, Section]) -> tuple[tuple[Section, ...], int]:
```

- Defines the function `check_refs`.
- Parameters:
  - `refs`, type `Sequence[str]`.
  - `allowed`, type `Mapping[str, Section]`.
- Gives back a value of type `tuple[tuple[Section, ...], int]`.

```python
"""(sections that may be shown, number dropped). A ref counts only when it is one of the sections allowed for this
request: the ones retrieved for it, plus the ones a reviewer cited."""
```

- The docstring (documentation kept with the code) says: *(sections that may be shown, number dropped). A ref counts only when it is one of the sections allowed for this request: the ones retrieved for it, plus the ones a reviewer cited.*

```python
shown = tuple(allowed[ref] for ref in refs if ref in allowed)
return shown, len(refs) - len(shown)
```

- `shown = tuple(allowed[ref] for ref in refs if ref in allowed)`: stores the result of calling `tuple(allowed[ref] for ref in refs if ref in allowed)`, which builds a tuple (a fixed-length list) from `(allowed[ref] for ref in refs if ref in allowed)` in `shown`.
- `return shown, len(refs) - len(shown)`: ends the function and gives back a tuple of 2 items.

#### `src/streaming_assistant/domain/errors.py`

```python
"""Named errors of the streaming assistant."""
```

- The docstring (documentation kept with the code) says: *Named errors of the streaming assistant.*

```python
from __future__ import annotations
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)

```python
class ProviderError(RuntimeError):
```

- Defines the class `ProviderError`.
- It extends `RuntimeError`: it is a kind of error that can be raised and caught.

```python
"""The model provider failed (a server error or a dropped connection)."""
```

- The docstring (documentation kept with the code) says: *The model provider failed (a server error or a dropped connection).*

```python
class RateLimitedError(RuntimeError):
```

- Defines the class `RateLimitedError`.
- It extends `RuntimeError`: it is a kind of error that can be raised and caught.

```python
"""The model provider answered 429."""
```

- The docstring (documentation kept with the code) says: *The model provider answered 429.*

```python
class RefusedError(RuntimeError):
```

- Defines the class `RefusedError`.
- It extends `RuntimeError`: it is a kind of error that can be raised and caught.

```python
"""The model declined to answer."""
```

- The docstring (documentation kept with the code) says: *The model declined to answer.*

```python
class ReviewRejectedError(ValueError):
```

- Defines the class `ReviewRejectedError`.
- It extends `ValueError`: it is a kind of error that can be raised and caught.

```python
"""A reviewer's answer is not allowed (empty, ungrounded, or the run is not waiting)."""
```

- The docstring (documentation kept with the code) says: *A reviewer's answer is not allowed (empty, ungrounded, or the run is not waiting).*

```python
class UnknownRunError(LookupError):
```

- Defines the class `UnknownRunError`.
- It extends `LookupError` (it starts with all of that class's methods and may add or replace some).

```python
"""No run with this id."""
```

- The docstring (documentation kept with the code) says: *No run with this id.*

#### `src/streaming_assistant/domain/retrieval.py`

```python
"""Help-page sections and a small BM25-style scorer whose score is the share of the question the section covers."""
```

- The docstring (documentation kept with the code) says: *Help-page sections and a small BM25-style scorer whose score is the share of the question the section covers.*

```python
from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import math`: makes the module `math` available (mathematical functions).
- `import re`: makes the module `re` available (regular expressions: patterns that match text).
- `from collections import ...`: takes names from `collections` (the standard library's extra container types (Counter, defaultdict, deque)). (`Counter`: a dict that counts: `counter[x] += 1`.)
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Mapping`: the type hint for a read-only dict-like collection.) (`Sequence`: the type hint for an ordered, indexable collection.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)

```python
_WORD = re.compile(r"[a-z0-9]+")
```

- `_WORD = re.compile(r"[a-z0-9]+")`: stores the result of calling `re.compile(r"[a-z0-9]+")`, which compiles the pattern `r"[a-z0-9]+"` so it can be matched many times in `_WORD`.

```python
STOP = frozenset(
    [
        "a",
        "an",
        "the",
        "i",
        "my",
        "me",
        "we",
        "you",
        "your",
        "is",
        "are",
        "was",
        "were",
        "be",
        "do",
        "does",
        "did",
        "can",
        "could",
        "would",
        "should",
        "how",
        "what",
        "when",
        "where",
        "why",
        "who",
        "which",
        "to",
        "of",
        "for",
        "in",
        "on",
        "at",
        "it",
        "this",
        "that",
        "and",
        "or",
        "if",
        "not",
        "no",
        "there",
        "any",
        "have",
        "has",
        "had",
        "with",
        "from",
        "by",
        "about",
        "as",
        "so",
        "than",
        "then",
        "please",
    ]
)
```

- `STOP = frozenset( [ "a", "an", "the", "i", "my", "me", "we", "you",...`: stores the result of calling `frozenset( [ "a", "an", "the", "i", "my", "me", "we", "you", "your", "is", "are", "was"...`, which builds a set that cannot change from `[ "a", "an", "the", "i", "my", "me", "we", "you", "your", "is", "are", "was", "were", "...` in `STOP`.

```python
K1 = 1.4
B = 0.7
```

- `K1 = 1.4`: stores the number `1.4` in `K1`.
- `B = 0.7`: stores the number `0.7` in `B`.

```python
@dataclass(frozen=True, slots=True)
class Section:
```

- Defines the class `Section`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""One section of a help page; `anchor` is where a citation opens the page."""
```

- The docstring (documentation kept with the code) says: *One section of a help page; `anchor` is where a citation opens the page.*

```python
page_id: str
page_title: str
anchor: str
heading: str
text: str
```

- `page_id: str`: a field named `page_id` of type `str`, no default (must be given).
- `page_title: str`: a field named `page_title` of type `str`, no default (must be given).
- `anchor: str`: a field named `anchor` of type `str`, no default (must be given).
- `heading: str`: a field named `heading` of type `str`, no default (must be given).
- `text: str`: a field named `text` of type `str`, no default (must be given).

```python
@property
def ref(self) -> str:
```

- Defines the method `ref`.
- `@property`: the method is read like an attribute.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `str`.

```python
"""The citation form: `page-07#refund-timing`."""
```

- The docstring (documentation kept with the code) says: *The citation form: `page-07#refund-timing`.*

```python
return f"{self.page_id}#{self.anchor}"
```

- `return f"{self.page_id}#{self.anchor}"`: ends the function and gives back the text built by the f-string `f"{self.page_id}#{self.anchor}"`.

```python
@dataclass(frozen=True, slots=True)
class Hit:
```

- Defines the class `Hit`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""A section the retriever returned, with its raw score and the share of the question's weight it covers."""
```

- The docstring (documentation kept with the code) says: *A section the retriever returned, with its raw score and the share of the question's weight it covers.*

```python
section: Section
score: float
coverage: float
```

- `section: Section`: a field named `section` of type `Section`, no default (must be given).
- `score: float`: a field named `score` of type `float`, no default (must be given).
- `coverage: float`: a field named `coverage` of type `float`, no default (must be given).

```python
def terms(text: str) -> list[str]:
```

- Defines the function `terms`.
- Parameters:
  - `text`, type `str`.
- Gives back a value of type `list[str]`.

```python
"""Lower-case content words (no stop words), with a crude plural fold."""
```

- The docstring (documentation kept with the code) says: *Lower-case content words (no stop words), with a crude plural fold.*

```python
return [
    word[:-1] if len(word) > 4 and word.endswith("s") else word
    for word in _WORD.findall(text.lower())
    if word not in STOP
]
```

- `return [ word[:-1] if len(word) > 4 and word.endswith("s") else wor...`: ends the function and gives back a list built by running `word[:-1] if len(word) > 4 and word.endswith("s") else word` for each `word` in `_WORD.findall(text.lower())` keeping only those where `word` is not among `STOP`.

```python
class Bm25Index:
```

- Defines the class `Bm25Index`.

```python
"""Built once from the sections. `search` returns the best sections; `coverage` is the idf weight of the query terms the
section contains over the idf weight of all the query's terms. A term found nowhere in the help center weighs as much
as the rarest known term, so a question about the weather does not look covered because one word matched."""
```

- The docstring (documentation kept with the code) says: *Built once from the sections. `search` returns the best sections; `coverage` is the idf weight of the query terms the section contains over the idf weight of all the query's terms. A term found nowhere in the help center weighs as much as the rarest known term, so a question about the weather does not look covered because one word matched.*

```python
def __init__(self, sections: Sequence[Section]) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `sections`, type `Sequence[Section]`.
- Gives back a value of type `None`.

```python
self._sections = list(sections)
self._tf = [Counter(terms(f"{s.heading} {s.heading} {s.page_title} {s.text}")) for s in self._sections]
self._lengths = [sum(tf.values()) for tf in self._tf]
self._average = sum(self._lengths) / len(self._lengths) if self._lengths else 1.0
document_frequency: Counter[str] = Counter()
```

- `self._sections = list(sections)`: stores the result of calling `list(sections)`, which builds a new list from `sections` in `self._sections`.
- `self._tf = [Counter(terms(f"{s.heading} {s.heading} {s.page_title} ...`: stores a list built by running `Counter(terms(f"{s.heading} {s.heading} {s.page_title} {s.text}"))` for each `s` in `self._sections` in `self._tf`.
- `self._lengths = [sum(tf.values()) for tf in self._tf]`: stores a list built by running `sum(tf.values())` for each `tf` in `self._tf` in `self._lengths`.
- `self._average = sum(self._lengths) / len(self._lengths) if self._le...`: stores `sum(self._lengths) / len(self._lengths)` when `self._lengths` is truthy, otherwise `1.0` in `self._average`.
- `document_frequency: Counter[str] = Counter()`: stores the result of calling `Counter()`, which makes a `Counter` object in `document_frequency`, whose type is declared as `Counter[str]`.

```python
for tf in self._tf:
```

- Repeats the indented lines once for each item of `self._tf`, naming the current item `tf`.

```python
document_frequency.update(tf.keys())
```

- `document_frequency.update(tf.keys())`: calling `document_frequency.update(tf.keys())`, which copies the entries of `tf.keys()` into `document_frequency`.

```python
count = len(self._sections)
self._idf: Mapping[str, float] = {
    term: math.log(1 + (count - freq + 0.5) / (freq + 0.5)) for term, freq in document_frequency.items()
}
self._unknown_idf = max(self._idf.values(), default=1.0)
```

- `count = len(self._sections)`: stores the result of calling `len(self._sections)`, which counts the items in `self._sections` in `count`.
- `self._idf: Mapping[str, float] = { term: math.log(1 + (count - freq...`: stores a dict built by running `term` for each `term, freq` in `document_frequency.items()` in `self._idf`, whose type is declared as `Mapping[str, float]`.
- `self._unknown_idf = max(self._idf.values(), default=1.0)`: stores the result of calling `max(self._idf.values(), default=1.0)`, which picks the largest of `self._idf.values()` The named values are `default`. in `self._unknown_idf`.

```python
def search(self, query: str, limit: int = 3) -> list[Hit]:
```

- Defines the method `search`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `query`, type `str`.
  - `limit`, type `int`, optional (default `3`).
- Gives back a value of type `list[Hit]`.

```python
"""Best sections for the query, best first; sections sharing no term are left out."""
```

- The docstring (documentation kept with the code) says: *Best sections for the query, best first; sections sharing no term are left out.*

```python
wanted = terms(query)
total = sum(self._idf.get(term, self._unknown_idf) for term in set(wanted)) or 1.0
hits = []
```

- `wanted = terms(query)`: stores the result of calling `terms(query)`, which is this repository's own `terms` (in `src/streaming_assistant/domain/retrieval.py`): lower-case content words (no stop words), with a crude plural fold in `wanted`.
- `total = sum(self._idf.get(term, self._unknown_idf) for term in set(...`: stores `sum(self._idf.get(term, self._unknown_idf) for term in set(wanted)) or 1.0` (the first operand that decides the or) in `total`.
- `hits = []`: stores a new list (empty) in `hits`.

```python
for index, section in enumerate(self._sections):
```

- Repeats the indented lines once for each item of `enumerate(self._sections)`, naming the current item the names `index`, `section`.

```python
tf, length = self._tf[index], self._lengths[index]
score = coverage = 0.0
```

- `tf, length = self._tf[index], self._lengths[index]`: unpacks a tuple of 2 items into the names `tf`, `length`, one item each.
- `score = coverage = 0.0`: stores the number `0.0` in `score`, `coverage`.

```python
for term in set(wanted):
```

- Repeats the indented lines once for each item of `set(wanted)`, naming the current item `term`.

```python
if term in tf:
```

- Checks whether `term` is among `tf`. If so, the indented lines run.

```python
idf = self._idf[term]
score += idf * tf[term] * (K1 + 1) / (tf[term] + K1 * (1 - B + B * length / self._average))
coverage += idf
```

- `idf = self._idf[term]`: stores the item `self._idf[term]` in `idf`.
- `score += idf * tf[term] * (K1 + 1) / (tf[term] + K1 * (1 - B + B * ...`: adds `idf * tf[term] * (K1 + 1) / (tf[term] + K1 * (1 - B + B * length / self._average))` to `score` and keeps the result there.
- `coverage += idf`: adds `idf` to `coverage` and keeps the result there.

```python
if score > 0:
```

- Checks whether `score` is greater than `0`. If so, the indented lines run.

```python
hits.append(Hit(section, score, coverage / total))
```

- `hits.append(Hit(section, score, coverage / total))`: calling `hits.append(Hit(section, score, coverage / total))`, which adds `Hit(section, score, coverage / total)` to the end of `hits`.

```python
hits.sort(key=lambda hit: (-hit.score, hit.section.ref))
return hits[:limit]
```

- `hits.sort(key=lambda hit: (-hit.score, hit.section.ref))`: calling `hits.sort(key=lambda hit: (-hit.score, hit.section.ref))`, which sorts `hits` in place The named values are `key`..
- `return hits[:limit]`: ends the function and gives back the item `hits[:limit]`.

#### `src/streaming_assistant/domain/routing.py`

```python
"""What to do with a question: answer, say it is thin, say nothing was found, or pause for a person. Thresholds are explicit."""
```

- The docstring (documentation kept with the code) says: *What to do with a question: answer, say it is thin, say nothing was found, or pause for a person. Thresholds are explicit.*

```python
from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from streaming_assistant.domain.retrieval import Hit

ANSWER = "answer"
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import re`: makes the module `re` available (regular expressions: patterns that match text).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Sequence`: the type hint for an ordered, indexable collection.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)
- `from streaming_assistant.domain.retrieval import ...`: takes names from `streaming_assistant.domain.retrieval`, this repository's own code. (`Hit`: A section the retriever returned, with its raw score and the share of the question's weight it covers.)
- `ANSWER = "answer"`: stores the text `'answer'` in `ANSWER`.

```python
LOW_CONFIDENCE = "low_confidence"
NO_EVIDENCE = "no_evidence"
PAUSE = "pause"
RETURN_WINDOW_DAYS = 30
LEGAL = re.compile(r"\b(?:lawyer|legal action|sue|chargeback)\b", re.I)
REFUND = re.compile(r"\b(?:refund|money back|reimburse)", re.I)
```

- `LOW_CONFIDENCE = "low_confidence"`: stores the text `'low_confidence'` in `LOW_CONFIDENCE`.
- `NO_EVIDENCE = "no_evidence"`: stores the text `'no_evidence'` in `NO_EVIDENCE`.
- `PAUSE = "pause"`: stores the text `'pause'` in `PAUSE`.
- `RETURN_WINDOW_DAYS = 30`: stores the number `30` in `RETURN_WINDOW_DAYS`.
- `LEGAL = re.compile(r"\b(?:lawyer|legal action|sue|chargeback)\b", r...`: stores the result of calling `re.compile(r"\b(?:lawyer|legal action|sue|chargeback)\b", re.I)`, which compiles the pattern `r"\b(?:lawyer|legal action|sue|chargeback)\b"` so it can be matched many times in `LEGAL`.
- `REFUND = re.compile(r"\b(?:refund|money back|reimburse)", re.I)`: stores the result of calling `re.compile(r"\b(?:refund|money back|reimburse)", re.I)`, which compiles the pattern `r"\b(?:refund|money back|reimburse)"` so it can be matched many times in `REFUND`.

```python
_UNITS = {
    word: number
    for number, word in enumerate(
        [
            "zero",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "eleven",
            "twelve",
            "thirteen",
            "fourteen",
            "fifteen",
            "sixteen",
            "seventeen",
            "eighteen",
            "nineteen",
        ]
    )
}
```

- `_UNITS = { word: number for number, word in enumerate( [ "zero", "o...`: stores a dict built by running `word` for each `number, word` in `enumerate( [ "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "n...` in `_UNITS`.

```python
_TENS = {
    word: 10 * number
    for number, word in enumerate(
        ["zero", "ten", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    )
    if number > 1
}
```

- `_TENS = { word: 10 * number for number, word in enumerate( ["zero",...`: stores a dict built by running `word` for each `number, word` in `enumerate( ["zero", "ten", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "e...` keeping only those where `number` is greater than `1` in `_TENS`.

```python
_DAYS_AGO = re.compile(r"\bdays? (?:ago|old|since)\b", re.I)
```

- `_DAYS_AGO = re.compile(r"\bdays? (?:ago|old|since)\b", re.I)`: stores the result of calling `re.compile(r"\bdays? (?:ago|old|since)\b", re.I)`, which compiles the pattern `r"\bdays? (?:ago|old|since)\b"` so it can be matched many times in `_DAYS_AGO`.

```python
def words_to_number(text: str) -> int | None:
```

- Defines the function `words_to_number`.
- Parameters:
  - `text`, type `str`.
- Gives back a value of type `int | None`.

```python
"""A small number written in digits or words ("75", "seventy five", "a hundred"); None when it is not one."""
```

- The docstring (documentation kept with the code) says: *A small number written in digits or words ("75", "seventy five", "a hundred"); None when it is not one.*

```python
words = text.lower().replace("-", " ").split()
```

- `words = text.lower().replace("-", " ").split()`: stores the result of calling `text.lower().replace("-", " ").split()`, which cuts `text.lower().replace("-", " ")` into pieces at its argument (whitespace if nothing is given) in `words`.

```python
if len(words) == 1 and words[0].isdigit():
```

- Checks whether `len(words)` equals `1` and `words[0].isdigit()` is true (the call asks whether `words[0]` is only digits). If so, the indented lines run.

```python
return int(words[0])
```

- `return int(words[0])`: ends the function and gives back the result of calling `int(words[0])`, which turns `words[0]` into a whole number.

```python
total, seen = 0, False
```

- `total, seen = 0, False`: unpacks a tuple of 2 items into the names `total`, `seen`, one item each.

```python
for word in words:
```

- Repeats the indented lines once for each item of `words`, naming the current item `word`.

```python
if word in ("a", "one") and not seen:
```

- Checks whether `word` is among `("a", "one")` and it is not the case that `seen` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
total, seen = 1, True
continue
```

- `total, seen = 1, True`: unpacks a tuple of 2 items into the names `total`, `seen`, one item each.
- `continue`: skips to the next round of the loop.

```python
if word == "hundred":
```

- Checks whether `word` equals `"hundred"`. If so, the indented lines run.

```python
total, seen = (total or 1) * 100, True
```

- `total, seen = (total or 1) * 100, True`: unpacks a tuple of 2 items into the names `total`, `seen`, one item each.

```python
elif word in _TENS:
```

- Otherwise, checks whether `word` is among `_TENS`. If so, the indented lines run.

```python
total, seen = total + _TENS[word], True
```

- `total, seen = total + _TENS[word], True`: unpacks a tuple of 2 items into the names `total`, `seen`, one item each.

```python
elif word in _UNITS:
```

- Otherwise, checks whether `word` is among `_UNITS`. If so, the indented lines run.

```python
total, seen = total + _UNITS[word], True
```

- `total, seen = total + _UNITS[word], True`: unpacks a tuple of 2 items into the names `total`, `seen`, one item each.

```python
elif word == "and":
```

- Otherwise, checks whether `word` equals `"and"`. If so, the indented lines run.

```python
continue
```

- `continue`: skips to the next round of the loop.

```python
else:
```

- Runs when none of the conditions above held.

```python
return None
```

- `return None`: ends the function and gives back nothing (`None`).

```python
return total if seen else None
```

- `return total if seen else None`: ends the function and gives back `total` when `seen` is truthy (not `None`, `False`, zero or empty), otherwise `None`.

```python
def days_since_delivery(question: str) -> int | None:
```

- Defines the function `days_since_delivery`.
- Parameters:
  - `question`, type `str`.
- Gives back a value of type `int | None`.

```python
"""The age in days a question states ("sixty days ago", "75 days ago"), or None. The longest run of up to four
words before "days ago" that reads as a number wins, so "seventy five" is 75, not 5."""
```

- The docstring (documentation kept with the code) says: *The age in days a question states ("sixty days ago", "75 days ago"), or None. The longest run of up to four words before "days ago" that reads as a number wins, so "seventy five" is 75, not 5.*

```python
for match in _DAYS_AGO.finditer(question):
```

- Repeats the indented lines once for each item of `_DAYS_AGO.finditer(question)`, naming the current item `match`.

```python
tokens = re.findall(r"[\w-]+", question[: match.start()])[-4:]
```

- `tokens = re.findall(r"[\w-]+", question[: match.start()])[-4:]`: stores the item `re.findall(r"[\w-]+", question[: match.start()])[-4:]` in `tokens`.

```python
for start in range(len(tokens)):
```

- Repeats the indented lines once for each item of `range(len(tokens))`, naming the current item `start`.

```python
number = words_to_number(" ".join(tokens[start:]))
```

- `number = words_to_number(" ".join(tokens[start:]))`: stores the result of calling `words_to_number(" ".join(tokens[start:]))`, which is this repository's own `words_to_number` (in `src/streaming_assistant/domain/routing.py`): a small number written in digits or words ("75", "seventy five", "a hundred"); None when it is not one in `number`.

```python
if number is not None:
```

- Checks whether `number` is something (not `None`). If so, the indented lines run.

```python
return number
```

- `return number`: ends the function and gives back the value of `number`.

```python
return None
```

- `return None`: ends the function and gives back nothing (`None`).

```python
def needs_a_person(question: str) -> bool:
```

- Defines the function `needs_a_person`.
- Parameters:
  - `question`, type `str`.
- Gives back a value of type `bool`.

```python
"""A refund asked for after the 30-day window, or a legal threat: a policy exception only a person can grant."""
```

- The docstring (documentation kept with the code) says: *A refund asked for after the 30-day window, or a legal threat: a policy exception only a person can grant.*

```python
age = days_since_delivery(question)
return bool(LEGAL.search(question)) or (
    REFUND.search(question) is not None and age is not None and age > RETURN_WINDOW_DAYS
)
```

- `age = days_since_delivery(question)`: stores the result of calling `days_since_delivery(question)`, which is this repository's own `days_since_delivery` (in `src/streaming_assistant/domain/routing.py`): the age in days a question states ("sixty days ago", "75 days ago"), or None in `age`.
- `return bool(LEGAL.search(question)) or ( REFUND.search(question) is...`: ends the function and gives back `bool(LEGAL.search(question)) or ( REFUND.search(question) is not None and age is not No...` (the first operand that decides the or).

```python
@dataclass(frozen=True, slots=True)
class Thresholds:
```

- Defines the class `Thresholds`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""Retrieval coverage at which a question is answered, called thin, or sent to a person."""
```

- The docstring (documentation kept with the code) says: *Retrieval coverage at which a question is answered, called thin, or sent to a person.*

```python
confident: float = 0.6
pause_below: float = 0.4
```

- `confident: float = 0.6`: a field named `confident` of type `float`, default `0.6`.
- `pause_below: float = 0.4`: a field named `pause_below` of type `float`, default `0.4`.

```python
@dataclass(frozen=True, slots=True)
class Route:
```

- Defines the class `Route`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""The decision and why."""
```

- The docstring (documentation kept with the code) says: *The decision and why.*

```python
kind: str
reason: str
```

- `kind: str`: a field named `kind` of type `str`, no default (must be given).
- `reason: str`: a field named `reason` of type `str`, no default (must be given).

```python
def decide_route(question: str, hits: Sequence[Hit], thresholds: Thresholds, *, pause_enabled: bool = True) -> Route:
```

- Defines the function `decide_route`.
- Parameters:
  - `question`, type `str`.
  - `hits`, type `Sequence[Hit]`.
  - `thresholds`, type `Thresholds`.
  - `pause_enabled`, type `bool`, optional (default `True`). Must be passed by name.
- Gives back a value of type `Route`.

```python
"""A question that matches a needs-a-person pattern pauses; so does one no page covers (when pausing is on)."""
```

- The docstring (documentation kept with the code) says: *A question that matches a needs-a-person pattern pauses; so does one no page covers (when pausing is on).*

```python
if pause_enabled and needs_a_person(question):
```

- Checks whether `pause_enabled` is truthy (not `None`, `False`, zero or empty) and `needs_a_person(question)` is true (the call is this repository's own `needs_a_person` (in `src/streaming_assistant/domain/routing.py`): a refund asked for after the 30-day window, or a legal threat: a policy exception only a person can grant). If so, the indented lines run.

```python
return Route(PAUSE, "policy_exception")
```

- `return Route(PAUSE, "policy_exception")`: ends the function and gives back the result of calling `Route(PAUSE, "policy_exception")`, which is this repository's own `Route` (in `src/streaming_assistant/domain/routing.py`): the decision and why.

```python
best = hits[0].coverage if hits else 0.0
```

- `best = hits[0].coverage if hits else 0.0`: stores `hits[0].coverage` when `hits` is truthy (not `None`, `False`, zero or empty), otherwise `0.0` in `best`.

```python
if best < thresholds.pause_below:
```

- Checks whether `best` is less than `thresholds.pause_below`. If so, the indented lines run.

```python
return Route(PAUSE, "no_page_covers") if pause_enabled else Route(NO_EVIDENCE, "no_page_covers")
```

- `return Route(PAUSE, "no_page_covers") if pause_enabled else Route(N...`: ends the function and gives back `Route(PAUSE, "no_page_covers")` when `pause_enabled` is truthy (not `None`, `False`, zero or empty), otherwise `Route(NO_EVIDENCE, "no_page_covers")`.

```python
if best < thresholds.confident:
```

- Checks whether `best` is less than `thresholds.confident`. If so, the indented lines run.

```python
return Route(LOW_CONFIDENCE, f"best coverage {best:.2f} is below {thresholds.confident:.2f}")
```

- `return Route(LOW_CONFIDENCE, f"best coverage {best:.2f} is below {t...`: ends the function and gives back the result of calling `Route(LOW_CONFIDENCE, f"best coverage {best:.2f} is below {thresholds.confident:.2f}")`, which is this repository's own `Route` (in `src/streaming_assistant/domain/routing.py`): the decision and why.

```python
return Route(ANSWER, f"best coverage {best:.2f}")
```

- `return Route(ANSWER, f"best coverage {best:.2f}")`: ends the function and gives back the result of calling `Route(ANSWER, f"best coverage {best:.2f}")`, which is this repository's own `Route` (in `src/streaming_assistant/domain/routing.py`): the decision and why.

#### `src/streaming_assistant/domain/stats.py`

```python
"""Small statistics for the load test."""
```

- The docstring (documentation kept with the code) says: *Small statistics for the load test.*

```python
from __future__ import annotations

import math
from collections.abc import Sequence
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import math`: makes the module `math` available (mathematical functions).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Sequence`: the type hint for an ordered, indexable collection.)

```python
def percentile(values: Sequence[float], fraction: float) -> float:
```

- Defines the function `percentile`.
- Parameters:
  - `values`, type `Sequence[float]`.
  - `fraction`, type `float`.
- Gives back a value of type `float`.

```python
"""Nearest-rank percentile of `values` (0.95 for p95); 0.0 for no values."""
```

- The docstring (documentation kept with the code) says: *Nearest-rank percentile of `values` (0.95 for p95); 0.0 for no values.*

```python
if not values:
```

- Checks whether it is not the case that `values` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
return 0.0
```

- `return 0.0`: ends the function and gives back the number `0.0`.

```python
ordered = sorted(values)
return ordered[min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))]
```

- `ordered = sorted(values)`: stores the result of calling `sorted(values)`, which builds a new list with the items of `values` in order in `ordered`.
- `return ordered[min(len(ordered) - 1, max(0, math.ceil(fraction * le...`: ends the function and gives back the item `ordered[min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))]`.

#### `src/streaming_assistant/infrastructure/__init__.py`

```python
"""The infrastructure layer."""
```

- The docstring (documentation kept with the code) says: *The infrastructure layer.*

#### `src/streaming_assistant/infrastructure/catalog.py`

```python
"""The help center on disk: page catalog, a lazily built BM25 index (so the cold start is real) and a query cache."""
```

- The docstring (documentation kept with the code) says: *The help center on disk: page catalog, a lazily built BM25 index (so the cold start is real) and a query cache.*

```python
from __future__ import annotations

import html
import json
import threading
import time
from collections import OrderedDict
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import html`: makes the module `html` available (helpers for HTML text, such as escaping).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import threading`: makes the module `threading` available (threads, locks and events).
- `import time`: makes the module `time` available (clocks and sleeping).
- `from collections import ...`: takes names from `collections` (the standard library's extra container types (Counter, defaultdict, deque)). (`OrderedDict`: a name provided by that module.)

```python
from pathlib import Path

from streaming_assistant.domain.retrieval import Bm25Index, Hit, Section
```

- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from streaming_assistant.domain.retrieval import ...`: takes names from `streaming_assistant.domain.retrieval`, this repository's own code. (`Bm25Index`: Built once from the sections.) (`Hit`: A section the retriever returned, with its raw score and the share of the question's weight it covers.) (`Section`: One section of a help page; `anchor` is where a citation opens the page.)

```python
class PageCatalog:
```

- Defines the class `PageCatalog`.

```python
"""Loads `data/help_pages.json`: 30 pages with titled sections."""
```

- The docstring (documentation kept with the code) says: *Loads `data/help_pages.json`: 30 pages with titled sections.*

```python
def __init__(self, path: Path) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `path`, type `Path`.
- Gives back a value of type `None`.

```python
pages = json.loads(path.read_text(encoding="utf-8"))
self._sections = [
    Section(page["page_id"], page["title"], section["anchor"], section["heading"], section["text"])
    for page in pages
    for section in page["sections"]
]
self._by_ref = {section.ref: section for section in self._sections}
self._pages = {page["page_id"]: page for page in pages}
```

- `pages = json.loads(path.read_text(encoding="utf-8"))`: stores the result of calling `json.loads(path.read_text(encoding="utf-8"))`, which turns the JSON text `path.read_text(encoding="utf-8")` into Python values in `pages`.
- `self._sections = [ Section(page["page_id"], page["title"], section[...`: stores a list built by running `Section(page["page_id"], page["title"], section["anchor"], section["heading"], section[...` for each `page` in `pages` in `self._sections`.
- `self._by_ref = {section.ref: section for section in self._sections}`: stores a dict built by running `section.ref` for each `section` in `self._sections` in `self._by_ref`.
- `self._pages = {page["page_id"]: page for page in pages}`: stores a dict built by running `page["page_id"]` for each `page` in `pages` in `self._pages`.

```python
@property
def sections(self) -> list[Section]:
```

- Defines the method `sections`.
- `@property`: the method is read like an attribute.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `list[Section]`.

```python
"""Every section of every page."""
```

- The docstring (documentation kept with the code) says: *Every section of every page.*

```python
return list(self._sections)
```

- `return list(self._sections)`: ends the function and gives back the result of calling `list(self._sections)`, which builds a new list from `self._sections`.

```python
def section(self, ref: str) -> Section | None:
```

- Defines the method `section`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `ref`, type `str`.
- Gives back a value of type `Section | None`.

```python
"""The section a `page#anchor` ref names, or None."""
```

- The docstring (documentation kept with the code) says: *The section a `page#anchor` ref names, or None.*

```python
return self._by_ref.get(ref)
```

- `return self._by_ref.get(ref)`: ends the function and gives back the result of calling `self._by_ref.get(ref)`, which is this repository's own `get` (in `src/streaming_assistant/application/ports.py`): one run, or None.

```python
def page_html(self, page_id: str) -> str | None:
```

- Defines the method `page_html`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `page_id`, type `str`.
- Gives back a value of type `str | None`.

```python
"""A page as HTML with an id on every section, so `#anchor` opens it at the cited section."""
```

- The docstring (documentation kept with the code) says: *A page as HTML with an id on every section, so `#anchor` opens it at the cited section.*

```python
page = self._pages.get(page_id)
```

- `page = self._pages.get(page_id)`: stores the result of calling `self._pages.get(page_id)`, which is this repository's own `get` (in `src/streaming_assistant/application/ports.py`): one run, or None in `page`.

```python
if page is None:
```

- Checks whether `page` is nothing (`None`). If so, the indented lines run.

```python
return None
```

- `return None`: ends the function and gives back nothing (`None`).

```python
body = "".join(
    f'<section id="{html.escape(s["anchor"])}"><h2>{html.escape(s["heading"])}</h2><p>{html.escape(s["text"])}</p></section>'
    for s in page["sections"]
)
title = html.escape(page["title"])
return (
    f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
    f"<title>{title}</title><style>:target{{background:#fff3b0}}body{{font:16px/1.5 system-ui;max-width:42rem;margin:2rem auto;padding:0 1rem}}</style>"
    f"</head><body><h1>{title}</h1>{body}</body></html>"
)
```

- `body = "".join( f'<section id="{html.escape(s["anchor"])}"><h2>{htm...`: stores the result of calling `"".join( f'<section id="{html.escape(s["anchor"])}"><h2>{html.escape(s["heading"])}</h2...`, which glues the items of `( f'<section id="{html.escape(s["anchor"])}"><h2>{html.escape(s["heading"])}</h2><p>{ht...` together with `""` between them in `body`.
- `title = html.escape(page["title"])`: stores the result of calling `html.escape(page["title"])`, which escapes the characters that mean something in HTML in `title`.
- `return ( f'<!doctype html><html lang="en"><head><meta charset="utf-...`: ends the function and gives back the text built by the f-string `f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" cont...`.

```python
class LazyBm25Retriever:
```

- Defines the class `LazyBm25Retriever`.

```python
"""Builds the index on the first search (the cold start the budget must account for); `warm` builds it ahead of time."""
```

- The docstring (documentation kept with the code) says: *Builds the index on the first search (the cold start the budget must account for); `warm` builds it ahead of time.*

```python
def __init__(self, catalog: PageCatalog) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `catalog`, type `PageCatalog`.
- Gives back a value of type `None`.

```python
self._catalog = catalog
self._index: Bm25Index | None = None
self._lock = threading.Lock()
self.build_seconds: float | None = None
```

- `self._catalog = catalog`: stores the value of `catalog` in `self._catalog`.
- `self._index: Bm25Index | None = None`: stores nothing (`None`) in `self._index`, whose type is declared as `Bm25Index | None`.
- `self._lock = threading.Lock()`: stores the result of calling `threading.Lock()`, which makes a `Lock` object in `self._lock`.
- `self.build_seconds: float | None = None`: stores nothing (`None`) in `self.build_seconds`, whose type is declared as `float | None`.

```python
def warm(self) -> None:
```

- Defines the method `warm`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `None`.

```python
"""Build the index now."""
```

- The docstring (documentation kept with the code) says: *Build the index now.*

```python
with self._lock:
```

- Opens `self._lock` for the indented lines, and releases it when they end (even after an error).

```python
if self._index is None:
```

- Checks whether `self._index` is nothing (`None`). If so, the indented lines run.

```python
started = time.perf_counter()
self._index = Bm25Index(self._catalog.sections)
self.build_seconds = time.perf_counter() - started
```

- `started = time.perf_counter()`: stores the result of calling `time.perf_counter()`, which reads the high-resolution timer in seconds in `started`.
- `self._index = Bm25Index(self._catalog.sections)`: stores the result of calling `Bm25Index(self._catalog.sections)`, which is this repository's own `Bm25Index` (in `src/streaming_assistant/domain/retrieval.py`): built once from the sections in `self._index`.
- `self.build_seconds = time.perf_counter() - started`: stores `time.perf_counter() - started`, which subtracts `time.perf_counter()` and `started` in `self.build_seconds`.

```python
def search(self, query: str, limit: int = 3) -> list[Hit]:
```

- Defines the method `search`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `query`, type `str`.
  - `limit`, type `int`, optional (default `3`).
- Gives back a value of type `list[Hit]`.

```python
"""Best sections first; the first call pays for building the index unless `warm` ran."""
```

- The docstring (documentation kept with the code) says: *Best sections first; the first call pays for building the index unless `warm` ran.*

```python
self.warm()
assert self._index is not None
return self._index.search(query, limit)
```

- `self.warm()`: calling `self.warm()`, which is this repository's own `warm` (in `src/streaming_assistant/infrastructure/catalog.py`): build the index now.
- `assert self._index is not None`: checks that `self._index` is something (not `None`). A false check stops the test as failed.
- `return self._index.search(query, limit)`: ends the function and gives back the result of calling `self._index.search(query, limit)`, which looks for the pattern anywhere in the text.

```python
class CachingRetriever:
```

- Defines the class `CachingRetriever`.

```python
"""A small LRU cache in front of a retriever, keyed by the normalized query. Repeated questions skip the scoring."""
```

- The docstring (documentation kept with the code) says: *A small LRU cache in front of a retriever, keyed by the normalized query. Repeated questions skip the scoring.*

```python
def __init__(self, inner: LazyBm25Retriever, size: int = 512) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `inner`, type `LazyBm25Retriever`.
  - `size`, type `int`, optional (default `512`).
- Gives back a value of type `None`.

```python
self._inner = inner
self._size = size
self._cache: OrderedDict[tuple[str, int], list[Hit]] = OrderedDict()
self._lock = threading.Lock()
self.hits = 0
self.misses = 0
```

- `self._inner = inner`: stores the value of `inner` in `self._inner`.
- `self._size = size`: stores the value of `size` in `self._size`.
- `self._cache: OrderedDict[tuple[str, int], list[Hit]] = OrderedDict()`: stores the result of calling `OrderedDict()`, which makes a `OrderedDict` object in `self._cache`, whose type is declared as `OrderedDict[tuple[str, int], list[Hit]]`.
- `self._lock = threading.Lock()`: stores the result of calling `threading.Lock()`, which makes a `Lock` object in `self._lock`.
- `self.hits = 0`: stores the number `0` in `self.hits`.
- `self.misses = 0`: stores the number `0` in `self.misses`.

```python
def search(self, query: str, limit: int = 3) -> list[Hit]:
```

- Defines the method `search`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `query`, type `str`.
  - `limit`, type `int`, optional (default `3`).
- Gives back a value of type `list[Hit]`.

```python
"""Cached hits for a repeated query."""
```

- The docstring (documentation kept with the code) says: *Cached hits for a repeated query.*

```python
key = (" ".join(query.lower().split()), limit)
```

- `key = (" ".join(query.lower().split()), limit)`: stores a tuple of 2 items in `key`.

```python
with self._lock:
```

- Opens `self._lock` for the indented lines, and releases it when they end (even after an error).

```python
if key in self._cache:
```

- Checks whether `key` is among `self._cache`. If so, the indented lines run.

```python
self._cache.move_to_end(key)
self.hits += 1
return list(self._cache[key])
```

- `self._cache.move_to_end(key)`: calling `self._cache.move_to_end(key)`.
- `self.hits += 1`: adds `1` to `self.hits` and keeps the result there.
- `return list(self._cache[key])`: ends the function and gives back the result of calling `list(self._cache[key])`, which builds a new list from `self._cache[key]`.

```python
found = self._inner.search(query, limit)
```

- `found = self._inner.search(query, limit)`: stores the result of calling `self._inner.search(query, limit)`, which looks for the pattern anywhere in the text in `found`.

```python
with self._lock:
```

- Opens `self._lock` for the indented lines, and releases it when they end (even after an error).

```python
self.misses += 1
self._cache[key] = found
```

- `self.misses += 1`: adds `1` to `self.misses` and keeps the result there.
- `self._cache[key] = found`: stores the value of `found` in the slot `self._cache[key]`.

```python
while len(self._cache) > self._size:
```

- Repeats the indented lines for as long as `len(self._cache)` is greater than `self._size`.

```python
self._cache.popitem(last=False)
```

- `self._cache.popitem(last=False)`: calling `self._cache.popitem(last=False)` The named values are `last`..

```python
return list(found)
```

- `return list(found)`: ends the function and gives back the result of calling `list(found)`, which builds a new list from `found`.

#### `src/streaming_assistant/infrastructure/claude_stream.py`

```python
"""The real adapter: Claude streaming through the official SDK. Leaving the stream closes the HTTP connection upstream."""
```

- The docstring (documentation kept with the code) says: *The real adapter: Claude streaming through the official SDK. Leaving the stream closes the HTTP connection upstream.*

```python
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import anthropic

from streaming_assistant.application.ports import Chunk, StreamRequest, TextDelta, Usage
from streaming_assistant.domain.errors import ProviderError, RateLimitedError, RefusedError
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`AsyncIterator`: a name provided by that module.)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`Any`: the type hint meaning 'anything'.)
- `import anthropic`: makes the module `anthropic` available (Anthropic's official Python library for calling Claude).
- `from streaming_assistant.application.ports import ...`: takes names from `streaming_assistant.application.ports`, this repository's own code. (`Chunk`: a name defined in this repository.) (`StreamRequest`: One streamed completion.) (`TextDelta`: A piece of the answer.) (`Usage`: Token counts, sent when the stream ends normally.)
- `from streaming_assistant.domain.errors import ...`: takes names from `streaming_assistant.domain.errors`, this repository's own code. (`ProviderError`: The model provider failed (a server error or a dropped connection).) (`RateLimitedError`: The model provider answered 429.) (`RefusedError`: The model declined to answer.)

```python
from streaming_assistant.infrastructure.environment import ConfigurationError
```

- `from streaming_assistant.infrastructure.environment import ...`: takes names from `streaming_assistant.infrastructure.environment`, this repository's own code. (`ConfigurationError`: An environment variable is missing or has an unusable value.)

```python
class ClaudeStreamingModel:
```

- Defines the class `ClaudeStreamingModel`.

```python
"""One streamed Messages API call. `tier` picks the model id: the fast tier uses the small model."""
```

- The docstring (documentation kept with the code) says: *One streamed Messages API call. `tier` picks the model id: the fast tier uses the small model.*

```python
def __init__(
    self, model_ids: dict[str, str], api_key: str | None, *, timeout_seconds: float = 60.0, client: Any = None
) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `model_ids`, type `dict[str, str]`.
  - `api_key`, type `str | None`.
  - `timeout_seconds`, type `float`, optional (default `60.0`). Must be passed by name.
  - `client`, type `Any`, optional (default `None`). Must be passed by name.
- Gives back a value of type `None`.

```python
if client is None:
```

- Checks whether `client` is nothing (`None`). If so, the indented lines run.

```python
if not api_key:
```

- Checks whether it is not the case that `api_key` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
raise ConfigurationError("ANTHROPIC_API_KEY must be set to use the Claude adapter")
```

- `raise ConfigurationError("ANTHROPIC_API_KEY must be set to use the ...`: stops with an error of kind `ConfigurationError` with the message `"ANTHROPIC_API_KEY must be set to use the Claude adapter"`. Whoever called this code must handle it or the program stops.

```python
client = anthropic.AsyncAnthropic(api_key=api_key, timeout=timeout_seconds, max_retries=0)
```

- `client = anthropic.AsyncAnthropic(api_key=api_key, timeout=timeout_...`: stores the result of calling `anthropic.AsyncAnthropic(api_key=api_key, timeout=timeout_seconds, max_retries=0)`, which makes a `AsyncAnthropic` object with the named values `api_key`, `timeout`, `max_retries` in `client`.

```python
self._client = client
self._model_ids = model_ids
```

- `self._client = client`: stores the value of `client` in `self._client`.
- `self._model_ids = model_ids`: stores the value of `model_ids` in `self._model_ids`.

```python
async def stream(self, request: StreamRequest) -> AsyncIterator[Chunk]:
```

- Defines the async method `stream` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `request`, type `StreamRequest`.
- Gives back a value of type `AsyncIterator[Chunk]`.

```python
"""Yield text deltas as they arrive, then the usage; map provider failures to the assistant's named errors."""
```

- The docstring (documentation kept with the code) says: *Yield text deltas as they arrive, then the usage; map provider failures to the assistant's named errors.*

```python
model = self._model_ids.get(request.tier, self._model_ids["standard"])
```

- `model = self._model_ids.get(request.tier, self._model_ids["standard"])`: stores the result of calling `self._model_ids.get(request.tier, self._model_ids["standard"])`, which is this repository's own `get` (in `src/streaming_assistant/application/ports.py`): one run, or None in `model`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
async with self._client.messages.stream(
    model=model, max_tokens=700, system=request.system, messages=[{"role": "user", "content": request.user}]
) as stream:
```

- Opens `self._client.messages.stream( model=model, max_tokens=700, system=request.system, messa...` as `stream` for the indented lines, and cleans it up when they end (even after an error).

```python
async for text in stream.text_stream:
```

- Repeats the indented lines once for each item of `stream.text_stream`, naming the current item `text`. (`async for` waits for each item.)

```python
yield TextDelta(text)
```

- `yield TextDelta(text)`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
final = await stream.get_final_message()
```

- `final = await stream.get_final_message()`: stores the answer of the result of calling `stream.get_final_message()` once the wait is over in `final`.

```python
except anthropic.RateLimitError as error:
```

- If an error of kind `anthropic.RateLimitError` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
raise RateLimitedError(str(error)) from error
```

- `raise RateLimitedError(str(error)) from error`: stops with an error of kind `RateLimitedError` with the message `str(error)`, recording `error` as the cause. Whoever called this code must handle it or the program stops.

```python
except (anthropic.APIConnectionError, anthropic.APIStatusError) as error:
```

- If an error of kind `(anthropic.APIConnectionError, anthropic.APIStatusError)` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
raise ProviderError(f"{type(error).__name__}: {error}") from error
```

- `raise ProviderError(f"{type(error).__name__}: {error}") from error`: stops with an error of kind `ProviderError` with the message `f"{type(error).__name__}: {error}"`, recording `error` as the cause. Whoever called this code must handle it or the program stops.

```python
if final.stop_reason == "refusal":
```

- Checks whether `final.stop_reason` equals `"refusal"`. If so, the indented lines run.

```python
raise RefusedError("stop_reason=refusal")
```

- `raise RefusedError("stop_reason=refusal")`: stops with an error of kind `RefusedError` with the message `"stop_reason=refusal"`. Whoever called this code must handle it or the program stops.

```python
yield Usage(final.usage.input_tokens, final.usage.output_tokens)
```

- `yield Usage(final.usage.input_tokens, final.usage.output_tokens)`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

#### `src/streaming_assistant/infrastructure/clock.py`

```python
"""The system clock."""
```

- The docstring (documentation kept with the code) says: *The system clock.*

```python
from __future__ import annotations

from datetime import UTC, datetime
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from datetime import ...`: takes names from `datetime` (dates, times and time spans). (`UTC`: the UTC time zone.) (`datetime`: the date-and-time type.)

```python
class SystemClock:
```

- Defines the class `SystemClock`.

```python
"""Now, in UTC."""
```

- The docstring (documentation kept with the code) says: *Now, in UTC.*

```python
def now(self) -> datetime:
```

- Defines the method `now`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `datetime`.

```python
"""The current time, timezone-aware."""
```

- The docstring (documentation kept with the code) says: *The current time, timezone-aware.*

```python
return datetime.now(UTC)
```

- `return datetime.now(UTC)`: ends the function and gives back the result of calling `datetime.now(UTC)`, which reads the current date and time.

#### `src/streaming_assistant/infrastructure/environment.py`

```python
"""Configuration helpers: read and validate environment variables once at startup (twelve-factor)."""
```

- The docstring (documentation kept with the code) says: *Configuration helpers: read and validate environment variables once at startup (twelve-factor).*

```python
from __future__ import annotations

from collections.abc import Mapping
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Mapping`: the type hint for a read-only dict-like collection.)

```python
class ConfigurationError(ValueError):
```

- Defines the class `ConfigurationError`.
- It extends `ValueError`: it is a kind of error that can be raised and caught.

```python
"""An environment variable is missing or has an unusable value."""
```

- The docstring (documentation kept with the code) says: *An environment variable is missing or has an unusable value.*

```python
def read_text(environ: Mapping[str, str], name: str, default: str | None = None) -> str:
```

- Defines the function `read_text`.
- Parameters:
  - `environ`, type `Mapping[str, str]`.
  - `name`, type `str`.
  - `default`, type `str | None`, optional (default `None`).
- Gives back a value of type `str`.

```python
"""A non-empty string variable, or `default`."""
```

- The docstring (documentation kept with the code) says: *A non-empty string variable, or `default`.*

```python
value = environ.get(name, default if default is not None else "").strip()
```

- `value = environ.get(name, default if default is not None else "").s...`: stores the result of calling `environ.get(name, default if default is not None else "").strip()`, which removes spaces and line breaks from both ends of `environ.get(name, default if default is not None else "")` (or the characters its argument) in `value`.

```python
if not value:
```

- Checks whether it is not the case that `value` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
raise ConfigurationError(f"{name} must be set and not empty")
```

- `raise ConfigurationError(f"{name} must be set and not empty")`: stops with an error of kind `ConfigurationError` with the message `f"{name} must be set and not empty"`. Whoever called this code must handle it or the program stops.

```python
return value
```

- `return value`: ends the function and gives back the value of `value`.

```python
def read_optional(environ: Mapping[str, str], name: str) -> str | None:
```

- Defines the function `read_optional`.
- Parameters:
  - `environ`, type `Mapping[str, str]`.
  - `name`, type `str`.
- Gives back a value of type `str | None`.

```python
"""A string variable that may be absent or empty (for example an API key)."""
```

- The docstring (documentation kept with the code) says: *A string variable that may be absent or empty (for example an API key).*

```python
value = environ.get(name, "").strip()
return value or None
```

- `value = environ.get(name, "").strip()`: stores the result of calling `environ.get(name, "").strip()`, which removes spaces and line breaks from both ends of `environ.get(name, "")` (or the characters its argument) in `value`.
- `return value or None`: ends the function and gives back `value or None` (the first operand that decides the or).

```python
def read_int(environ: Mapping[str, str], name: str, default: int, minimum: int = 1) -> int:
```

- Defines the function `read_int`.
- Parameters:
  - `environ`, type `Mapping[str, str]`.
  - `name`, type `str`.
  - `default`, type `int`.
  - `minimum`, type `int`, optional (default `1`).
- Gives back a value of type `int`.

```python
"""An integer variable of at least `minimum`."""
```

- The docstring (documentation kept with the code) says: *An integer variable of at least `minimum`.*

```python
raw = environ.get(name, str(default)).strip()
```

- `raw = environ.get(name, str(default)).strip()`: stores the result of calling `environ.get(name, str(default)).strip()`, which removes spaces and line breaks from both ends of `environ.get(name, str(default))` (or the characters its argument) in `raw`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
value = int(raw)
```

- `value = int(raw)`: stores the result of calling `int(raw)`, which turns `raw` into a whole number in `value`.

```python
except ValueError:
```

- If an error of kind `ValueError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
raise ConfigurationError(f"{name} must be an integer, got {raw!r}") from None
```

- `raise ConfigurationError(f"{name} must be an integer, got {raw!r}")...`: stops with an error of kind `ConfigurationError` with the message `f"{name} must be an integer, got {raw!r}"`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
if value < minimum:
```

- Checks whether `value` is less than `minimum`. If so, the indented lines run.

```python
raise ConfigurationError(f"{name} must be at least {minimum}, got {value}")
```

- `raise ConfigurationError(f"{name} must be at least {minimum}, got {...`: stops with an error of kind `ConfigurationError` with the message `f"{name} must be at least {minimum}, got {value}"`. Whoever called this code must handle it or the program stops.

```python
return value
```

- `return value`: ends the function and gives back the value of `value`.

```python
def read_float(environ: Mapping[str, str], name: str, default: float, minimum: float = 0.0) -> float:
```

- Defines the function `read_float`.
- Parameters:
  - `environ`, type `Mapping[str, str]`.
  - `name`, type `str`.
  - `default`, type `float`.
  - `minimum`, type `float`, optional (default `0.0`).
- Gives back a value of type `float`.

```python
"""A float variable of at least `minimum`."""
```

- The docstring (documentation kept with the code) says: *A float variable of at least `minimum`.*

```python
raw = environ.get(name, str(default)).strip()
```

- `raw = environ.get(name, str(default)).strip()`: stores the result of calling `environ.get(name, str(default)).strip()`, which removes spaces and line breaks from both ends of `environ.get(name, str(default))` (or the characters its argument) in `raw`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
value = float(raw)
```

- `value = float(raw)`: stores the result of calling `float(raw)`, which turns `raw` into a decimal number in `value`.

```python
except ValueError:
```

- If an error of kind `ValueError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
raise ConfigurationError(f"{name} must be a number, got {raw!r}") from None
```

- `raise ConfigurationError(f"{name} must be a number, got {raw!r}") f...`: stops with an error of kind `ConfigurationError` with the message `f"{name} must be a number, got {raw!r}"`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
if value < minimum:
```

- Checks whether `value` is less than `minimum`. If so, the indented lines run.

```python
raise ConfigurationError(f"{name} must be at least {minimum}, got {value}")
```

- `raise ConfigurationError(f"{name} must be at least {minimum}, got {...`: stops with an error of kind `ConfigurationError` with the message `f"{name} must be at least {minimum}, got {value}"`. Whoever called this code must handle it or the program stops.

```python
return value
```

- `return value`: ends the function and gives back the value of `value`.

```python
def read_choice(environ: Mapping[str, str], name: str, default: str, choices: frozenset[str]) -> str:
```

- Defines the function `read_choice`.
- Parameters:
  - `environ`, type `Mapping[str, str]`.
  - `name`, type `str`.
  - `default`, type `str`.
  - `choices`, type `frozenset[str]`.
- Gives back a value of type `str`.

```python
"""A string variable restricted to `choices`."""
```

- The docstring (documentation kept with the code) says: *A string variable restricted to `choices`.*

```python
value = environ.get(name, default).strip()
```

- `value = environ.get(name, default).strip()`: stores the result of calling `environ.get(name, default).strip()`, which removes spaces and line breaks from both ends of `environ.get(name, default)` (or the characters its argument) in `value`.

```python
if value not in choices:
```

- Checks whether `value` is not among `choices`. If so, the indented lines run.

```python
raise ConfigurationError(f"{name} must be one of {sorted(choices)}, got {value!r}")
```

- `raise ConfigurationError(f"{name} must be one of {sorted(choices)},...`: stops with an error of kind `ConfigurationError` with the message `f"{name} must be one of {sorted(choices)}, got {value!r}"`. Whoever called this code must handle it or the program stops.

```python
return value
```

- `return value`: ends the function and gives back the value of `value`.

#### `src/streaming_assistant/infrastructure/logging.py`

```python
"""Structured logging: one logfmt line per event. Prompt and completion text is never logged at INFO."""
```

- The docstring (documentation kept with the code) says: *Structured logging: one logfmt line per event. Prompt and completion text is never logged at INFO.*

```python
from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any, TextIO
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import logging`: makes the module `logging` available (the standard library's logging system).
- `import sys`: makes the module `sys` available (facts about the running Python program: arguments, exit, standard streams).
- `from datetime import ...`: takes names from `datetime` (dates, times and time spans). (`UTC`: the UTC time zone.) (`datetime`: the date-and-time type.)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`Any`: the type hint meaning 'anything'.) (`TextIO`: a name provided by that module.)

```python
def _quote(value: object) -> str:
```

- Defines the function `_quote`.
- Parameters:
  - `value`, type `object`.
- Gives back a value of type `str`.

```python
text = str(value)
return json.dumps(text) if not text or any(char in text for char in ' ="\n') else text
```

- `text = str(value)`: stores the result of calling `str(value)`, which turns `value` into text in `text`.
- `return json.dumps(text) if not text or any(char in text for char in...`: ends the function and gives back `json.dumps(text)` when it is not the case that `text` is truthy (not `None`, `False`, zero or empty) or `any(char in text for char in ' ="\n')` is true (the call is true if at least one item of `(char in text for char in ' ="\n')` is true), otherwise `text`.

```python
class LogfmtFormatter(logging.Formatter):
```

- Defines the class `LogfmtFormatter`.
- It extends `logging.Formatter` (it starts with all of that class's methods and may add or replace some).

```python
"""Format a log record as one logfmt line, with the record's extra fields as key=value pairs."""
```

- The docstring (documentation kept with the code) says: *Format a log record as one logfmt line, with the record's extra fields as key=value pairs.*

```python
def format(self, record: logging.LogRecord) -> str:
```

- Defines the method `format`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `record`, type `logging.LogRecord`.
- Gives back a value of type `str`.

```python
timestamp = datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds")
parts = [
    f"ts={timestamp}",
    f"level={record.levelname}",
    f"logger={record.name}",
    f"msg={_quote(record.getMessage())}",
]
parts.extend(f"{key}={_quote(value)}" for key, value in getattr(record, "fields", {}).items())
```

- `timestamp = datetime.fromtimestamp(record.created, tz=UTC).isoforma...`: stores the result of calling `datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds")`, which writes the date or time as ISO text The named values are `timespec`. in `timestamp`.
- `parts = [ f"ts={timestamp}", f"level={record.levelname}", f"logger=...`: stores a new list holding 4 items in `parts`.
- `parts.extend(f"{key}={_quote(value)}" for key, value in getattr(rec...`: calling `parts.extend(f"{key}={_quote(value)}" for key, value in getattr(record, "fields", {}).i...`, which adds every item of `(f"{key}={_quote(value)}" for key, value in getattr(record, "fields", {}).items())` to the end of `parts`.

```python
if record.exc_info:
```

- Checks whether `record.exc_info` is truthy. If so, the indented lines run.

```python
parts.append(f"exc={_quote(self.formatException(record.exc_info))}")
```

- `parts.append(f"exc={_quote(self.formatException(record.exc_info))}")`: calling `parts.append(f"exc={_quote(self.formatException(record.exc_info))}")`, which adds `f"exc={_quote(self.formatException(record.exc_info))}"` to the end of `parts`.

```python
return " ".join(parts)
```

- `return " ".join(parts)`: ends the function and gives back the result of calling `" ".join(parts)`, which glues the items of `parts` together with `" "` between them.

```python
def fields(**values: Any) -> dict[str, Any]:
```

- Defines the function `fields`.
- Parameters:
  - `**values`: collects extra named arguments in a dict.
- Gives back a value of type `dict[str, Any]`.

```python
"""Use as `logger.info("message", extra=fields(order_id=...))` to attach key=value pairs."""
```

- The docstring (documentation kept with the code) says: *Use as `logger.info("message", extra=fields(order_id=...))` to attach key=value pairs.*

```python
return {"fields": values}
```

- `return {"fields": values}`: ends the function and gives back a new dict with 1 entries.

```python
def configure_logging(level: str, stream: TextIO | None = None) -> None:
```

- Defines the function `configure_logging`.
- Parameters:
  - `level`, type `str`.
  - `stream`, type `TextIO | None`, optional (default `None`).
- Gives back a value of type `None`.

```python
"""Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice."""
```

- The docstring (documentation kept with the code) says: *Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.*

```python
handler = logging.StreamHandler(stream or sys.stderr)
handler.setFormatter(LogfmtFormatter())
root = logging.getLogger()
root.handlers[:] = [handler]
root.setLevel(level)
```

- `handler = logging.StreamHandler(stream or sys.stderr)`: stores the result of calling `logging.StreamHandler(stream or sys.stderr)`, which makes a `StreamHandler` object from `stream or sys.stderr` in `handler`.
- `handler.setFormatter(LogfmtFormatter())`: calling `handler.setFormatter(LogfmtFormatter())`.
- `root = logging.getLogger()`: stores the result of calling `logging.getLogger()`, which gets the logger named its argument in `root`.
- `root.handlers[:] = [handler]`: stores a new list holding 1 items in the slot `root.handlers[:]`.
- `root.setLevel(level)`: calling `root.setLevel(level)`.

```python
for noisy in ("httpx", "httpcore", "anthropic", "uvicorn.access"):
```

- Repeats the indented lines once for each item of `("httpx", "httpcore", "anthropic", "uvicorn.access")`, naming the current item `noisy`.

```python
logging.getLogger(noisy).setLevel(max(logging.getLevelName(level), logging.WARNING))
```

- `logging.getLogger(noisy).setLevel(max(logging.getLevelName(level), ...`: calling `logging.getLogger(noisy).setLevel(max(logging.getLevelName(level), logging.WARNING))`.

#### `src/streaming_assistant/infrastructure/recorded_stream.py`

```python
"""Recorded streams: a cassette maps a hash of the whole request to the text pieces and usage, so tests run offline."""
```

- The docstring (documentation kept with the code) says: *Recorded streams: a cassette maps a hash of the whole request to the text pieces and usage, so tests run offline.*

```python
from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import hashlib`: makes the module `hashlib` available (hash functions such as SHA-256).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`AsyncIterator`: a name provided by that module.)
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`Any`: the type hint meaning 'anything'.)

```python
from streaming_assistant.application.ports import Chunk, StreamingModel, StreamRequest, TextDelta, Usage
```

- `from streaming_assistant.application.ports import ...`: takes names from `streaming_assistant.application.ports`, this repository's own code. (`Chunk`: a name defined in this repository.) (`StreamingModel`: A model that streams.) (`StreamRequest`: One streamed completion.) (`TextDelta`: A piece of the answer.) (`Usage`: Token counts, sent when the stream ends normally.)

```python
class MissingRecordingError(LookupError):
```

- Defines the class `MissingRecordingError`.
- It extends `LookupError` (it starts with all of that class's methods and may add or replace some).

```python
"""No recording matches this request; the message says how to re-record."""
```

- The docstring (documentation kept with the code) says: *No recording matches this request; the message says how to re-record.*

```python
def request_key(model_id: str, request: StreamRequest) -> str:
```

- Defines the function `request_key`.
- Parameters:
  - `model_id`, type `str`.
  - `request`, type `StreamRequest`.
- Gives back a value of type `str`.

```python
"""Hash of everything that decides the stream: model, prompt version, tier, system text and user text."""
```

- The docstring (documentation kept with the code) says: *Hash of everything that decides the stream: model, prompt version, tier, system text and user text.*

```python
return hashlib.sha256(
    json.dumps([model_id, request.prompt_version, request.tier, request.system, request.user]).encode()
).hexdigest()
```

- `return hashlib.sha256( json.dumps([model_id, request.prompt_version...`: ends the function and gives back the result of calling `hashlib.sha256( json.dumps([model_id, request.prompt_version, request.tier, request.sys...`, which writes the hash as hexadecimal text.

```python
class RecordedStreamingModel:
```

- Defines the class `RecordedStreamingModel`.

```python
"""Replays the recorded pieces; a request with no recording fails loudly."""
```

- The docstring (documentation kept with the code) says: *Replays the recorded pieces; a request with no recording fails loudly.*

```python
def __init__(self, path: Path) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `path`, type `Path`.
- Gives back a value of type `None`.

```python
data = json.loads(path.read_text(encoding="utf-8"))
self.model_id: str = data["model"]
self.provenance: str = data["provenance"]
self._entries: dict[str, dict[str, Any]] = data["entries"]
```

- `data = json.loads(path.read_text(encoding="utf-8"))`: stores the result of calling `json.loads(path.read_text(encoding="utf-8"))`, which turns the JSON text `path.read_text(encoding="utf-8")` into Python values in `data`.
- `self.model_id: str = data["model"]`: stores the item `data["model"]` in `self.model_id`, whose type is declared as `str`.
- `self.provenance: str = data["provenance"]`: stores the item `data["provenance"]` in `self.provenance`, whose type is declared as `str`.
- `self._entries: dict[str, dict[str, Any]] = data["entries"]`: stores the item `data["entries"]` in `self._entries`, whose type is declared as `dict[str, dict[str, Any]]`.

```python
async def stream(self, request: StreamRequest) -> AsyncIterator[Chunk]:
```

- Defines the async method `stream` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `request`, type `StreamRequest`.
- Gives back a value of type `AsyncIterator[Chunk]`.

```python
"""The recorded text pieces, then the usage."""
```

- The docstring (documentation kept with the code) says: *The recorded text pieces, then the usage.*

```python
key = request_key(self.model_id, request)
entry = self._entries.get(key)
```

- `key = request_key(self.model_id, request)`: stores the result of calling `request_key(self.model_id, request)`, which is this repository's own `request_key` (in `src/streaming_assistant/infrastructure/recorded_stream.py`): hash of everything that decides the stream: model, prompt version, tier, system text and user text in `key`.
- `entry = self._entries.get(key)`: stores the result of calling `self._entries.get(key)`, which is this repository's own `get` (in `src/streaming_assistant/application/ports.py`): one run, or None in `entry`.

```python
if entry is None:
```

- Checks whether `entry` is nothing (`None`). If so, the indented lines run.

```python
raise MissingRecordingError(
    f"no recording for prompt {request.prompt_version} (key {key[:12]}); re-record with `make record` (needs ANTHROPIC_API_KEY)"
)
```

- `raise MissingRecordingError( f"no recording for prompt {request.pro...`: stops with an error of kind `MissingRecordingError` with the message ``f"no recording for prompt {request.prompt_version} (key {key[:12]}); re-record with `ma...``. Whoever called this code must handle it or the program stops.

```python
for piece in entry["pieces"]:
```

- Repeats the indented lines once for each item of `entry["pieces"]`, naming the current item `piece`.

```python
yield TextDelta(piece)
```

- `yield TextDelta(piece)`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
yield Usage(int(entry["input_tokens"]), int(entry["output_tokens"]))
```

- `yield Usage(int(entry["input_tokens"]), int(entry["output_tokens"]))`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
class RecordingStreamingModel:
```

- Defines the class `RecordingStreamingModel`.

```python
"""Wraps a model and writes every stream it returns to a cassette."""
```

- The docstring (documentation kept with the code) says: *Wraps a model and writes every stream it returns to a cassette.*

```python
def __init__(self, inner: StreamingModel, path: Path, model_id: str, provenance: str) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `inner`, type `StreamingModel`.
  - `path`, type `Path`.
  - `model_id`, type `str`.
  - `provenance`, type `str`.
- Gives back a value of type `None`.

```python
self._inner = inner
self._path = path
self._model_id = model_id
self._provenance = provenance
self._entries: dict[str, dict[str, Any]] = {}
```

- `self._inner = inner`: stores the value of `inner` in `self._inner`.
- `self._path = path`: stores the value of `path` in `self._path`.
- `self._model_id = model_id`: stores the value of `model_id` in `self._model_id`.
- `self._provenance = provenance`: stores the value of `provenance` in `self._provenance`.
- `self._entries: dict[str, dict[str, Any]] = {}`: stores a new dict (empty) in `self._entries`, whose type is declared as `dict[str, dict[str, Any]]`.

```python
async def stream(self, request: StreamRequest) -> AsyncIterator[Chunk]:
```

- Defines the async method `stream` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `request`, type `StreamRequest`.
- Gives back a value of type `AsyncIterator[Chunk]`.

```python
"""Pass the stream through, remember it and rewrite the cassette when it ends."""
```

- The docstring (documentation kept with the code) says: *Pass the stream through, remember it and rewrite the cassette when it ends.*

```python
pieces: list[str] = []
usage = Usage(0, 0)
```

- `pieces: list[str] = []`: stores a new list (empty) in `pieces`, whose type is declared as `list[str]`.
- `usage = Usage(0, 0)`: stores the result of calling `Usage(0, 0)`, which is this repository's own `Usage` (in `src/streaming_assistant/application/ports.py`): token counts, sent when the stream ends normally in `usage`.

```python
async for chunk in self._inner.stream(request):
```

- Repeats the indented lines once for each item of `self._inner.stream(request)`, naming the current item `chunk`. (`async for` waits for each item.)

```python
if isinstance(chunk, TextDelta):
```

- Checks whether `isinstance(chunk, TextDelta)` is true (the call asks whether `chunk` is a `TextDelta`). If so, the indented lines run.

```python
pieces.append(chunk.text)
```

- `pieces.append(chunk.text)`: calling `pieces.append(chunk.text)`, which adds `chunk.text` to the end of `pieces`.

```python
else:
```

- Runs when none of the conditions above held.

```python
usage = chunk
```

- `usage = chunk`: stores the value of `chunk` in `usage`.

```python
yield chunk
```

- `yield chunk`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
self._entries[request_key(self._model_id, request)] = {
    "pieces": pieces,
    "input_tokens": usage.input_tokens,
    "output_tokens": usage.output_tokens,
}
document = {"provenance": self._provenance, "model": self._model_id, "entries": self._entries}
self._path.parent.mkdir(parents=True, exist_ok=True)
self._path.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")
```

- `self._entries[request_key(self._model_id, request)] = { "pieces": p...`: stores a new dict with 3 entries in the slot `self._entries[request_key(self._model_id, request)]`.
- `document = {"provenance": self._provenance, "model": self._model_id...`: stores a new dict with 3 entries in `document`.
- `self._path.parent.mkdir(parents=True, exist_ok=True)`: calling `self._path.parent.mkdir(parents=True, exist_ok=True)`, which creates the folder `self._path.parent` The named values are `parents`, `exist_ok`..
- `self._path.write_text(json.dumps(document, indent=1, sort_keys=True...`: calling `self._path.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="...`, which writes text to the file `self._path`, replacing it The named values are `encoding`..

#### `src/streaming_assistant/infrastructure/retry.py`

```python
"""Retry with exponential backoff and full jitter for calls that cross the network."""
```

- The docstring (documentation kept with the code) says: *Retry with exponential backoff and full jitter for calls that cross the network.*

```python
from __future__ import annotations

import random
import time
from collections.abc import Callable
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import random`: makes the module `random` available (random numbers (a seeded generator gives the same numbers every run)).
- `import time`: makes the module `time` available (clocks and sleeping).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Callable`: the type hint for a function value.)

```python
def retry[T](
    operation: Callable[[], T],
    *,
    attempts: int,
    base_delay_seconds: float,
    retry_on: tuple[type[BaseException], ...],
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    max_delay_seconds: float = 10.0,
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> T:
```

- Defines the function `retry`.
- Parameters:
  - `operation`, type `Callable[[], T]`.
  - `attempts`, type `int`. Must be passed by name.
  - `base_delay_seconds`, type `float`. Must be passed by name.
  - `retry_on`, type `tuple[type[BaseException], ...]`. Must be passed by name.
  - `sleep`, type `Callable[[float], None]`, optional (default `time.sleep`). Must be passed by name.
  - `rng`, type `random.Random | None`, optional (default `None`). Must be passed by name.
  - `max_delay_seconds`, type `float`, optional (default `10.0`). Must be passed by name.
  - `on_retry`, type `Callable[[int, BaseException], None] | None`, optional (default `None`). Must be passed by name.
- Gives back a value of type `T`.

```python
"""Call `operation` up to `attempts` times, backing off after each failure in `retry_on`.

The pause after attempt n is a random value in [0, min(max_delay, base * 2**(n - 1))] (full jitter),
so many clients do not retry in step. The last failure is raised.
"""
```

- The docstring (documentation kept with the code) says: *Call `operation` up to `attempts` times, backing off after each failure in `retry_on`. The pause after attempt n is a random value in [0, min(max_delay, base * 2**(n - 1))] (full jitter), so many clients do not retry in step. The last failure is raised.*

```python
if attempts < 1:
```

- Checks whether `attempts` is less than `1`. If so, the indented lines run.

```python
raise ValueError("attempts must be at least 1")
```

- `raise ValueError("attempts must be at least 1")`: stops with an error of kind `ValueError` with the message `"attempts must be at least 1"`. Whoever called this code must handle it or the program stops.

```python
jitter = rng or random.Random()
```

- `jitter = rng or random.Random()`: stores `rng or random.Random()` (the first operand that decides the or) in `jitter`.

```python
for attempt in range(1, attempts + 1):
```

- Repeats the indented lines once for each item of `range(1, attempts + 1)`, naming the current item `attempt`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
return operation()
```

- `return operation()`: ends the function and gives back the result of calling `operation()`.

```python
except retry_on as error:
```

- If an error of kind `retry_on` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
if attempt == attempts:
```

- Checks whether `attempt` equals `attempts`. If so, the indented lines run.

```python
raise
```

- `raise`: raises the error again.

```python
if on_retry:
```

- Checks whether `on_retry` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
on_retry(attempt, error)
```

- `on_retry(attempt, error)`: calling `on_retry(attempt, error)`.

```python
sleep(jitter.uniform(0, min(max_delay_seconds, base_delay_seconds * 2 ** (attempt - 1))))
```

- `sleep(jitter.uniform(0, min(max_delay_seconds, base_delay_seconds *...`: calling `sleep(jitter.uniform(0, min(max_delay_seconds, base_delay_seconds * 2 ** (attempt - 1))))`, which waits `jitter.uniform(0, min(max_delay_seconds, base_delay_seconds * 2 ** (attempt - 1)))` seconds.

```python
raise AssertionError("unreachable")  # pragma: no cover
```

- `raise AssertionError("unreachable")`: stops with an error of kind `AssertionError` with the message `"unreachable"`. Whoever called this code must handle it or the program stops.

#### `src/streaming_assistant/infrastructure/scripted_stream.py`

```python
"""A scripted streaming model: configurable time to first token, prefill cost, token pace and failure, with counters.

It writes its answer from the passages in the prompt (the first sentence of the best passage, with its citation), so a run
has real text and real citations. Its latencies are settings, not measurements of any provider. It is not a model.
"""
```

- The docstring (documentation kept with the code) says: *A scripted streaming model: configurable time to first token, prefill cost, token pace and failure, with counters. It writes its answer from the passages in the prompt (the first sentence of the best passage, with its citation), so a run has real text and real citations. Its latencies are settings, not measurements of any provider. It is not a model.*

```python
from __future__ import annotations

import asyncio
import hashlib
import math
import re
import time
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import asyncio`: makes the module `asyncio` available (the standard library's tools for asynchronous code (many waits interleaved on one thread)).
- `import hashlib`: makes the module `hashlib` available (hash functions such as SHA-256).
- `import math`: makes the module `math` available (mathematical functions).
- `import re`: makes the module `re` available (regular expressions: patterns that match text).
- `import time`: makes the module `time` available (clocks and sleeping).

```python
from collections.abc import AsyncIterator
from dataclasses import dataclass

from streaming_assistant.application.ports import Chunk, StreamRequest, TextDelta, Usage
from streaming_assistant.domain.errors import ProviderError, RateLimitedError, RefusedError

_PASSAGE = re.compile(r"^\[(help-\d+#[a-z0-9-]+)\] [^:]+: (.+)$", re.MULTILINE)
_REVIEWER = re.compile(r"Reviewer-validated answer: (.+)", re.DOTALL)
```

- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`AsyncIterator`: a name provided by that module.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)
- `from streaming_assistant.application.ports import ...`: takes names from `streaming_assistant.application.ports`, this repository's own code. (`Chunk`: a name defined in this repository.) (`StreamRequest`: One streamed completion.) (`TextDelta`: A piece of the answer.) (`Usage`: Token counts, sent when the stream ends normally.)
- `from streaming_assistant.domain.errors import ...`: takes names from `streaming_assistant.domain.errors`, this repository's own code. (`ProviderError`: The model provider failed (a server error or a dropped connection).) (`RateLimitedError`: The model provider answered 429.) (`RefusedError`: The model declined to answer.)
- `_PASSAGE = re.compile(r"^\[(help-\d+#[a-z0-9-]+)\] [^:]+: (.+)$", r...`: stores the result of calling `re.compile(r"^\[(help-\d+#[a-z0-9-]+)\] [^:]+: (.+)$", re.MULTILINE)`, which compiles the pattern `r"^\[(help-\d+#[a-z0-9-]+)\] [^:]+: (.+)$"` so it can be matched many times in `_PASSAGE`.
- `_REVIEWER = re.compile(r"Reviewer-validated answer: (.+)", re.DOTALL)`: stores the result of calling `re.compile(r"Reviewer-validated answer: (.+)", re.DOTALL)`, which compiles the pattern `r"Reviewer-validated answer: (.+)"` so it can be matched many times in `_REVIEWER`.

```python
@dataclass(frozen=True, slots=True)
class Pace:
```

- Defines the class `Pace`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""Latency settings in milliseconds."""
```

- The docstring (documentation kept with the code) says: *Latency settings in milliseconds.*

```python
ttft_standard_ms: float = 1300.0
ttft_fast_ms: float = 350.0
prefill_ms_per_1k_tokens: float = 400.0
token_ms: float = 15.0
cached_prefix_chars: int = 400
jitter: float = 0.15
```

- `ttft_standard_ms: float = 1300.0`: a field named `ttft_standard_ms` of type `float`, default `1300.0`.
- `ttft_fast_ms: float = 350.0`: a field named `ttft_fast_ms` of type `float`, default `350.0`.
- `prefill_ms_per_1k_tokens: float = 400.0`: a field named `prefill_ms_per_1k_tokens` of type `float`, default `400.0`.
- `token_ms: float = 15.0`: a field named `token_ms` of type `float`, default `15.0`.
- `cached_prefix_chars: int = 400`: a field named `cached_prefix_chars` of type `int`, default `400`.
- `jitter: float = 0.15`: a field named `jitter` of type `float`, default `0.15`.

```python
class ScriptedStreamingModel:
```

- Defines the class `ScriptedStreamingModel`.

```python
"""Async streaming with counters: tokens produced (what would be billed), cancellations and their times."""
```

- The docstring (documentation kept with the code) says: *Async streaming with counters: tokens produced (what would be billed), cancellations and their times.*

```python
name = "scripted-streaming-model"
```

- `name = "scripted-streaming-model"`: a class-level value `name` shared by all objects of the class: the text `'scripted-streaming-model'`.

```python
def __init__(self, pace: Pace | None = None, mode: str = "ok", hallucinate_every: int = 25) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `pace`, type `Pace | None`, optional (default `None`).
  - `mode`, type `str`, optional (default `"ok"`).
  - `hallucinate_every`, type `int`, optional (default `25`).
- Gives back a value of type `None`.

```python
self._pace = pace or Pace()
self._mode = mode
self._hallucinate_every = hallucinate_every
self._cached_prefixes: set[str] = set()
self.produced_tokens = 0
self.cancelled_at: list[float] = []
```

- `self._pace = pace or Pace()`: stores `pace or Pace()` (the first operand that decides the or) in `self._pace`.
- `self._mode = mode`: stores the value of `mode` in `self._mode`.
- `self._hallucinate_every = hallucinate_every`: stores the value of `hallucinate_every` in `self._hallucinate_every`.
- `self._cached_prefixes: set[str] = set()`: stores the result of calling `set()`, which sets  in `self._cached_prefixes`, whose type is declared as `set[str]`.
- `self.produced_tokens = 0`: stores the number `0` in `self.produced_tokens`.
- `self.cancelled_at: list[float] = []`: stores a new list (empty) in `self.cancelled_at`, whose type is declared as `list[float]`.

```python
self.started = 0
self.prefix_cache_hits = 0
```

- `self.started = 0`: stores the number `0` in `self.started`.
- `self.prefix_cache_hits = 0`: stores the number `0` in `self.prefix_cache_hits`.

```python
def _ttft(self, request: StreamRequest) -> float:
```

- Defines the method `_ttft`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `request`, type `StreamRequest`.
- Gives back a value of type `float`.

```python
prefix = hashlib.sha1(request.system[: self._pace.cached_prefix_chars].encode()).hexdigest()
cached = prefix in self._cached_prefixes
self._cached_prefixes.add(prefix)
```

- `prefix = hashlib.sha1(request.system[: self._pace.cached_prefix_cha...`: stores the result of calling `hashlib.sha1(request.system[: self._pace.cached_prefix_chars].encode()).hexdigest()`, which writes the hash as hexadecimal text in `prefix`.
- `cached = prefix in self._cached_prefixes`: stores whether `prefix` is among `self._cached_prefixes` in `cached`.
- `self._cached_prefixes.add(prefix)`: calling `self._cached_prefixes.add(prefix)`, which puts `prefix` into the set `self._cached_prefixes`.

```python
if cached:
```

- Checks whether `cached` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
self.prefix_cache_hits += 1
```

- `self.prefix_cache_hits += 1`: adds `1` to `self.prefix_cache_hits` and keeps the result there.

```python
prompt_tokens = len(request.system + request.user) / 4
uncached = (len(request.user) / 4) if cached else prompt_tokens
base = self._pace.ttft_fast_ms if request.tier == "fast" else self._pace.ttft_standard_ms
spread = (int(hashlib.sha1(request.user.encode()).hexdigest(), 16) % 1000) / 1000 * 2 - 1
return (base + self._pace.prefill_ms_per_1k_tokens * uncached / 1000) * (1 + self._pace.jitter * spread)
```

- `prompt_tokens = len(request.system + request.user) / 4`: stores `len(request.system + request.user) / 4`, which divides `len(request.system + request.user)` and `4` in `prompt_tokens`.
- `uncached = (len(request.user) / 4) if cached else prompt_tokens`: stores `len(request.user) / 4` when `cached` is truthy (not `None`, `False`, zero or empty), otherwise `prompt_tokens` in `uncached`.
- `base = self._pace.ttft_fast_ms if request.tier == "fast" else self....`: stores `self._pace.ttft_fast_ms` when `request.tier` equals `"fast"`, otherwise `self._pace.ttft_standard_ms` in `base`.
- `spread = (int(hashlib.sha1(request.user.encode()).hexdigest(), 16) ...`: stores `(int(hashlib.sha1(request.user.encode()).hexdigest(), 16) % 1000) / 1000 * 2 - 1`, which subtracts `(int(hashlib.sha1(request.user.encode()).hexdigest(), 16) % 1000) / 1000 * 2` and `1` in `spread`.
- `return (base + self._pace.prefill_ms_per_1k_tokens * uncached / 100...`: ends the function and gives back `(base + self._pace.prefill_ms_per_1k_tokens * uncached / 1000) * (1 + self._pace.jitter...`, which multiplies `base + self._pace.prefill_ms_per_1k_tokens * uncached / 1000` and `1 + self._pace.jitter * spread`.

```python
def _answer(self, request: StreamRequest) -> str:
```

- Defines the method `_answer`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `request`, type `StreamRequest`.
- Gives back a value of type `str`.

```python
reviewer = _REVIEWER.search(request.user)
passages = _PASSAGE.findall(request.user)
```

- `reviewer = _REVIEWER.search(request.user)`: stores the result of calling `_REVIEWER.search(request.user)`, which looks for the pattern anywhere in the text in `reviewer`.
- `passages = _PASSAGE.findall(request.user)`: stores the result of calling `_PASSAGE.findall(request.user)`, which lists every match of the pattern in `passages`.

```python
if reviewer:
```

- Checks whether `reviewer` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
refs = " ".join(f"[{ref}]" for ref, _ in passages[:1])
return f"{reviewer.group(1).strip()} {refs}".strip()
```

- `refs = " ".join(f"[{ref}]" for ref, _ in passages[:1])`: stores the result of calling `" ".join(f"[{ref}]" for ref, _ in passages[:1])`, which glues the items of `(f"[{ref}]" for ref, _ in passages[:1])` together with `" "` between them in `refs`.
- `return f"{reviewer.group(1).strip()} {refs}".strip()`: ends the function and gives back the result of calling `f"{reviewer.group(1).strip()} {refs}".strip()`, which removes spaces and line breaks from both ends of `f"{reviewer.group(1).strip()} {refs}"` (or the characters its argument).

```python
if not passages:
```

- Checks whether it is not the case that `passages` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
return "I do not have a passage for that."
```

- `return "I do not have a passage for that."`: ends the function and gives back the text `'I do not have a passage for that.'`.

```python
ref, text = passages[0]
sentence = text.split(". ")[0].rstrip(".") + "."
answer = f"{sentence} [{ref}]"
```

- `ref, text = passages[0]`: unpacks the item `passages[0]` into the names `ref`, `text`, one item each.
- `sentence = text.split(". ")[0].rstrip(".") + "."`: stores `text.split(". ")[0].rstrip(".") + "."`, which adds `text.split(". ")[0].rstrip(".")` and `"."` in `sentence`.
- `answer = f"{sentence} [{ref}]"`: stores the text built by the f-string `f"{sentence} [{ref}]"` in `answer`.

```python
if (
    self._hallucinate_every
    and int(hashlib.sha1(request.user.encode()).hexdigest(), 16) % self._hallucinate_every == 0
):
```

- Checks whether `self._hallucinate_every` is truthy and `int(hashlib.sha1(request.user.encode()).hexdigest(), 16) % self._hallucinate_every` equals `0`. If so, the indented lines run.

```python
answer += " See also [help-99#made-up]."
```

- `answer += " See also [help-99#made-up]."`: adds `" See also [help-99#made-up]."` to `answer` and keeps the result there.

```python
return answer
```

- `return answer`: ends the function and gives back the value of `answer`.

```python
async def stream(self, request: StreamRequest) -> AsyncIterator[Chunk]:
```

- Defines the async method `stream` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `request`, type `StreamRequest`.
- Gives back a value of type `AsyncIterator[Chunk]`.

```python
"""Wait for the first token, then emit the answer a word at a time."""
```

- The docstring (documentation kept with the code) says: *Wait for the first token, then emit the answer a word at a time.*

```python
self.started += 1
```

- `self.started += 1`: adds `1` to `self.started` and keeps the result there.

```python
if self._mode == "provider_error":
```

- Checks whether `self._mode` equals `"provider_error"`. If so, the indented lines run.

```python
raise ProviderError("scripted provider failure")
```

- `raise ProviderError("scripted provider failure")`: stops with an error of kind `ProviderError` with the message `"scripted provider failure"`. Whoever called this code must handle it or the program stops.

```python
if self._mode == "rate_limited":
```

- Checks whether `self._mode` equals `"rate_limited"`. If so, the indented lines run.

```python
raise RateLimitedError("scripted 429")
```

- `raise RateLimitedError("scripted 429")`: stops with an error of kind `RateLimitedError` with the message `"scripted 429"`. Whoever called this code must handle it or the program stops.

```python
if self._mode == "refusal":
```

- Checks whether `self._mode` equals `"refusal"`. If so, the indented lines run.

```python
raise RefusedError("scripted refusal")
```

- `raise RefusedError("scripted refusal")`: stops with an error of kind `RefusedError` with the message `"scripted refusal"`. Whoever called this code must handle it or the program stops.

```python
produced = 0
```

- `produced = 0`: stores the number `0` in `produced`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
if self._mode == "timeout":
```

- Checks whether `self._mode` equals `"timeout"`. If so, the indented lines run.

```python
await asyncio.sleep(3600)
```

- `await asyncio.sleep(3600)`: waits for the result of calling `asyncio.sleep(3600)`, which waits `3600` seconds to finish.

```python
await asyncio.sleep(self._ttft(request) / 1000)
words = self._answer(request).split(" ")
```

- `await asyncio.sleep(self._ttft(request) / 1000)`: waits for the result of calling `asyncio.sleep(self._ttft(request) / 1000)`, which waits `self._ttft(request) / 1000` seconds to finish.
- `words = self._answer(request).split(" ")`: stores the result of calling `self._answer(request).split(" ")`, which cuts `self._answer(request)` into pieces at `" "` (whitespace if nothing is given) in `words`.

```python
for index, word in enumerate(words):
```

- Repeats the indented lines once for each item of `enumerate(words)`, naming the current item the names `index`, `word`.

```python
if index:
```

- Checks whether `index` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
await asyncio.sleep(self._pace.token_ms / 1000)
```

- `await asyncio.sleep(self._pace.token_ms / 1000)`: waits for the result of calling `asyncio.sleep(self._pace.token_ms / 1000)`, which waits `self._pace.token_ms / 1000` seconds to finish.

```python
self.produced_tokens += 1
produced += 1
yield TextDelta(word + (" " if index < len(words) - 1 else ""))
```

- `self.produced_tokens += 1`: adds `1` to `self.produced_tokens` and keeps the result there.
- `produced += 1`: adds `1` to `produced` and keeps the result there.
- `yield TextDelta(word + (" " if index < len(words) - 1 else ""))`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
yield Usage(math.ceil(len(request.system + request.user) / 4), produced)
```

- `yield Usage(math.ceil(len(request.system + request.user) / 4), prod...`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
except (asyncio.CancelledError, GeneratorExit):
```

- If an error of kind `(asyncio.CancelledError, GeneratorExit)` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
self.cancelled_at.append(time.perf_counter())
raise
```

- `self.cancelled_at.append(time.perf_counter())`: calling `self.cancelled_at.append(time.perf_counter())`, which adds `time.perf_counter()` to the end of `self.cancelled_at`.
- `raise`: raises the error again.

#### `src/streaming_assistant/infrastructure/settings.py`

```python
"""Configuration from the environment, validated once at startup (twelve-factor). Secrets only from here."""
```

- The docstring (documentation kept with the code) says: *Configuration from the environment, validated once at startup (twelve-factor). Secrets only from here.*

```python
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
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Mapping`: the type hint for a read-only dict-like collection.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from streaming_assistant.infrastructure.environment import ...`: takes names from `streaming_assistant.infrastructure.environment`, this repository's own code. (`read_choice`: A string variable restricted to `choices`.) (`read_float`: A float variable of at least `minimum`.) (`read_int`: An integer variable of at least `minimum`.) (`read_optional`: A string variable that may be absent or empty (for example an API key).) (`read_text`: A non-empty string variable, or `default`.)

```python
def _flag(environ: Mapping[str, str], name: str, default: bool) -> bool:
```

- Defines the function `_flag`.
- Parameters:
  - `environ`, type `Mapping[str, str]`.
  - `name`, type `str`.
  - `default`, type `bool`.
- Gives back a value of type `bool`.

```python
return read_choice(environ, name, "on" if default else "off", frozenset({"on", "off"})) == "on"
```

- `return read_choice(environ, name, "on" if default else "off", froze...`: ends the function and gives back whether `read_choice(environ, name, "on" if default else "off", frozenset({"on", "off"}))` equals `"on"`.

```python
@dataclass(frozen=True, slots=True)
class Settings:
```

- Defines the class `Settings`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""Everything the programs read from the environment."""
```

- The docstring (documentation kept with the code) says: *Everything the programs read from the environment.*

```python
log_level: str
root: Path
database: str
model_adapter: str
model_ids: dict[str, str]
anthropic_api_key: str | None
cassette: Path
host: str
```

- `log_level: str`: a field named `log_level` of type `str`, no default (must be given).
- `root: Path`: a field named `root` of type `Path`, no default (must be given).
- `database: str`: a field named `database` of type `str`, no default (must be given).
- `model_adapter: str`: a field named `model_adapter` of type `str`, no default (must be given).
- `model_ids: dict[str, str]`: a field named `model_ids` of type `dict[str, str]`, no default (must be given).
- `anthropic_api_key: str | None`: a field named `anthropic_api_key` of type `str | None`, no default (must be given).
- `cassette: Path`: a field named `cassette` of type `Path`, no default (must be given).
- `host: str`: a field named `host` of type `str`, no default (must be given).

```python
port: int
first_token_timeout_seconds: float
idle_timeout_seconds: float
pause_enabled: bool
stable_prefix_first: bool
parallel_prep: bool
cache_retrieval: bool
route_easy_to_fast: bool
```

- `port: int`: a field named `port` of type `int`, no default (must be given).
- `first_token_timeout_seconds: float`: a field named `first_token_timeout_seconds` of type `float`, no default (must be given).
- `idle_timeout_seconds: float`: a field named `idle_timeout_seconds` of type `float`, no default (must be given).
- `pause_enabled: bool`: a field named `pause_enabled` of type `bool`, no default (must be given).
- `stable_prefix_first: bool`: a field named `stable_prefix_first` of type `bool`, no default (must be given).
- `parallel_prep: bool`: a field named `parallel_prep` of type `bool`, no default (must be given).
- `cache_retrieval: bool`: a field named `cache_retrieval` of type `bool`, no default (must be given).
- `route_easy_to_fast: bool`: a field named `route_easy_to_fast` of type `bool`, no default (must be given).

```python
warm_index: bool
ttft_standard_ms: float
ttft_fast_ms: float
token_ms: float
first_token_budget_ms: float
```

- `warm_index: bool`: a field named `warm_index` of type `bool`, no default (must be given).
- `ttft_standard_ms: float`: a field named `ttft_standard_ms` of type `float`, no default (must be given).
- `ttft_fast_ms: float`: a field named `ttft_fast_ms` of type `float`, no default (must be given).
- `token_ms: float`: a field named `token_ms` of type `float`, no default (must be given).
- `first_token_budget_ms: float`: a field named `first_token_budget_ms` of type `float`, no default (must be given).

```python
@classmethod
def from_environ(cls, environ: Mapping[str, str]) -> Settings:
```

- Defines the method `from_environ`.
- `@classmethod`: a method that receives the class itself as `cls`.
- Parameters:
  - `cls`: the object (or class) the method was called on.
  - `environ`, type `Mapping[str, str]`.
- Gives back a value of type `Settings`.

```python
"""Read and validate; raises `ConfigurationError` naming the first bad variable."""
```

- The docstring (documentation kept with the code) says: *Read and validate; raises `ConfigurationError` naming the first bad variable.*

```python
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
```

- `return cls( log_level=read_choice(environ, "LOG_LEVEL", "INFO", fro...`: ends the function and gives back the result of calling `cls( log_level=read_choice(environ, "LOG_LEVEL", "INFO", frozenset({"DEBUG", "INFO", "W...` The named values are `log_level`, `root`, `database`, `model_adapter`, `model_ids`, `anthropic_api_key`, `cassette`, `host`, `port`, `first_token_timeout_seconds`, `idle_timeout_seconds`, `pause_enabled`, `stable_prefix_first`, `parallel_prep`, `cache_retrieval`, `route_easy_to_fast`, `warm_index`, `ttft_standard_ms`, `ttft_fast_ms`, `token_ms`, `first_token_budget_ms`..

#### `src/streaming_assistant/infrastructure/shutdown.py`

```python
"""Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work."""
```

- The docstring (documentation kept with the code) says: *Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work.*

```python
from __future__ import annotations

import signal
import threading
from types import FrameType
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import signal`: makes the module `signal` available (operating-system signals such as SIGTERM).
- `import threading`: makes the module `threading` available (threads, locks and events).
- `from types import ...`: takes names from `types` (names for built-in types such as a module or a function). (`FrameType`: a name provided by that module.)

```python
class ShutdownSignal:
```

- Defines the class `ShutdownSignal`.

```python
"""A flag that SIGINT and SIGTERM set, which work loops check between units of work."""
```

- The docstring (documentation kept with the code) says: *A flag that SIGINT and SIGTERM set, which work loops check between units of work.*

```python
def __init__(self) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `None`.

```python
self._requested = threading.Event()
```

- `self._requested = threading.Event()`: stores the result of calling `threading.Event()`, which is this repository's own `Event` (in `src/streaming_assistant/application/assistant.py`): one server-sent event: a type name and its data in `self._requested`.

```python
def install(self) -> None:
```

- Defines the method `install`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `None`.

```python
"""Route SIGINT and SIGTERM to `request`, so in-flight work finishes and connections close."""
```

- The docstring (documentation kept with the code) says: *Route SIGINT and SIGTERM to `request`, so in-flight work finishes and connections close.*

```python
for number in (signal.SIGINT, signal.SIGTERM):
```

- Repeats the indented lines once for each item of `(signal.SIGINT, signal.SIGTERM)`, naming the current item `number`.

```python
signal.signal(number, self._handle)
```

- `signal.signal(number, self._handle)`: calling `signal.signal(number, self._handle)`, which installs a handler for an operating-system signal.

```python
def _handle(self, _number: int, _frame: FrameType | None) -> None:
```

- Defines the method `_handle`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `_number`, type `int`.
  - `_frame`, type `FrameType | None`.
- Gives back a value of type `None`.

```python
self.request()
```

- `self.request()`: calling `self.request()`.

```python
def request(self) -> None:
```

- Defines the method `request`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `None`.

```python
"""Ask the loops to stop after the unit of work in flight."""
```

- The docstring (documentation kept with the code) says: *Ask the loops to stop after the unit of work in flight.*

```python
self._requested.set()
```

- `self._requested.set()`: calling `self._requested.set()`, which sets `self._requested`.

```python
@property
def requested(self) -> bool:
```

- Defines the method `requested`.
- `@property`: the method is read like an attribute.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `bool`.

```python
"""True once a stop was requested."""
```

- The docstring (documentation kept with the code) says: *True once a stop was requested.*

```python
return self._requested.is_set()
```

- `return self._requested.is_set()`: ends the function and gives back the result of calling `self._requested.is_set()`, which asks whether the event `self._requested` is set.

```python
def wait(self, seconds: float) -> bool:
```

- Defines the method `wait`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `seconds`, type `float`.
- Gives back a value of type `bool`.

```python
"""Sleep up to `seconds`, waking early on a stop request; returns True when a stop was requested."""
```

- The docstring (documentation kept with the code) says: *Sleep up to `seconds`, waking early on a stop request; returns True when a stop was requested.*

```python
return self._requested.wait(seconds)
```

- `return self._requested.wait(seconds)`: ends the function and gives back the result of calling `self._requested.wait(seconds)`, which is this repository's own `wait` (in `src/streaming_assistant/infrastructure/shutdown.py`): sleep up to `seconds`, waking early on a stop request; returns True when a stop was requested.

#### `src/streaming_assistant/infrastructure/sqlite_store.py`

```python
"""SQLite adapters: API tokens, paused runs (durable across a restart) and the hash-chained audit log."""
```

- The docstring (documentation kept with the code) says: *SQLite adapters: API tokens, paused runs (durable across a restart) and the hash-chained audit log.*

```python
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from collections.abc import Sequence
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import hashlib`: makes the module `hashlib` available (hash functions such as SHA-256).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import sqlite3`: makes the module `sqlite3` available (the standard library's SQLite database driver).
- `import threading`: makes the module `threading` available (threads, locks and events).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Sequence`: the type hint for an ordered, indexable collection.)

```python
from datetime import datetime
from pathlib import Path

from streaming_assistant.application.ports import PausedRun
from streaming_assistant.domain.audit import AuditEntry, make_entry
from streaming_assistant.infrastructure.clock import SystemClock

SCRIPTS = ("001_schema.sql", "002_seed.sql")
```

- `from datetime import ...`: takes names from `datetime` (dates, times and time spans). (`datetime`: the date-and-time type.)
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from streaming_assistant.application.ports import ...`: takes names from `streaming_assistant.application.ports`, this repository's own code. (`PausedRun`: A run waiting for, or past, a reviewer.)
- `from streaming_assistant.domain.audit import ...`: takes names from `streaming_assistant.domain.audit`, this repository's own code. (`AuditEntry`: One step of a run, with its place in the chain.) (`make_entry`: The next entry in the chain.)
- `from streaming_assistant.infrastructure.clock import ...`: takes names from `streaming_assistant.infrastructure.clock`, this repository's own code. (`SystemClock`: Now, in UTC.)
- `SCRIPTS = ("001_schema.sql", "002_seed.sql")`: stores a tuple of 2 items in `SCRIPTS`.

```python
class Database:
```

- Defines the class `Database`.

```python
"""One SQLite file behind a lock; every operation is a short transaction."""
```

- The docstring (documentation kept with the code) says: *One SQLite file behind a lock; every operation is a short transaction.*

```python
def __init__(self, path: Path | str) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `path`, type `Path | str`.
- Gives back a value of type `None`.

```python
if str(path) != ":memory:":
```

- Checks whether `str(path)` is different from `":memory:"`. If so, the indented lines run.

```python
Path(path).parent.mkdir(parents=True, exist_ok=True)
```

- `Path(path).parent.mkdir(parents=True, exist_ok=True)`: calling `Path(path).parent.mkdir(parents=True, exist_ok=True)`, which creates the folder `Path(path).parent` The named values are `parents`, `exist_ok`..

```python
self._connection = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
self.lock = threading.RLock()
```

- `self._connection = sqlite3.connect(path, check_same_thread=False, i...`: stores the result of calling `sqlite3.connect(path, check_same_thread=False, isolation_level=None)`, which opens a connection The named values are `check_same_thread`, `isolation_level`. in `self._connection`.
- `self.lock = threading.RLock()`: stores the result of calling `threading.RLock()`, which makes a `RLock` object in `self.lock`.

```python
def apply_scripts(self, sql_dir: Path) -> list[str]:
```

- Defines the method `apply_scripts`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `sql_dir`, type `Path`.
- Gives back a value of type `list[str]`.

```python
"""Run the numbered scripts (DDL, then seed); returns the names that ran."""
```

- The docstring (documentation kept with the code) says: *Run the numbered scripts (DDL, then seed); returns the names that ran.*

```python
with self.lock:
```

- Opens `self.lock` for the indented lines, and releases it when they end (even after an error).

```python
for table in ("audit_log", "paused_runs", "api_tokens"):
```

- Repeats the indented lines once for each item of `("audit_log", "paused_runs", "api_tokens")`, naming the current item `table`.

```python
self._connection.execute(f"DROP TABLE IF EXISTS {table}")
```

- `self._connection.execute(f"DROP TABLE IF EXISTS {table}")`: calling `self._connection.execute(f"DROP TABLE IF EXISTS {table}")`, which is this repository's own `execute` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run one statement in a transaction and return its rows.

```python
for name in SCRIPTS:
```

- Repeats the indented lines once for each item of `SCRIPTS`, naming the current item `name`.

```python
self._connection.executescript((sql_dir / name).read_text(encoding="utf-8"))
```

- `self._connection.executescript((sql_dir / name).read_text(encoding=...`: calling `self._connection.executescript((sql_dir / name).read_text(encoding="utf-8"))`, which runs several SQL statements written as one text.

```python
return list(SCRIPTS)
```

- `return list(SCRIPTS)`: ends the function and gives back the result of calling `list(SCRIPTS)`, which builds a new list from `SCRIPTS`.

```python
def execute(self, sql: str, parameters: Sequence[object] = ()) -> list[tuple[object, ...]]:
```

- Defines the method `execute`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `sql`, type `str`.
  - `parameters`, type `Sequence[object]`, optional (default `()`).
- Gives back a value of type `list[tuple[object, ...]]`.

```python
"""Run one statement in a transaction and return its rows."""
```

- The docstring (documentation kept with the code) says: *Run one statement in a transaction and return its rows.*

```python
with self.lock:
```

- Opens `self.lock` for the indented lines, and releases it when they end (even after an error).

```python
self._connection.execute("BEGIN IMMEDIATE")
```

- `self._connection.execute("BEGIN IMMEDIATE")`: calling `self._connection.execute("BEGIN IMMEDIATE")`, which is this repository's own `execute` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run one statement in a transaction and return its rows.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
rows = self._connection.execute(sql, tuple(parameters)).fetchall()
```

- `rows = self._connection.execute(sql, tuple(parameters)).fetchall()`: stores the result of calling `self._connection.execute(sql, tuple(parameters)).fetchall()`, which takes all remaining rows of the result in `rows`.

```python
except BaseException:
```

- If an error of kind `BaseException` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
self._connection.execute("ROLLBACK")
raise
```

- `self._connection.execute("ROLLBACK")`: calling `self._connection.execute("ROLLBACK")`, which is this repository's own `execute` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run one statement in a transaction and return its rows.
- `raise`: raises the error again.

```python
self._connection.execute("COMMIT")
```

- `self._connection.execute("COMMIT")`: calling `self._connection.execute("COMMIT")`, which is this repository's own `execute` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run one statement in a transaction and return its rows.

```python
return rows
```

- `return rows`: ends the function and gives back the value of `rows`.

```python
def close(self) -> None:
```

- Defines the method `close`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `None`.

```python
"""Close the connection."""
```

- The docstring (documentation kept with the code) says: *Close the connection.*

```python
with self.lock:
```

- Opens `self.lock` for the indented lines, and releases it when they end (even after an error).

```python
self._connection.close()
```

- `self._connection.close()`: calling `self._connection.close()`, which is this repository's own `close` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): close the connection.

```python
def token_hash(token: str) -> str:
```

- Defines the function `token_hash`.
- Parameters:
  - `token`, type `str`.
- Gives back a value of type `str`.

```python
"""The stored form of a bearer token."""
```

- The docstring (documentation kept with the code) says: *The stored form of a bearer token.*

```python
return hashlib.sha256(token.encode()).hexdigest()
```

- `return hashlib.sha256(token.encode()).hexdigest()`: ends the function and gives back the result of calling `hashlib.sha256(token.encode()).hexdigest()`, which writes the hash as hexadecimal text.

```python
class SqliteAuthenticator:
```

- Defines the class `SqliteAuthenticator`.

```python
"""Looks a bearer token up by its hash."""
```

- The docstring (documentation kept with the code) says: *Looks a bearer token up by its hash.*

```python
def __init__(self, database: Database) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `database`, type `Database`.
- Gives back a value of type `None`.

```python
self._database = database
```

- `self._database = database`: stores the value of `database` in `self._database`.

```python
def role_of(self, token: str) -> str | None:
```

- Defines the method `role_of`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `token`, type `str`.
- Gives back a value of type `str | None`.

```python
"""'customer', 'reviewer' or None."""
```

- The docstring (documentation kept with the code) says: *'customer', 'reviewer' or None.*

```python
rows = self._database.execute("SELECT role FROM api_tokens WHERE token_hash = ?", (token_hash(token),))
return str(rows[0][0]) if rows else None
```

- `rows = self._database.execute("SELECT role FROM api_tokens WHERE to...`: stores the result of calling `self._database.execute("SELECT role FROM api_tokens WHERE token_hash = ?", (token_hash(...`, which is this repository's own `execute` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run one statement in a transaction and return its rows in `rows`.
- `return str(rows[0][0]) if rows else None`: ends the function and gives back `str(rows[0][0])` when `rows` is truthy (not `None`, `False`, zero or empty), otherwise `None`.

```python
class SqliteRunStore:
```

- Defines the class `SqliteRunStore`.

```python
"""Paused runs."""
```

- The docstring (documentation kept with the code) says: *Paused runs.*

```python
def __init__(self, database: Database) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `database`, type `Database`.
- Gives back a value of type `None`.

```python
self._database = database
```

- `self._database = database`: stores the value of `database` in `self._database`.

```python
def save_pause(self, run: PausedRun, at: datetime) -> None:
```

- Defines the method `save_pause`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run`, type `PausedRun`.
  - `at`, type `datetime`.
- Gives back a value of type `None`.

```python
"""Store a new paused run (waiting)."""
```

- The docstring (documentation kept with the code) says: *Store a new paused run (waiting).*

```python
self._database.execute(
    "INSERT OR REPLACE INTO paused_runs (run_id, question, retrieved, reason, status, created_at) VALUES (?, ?, ?, ?, 'waiting', ?)",
    (run.run_id, run.question, json.dumps(list(run.retrieved)), run.reason, at.isoformat()),
)
```

- `self._database.execute( "INSERT OR REPLACE INTO paused_runs (run_id...`: calling `self._database.execute( "INSERT OR REPLACE INTO paused_runs (run_id, question, retrieve...`, which is this repository's own `execute` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run one statement in a transaction and return its rows.

```python
def get(self, run_id: str) -> PausedRun | None:
```

- Defines the method `get`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run_id`, type `str`.
- Gives back a value of type `PausedRun | None`.

```python
"""One run, or None."""
```

- The docstring (documentation kept with the code) says: *One run, or None.*

```python
rows = self._database.execute(
    "SELECT run_id, question, retrieved, reason, status, reviewer_id, answer, cited, no_page FROM paused_runs WHERE run_id = ?",
    (run_id,),
)
return self._row(rows[0]) if rows else None
```

- `rows = self._database.execute( "SELECT run_id, question, retrieved,...`: stores the result of calling `self._database.execute( "SELECT run_id, question, retrieved, reason, status, reviewer_i...`, which is this repository's own `execute` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run one statement in a transaction and return its rows in `rows`.
- `return self._row(rows[0]) if rows else None`: ends the function and gives back `self._row(rows[0])` when `rows` is truthy (not `None`, `False`, zero or empty), otherwise `None`.

```python
def waiting(self, limit: int) -> Sequence[PausedRun]:
```

- Defines the method `waiting`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `limit`, type `int`.
- Gives back a value of type `Sequence[PausedRun]`.

```python
"""Runs waiting for a reviewer, oldest first."""
```

- The docstring (documentation kept with the code) says: *Runs waiting for a reviewer, oldest first.*

```python
rows = self._database.execute(
    "SELECT run_id, question, retrieved, reason, status, reviewer_id, answer, cited, no_page FROM paused_runs "
    "WHERE status = 'waiting' ORDER BY created_at, run_id LIMIT ?",
    (limit,),
)
return [self._row(row) for row in rows]
```

- `rows = self._database.execute( "SELECT run_id, question, retrieved,...`: stores the result of calling `self._database.execute( "SELECT run_id, question, retrieved, reason, status, reviewer_i...`, which is this repository's own `execute` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run one statement in a transaction and return its rows in `rows`.
- `return [self._row(row) for row in rows]`: ends the function and gives back a list built by running `self._row(row)` for each `row` in `rows`.

```python
def record_answer(
    self, run_id: str, reviewer_id: str, answer: str, cited: Sequence[str], no_page: bool, at: datetime
) -> None:
```

- Defines the method `record_answer`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run_id`, type `str`.
  - `reviewer_id`, type `str`.
  - `answer`, type `str`.
  - `cited`, type `Sequence[str]`.
  - `no_page`, type `bool`.
  - `at`, type `datetime`.
- Gives back a value of type `None`.

```python
"""Store a validated answer and move the run to `answered`."""
```

- The docstring (documentation kept with the code) says: *Store a validated answer and move the run to `answered`.*

```python
self._database.execute(
    "UPDATE paused_runs SET status = 'answered', reviewer_id = ?, answer = ?, cited = ?, no_page = ?, answered_at = ? "
    "WHERE run_id = ? AND status = 'waiting'",
    (reviewer_id, answer, json.dumps(list(cited)), int(no_page), at.isoformat(), run_id),
)
```

- `self._database.execute( "UPDATE paused_runs SET status = 'answered'...`: calling `self._database.execute( "UPDATE paused_runs SET status = 'answered', reviewer_id = ?, a...`, which is this repository's own `execute` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run one statement in a transaction and return its rows.

```python
def mark_resumed(self, run_id: str, at: datetime) -> None:
```

- Defines the method `mark_resumed`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run_id`, type `str`.
  - `at`, type `datetime`.
- Gives back a value of type `None`.

```python
"""Move the run to `resumed`."""
```

- The docstring (documentation kept with the code) says: *Move the run to `resumed`.*

```python
self._database.execute(
    "UPDATE paused_runs SET status = 'resumed', resumed_at = ? WHERE run_id = ?", (at.isoformat(), run_id)
)
```

- `self._database.execute( "UPDATE paused_runs SET status = 'resumed',...`: calling `self._database.execute( "UPDATE paused_runs SET status = 'resumed', resumed_at = ? WHER...`, which is this repository's own `execute` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run one statement in a transaction and return its rows.

```python
@staticmethod
def _row(row: tuple[object, ...]) -> PausedRun:
```

- Defines the method `_row`.
- `@staticmethod`: a method of the class that does not receive an object
- Parameters:
  - `row`, type `tuple[object, ...]`.
- Gives back a value of type `PausedRun`.

```python
return PausedRun(
    str(row[0]),
    str(row[1]),
    tuple(json.loads(str(row[2]))),
    str(row[3]),
    str(row[4]),
    None if row[5] is None else str(row[5]),
    None if row[6] is None else str(row[6]),
    tuple(json.loads(str(row[7]))),
    bool(row[8]),
)
```

- `return PausedRun( str(row[0]), str(row[1]), tuple(json.loads(str(ro...`: ends the function and gives back the result of calling `PausedRun( str(row[0]), str(row[1]), tuple(json.loads(str(row[2]))), str(row[3]), str(r...`, which is this repository's own `PausedRun` (in `src/streaming_assistant/application/ports.py`): a run waiting for, or past, a reviewer.

```python
class SqliteAudit:
```

- Defines the class `SqliteAudit`.

```python
"""The audit log. Appending reads the last hash and inserts in one transaction, so the chain has no fork."""
```

- The docstring (documentation kept with the code) says: *The audit log. Appending reads the last hash and inserts in one transaction, so the chain has no fork.*

```python
def __init__(self, database: Database, clock: SystemClock | None = None) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `database`, type `Database`.
  - `clock`, type `SystemClock | None`, optional (default `None`).
- Gives back a value of type `None`.

```python
self._database = database
self._clock = clock or SystemClock()
```

- `self._database = database`: stores the value of `database` in `self._database`.
- `self._clock = clock or SystemClock()`: stores `clock or SystemClock()` (the first operand that decides the or) in `self._clock`.

```python
def append(self, run: str, step: str, actor: str, content: str) -> AuditEntry:
```

- Defines the method `append`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run`, type `str`.
  - `step`, type `str`.
  - `actor`, type `str`.
  - `content`, type `str`.
- Gives back a value of type `AuditEntry`.

```python
"""Add one step to the chain."""
```

- The docstring (documentation kept with the code) says: *Add one step to the chain.*

```python
with self._database.lock:
```

- Opens `self._database.lock` for the indented lines, and releases it when they end (even after an error).

```python
last = self._database.execute("SELECT hash FROM audit_log ORDER BY seq DESC LIMIT 1")
entry = make_entry(str(last[0][0]) if last else None, run, step, actor, self._clock.now(), content)
self._database.execute(
    "INSERT INTO audit_log (run_id, step, actor, at, content, previous, hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
    (entry.run, entry.step, entry.actor, entry.at, entry.content, entry.previous, entry.hash),
)
```

- `last = self._database.execute("SELECT hash FROM audit_log ORDER BY ...`: stores the result of calling `self._database.execute("SELECT hash FROM audit_log ORDER BY seq DESC LIMIT 1")`, which is this repository's own `execute` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run one statement in a transaction and return its rows in `last`.
- `entry = make_entry(str(last[0][0]) if last else None, run, step, ac...`: stores the result of calling `make_entry(str(last[0][0]) if last else None, run, step, actor, self._clock.now(), cont...`, which is this repository's own `make_entry` (in `src/streaming_assistant/domain/audit.py`): the next entry in the chain in `entry`.
- `self._database.execute( "INSERT INTO audit_log (run_id, step, actor...`: calling `self._database.execute( "INSERT INTO audit_log (run_id, step, actor, at, content, previ...`, which is this repository's own `execute` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run one statement in a transaction and return its rows.

```python
return entry
```

- `return entry`: ends the function and gives back the value of `entry`.

```python
def entries(self, run: str | None = None) -> Sequence[AuditEntry]:
```

- Defines the method `entries`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `run`, type `str | None`, optional (default `None`).
- Gives back a value of type `Sequence[AuditEntry]`.

```python
"""The whole chain in order, or the steps of one run."""
```

- The docstring (documentation kept with the code) says: *The whole chain in order, or the steps of one run.*

```python
sql = "SELECT previous, run_id, step, actor, at, content, hash FROM audit_log"
rows = self._database.execute(
    sql + (" WHERE run_id = ?" if run else "") + " ORDER BY seq", (run,) if run else ()
)
return [AuditEntry(*(str(cell) for cell in row)) for row in rows]
```

- `sql = "SELECT previous, run_id, step, actor, at, content, hash FROM...`: stores the text `'SELECT previous, run_id, step, actor, at, content, hash FROM audit_log'` in `sql`.
- `rows = self._database.execute( sql + (" WHERE run_id = ?" if run el...`: stores the result of calling `self._database.execute( sql + (" WHERE run_id = ?" if run else "") + " ORDER BY seq", (...`, which is this repository's own `execute` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run one statement in a transaction and return its rows in `rows`.
- `return [AuditEntry(*(str(cell) for cell in row)) for row in rows]`: ends the function and gives back a list built by running `AuditEntry(*(str(cell) for cell in row))` for each `row` in `rows`.

#### `src/streaming_assistant/interfaces/__init__.py`

```python
"""The interfaces layer."""
```

- The docstring (documentation kept with the code) says: *The interfaces layer.*

#### `src/streaming_assistant/interfaces/cli.py`

```python
"""The `streaming-assistant` command: serve, db, trace, evaluate, stop-test, load-test, audit verification and replay."""
```

- The docstring (documentation kept with the code) says: *The `streaming-assistant` command: serve, db, trace, evaluate, stop-test, load-test, audit verification and replay.*

```python
import argparse
import asyncio
import json
import logging
import os
import sys
```

- `import argparse`: makes the module `argparse` available (the standard library's command-line argument parser).
- `import asyncio`: makes the module `asyncio` available (the standard library's tools for asynchronous code (many waits interleaved on one thread)).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import logging`: makes the module `logging` available (the standard library's logging system).
- `import os`: makes the module `os` available (operating-system services: environment variables, paths, processes).
- `import sys`: makes the module `sys` available (facts about the running Python program: arguments, exit, standard streams).

```python
from collections.abc import Sequence
from dataclasses import replace

from streaming_assistant.domain.audit import verify
from streaming_assistant.infrastructure.environment import ConfigurationError
from streaming_assistant.infrastructure.logging import configure_logging
from streaming_assistant.infrastructure.recorded_stream import MissingRecordingError
```

- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Sequence`: the type hint for an ordered, indexable collection.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`replace`: a name provided by that module.)
- `from streaming_assistant.domain.audit import ...`: takes names from `streaming_assistant.domain.audit`, this repository's own code. (`verify`: Index of the first entry that was edited, removed or reordered; None when the chain holds.)
- `from streaming_assistant.infrastructure.environment import ...`: takes names from `streaming_assistant.infrastructure.environment`, this repository's own code. (`ConfigurationError`: An environment variable is missing or has an unusable value.)
- `from streaming_assistant.infrastructure.logging import ...`: takes names from `streaming_assistant.infrastructure.logging`, this repository's own code. (`configure_logging`: Send every log record to `stream` (stderr by default) as logfmt.)
- `from streaming_assistant.infrastructure.recorded_stream import ...`: takes names from `streaming_assistant.infrastructure.recorded_stream`, this repository's own code. (`MissingRecordingError`: No recording matches this request; the message says how to re-record.)

```python
from streaming_assistant.infrastructure.settings import Settings
from streaming_assistant.interfaces.measure import evaluate_questions, load_test, stop_test, trace_one
from streaming_assistant.interfaces.wiring import build_components, database_exists

LOGGER = logging.getLogger("streaming_assistant")
```

- `from streaming_assistant.infrastructure.settings import ...`: takes names from `streaming_assistant.infrastructure.settings`, this repository's own code. (`Settings`: Everything the programs read from the environment.)
- `from streaming_assistant.interfaces.measure import ...`: takes names from `streaming_assistant.interfaces.measure`, this repository's own code. (`evaluate_questions`: All 200 questions: pauses, false pauses, citations shown outside the retrieved set, dropped citations.) (`load_test`: Replay the answerable questions at `rps` for `duration` seconds against a server per configuration.) (`stop_test`: Close the connection after 3 tokens and look at the upstream call; then time an unrelated request.) (`trace_one`: One request's stage times from the real path.)
- `from streaming_assistant.interfaces.wiring import ...`: takes names from `streaming_assistant.interfaces.wiring`, this repository's own code. (`build_components`: Wire everything.) (`database_exists`: True when the database file is already there (an in-memory database never is: it starts empty).)
- `LOGGER = logging.getLogger("streaming_assistant")`: stores the result of calling `logging.getLogger("streaming_assistant")`, which gets the logger named `"streaming_assistant"` in `LOGGER`.

```python
def _parser() -> argparse.ArgumentParser:
```

- Defines the function `_parser`.
- Gives back a value of type `argparse.ArgumentParser`.

```python
parser = argparse.ArgumentParser(
    prog="streaming-assistant", description="A streaming support assistant inside a latency budget."
)
commands = parser.add_subparsers(dest="command", required=True)
```

- `parser = argparse.ArgumentParser( prog="streaming-assistant", descr...`: stores the result of calling `argparse.ArgumentParser( prog="streaming-assistant", description="A streaming support a...`, which makes a `ArgumentParser` object with the named values `prog`, `description` in `parser`.
- `commands = parser.add_subparsers(dest="command", required=True)`: stores the result of calling `parser.add_subparsers(dest="command", required=True)`, which prepares sub-commands The named values are `dest`, `required`. in `commands`.

```python
for name, text in (
    ("serve", "start the HTTP server"),
    ("db", "rebuild the SQLite database from sql/001_schema.sql and sql/002_seed.sql"),
    ("evaluate", "the 200 sample questions: pauses, false pauses, citations"),
    ("stop-test", "close the stream after 3 tokens and look at the upstream call"),
    ("verify-audit", "check the hash chain of the audit log"),
    ("tamper-demo", "edit and delete entries in a copy of the chain and verify"),
):
```

- Repeats the indented lines once for each item of `( ("serve", "start the HTTP server"), ("db", "rebuild the SQLite database from sql/001_...`, naming the current item the names `name`, `text`.

```python
commands.add_parser(name, help=text)
```

- `commands.add_parser(name, help=text)`: calling `commands.add_parser(name, help=text)`, which declares the sub-command `name` The named values are `help`..

```python
trace = commands.add_parser("trace", help="one request's stage times, cold and warm")
trace.add_argument(
    "--question",
    default="A question about shipping times: standard delivery takes three to five business days after dispatch?",
)
load = commands.add_parser("load-test", help="replay the questions at a steady rate against four configurations")
load.add_argument("--rps", type=float, default=5.0)
load.add_argument("--duration", type=float, default=40.0)
replay = commands.add_parser("replay", help="what the customer saw and who approved it, from the audit log")
```

- `trace = commands.add_parser("trace", help="one request's stage time...`: stores the result of calling `commands.add_parser("trace", help="one request's stage times, cold and warm")`, which declares the sub-command `"trace"` The named values are `help`. in `trace`.
- `trace.add_argument( "--question", default="A question about shippin...`: calling `trace.add_argument( "--question", default="A question about shipping times: standard de...`, which declares a command-line argument `"--question"` The named values are `default`..
- `load = commands.add_parser("load-test", help="replay the questions ...`: stores the result of calling `commands.add_parser("load-test", help="replay the questions at a steady rate against fo...`, which declares the sub-command `"load-test"` The named values are `help`. in `load`.
- `load.add_argument("--rps", type=float, default=5.0)`: calling `load.add_argument("--rps", type=float, default=5.0)`, which declares a command-line argument `"--rps"` The named values are `type`, `default`..
- `load.add_argument("--duration", type=float, default=40.0)`: calling `load.add_argument("--duration", type=float, default=40.0)`, which declares a command-line argument `"--duration"` The named values are `type`, `default`..
- `replay = commands.add_parser("replay", help="what the customer saw ...`: stores the result of calling `commands.add_parser("replay", help="what the customer saw and who approved it, from the...`, which declares the sub-command `"replay"` The named values are `help`. in `replay`.

```python
replay.add_argument("run_id")
return parser
```

- `replay.add_argument("run_id")`: calling `replay.add_argument("run_id")`, which declares a command-line argument `"run_id"`.
- `return parser`: ends the function and gives back the value of `parser`.

```python
def _tamper(components: object) -> int:
```

- Defines the function `_tamper`.
- Parameters:
  - `components`, type `object`.
- Gives back a value of type `int`.

```python
from streaming_assistant.interfaces.wiring import Components

assert isinstance(components, Components)
entries = list(components.audit.entries())
```

- `from streaming_assistant.interfaces.wiring import ...`: takes names from `streaming_assistant.interfaces.wiring`, this repository's own code. (`Components`: Everything a command needs.)
- `assert isinstance(components, Components)`: checks that `isinstance(components, Components)` is true (the call asks whether `components` is a `Components`). A false check stops the test as failed.
- `entries = list(components.audit.entries())`: stores the result of calling `list(components.audit.entries())`, which builds a new list from `components.audit.entries()` in `entries`.

```python
if len(entries) < 3:
```

- Checks whether `len(entries)` is less than `3`. If so, the indented lines run.

```python
for step in ("paused", "answered", "resumed"):
```

- Repeats the indented lines once for each item of `("paused", "answered", "resumed")`, naming the current item `step`.

```python
components.audit.append("run-demo", step, "demo", f"content of {step}")
```

- `components.audit.append("run-demo", step, "demo", f"content of {ste...`: calling `components.audit.append("run-demo", step, "demo", f"content of {step}")`, which adds `"run-demo"` to the end of `components.audit`.

```python
entries = list(components.audit.entries())
```

- `entries = list(components.audit.entries())`: stores the result of calling `list(components.audit.entries())`, which builds a new list from `components.audit.entries()` in `entries`.

```python
print("chain intact:", verify(entries))
edited = [
    replace(entry, content="Approve a full refund") if index == 1 else entry for index, entry in enumerate(entries)
]
print("after tampering entry 1:", verify(edited))
removed = [entry for index, entry in enumerate(entries) if index != 1]
print("after deleting entry 1:", verify(removed))
return 0
```

- `print("chain intact:", verify(entries))`: calling `print("chain intact:", verify(entries))`, which writes `"chain intact:"`, `verify(entries)` to the screen (standard output).
- `edited = [ replace(entry, content="Approve a full refund") if index...`: stores a list built by running `replace(entry, content="Approve a full refund") if index == 1 else entry` for each `index, entry` in `enumerate(entries)` in `edited`.
- `print("after tampering entry 1:", verify(edited))`: calling `print("after tampering entry 1:", verify(edited))`, which writes `"after tampering entry 1:"`, `verify(edited)` to the screen (standard output).
- `removed = [entry for index, entry in enumerate(entries) if index != 1]`: stores a list built by running `entry` for each `index, entry` in `enumerate(entries)` keeping only those where `index` is different from `1` in `removed`.
- `print("after deleting entry 1:", verify(removed))`: calling `print("after deleting entry 1:", verify(removed))`, which writes `"after deleting entry 1:"`, `verify(removed)` to the screen (standard output).
- `return 0`: ends the function and gives back the number `0`.

```python
def main(argv: Sequence[str] | None = None) -> int:
```

- Defines the function `main`.
- Parameters:
  - `argv`, type `Sequence[str] | None`, optional (default `None`).
- Gives back a value of type `int`.

```python
"""Run one subcommand; returns the process exit code."""
```

- The docstring (documentation kept with the code) says: *Run one subcommand; returns the process exit code.*

```python
arguments = _parser().parse_args(argv)
```

- `arguments = _parser().parse_args(argv)`: stores the result of calling `_parser().parse_args(argv)`, which reads the command line into an object in `arguments`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
settings = Settings.from_environ(os.environ)
```

- `settings = Settings.from_environ(os.environ)`: stores the result of calling `Settings.from_environ(os.environ)`, which is this repository's own `from_environ` (in `src/streaming_assistant/infrastructure/settings.py`): read and validate; raises `ConfigurationError` naming the first bad variable in `settings`.

```python
except ConfigurationError as error:
```

- If an error of kind `ConfigurationError` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
print(f"configuration error: {error}", file=sys.stderr)
return 2
```

- `print(f"configuration error: {error}", file=sys.stderr)`: calling `print(f"configuration error: {error}", file=sys.stderr)`, which writes `f"configuration error: {error}"` to the screen (standard output) The named values are `file`..
- `return 2`: ends the function and gives back the number `2`.

```python
configure_logging(settings.log_level)
```

- `configure_logging(settings.log_level)`: calling `configure_logging(settings.log_level)`, which is this repository's own `configure_logging` (in `src/streaming_assistant/infrastructure/logging.py`): send every log record to `stream` (stderr by default) as logfmt.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
if arguments.command == "load-test":
```

- Checks whether `arguments.command` equals `"load-test"`. If so, the indented lines run.

```python
print(
    "| Configuration | Requests | Server p50 (ms) | Server p95 (ms) | Client p50 (ms) | Client p95 (ms) | Budget (ms) |"
)
print("| --- | --- | --- | --- | --- | --- | --- |")
```

- `print( "| Configuration | Requests | Server p50 (ms) | Server p95 (...`: calling `print( "| Configuration | Requests | Server p50 (ms) | Server p95 (ms) | Client p50 (ms...`, which writes `"| Configuration | Requests | Server p50 (ms) | Server p95 (ms) | Client p50 (ms) | Cli...` to the screen (standard output).
- `print("| --- | --- | --- | --- | --- | --- | --- |")`: calling `print("| --- | --- | --- | --- | --- | --- | --- |")`, which writes `"| --- | --- | --- | --- | --- | --- | --- |"` to the screen (standard output).

```python
for row in load_test(settings, arguments.rps, arguments.duration):
```

- Repeats the indented lines once for each item of `load_test(settings, arguments.rps, arguments.duration)`, naming the current item `row`.

```python
print(
    f"| {row['config']} | {row['requests']} | {row['server_p50_ms']} | {row['server_p95_ms']} | {row['client_p50_ms']} | {row['client_p95_ms']} | {row['budget_ms']} |"
)
```

- `print( f"| {row['config']} | {row['requests']} | {row['server_p50_m...`: calling `print( f"| {row['config']} | {row['requests']} | {row['server_p50_ms']} | {row['server_...`, which writes `f"| {row['config']} | {row['requests']} | {row['server_p50_ms']} | {row['server_p95_ms'...` to the screen (standard output).

```python
return 0
```

- `return 0`: ends the function and gives back the number `0`.

```python
if arguments.command == "stop-test":
```

- Checks whether `arguments.command` equals `"stop-test"`. If so, the indented lines run.

```python
print(json.dumps(asyncio.run(stop_test(settings)), indent=1))
return 0
```

- `print(json.dumps(asyncio.run(stop_test(settings)), indent=1))`: calling `print(json.dumps(asyncio.run(stop_test(settings)), indent=1))`, which writes `json.dumps(asyncio.run(stop_test(settings)), indent=1)` to the screen (standard output).
- `return 0`: ends the function and gives back the number `0`.

```python
fresh = arguments.command == "db" or not database_exists(settings)
components = build_components(settings, fresh=fresh)
```

- `fresh = arguments.command == "db" or not database_exists(settings)`: stores `arguments.command == "db" or not database_exists(settings)` (the first operand that decides the or) in `fresh`.
- `components = build_components(settings, fresh=fresh)`: stores the result of calling `build_components(settings, fresh=fresh)`, which is this repository's own `build_components` (in `src/streaming_assistant/interfaces/wiring.py`): wire everything The named values are `fresh`. in `components`.

```python
if arguments.command == "db":
```

- Checks whether `arguments.command` equals `"db"`. If so, the indented lines run.

```python
print("applied 001_schema.sql, 002_seed.sql to", settings.root / settings.database)
```

- `print("applied 001_schema.sql, 002_seed.sql to", settings.root / se...`: calling `print("applied 001_schema.sql, 002_seed.sql to", settings.root / settings.database)`, which writes `"applied 001_schema.sql, 002_seed.sql to"`, `settings.root / settings.database` to the screen (standard output).

```python
elif arguments.command == "serve":
```

- Otherwise, checks whether `arguments.command` equals `"serve"`. If so, the indented lines run.

```python
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
```

- `import uvicorn`: makes the module `uvicorn` available (the web server that runs a FastAPI application).
- `from streaming_assistant.interfaces.http import ...`: takes names from `streaming_assistant.interfaces.http`, this repository's own code. (`create_app`: Build the app over the assistant and its collaborators.)
- `app = create_app( components.assistant, components.desk, components...`: stores the result of calling `create_app( components.assistant, components.desk, components.catalog, components.authe...`, which is this repository's own `create_app` (in `src/streaming_assistant/interfaces/http.py`): build the app over the assistant and its collaborators in `app`.
- `uvicorn.run( app, host=settings.host, port=settings.port, log_level...`: calling `uvicorn.run( app, host=settings.host, port=settings.port, log_level=settings.log_level....`, which runs a program or a coroutine The named values are `host`, `port`, `log_level`, `timeout_graceful_shutdown`..

```python
elif arguments.command == "trace":
```

- Otherwise, checks whether `arguments.command` equals `"trace"`. If so, the indented lines run.

```python
cold_settings = replace(settings, warm_index=False, database=":memory:")
cold = asyncio.run(trace_one(build_components(cold_settings, fresh=True), arguments.question))
warm_components = build_components(replace(settings, database=":memory:"), fresh=True)
asyncio.run(trace_one(warm_components, arguments.question))
warm = asyncio.run(trace_one(warm_components, arguments.question))
print("cold (index built on the first request):", cold)
```

- `cold_settings = replace(settings, warm_index=False, database=":memo...`: stores the result of calling `replace(settings, warm_index=False, database=":memory:")`, which replaces `settings` with the second argument in  The named values are `warm_index`, `database`. in `cold_settings`.
- `cold = asyncio.run(trace_one(build_components(cold_settings, fresh=...`: stores the result of calling `asyncio.run(trace_one(build_components(cold_settings, fresh=True), arguments.question))`, which runs a program or a coroutine in `cold`.
- `warm_components = build_components(replace(settings, database=":mem...`: stores the result of calling `build_components(replace(settings, database=":memory:"), fresh=True)`, which is this repository's own `build_components` (in `src/streaming_assistant/interfaces/wiring.py`): wire everything The named values are `fresh`. in `warm_components`.
- `asyncio.run(trace_one(warm_components, arguments.question))`: calling `asyncio.run(trace_one(warm_components, arguments.question))`, which runs a program or a coroutine.
- `warm = asyncio.run(trace_one(warm_components, arguments.question))`: stores the result of calling `asyncio.run(trace_one(warm_components, arguments.question))`, which runs a program or a coroutine in `warm`.
- `print("cold (index built on the first request):", cold)`: calling `print("cold (index built on the first request):", cold)`, which writes `"cold (index built on the first request):"`, `cold` to the screen (standard output).

```python
print("warm:", warm)
```

- `print("warm:", warm)`: calling `print("warm:", warm)`, which writes `"warm:"`, `warm` to the screen (standard output).

```python
for label, timings in (("cold", cold), ("warm", warm)):
```

- Repeats the indented lines once for each item of `(("cold", cold), ("warm", warm))`, naming the current item the names `label`, `timings`.

```python
gap = abs(timings["first_token_ms"] - timings["stage_sum_ms"])
print(
    f"{label}: stage sum {timings['stage_sum_ms']} ms vs first token {timings['first_token_ms']} ms (difference {gap:.1f} ms)"
)
```

- `gap = abs(timings["first_token_ms"] - timings["stage_sum_ms"])`: stores the result of calling `abs(timings["first_token_ms"] - timings["stage_sum_ms"])`, which takes the size of `timings["first_token_ms"] - timings["stage_sum_ms"]` without its sign in `gap`.
- `print( f"{label}: stage sum {timings['stage_sum_ms']} ms vs first t...`: calling `print( f"{label}: stage sum {timings['stage_sum_ms']} ms vs first token {timings['first...`, which writes `f"{label}: stage sum {timings['stage_sum_ms']} ms vs first token {timings['first_token_...` to the screen (standard output).

```python
elif arguments.command == "evaluate":
```

- Otherwise, checks whether `arguments.command` equals `"evaluate"`. If so, the indented lines run.

```python
print(
    json.dumps(
        asyncio.run(
            evaluate_questions(build_components(replace(settings, database=":memory:"), fresh=True))
        ),
        indent=1,
    )
)
```

- `print( json.dumps( asyncio.run( evaluate_questions(build_components...`: calling `print( json.dumps( asyncio.run( evaluate_questions(build_components(replace(settings, d...`, which writes `json.dumps( asyncio.run( evaluate_questions(build_components(replace(settings, database...` to the screen (standard output).

```python
elif arguments.command == "verify-audit":
```

- Otherwise, checks whether `arguments.command` equals `"verify-audit"`. If so, the indented lines run.

```python
entries = components.audit.entries()
broken = verify(entries)
print(f"{len(entries)} entries; first broken index: {broken}")
return 0 if broken is None else 1
```

- `entries = components.audit.entries()`: stores the result of calling `components.audit.entries()` in `entries`.
- `broken = verify(entries)`: stores the result of calling `verify(entries)`, which is this repository's own `verify` (in `src/streaming_assistant/domain/audit.py`): index of the first entry that was edited, removed or reordered; None when the chain holds in `broken`.
- `print(f"{len(entries)} entries; first broken index: {broken}")`: calling `print(f"{len(entries)} entries; first broken index: {broken}")`, which writes `f"{len(entries)} entries; first broken index: {broken}"` to the screen (standard output).
- `return 0 if broken is None else 1`: ends the function and gives back `0` when `broken` is nothing (`None`), otherwise `1`.

```python
elif arguments.command == "tamper-demo":
```

- Otherwise, checks whether `arguments.command` equals `"tamper-demo"`. If so, the indented lines run.

```python
return _tamper(components)
```

- `return _tamper(components)`: ends the function and gives back the result of calling `_tamper(components)`.

```python
elif arguments.command == "replay":
```

- Otherwise, checks whether `arguments.command` equals `"replay"`. If so, the indented lines run.

```python
for entry in components.audit.entries(arguments.run_id):
```

- Repeats the indented lines once for each item of `components.audit.entries(arguments.run_id)`, naming the current item `entry`.

```python
print(f"{entry.at} {entry.step:10} {entry.actor:14} {entry.content}")
```

- `print(f"{entry.at} {entry.step:10} {entry.actor:14} {entry.content}")`: calling `print(f"{entry.at} {entry.step:10} {entry.actor:14} {entry.content}")`, which writes `f"{entry.at} {entry.step:10} {entry.actor:14} {entry.content}"` to the screen (standard output).

```python
return 0
```

- `return 0`: ends the function and gives back the number `0`.

```python
except MissingRecordingError as error:
```

- If an error of kind `MissingRecordingError` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
LOGGER.error("%s", error)
return 1
```

- `LOGGER.error("%s", error)`: calling `LOGGER.error("%s", error)`, which writes an ERROR log line.
- `return 1`: ends the function and gives back the number `1`.

```python
if __name__ == "__main__":
```

- Checks whether `__name__` equals `"__main__"`. If so, the indented lines run.

```python
raise SystemExit(main())
```

- `raise SystemExit(main())`: stops with an error of kind `SystemExit` with the message `main()`. Whoever called this code must handle it or the program stops.

#### `src/streaming_assistant/interfaces/http.py`

```python
"""The HTTP interface: POST /ask streams typed server-sent events, Stop cancels the upstream call, reviewers answer paused runs.

This module deliberately has no `from __future__ import annotations`: FastAPI reads the annotations of the handlers
defined inside `create_app` to resolve their dependencies.
"""
```

- The docstring (documentation kept with the code) says: *The HTTP interface: POST /ask streams typed server-sent events, Stop cancels the upstream call, reviewers answer paused runs. This module deliberately has no `from __future__ import annotations`: FastAPI reads the annotations of the handlers defined inside `create_app` to resolve their dependencies.*

```python
import json
import logging
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated
```

- `import json`: makes the module `json` available (reads and writes JSON text).
- `import logging`: makes the module `logging` available (the standard library's logging system).
- `import uuid`: makes the module `uuid` available (universally unique identifiers).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`AsyncIterator`: a name provided by that module.)
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`Annotated`: attaches extra information to a type hint.)

```python
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from streaming_assistant.application.assistant import Assistant, Event, UnauthorizedError
from streaming_assistant.application.ports import AuditLog, Authenticator
from streaming_assistant.application.review import ReviewDesk
```

- `from fastapi import ...`: takes names from `fastapi` (the web framework that turns Python functions into HTTP endpoints). (`Depends`: runs another function before the endpoint and passes in its result.) (`FastAPI`: the application class.) (`Header`: reads an HTTP header into a parameter.) (`HTTPException`: an error that FastAPI turns into an HTTP error response.)
- `from fastapi.responses import ...`: takes names from `fastapi.responses` (the web framework that turns Python functions into HTTP endpoints). (`FileResponse`: an HTTP response that sends a file.) (`HTMLResponse`: an HTTP response whose body is HTML.) (`JSONResponse`: an HTTP response whose body is JSON.) (`StreamingResponse`: an HTTP response whose body is produced piece by piece.)
- `from pydantic import ...`: takes names from `pydantic` (data classes that validate their input). (`BaseModel`: the base class of a pydantic model.) (`Field`: describes one pydantic field (limits, default, description).)
- `from streaming_assistant.application.assistant import ...`: takes names from `streaming_assistant.application.assistant`, this repository's own code. (`Assistant`: Orchestrates one request.) (`Event`: One server-sent event: a type name and its data.) (`UnauthorizedError`: The bearer token is missing or unknown.)
- `from streaming_assistant.application.ports import ...`: takes names from `streaming_assistant.application.ports`, this repository's own code. (`AuditLog`: An append-only, hash-chained log.) (`Authenticator`: Checks a bearer token.)
- `from streaming_assistant.application.review import ...`: takes names from `streaming_assistant.application.review`, this repository's own code. (`ReviewDesk`: Lists waiting runs and validates a reviewer's answer: not empty, and either citing a real section or saying that no page covers the question.)

```python
from streaming_assistant.domain.audit import verify
from streaming_assistant.domain.errors import ReviewRejectedError, UnknownRunError
from streaming_assistant.infrastructure.catalog import PageCatalog

LOGGER = logging.getLogger("streaming_assistant.http")
STATIC = Path(__file__).parent / "static"
SSE_HEADERS = {"Cache-Control": "no-store", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
```

- `from streaming_assistant.domain.audit import ...`: takes names from `streaming_assistant.domain.audit`, this repository's own code. (`verify`: Index of the first entry that was edited, removed or reordered; None when the chain holds.)
- `from streaming_assistant.domain.errors import ...`: takes names from `streaming_assistant.domain.errors`, this repository's own code. (`ReviewRejectedError`: A reviewer's answer is not allowed (empty, ungrounded, or the run is not waiting).) (`UnknownRunError`: No run with this id.)
- `from streaming_assistant.infrastructure.catalog import ...`: takes names from `streaming_assistant.infrastructure.catalog`, this repository's own code. (`PageCatalog`: Loads `data/help_pages.json`: 30 pages with titled sections.)
- `LOGGER = logging.getLogger("streaming_assistant.http")`: stores the result of calling `logging.getLogger("streaming_assistant.http")`, which gets the logger named `"streaming_assistant.http"` in `LOGGER`.
- `STATIC = Path(__file__).parent / "static"`: stores the path `Path(__file__).parent / "static"` (`/` joins path parts) in `STATIC`.
- `SSE_HEADERS = {"Cache-Control": "no-store", "X-Accel-Buffering": "n...`: stores a new dict with 3 entries in `SSE_HEADERS`.

```python
class AskIn(BaseModel):
```

- Defines the class `AskIn`.
- It extends `BaseModel` (it starts with all of that class's methods and may add or replace some).

```python
"""A customer question."""
```

- The docstring (documentation kept with the code) says: *A customer question.*

```python
question: str = Field(min_length=3, max_length=1000)
```

- `question: str = Field(min_length=3, max_length=1000)`: a field named `question` of type `str`, default `Field(min_length=3, max_length=1000)`.

```python
class ReviewIn(BaseModel):
```

- Defines the class `ReviewIn`.
- It extends `BaseModel` (it starts with all of that class's methods and may add or replace some).

```python
"""A reviewer's answer to a paused run."""
```

- The docstring (documentation kept with the code) says: *A reviewer's answer to a paused run.*

```python
reviewer_id: str = Field(min_length=1, max_length=64)
answer: str = Field(max_length=2000)
cited: list[str] = Field(default_factory=list, max_length=5)
no_page: bool = False
```

- `reviewer_id: str = Field(min_length=1, max_length=64)`: a field named `reviewer_id` of type `str`, default `Field(min_length=1, max_length=64)`.
- `answer: str = Field(max_length=2000)`: a field named `answer` of type `str`, default `Field(max_length=2000)`.
- `cited: list[str] = Field(default_factory=list, max_length=5)`: a field named `cited` of type `list[str]`, default `Field(default_factory=list, max_length=5)`.
- `no_page: bool = False`: a field named `no_page` of type `bool`, default `False`.

```python
def encode(event: Event) -> str:
```

- Defines the function `encode`.
- Parameters:
  - `event`, type `Event`.
- Gives back a value of type `str`.

```python
"""One server-sent event."""
```

- The docstring (documentation kept with the code) says: *One server-sent event.*

```python
return f"event: {event.name}\ndata: {json.dumps(event.data)}\n\n"
```

- `return f"event: {event.name}\ndata: {json.dumps(event.data)}\n\n"`: ends the function and gives back the text built by the f-string `f"event: {event.name}\ndata: {json.dumps(event.data)}\n\n"`.

```python
def create_app(
    assistant: Assistant, desk: ReviewDesk, catalog: PageCatalog, authenticator: Authenticator, audit: AuditLog
) -> FastAPI:
```

- Defines the function `create_app`.
- Parameters:
  - `assistant`, type `Assistant`.
  - `desk`, type `ReviewDesk`.
  - `catalog`, type `PageCatalog`.
  - `authenticator`, type `Authenticator`.
  - `audit`, type `AuditLog`.
- Gives back a value of type `FastAPI`.

```python
"""Build the app over the assistant and its collaborators."""
```

- The docstring (documentation kept with the code) says: *Build the app over the assistant and its collaborators.*

```python
app = FastAPI(title="Streaming support assistant", version="0.1.0")
```

- `app = FastAPI(title="Streaming support assistant", version="0.1.0")`: stores the result of calling `FastAPI(title="Streaming support assistant", version="0.1.0")`, which makes a `FastAPI` object with the named values `title`, `version` in `app`.

```python
def role(authorization: Annotated[str | None, Header()] = None) -> str:
```

- Defines the function `role`.
- Parameters:
  - `authorization`, type `Annotated[str | None, Header()]`, optional (default `None`).
- Gives back a value of type `str`.

```python
found = authenticator.role_of((authorization or "").removeprefix("Bearer ").strip())
```

- `found = authenticator.role_of((authorization or "").removeprefix("B...`: stores the result of calling `authenticator.role_of((authorization or "").removeprefix("Bearer ").strip())` in `found`.

```python
if found is None:
```

- Checks whether `found` is nothing (`None`). If so, the indented lines run.

```python
raise HTTPException(status_code=401, detail="sign in first")
```

- `raise HTTPException(status_code=401, detail="sign in first")`: stops with an error of kind `HTTPException`. Whoever called this code must handle it or the program stops.

```python
return found
```

- `return found`: ends the function and gives back the value of `found`.

```python
def reviewer(found: Annotated[str, Depends(role)]) -> None:
```

- Defines the function `reviewer`.
- Parameters:
  - `found`, type `Annotated[str, Depends(role)]`.
- Gives back a value of type `None`.

```python
if found != "reviewer":
```

- Checks whether `found` is different from `"reviewer"`. If so, the indented lines run.

```python
raise HTTPException(status_code=403, detail="reviewers only")
```

- `raise HTTPException(status_code=403, detail="reviewers only")`: stops with an error of kind `HTTPException`. Whoever called this code must handle it or the program stops.

```python
async def sse(events: AsyncIterator[Event]) -> AsyncIterator[str]:
```

- Defines the async function `sse` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `events`, type `AsyncIterator[Event]`.
- Gives back a value of type `AsyncIterator[str]`.

```python
async for event in events:
```

- Repeats the indented lines once for each item of `events`, naming the current item `event`. (`async for` waits for each item.)

```python
yield encode(event)
```

- `yield encode(event)`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
@app.get("/", response_class=HTMLResponse)
def home() -> FileResponse:
```

- Defines the function `home`.
- `@app.get("/", response_class=HTMLResponse)`: registers the function with the web application: it runs when a matching request arrives.
- Gives back a value of type `FileResponse`.

```python
return FileResponse(STATIC / "index.html")
```

- `return FileResponse(STATIC / "index.html")`: ends the function and gives back the result of calling `FileResponse(STATIC / "index.html")`, which makes a `FileResponse` object from `STATIC / "index.html"`.

```python
@app.get("/review", response_class=HTMLResponse)
def review_page() -> FileResponse:
```

- Defines the function `review_page`.
- `@app.get("/review", response_class=HTMLResponse)`: registers the function with the web application: it runs when a matching request arrives.
- Gives back a value of type `FileResponse`.

```python
return FileResponse(STATIC / "review.html")
```

- `return FileResponse(STATIC / "review.html")`: ends the function and gives back the result of calling `FileResponse(STATIC / "review.html")`, which makes a `FileResponse` object from `STATIC / "review.html"`.

```python
@app.post("/ask")
async def ask(body: AskIn, authorization: Annotated[str | None, Header()] = None) -> StreamingResponse:
```

- Defines the async function `ask` (a coroutine: calling it makes a job for the event loop to run).
- `@app.post("/ask")`: registers the function with the web application: it runs when a matching request arrives.
- Parameters:
  - `body`, type `AskIn`.
  - `authorization`, type `Annotated[str | None, Header()]`, optional (default `None`).
- Gives back a value of type `StreamingResponse`.

```python
run_id = f"run-{uuid.uuid4().hex[:12]}"
```

- `run_id = f"run-{uuid.uuid4().hex[:12]}"`: stores the text built by the f-string `f"run-{uuid.uuid4().hex[:12]}"` in `run_id`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
prepared = await assistant.prepare(
    run_id, body.question, (authorization or "").removeprefix("Bearer ").strip()
)
```

- `prepared = await assistant.prepare( run_id, body.question, (authori...`: stores the answer of the result of calling `assistant.prepare( run_id, body.question, (authorization or "").removeprefix("Bearer ")...`, which is this repository's own `prepare` (in `src/streaming_assistant/application/assistant.py`): authenticate, retrieve, assemble and route; each stage is timed inside the real path once the wait is over in `prepared`.

```python
except UnauthorizedError:
```

- If an error of kind `UnauthorizedError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
raise HTTPException(status_code=401, detail="sign in first") from None
```

- `raise HTTPException(status_code=401, detail="sign in first") from None`: stops with an error of kind `HTTPException`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
LOGGER.info("run started", extra={"fields": {"run_id": run_id, "route": prepared.route.kind}})
return StreamingResponse(
    sse(assistant.stream(prepared)), media_type="text/event-stream", headers={**SSE_HEADERS, "X-Run-Id": run_id}
)
```

- `LOGGER.info("run started", extra={"fields": {"run_id": run_id, "rou...`: calling `LOGGER.info("run started", extra={"fields": {"run_id": run_id, "route": prepared.route....`, which writes an INFO log line The named values are `extra`..
- `return StreamingResponse( sse(assistant.stream(prepared)), media_ty...`: ends the function and gives back the result of calling `StreamingResponse( sse(assistant.stream(prepared)), media_type="text/event-stream", hea...`, which makes a `StreamingResponse` object from `sse(assistant.stream(prepared))` with the named values `media_type`, `headers`.

```python
@app.post("/runs/{run_id}/stop", status_code=202)
def stop(run_id: str, _: Annotated[str, Depends(role)]) -> dict[str, str]:
```

- Defines the function `stop`.
- `@app.post("/runs/{run_id}/stop", status_code=202)`: registers the function with the web application: it runs when a matching request arrives.
- Parameters:
  - `run_id`, type `str`.
  - `_`, type `Annotated[str, Depends(role)]`.
- Gives back a value of type `dict[str, str]`.

```python
assistant.stops.request(run_id)
return {"run_id": run_id, "status": "stop requested"}
```

- `assistant.stops.request(run_id)`: calling `assistant.stops.request(run_id)`.
- `return {"run_id": run_id, "status": "stop requested"}`: ends the function and gives back a new dict with 2 entries.

```python
@app.get("/runs/{run_id}/status")
def status(run_id: str, _: Annotated[str, Depends(role)]) -> dict[str, str | None]:
```

- Defines the function `status`.
- `@app.get("/runs/{run_id}/status")`: registers the function with the web application: it runs when a matching request arrives.
- Parameters:
  - `run_id`, type `str`.
  - `_`, type `Annotated[str, Depends(role)]`.
- Gives back a value of type `dict[str, str | None]`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
return {"run_id": run_id, "status": desk.status(run_id)}
```

- `return {"run_id": run_id, "status": desk.status(run_id)}`: ends the function and gives back a new dict with 2 entries.

```python
except UnknownRunError:
```

- If an error of kind `UnknownRunError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
raise HTTPException(status_code=404, detail="no such run") from None
```

- `raise HTTPException(status_code=404, detail="no such run") from None`: stops with an error of kind `HTTPException`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
@app.get("/runs/{run_id}/resume")
async def resume(run_id: str, _: Annotated[str, Depends(role)]) -> StreamingResponse:
```

- Defines the async function `resume` (a coroutine: calling it makes a job for the event loop to run).
- `@app.get("/runs/{run_id}/resume")`: registers the function with the web application: it runs when a matching request arrives.
- Parameters:
  - `run_id`, type `str`.
  - `_`, type `Annotated[str, Depends(role)]`.
- Gives back a value of type `StreamingResponse`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
events = assistant.resume(run_id)
first = await events.__anext__()
```

- `events = assistant.resume(run_id)`: stores the result of calling `assistant.resume(run_id)`, which is this repository's own `resume` (in `src/streaming_assistant/application/assistant.py`): continue a paused run whose reviewer answer was validated; the answer goes into the model's context in `events`.
- `first = await events.__anext__()`: stores the answer of the result of calling `events.__anext__()` once the wait is over in `first`.

```python
except UnknownRunError as error:
```

- If an error of kind `UnknownRunError` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
raise HTTPException(status_code=409, detail=str(error)) from None
```

- `raise HTTPException(status_code=409, detail=str(error)) from None`: stops with an error of kind `HTTPException`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
async def chained() -> AsyncIterator[Event]:
```

- Defines the async function `chained` (a coroutine: calling it makes a job for the event loop to run).
- Gives back a value of type `AsyncIterator[Event]`.

```python
yield first
```

- `yield first`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
async for event in events:
```

- Repeats the indented lines once for each item of `events`, naming the current item `event`. (`async for` waits for each item.)

```python
yield event
```

- `yield event`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
return StreamingResponse(sse(chained()), media_type="text/event-stream", headers=SSE_HEADERS)
```

- `return StreamingResponse(sse(chained()), media_type="text/event-str...`: ends the function and gives back the result of calling `StreamingResponse(sse(chained()), media_type="text/event-stream", headers=SSE_HEADERS)`, which makes a `StreamingResponse` object from `sse(chained())` with the named values `media_type`, `headers`.

```python
@app.get("/reviews", dependencies=[Depends(reviewer)])
def waiting() -> list[dict[str, object]]:
```

- Defines the function `waiting`.
- `@app.get("/reviews", dependencies=[Depends(reviewer)])`: registers the function with the web application: it runs when a matching request arrives.
- Gives back a value of type `list[dict[str, object]]`.

```python
return [
    {"run_id": r.run_id, "question": r.question, "reason": r.reason, "retrieved": list(r.retrieved)}
    for r in desk.waiting()
]
```

- `return [ {"run_id": r.run_id, "question": r.question, "reason": r.r...`: ends the function and gives back a list built by running `{"run_id": r.run_id, "question": r.question, "reason": r.reason, "retrieved": list(r.re...` for each `r` in `desk.waiting()`.

```python
@app.post("/reviews/{run_id}/answer", dependencies=[Depends(reviewer)])
def answer(run_id: str, body: ReviewIn) -> JSONResponse:
```

- Defines the function `answer`.
- `@app.post("/reviews/{run_id}/answer", dependencies=[Depends(reviewer)])`: registers the function with the web application: it runs when a matching request arrives.
- Parameters:
  - `run_id`, type `str`.
  - `body`, type `ReviewIn`.
- Gives back a value of type `JSONResponse`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
run = desk.answer(run_id, body.reviewer_id, body.answer, body.cited, body.no_page)
```

- `run = desk.answer(run_id, body.reviewer_id, body.answer, body.cited...`: stores the result of calling `desk.answer(run_id, body.reviewer_id, body.answer, body.cited, body.no_page)`, which is this repository's own `answer` (in `src/streaming_assistant/application/review.py`): validate and store the reviewer's answer; raises `ReviewRejectedError` with the reason when it is not allowed in `run`.

```python
except UnknownRunError:
```

- If an error of kind `UnknownRunError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
raise HTTPException(status_code=404, detail="no such run") from None
```

- `raise HTTPException(status_code=404, detail="no such run") from None`: stops with an error of kind `HTTPException`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
except ReviewRejectedError as error:
```

- If an error of kind `ReviewRejectedError` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
raise HTTPException(status_code=422, detail=str(error)) from None
```

- `raise HTTPException(status_code=422, detail=str(error)) from None`: stops with an error of kind `HTTPException`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
return JSONResponse({"run_id": run.run_id, "status": run.status})
```

- `return JSONResponse({"run_id": run.run_id, "status": run.status})`: ends the function and gives back the result of calling `JSONResponse({"run_id": run.run_id, "status": run.status})`, which makes a `JSONResponse` object from `{"run_id": run.run_id, "status": run.status}`.

```python
@app.get("/audit/verify", dependencies=[Depends(reviewer)])
def audit_verify() -> dict[str, object]:
```

- Defines the function `audit_verify`.
- `@app.get("/audit/verify", dependencies=[Depends(reviewer)])`: registers the function with the web application: it runs when a matching request arrives.
- Gives back a value of type `dict[str, object]`.

```python
entries = audit.entries()
return {"entries": len(entries), "first_broken_index": verify(entries)}
```

- `entries = audit.entries()`: stores the result of calling `audit.entries()` in `entries`.
- `return {"entries": len(entries), "first_broken_index": verify(entri...`: ends the function and gives back a new dict with 2 entries.

```python
@app.get("/pages/{page_id}", response_class=HTMLResponse)
def page(page_id: str) -> HTMLResponse:
```

- Defines the function `page`.
- `@app.get("/pages/{page_id}", response_class=HTMLResponse)`: registers the function with the web application: it runs when a matching request arrives.
- Parameters:
  - `page_id`, type `str`.
- Gives back a value of type `HTMLResponse`.

```python
found = catalog.page_html(page_id)
```

- `found = catalog.page_html(page_id)`: stores the result of calling `catalog.page_html(page_id)`, which is this repository's own `page_html` (in `src/streaming_assistant/infrastructure/catalog.py`): a page as HTML with an id on every section, so `#anchor` opens it at the cited section in `found`.

```python
if found is None:
```

- Checks whether `found` is nothing (`None`). If so, the indented lines run.

```python
raise HTTPException(status_code=404, detail="no such page")
```

- `raise HTTPException(status_code=404, detail="no such page")`: stops with an error of kind `HTTPException`. Whoever called this code must handle it or the program stops.

```python
return HTMLResponse(found)
```

- `return HTMLResponse(found)`: ends the function and gives back the result of calling `HTMLResponse(found)`, which makes a `HTMLResponse` object from `found`.

```python
@app.get("/healthz")
def healthz() -> dict[str, str]:
```

- Defines the function `healthz`.
- `@app.get("/healthz")`: registers the function with the web application: it runs when a matching request arrives.
- Gives back a value of type `dict[str, str]`.

```python
return {"status": "ok"}
```

- `return {"status": "ok"}`: ends the function and gives back a new dict with 1 entries.

```python
@app.get("/readyz")
def readyz() -> dict[str, object]:
```

- Defines the function `readyz`.
- `@app.get("/readyz")`: registers the function with the web application: it runs when a matching request arrives.
- Gives back a value of type `dict[str, object]`.

```python
return {"status": "ready", "sections": len(catalog.sections)}
```

- `return {"status": "ready", "sections": len(catalog.sections)}`: ends the function and gives back a new dict with 2 entries.

```python
@app.get("/stats")
def stats() -> dict[str, int]:
```

- Defines the function `stats`.
- `@app.get("/stats")`: registers the function with the web application: it runs when a matching request arrives.
- Gives back a value of type `dict[str, int]`.

```python
return dict(assistant.stats)
```

- `return dict(assistant.stats)`: ends the function and gives back the result of calling `dict(assistant.stats)`, which builds a dict.

```python
return app
```

- `return app`: ends the function and gives back the value of `app`.

#### `src/streaming_assistant/interfaces/measure.py`

```python
"""Measurements that need a running server or the whole question set: the 200 questions, Stop, the budget under load."""
```

- The docstring (documentation kept with the code) says: *Measurements that need a running server or the whole question set: the 200 questions, Stop, the budget under load.*

```python
import asyncio
import json
import os
import socket
import statistics
import subprocess
```

- `import asyncio`: makes the module `asyncio` available (the standard library's tools for asynchronous code (many waits interleaved on one thread)).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import os`: makes the module `os` available (operating-system services: environment variables, paths, processes).
- `import socket`: makes the module `socket` available (network connections at the lowest level).
- `import statistics`: makes the module `statistics` available (mean, median and similar summaries).
- `import subprocess`: makes the module `subprocess` available (starting other programs).

```python
import sys
import threading
import time
from dataclasses import replace

import httpx
import uvicorn
```

- `import sys`: makes the module `sys` available (facts about the running Python program: arguments, exit, standard streams).
- `import threading`: makes the module `threading` available (threads, locks and events).
- `import time`: makes the module `time` available (clocks and sleeping).
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`replace`: a name provided by that module.)
- `import httpx`: makes the module `httpx` available (an HTTP client library).
- `import uvicorn`: makes the module `uvicorn` available (the web server that runs a FastAPI application).

```python
from streaming_assistant.application.assistant import Event
from streaming_assistant.domain.stats import percentile
from streaming_assistant.infrastructure.scripted_stream import Pace, ScriptedStreamingModel
from streaming_assistant.infrastructure.settings import Settings
from streaming_assistant.interfaces.http import create_app
from streaming_assistant.interfaces.wiring import Components, build_components
```

- `from streaming_assistant.application.assistant import ...`: takes names from `streaming_assistant.application.assistant`, this repository's own code. (`Event`: One server-sent event: a type name and its data.)
- `from streaming_assistant.domain.stats import ...`: takes names from `streaming_assistant.domain.stats`, this repository's own code. (`percentile`: Nearest-rank percentile of `values` (0.95 for p95); 0.0 for no values.)
- `from streaming_assistant.infrastructure.scripted_stream import ...`: takes names from `streaming_assistant.infrastructure.scripted_stream`, this repository's own code. (`Pace`: Latency settings in milliseconds.) (`ScriptedStreamingModel`: Async streaming with counters: tokens produced (what would be billed), cancellations and their times.)
- `from streaming_assistant.infrastructure.settings import ...`: takes names from `streaming_assistant.infrastructure.settings`, this repository's own code. (`Settings`: Everything the programs read from the environment.)
- `from streaming_assistant.interfaces.http import ...`: takes names from `streaming_assistant.interfaces.http`, this repository's own code. (`create_app`: Build the app over the assistant and its collaborators.)
- `from streaming_assistant.interfaces.wiring import ...`: takes names from `streaming_assistant.interfaces.wiring`, this repository's own code. (`Components`: Everything a command needs.) (`build_components`: Wire everything.)

```python
CUSTOMER = {"Authorization": "Bearer demo-customer-token"}
```

- `CUSTOMER = {"Authorization": "Bearer demo-customer-token"}`: stores a new dict with 1 entries in `CUSTOMER`.

```python
async def collect(
    components: Components, run_id: str, question: str, token: str = "demo-customer-token"
) -> tuple[list[Event], list[str]]:
```

- Defines the async function `collect` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `components`, type `Components`.
  - `run_id`, type `str`.
  - `question`, type `str`.
  - `token`, type `str`, optional (default `"demo-customer-token"`).
- Gives back a value of type `tuple[list[Event], list[str]]`.

```python
"""Run one question in process; returns the events and the refs that were retrieved for it."""
```

- The docstring (documentation kept with the code) says: *Run one question in process; returns the events and the refs that were retrieved for it.*

```python
prepared = await components.assistant.prepare(run_id, question, token)
return [event async for event in components.assistant.stream(prepared)], [hit.section.ref for hit in prepared.hits]
```

- `prepared = await components.assistant.prepare(run_id, question, token)`: stores the answer of the result of calling `components.assistant.prepare(run_id, question, token)`, which is this repository's own `prepare` (in `src/streaming_assistant/application/assistant.py`): authenticate, retrieve, assemble and route; each stage is timed inside the real path once the wait is over in `prepared`.
- `return [event async for event in components.assistant.stream(prepar...`: ends the function and gives back a tuple of 2 items.

```python
async def trace_one(components: Components, question: str) -> dict[str, float]:
```

- Defines the async function `trace_one` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `components`, type `Components`.
  - `question`, type `str`.
- Gives back a value of type `dict[str, float]`.

```python
"""One request's stage times from the real path."""
```

- The docstring (documentation kept with the code) says: *One request's stage times from the real path.*

```python
events, _ = await collect(components, "run-trace", question)
done = next(event.data for event in events if event.name == "done")
return dict(done["timings"])
```

- `events, _ = await collect(components, "run-trace", question)`: unpacks the answer of the result of calling `collect(components, "run-trace", question)`, which is this repository's own `collect` (in `src/streaming_assistant/interfaces/measure.py`): run one question in process; returns the events and the refs that were retrieved for it once the wait is over into the names `events`, `_`, one item each.
- `done = next(event.data for event in events if event.name == "done")`: stores the result of calling `next(event.data for event in events if event.name == "done")`, which takes the next item from `(event.data for event in events if event.name == "done")` in `done`.
- `return dict(done["timings"])`: ends the function and gives back the result of calling `dict(done["timings"])`, which builds a dict.

```python
async def evaluate_questions(components: Components) -> dict[str, object]:
```

- Defines the async function `evaluate_questions` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `components`, type `Components`.
- Gives back a value of type `dict[str, object]`.

```python
"""All 200 questions: pauses, false pauses, citations shown outside the retrieved set, dropped citations."""
```

- The docstring (documentation kept with the code) says: *All 200 questions: pauses, false pauses, citations shown outside the retrieved set, dropped citations.*

```python
questions = [
    json.loads(line)
    for line in (components.settings.root / "data/questions.jsonl").read_text(encoding="utf-8").splitlines()
]
paused_should = paused_other = outside = right_page = answered = 0
```

- `questions = [ json.loads(line) for line in (components.settings.roo...`: stores a list built by running `json.loads(line)` for each `line` in `(components.settings.root / "data/questions.jsonl").read_text(encoding="utf-8").splitli...` in `questions`.
- `paused_should = paused_other = outside = right_page = answered = 0`: stores the number `0` in `paused_should`, `paused_other`, `outside`, `right_page`, `answered`.

```python
for number, item in enumerate(questions):
```

- Repeats the indented lines once for each item of `enumerate(questions)`, naming the current item the names `number`, `item`.

```python
events, retrieved = await collect(components, f"run-q{number:03d}", item["question"])
names = [event.name for event in events]
```

- `events, retrieved = await collect(components, f"run-q{number:03d}",...`: unpacks the answer of the result of calling `collect(components, f"run-q{number:03d}", item["question"])`, which is this repository's own `collect` (in `src/streaming_assistant/interfaces/measure.py`): run one question in process; returns the events and the refs that were retrieved for it once the wait is over into the names `events`, `retrieved`, one item each.
- `names = [event.name for event in events]`: stores a list built by running `event.name` for each `event` in `events` in `names`.

```python
if "paused" in names:
```

- Checks whether `"paused"` is among `names`. If so, the indented lines run.

```python
paused_should += item["should_pause"]
paused_other += not item["should_pause"]
continue
```

- `paused_should += item["should_pause"]`: adds `item["should_pause"]` to `paused_should` and keeps the result there.
- `paused_other += not item["should_pause"]`: adds `not item["should_pause"]` to `paused_other` and keeps the result there.
- `continue`: skips to the next round of the loop.

```python
shown = [event.data for event in events if event.name == "citation"]
outside += sum(f"{c['page_id']}#{c['anchor']}" not in retrieved for c in shown)
```

- `shown = [event.data for event in events if event.name == "citation"]`: stores a list built by running `event.data` for each `event` in `events` keeping only those where `event.name` equals `"citation"` in `shown`.
- `outside += sum(f"{c['page_id']}#{c['anchor']}" not in retrieved for...`: adds `sum(f"{c['page_id']}#{c['anchor']}" not in retrieved for c in shown)` to `outside` and keeps the result there.

```python
if not item["should_pause"]:
```

- Checks whether it is not the case that `item["should_pause"]` is true. If so, the indented lines run.

```python
answered += "token" in names
right_page += any(c["page_id"] == item["expected_page"] for c in shown)
```

- `answered += "token" in names`: adds `"token" in names` to `answered` and keeps the result there.
- `right_page += any(c["page_id"] == item["expected_page"] for c in sh...`: adds `any(c["page_id"] == item["expected_page"] for c in shown)` to `right_page` and keeps the result there.

```python
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
```

- `should = sum(q["should_pause"] for q in questions)`: stores the result of calling `sum(q["should_pause"] for q in questions)`, which adds up the numbers in `(q["should_pause"] for q in questions)` in `should`.
- `return { "questions": len(questions), "should_pause": should, "paus...`: ends the function and gives back a new dict with 10 entries.

```python
def free_port() -> int:
```

- Defines the function `free_port`.
- Gives back a value of type `int`.

```python
"""A port nothing is listening on (the measurements must not collide with services already on the machine)."""
```

- The docstring (documentation kept with the code) says: *A port nothing is listening on (the measurements must not collide with services already on the machine).*

```python
with socket.socket() as probe:
```

- Opens `socket.socket()` as `probe` for the indented lines, and cleans it up when they end (even after an error).

```python
probe.bind(("127.0.0.1", 0))
return int(probe.getsockname()[1])
```

- `probe.bind(("127.0.0.1", 0))`: calling `probe.bind(("127.0.0.1", 0))`, which attaches a socket to an address and port.
- `return int(probe.getsockname()[1])`: ends the function and gives back the result of calling `int(probe.getsockname()[1])`, which turns `probe.getsockname()[1]` into a whole number.

```python
class RunningServer:
```

- Defines the class `RunningServer`.

```python
"""uvicorn in a thread, for tests of behavior over a real socket."""
```

- The docstring (documentation kept with the code) says: *uvicorn in a thread, for tests of behavior over a real socket.*

```python
def __init__(self, components: Components, port: int) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `components`, type `Components`.
  - `port`, type `int`.
- Gives back a value of type `None`.

```python
app = create_app(
    components.assistant, components.desk, components.catalog, components.authenticator, components.audit
)
self._server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
self._thread = threading.Thread(target=self._server.run, daemon=True)
self.base = f"http://127.0.0.1:{port}"
```

- `app = create_app( components.assistant, components.desk, components...`: stores the result of calling `create_app( components.assistant, components.desk, components.catalog, components.authe...`, which is this repository's own `create_app` (in `src/streaming_assistant/interfaces/http.py`): build the app over the assistant and its collaborators in `app`.
- `self._server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1",...`: stores the result of calling `uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))`, which makes a `Server` object from `uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")` in `self._server`.
- `self._thread = threading.Thread(target=self._server.run, daemon=True)`: stores the result of calling `threading.Thread(target=self._server.run, daemon=True)`, which makes a `Thread` object with the named values `target`, `daemon` in `self._thread`.
- `self.base = f"http://127.0.0.1:{port}"`: stores the text built by the f-string `f"http://127.0.0.1:{port}"` in `self.base`.

```python
def __enter__(self) -> "RunningServer":
```

- Defines the special method `__enter__`, which Python calls itself at the right moment.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `"RunningServer"`.

```python
self._thread.start()
```

- `self._thread.start()`: calling `self._thread.start()`, which is this repository's own `start` (in `scripts/pause_demo.py`): start the server on a free port over the given database file and wait for /healthz.

```python
for _ in range(100):
```

- Repeats the indented lines once for each item of `range(100)`, naming the current item `_`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
if httpx.get(self.base + "/healthz", timeout=1).status_code == 200:
```

- Checks whether `httpx.get(self.base + "/healthz", timeout=1).status_code` equals `200`. If so, the indented lines run.

```python
return self
```

- `return self`: ends the function and gives back the value of `self`.

```python
except httpx.HTTPError:
```

- If an error of kind `httpx.HTTPError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
time.sleep(0.05)
```

- `time.sleep(0.05)`: calling `time.sleep(0.05)`, which waits `0.05` seconds.

```python
raise RuntimeError("server did not start")
```

- `raise RuntimeError("server did not start")`: stops with an error of kind `RuntimeError` with the message `"server did not start"`. Whoever called this code must handle it or the program stops.

```python
def __exit__(self, *exc: object) -> None:
```

- Defines the special method `__exit__`, which Python calls itself at the right moment.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `*exc`: collects extra positional arguments in a tuple.
- Gives back a value of type `None`.

```python
self._server.should_exit = True
self._thread.join(timeout=10)
```

- `self._server.should_exit = True`: stores `True` in `self._server.should_exit`.
- `self._thread.join(timeout=10)`: calling `self._thread.join(timeout=10)`, which glues the items of its argument together with `self._thread` between them The named values are `timeout`..

```python
async def first_event(client: httpx.AsyncClient, question: str) -> float:
```

- Defines the async function `first_event` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `client`, type `httpx.AsyncClient`.
  - `question`, type `str`.
- Gives back a value of type `float`.

```python
"""Seconds from sending the request until the first `token` event line arrives."""
```

- The docstring (documentation kept with the code) says: *Seconds from sending the request until the first `token` event line arrives.*

```python
started = time.perf_counter()
elapsed = float("nan")
```

- `started = time.perf_counter()`: stores the result of calling `time.perf_counter()`, which reads the high-resolution timer in seconds in `started`.
- `elapsed = float("nan")`: stores the result of calling `float("nan")`, which turns `"nan"` into a decimal number in `elapsed`.

```python
async with client.stream("POST", "/ask", json={"question": question}, headers=CUSTOMER) as response:
```

- Opens `client.stream("POST", "/ask", json={"question": question}, headers=CUSTOMER)` as `response` for the indented lines, and cleans it up when they end (even after an error).

```python
async for line in response.aiter_lines():  # read to the end so the connection closes cleanly
```

- Repeats the indented lines once for each item of `response.aiter_lines()`, naming the current item `line`. (`async for` waits for each item.)

```python
if line == "event: token" and elapsed != elapsed:  # NaN until the first token line
```

- Checks whether `line` equals `"event: token"` and `elapsed` is different from `elapsed`. If so, the indented lines run.

```python
elapsed = time.perf_counter() - started
```

- `elapsed = time.perf_counter() - started`: stores `time.perf_counter() - started`, which subtracts `time.perf_counter()` and `started` in `elapsed`.

```python
return elapsed
```

- `return elapsed`: ends the function and gives back the value of `elapsed`.

```python
async def stop_test(settings: Settings) -> dict[str, object]:
```

- Defines the async function `stop_test` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `settings`, type `Settings`.
- Gives back a value of type `dict[str, object]`.

```python
"""Close the connection after 3 tokens and look at the upstream call; then time an unrelated request."""
```

- The docstring (documentation kept with the code) says: *Close the connection after 3 tokens and look at the upstream call; then time an unrelated request.*

```python
model = ScriptedStreamingModel(
    Pace(ttft_standard_ms=80, ttft_fast_ms=40, prefill_ms_per_1k_tokens=0, token_ms=120, jitter=0)
)
components = build_components(replace(settings, database=":memory:"), model=model, fresh=True)
question = "A question about shipping times: standard delivery takes three to five business days after dispatch?"
```

- `model = ScriptedStreamingModel( Pace(ttft_standard_ms=80, ttft_fast...`: stores the result of calling `ScriptedStreamingModel( Pace(ttft_standard_ms=80, ttft_fast_ms=40, prefill_ms_per_1k_to...`, which is this repository's own `ScriptedStreamingModel` (in `src/streaming_assistant/infrastructure/scripted_stream.py`): async streaming with counters: tokens produced (what would be billed), cancellations and their times in `model`.
- `components = build_components(replace(settings, database=":memory:"...`: stores the result of calling `build_components(replace(settings, database=":memory:"), model=model, fresh=True)`, which is this repository's own `build_components` (in `src/streaming_assistant/interfaces/wiring.py`): wire everything The named values are `model`, `fresh`. in `components`.
- `question = "A question about shipping times: standard delivery take...`: stores the text `'A question about shipping times: standard delivery takes three to five business days a...` in `question`.

```python
with RunningServer(components, free_port()) as server:
```

- Opens `RunningServer(components, free_port())` as `server` for the indented lines, and cleans it up when they end (even after an error).

```python
async with httpx.AsyncClient(base_url=server.base, timeout=30) as client:
```

- Opens `httpx.AsyncClient(base_url=server.base, timeout=30)` as `client` for the indented lines, and cleans it up when they end (even after an error).

```python
baseline = [await first_event(client, question) for _ in range(5)]
tokens = 0
closed_at = 0.0
```

- `baseline = [await first_event(client, question) for _ in range(5)]`: stores a list built by running `await first_event(client, question)` for each `_` in `range(5)` in `baseline`.
- `tokens = 0`: stores the number `0` in `tokens`.
- `closed_at = 0.0`: stores the number `0.0` in `closed_at`.

```python
async with client.stream("POST", "/ask", json={"question": question}, headers=CUSTOMER) as response:
```

- Opens `client.stream("POST", "/ask", json={"question": question}, headers=CUSTOMER)` as `response` for the indented lines, and cleans it up when they end (even after an error).

```python
async for line in response.aiter_lines():
```

- Repeats the indented lines once for each item of `response.aiter_lines()`, naming the current item `line`. (`async for` waits for each item.)

```python
if line == "event: token":
```

- Checks whether `line` equals `"event: token"`. If so, the indented lines run.

```python
tokens += 1
```

- `tokens += 1`: adds `1` to `tokens` and keeps the result there.

```python
if tokens == 3:
```

- Checks whether `tokens` equals `3`. If so, the indented lines run.

```python
closed_at = time.perf_counter()
break
```

- `closed_at = time.perf_counter()`: stores the result of calling `time.perf_counter()`, which reads the high-resolution timer in seconds in `closed_at`.
- `break`: leaves the loop now.

```python
cancelled = 0.0
```

- `cancelled = 0.0`: stores the number `0.0` in `cancelled`.

```python
for _ in range(100):
```

- Repeats the indented lines once for each item of `range(100)`, naming the current item `_`.

```python
await asyncio.sleep(0.01)
```

- `await asyncio.sleep(0.01)`: waits for the result of calling `asyncio.sleep(0.01)`, which waits `0.01` seconds to finish.

```python
if model.cancelled_at:
```

- Checks whether `model.cancelled_at` is truthy. If so, the indented lines run.

```python
cancelled = model.cancelled_at[-1]
break
```

- `cancelled = model.cancelled_at[-1]`: stores the item `model.cancelled_at[-1]` in `cancelled`.
- `break`: leaves the loop now.

```python
produced_then = model.produced_tokens
await asyncio.sleep(0.8)
produced_later = model.produced_tokens
fresh = await first_event(
    client, "A question about gift wrapping: gift wrap is a checkout option for a small fee?"
)
```

- `produced_then = model.produced_tokens`: stores `model.produced_tokens` in `produced_then`.
- `await asyncio.sleep(0.8)`: waits for the result of calling `asyncio.sleep(0.8)`, which waits `0.8` seconds to finish.
- `produced_later = model.produced_tokens`: stores `model.produced_tokens` in `produced_later`.
- `fresh = await first_event( client, "A question about gift wrapping:...`: stores the answer of the result of calling `first_event( client, "A question about gift wrapping: gift wrap is a checkout option fo...`, which is this repository's own `first_event` (in `src/streaming_assistant/interfaces/measure.py`): seconds from sending the request until the first `token` event line arrives once the wait is over in `fresh`.

```python
return {
    "tokens_before_close": tokens,
    "upstream_cancelled_after_ms": round((cancelled - closed_at) * 1000, 1) if cancelled else None,
    "billed_tokens_when_cancelled": produced_then,
    "billed_tokens_800ms_later": produced_later,
    "baseline_first_token_ms": round(statistics.median(baseline) * 1000, 1),
    "fresh_request_after_stop_ms": round(fresh * 1000, 1),
}
```

- `return { "tokens_before_close": tokens, "upstream_cancelled_after_m...`: ends the function and gives back a new dict with 6 entries.

```python
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
```

- `CONFIGS: dict[str, dict[str, str]] = { "baseline": { "STABLE_PREFIX...`: stores a new dict with 4 entries in `CONFIGS`, whose type is declared as `dict[str, dict[str, str]]`.

```python
async def drive(base: str, questions: list[str], rps: float, duration: float) -> tuple[list[float], list[float], int]:
```

- Defines the async function `drive` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `base`, type `str`.
  - `questions`, type `list[str]`.
  - `rps`, type `float`.
  - `duration`, type `float`.
- Gives back a value of type `tuple[list[float], list[float], int]`.

```python
"""Send requests at a steady rate; returns client first-token seconds, server first-token ms and the request count."""
```

- The docstring (documentation kept with the code) says: *Send requests at a steady rate; returns client first-token seconds, server first-token ms and the request count.*

```python
client_times: list[float] = []
server_times: list[float] = []
```

- `client_times: list[float] = []`: stores a new list (empty) in `client_times`, whose type is declared as `list[float]`.
- `server_times: list[float] = []`: stores a new list (empty) in `server_times`, whose type is declared as `list[float]`.

```python
async def one(client: httpx.AsyncClient, question: str) -> None:
```

- Defines the async function `one` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `client`, type `httpx.AsyncClient`.
  - `question`, type `str`.
- Gives back a value of type `None`.

```python
started = time.perf_counter()
```

- `started = time.perf_counter()`: stores the result of calling `time.perf_counter()`, which reads the high-resolution timer in seconds in `started`.

```python
async with client.stream("POST", "/ask", json={"question": question}, headers=CUSTOMER) as response:
```

- Opens `client.stream("POST", "/ask", json={"question": question}, headers=CUSTOMER)` as `response` for the indented lines, and cleans it up when they end (even after an error).

```python
seen_first = False
event = ""
```

- `seen_first = False`: stores `False` in `seen_first`.
- `event = ""`: stores the empty text in `event`.

```python
async for line in response.aiter_lines():
```

- Repeats the indented lines once for each item of `response.aiter_lines()`, naming the current item `line`. (`async for` waits for each item.)

```python
if line.startswith("event: "):
```

- Checks whether `line.startswith("event: ")` is true (the call asks whether `line` begins with `"event: "`). If so, the indented lines run.

```python
event = line[7:]
```

- `event = line[7:]`: stores the item `line[7:]` in `event`.

```python
if event == "token" and not seen_first:
```

- Checks whether `event` equals `"token"` and it is not the case that `seen_first` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
client_times.append(time.perf_counter() - started)
seen_first = True
```

- `client_times.append(time.perf_counter() - started)`: calling `client_times.append(time.perf_counter() - started)`, which adds `time.perf_counter() - started` to the end of `client_times`.
- `seen_first = True`: stores `True` in `seen_first`.

```python
elif line.startswith("data: ") and event == "done":
```

- Otherwise, checks whether `line.startswith("data: ")` is true (the call asks whether `line` begins with `"data: "`) and `event` equals `"done"`. If so, the indented lines run.

```python
done = json.loads(line[6:])
```

- `done = json.loads(line[6:])`: stores the result of calling `json.loads(line[6:])`, which turns the JSON text `line[6:]` into Python values in `done`.

```python
if "first_token_ms" in done["timings"]:
```

- Checks whether `"first_token_ms"` is among `done["timings"]`. If so, the indented lines run.

```python
server_times.append(done["timings"]["first_token_ms"])
```

- `server_times.append(done["timings"]["first_token_ms"])`: calling `server_times.append(done["timings"]["first_token_ms"])`, which adds `done["timings"]["first_token_ms"]` to the end of `server_times`.

```python
async with httpx.AsyncClient(base_url=base, timeout=60) as client:
```

- Opens `httpx.AsyncClient(base_url=base, timeout=60)` as `client` for the indented lines, and cleans it up when they end (even after an error).

```python
tasks = []
total = int(rps * duration)
started = time.perf_counter()
```

- `tasks = []`: stores a new list (empty) in `tasks`.
- `total = int(rps * duration)`: stores the result of calling `int(rps * duration)`, which turns `rps * duration` into a whole number in `total`.
- `started = time.perf_counter()`: stores the result of calling `time.perf_counter()`, which reads the high-resolution timer in seconds in `started`.

```python
for index in range(total):
```

- Repeats the indented lines once for each item of `range(total)`, naming the current item `index`.

```python
tasks.append(asyncio.create_task(one(client, questions[index % len(questions)])))
delay = started + (index + 1) / rps - time.perf_counter()
```

- `tasks.append(asyncio.create_task(one(client, questions[index % len(...`: calling `tasks.append(asyncio.create_task(one(client, questions[index % len(questions)])))`, which adds `asyncio.create_task(one(client, questions[index % len(questions)]))` to the end of `tasks`.
- `delay = started + (index + 1) / rps - time.perf_counter()`: stores `started + (index + 1) / rps - time.perf_counter()`, which subtracts `started + (index + 1) / rps` and `time.perf_counter()` in `delay`.

```python
if delay > 0:
```

- Checks whether `delay` is greater than `0`. If so, the indented lines run.

```python
await asyncio.sleep(delay)
```

- `await asyncio.sleep(delay)`: waits for the result of calling `asyncio.sleep(delay)`, which waits `delay` seconds to finish.

```python
await asyncio.gather(*tasks)
```

- `await asyncio.gather(*tasks)`: waits for the result of calling `asyncio.gather(*tasks)`, which runs several coroutines at once and collects their answers to finish.

> **`*` and `**` in a call.** `f(*items)` passes the items of a list as separate arguments; `f(**mapping)` passes the entries of a dict as named arguments. In an unpacking `a, *rest = items`, the star collects the leftovers.

```python
return client_times, server_times, total
```

- `return client_times, server_times, total`: ends the function and gives back a tuple of 3 items.

```python
def load_test(settings: Settings, rps: float, duration: float) -> list[dict[str, object]]:
```

- Defines the function `load_test`.
- Parameters:
  - `settings`, type `Settings`.
  - `rps`, type `float`.
  - `duration`, type `float`.
- Gives back a value of type `list[dict[str, object]]`.

```python
"""Replay the answerable questions at `rps` for `duration` seconds against a server per configuration."""
```

- The docstring (documentation kept with the code) says: *Replay the answerable questions at `rps` for `duration` seconds against a server per configuration.*

```python
root = settings.root
questions = [
    item["question"]
    for item in (
        json.loads(line) for line in (root / "data/questions.jsonl").read_text(encoding="utf-8").splitlines()
    )
    if not item["should_pause"]
]
```

- `root = settings.root`: stores `settings.root` in `root`.
- `questions = [ item["question"] for item in ( json.loads(line) for l...`: stores a list built by running `item["question"]` for each `item` in `( json.loads(line) for line in (root / "data/questions.jsonl").read_text(encoding="utf-...` keeping only those where it is not the case that `item["should_pause"]` is true in `questions`.

```python
results = []
```

- `results = []`: stores a new list (empty) in `results`.

```python
for name, flags in CONFIGS.items():
```

- Repeats the indented lines once for each item of `CONFIGS.items()`, naming the current item the names `name`, `flags`.

```python
port = free_port()
env = {
    **os.environ,
    **flags,
    "PROJECT_ROOT": str(root),
    "PORT": str(port),
    "DATABASE": ":memory:",
    "LOG_LEVEL": "WARNING",
}
```

- `port = free_port()`: stores the result of calling `free_port()` in `port`.
- `env = { **os.environ, **flags, "PROJECT_ROOT": str(root), "PORT": s...`: stores a new dict with 6 entries in `env`.

```python
server = subprocess.Popen(
    [sys.executable, "-m", "streaming_assistant.interfaces.cli", "serve"], env=env, cwd=root
)
```

- `server = subprocess.Popen( [sys.executable, "-m", "streaming_assist...`: stores the result of calling `subprocess.Popen( [sys.executable, "-m", "streaming_assistant.interfaces.cli", "serve"]...`, which makes a `Popen` object from `[sys.executable, "-m", "streaming_assistant.interfaces.cli", "serve"]` with the named values `env`, `cwd` in `server`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
for _ in range(200):
```

- Repeats the indented lines once for each item of `range(200)`, naming the current item `_`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
if httpx.get(f"http://127.0.0.1:{port}/healthz", timeout=1).status_code == 200:
```

- Checks whether `httpx.get(f"http://127.0.0.1:{port}/healthz", timeout=1).status_code` equals `200`. If so, the indented lines run.

```python
break
```

- `break`: leaves the loop now.

```python
except httpx.HTTPError:
```

- If an error of kind `httpx.HTTPError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
time.sleep(0.1)
```

- `time.sleep(0.1)`: calling `time.sleep(0.1)`, which waits `0.1` seconds.

```python
client_times, server_times, total = asyncio.run(drive(f"http://127.0.0.1:{port}", questions, rps, duration))
```

- `client_times, server_times, total = asyncio.run(drive(f"http://127....`: unpacks the result of calling `asyncio.run(drive(f"http://127.0.0.1:{port}", questions, rps, duration))`, which runs a program or a coroutine into the names `client_times`, `server_times`, `total`, one item each.

```python
finally:
```

- Always runs last, whether or not an error happened. It is used to clean up.

```python
server.terminate()
server.wait(timeout=20)
```

- `server.terminate()`: calling `server.terminate()`.
- `server.wait(timeout=20)`: calling `server.wait(timeout=20)`, which waits for `server` The named values are `timeout`..

```python
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
```

- `results.append( { "config": name, "requests": total, "server_p50_ms...`: calling `results.append( { "config": name, "requests": total, "server_p50_ms": round(percentile(...`, which adds `{ "config": name, "requests": total, "server_p50_ms": round(percentile(server_times, 0....` to the end of `results`.

```python
return results
```

- `return results`: ends the function and gives back the value of `results`.

#### `src/streaming_assistant/interfaces/wiring.py`

```python
"""Compose the database, retriever, model and assistant the settings ask for."""
```

- The docstring (documentation kept with the code) says: *Compose the database, retriever, model and assistant the settings ask for.*

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from streaming_assistant.application.assistant import Assistant, AssistantConfig, StopRegistry
from streaming_assistant.application.ports import Retriever, StreamingModel
from streaming_assistant.application.prompts import parse_prompt_file
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from streaming_assistant.application.assistant import ...`: takes names from `streaming_assistant.application.assistant`, this repository's own code. (`Assistant`: Orchestrates one request.) (`AssistantConfig`: Behavior switches.) (`StopRegistry`: Run ids a user asked to stop, safe to use from any thread.)
- `from streaming_assistant.application.ports import ...`: takes names from `streaming_assistant.application.ports`, this repository's own code. (`Retriever`: Finds the help sections for a question.) (`StreamingModel`: A model that streams.)
- `from streaming_assistant.application.prompts import ...`: takes names from `streaming_assistant.application.prompts`, this repository's own code. (`parse_prompt_file`: Split `---`, header lines, `---`, then the prompt text; both fences are required.)

```python
from streaming_assistant.application.review import ReviewDesk
from streaming_assistant.domain.routing import Thresholds
from streaming_assistant.infrastructure.catalog import CachingRetriever, LazyBm25Retriever, PageCatalog
from streaming_assistant.infrastructure.claude_stream import ClaudeStreamingModel
from streaming_assistant.infrastructure.clock import SystemClock
from streaming_assistant.infrastructure.recorded_stream import RecordedStreamingModel
```

- `from streaming_assistant.application.review import ...`: takes names from `streaming_assistant.application.review`, this repository's own code. (`ReviewDesk`: Lists waiting runs and validates a reviewer's answer: not empty, and either citing a real section or saying that no page covers the question.)
- `from streaming_assistant.domain.routing import ...`: takes names from `streaming_assistant.domain.routing`, this repository's own code. (`Thresholds`: Retrieval coverage at which a question is answered, called thin, or sent to a person.)
- `from streaming_assistant.infrastructure.catalog import ...`: takes names from `streaming_assistant.infrastructure.catalog`, this repository's own code. (`CachingRetriever`: A small LRU cache in front of a retriever, keyed by the normalized query.) (`LazyBm25Retriever`: Builds the index on the first search (the cold start the budget must account for); `warm` builds it ahead of time.) (`PageCatalog`: Loads `data/help_pages.json`: 30 pages with titled sections.)
- `from streaming_assistant.infrastructure.claude_stream import ...`: takes names from `streaming_assistant.infrastructure.claude_stream`, this repository's own code. (`ClaudeStreamingModel`: One streamed Messages API call.)
- `from streaming_assistant.infrastructure.clock import ...`: takes names from `streaming_assistant.infrastructure.clock`, this repository's own code. (`SystemClock`: Now, in UTC.)
- `from streaming_assistant.infrastructure.recorded_stream import ...`: takes names from `streaming_assistant.infrastructure.recorded_stream`, this repository's own code. (`RecordedStreamingModel`: Replays the recorded pieces; a request with no recording fails loudly.)

```python
from streaming_assistant.infrastructure.scripted_stream import Pace, ScriptedStreamingModel
from streaming_assistant.infrastructure.settings import Settings
from streaming_assistant.infrastructure.sqlite_store import Database, SqliteAudit, SqliteAuthenticator, SqliteRunStore
```

- `from streaming_assistant.infrastructure.scripted_stream import ...`: takes names from `streaming_assistant.infrastructure.scripted_stream`, this repository's own code. (`Pace`: Latency settings in milliseconds.) (`ScriptedStreamingModel`: Async streaming with counters: tokens produced (what would be billed), cancellations and their times.)
- `from streaming_assistant.infrastructure.settings import ...`: takes names from `streaming_assistant.infrastructure.settings`, this repository's own code. (`Settings`: Everything the programs read from the environment.)
- `from streaming_assistant.infrastructure.sqlite_store import ...`: takes names from `streaming_assistant.infrastructure.sqlite_store`, this repository's own code. (`Database`: One SQLite file behind a lock; every operation is a short transaction.) (`SqliteAudit`: The audit log.) (`SqliteAuthenticator`: Looks a bearer token up by its hash.) (`SqliteRunStore`: Paused runs.)

```python
@dataclass(frozen=True, slots=True)
class Components:
```

- Defines the class `Components`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""Everything a command needs."""
```

- The docstring (documentation kept with the code) says: *Everything a command needs.*

```python
settings: Settings
database: Database
catalog: PageCatalog
retriever: Retriever
lazy: LazyBm25Retriever
model: StreamingModel
assistant: Assistant
desk: ReviewDesk
```

- `settings: Settings`: a field named `settings` of type `Settings`, no default (must be given).
- `database: Database`: a field named `database` of type `Database`, no default (must be given).
- `catalog: PageCatalog`: a field named `catalog` of type `PageCatalog`, no default (must be given).
- `retriever: Retriever`: a field named `retriever` of type `Retriever`, no default (must be given).
- `lazy: LazyBm25Retriever`: a field named `lazy` of type `LazyBm25Retriever`, no default (must be given).
- `model: StreamingModel`: a field named `model` of type `StreamingModel`, no default (must be given).
- `assistant: Assistant`: a field named `assistant` of type `Assistant`, no default (must be given).
- `desk: ReviewDesk`: a field named `desk` of type `ReviewDesk`, no default (must be given).

```python
audit: SqliteAudit
authenticator: SqliteAuthenticator
runs: SqliteRunStore
```

- `audit: SqliteAudit`: a field named `audit` of type `SqliteAudit`, no default (must be given).
- `authenticator: SqliteAuthenticator`: a field named `authenticator` of type `SqliteAuthenticator`, no default (must be given).
- `runs: SqliteRunStore`: a field named `runs` of type `SqliteRunStore`, no default (must be given).

```python
def build_model(settings: Settings) -> StreamingModel:
```

- Defines the function `build_model`.
- Parameters:
  - `settings`, type `Settings`.
- Gives back a value of type `StreamingModel`.

```python
"""The scripted model (offline, with the pace from the settings), the recorded one, or Claude."""
```

- The docstring (documentation kept with the code) says: *The scripted model (offline, with the pace from the settings), the recorded one, or Claude.*

```python
if settings.model_adapter == "claude":
```

- Checks whether `settings.model_adapter` equals `"claude"`. If so, the indented lines run.

```python
return ClaudeStreamingModel(settings.model_ids, settings.anthropic_api_key)
```

- `return ClaudeStreamingModel(settings.model_ids, settings.anthropic_...`: ends the function and gives back the result of calling `ClaudeStreamingModel(settings.model_ids, settings.anthropic_api_key)`, which is this repository's own `ClaudeStreamingModel` (in `src/streaming_assistant/infrastructure/claude_stream.py`): one streamed Messages API call.

```python
if settings.model_adapter == "recorded":
```

- Checks whether `settings.model_adapter` equals `"recorded"`. If so, the indented lines run.

```python
return RecordedStreamingModel(settings.root / settings.cassette)
```

- `return RecordedStreamingModel(settings.root / settings.cassette)`: ends the function and gives back the result of calling `RecordedStreamingModel(settings.root / settings.cassette)`, which is this repository's own `RecordedStreamingModel` (in `src/streaming_assistant/infrastructure/recorded_stream.py`): replays the recorded pieces; a request with no recording fails loudly.

```python
return ScriptedStreamingModel(Pace(settings.ttft_standard_ms, settings.ttft_fast_ms, token_ms=settings.token_ms))
```

- `return ScriptedStreamingModel(Pace(settings.ttft_standard_ms, setti...`: ends the function and gives back the result of calling `ScriptedStreamingModel(Pace(settings.ttft_standard_ms, settings.ttft_fast_ms, token_ms=...`, which is this repository's own `ScriptedStreamingModel` (in `src/streaming_assistant/infrastructure/scripted_stream.py`): async streaming with counters: tokens produced (what would be billed), cancellations and their times.

```python
def build_components(
    settings: Settings, *, database: Database | None = None, model: StreamingModel | None = None, fresh: bool = False
) -> Components:
```

- Defines the function `build_components`.
- Parameters:
  - `settings`, type `Settings`.
  - `database`, type `Database | None`, optional (default `None`). Must be passed by name.
  - `model`, type `StreamingModel | None`, optional (default `None`). Must be passed by name.
  - `fresh`, type `bool`, optional (default `False`). Must be passed by name.
- Gives back a value of type `Components`.

```python
"""Wire everything. `fresh` rebuilds the database from the SQL scripts (a new file or `:memory:`)."""
```

- The docstring (documentation kept with the code) says: *Wire everything. `fresh` rebuilds the database from the SQL scripts (a new file or `:memory:`).*

```python
root = settings.root
db = database or Database(root / settings.database if settings.database != ":memory:" else ":memory:")
```

- `root = settings.root`: stores `settings.root` in `root`.
- `db = database or Database(root / settings.database if settings.data...`: stores `database or Database(root / settings.database if settings.database != ":memory:" else "...` (the first operand that decides the or) in `db`.

```python
if fresh:
```

- Checks whether `fresh` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
db.apply_scripts(root / "sql")
```

- `db.apply_scripts(root / "sql")`: calling `db.apply_scripts(root / "sql")`, which is this repository's own `apply_scripts` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run the numbered scripts (DDL, then seed); returns the names that ran.

```python
catalog = PageCatalog(root / "data/help_pages.json")
lazy = LazyBm25Retriever(catalog)
```

- `catalog = PageCatalog(root / "data/help_pages.json")`: stores the result of calling `PageCatalog(root / "data/help_pages.json")`, which is this repository's own `PageCatalog` (in `src/streaming_assistant/infrastructure/catalog.py`): loads `data/help_pages.json`: 30 pages with titled sections in `catalog`.
- `lazy = LazyBm25Retriever(catalog)`: stores the result of calling `LazyBm25Retriever(catalog)`, which is this repository's own `LazyBm25Retriever` (in `src/streaming_assistant/infrastructure/catalog.py`): builds the index on the first search (the cold start the budget must account for); `warm` builds it ahead of time in `lazy`.

```python
if settings.warm_index:
```

- Checks whether `settings.warm_index` is truthy. If so, the indented lines run.

```python
lazy.warm()
```

- `lazy.warm()`: calling `lazy.warm()`, which is this repository's own `warm` (in `src/streaming_assistant/infrastructure/catalog.py`): build the index now.

```python
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
```

- `retriever: Retriever = CachingRetriever(lazy) if settings.cache_ret...`: stores `CachingRetriever(lazy)` when `settings.cache_retrieval` is truthy, otherwise `lazy` in `retriever`, whose type is declared as `Retriever`.
- `chosen = model or build_model(settings)`: stores `model or build_model(settings)` (the first operand that decides the or) in `chosen`.
- `clock, audit, runs = SystemClock(), SqliteAudit(db), SqliteRunStore...`: unpacks a tuple of 3 items into the names `clock`, `audit`, `runs`, one item each.
- `authenticator = SqliteAuthenticator(db)`: stores the result of calling `SqliteAuthenticator(db)`, which is this repository's own `SqliteAuthenticator` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): looks a bearer token up by its hash in `authenticator`.
- `prompt = parse_prompt_file("answer", (root / "prompts/answer.v1.md"...`: stores the result of calling `parse_prompt_file("answer", (root / "prompts/answer.v1.md").read_text(encoding="utf-8"))`, which is this repository's own `parse_prompt_file` (in `src/streaming_assistant/application/prompts.py`): split `---`, header lines, `---`, then the prompt text; both fences are required in `prompt`.
- `config = AssistantConfig( stable_prompt=prompt.text, thresholds=Thr...`: stores the result of calling `AssistantConfig( stable_prompt=prompt.text, thresholds=Thresholds(), first_token_timeou...`, which is this repository's own `AssistantConfig` (in `src/streaming_assistant/application/assistant.py`): behavior switches in `config`.

```python
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
```

- `assistant = Assistant( retriever, {"standard": chosen, "fast": chos...`: stores the result of calling `Assistant( retriever, {"standard": chosen, "fast": chosen}, runs, audit, authenticator,...`, which is this repository's own `Assistant` (in `src/streaming_assistant/application/assistant.py`): orchestrates one request in `assistant`.

```python
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
```

- `return Components( settings, db, catalog, retriever, lazy, chosen, ...`: ends the function and gives back the result of calling `Components( settings, db, catalog, retriever, lazy, chosen, assistant, ReviewDesk(runs,...`, which is this repository's own `Components` (in `src/streaming_assistant/interfaces/wiring.py`): everything a command needs.

```python
def database_exists(settings: Settings) -> bool:
```

- Defines the function `database_exists`.
- Parameters:
  - `settings`, type `Settings`.
- Gives back a value of type `bool`.

```python
"""True when the database file is already there (an in-memory database never is: it starts empty)."""
```

- The docstring (documentation kept with the code) says: *True when the database file is already there (an in-memory database never is: it starts empty).*

```python
return settings.database != ":memory:" and Path(settings.root / settings.database).exists()
```

- `return settings.database != ":memory:" and Path(settings.root / set...`: ends the function and gives back `settings.database != ":memory:" and Path(settings.root / settings.database).exists()` (the first operand that decides the and).

<!-- /fullwalk -->

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/python --version
```

Prints the interpreter version: `Python 3.13.12` on the machine this was written on. Any 3.12 or newer works.

```bash
.venv/bin/python -c "import streaming_assistant; print(streaming_assistant.__file__)"
```

Prints the path of `src/streaming_assistant/__init__.py`. This shows the editable install: Python imports the package straight from the `src` folder.

```bash
.venv/bin/python -c "import sys; print(sys.prefix)"
```

Prints the path of the `.venv` folder, which proves this is the private environment and not the system Python.

```bash
grep -c 'def ' src/streaming_assistant/domain/*.py | head -5
```

Counts the function definitions in a few domain modules (a quick way to see how much logic the layer holds).

## Mistakes people make

- Mixing the system Python with project packages. This repository always runs `.venv/bin/python`, the Python of its private virtual environment, so the packages it needs are exactly the pinned ones.
- Using a mutable default argument, such as `def f(items=[])`. The list is created once and shared by every call. The code here uses `field(default_factory=list)` in dataclasses and `None` defaults instead.
- Catching every exception with a bare `except:`. That hides real bugs. The code catches the specific exception types it expects.
- Comparing money or other exact amounts with floating-point numbers. `0.1 + 0.2` is not exactly `0.3`. Where exactness matters the code keeps the amount as text or uses `Decimal`.
- Forgetting that indentation is part of the syntax. A block is whatever is indented under its `:` line.

## Check yourself

1. What is the difference between a module and a package?
   *Answer:* A module is one `.py` file. A package is a folder of modules that contains an `__init__.py` file.
2. Does Python check type hints while the program runs?
   *Answer:* No. It stores them but ignores them. A separate tool such as `mypy` checks them before the program runs.
3. What does `import x` do the first time it runs for a module?
   *Answer:* It finds the module on `sys.path`, runs its top-level code once, and keeps the result so later imports reuse it.
4. Why does the repository run `.venv/bin/python` and not just `python`?
   *Answer:* So the program uses the private virtual environment with the pinned package versions, not whatever happens to be installed on the machine.
5. What is an exception, and how do you stop one from ending the program?
   *Answer:* An error object that interrupts the normal flow. Wrap the risky code in `try:` and handle the type you expect in `except ThatType:`.

## Further reading

- [The Python 3.12 tutorial](https://docs.python.org/3.12/tutorial/)
- [The Python 3.12 language reference](https://docs.python.org/3.12/reference/)
- [The Python 3.12 standard library](https://docs.python.org/3.12/library/)
- [What is new in Python 3.12](https://docs.python.org/3.12/whatsnew/3.12.html)
