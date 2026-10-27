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
