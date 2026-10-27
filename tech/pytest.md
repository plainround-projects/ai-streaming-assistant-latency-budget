# pytest

## What it is

`pytest` is the most used Python test runner. A *test* is a small function that runs a piece of the program and checks the result with `assert`. `pytest` finds the tests, runs them, and tells you which passed and which failed and why.

## Why this repository uses it

The tests are the evidence for every claim in the README. They run offline against fakes, so they pass on any machine without a key. There are 5 test files; the Done-when lines of the lesson each have a test or a command.

## Where it appears

| File | What it does with pytest |
| --- | --- |
| `tests/` | the tests |
| `pyproject.toml` (`[tool.pytest.ini_options]`) | paths, options, markers |
| `Makefile` (`test`...) | the commands |

## How it works underneath

`pytest` looks in the folders named in `testpaths` for files called `test_*.py`, imports them, and treats every function called `test_*` as a test. A plain `assert x == y` is enough: `pytest` rewrites the assertion when the file is imported so that a failure prints the two values and where they differ.

A *fixture* is a function marked `@pytest.fixture` that prepares something a test needs (a database, a temporary folder). A test asks for it by naming it as a parameter, and `pytest` supplies it. `@pytest.mark.parametrize` runs one test with several inputs. A *marker* such as `@pytest.mark.live` labels a test so you can select or skip groups with `-m`. With `--strict-markers` a marker that is not registered in `pyproject.toml` is an error.

`pytest.raises(SomeError)` checks that code fails the way it should. `capsys` captures what a program prints so a test can check it. `monkeypatch` changes an environment variable or function for one test and undoes it afterwards. A test passes if it finishes without an exception; it fails on an exception or a failed `assert`.

## Walkthrough of this repository's use

### Where the tests live

| Folder | Test files | Examples |
| --- | --- | --- |
| `tests/unit/` | 4 | test_assistant.py, test_domain.py, test_adapters.py, test_http_and_cli.py |
| `tests/live/` | 1 | test_claude_live.py |

### The settings

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"
markers = [
    "live: calls the real model; needs ANTHROPIC_API_KEY and RUN_LIVE=1 (make test-live)",
    "load: starts a server and sends requests for several seconds (make load-test)",
]
```

- `[tool.pytest.ini_options]`: Settings for `pytest`, the test runner.
- `testpaths = ["tests"]`: Look for tests in the `tests` folder when `pytest` runs with no arguments.
- `addopts = "-ra --strict-markers"`: Options added to every run. `-ra` prints a short reason for every test that did not simply pass. `--strict-markers` makes an unknown marker name an error, so a typo cannot silently skip a test.
- `markers = [`: The list of marker names the tests may use. A marker is a label attached to a test with `@pytest.mark.name`.
- `"live: calls the real model; needs ANTHROPIC_API_KEY and RUN_LIVE=1 (make test-live)",`: Registers the marker `live`. Its description says: calls the real model; needs ANTHROPIC_API_KEY and RUN_LIVE=1 (make test-live)
- `"load: starts a server and sends requests for several seconds (make load-test)",`: Registers the marker `load`. Its description says: starts a server and sends requests for several seconds (make load-test)

### The commands

```make
test: install ## offline tests with coverage; domain and application stay at 95% or more
	$(PY) -m pytest tests -m "not live" --cov=$(PKG) --cov-report=term
	$(PY) -m coverage report --include='src/$(PKG)/domain/*,src/$(PKG)/application/*' --fail-under=95
```

- `test: install ## offline tests with coverage; domain and application stay at 95% or more`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(PY) -m pytest tests -m "not live" --cov=$(PKG) --cov-report=term`: Run the tests with pytest, using the virtual environment's Python (`-m` runs a module). The options: `tests -m "not live" --cov=$(PKG) --cov-report=term`.
- `$(PY) -m coverage report --include='src/$(PKG)/domain/*,src/$(PKG)/application/*' --fail-under=95`: Print the coverage of the domain and application layers only (`--include`) and exit with an error if it is below 95 percent.

```make
test-live: install ## the opt-in test that calls the real model (needs ANTHROPIC_API_KEY)
	RUN_LIVE=1 $(PY) -m pytest tests/live -m live
```

- `test-live: install ## the opt-in test that calls the real model (needs ANTHROPIC_API_KEY)`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `RUN_LIVE=1 $(PY) -m pytest tests/live -m live`: Put `RUN_LIVE=1` in the environment of this one command, then run only tests marked `live`. The live test refuses to run unless this variable is set.

### A test, line by line

From `tests/unit/application/test_assistant.py`:

```python
def test_an_answerable_question_streams_tokens_then_citations_then_done_with_usage_and_timings():
    events = asyncio.run(Rig().ask(SHIPPING))
    assert names(events)[0] == "token" and names(events)[-1] == "done"
    assert "citation" in names(events) and "[" not in "".join(e.data["text"] for e in events if e.name == "token")
    done = events[-1].data
    assert done["outcome"] == "answered" and done["usage"]["output_tokens"] > 0 and done["dropped_citations"] == 0
    timings = done["timings"]
    assert abs(timings["first_token_ms"] - timings["stage_sum_ms"]) < TRACE_TOLERANCE_MS
```

- `def test_an_answerable_question_streams_tokens_then_citations_then_done_with_usage_and_timings():`: A test: the name starts with `test_`, so pytest runs it, and the name says what it checks. The parameters are *fixtures* that pytest supplies by name.
- `events = asyncio.run(Rig().ask(SHIPPING))`: Prepares `events` as `asyncio.run(Rig().ask(SHIPPING))`.
- `assert names(events)[0] == "token" and names(events)[-1] == "done"`: The check: if the expression is false the test fails, and pytest prints both sides.
- `assert "citation" in names(events) and "[" not in "".join(e.data["text"] for e in events if e.name == "token")`: The check: if the expression is false the test fails, and pytest prints both sides.
- `done = events[-1].data`: Prepares `done` as `events[-1].data`.
- `assert done["outcome"] == "answered" and done["usage"]["output_tokens"] > 0 and done["dropped_citations"] == 0`: The check: if the expression is false the test fails, and pytest prints both sides.
- `timings = done["timings"]`: Prepares `timings` as `done["timings"]`.
- `assert abs(timings["first_token_ms"] - timings["stage_sum_ms"]) < TRACE_TOLERANCE_MS`: The check: if the expression is false the test fails, and pytest prints both sides.

```python
def test_the_stage_times_add_up_to_the_first_token_time_with_and_without_parallel_prep():
    for parallel in (True, False):
```

- `def test_the_stage_times_add_up_to_the_first_token_time_with_and_without_parallel_prep():`: A test: the name starts with `test_`, so pytest runs it, and the name says what it checks. The parameters are *fixtures* that pytest supplies by name.
- `for parallel in (True, False):`: A step of the test (the statement continues or calls the code under test).


<!-- fullwalk -->
### Every test file, statement by statement

This part quotes every file under `tests/`, in the order git lists them, and says in plain words what each statement does. A test is a small program that runs a piece of the repository with chosen inputs and checks the result with `assert`.

#### `tests/__init__.py`

This file is empty. Its presence tells Python that the folder is a package.

#### `tests/e2e/__init__.py`

This file is empty. Its presence tells Python that the folder is a package.

#### `tests/integration/__init__.py`

This file is empty. Its presence tells Python that the folder is a package.

#### `tests/live/test_claude_live.py`

```python
"""Opt-in: streams one real answer and closes a second stream early. Run with `make test-live` (RUN_LIVE=1 and a key)."""
```

- The docstring (documentation kept with the code) says: *Opt-in: streams one real answer and closes a second stream early. Run with `make test-live` (RUN_LIVE=1 and a key).*

> **A Python file is a module.** When another file writes `import` or `from ... import`, Python runs this file once and hands over the names it defines. A docstring is a string that sits first in a module, class or function; Python keeps it as the documentation of that thing.

```python
import asyncio
import os

import pytest

from streaming_assistant.application.ports import StreamRequest, TextDelta, Usage
from streaming_assistant.infrastructure.claude_stream import ClaudeStreamingModel

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("RUN_LIVE") != "1" or not os.environ.get("ANTHROPIC_API_KEY"),
        reason="set RUN_LIVE=1 and ANTHROPIC_API_KEY to call the real model",
    ),
]
```

- `import asyncio`: makes the module `asyncio` available (the standard library's tools for asynchronous code (many waits interleaved on one thread)).
- `import os`: makes the module `os` available (operating-system services: environment variables, paths, processes).
- `import pytest`: makes the module `pytest` available (the test framework).
- `from streaming_assistant.application.ports import ...`: takes names from `streaming_assistant.application.ports`, this repository's own code. (`StreamRequest`: One streamed completion.) (`TextDelta`: A piece of the answer.) (`Usage`: Token counts, sent when the stream ends normally.)
- `from streaming_assistant.infrastructure.claude_stream import ...`: takes names from `streaming_assistant.infrastructure.claude_stream`, this repository's own code. (`ClaudeStreamingModel`: One streamed Messages API call.)
- `pytestmark = [ pytest.mark.live, pytest.mark.skipif( os.environ.get...`: stores a new list holding 2 items in `pytestmark`.

> **`import` and `from ... import`.** `import x` makes the module `x` available under that name. `from x import y` fetches only the name `y` from `x` so it can be used without the prefix. `as` renames what you import. Imports at the top mean: this file needs those things from elsewhere.

> **A name is a label for a value.** `x = 5` makes the name `x` point to the value 5. Names are not boxes with a fixed type; Python looks at the value at run time. A name written in CAPITALS by habit marks a constant: nobody should change it.

```python
REQUEST = StreamRequest(
    "Answer in one short sentence and cite the passage as [help-01#shipping-times].",
    "Passages:\n[help-01#shipping-times] Shipping times: Standard delivery takes three to five days.\nQuestion: How long is delivery?",
    "answer.v1",
)
```

- `REQUEST = StreamRequest( "Answer in one short sentence and cite the...`: stores the result of calling `StreamRequest( "Answer in one short sentence and cite the passage as [help-01#shipping-...`, which is this repository's own `StreamRequest` (in `src/streaming_assistant/application/ports.py`): one streamed completion in `REQUEST`.

```python
def model() -> ClaudeStreamingModel:
```

- Defines the function `model`.
- Gives back a value of type `ClaudeStreamingModel`.

> **A function.** `def name(parameters):` defines a reusable block of code. The indented lines below it are the body; they run each time the function is called. `return` ends the call and hands a value back. A function that reaches its end without `return` hands back `None`, Python's 'nothing'.

```python
return ClaudeStreamingModel(
    {"standard": os.environ.get("MODEL_ID", "claude-sonnet-5-5"), "fast": "claude-haiku-5-5"},
    os.environ["ANTHROPIC_API_KEY"],
)
```

- `return ClaudeStreamingModel( {"standard": os.environ.get("MODEL_ID"...`: ends the function and gives back the result of calling `ClaudeStreamingModel( {"standard": os.environ.get("MODEL_ID", "claude-sonnet-5-5"), "fa...`, which is this repository's own `ClaudeStreamingModel` (in `src/streaming_assistant/infrastructure/claude_stream.py`): one streamed Messages API call.

```python
def test_the_real_model_streams_text_then_usage():
```

- Defines the test `test_the_real_model_streams_text_then_usage`.

> **A pytest test.** pytest finds every function whose name starts with `test_` in a file whose name starts with `test_`, calls it, and counts it as passed if it returns without an error. The parameters of a test are *fixtures*: pytest looks each name up and passes in the value the fixture makes.

```python
async def go():
```

- Defines the async function `go` (a coroutine: calling it makes a job for the event loop to run).

> **`async def` and `await`.** An `async def` function is a coroutine: calling it does not run the body but makes an object that the event loop runs. `await` inside it pauses this function until the awaited thing is ready, and lets the loop run other work meanwhile, all on one thread.

```python
return [chunk async for chunk in model().stream(REQUEST)]
```

- `return [chunk async for chunk in model().stream(REQUEST)]`: ends the function and gives back a list built by running `chunk` for each `chunk` in `model().stream(REQUEST)`.

> **Comprehensions.** `[f(x) for x in items if test(x)]` builds a new list: run `f` on every item that passes the test. With `{k: v for ...}` it builds a dict, with `{x for ...}` a set. With round brackets it is a generator expression: the values are produced one at a time, only when something asks for the next one.

```python
chunks = asyncio.run(go())
assert any(isinstance(c, TextDelta) and c.text for c in chunks) and isinstance(chunks[-1], Usage)
assert "help-01#shipping-times" in "".join(c.text for c in chunks if isinstance(c, TextDelta))
```

- `chunks = asyncio.run(go())`: stores the result of calling `asyncio.run(go())`, which runs a program or a coroutine in `chunks`.
- `assert any(isinstance(c, TextDelta) and c.text for c in chunks) and...`: checks that `any(isinstance(c, TextDelta) and c.text for c in chunks)` is true (the call is true if at least one item of `(isinstance(c, TextDelta) and c.text for c in chunks)` is true) and `isinstance(chunks[-1], Usage)` is true (the call asks whether `chunks[-1]` is a `Usage`). A false check stops the test as failed.
- `assert "help-01#shipping-times" in "".join(c.text for c in chunks i...`: checks that `"help-01#shipping-times"` is among `"".join(c.text for c in chunks if isinstance(c, TextDelta))`. A false check stops the test as failed.

> **`assert`.** `assert condition` does nothing when the condition is true and stops with an `AssertionError` when it is false. In a test file, a failing assert is how a test fails. `pytest` rewrites assert lines so its failure message shows the values involved.

> **Operators.** `//` divides and rounds down; `%` is the remainder; `**` is the power; `a and b` / `a or b` / `not a` combine conditions and stop at the first answer that decides the result; `x in items` asks whether `x` is among them; `x is None` asks whether it is exactly `None`.

```python
def test_closing_the_stream_early_ends_the_call_without_an_error():
```

- Defines the test `test_closing_the_stream_early_ends_the_call_without_an_error`.

```python
async def go():
```

- Defines the async function `go` (a coroutine: calling it makes a job for the event loop to run).

```python
stream = aiter(model().stream(REQUEST))
first = await anext(stream)
await stream.aclose()  # type: ignore[attr-defined]
return first
```

- `stream = aiter(model().stream(REQUEST))`: stores the result of calling `aiter(model().stream(REQUEST))` in `stream`.
- `first = await anext(stream)`: stores the answer of the result of calling `anext(stream)` once the wait is over in `first`.
- `await stream.aclose()`: waits for the result of calling `stream.aclose()` to finish.
- `return first`: ends the function and gives back the value of `first`.

```python
assert isinstance(asyncio.run(go()), TextDelta)
```

- `assert isinstance(asyncio.run(go()), TextDelta)`: checks that `isinstance(asyncio.run(go()), TextDelta)` is true (the call asks whether `asyncio.run(go())` is a `TextDelta`). A false check stops the test as failed.

#### `tests/unit/__init__.py`

This file is empty. Its presence tells Python that the folder is a package.

#### `tests/unit/application/test_assistant.py`

- This file has no docstring at the top.

```python
import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from streaming_assistant.application.assistant import STATES, Assistant, AssistantConfig, UnauthorizedError
```

- `import asyncio`: makes the module `asyncio` available (the standard library's tools for asynchronous code (many waits interleaved on one thread)).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`AsyncIterator`: a name provided by that module.)
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `import pytest`: makes the module `pytest` available (the test framework).
- `from streaming_assistant.application.assistant import ...`: takes names from `streaming_assistant.application.assistant`, this repository's own code. (`STATES`: a name defined in this repository.) (`Assistant`: Orchestrates one request.) (`AssistantConfig`: Behavior switches.) (`UnauthorizedError`: The bearer token is missing or unknown.)

```python
from streaming_assistant.application.ports import Chunk, StreamRequest, TextDelta, Usage
from streaming_assistant.application.prompt import PROMPT_VERSION, assemble
from streaming_assistant.application.prompts import PromptFileError, parse_prompt_file
from streaming_assistant.application.review import ReviewDesk
from streaming_assistant.domain.audit import verify
from streaming_assistant.domain.errors import ProviderError, ReviewRejectedError, UnknownRunError
```

- `from streaming_assistant.application.ports import ...`: takes names from `streaming_assistant.application.ports`, this repository's own code. (`Chunk`: a name defined in this repository.) (`StreamRequest`: One streamed completion.) (`TextDelta`: A piece of the answer.) (`Usage`: Token counts, sent when the stream ends normally.)
- `from streaming_assistant.application.prompt import ...`: takes names from `streaming_assistant.application.prompt`, this repository's own code. (`PROMPT_VERSION`: a name defined in this repository.) (`assemble`: Stable instructions first (cacheable, the same for every request), then the passages and the question.)
- `from streaming_assistant.application.prompts import ...`: takes names from `streaming_assistant.application.prompts`, this repository's own code. (`PromptFileError`: A prompt file does not have the two-fence header with a version and an owner.) (`parse_prompt_file`: Split `---`, header lines, `---`, then the prompt text; both fences are required.)
- `from streaming_assistant.application.review import ...`: takes names from `streaming_assistant.application.review`, this repository's own code. (`ReviewDesk`: Lists waiting runs and validates a reviewer's answer: not empty, and either citing a real section or saying that no page covers the question.)
- `from streaming_assistant.domain.audit import ...`: takes names from `streaming_assistant.domain.audit`, this repository's own code. (`verify`: Index of the first entry that was edited, removed or reordered; None when the chain holds.)
- `from streaming_assistant.domain.errors import ...`: takes names from `streaming_assistant.domain.errors`, this repository's own code. (`ProviderError`: The model provider failed (a server error or a dropped connection).) (`ReviewRejectedError`: A reviewer's answer is not allowed (empty, ungrounded, or the run is not waiting).) (`UnknownRunError`: No run with this id.)

```python
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
```

- `from streaming_assistant.domain.routing import ...`: takes names from `streaming_assistant.domain.routing`, this repository's own code. (`Thresholds`: Retrieval coverage at which a question is answered, called thin, or sent to a person.)
- `from streaming_assistant.infrastructure.catalog import ...`: takes names from `streaming_assistant.infrastructure.catalog`, this repository's own code. (`LazyBm25Retriever`: Builds the index on the first search (the cold start the budget must account for); `warm` builds it ahead of time.) (`PageCatalog`: Loads `data/help_pages.json`: 30 pages with titled sections.)
- `from streaming_assistant.infrastructure.clock import ...`: takes names from `streaming_assistant.infrastructure.clock`, this repository's own code. (`SystemClock`: Now, in UTC.)
- `from streaming_assistant.infrastructure.scripted_stream import ...`: takes names from `streaming_assistant.infrastructure.scripted_stream`, this repository's own code. (`Pace`: Latency settings in milliseconds.) (`ScriptedStreamingModel`: Async streaming with counters: tokens produced (what would be billed), cancellations and their times.)
- `from streaming_assistant.infrastructure.sqlite_store import ...`: takes names from `streaming_assistant.infrastructure.sqlite_store`, this repository's own code. (`Database`: One SQLite file behind a lock; every operation is a short transaction.) (`SqliteAudit`: The audit log.) (`SqliteAuthenticator`: Looks a bearer token up by its hash.) (`SqliteRunStore`: Paused runs.)
- `ROOT = Path(__file__).resolve().parents[3]`: stores the item `Path(__file__).resolve().parents[3]` in `ROOT`.

> **Indexing and slicing.** `items[0]` is the first item; `items[-1]` the last; `items[a:b]` is a new list from position `a` up to but not including `b`; `d['key']` looks a key up in a dict (and raises `KeyError` if it is missing).

```python
SHIPPING = "A question about shipping times: standard delivery takes three to five business days after dispatch?"
OFF_TOPIC = "How do I tune a guitar string?"
REFUND_LATE = "Can I get a refund on an order from seventy five days ago?"
FAST = Pace(0, 0, 0, 0, jitter=0)
CUSTOMER = "demo-customer-token"
# `make trace` holds the sum to the lesson's 50 ms on a quiet machine; a unit test must not fail when the machine is busy.
TRACE_TOLERANCE_MS = 400
```

- `SHIPPING = "A question about shipping times: standard delivery take...`: stores the text `'A question about shipping times: standard delivery takes three to five business days a...` in `SHIPPING`.
- `OFF_TOPIC = "How do I tune a guitar string?"`: stores the text `'How do I tune a guitar string?'` in `OFF_TOPIC`.
- `REFUND_LATE = "Can I get a refund on an order from seventy five day...`: stores the text `'Can I get a refund on an order from seventy five days ago?'` in `REFUND_LATE`.
- `FAST = Pace(0, 0, 0, 0, jitter=0)`: stores the result of calling `Pace(0, 0, 0, 0, jitter=0)`, which is this repository's own `Pace` (in `src/streaming_assistant/infrastructure/scripted_stream.py`): latency settings in milliseconds in `FAST`.
- `CUSTOMER = "demo-customer-token"`: stores the text `'demo-customer-token'` in `CUSTOMER`.
- `TRACE_TOLERANCE_MS = 400`: stores the number `400` in `TRACE_TOLERANCE_MS`.

```python
class Rig:
```

- Defines the class `Rig`.

> **A class.** `class Name:` defines a new kind of object. The functions inside it are methods; the first parameter, called `self` by habit, is the object the method was called on. `__init__` runs when an object is made. `Name(...)` makes an object (an instance) of the class. A class listed in brackets after the name is a base class: the new class inherits its methods.

```python
"""The assistant over real in-memory collaborators and a model the test chooses."""
```

- The docstring (documentation kept with the code) says: *The assistant over real in-memory collaborators and a model the test chooses.*

```python
def __init__(self, model=None, **config):
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `model`, optional (default `None`).
  - `**config`: collects extra named arguments in a dict.

> **Parameters.** A parameter with `= value` is optional: if the caller gives nothing, the default is used. A bare `*` in the list means everything after it must be passed by name (`f(x=1)`). `*args` collects extra positional arguments in a tuple and `**kwargs` collects extra named ones in a dict. `->` followed by a type says what the function gives back.

```python
self.db = Database(":memory:")
self.db.apply_scripts(ROOT / "sql")
self.catalog = PageCatalog(ROOT / "data/help_pages.json")
self.audit, self.runs = SqliteAudit(self.db), SqliteRunStore(self.db)
self.model = model or ScriptedStreamingModel(FAST, hallucinate_every=0)
stable = parse_prompt_file("answer", (ROOT / "prompts/answer.v1.md").read_text(encoding="utf-8")).text
```

- `self.db = Database(":memory:")`: stores the result of calling `Database(":memory:")`, which is this repository's own `Database` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): one SQLite file behind a lock; every operation is a short transaction in `self.db`.
- `self.db.apply_scripts(ROOT / "sql")`: calling `self.db.apply_scripts(ROOT / "sql")`, which is this repository's own `apply_scripts` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run the numbered scripts (DDL, then seed); returns the names that ran.
- `self.catalog = PageCatalog(ROOT / "data/help_pages.json")`: stores the result of calling `PageCatalog(ROOT / "data/help_pages.json")`, which is this repository's own `PageCatalog` (in `src/streaming_assistant/infrastructure/catalog.py`): loads `data/help_pages.json`: 30 pages with titled sections in `self.catalog`.
- `self.audit, self.runs = SqliteAudit(self.db), SqliteRunStore(self.db)`: unpacks a tuple of 2 items into the names `self.audit`, `self.runs`, one item each.
- `self.model = model or ScriptedStreamingModel(FAST, hallucinate_ever...`: stores `model or ScriptedStreamingModel(FAST, hallucinate_every=0)` (the first operand that decides the or) in `self.model`.
- `stable = parse_prompt_file("answer", (ROOT / "prompts/answer.v1.md"...`: stores `parse_prompt_file("answer", (ROOT / "prompts/answer.v1.md").read_text(encoding="utf-8")...` in `stable`.

> **Tuples and unpacking.** `(a, b)` is a fixed-length group. `x, y = pair` unpacks the two items into two names at once.

```python
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
```

- `self.assistant = Assistant( LazyBm25Retriever(self.catalog), {"stan...`: stores the result of calling `Assistant( LazyBm25Retriever(self.catalog), {"standard": self.model, "fast": self.model...`, which is this repository's own `Assistant` (in `src/streaming_assistant/application/assistant.py`): orchestrates one request in `self.assistant`.

```python
self.desk = ReviewDesk(self.runs, self.audit, self.catalog, SystemClock())
```

- `self.desk = ReviewDesk(self.runs, self.audit, self.catalog, SystemC...`: stores the result of calling `ReviewDesk(self.runs, self.audit, self.catalog, SystemClock())`, which is this repository's own `ReviewDesk` (in `src/streaming_assistant/application/review.py`): lists waiting runs and validates a reviewer's answer: not empty, and either citing a real section or saying that no page covers the question in `self.desk`.

```python
async def ask(self, question, run_id="run-1", token=CUSTOMER):
```

- Defines the async method `ask` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `question`.
  - `run_id`, optional (default `"run-1"`).
  - `token`, optional (default `CUSTOMER`).

```python
prepared = await self.assistant.prepare(run_id, question, token)
return [event async for event in self.assistant.stream(prepared)]
```

- `prepared = await self.assistant.prepare(run_id, question, token)`: stores the answer of the result of calling `self.assistant.prepare(run_id, question, token)`, which is this repository's own `prepare` (in `src/streaming_assistant/application/assistant.py`): authenticate, retrieve, assemble and route; each stage is timed inside the real path once the wait is over in `prepared`.
- `return [event async for event in self.assistant.stream(prepared)]`: ends the function and gives back a list built by running `event` for each `event` in `self.assistant.stream(prepared)`.

```python
def names(events):
```

- Defines the function `names`.
- Parameters:
  - `events`.

```python
return [event.name for event in events]
```

- `return [event.name for event in events]`: ends the function and gives back a list built by running `event.name` for each `event` in `events`.

```python
def state_of(events):
```

- Defines the function `state_of`.
- Parameters:
  - `events`.

```python
return next(event.data for event in events if event.name == "state")
```

- `return next(event.data for event in events if event.name == "state")`: ends the function and gives back the result of calling `next(event.data for event in events if event.name == "state")`, which takes the next item from `(event.data for event in events if event.name == "state")`.

```python
def test_an_answerable_question_streams_tokens_then_citations_then_done_with_usage_and_timings():
```

- Defines the test `test_an_answerable_question_streams_tokens_then_citations_then_done_with_usage_and_timings`.

```python
events = asyncio.run(Rig().ask(SHIPPING))
assert names(events)[0] == "token" and names(events)[-1] == "done"
assert "citation" in names(events) and "[" not in "".join(e.data["text"] for e in events if e.name == "token")
done = events[-1].data
assert done["outcome"] == "answered" and done["usage"]["output_tokens"] > 0 and done["dropped_citations"] == 0
timings = done["timings"]
```

- `events = asyncio.run(Rig().ask(SHIPPING))`: stores the result of calling `asyncio.run(Rig().ask(SHIPPING))`, which runs a program or a coroutine in `events`.
- `assert names(events)[0] == "token" and names(events)[-1] == "done"`: checks that `names(events)[0]` equals `"token"` and `names(events)[-1]` equals `"done"`. A false check stops the test as failed.
- `assert "citation" in names(events) and "[" not in "".join(e.data["t...`: checks that `"citation"` is among `names(events)` and `"["` is not among `"".join(e.data["text"] for e in events if e.name == "token")`. A false check stops the test as failed.
- `done = events[-1].data`: stores `events[-1].data` in `done`.
- `assert done["outcome"] == "answered" and done["usage"]["output_toke...`: checks that `done["outcome"]` equals `"answered"` and `done["usage"]["output_tokens"]` is greater than `0` and `done["dropped_citations"]` equals `0`. A false check stops the test as failed.
- `timings = done["timings"]`: stores the item `done["timings"]` in `timings`.

```python
assert abs(timings["first_token_ms"] - timings["stage_sum_ms"]) < TRACE_TOLERANCE_MS
```

- `assert abs(timings["first_token_ms"] - timings["stage_sum_ms"]) < T...`: checks that `abs(timings["first_token_ms"] - timings["stage_sum_ms"])` is less than `TRACE_TOLERANCE_MS`. A false check stops the test as failed.

```python
def test_the_stage_times_add_up_to_the_first_token_time_with_and_without_parallel_prep():
```

- Defines the test `test_the_stage_times_add_up_to_the_first_token_time_with_and_without_parallel_prep`.

```python
for parallel in (True, False):
```

- Repeats the indented lines once for each item of `(True, False)`, naming the current item `parallel`.

> **`for`.** `for item in things:` runs the indented lines once per item, giving the name `item` the next value each time. `break` leaves the loop early; `continue` jumps to the next item.

```python
done = asyncio.run(Rig(parallel_prep=parallel).ask(SHIPPING))[-1].data["timings"]
assert abs(done["first_token_ms"] - done["stage_sum_ms"]) < TRACE_TOLERANCE_MS
assert set(done) >= {"auth_ms", "retrieval_ms", "assembly_ms", "overlap_ms", "model_ms"}
```

- `done = asyncio.run(Rig(parallel_prep=parallel).ask(SHIPPING))[-1].d...`: stores the item `asyncio.run(Rig(parallel_prep=parallel).ask(SHIPPING))[-1].data["timings"]` in `done`.
- `assert abs(done["first_token_ms"] - done["stage_sum_ms"]) < TRACE_T...`: checks that `abs(done["first_token_ms"] - done["stage_sum_ms"])` is less than `TRACE_TOLERANCE_MS`. A false check stops the test as failed.
- `assert set(done) >= {"auth_ms", "retrieval_ms", "assembly_ms", "ove...`: checks that `set(done)` is greater than or equal to `{"auth_ms", "retrieval_ms", "assembly_ms", "overlap_ms", "model_ms"}`. A false check stops the test as failed.

```python
@pytest.mark.parametrize(
    ("mode", "state"), [("provider_error", "provider_error"), ("rate_limited", "rate_limited"), ("refusal", "refusal")]
)
def test_a_provider_failure_gets_its_own_state_with_the_designed_message(mode, state):
```

- Defines the test `test_a_provider_failure_gets_its_own_state_with_the_designed_message`.
- `@pytest.mark.parametrize( ("mode", "state"), [("provider_error", "provider_err...`: runs the test once per listed set of values.
- Parameters:
  - `mode`.
  - `state`.

> **Decorators.** A line `@something` above a function or class passes the definition through `something`, and the name then refers to what comes back.

> **`@pytest.mark.parametrize`.** Runs one test function many times, once per set of values listed, so each case is its own test.

```python
events = asyncio.run(Rig(ScriptedStreamingModel(FAST, mode=mode)).ask(SHIPPING))
shown = state_of(events)
assert shown["name"] == state and shown["message"] == STATES[state][0] and shown["action"] == STATES[state][1]
assert "token" not in names(events) and events[-1].data["outcome"] == state
```

- `events = asyncio.run(Rig(ScriptedStreamingModel(FAST, mode=mode)).a...`: stores the result of calling `asyncio.run(Rig(ScriptedStreamingModel(FAST, mode=mode)).ask(SHIPPING))`, which runs a program or a coroutine in `events`.
- `shown = state_of(events)`: stores the result of calling `state_of(events)` in `shown`.
- `assert shown["name"] == state and shown["message"] == STATES[state]...`: checks that `shown["name"]` equals `state` and `shown["message"]` equals `STATES[state][0]` and `shown["action"]` equals `STATES[state][1]`. A false check stops the test as failed.
- `assert "token" not in names(events) and events[-1].data["outcome"] ...`: checks that `"token"` is not among `names(events)` and `events[-1].data["outcome"]` equals `state`. A false check stops the test as failed.

```python
def test_a_model_that_never_answers_gets_the_timeout_state_at_the_first_token_deadline():
```

- Defines the test `test_a_model_that_never_answers_gets_the_timeout_state_at_the_first_token_deadline`.

```python
rig = Rig(ScriptedStreamingModel(FAST, mode="timeout"), first_token_timeout_seconds=0.05)
events = asyncio.run(rig.ask(SHIPPING))
assert state_of(events)["name"] == "timeout" and rig.model.cancelled_at
```

- `rig = Rig(ScriptedStreamingModel(FAST, mode="timeout"), first_token...`: stores the result of calling `Rig(ScriptedStreamingModel(FAST, mode="timeout"), first_token_timeout_seconds=0.05)`, which is this repository's own `Rig` (in `tests/unit/application/test_assistant.py`): the assistant over real in-memory collaborators and a model the test chooses in `rig`.
- `events = asyncio.run(rig.ask(SHIPPING))`: stores the result of calling `asyncio.run(rig.ask(SHIPPING))`, which runs a program or a coroutine in `events`.
- `assert state_of(events)["name"] == "timeout" and rig.model.cancelle...`: checks that `state_of(events)["name"]` equals `"timeout"` and `rig.model.cancelled_at` is truthy. A false check stops the test as failed.

```python
def test_a_stream_that_stalls_after_the_first_token_hits_the_idle_timeout():
```

- Defines the test `test_a_stream_that_stalls_after_the_first_token_hits_the_idle_timeout`.

```python
class Stalls:
```

- Defines the class `Stalls`.

> **`yield`.** A function with `yield` is a generator: calling it does not run the body at once; each time the caller asks for the next value, the body runs up to the next `yield`, gives that value out, and waits.

```python
async def stream(self, request: StreamRequest):
```

- Defines the async method `stream` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `request`, type `StreamRequest`.

```python
yield TextDelta("Hello ")
await asyncio.sleep(3600)
yield Usage(1, 1)
```

- `yield TextDelta("Hello ")`: hands a value to whoever is looping over this generator, then waits to be asked for the next.
- `await asyncio.sleep(3600)`: waits for the result of calling `asyncio.sleep(3600)`, which waits `3600` seconds to finish.
- `yield Usage(1, 1)`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
events = asyncio.run(Rig(Stalls(), idle_timeout_seconds=0.05).ask(SHIPPING))
assert names(events)[0] == "token" and state_of(events)["name"] == "timeout"
```

- `events = asyncio.run(Rig(Stalls(), idle_timeout_seconds=0.05).ask(S...`: stores the result of calling `asyncio.run(Rig(Stalls(), idle_timeout_seconds=0.05).ask(SHIPPING))`, which runs a program or a coroutine in `events`.
- `assert names(events)[0] == "token" and state_of(events)["name"] == ...`: checks that `names(events)[0]` equals `"token"` and `state_of(events)["name"]` equals `"timeout"`. A false check stops the test as failed.

```python
def test_nothing_found_with_pausing_off_gets_the_no_evidence_state():
```

- Defines the test `test_nothing_found_with_pausing_off_gets_the_no_evidence_state`.

```python
events = asyncio.run(Rig(pause_enabled=False).ask(OFF_TOPIC))
assert state_of(events)["name"] == "no_evidence" and "token" not in names(events)
```

- `events = asyncio.run(Rig(pause_enabled=False).ask(OFF_TOPIC))`: stores the result of calling `asyncio.run(Rig(pause_enabled=False).ask(OFF_TOPIC))`, which runs a program or a coroutine in `events`.
- `assert state_of(events)["name"] == "no_evidence" and "token" not in...`: checks that `state_of(events)["name"]` equals `"no_evidence"` and `"token"` is not among `names(events)`. A false check stops the test as failed.

```python
def test_a_thin_match_gets_the_low_confidence_state_that_offers_a_rephrase():
```

- Defines the test `test_a_thin_match_gets_the_low_confidence_state_that_offers_a_rephrase`.

```python
rig = Rig(thresholds=Thresholds(confident=1.5, pause_below=0.1))
events = asyncio.run(rig.ask(SHIPPING))
shown = state_of(events)
assert shown["name"] == "low_confidence" and shown["action"] == "rephrase" and "token" not in names(events)
```

- `rig = Rig(thresholds=Thresholds(confident=1.5, pause_below=0.1))`: stores the result of calling `Rig(thresholds=Thresholds(confident=1.5, pause_below=0.1))`, which is this repository's own `Rig` (in `tests/unit/application/test_assistant.py`): the assistant over real in-memory collaborators and a model the test chooses in `rig`.
- `events = asyncio.run(rig.ask(SHIPPING))`: stores the result of calling `asyncio.run(rig.ask(SHIPPING))`, which runs a program or a coroutine in `events`.
- `shown = state_of(events)`: stores the result of calling `state_of(events)` in `shown`.
- `assert shown["name"] == "low_confidence" and shown["action"] == "re...`: checks that `shown["name"]` equals `"low_confidence"` and `shown["action"]` equals `"rephrase"` and `"token"` is not among `names(events)`. A false check stops the test as failed.

```python
def test_stop_ends_the_stream_cancels_the_upstream_call_and_is_audited():
```

- Defines the test `test_stop_ends_the_stream_cancels_the_upstream_call_and_is_audited`.

```python
slow = ScriptedStreamingModel(Pace(0, 0, 0, 30, jitter=0), hallucinate_every=0)
rig = Rig(slow)
```

- `slow = ScriptedStreamingModel(Pace(0, 0, 0, 30, jitter=0), hallucin...`: stores the result of calling `ScriptedStreamingModel(Pace(0, 0, 0, 30, jitter=0), hallucinate_every=0)`, which is this repository's own `ScriptedStreamingModel` (in `src/streaming_assistant/infrastructure/scripted_stream.py`): async streaming with counters: tokens produced (what would be billed), cancellations and their times in `slow`.
- `rig = Rig(slow)`: stores the result of calling `Rig(slow)`, which is this repository's own `Rig` (in `tests/unit/application/test_assistant.py`): the assistant over real in-memory collaborators and a model the test chooses in `rig`.

```python
async def go():
```

- Defines the async function `go` (a coroutine: calling it makes a job for the event loop to run).

```python
rig.assistant.stops.request("run-1")
return await rig.ask(SHIPPING)
```

- `rig.assistant.stops.request("run-1")`: calling `rig.assistant.stops.request("run-1")`.
- `return await rig.ask(SHIPPING)`: ends the function and gives back the answer of the result of calling `rig.ask(SHIPPING)` once the wait is over.

```python
events = asyncio.run(go())
assert state_of(events)["name"] == "stopped" and events[-1].data["outcome"] == "stopped"
assert slow.cancelled_at and ("stopped", "customer") in [(e.step, e.actor) for e in rig.audit.entries("run-1")]
assert not rig.assistant.stops.is_requested("run-1")
```

- `events = asyncio.run(go())`: stores the result of calling `asyncio.run(go())`, which runs a program or a coroutine in `events`.
- `assert state_of(events)["name"] == "stopped" and events[-1].data["o...`: checks that `state_of(events)["name"]` equals `"stopped"` and `events[-1].data["outcome"]` equals `"stopped"`. A false check stops the test as failed.
- `assert slow.cancelled_at and ("stopped", "customer") in [(e.step, e...`: checks that `slow.cancelled_at` is truthy and `("stopped", "customer")` is among `[(e.step, e.actor) for e in rig.audit.entries("run-1")]`. A false check stops the test as failed.
- `assert not rig.assistant.stops.is_requested("run-1")`: checks that it is not the case that `rig.assistant.stops.is_requested("run-1")` is true (the call is this repository's own `is_requested` (in `src/streaming_assistant/application/assistant.py`): true once a stop was asked for). A false check stops the test as failed.

```python
def test_a_closed_connection_cancels_the_upstream_call_and_is_audited_as_the_clients_doing():
```

- Defines the test `test_a_closed_connection_cancels_the_upstream_call_and_is_audited_as_the_clients_doing`.

```python
slow = ScriptedStreamingModel(Pace(0, 0, 0, 200, jitter=0), hallucinate_every=0)
rig = Rig(slow)
```

- `slow = ScriptedStreamingModel(Pace(0, 0, 0, 200, jitter=0), halluci...`: stores the result of calling `ScriptedStreamingModel(Pace(0, 0, 0, 200, jitter=0), hallucinate_every=0)`, which is this repository's own `ScriptedStreamingModel` (in `src/streaming_assistant/infrastructure/scripted_stream.py`): async streaming with counters: tokens produced (what would be billed), cancellations and their times in `slow`.
- `rig = Rig(slow)`: stores the result of calling `Rig(slow)`, which is this repository's own `Rig` (in `tests/unit/application/test_assistant.py`): the assistant over real in-memory collaborators and a model the test chooses in `rig`.

```python
async def go():
```

- Defines the async function `go` (a coroutine: calling it makes a job for the event loop to run).

```python
prepared = await rig.assistant.prepare("run-1", SHIPPING, CUSTOMER)
```

- `prepared = await rig.assistant.prepare("run-1", SHIPPING, CUSTOMER)`: stores the answer of the result of calling `rig.assistant.prepare("run-1", SHIPPING, CUSTOMER)`, which is this repository's own `prepare` (in `src/streaming_assistant/application/assistant.py`): authenticate, retrieve, assemble and route; each stage is timed inside the real path once the wait is over in `prepared`.

```python
async def consume():
```

- Defines the async function `consume` (a coroutine: calling it makes a job for the event loop to run).

```python
async for _ in rig.assistant.stream(prepared):
```

- Repeats the indented lines once for each item of `rig.assistant.stream(prepared)`, naming the current item `_`. (`async for` waits for each item.)

```python
pass
```

- `pass`: does nothing; it fills a place where a statement is required.

```python
task = asyncio.create_task(consume())
await asyncio.sleep(0.15)
task.cancel()
```

- `task = asyncio.create_task(consume())`: stores the result of calling `asyncio.create_task(consume())`, which starts a coroutine running in the background in `task`.
- `await asyncio.sleep(0.15)`: waits for the result of calling `asyncio.sleep(0.15)`, which waits `0.15` seconds to finish.
- `task.cancel()`: calling `task.cancel()`.

```python
with pytest.raises(asyncio.CancelledError):
```

- `pytest.raises(asyncio.CancelledError)`: the test passes only if the indented lines raise `asyncio.CancelledError`; it fails if nothing is raised.

> **`with`.** `with thing as name:` uses a resource for the indented lines and then cleans it up, even if an error happens: a file is closed, a lock is released, a database transaction is committed or rolled back.

> **`pytest.raises(E)`.** A `with` block that passes only if the code inside raises an error of kind `E`; it fails if nothing is raised.

```python
await task
```

- `await task`: waits for the value of `task` to finish.

```python
asyncio.run(go())
assert slow.cancelled_at and ("stopped", "client") in [(e.step, e.actor) for e in rig.audit.entries("run-1")]
assert rig.assistant.stats["disconnected"] == 1
```

- `asyncio.run(go())`: calling `asyncio.run(go())`, which runs a program or a coroutine.
- `assert slow.cancelled_at and ("stopped", "client") in [(e.step, e.a...`: checks that `slow.cancelled_at` is truthy and `("stopped", "client")` is among `[(e.step, e.actor) for e in rig.audit.entries("run-1")]`. A false check stops the test as failed.
- `assert rig.assistant.stats["disconnected"] == 1`: checks that `rig.assistant.stats["disconnected"]` equals `1`. A false check stops the test as failed.

```python
def test_a_citation_to_a_page_that_was_not_retrieved_is_dropped_and_counted():
```

- Defines the test `test_a_citation_to_a_page_that_was_not_retrieved_is_dropped_and_counted`.

```python
rig = Rig(ScriptedStreamingModel(FAST, hallucinate_every=1))
events = asyncio.run(rig.ask(SHIPPING))
cited = [e.data["page_id"] for e in events if e.name == "citation"]
assert "help-99" not in cited and cited and events[-1].data["dropped_citations"] == 1
assert rig.assistant.stats["dropped_citations"] == 1
```

- `rig = Rig(ScriptedStreamingModel(FAST, hallucinate_every=1))`: stores the result of calling `Rig(ScriptedStreamingModel(FAST, hallucinate_every=1))`, which is this repository's own `Rig` (in `tests/unit/application/test_assistant.py`): the assistant over real in-memory collaborators and a model the test chooses in `rig`.
- `events = asyncio.run(rig.ask(SHIPPING))`: stores the result of calling `asyncio.run(rig.ask(SHIPPING))`, which runs a program or a coroutine in `events`.
- `cited = [e.data["page_id"] for e in events if e.name == "citation"]`: stores a list built by running `e.data["page_id"]` for each `e` in `events` keeping only those where `e.name` equals `"citation"` in `cited`.
- `assert "help-99" not in cited and cited and events[-1].data["droppe...`: checks that `"help-99"` is not among `cited` and `cited` is truthy (not `None`, `False`, zero or empty) and `events[-1].data["dropped_citations"]` equals `1`. A false check stops the test as failed.
- `assert rig.assistant.stats["dropped_citations"] == 1`: checks that `rig.assistant.stats["dropped_citations"]` equals `1`. A false check stops the test as failed.

```python
def test_a_should_pause_question_pauses_with_a_saved_run_and_an_audit_entry():
```

- Defines the test `test_a_should_pause_question_pauses_with_a_saved_run_and_an_audit_entry`.

```python
rig = Rig()
events = asyncio.run(rig.ask(REFUND_LATE))
assert names(events) == ["paused", "done"] and events[0].data["reason"] == "policy_exception"
saved = rig.runs.get("run-1")
assert saved is not None and saved.status == "waiting" and saved.retrieved
assert [e.step for e in rig.audit.entries("run-1")] == ["received", "paused"]
```

- `rig = Rig()`: stores the result of calling `Rig()`, which is this repository's own `Rig` (in `tests/unit/application/test_assistant.py`): the assistant over real in-memory collaborators and a model the test chooses in `rig`.
- `events = asyncio.run(rig.ask(REFUND_LATE))`: stores the result of calling `asyncio.run(rig.ask(REFUND_LATE))`, which runs a program or a coroutine in `events`.
- `assert names(events) == ["paused", "done"] and events[0].data["reas...`: checks that `names(events)` equals `["paused", "done"]` and `events[0].data["reason"]` equals `"policy_exception"`. A false check stops the test as failed.
- `saved = rig.runs.get("run-1")`: stores the result of calling `rig.runs.get("run-1")`, which looks up `"run-1"` in `rig.runs`; a second value is the answer when the key is missing in `saved`.
- `assert saved is not None and saved.status == "waiting" and saved.re...`: checks that `saved` is something (not `None`) and `saved.status` equals `"waiting"` and `saved.retrieved` is truthy. A false check stops the test as failed.
- `assert [e.step for e in rig.audit.entries("run-1")] == ["received",...`: checks that `[e.step for e in rig.audit.entries("run-1")]` equals `["received", "paused"]`. A false check stops the test as failed.

```python
def test_off_topic_questions_pause_for_no_page_covers():
```

- Defines the test `test_off_topic_questions_pause_for_no_page_covers`.

```python
events = asyncio.run(Rig().ask(OFF_TOPIC))
assert names(events) == ["paused", "done"] and events[0].data["reason"] == "no_page_covers"
```

- `events = asyncio.run(Rig().ask(OFF_TOPIC))`: stores the result of calling `asyncio.run(Rig().ask(OFF_TOPIC))`, which runs a program or a coroutine in `events`.
- `assert names(events) == ["paused", "done"] and events[0].data["reas...`: checks that `names(events)` equals `["paused", "done"]` and `events[0].data["reason"]` equals `"no_page_covers"`. A false check stops the test as failed.

```python
def test_a_reviewer_answer_is_validated_then_the_run_resumes_with_it_in_context_and_the_trail_verifies():
```

- Defines the test `test_a_reviewer_answer_is_validated_then_the_run_resumes_with_it_in_context_and_the_trail_verifies`.

```python
rig = Rig()
asyncio.run(rig.ask(REFUND_LATE))
saved = rig.runs.get("run-1")
assert saved is not None
ref = saved.retrieved[0]
```

- `rig = Rig()`: stores the result of calling `Rig()`, which is this repository's own `Rig` (in `tests/unit/application/test_assistant.py`): the assistant over real in-memory collaborators and a model the test chooses in `rig`.
- `asyncio.run(rig.ask(REFUND_LATE))`: calling `asyncio.run(rig.ask(REFUND_LATE))`, which runs a program or a coroutine.
- `saved = rig.runs.get("run-1")`: stores the result of calling `rig.runs.get("run-1")`, which looks up `"run-1"` in `rig.runs`; a second value is the answer when the key is missing in `saved`.
- `assert saved is not None`: checks that `saved` is something (not `None`). A false check stops the test as failed.
- `ref = saved.retrieved[0]`: stores the item `saved.retrieved[0]` in `ref`.

```python
for text, cited, message in (
    (" ", [ref], "empty"),
    ("Sure.", [], "cite a help section"),
    ("Sure.", ["help-99#nope"], "unknown section"),
):
```

- Repeats the indented lines once for each item of `( (" ", [ref], "empty"), ("Sure.", [], "cite a help section"), ("Sure.", ["help-99#nope...`, naming the current item the names `text`, `cited`, `message`.

```python
with pytest.raises(ReviewRejectedError, match=message):
```

- `pytest.raises(ReviewRejectedError, match=message)`: the test passes only if the indented lines raise `ReviewRejectedError`; it fails if nothing is raised.

```python
rig.desk.answer("run-1", "ana", text, cited, False)
```

- `rig.desk.answer("run-1", "ana", text, cited, False)`: calling `rig.desk.answer("run-1", "ana", text, cited, False)`, which is this repository's own `answer` (in `src/streaming_assistant/application/review.py`): validate and store the reviewer's answer; raises `ReviewRejectedError` with the reason when it is not allowed.

```python
with pytest.raises(ReviewRejectedError, match="reviewer id"):
```

- `pytest.raises(ReviewRejectedError, match="reviewer id")`: the test passes only if the indented lines raise `ReviewRejectedError`; it fails if nothing is raised.

```python
rig.desk.answer("run-1", " ", "Sure.", [ref], False)
```

- `rig.desk.answer("run-1", " ", "Sure.", [ref], False)`: calling `rig.desk.answer("run-1", " ", "Sure.", [ref], False)`, which is this repository's own `answer` (in `src/streaming_assistant/application/review.py`): validate and store the reviewer's answer; raises `ReviewRejectedError` with the reason when it is not allowed.

```python
assert rig.desk.status("run-1") == "waiting"
answered = rig.desk.answer("run-1", "ana", "Store credit approved for the late return.", [ref], False)
assert answered.status == "answered" and rig.desk.status("run-1") == "answered"
```

- `assert rig.desk.status("run-1") == "waiting"`: checks that `rig.desk.status("run-1")` equals `"waiting"`. A false check stops the test as failed.
- `answered = rig.desk.answer("run-1", "ana", "Store credit approved f...`: stores the result of calling `rig.desk.answer("run-1", "ana", "Store credit approved for the late return.", [ref], Fa...`, which is this repository's own `answer` (in `src/streaming_assistant/application/review.py`): validate and store the reviewer's answer; raises `ReviewRejectedError` with the reason when it is not allowed in `answered`.
- `assert answered.status == "answered" and rig.desk.status("run-1") =...`: checks that `answered.status` equals `"answered"` and `rig.desk.status("run-1")` equals `"answered"`. A false check stops the test as failed.

```python
with pytest.raises(ReviewRejectedError, match="not waiting"):
```

- `pytest.raises(ReviewRejectedError, match="not waiting")`: the test passes only if the indented lines raise `ReviewRejectedError`; it fails if nothing is raised.

```python
rig.desk.answer("run-1", "ana", "Again.", [ref], False)
```

- `rig.desk.answer("run-1", "ana", "Again.", [ref], False)`: calling `rig.desk.answer("run-1", "ana", "Again.", [ref], False)`, which is this repository's own `answer` (in `src/streaming_assistant/application/review.py`): validate and store the reviewer's answer; raises `ReviewRejectedError` with the reason when it is not allowed.

```python
async def resume():
```

- Defines the async function `resume` (a coroutine: calling it makes a job for the event loop to run).

```python
return [event async for event in rig.assistant.resume("run-1")]
```

- `return [event async for event in rig.assistant.resume("run-1")]`: ends the function and gives back a list built by running `event` for each `event` in `rig.assistant.resume("run-1")`.

```python
events = asyncio.run(resume())
text = "".join(e.data["text"] for e in events if e.name == "token")
assert "Store credit approved for the late return." in text and events[-1].data["outcome"] == "answered"
assert [e.data["page_id"] for e in events if e.name == "citation"]
assert rig.desk.status("run-1") == "resumed"
steps = [e.step for e in rig.audit.entries("run-1")]
```

- `events = asyncio.run(resume())`: stores the result of calling `asyncio.run(resume())`, which runs a program or a coroutine in `events`.
- `text = "".join(e.data["text"] for e in events if e.name == "token")`: stores the result of calling `"".join(e.data["text"] for e in events if e.name == "token")`, which glues the items of `(e.data["text"] for e in events if e.name == "token")` together with `""` between them in `text`.
- `assert "Store credit approved for the late return." in text and eve...`: checks that `"Store credit approved for the late return."` is among `text` and `events[-1].data["outcome"]` equals `"answered"`. A false check stops the test as failed.
- `assert [e.data["page_id"] for e in events if e.name == "citation"]`: checks that `[e.data["page_id"] for e in events if e.name == "citation"]` is true. A false check stops the test as failed.
- `assert rig.desk.status("run-1") == "resumed"`: checks that `rig.desk.status("run-1")` equals `"resumed"`. A false check stops the test as failed.
- `steps = [e.step for e in rig.audit.entries("run-1")]`: stores a list built by running `e.step` for each `e` in `rig.audit.entries("run-1")` in `steps`.

```python
assert steps == ["received", "paused", "answered", "validated", "resumed", "citations", "shown"]
assert verify(rig.audit.entries()) is None
```

- `assert steps == ["received", "paused", "answered", "validated", "re...`: checks that `steps` equals `["received", "paused", "answered", "validated", "resumed", "citations", "shown"]`. A false check stops the test as failed.
- `assert verify(rig.audit.entries()) is None`: checks that `verify(rig.audit.entries())` is nothing (`None`). A false check stops the test as failed.

```python
def test_a_reviewer_may_say_that_no_page_covers_the_question():
```

- Defines the test `test_a_reviewer_may_say_that_no_page_covers_the_question`.

```python
rig = Rig()
asyncio.run(rig.ask(OFF_TOPIC))
assert rig.desk.answer("run-1", "ana", "We do not sell guitars.", [], True).no_page
```

- `rig = Rig()`: stores the result of calling `Rig()`, which is this repository's own `Rig` (in `tests/unit/application/test_assistant.py`): the assistant over real in-memory collaborators and a model the test chooses in `rig`.
- `asyncio.run(rig.ask(OFF_TOPIC))`: calling `asyncio.run(rig.ask(OFF_TOPIC))`, which runs a program or a coroutine.
- `assert rig.desk.answer("run-1", "ana", "We do not sell guitars.", [...`: checks that `rig.desk.answer("run-1", "ana", "We do not sell guitars.", [], True).no_page` is truthy. A false check stops the test as failed.

```python
def test_resuming_a_run_that_is_unknown_or_not_answered_is_refused():
```

- Defines the test `test_resuming_a_run_that_is_unknown_or_not_answered_is_refused`.

```python
rig = Rig()
asyncio.run(rig.ask(REFUND_LATE))
```

- `rig = Rig()`: stores the result of calling `Rig()`, which is this repository's own `Rig` (in `tests/unit/application/test_assistant.py`): the assistant over real in-memory collaborators and a model the test chooses in `rig`.
- `asyncio.run(rig.ask(REFUND_LATE))`: calling `asyncio.run(rig.ask(REFUND_LATE))`, which runs a program or a coroutine.

```python
async def resume(run_id):
```

- Defines the async function `resume` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `run_id`.

```python
return [event async for event in rig.assistant.resume(run_id)]
```

- `return [event async for event in rig.assistant.resume(run_id)]`: ends the function and gives back a list built by running `event` for each `event` in `rig.assistant.resume(run_id)`.

```python
with pytest.raises(UnknownRunError):
```

- `pytest.raises(UnknownRunError)`: the test passes only if the indented lines raise `UnknownRunError`; it fails if nothing is raised.

```python
asyncio.run(resume("nope"))
```

- `asyncio.run(resume("nope"))`: calling `asyncio.run(resume("nope"))`, which runs a program or a coroutine.

```python
with pytest.raises(UnknownRunError, match="not answered"):
```

- `pytest.raises(UnknownRunError, match="not answered")`: the test passes only if the indented lines raise `UnknownRunError`; it fails if nothing is raised.

```python
asyncio.run(resume("run-1"))
```

- `asyncio.run(resume("run-1"))`: calling `asyncio.run(resume("run-1"))`, which runs a program or a coroutine.

```python
with pytest.raises(UnknownRunError):
```

- `pytest.raises(UnknownRunError)`: the test passes only if the indented lines raise `UnknownRunError`; it fails if nothing is raised.

```python
rig.desk.status("nope")
```

- `rig.desk.status("nope")`: calling `rig.desk.status("nope")`, which is this repository's own `status` (in `src/streaming_assistant/application/review.py`): the run's status: waiting, answered or resumed.

```python
with pytest.raises(UnknownRunError):
```

- `pytest.raises(UnknownRunError)`: the test passes only if the indented lines raise `UnknownRunError`; it fails if nothing is raised.

```python
rig.desk.answer("nope", "ana", "x", [], True)
```

- `rig.desk.answer("nope", "ana", "x", [], True)`: calling `rig.desk.answer("nope", "ana", "x", [], True)`, which is this repository's own `answer` (in `src/streaming_assistant/application/review.py`): validate and store the reviewer's answer; raises `ReviewRejectedError` with the reason when it is not allowed.

```python
assert [run.run_id for run in rig.desk.waiting()] == ["run-1"]
```

- `assert [run.run_id for run in rig.desk.waiting()] == ["run-1"]`: checks that `[run.run_id for run in rig.desk.waiting()]` equals `["run-1"]`. A false check stops the test as failed.

```python
def test_an_unknown_token_is_refused_on_both_prepare_paths():
```

- Defines the test `test_an_unknown_token_is_refused_on_both_prepare_paths`.

```python
for parallel in (True, False):
```

- Repeats the indented lines once for each item of `(True, False)`, naming the current item `parallel`.

```python
with pytest.raises(UnauthorizedError):
```

- `pytest.raises(UnauthorizedError)`: the test passes only if the indented lines raise `UnauthorizedError`; it fails if nothing is raised.

```python
asyncio.run(Rig(parallel_prep=parallel).ask(SHIPPING, token="wrong"))
```

- `asyncio.run(Rig(parallel_prep=parallel).ask(SHIPPING, token="wrong"))`: calling `asyncio.run(Rig(parallel_prep=parallel).ask(SHIPPING, token="wrong"))`, which runs a program or a coroutine.

```python
def test_easy_questions_go_to_the_fast_tier_when_routing_is_on():
```

- Defines the test `test_easy_questions_go_to_the_fast_tier_when_routing_is_on`.

```python
seen = []
```

- `seen = []`: stores a new list (empty) in `seen`.

```python
class Spy(ScriptedStreamingModel):
```

- Defines the class `Spy`.
- It extends `ScriptedStreamingModel` (it starts with all of that class's methods and may add or replace some).

```python
async def stream(self, request):
```

- Defines the async method `stream` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `request`.

```python
seen.append(request.tier)
```

- `seen.append(request.tier)`: calling `seen.append(request.tier)`, which adds `request.tier` to the end of `seen`.

```python
async for chunk in super().stream(request):
```

- Repeats the indented lines once for each item of `super().stream(request)`, naming the current item `chunk`. (`async for` waits for each item.)

```python
yield chunk
```

- `yield chunk`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
asyncio.run(Rig(Spy(FAST, hallucinate_every=0), route_easy_to_fast=True).ask(SHIPPING))
asyncio.run(Rig(Spy(FAST, hallucinate_every=0), route_easy_to_fast=False).ask(SHIPPING))
assert seen == ["fast", "standard"]
```

- `asyncio.run(Rig(Spy(FAST, hallucinate_every=0), route_easy_to_fast=...`: calling `asyncio.run(Rig(Spy(FAST, hallucinate_every=0), route_easy_to_fast=True).ask(SHIPPING))`, which runs a program or a coroutine.
- `asyncio.run(Rig(Spy(FAST, hallucinate_every=0), route_easy_to_fast=...`: calling `asyncio.run(Rig(Spy(FAST, hallucinate_every=0), route_easy_to_fast=False).ask(SHIPPING))`, which runs a program or a coroutine.
- `assert seen == ["fast", "standard"]`: checks that `seen` equals `["fast", "standard"]`. A false check stops the test as failed.

```python
def test_stable_text_goes_first_so_a_prefix_cache_can_apply():
```

- Defines the test `test_stable_text_goes_first_so_a_prefix_cache_can_apply`.

```python
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
```

- `rig = Rig()`: stores the result of calling `Rig()`, which is this repository's own `Rig` (in `tests/unit/application/test_assistant.py`): the assistant over real in-memory collaborators and a model the test chooses in `rig`.
- `hits = rig.assistant._retriever.search(SHIPPING, 3)`: stores the result of calling `rig.assistant._retriever.search(SHIPPING, 3)`, which looks for the pattern anywhere in the text in `hits`.
- `stable_first = assemble("STABLE", hits, SHIPPING, stable_first=True...`: stores the result of calling `assemble("STABLE", hits, SHIPPING, stable_first=True, tier="standard")`, which is this repository's own `assemble` (in `src/streaming_assistant/application/prompt.py`): stable instructions first (cacheable, the same for every request), then the passages and the question The named values are `stable_first`, `tier`. in `stable_first`.
- `stable_last = assemble("STABLE", hits, SHIPPING, stable_first=False...`: stores the result of calling `assemble("STABLE", hits, SHIPPING, stable_first=False, tier="fast", reviewer_answer="Ye...`, which is this repository's own `assemble` (in `src/streaming_assistant/application/prompt.py`): stable instructions first (cacheable, the same for every request), then the passages and the question The named values are `stable_first`, `tier`, `reviewer_answer`. in `stable_last`.
- `assert ( stable_first.system == "STABLE" and SHIPPING in stable_fir...`: checks that `stable_first.system` equals `"STABLE"` and `SHIPPING` is among `stable_first.user` and `stable_first.prompt_version` equals `PROMPT_VERSION`. A false check stops the test as failed.
- `assert stable_last.system.startswith("Passages:") and stable_last.t...`: checks that `stable_last.system.startswith("Passages:")` is true (the call asks whether `stable_last.system` begins with `"Passages:"`) and `stable_last.tier` equals `"fast"` and `"STABLE"` is among `stable_last.system`. A false check stops the test as failed.

```python
other = assemble("STABLE", hits[:1], "another question", stable_first=True, tier="standard")
assert other.system == stable_first.system
```

- `other = assemble("STABLE", hits[:1], "another question", stable_fir...`: stores the result of calling `assemble("STABLE", hits[:1], "another question", stable_first=True, tier="standard")`, which is this repository's own `assemble` (in `src/streaming_assistant/application/prompt.py`): stable instructions first (cacheable, the same for every request), then the passages and the question The named values are `stable_first`, `tier`. in `other`.
- `assert other.system == stable_first.system`: checks that `other.system` equals `stable_first.system`. A false check stops the test as failed.

```python
def test_the_prompt_file_needs_both_fences_and_a_version_and_an_owner():
```

- Defines the test `test_the_prompt_file_needs_both_fences_and_a_version_and_an_owner`.

```python
ok = parse_prompt_file("answer", "---\nversion: v1\nowner: me\n---\nText.")
assert (ok.version, ok.owner, ok.text) == ("v1", "me", "Text.")
```

- `ok = parse_prompt_file("answer", "---\nversion: v1\nowner: me\n---\...`: stores the result of calling `parse_prompt_file("answer", "---\nversion: v1\nowner: me\n---\nText.")`, which is this repository's own `parse_prompt_file` (in `src/streaming_assistant/application/prompts.py`): split `---`, header lines, `---`, then the prompt text; both fences are required in `ok`.
- `assert (ok.version, ok.owner, ok.text) == ("v1", "me", "Text.")`: checks that `(ok.version, ok.owner, ok.text)` equals `("v1", "me", "Text.")`. A false check stops the test as failed.

```python
for bad in ("no fences", "---\nversion: v1\n---\nText.", "---\nowner: me\n---\nText."):
```

- Repeats the indented lines once for each item of `("no fences", "---\nversion: v1\n---\nText.", "---\nowner: me\n---\nText.")`, naming the current item `bad`.

```python
with pytest.raises(PromptFileError):
```

- `pytest.raises(PromptFileError)`: the test passes only if the indented lines raise `PromptFileError`; it fails if nothing is raised.

```python
parse_prompt_file("answer", bad)
```

- `parse_prompt_file("answer", bad)`: calling `parse_prompt_file("answer", bad)`, which is this repository's own `parse_prompt_file` (in `src/streaming_assistant/application/prompts.py`): split `---`, header lines, `---`, then the prompt text; both fences are required.

```python
def test_a_failure_in_the_provider_before_any_token_is_mapped_by_the_assistant_not_leaked():
```

- Defines the test `test_a_failure_in_the_provider_before_any_token_is_mapped_by_the_assistant_not_leaked`.

```python
class Boom:
```

- Defines the class `Boom`.

```python
async def stream(self, request) -> AsyncIterator[Chunk]:
```

- Defines the async method `stream` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `request`.
- Gives back a value of type `AsyncIterator[Chunk]`.

```python
raise ProviderError("down")
yield  # pragma: no cover
```

- `raise ProviderError("down")`: stops with an error of kind `ProviderError` with the message `"down"`. Whoever called this code must handle it or the program stops.
- `yield`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

> **`try` / `except` / `finally`.** Code in `try` runs; if it raises an error of the kind named in `except`, that block runs instead of the program stopping. `else` runs only if there was no error. `finally` always runs last. `raise` makes an error on purpose; `raise ... from other` records the earlier error as its cause.

```python
events = asyncio.run(Rig(Boom()).ask(SHIPPING))
assert state_of(events)["name"] == "provider_error"
```

- `events = asyncio.run(Rig(Boom()).ask(SHIPPING))`: stores the result of calling `asyncio.run(Rig(Boom()).ask(SHIPPING))`, which runs a program or a coroutine in `events`.
- `assert state_of(events)["name"] == "provider_error"`: checks that `state_of(events)["name"]` equals `"provider_error"`. A false check stops the test as failed.

```python
def test_the_questions_file_has_200_questions_and_20_should_pause():
```

- Defines the test `test_the_questions_file_has_200_questions_and_20_should_pause`.

```python
rows = [json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines()]
assert len(rows) == 200 and sum(row["should_pause"] for row in rows) == 20
```

- `rows = [json.loads(line) for line in (ROOT / "data/questions.jsonl"...`: stores a list built by running `json.loads(line)` for each `line` in `(ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines()` in `rows`.
- `assert len(rows) == 200 and sum(row["should_pause"] for row in rows...`: checks that `len(rows)` equals `200` and `sum(row["should_pause"] for row in rows)` equals `20`. A false check stops the test as failed.

#### `tests/unit/domain/test_domain.py`

- This file has no docstring at the top.

```python
from datetime import UTC, datetime

import pytest

from streaming_assistant.domain.audit import GENESIS, make_entry, verify
from streaming_assistant.domain.citations import MarkerStripper, check_refs
from streaming_assistant.domain.retrieval import Bm25Index, Section, terms
```

- `from datetime import ...`: takes names from `datetime` (dates, times and time spans). (`UTC`: the UTC time zone.) (`datetime`: the date-and-time type.)
- `import pytest`: makes the module `pytest` available (the test framework).
- `from streaming_assistant.domain.audit import ...`: takes names from `streaming_assistant.domain.audit`, this repository's own code. (`GENESIS`: a name defined in this repository.) (`make_entry`: The next entry in the chain.) (`verify`: Index of the first entry that was edited, removed or reordered; None when the chain holds.)
- `from streaming_assistant.domain.citations import ...`: takes names from `streaming_assistant.domain.citations`, this repository's own code. (`MarkerStripper`: Removes `[page#section]` markers from a stream of text pieces, even when a marker is split across pieces, and remembers the refs it saw.) (`check_refs`: (sections that may be shown, number dropped).)
- `from streaming_assistant.domain.retrieval import ...`: takes names from `streaming_assistant.domain.retrieval`, this repository's own code. (`Bm25Index`: Built once from the sections.) (`Section`: One section of a help page; `anchor` is where a citation opens the page.) (`terms`: Lower-case content words (no stop words), with a crude plural fold.)

```python
from streaming_assistant.domain.routing import (
    ANSWER,
    LOW_CONFIDENCE,
    NO_EVIDENCE,
    PAUSE,
    Thresholds,
    days_since_delivery,
    decide_route,
    needs_a_person,
    words_to_number,
)
```

- `from streaming_assistant.domain.routing import ...`: takes names from `streaming_assistant.domain.routing`, this repository's own code. (`ANSWER`: a name defined in this repository.) (`LOW_CONFIDENCE`: a name defined in this repository.) (`NO_EVIDENCE`: a name defined in this repository.) (`PAUSE`: a name defined in this repository.) (`Thresholds`: Retrieval coverage at which a question is answered, called thin, or sent to a person.) (`days_since_delivery`: The age in days a question states ("sixty days ago", "75 days ago"), or None.) (`decide_route`: A question that matches a needs-a-person pattern pauses; so does one no page covers (when pausing is on).) (`needs_a_person`: A refund asked for after the 30-day window, or a legal threat: a policy exception only a person can grant.) (`words_to_number`: A small number written in digits or words ("75", "seventy five", "a hundred"); None when it is not one.)

```python
from streaming_assistant.domain.stats import percentile

NOW = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)
```

- `from streaming_assistant.domain.stats import ...`: takes names from `streaming_assistant.domain.stats`, this repository's own code. (`percentile`: Nearest-rank percentile of `values` (0.95 for p95); 0.0 for no values.)
- `NOW = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)`: stores the result of calling `datetime(2026, 10, 27, 12, 0, tzinfo=UTC)` The named values are `tzinfo`. in `NOW`.

```python
def chain(count: int = 4):
```

- Defines the function `chain`.
- Parameters:
  - `count`, type `int`, optional (default `4`).

```python
entries, previous = [], None
```

- `entries, previous = [], None`: unpacks a tuple of 2 items into the names `entries`, `previous`, one item each.

```python
for number in range(count):
```

- Repeats the indented lines once for each item of `range(count)`, naming the current item `number`.

```python
entry = make_entry(
    previous, "run-1", ("received", "paused", "answered", "shown")[number % 4], "actor", NOW, f"step {number}"
)
entries.append(entry)
previous = entry.hash
```

- `entry = make_entry( previous, "run-1", ("received", "paused", "answ...`: stores the result of calling `make_entry( previous, "run-1", ("received", "paused", "answered", "shown")[number % 4],...`, which is this repository's own `make_entry` (in `src/streaming_assistant/domain/audit.py`): the next entry in the chain in `entry`.
- `entries.append(entry)`: calling `entries.append(entry)`, which adds `entry` to the end of `entries`.
- `previous = entry.hash`: stores `entry.hash` in `previous`.

```python
return entries
```

- `return entries`: ends the function and gives back the value of `entries`.

```python
def test_an_intact_chain_verifies_and_starts_from_the_genesis_marker():
```

- Defines the test `test_an_intact_chain_verifies_and_starts_from_the_genesis_marker`.

```python
entries = chain()
assert verify(entries) is None and entries[0].previous == GENESIS and verify([]) is None
```

- `entries = chain()`: stores the result of calling `chain()` in `entries`.
- `assert verify(entries) is None and entries[0].previous == GENESIS a...`: checks that `verify(entries)` is nothing (`None`) and `entries[0].previous` equals `GENESIS` and `verify([])` is nothing (`None`). A false check stops the test as failed.

```python
def test_an_edited_entry_is_reported_at_its_own_index():
```

- Defines the test `test_an_edited_entry_is_reported_at_its_own_index`.

```python
from dataclasses import replace

entries = chain()
entries[2] = replace(entries[2], content="Approve a full refund")
assert verify(entries) == 2
```

- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`replace`: a name provided by that module.)
- `entries = chain()`: stores the result of calling `chain()` in `entries`.
- `entries[2] = replace(entries[2], content="Approve a full refund")`: stores the result of calling `replace(entries[2], content="Approve a full refund")`, which replaces `entries[2]` with the second argument in  The named values are `content`. in the slot `entries[2]`.
- `assert verify(entries) == 2`: checks that `verify(entries)` equals `2`. A false check stops the test as failed.

```python
def test_a_removed_entry_is_reported_where_the_gap_is():
```

- Defines the test `test_a_removed_entry_is_reported_where_the_gap_is`.

```python
entries = chain()
del entries[1]
assert verify(entries) == 1
```

- `entries = chain()`: stores the result of calling `chain()` in `entries`.
- `del entries[1]`: removes `entries[1]`.
- `assert verify(entries) == 1`: checks that `verify(entries)` equals `1`. A false check stops the test as failed.

```python
def test_a_reordered_pair_is_reported_at_the_first_moved_entry():
```

- Defines the test `test_a_reordered_pair_is_reported_at_the_first_moved_entry`.

```python
entries = chain()
entries[1], entries[2] = entries[2], entries[1]
assert verify(entries) == 1
```

- `entries = chain()`: stores the result of calling `chain()` in `entries`.
- `entries[1], entries[2] = entries[2], entries[1]`: unpacks a tuple of 2 items into the names `entries[1]`, `entries[2]`, one item each.
- `assert verify(entries) == 1`: checks that `verify(entries)` equals `1`. A false check stops the test as failed.

```python
def test_a_hash_recomputed_by_the_editor_still_breaks_the_next_link():
```

- Defines the test `test_a_hash_recomputed_by_the_editor_still_breaks_the_next_link`.

```python
from dataclasses import replace

from streaming_assistant.domain.audit import digest

entries = chain()
edited = replace(entries[1], content="changed")
edited = replace(edited, hash=digest(edited.previous, edited.run, edited.step, edited.actor, edited.at, "changed"))
entries[1] = edited
```

- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`replace`: a name provided by that module.)
- `from streaming_assistant.domain.audit import ...`: takes names from `streaming_assistant.domain.audit`, this repository's own code. (`digest`: SHA-256 over the six fields, in a fixed order, joined by a separator that text does not contain.)
- `entries = chain()`: stores the result of calling `chain()` in `entries`.
- `edited = replace(entries[1], content="changed")`: stores the result of calling `replace(entries[1], content="changed")`, which replaces `entries[1]` with the second argument in  The named values are `content`. in `edited`.
- `edited = replace(edited, hash=digest(edited.previous, edited.run, e...`: stores the result of calling `replace(edited, hash=digest(edited.previous, edited.run, edited.step, edited.actor, edi...`, which replaces `edited` with the second argument in  The named values are `hash`. in `edited`.
- `entries[1] = edited`: stores the value of `edited` in the slot `entries[1]`.

```python
assert verify(entries) == 2
```

- `assert verify(entries) == 2`: checks that `verify(entries)` equals `2`. A false check stops the test as failed.

```python
def section(ref="help-01#shipping-times", heading="Shipping times", text="Standard delivery takes three to five days."):
```

- Defines the function `section`.
- Parameters:
  - `ref`, optional (default `"help-01#shipping-times"`).
  - `heading`, optional (default `"Shipping times"`).
  - `text`, optional (default `"Standard delivery takes three to five days."`).

```python
page, anchor = ref.split("#")
return Section(page, "Shipping", anchor, heading, text)
```

- `page, anchor = ref.split("#")`: unpacks the result of calling `ref.split("#")`, which cuts `ref` into pieces at `"#"` (whitespace if nothing is given) into the names `page`, `anchor`, one item each.
- `return Section(page, "Shipping", anchor, heading, text)`: ends the function and gives back the result of calling `Section(page, "Shipping", anchor, heading, text)`, which is this repository's own `Section` (in `src/streaming_assistant/domain/retrieval.py`): one section of a help page; `anchor` is where a citation opens the page.

```python
def test_markers_are_removed_even_when_split_across_pieces_and_their_refs_are_remembered():
```

- Defines the test `test_markers_are_removed_even_when_split_across_pieces_and_their_refs_are_remembered`.

```python
strip = MarkerStripper()
shown = strip.feed("Delivery takes days [help-01#ship")
shown += strip.feed("ping-times] and more.")
assert shown == "Delivery takes days  and more." and strip.refs == ["help-01#shipping-times"]
assert strip.feed("again [help-01#shipping-times]") == "again " and strip.refs == ["help-01#shipping-times"]
```

- `strip = MarkerStripper()`: stores the result of calling `MarkerStripper()`, which is this repository's own `MarkerStripper` (in `src/streaming_assistant/domain/citations.py`): removes `[page#section]` markers from a stream of text pieces, even when a marker is split across pieces, and remembers the refs it saw in `strip`.
- `shown = strip.feed("Delivery takes days [help-01#ship")`: stores the result of calling `strip.feed("Delivery takes days [help-01#ship")`, which is this repository's own `feed` (in `src/streaming_assistant/domain/citations.py`): text that is safe to show now in `shown`.
- `shown += strip.feed("ping-times] and more.")`: adds `strip.feed("ping-times] and more.")` to `shown` and keeps the result there.
- `assert shown == "Delivery takes days and more." and strip.refs == [...`: checks that `shown` equals `"Delivery takes days and more."` and `strip.refs` equals `["help-01#shipping-times"]`. A false check stops the test as failed.
- `assert strip.feed("again [help-01#shipping-times]") == "again " and...`: checks that `strip.feed("again [help-01#shipping-times]")` equals `"again "` and `strip.refs` equals `["help-01#shipping-times"]`. A false check stops the test as failed.

```python
def test_brackets_that_are_not_citations_are_shown_and_unclosed_ones_are_held_then_released():
```

- Defines the test `test_brackets_that_are_not_citations_are_shown_and_unclosed_ones_are_held_then_released`.

```python
strip = MarkerStripper()
assert strip.feed("a [note] b") == "a [note] b" and strip.refs == []
assert strip.feed("open [help-01") == "open "
assert strip.finish() == "[help-01" and strip.finish() == ""
long = "x [" + "y" * 60
assert MarkerStripper().feed(long) == long
```

- `strip = MarkerStripper()`: stores the result of calling `MarkerStripper()`, which is this repository's own `MarkerStripper` (in `src/streaming_assistant/domain/citations.py`): removes `[page#section]` markers from a stream of text pieces, even when a marker is split across pieces, and remembers the refs it saw in `strip`.
- `assert strip.feed("a [note] b") == "a [note] b" and strip.refs == []`: checks that `strip.feed("a [note] b")` equals `"a [note] b"` and `strip.refs` equals `[]`. A false check stops the test as failed.
- `assert strip.feed("open [help-01") == "open "`: checks that `strip.feed("open [help-01")` equals `"open "`. A false check stops the test as failed.
- `assert strip.finish() == "[help-01" and strip.finish() == ""`: checks that `strip.finish()` equals `"[help-01"` and `strip.finish()` equals `""`. A false check stops the test as failed.
- `long = "x [" + "y" * 60`: stores `"x [" + "y" * 60`, which adds `"x ["` and `"y" * 60` in `long`.
- `assert MarkerStripper().feed(long) == long`: checks that `MarkerStripper().feed(long)` equals `long`. A false check stops the test as failed.

```python
def test_only_refs_retrieved_for_the_request_may_be_shown_and_the_rest_are_counted():
```

- Defines the test `test_only_refs_retrieved_for_the_request_may_be_shown_and_the_rest_are_counted`.

```python
allowed = {"help-01#shipping-times": section()}
shown, dropped = check_refs(["help-01#shipping-times", "help-99#made-up"], allowed)
assert [s.ref for s in shown] == ["help-01#shipping-times"] and dropped == 1
assert check_refs([], allowed) == ((), 0)
```

- `allowed = {"help-01#shipping-times": section()}`: stores a new dict with 1 entries in `allowed`.
- `shown, dropped = check_refs(["help-01#shipping-times", "help-99#mad...`: unpacks the result of calling `check_refs(["help-01#shipping-times", "help-99#made-up"], allowed)`, which is this repository's own `check_refs` (in `src/streaming_assistant/domain/citations.py`): (sections that may be shown, number dropped) into the names `shown`, `dropped`, one item each.
- `assert [s.ref for s in shown] == ["help-01#shipping-times"] and dro...`: checks that `[s.ref for s in shown]` equals `["help-01#shipping-times"]` and `dropped` equals `1`. A false check stops the test as failed.
- `assert check_refs([], allowed) == ((), 0)`: checks that `check_refs([], allowed)` equals `((), 0)`. A false check stops the test as failed.

```python
def test_terms_drop_stop_words_and_fold_plurals():
```

- Defines the test `test_terms_drop_stop_words_and_fold_plurals`.

```python
assert terms("How do I track my parcels?") == ["track", "parcel"]
```

- `assert terms("How do I track my parcels?") == ["track", "parcel"]`: checks that `terms("How do I track my parcels?")` equals `["track", "parcel"]`. A false check stops the test as failed.

```python
def make_index():
```

- Defines the function `make_index`.

```python
return Bm25Index(
    [
        section(),
        section(
            "help-02#refund-timing", "Refund timing", "A refund appears on the card within five business days."
        ),
        section("help-03#gift-wrap", "Gift wrap", "Gift wrap is a checkout option for a small fee."),
    ]
)
```

- `return Bm25Index( [ section(), section( "help-02#refund-timing", "R...`: ends the function and gives back the result of calling `Bm25Index( [ section(), section( "help-02#refund-timing", "Refund timing", "A refund ap...`, which is this repository's own `Bm25Index` (in `src/streaming_assistant/domain/retrieval.py`): built once from the sections.

```python
def test_search_ranks_the_covering_section_first_and_reports_its_coverage():
```

- Defines the test `test_search_ranks_the_covering_section_first_and_reports_its_coverage`.

```python
hits = make_index().search("When does a refund appear on the card?")
assert hits[0].section.ref == "help-02#refund-timing" and hits[0].coverage == pytest.approx(1.0)
assert make_index().search("zebra") == []
```

- `hits = make_index().search("When does a refund appear on the card?")`: stores the result of calling `make_index().search("When does a refund appear on the card?")`, which looks for the pattern anywhere in the text in `hits`.
- `assert hits[0].section.ref == "help-02#refund-timing" and hits[0].c...`: checks that `hits[0].section.ref` equals `"help-02#refund-timing"` and `hits[0].coverage` equals `pytest.approx(1.0)`. A false check stops the test as failed.
- `assert make_index().search("zebra") == []`: checks that `make_index().search("zebra")` equals `[]`. A false check stops the test as failed.

```python
def test_words_found_nowhere_count_against_coverage():
```

- Defines the test `test_words_found_nowhere_count_against_coverage`.

```python
covered = make_index().search("refund card")[0].coverage
diluted = make_index().search("refund card zebra giraffe")[0].coverage
assert covered == pytest.approx(1.0) and diluted < covered and diluted <= 0.55
```

- `covered = make_index().search("refund card")[0].coverage`: stores `make_index().search("refund card")[0].coverage` in `covered`.
- `diluted = make_index().search("refund card zebra giraffe")[0].coverage`: stores `make_index().search("refund card zebra giraffe")[0].coverage` in `diluted`.
- `assert covered == pytest.approx(1.0) and diluted < covered and dilu...`: checks that `covered` equals `pytest.approx(1.0)` and `diluted` is less than `covered` and `diluted` is less than or equal to `0.55`. A false check stops the test as failed.

```python
@pytest.mark.parametrize(
    ("text", "number"),
    [
        ("75", 75),
        ("seventy five", 75),
        ("a hundred", 100),
        ("one hundred and five", 105),
        ("sixty-five", 65),
        ("banana", None),
        ("", None),
        ("and", None),
    ],
)
def test_small_numbers_are_read_from_digits_and_words(text, number):
```

- Defines the test `test_small_numbers_are_read_from_digits_and_words`.
- `@pytest.mark.parametrize( ("text", "number"), [ ("75", 75), ("seventy five", 7...`: runs the test once per listed set of values.
- Parameters:
  - `text`.
  - `number`.

```python
assert words_to_number(text) == number
```

- `assert words_to_number(text) == number`: checks that `words_to_number(text)` equals `number`. A false check stops the test as failed.

```python
@pytest.mark.parametrize(
    ("question", "days"),
    [
        ("I got it seventy five days ago", 75),
        ("it came a hundred days ago", 100),
        ("delivered 12 days since", 12),
        ("How do I get a refund?", None),
        ("a banana days ago", None),
    ],
)
def test_the_age_of_an_order_is_read_from_the_question(question, days):
```

- Defines the test `test_the_age_of_an_order_is_read_from_the_question`.
- `@pytest.mark.parametrize( ("question", "days"), [ ("I got it seventy five days...`: runs the test once per listed set of values.
- Parameters:
  - `question`.
  - `days`.

```python
assert days_since_delivery(question) == days
```

- `assert days_since_delivery(question) == days`: checks that `days_since_delivery(question)` equals `days`. A false check stops the test as failed.

```python
@pytest.mark.parametrize(
    ("question", "pauses"),
    [
        ("I want a refund for something I received fifty days ago.", True),
        ("I received it ten days ago, refund please", False),
        ("Refund me, it arrived thirty days ago", False),
        ("How do I get a refund?", False),
        ("I will take legal action", True),
        ("The chargeback is filed", True),
        ("Sixty days ago I ordered a lamp", False),
    ],
)
def test_a_refund_after_the_window_or_a_legal_threat_needs_a_person(question, pauses):
```

- Defines the test `test_a_refund_after_the_window_or_a_legal_threat_needs_a_person`.
- `@pytest.mark.parametrize( ("question", "pauses"), [ ("I want a refund for some...`: runs the test once per listed set of values.
- Parameters:
  - `question`.
  - `pauses`.

```python
assert needs_a_person(question) is pauses
```

- `assert needs_a_person(question) is pauses`: checks that `needs_a_person(question)` is exactly `pauses`. A false check stops the test as failed.

```python
def hit(coverage):
```

- Defines the function `hit`.
- Parameters:
  - `coverage`.

```python
from streaming_assistant.domain.retrieval import Hit

return Hit(section(), 1.0, coverage)
```

- `from streaming_assistant.domain.retrieval import ...`: takes names from `streaming_assistant.domain.retrieval`, this repository's own code. (`Hit`: A section the retriever returned, with its raw score and the share of the question's weight it covers.)
- `return Hit(section(), 1.0, coverage)`: ends the function and gives back the result of calling `Hit(section(), 1.0, coverage)`, which is this repository's own `Hit` (in `src/streaming_assistant/domain/retrieval.py`): a section the retriever returned, with its raw score and the share of the question's weight it covers.

```python
def test_routes_follow_the_thresholds():
```

- Defines the test `test_routes_follow_the_thresholds`.

```python
thresholds = Thresholds()
assert decide_route("how long is delivery", [hit(0.9)], thresholds).kind == ANSWER
assert decide_route("how long is delivery", [hit(0.5)], thresholds).kind == LOW_CONFIDENCE
assert decide_route("how long is delivery", [hit(0.1)], thresholds).kind == PAUSE
assert decide_route("how long is delivery", [], thresholds).kind == PAUSE
assert decide_route("how long is delivery", [], thresholds, pause_enabled=False).kind == NO_EVIDENCE
```

- `thresholds = Thresholds()`: stores the result of calling `Thresholds()`, which is this repository's own `Thresholds` (in `src/streaming_assistant/domain/routing.py`): retrieval coverage at which a question is answered, called thin, or sent to a person in `thresholds`.
- `assert decide_route("how long is delivery", [hit(0.9)], thresholds)...`: checks that `decide_route("how long is delivery", [hit(0.9)], thresholds).kind` equals `ANSWER`. A false check stops the test as failed.
- `assert decide_route("how long is delivery", [hit(0.5)], thresholds)...`: checks that `decide_route("how long is delivery", [hit(0.5)], thresholds).kind` equals `LOW_CONFIDENCE`. A false check stops the test as failed.
- `assert decide_route("how long is delivery", [hit(0.1)], thresholds)...`: checks that `decide_route("how long is delivery", [hit(0.1)], thresholds).kind` equals `PAUSE`. A false check stops the test as failed.
- `assert decide_route("how long is delivery", [], thresholds).kind ==...`: checks that `decide_route("how long is delivery", [], thresholds).kind` equals `PAUSE`. A false check stops the test as failed.
- `assert decide_route("how long is delivery", [], thresholds, pause_e...`: checks that `decide_route("how long is delivery", [], thresholds, pause_enabled=False).kind` equals `NO_EVIDENCE`. A false check stops the test as failed.

```python
assert decide_route("refund from ninety days ago", [hit(0.9)], thresholds).kind == PAUSE
assert decide_route("refund from ninety days ago", [hit(0.9)], thresholds, pause_enabled=False).kind == ANSWER
```

- `assert decide_route("refund from ninety days ago", [hit(0.9)], thre...`: checks that `decide_route("refund from ninety days ago", [hit(0.9)], thresholds).kind` equals `PAUSE`. A false check stops the test as failed.
- `assert decide_route("refund from ninety days ago", [hit(0.9)], thre...`: checks that `decide_route("refund from ninety days ago", [hit(0.9)], thresholds, pause_enabled=False...` equals `ANSWER`. A false check stops the test as failed.

```python
def test_percentile_is_nearest_rank_and_safe_on_nothing():
```

- Defines the test `test_percentile_is_nearest_rank_and_safe_on_nothing`.

```python
assert percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.95) == 10
assert percentile([5.0], 0.5) == 5.0 and percentile([], 0.5) == 0.0
assert percentile([4, 1, 3, 2], 0.5) == 2
```

- `assert percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.95) == 10`: checks that `percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.95)` equals `10`. A false check stops the test as failed.
- `assert percentile([5.0], 0.5) == 5.0 and percentile([], 0.5) == 0.0`: checks that `percentile([5.0], 0.5)` equals `5.0` and `percentile([], 0.5)` equals `0.0`. A false check stops the test as failed.
- `assert percentile([4, 1, 3, 2], 0.5) == 2`: checks that `percentile([4, 1, 3, 2], 0.5)` equals `2`. A false check stops the test as failed.

#### `tests/unit/infrastructure/test_adapters.py`

- This file has no docstring at the top.

```python
import asyncio
import io
import json
import logging
import random
import sqlite3
```

- `import asyncio`: makes the module `asyncio` available (the standard library's tools for asynchronous code (many waits interleaved on one thread)).
- `import io`: makes the module `io` available (in-memory byte and text streams).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import logging`: makes the module `logging` available (the standard library's logging system).
- `import random`: makes the module `random` available (random numbers (a seeded generator gives the same numbers every run)).
- `import sqlite3`: makes the module `sqlite3` available (the standard library's SQLite database driver).

```python
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import anthropic
import httpx
import pytest
```

- `from datetime import ...`: takes names from `datetime` (dates, times and time spans). (`UTC`: the UTC time zone.) (`datetime`: the date-and-time type.)
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from types import ...`: takes names from `types` (names for built-in types such as a module or a function). (`SimpleNamespace`: a name provided by that module.)
- `import anthropic`: makes the module `anthropic` available (Anthropic's official Python library for calling Claude).
- `import httpx`: makes the module `httpx` available (an HTTP client library).
- `import pytest`: makes the module `pytest` available (the test framework).

```python
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
```

- `from streaming_assistant.application.ports import ...`: takes names from `streaming_assistant.application.ports`, this repository's own code. (`PausedRun`: A run waiting for, or past, a reviewer.) (`StreamRequest`: One streamed completion.) (`TextDelta`: A piece of the answer.) (`Usage`: Token counts, sent when the stream ends normally.)
- `from streaming_assistant.domain.audit import ...`: takes names from `streaming_assistant.domain.audit`, this repository's own code. (`verify`: Index of the first entry that was edited, removed or reordered; None when the chain holds.)
- `from streaming_assistant.domain.errors import ...`: takes names from `streaming_assistant.domain.errors`, this repository's own code. (`ProviderError`: The model provider failed (a server error or a dropped connection).) (`RateLimitedError`: The model provider answered 429.) (`RefusedError`: The model declined to answer.)
- `from streaming_assistant.infrastructure.catalog import ...`: takes names from `streaming_assistant.infrastructure.catalog`, this repository's own code. (`CachingRetriever`: A small LRU cache in front of a retriever, keyed by the normalized query.) (`LazyBm25Retriever`: Builds the index on the first search (the cold start the budget must account for); `warm` builds it ahead of time.) (`PageCatalog`: Loads `data/help_pages.json`: 30 pages with titled sections.)
- `from streaming_assistant.infrastructure.claude_stream import ...`: takes names from `streaming_assistant.infrastructure.claude_stream`, this repository's own code. (`ClaudeStreamingModel`: One streamed Messages API call.)
- `from streaming_assistant.infrastructure.environment import ...`: takes names from `streaming_assistant.infrastructure.environment`, this repository's own code. (`ConfigurationError`: An environment variable is missing or has an unusable value.) (`read_choice`: A string variable restricted to `choices`.) (`read_float`: A float variable of at least `minimum`.) (`read_int`: An integer variable of at least `minimum`.) (`read_optional`: A string variable that may be absent or empty (for example an API key).) (`read_text`: A non-empty string variable, or `default`.)

```python
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
```

- `from streaming_assistant.infrastructure.logging import ...`: takes names from `streaming_assistant.infrastructure.logging`, this repository's own code. (`LogfmtFormatter`: Format a log record as one logfmt line, with the record's extra fields as key=value pairs.) (`configure_logging`: Send every log record to `stream` (stderr by default) as logfmt.) (`fields`: Use as `logger.info("message", extra=fields(order_id=...))` to attach key=value pairs.)
- `from streaming_assistant.infrastructure.recorded_stream import ...`: takes names from `streaming_assistant.infrastructure.recorded_stream`, this repository's own code. (`MissingRecordingError`: No recording matches this request; the message says how to re-record.) (`RecordedStreamingModel`: Replays the recorded pieces; a request with no recording fails loudly.) (`RecordingStreamingModel`: Wraps a model and writes every stream it returns to a cassette.)
- `from streaming_assistant.infrastructure.retry import ...`: takes names from `streaming_assistant.infrastructure.retry`, this repository's own code. (`retry`: Call `operation` up to `attempts` times, backing off after each failure in `retry_on`.)
- `from streaming_assistant.infrastructure.scripted_stream import ...`: takes names from `streaming_assistant.infrastructure.scripted_stream`, this repository's own code. (`Pace`: Latency settings in milliseconds.) (`ScriptedStreamingModel`: Async streaming with counters: tokens produced (what would be billed), cancellations and their times.)
- `from streaming_assistant.infrastructure.settings import ...`: takes names from `streaming_assistant.infrastructure.settings`, this repository's own code. (`Settings`: Everything the programs read from the environment.)
- `from streaming_assistant.infrastructure.shutdown import ...`: takes names from `streaming_assistant.infrastructure.shutdown`, this repository's own code. (`ShutdownSignal`: A flag that SIGINT and SIGTERM set, which work loops check between units of work.)

```python
from streaming_assistant.infrastructure.sqlite_store import (
    Database,
    SqliteAudit,
    SqliteAuthenticator,
    SqliteRunStore,
    token_hash,
)
```

- `from streaming_assistant.infrastructure.sqlite_store import ...`: takes names from `streaming_assistant.infrastructure.sqlite_store`, this repository's own code. (`Database`: One SQLite file behind a lock; every operation is a short transaction.) (`SqliteAudit`: The audit log.) (`SqliteAuthenticator`: Looks a bearer token up by its hash.) (`SqliteRunStore`: Paused runs.) (`token_hash`: The stored form of a bearer token.)

```python
ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)
```

- `ROOT = Path(__file__).resolve().parents[3]`: stores the item `Path(__file__).resolve().parents[3]` in `ROOT`.
- `NOW = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)`: stores the result of calling `datetime(2026, 10, 27, 12, 0, tzinfo=UTC)` The named values are `tzinfo`. in `NOW`.

```python
@pytest.fixture
def db():
```

- Defines the function `db`.
- `@pytest.fixture`: marks the function as a pytest fixture.

> **A fixture** is a function marked `@pytest.fixture` that prepares something a test needs (a temporary folder, a database, a client). A test asks for it by naming it as a parameter.

```python
database = Database(":memory:")
database.apply_scripts(ROOT / "sql")
return database
```

- `database = Database(":memory:")`: stores the result of calling `Database(":memory:")`, which is this repository's own `Database` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): one SQLite file behind a lock; every operation is a short transaction in `database`.
- `database.apply_scripts(ROOT / "sql")`: calling `database.apply_scripts(ROOT / "sql")`, which is this repository's own `apply_scripts` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run the numbered scripts (DDL, then seed); returns the names that ran.
- `return database`: ends the function and gives back the value of `database`.

```python
def test_demo_tokens_are_stored_as_hashes_and_map_to_roles(db):
```

- Defines the test `test_demo_tokens_are_stored_as_hashes_and_map_to_roles`.
- Parameters:
  - `db`: a fixture (defined in `tests/unit/infrastructure/test_adapters.py`).

```python
auth = SqliteAuthenticator(db)
assert auth.role_of("demo-customer-token") == "customer" and auth.role_of("demo-reviewer-token") == "reviewer"
assert auth.role_of("nope") is None and auth.role_of("") is None
assert token_hash("demo-customer-token") in {row[0] for row in db.execute("SELECT token_hash FROM api_tokens")}
assert "demo-customer-token" not in json.dumps(db.execute("SELECT * FROM api_tokens"))
```

- `auth = SqliteAuthenticator(db)`: stores the result of calling `SqliteAuthenticator(db)`, which is this repository's own `SqliteAuthenticator` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): looks a bearer token up by its hash in `auth`.
- `assert auth.role_of("demo-customer-token") == "customer" and auth.r...`: checks that `auth.role_of("demo-customer-token")` equals `"customer"` and `auth.role_of("demo-reviewer-token")` equals `"reviewer"`. A false check stops the test as failed.
- `assert auth.role_of("nope") is None and auth.role_of("") is None`: checks that `auth.role_of("nope")` is nothing (`None`) and `auth.role_of("")` is nothing (`None`). A false check stops the test as failed.
- `assert token_hash("demo-customer-token") in {row[0] for row in db.e...`: checks that `token_hash("demo-customer-token")` is among `{row[0] for row in db.execute("SELECT token_hash FROM api_tokens")}`. A false check stops the test as failed.
- `assert "demo-customer-token" not in json.dumps(db.execute("SELECT *...`: checks that `"demo-customer-token"` is not among `json.dumps(db.execute("SELECT * FROM api_tokens"))`. A false check stops the test as failed.

```python
def test_applying_the_scripts_twice_leaves_one_clean_database(db):
```

- Defines the test `test_applying_the_scripts_twice_leaves_one_clean_database`.
- Parameters:
  - `db`: a fixture (defined in `tests/unit/infrastructure/test_adapters.py`).

```python
SqliteAudit(db).append("run-1", "received", "customer", "hello")
db.apply_scripts(ROOT / "sql")
assert db.execute("SELECT COUNT(*) FROM audit_log") == [(0,)] and db.execute("SELECT COUNT(*) FROM api_tokens") == [
    (2,)
]
```

- `SqliteAudit(db).append("run-1", "received", "customer", "hello")`: calling `SqliteAudit(db).append("run-1", "received", "customer", "hello")`, which adds `"run-1"` to the end of `SqliteAudit(db)`.
- `db.apply_scripts(ROOT / "sql")`: calling `db.apply_scripts(ROOT / "sql")`, which is this repository's own `apply_scripts` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run the numbered scripts (DDL, then seed); returns the names that ran.
- `assert db.execute("SELECT COUNT(*) FROM audit_log") == [(0,)] and d...`: checks that `db.execute("SELECT COUNT(*) FROM audit_log")` equals `[(0,)]` and `db.execute("SELECT COUNT(*) FROM api_tokens")` equals `[ (2,) ]`. A false check stops the test as failed.

```python
def test_a_failed_statement_rolls_back_and_the_database_stays_usable(db):
```

- Defines the test `test_a_failed_statement_rolls_back_and_the_database_stays_usable`.
- Parameters:
  - `db`: a fixture (defined in `tests/unit/infrastructure/test_adapters.py`).

```python
with pytest.raises(Exception, match="no such table"):
```

- `pytest.raises(Exception, match="no such table")`: the test passes only if the indented lines raise `Exception`; it fails if nothing is raised.

```python
db.execute("SELECT * FROM missing_table")
```

- `db.execute("SELECT * FROM missing_table")`: calling `db.execute("SELECT * FROM missing_table")`, which sends the SQL statement `"SELECT * FROM missing_table"` to the database.

```python
assert db.execute("SELECT 1") == [(1,)]
```

- `assert db.execute("SELECT 1") == [(1,)]`: checks that `db.execute("SELECT 1")` equals `[(1,)]`. A false check stops the test as failed.

```python
def test_paused_runs_survive_a_reopen_of_the_same_file(tmp_path):
```

- Defines the test `test_paused_runs_survive_a_reopen_of_the_same_file`.
- Parameters:
  - `tmp_path`: a fixture; a fresh empty temporary folder for this test.

> **`tmp_path`.** A built-in fixture that gives each test a fresh empty temporary folder (a `Path`).

```python
path = tmp_path / "assistant.sqlite"
first = Database(path)
first.apply_scripts(ROOT / "sql")
SqliteRunStore(first).save_pause(PausedRun("run-1", "q?", ("help-01#a",), "no_page_covers", "waiting"), NOW)
SqliteAudit(first).append("run-1", "paused", "assistant", "no_page_covers")
first.close()
```

- `path = tmp_path / "assistant.sqlite"`: stores `tmp_path / "assistant.sqlite"`, which divides `tmp_path` and `"assistant.sqlite"` in `path`.
- `first = Database(path)`: stores the result of calling `Database(path)`, which is this repository's own `Database` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): one SQLite file behind a lock; every operation is a short transaction in `first`.
- `first.apply_scripts(ROOT / "sql")`: calling `first.apply_scripts(ROOT / "sql")`, which is this repository's own `apply_scripts` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run the numbered scripts (DDL, then seed); returns the names that ran.
- `SqliteRunStore(first).save_pause(PausedRun("run-1", "q?", ("help-01...`: calling `SqliteRunStore(first).save_pause(PausedRun("run-1", "q?", ("help-01#a",), "no_page_cove...`.
- `SqliteAudit(first).append("run-1", "paused", "assistant", "no_page_...`: calling `SqliteAudit(first).append("run-1", "paused", "assistant", "no_page_covers")`, which adds `"run-1"` to the end of `SqliteAudit(first)`.
- `first.close()`: calling `first.close()`, which closes `first`.

```python
second = Database(path)
runs = SqliteRunStore(second)
saved = runs.get("run-1")
assert saved is not None and saved.retrieved == ("help-01#a",) and saved.status == "waiting"
runs.record_answer("run-1", "ana", "Answer.", ["help-01#a"], False, NOW)
runs.mark_resumed("run-1", NOW)
```

- `second = Database(path)`: stores the result of calling `Database(path)`, which is this repository's own `Database` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): one SQLite file behind a lock; every operation is a short transaction in `second`.
- `runs = SqliteRunStore(second)`: stores the result of calling `SqliteRunStore(second)`, which is this repository's own `SqliteRunStore` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): paused runs in `runs`.
- `saved = runs.get("run-1")`: stores the result of calling `runs.get("run-1")`, which looks up `"run-1"` in `runs`; a second value is the answer when the key is missing in `saved`.
- `assert saved is not None and saved.retrieved == ("help-01#a",) and ...`: checks that `saved` is something (not `None`) and `saved.retrieved` equals `("help-01#a",)` and `saved.status` equals `"waiting"`. A false check stops the test as failed.
- `runs.record_answer("run-1", "ana", "Answer.", ["help-01#a"], False,...`: calling `runs.record_answer("run-1", "ana", "Answer.", ["help-01#a"], False, NOW)`.
- `runs.mark_resumed("run-1", NOW)`: calling `runs.mark_resumed("run-1", NOW)`, which is this repository's own `mark_resumed` (in `src/streaming_assistant/application/ports.py`): move the run to `resumed`.

```python
done = runs.get("run-1")
assert done is not None and (done.status, done.reviewer_id, done.cited, done.no_page) == (
    "resumed",
    "ana",
    ("help-01#a",),
    False,
)
assert runs.waiting(10) == [] and runs.get("nope") is None
assert verify(SqliteAudit(second).entries()) is None
```

- `done = runs.get("run-1")`: stores the result of calling `runs.get("run-1")`, which looks up `"run-1"` in `runs`; a second value is the answer when the key is missing in `done`.
- `assert done is not None and (done.status, done.reviewer_id, done.ci...`: checks that `done` is something (not `None`) and `(done.status, done.reviewer_id, done.cited, done.no_page)` equals `( "resumed", "ana", ("help-01#a",), False, )`. A false check stops the test as failed.
- `assert runs.waiting(10) == [] and runs.get("nope") is None`: checks that `runs.waiting(10)` equals `[]` and `runs.get("nope")` is nothing (`None`). A false check stops the test as failed.
- `assert verify(SqliteAudit(second).entries()) is None`: checks that `verify(SqliteAudit(second).entries())` is nothing (`None`). A false check stops the test as failed.

```python
def test_the_audit_chain_in_the_database_breaks_at_an_edited_row_and_a_deleted_row(db):
```

- Defines the test `test_the_audit_chain_in_the_database_breaks_at_an_edited_row_and_a_deleted_row`.
- Parameters:
  - `db`: a fixture (defined in `tests/unit/infrastructure/test_adapters.py`).

```python
audit = SqliteAudit(db)
```

- `audit = SqliteAudit(db)`: stores the result of calling `SqliteAudit(db)`, which is this repository's own `SqliteAudit` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): the audit log in `audit`.

```python
for step in ("received", "paused", "answered", "shown"):
```

- Repeats the indented lines once for each item of `("received", "paused", "answered", "shown")`, naming the current item `step`.

```python
audit.append("run-1", step, "actor", f"content of {step}")
```

- `audit.append("run-1", step, "actor", f"content of {step}")`: calling `audit.append("run-1", step, "actor", f"content of {step}")`, which adds `"run-1"` to the end of `audit`.

```python
audit.append("run-2", "received", "actor", "another run")
assert verify(audit.entries()) is None and len(audit.entries("run-1")) == 4
```

- `audit.append("run-2", "received", "actor", "another run")`: calling `audit.append("run-2", "received", "actor", "another run")`, which adds `"run-2"` to the end of `audit`.
- `assert verify(audit.entries()) is None and len(audit.entries("run-1...`: checks that `verify(audit.entries())` is nothing (`None`) and `len(audit.entries("run-1"))` equals `4`. A false check stops the test as failed.

```python
with pytest.raises(sqlite3.IntegrityError, match="append-only"):
```

- `pytest.raises(sqlite3.IntegrityError, match="append-only")`: the test passes only if the indented lines raise `sqlite3.IntegrityError`; it fails if nothing is raised.

```python
db.execute("UPDATE audit_log SET content = 'Approve a full refund' WHERE seq = 2")
```

- `db.execute("UPDATE audit_log SET content = 'Approve a full refund' ...`: calling `db.execute("UPDATE audit_log SET content = 'Approve a full refund' WHERE seq = 2")`, which sends the SQL statement `"UPDATE audit_log SET content = 'Approve a full refund' WHERE seq = 2"` to the database.

```python
with pytest.raises(sqlite3.IntegrityError, match="append-only"):
```

- `pytest.raises(sqlite3.IntegrityError, match="append-only")`: the test passes only if the indented lines raise `sqlite3.IntegrityError`; it fails if nothing is raised.

```python
db.execute("DELETE FROM audit_log WHERE seq = 2")
```

- `db.execute("DELETE FROM audit_log WHERE seq = 2")`: calling `db.execute("DELETE FROM audit_log WHERE seq = 2")`, which sends the SQL statement `"DELETE FROM audit_log WHERE seq = 2"` to the database.

```python
db.execute("DROP TRIGGER audit_log_no_update")
db.execute("DROP TRIGGER audit_log_no_delete")
db.execute("UPDATE audit_log SET content = 'Approve a full refund' WHERE seq = 2")
assert verify(audit.entries()) == 1
db.apply_scripts(ROOT / "sql")
```

- `db.execute("DROP TRIGGER audit_log_no_update")`: calling `db.execute("DROP TRIGGER audit_log_no_update")`, which sends the SQL statement `"DROP TRIGGER audit_log_no_update"` to the database.
- `db.execute("DROP TRIGGER audit_log_no_delete")`: calling `db.execute("DROP TRIGGER audit_log_no_delete")`, which sends the SQL statement `"DROP TRIGGER audit_log_no_delete"` to the database.
- `db.execute("UPDATE audit_log SET content = 'Approve a full refund' ...`: calling `db.execute("UPDATE audit_log SET content = 'Approve a full refund' WHERE seq = 2")`, which sends the SQL statement `"UPDATE audit_log SET content = 'Approve a full refund' WHERE seq = 2"` to the database.
- `assert verify(audit.entries()) == 1`: checks that `verify(audit.entries())` equals `1`. A false check stops the test as failed.
- `db.apply_scripts(ROOT / "sql")`: calling `db.apply_scripts(ROOT / "sql")`, which is this repository's own `apply_scripts` (in `src/streaming_assistant/infrastructure/sqlite_store.py`): run the numbered scripts (DDL, then seed); returns the names that ran.

```python
for step in ("received", "paused", "answered"):
```

- Repeats the indented lines once for each item of `("received", "paused", "answered")`, naming the current item `step`.

```python
audit.append("run-1", step, "actor", step)
```

- `audit.append("run-1", step, "actor", step)`: calling `audit.append("run-1", step, "actor", step)`, which adds `"run-1"` to the end of `audit`.

```python
db.execute("DROP TRIGGER audit_log_no_delete")
db.execute("DELETE FROM audit_log WHERE seq = 2")
assert verify(audit.entries()) == 1
```

- `db.execute("DROP TRIGGER audit_log_no_delete")`: calling `db.execute("DROP TRIGGER audit_log_no_delete")`, which sends the SQL statement `"DROP TRIGGER audit_log_no_delete"` to the database.
- `db.execute("DELETE FROM audit_log WHERE seq = 2")`: calling `db.execute("DELETE FROM audit_log WHERE seq = 2")`, which sends the SQL statement `"DELETE FROM audit_log WHERE seq = 2"` to the database.
- `assert verify(audit.entries()) == 1`: checks that `verify(audit.entries())` equals `1`. A false check stops the test as failed.

```python
def test_the_catalog_serves_pages_with_an_anchor_per_section_and_escapes_text():
```

- Defines the test `test_the_catalog_serves_pages_with_an_anchor_per_section_and_escapes_text`.

```python
catalog = PageCatalog(ROOT / "data/help_pages.json")
assert len(catalog.sections) > 30 and catalog.section("help-99#nope") is None
first = catalog.sections[0]
page = catalog.page_html(first.page_id)
assert page is not None and f'id="{first.anchor}"' in page and ":target" in page
assert catalog.page_html("help-99") is None and catalog.section(first.ref) == first
```

- `catalog = PageCatalog(ROOT / "data/help_pages.json")`: stores the result of calling `PageCatalog(ROOT / "data/help_pages.json")`, which is this repository's own `PageCatalog` (in `src/streaming_assistant/infrastructure/catalog.py`): loads `data/help_pages.json`: 30 pages with titled sections in `catalog`.
- `assert len(catalog.sections) > 30 and catalog.section("help-99#nope...`: checks that `len(catalog.sections)` is greater than `30` and `catalog.section("help-99#nope")` is nothing (`None`). A false check stops the test as failed.
- `first = catalog.sections[0]`: stores the item `catalog.sections[0]` in `first`.
- `page = catalog.page_html(first.page_id)`: stores the result of calling `catalog.page_html(first.page_id)`, which is this repository's own `page_html` (in `src/streaming_assistant/infrastructure/catalog.py`): a page as HTML with an id on every section, so `#anchor` opens it at the cited section in `page`.
- `assert page is not None and f'id="{first.anchor}"' in page and ":ta...`: checks that `page` is something (not `None`) and `f'id="{first.anchor}"'` is among `page` and `":target"` is among `page`. A false check stops the test as failed.
- `assert catalog.page_html("help-99") is None and catalog.section(fir...`: checks that `catalog.page_html("help-99")` is nothing (`None`) and `catalog.section(first.ref)` equals `first`. A false check stops the test as failed.

```python
def test_the_cold_retriever_builds_its_index_on_the_first_search_and_a_warm_one_does_not():
```

- Defines the test `test_the_cold_retriever_builds_its_index_on_the_first_search_and_a_warm_one_does_not`.

```python
catalog = PageCatalog(ROOT / "data/help_pages.json")
cold = LazyBm25Retriever(catalog)
assert cold.build_seconds is None
cold.search("shipping times")
assert cold.build_seconds is not None
warm = LazyBm25Retriever(catalog)
```

- `catalog = PageCatalog(ROOT / "data/help_pages.json")`: stores the result of calling `PageCatalog(ROOT / "data/help_pages.json")`, which is this repository's own `PageCatalog` (in `src/streaming_assistant/infrastructure/catalog.py`): loads `data/help_pages.json`: 30 pages with titled sections in `catalog`.
- `cold = LazyBm25Retriever(catalog)`: stores the result of calling `LazyBm25Retriever(catalog)`, which is this repository's own `LazyBm25Retriever` (in `src/streaming_assistant/infrastructure/catalog.py`): builds the index on the first search (the cold start the budget must account for); `warm` builds it ahead of time in `cold`.
- `assert cold.build_seconds is None`: checks that `cold.build_seconds` is nothing (`None`). A false check stops the test as failed.
- `cold.search("shipping times")`: calling `cold.search("shipping times")`, which looks for the pattern anywhere in the text.
- `assert cold.build_seconds is not None`: checks that `cold.build_seconds` is something (not `None`). A false check stops the test as failed.
- `warm = LazyBm25Retriever(catalog)`: stores the result of calling `LazyBm25Retriever(catalog)`, which is this repository's own `LazyBm25Retriever` (in `src/streaming_assistant/infrastructure/catalog.py`): builds the index on the first search (the cold start the budget must account for); `warm` builds it ahead of time in `warm`.

```python
warm.warm()
built = warm.build_seconds
warm.search("shipping times")
assert warm.build_seconds == built
```

- `warm.warm()`: calling `warm.warm()`, which is this repository's own `warm` (in `src/streaming_assistant/infrastructure/catalog.py`): build the index now.
- `built = warm.build_seconds`: stores `warm.build_seconds` in `built`.
- `warm.search("shipping times")`: calling `warm.search("shipping times")`, which looks for the pattern anywhere in the text.
- `assert warm.build_seconds == built`: checks that `warm.build_seconds` equals `built`. A false check stops the test as failed.

```python
def test_the_retrieval_cache_counts_hits_misses_and_evicts_the_oldest():
```

- Defines the test `test_the_retrieval_cache_counts_hits_misses_and_evicts_the_oldest`.

```python
cache = CachingRetriever(LazyBm25Retriever(PageCatalog(ROOT / "data/help_pages.json")), size=2)
cache.search("shipping times")
cache.search("  Shipping   TIMES ")
cache.search("refund timing")
cache.search("gift wrap")
cache.search("shipping times")
```

- `cache = CachingRetriever(LazyBm25Retriever(PageCatalog(ROOT / "data...`: stores the result of calling `CachingRetriever(LazyBm25Retriever(PageCatalog(ROOT / "data/help_pages.json")), size=2)`, which is this repository's own `CachingRetriever` (in `src/streaming_assistant/infrastructure/catalog.py`): a small LRU cache in front of a retriever, keyed by the normalized query in `cache`.
- `cache.search("shipping times")`: calling `cache.search("shipping times")`, which looks for the pattern anywhere in the text.
- `cache.search(" Shipping TIMES ")`: calling `cache.search(" Shipping TIMES ")`, which looks for the pattern anywhere in the text.
- `cache.search("refund timing")`: calling `cache.search("refund timing")`, which looks for the pattern anywhere in the text.
- `cache.search("gift wrap")`: calling `cache.search("gift wrap")`, which looks for the pattern anywhere in the text.
- `cache.search("shipping times")`: calling `cache.search("shipping times")`, which looks for the pattern anywhere in the text.

```python
assert (cache.hits, cache.misses) == (1, 4)
```

- `assert (cache.hits, cache.misses) == (1, 4)`: checks that `(cache.hits, cache.misses)` equals `(1, 4)`. A false check stops the test as failed.

```python
def request(text="Question: hi"):
```

- Defines the function `request`.
- Parameters:
  - `text`, optional (default `"Question: hi"`).

```python
return StreamRequest("system text", text, "answer.v1", "standard")
```

- `return StreamRequest("system text", text, "answer.v1", "standard")`: ends the function and gives back the result of calling `StreamRequest("system text", text, "answer.v1", "standard")`, which is this repository's own `StreamRequest` (in `src/streaming_assistant/application/ports.py`): one streamed completion.

```python
async def collect(model, req):
```

- Defines the async function `collect` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `model`.
  - `req`.

```python
return [chunk async for chunk in model.stream(req)]
```

- `return [chunk async for chunk in model.stream(req)]`: ends the function and gives back a list built by running `chunk` for each `chunk` in `model.stream(req)`.

```python
def test_the_scripted_model_cites_the_first_passage_and_counts_cached_prefixes():
```

- Defines the test `test_the_scripted_model_cites_the_first_passage_and_counts_cached_prefixes`.

```python
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
```

- `model = ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0), hallucin...`: stores the result of calling `ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0), hallucinate_every=0)`, which is this repository's own `ScriptedStreamingModel` (in `src/streaming_assistant/infrastructure/scripted_stream.py`): async streaming with counters: tokens produced (what would be billed), cancellations and their times in `model`.
- `req = StreamRequest( "stable " * 100, "Passages:\n[help-01#shipping...`: stores the result of calling `StreamRequest( "stable " * 100, "Passages:\n[help-01#shipping-times] Shipping times: St...`, which is this repository's own `StreamRequest` (in `src/streaming_assistant/application/ports.py`): one streamed completion in `req`.
- `chunks = asyncio.run(collect(model, req))`: stores the result of calling `asyncio.run(collect(model, req))`, which runs a program or a coroutine in `chunks`.
- `text = "".join(c.text for c in chunks if isinstance(c, TextDelta))`: stores the result of calling `"".join(c.text for c in chunks if isinstance(c, TextDelta))`, which glues the items of `(c.text for c in chunks if isinstance(c, TextDelta))` together with `""` between them in `text`.
- `assert text.strip() == "Standard delivery takes three days. [help-0...`: checks that `text.strip()` equals `"Standard delivery takes three days. [help-01#shipping-times]"` and `isinstance( chunks[-1], Usage )` is true (the call asks whether `chunks[-1]` is a `Usage`). A false check stops the test as failed.
- `asyncio.run(collect(model, req))`: calling `asyncio.run(collect(model, req))`, which runs a program or a coroutine.

```python
assert model.prefix_cache_hits == 1 and model.produced_tokens > 0 and model.started == 2
no_passage = asyncio.run(collect(model, StreamRequest("s", "Question: x", "answer.v1")))
assert "do not have a passage" in "".join(c.text for c in no_passage if isinstance(c, TextDelta))
```

- `assert model.prefix_cache_hits == 1 and model.produced_tokens > 0 a...`: checks that `model.prefix_cache_hits` equals `1` and `model.produced_tokens` is greater than `0` and `model.started` equals `2`. A false check stops the test as failed.
- `no_passage = asyncio.run(collect(model, StreamRequest("s", "Questio...`: stores the result of calling `asyncio.run(collect(model, StreamRequest("s", "Question: x", "answer.v1")))`, which runs a program or a coroutine in `no_passage`.
- `assert "do not have a passage" in "".join(c.text for c in no_passag...`: checks that `"do not have a passage"` is among `"".join(c.text for c in no_passage if isinstance(c, TextDelta))`. A false check stops the test as failed.

```python
def test_the_scripted_model_hallucinates_a_citation_now_and_then_when_asked_to():
```

- Defines the test `test_the_scripted_model_hallucinates_a_citation_now_and_then_when_asked_to`.

```python
model = ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0), hallucinate_every=1)
text = "".join(
    c.text
    for c in asyncio.run(collect(model, request("Passages:\n[help-01#a] H: T.\nQuestion: q")))
    if isinstance(c, TextDelta)
)
assert "[help-99#made-up]" in text
```

- `model = ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0), hallucin...`: stores the result of calling `ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0), hallucinate_every=1)`, which is this repository's own `ScriptedStreamingModel` (in `src/streaming_assistant/infrastructure/scripted_stream.py`): async streaming with counters: tokens produced (what would be billed), cancellations and their times in `model`.
- `text = "".join( c.text for c in asyncio.run(collect(model, request(...`: stores the result of calling `"".join( c.text for c in asyncio.run(collect(model, request("Passages:\n[help-01#a] H: ...`, which glues the items of `( c.text for c in asyncio.run(collect(model, request("Passages:\n[help-01#a] H: T.\nQue...` together with `""` between them in `text`.
- `assert "[help-99#made-up]" in text`: checks that `"[help-99#made-up]"` is among `text`. A false check stops the test as failed.

```python
def test_a_recording_replays_and_a_missing_one_says_how_to_record(tmp_path):
```

- Defines the test `test_a_recording_replays_and_a_missing_one_says_how_to_record`.
- Parameters:
  - `tmp_path`: a fixture; a fresh empty temporary folder for this test.

```python
path = tmp_path / "cassette.json"
inner = ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0), hallucinate_every=0)
recorder = RecordingStreamingModel(inner, path, "m", "authored")
req = request("Passages:\n[help-01#a] H: Text here.\nQuestion: q")
original = asyncio.run(collect(recorder, req))
replay = RecordedStreamingModel(path)
```

- `path = tmp_path / "cassette.json"`: stores `tmp_path / "cassette.json"`, which divides `tmp_path` and `"cassette.json"` in `path`.
- `inner = ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0), hallucin...`: stores the result of calling `ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0), hallucinate_every=0)`, which is this repository's own `ScriptedStreamingModel` (in `src/streaming_assistant/infrastructure/scripted_stream.py`): async streaming with counters: tokens produced (what would be billed), cancellations and their times in `inner`.
- `recorder = RecordingStreamingModel(inner, path, "m", "authored")`: stores the result of calling `RecordingStreamingModel(inner, path, "m", "authored")`, which is this repository's own `RecordingStreamingModel` (in `src/streaming_assistant/infrastructure/recorded_stream.py`): wraps a model and writes every stream it returns to a cassette in `recorder`.
- `req = request("Passages:\n[help-01#a] H: Text here.\nQuestion: q")`: stores the result of calling `request("Passages:\n[help-01#a] H: Text here.\nQuestion: q")` in `req`.
- `original = asyncio.run(collect(recorder, req))`: stores the result of calling `asyncio.run(collect(recorder, req))`, which runs a program or a coroutine in `original`.
- `replay = RecordedStreamingModel(path)`: stores the result of calling `RecordedStreamingModel(path)`, which is this repository's own `RecordedStreamingModel` (in `src/streaming_assistant/infrastructure/recorded_stream.py`): replays the recorded pieces; a request with no recording fails loudly in `replay`.

```python
assert asyncio.run(collect(replay, req)) == original and replay.provenance == "authored" and replay.model_id == "m"
```

- `assert asyncio.run(collect(replay, req)) == original and replay.pro...`: checks that `asyncio.run(collect(replay, req))` equals `original` and `replay.provenance` equals `"authored"` and `replay.model_id` equals `"m"`. A false check stops the test as failed.

```python
with pytest.raises(MissingRecordingError, match="make record"):
```

- `pytest.raises(MissingRecordingError, match="make record")`: the test passes only if the indented lines raise `MissingRecordingError`; it fails if nothing is raised.

```python
asyncio.run(collect(replay, request("Question: something else")))
```

- `asyncio.run(collect(replay, request("Question: something else")))`: calling `asyncio.run(collect(replay, request("Question: something else")))`, which runs a program or a coroutine.

```python
with pytest.raises(MissingRecordingError):
```

- `pytest.raises(MissingRecordingError)`: the test passes only if the indented lines raise `MissingRecordingError`; it fails if nothing is raised.

```python
asyncio.run(collect(replay, StreamRequest(req.system, req.user, "answer.v2")))
```

- `asyncio.run(collect(replay, StreamRequest(req.system, req.user, "an...`: calling `asyncio.run(collect(replay, StreamRequest(req.system, req.user, "answer.v2")))`, which runs a program or a coroutine.

```python
def test_the_committed_cassette_replays_its_samples_and_says_it_is_not_a_model_recording():
```

- Defines the test `test_the_committed_cassette_replays_its_samples_and_says_it_is_not_a_model_recording`.

```python
replay = RecordedStreamingModel(ROOT / "tests/fixtures/cassettes/stream-v1.json")
assert "not a model recording" in replay.provenance
```

- `replay = RecordedStreamingModel(ROOT / "tests/fixtures/cassettes/st...`: stores the result of calling `RecordedStreamingModel(ROOT / "tests/fixtures/cassettes/stream-v1.json")`, which is this repository's own `RecordedStreamingModel` (in `src/streaming_assistant/infrastructure/recorded_stream.py`): replays the recorded pieces; a request with no recording fails loudly in `replay`.
- `assert "not a model recording" in replay.provenance`: checks that `"not a model recording"` is among `replay.provenance`. A false check stops the test as failed.

```python
class FakeStream:
```

- Defines the class `FakeStream`.

```python
def __init__(self, texts, stop_reason="end_turn", error=None):
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `texts`.
  - `stop_reason`, optional (default `"end_turn"`).
  - `error`, optional (default `None`).

```python
self.text_stream = self._texts(texts, error)
self._stop = stop_reason
```

- `self.text_stream = self._texts(texts, error)`: stores the result of calling `self._texts(texts, error)` in `self.text_stream`.
- `self._stop = stop_reason`: stores the value of `stop_reason` in `self._stop`.

```python
@staticmethod
async def _texts(texts, error):
```

- Defines the async method `_texts` (a coroutine: calling it makes a job for the event loop to run).
- `@staticmethod`: a method of the class that does not receive an object
- Parameters:
  - `texts`.
  - `error`.

> **`@property`, `@staticmethod`, `@classmethod`.** `@property` lets a method be read like an attribute (`obj.size` instead of `obj.size()`). `@staticmethod` is a function that lives in the class but needs no object. `@classmethod` receives the class itself (named `cls`) instead of an object, often to build objects in another way.

```python
for text in texts:
```

- Repeats the indented lines once for each item of `texts`, naming the current item `text`.

```python
yield text
```

- `yield text`: hands a value to whoever is looping over this generator, then waits to be asked for the next.

```python
if error:
```

- Checks whether `error` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

> **`if`.** `if condition:` runs the indented lines only when the condition is true. `elif` adds another condition to try, `else` runs when none held. 'Truthy' values count as true; 'falsy' ones are `False`, `None`, zero and anything empty (`''`, `[]`, `{}`).

```python
raise error
```

- `raise error`: raises the error `error`.

```python
async def __aenter__(self):
```

- Defines the special method `__aenter__`, which Python calls itself at the right moment.
- Parameters:
  - `self`: the object (or class) the method was called on.

```python
return self
```

- `return self`: ends the function and gives back the value of `self`.

```python
async def __aexit__(self, *exc):
```

- Defines the special method `__aexit__`, which Python calls itself at the right moment.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `*exc`: collects extra positional arguments in a tuple.

```python
return False
```

- `return False`: ends the function and gives back `False`.

```python
async def get_final_message(self):
```

- Defines the async method `get_final_message` (a coroutine: calling it makes a job for the event loop to run).
- Parameters:
  - `self`: the object (or class) the method was called on.

```python
return SimpleNamespace(stop_reason=self._stop, usage=SimpleNamespace(input_tokens=11, output_tokens=7))
```

- `return SimpleNamespace(stop_reason=self._stop, usage=SimpleNamespac...`: ends the function and gives back the result of calling `SimpleNamespace(stop_reason=self._stop, usage=SimpleNamespace(input_tokens=11, output_t...`, which makes a `SimpleNamespace` object with the named values `stop_reason`, `usage`.

```python
class FakeClient:
```

- Defines the class `FakeClient`.

```python
def __init__(self, stream):
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `stream`.

```python
self.calls = []
self.messages = SimpleNamespace(stream=self._stream)
self._next = stream
```

- `self.calls = []`: stores a new list (empty) in `self.calls`.
- `self.messages = SimpleNamespace(stream=self._stream)`: stores the result of calling `SimpleNamespace(stream=self._stream)`, which makes a `SimpleNamespace` object with the named values `stream` in `self.messages`.
- `self._next = stream`: stores the value of `stream` in `self._next`.

```python
def _stream(self, **kwargs):
```

- Defines the method `_stream`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `**kwargs`: collects extra named arguments in a dict.

```python
self.calls.append(kwargs)
return self._next
```

- `self.calls.append(kwargs)`: calling `self.calls.append(kwargs)`, which adds `kwargs` to the end of `self.calls`.
- `return self._next`: ends the function and gives back `self._next`.

```python
def claude(stream):
```

- Defines the function `claude`.
- Parameters:
  - `stream`.

```python
client = FakeClient(stream)
return ClaudeStreamingModel(
    {"standard": "claude-sonnet-5-5", "fast": "claude-haiku-5-5"}, "key", client=client
), client
```

- `client = FakeClient(stream)`: stores the result of calling `FakeClient(stream)`, which makes a `FakeClient` object from `stream` in `client`.
- `return ClaudeStreamingModel( {"standard": "claude-sonnet-5-5", "fas...`: ends the function and gives back a tuple of 2 items.

```python
def test_the_claude_adapter_streams_text_then_usage_and_picks_the_model_by_tier():
```

- Defines the test `test_the_claude_adapter_streams_text_then_usage_and_picks_the_model_by_tier`.

```python
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
```

- `model, client = claude(FakeStream(["Hel", "lo"]))`: unpacks the result of calling `claude(FakeStream(["Hel", "lo"]))` into the names `model`, `client`, one item each.
- `chunks = asyncio.run(collect(model, StreamRequest("sys", "usr", "an...`: stores the result of calling `asyncio.run(collect(model, StreamRequest("sys", "usr", "answer.v1", "fast")))`, which runs a program or a coroutine in `chunks`.
- `assert [c.text for c in chunks[:2]] == ["Hel", "lo"] and chunks[2] ...`: checks that `[c.text for c in chunks[:2]]` equals `["Hel", "lo"]` and `chunks[2]` equals `Usage(11, 7)`. A false check stops the test as failed.
- `call = client.calls[0]`: stores the item `client.calls[0]` in `call`.
- `assert ( call["model"] == "claude-haiku-5-5" and call["system"] == ...`: checks that `call["model"]` equals `"claude-haiku-5-5"` and `call["system"]` equals `"sys"` and `call["messages"]` equals `[{"role": "user", "content": "usr"}]`. A false check stops the test as failed.
- `assert "temperature" not in call`: checks that `"temperature"` is not among `call`. A false check stops the test as failed.

```python
def response(status):
```

- Defines the function `response`.
- Parameters:
  - `status`.

```python
return httpx.Response(status, request=httpx.Request("POST", "https://api.example"))
```

- `return httpx.Response(status, request=httpx.Request("POST", "https:...`: ends the function and gives back the result of calling `httpx.Response(status, request=httpx.Request("POST", "https://api.example"))`, which makes a `Response` object from `status` with the named values `request`.

```python
def test_the_claude_adapter_maps_provider_failures_to_the_assistants_named_errors():
```

- Defines the test `test_the_claude_adapter_maps_provider_failures_to_the_assistants_named_errors`.

```python
limited = anthropic.RateLimitError("slow down", response=response(429), body=None)
broken = anthropic.APIStatusError("boom", response=response(500), body=None)
refused = FakeStream(["I"], stop_reason="refusal")
```

- `limited = anthropic.RateLimitError("slow down", response=response(4...`: stores the result of calling `anthropic.RateLimitError("slow down", response=response(429), body=None)`, which makes a `RateLimitError` object from `"slow down"` with the named values `response`, `body` in `limited`.
- `broken = anthropic.APIStatusError("boom", response=response(500), b...`: stores the result of calling `anthropic.APIStatusError("boom", response=response(500), body=None)`, which makes a `APIStatusError` object from `"boom"` with the named values `response`, `body` in `broken`.
- `refused = FakeStream(["I"], stop_reason="refusal")`: stores the result of calling `FakeStream(["I"], stop_reason="refusal")`, which makes a `FakeStream` object from `["I"]` with the named values `stop_reason` in `refused`.

```python
for stream, expected in (
    (FakeStream([], error=limited), RateLimitedError),
    (FakeStream([], error=broken), ProviderError),
    (refused, RefusedError),
):
```

- Repeats the indented lines once for each item of `( (FakeStream([], error=limited), RateLimitedError), (FakeStream([], error=broken), Pro...`, naming the current item the names `stream`, `expected`.

```python
model, _ = claude(stream)
```

- `model, _ = claude(stream)`: unpacks the result of calling `claude(stream)` into the names `model`, `_`, one item each.

```python
with pytest.raises(expected):
```

- `pytest.raises(expected)`: the test passes only if the indented lines raise `expected`; it fails if nothing is raised.

```python
asyncio.run(collect(model, request()))
```

- `asyncio.run(collect(model, request()))`: calling `asyncio.run(collect(model, request()))`, which runs a program or a coroutine.

```python
def test_the_claude_adapter_needs_a_key():
```

- Defines the test `test_the_claude_adapter_needs_a_key`.

```python
with pytest.raises(ConfigurationError):
```

- `pytest.raises(ConfigurationError)`: the test passes only if the indented lines raise `ConfigurationError`; it fails if nothing is raised.

```python
ClaudeStreamingModel({"standard": "m"}, None)
```

- `ClaudeStreamingModel({"standard": "m"}, None)`: calling `ClaudeStreamingModel({"standard": "m"}, None)`, which is this repository's own `ClaudeStreamingModel` (in `src/streaming_assistant/infrastructure/claude_stream.py`): one streamed Messages API call.

```python
def test_environment_readers_name_the_bad_variable():
```

- Defines the test `test_environment_readers_name_the_bad_variable`.

```python
env = {"A": " x ", "N": "5", "F": "0.5", "C": "on", "E": ""}
assert read_text(env, "A") == "x" and read_int(env, "N", 1) == 5 and read_float(env, "F", 1.0) == 0.5
assert read_choice(env, "C", "off", frozenset({"on", "off"})) == "on" and read_optional(env, "E") is None
```

- `env = {"A": " x ", "N": "5", "F": "0.5", "C": "on", "E": ""}`: stores a new dict with 5 entries in `env`.
- `assert read_text(env, "A") == "x" and read_int(env, "N", 1) == 5 an...`: checks that `read_text(env, "A")` equals `"x"` and `read_int(env, "N", 1)` equals `5` and `read_float(env, "F", 1.0)` equals `0.5`. A false check stops the test as failed.
- `assert read_choice(env, "C", "off", frozenset({"on", "off"})) == "o...`: checks that `read_choice(env, "C", "off", frozenset({"on", "off"}))` equals `"on"` and `read_optional(env, "E")` is nothing (`None`). A false check stops the test as failed.

```python
for call in (
    lambda: read_text(env, "E"),
    lambda: read_int({"N": "x"}, "N", 1),
    lambda: read_int({"N": "0"}, "N", 1),
    lambda: read_float({"F": "x"}, "F", 1.0),
    lambda: read_float({"F": "-1"}, "F", 1.0),
    lambda: read_choice({"C": "maybe"}, "C", "on", frozenset({"on", "off"})),
):
```

- Repeats the indented lines once for each item of `( lambda: read_text(env, "E"), lambda: read_int({"N": "x"}, "N", 1), lambda: read_int({...`, naming the current item `call`.

```python
with pytest.raises(ConfigurationError):
```

- `pytest.raises(ConfigurationError)`: the test passes only if the indented lines raise `ConfigurationError`; it fails if nothing is raised.

```python
call()
```

- `call()`: calling `call()`.

```python
def test_settings_have_safe_defaults_and_reject_bad_values():
```

- Defines the test `test_settings_have_safe_defaults_and_reject_bad_values`.

```python
settings = Settings.from_environ({})
assert settings.model_adapter == "scripted" and settings.pause_enabled and settings.port == 8100
assert settings.first_token_budget_ms > 0
```

- `settings = Settings.from_environ({})`: stores the result of calling `Settings.from_environ({})`, which is this repository's own `from_environ` (in `src/streaming_assistant/infrastructure/settings.py`): read and validate; raises `ConfigurationError` naming the first bad variable in `settings`.
- `assert settings.model_adapter == "scripted" and settings.pause_enab...`: checks that `settings.model_adapter` equals `"scripted"` and `settings.pause_enabled` is truthy and `settings.port` equals `8100`. A false check stops the test as failed.
- `assert settings.first_token_budget_ms > 0`: checks that `settings.first_token_budget_ms` is greater than `0`. A false check stops the test as failed.

```python
with pytest.raises(ConfigurationError, match="MODEL_ADAPTER"):
```

- `pytest.raises(ConfigurationError, match="MODEL_ADAPTER")`: the test passes only if the indented lines raise `ConfigurationError`; it fails if nothing is raised.

```python
Settings.from_environ({"MODEL_ADAPTER": "gpt"})
```

- `Settings.from_environ({"MODEL_ADAPTER": "gpt"})`: calling `Settings.from_environ({"MODEL_ADAPTER": "gpt"})`, which is this repository's own `from_environ` (in `src/streaming_assistant/infrastructure/settings.py`): read and validate; raises `ConfigurationError` naming the first bad variable.

```python
def test_retry_backs_off_with_full_jitter_and_raises_the_last_failure():
```

- Defines the test `test_retry_backs_off_with_full_jitter_and_raises_the_last_failure`.

```python
pauses: list[float] = []
attempts: list[int] = []
```

- `pauses: list[float] = []`: stores a new list (empty) in `pauses`, whose type is declared as `list[float]`.
- `attempts: list[int] = []`: stores a new list (empty) in `attempts`, whose type is declared as `list[int]`.

> **A type hint.** `x: int = 5` stores 5 in `x` and records that `x` is meant to hold an `int`. Python itself does not enforce the hint; the type checker `mypy` reads it before the program runs and complains if the code disagrees.

```python
def flaky():
```

- Defines the function `flaky`.

```python
attempts.append(1)
```

- `attempts.append(1)`: calling `attempts.append(1)`, which adds `1` to the end of `attempts`.

```python
if len(attempts) < 3:
```

- Checks whether `len(attempts)` is less than `3`. If so, the indented lines run.

```python
raise ConnectionError("x")
```

- `raise ConnectionError("x")`: stops with an error of kind `ConnectionError` with the message `"x"`. Whoever called this code must handle it or the program stops.

```python
return "ok"
```

- `return "ok"`: ends the function and gives back the text `'ok'`.

```python
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
```

- `assert ( retry( flaky, attempts=4, base_delay_seconds=1.0, retry_on...`: checks that `retry( flaky, attempts=4, base_delay_seconds=1.0, retry_on=(ConnectionError,), sleep=pa...` equals `"ok"`. A false check stops the test as failed.

```python
assert len(pauses) == 2 and 0 <= pauses[0] <= 1.0 and 0 <= pauses[1] <= 2.0
```

- `assert len(pauses) == 2 and 0 <= pauses[0] <= 1.0 and 0 <= pauses[1...`: checks that `len(pauses)` equals `2` and `0` is less than or equal to `pauses[0]` and `pauses[0]` is less than or equal to `1.0` and `0` is less than or equal to `pauses[1]` and `pauses[1]` is less than or equal to `2.0`. A false check stops the test as failed.

```python
with pytest.raises(ConnectionError):
```

- `pytest.raises(ConnectionError)`: the test passes only if the indented lines raise `ConnectionError`; it fails if nothing is raised.

```python
retry(
    lambda: (_ for _ in ()).throw(ConnectionError("always")),
    attempts=2,
    base_delay_seconds=0,
    retry_on=(ConnectionError,),
    sleep=lambda s: None,
)
```

- `retry( lambda: (_ for _ in ()).throw(ConnectionError("always")), at...`: calling `retry( lambda: (_ for _ in ()).throw(ConnectionError("always")), attempts=2, base_delay...`, which is this repository's own `retry` (in `src/streaming_assistant/infrastructure/retry.py`): call `operation` up to `attempts` times, backing off after each failure in `retry_on` The named values are `attempts`, `base_delay_seconds`, `retry_on`, `sleep`..

```python
with pytest.raises(ValueError, match="at least 1"):
```

- `pytest.raises(ValueError, match="at least 1")`: the test passes only if the indented lines raise `ValueError`; it fails if nothing is raised.

```python
retry(lambda: 1, attempts=0, base_delay_seconds=0, retry_on=())
```

- `retry(lambda: 1, attempts=0, base_delay_seconds=0, retry_on=())`: calling `retry(lambda: 1, attempts=0, base_delay_seconds=0, retry_on=())`, which is this repository's own `retry` (in `src/streaming_assistant/infrastructure/retry.py`): call `operation` up to `attempts` times, backing off after each failure in `retry_on` The named values are `attempts`, `base_delay_seconds`, `retry_on`..

```python
def test_shutdown_signal_wakes_waiters_and_logfmt_quotes_values():
```

- Defines the test `test_shutdown_signal_wakes_waiters_and_logfmt_quotes_values`.

```python
shutdown = ShutdownSignal()
assert not shutdown.requested and shutdown.wait(0.01) is False
shutdown.request()
assert shutdown.requested and shutdown.wait(0.01) is True
stream = io.StringIO()
configure_logging("INFO", stream)
```

- `shutdown = ShutdownSignal()`: stores the result of calling `ShutdownSignal()`, which is this repository's own `ShutdownSignal` (in `src/streaming_assistant/infrastructure/shutdown.py`): a flag that SIGINT and SIGTERM set, which work loops check between units of work in `shutdown`.
- `assert not shutdown.requested and shutdown.wait(0.01) is False`: checks that it is not the case that `shutdown.requested` is truthy and `shutdown.wait(0.01)` is exactly `False`. A false check stops the test as failed.
- `shutdown.request()`: calling `shutdown.request()`.
- `assert shutdown.requested and shutdown.wait(0.01) is True`: checks that `shutdown.requested` is truthy and `shutdown.wait(0.01)` is exactly `True`. A false check stops the test as failed.
- `stream = io.StringIO()`: stores the result of calling `io.StringIO()`, which makes a `StringIO` object in `stream`.
- `configure_logging("INFO", stream)`: calling `configure_logging("INFO", stream)`, which is this repository's own `configure_logging` (in `src/streaming_assistant/infrastructure/logging.py`): send every log record to `stream` (stderr by default) as logfmt.

```python
logging.getLogger("t").info("hello world", extra=fields(run_id="r 1", n=3))
line = stream.getvalue()
assert 'msg="hello world"' in line and 'run_id="r 1"' in line and "n=3" in line
assert isinstance(LogfmtFormatter(), logging.Formatter)
```

- `logging.getLogger("t").info("hello world", extra=fields(run_id="r 1...`: calling `logging.getLogger("t").info("hello world", extra=fields(run_id="r 1", n=3))`, which writes an INFO log line The named values are `extra`..
- `line = stream.getvalue()`: stores the result of calling `stream.getvalue()` in `line`.
- `assert 'msg="hello world"' in line and 'run_id="r 1"' in line and "...`: checks that `'msg="hello world"'` is among `line` and `'run_id="r 1"'` is among `line` and `"n=3"` is among `line`. A false check stops the test as failed.
- `assert isinstance(LogfmtFormatter(), logging.Formatter)`: checks that `isinstance(LogfmtFormatter(), logging.Formatter)` is true (the call asks whether `LogfmtFormatter()` is a `logging.Formatter`). A false check stops the test as failed.

#### `tests/unit/interfaces/test_http_and_cli.py`

- This file has no docstring at the top.

```python
import asyncio
import json
import os
from pathlib import Path

import httpx
import pytest
```

- `import asyncio`: makes the module `asyncio` available (the standard library's tools for asynchronous code (many waits interleaved on one thread)).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import os`: makes the module `os` available (operating-system services: environment variables, paths, processes).
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `import httpx`: makes the module `httpx` available (an HTTP client library).
- `import pytest`: makes the module `pytest` available (the test framework).

```python
from streaming_assistant.infrastructure.scripted_stream import Pace, ScriptedStreamingModel
from streaming_assistant.infrastructure.settings import Settings
from streaming_assistant.interfaces import cli
from streaming_assistant.interfaces.http import create_app, encode
from streaming_assistant.interfaces.wiring import build_components, database_exists

ROOT = Path(__file__).resolve().parents[3]
```

- `from streaming_assistant.infrastructure.scripted_stream import ...`: takes names from `streaming_assistant.infrastructure.scripted_stream`, this repository's own code. (`Pace`: Latency settings in milliseconds.) (`ScriptedStreamingModel`: Async streaming with counters: tokens produced (what would be billed), cancellations and their times.)
- `from streaming_assistant.infrastructure.settings import ...`: takes names from `streaming_assistant.infrastructure.settings`, this repository's own code. (`Settings`: Everything the programs read from the environment.)
- `from streaming_assistant.interfaces import ...`: takes names from `streaming_assistant.interfaces`, this repository's own code. (`cli`: a name defined in this repository.)
- `from streaming_assistant.interfaces.http import ...`: takes names from `streaming_assistant.interfaces.http`, this repository's own code. (`create_app`: Build the app over the assistant and its collaborators.) (`encode`: One server-sent event.)
- `from streaming_assistant.interfaces.wiring import ...`: takes names from `streaming_assistant.interfaces.wiring`, this repository's own code. (`build_components`: Wire everything.) (`database_exists`: True when the database file is already there (an in-memory database never is: it starts empty).)
- `ROOT = Path(__file__).resolve().parents[3]`: stores the item `Path(__file__).resolve().parents[3]` in `ROOT`.

```python
CUSTOMER = {"Authorization": "Bearer demo-customer-token"}
REVIEWER = {"Authorization": "Bearer demo-reviewer-token"}
SHIPPING = "A question about shipping times: standard delivery takes three to five business days after dispatch?"
LATE_REFUND = "Can I get a refund on an order from seventy five days ago?"
FAST = Pace(0, 0, 0, 0, jitter=0)
```

- `CUSTOMER = {"Authorization": "Bearer demo-customer-token"}`: stores a new dict with 1 entries in `CUSTOMER`.
- `REVIEWER = {"Authorization": "Bearer demo-reviewer-token"}`: stores a new dict with 1 entries in `REVIEWER`.
- `SHIPPING = "A question about shipping times: standard delivery take...`: stores the text `'A question about shipping times: standard delivery takes three to five business days a...` in `SHIPPING`.
- `LATE_REFUND = "Can I get a refund on an order from seventy five day...`: stores the text `'Can I get a refund on an order from seventy five days ago?'` in `LATE_REFUND`.
- `FAST = Pace(0, 0, 0, 0, jitter=0)`: stores the result of calling `Pace(0, 0, 0, 0, jitter=0)`, which is this repository's own `Pace` (in `src/streaming_assistant/infrastructure/scripted_stream.py`): latency settings in milliseconds in `FAST`.

```python
def settings(**env):
```

- Defines the function `settings`.
- Parameters:
  - `**env`: collects extra named arguments in a dict.

```python
return Settings.from_environ({"PROJECT_ROOT": str(ROOT), "DATABASE": ":memory:", "TTFT_STANDARD_MS": "0", **env})
```

- `return Settings.from_environ({"PROJECT_ROOT": str(ROOT), "DATABASE"...`: ends the function and gives back the result of calling `Settings.from_environ({"PROJECT_ROOT": str(ROOT), "DATABASE": ":memory:", "TTFT_STANDAR...`, which is this repository's own `from_environ` (in `src/streaming_assistant/infrastructure/settings.py`): read and validate; raises `ConfigurationError` naming the first bad variable.

```python
def client_for(components):
```

- Defines the function `client_for`.
- Parameters:
  - `components`.

```python
app = create_app(
    components.assistant, components.desk, components.catalog, components.authenticator, components.audit
)
return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
```

- `app = create_app( components.assistant, components.desk, components...`: stores the result of calling `create_app( components.assistant, components.desk, components.catalog, components.authe...`, which is this repository's own `create_app` (in `src/streaming_assistant/interfaces/http.py`): build the app over the assistant and its collaborators in `app`.
- `return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), ba...`: ends the function and gives back the result of calling `httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")`, which makes a `AsyncClient` object with the named values `transport`, `base_url`.

```python
def parse(body):
```

- Defines the function `parse`.
- Parameters:
  - `body`.

```python
out, name = [], ""
```

- `out, name = [], ""`: unpacks a tuple of 2 items into the names `out`, `name`, one item each.

```python
for line in body.splitlines():
```

- Repeats the indented lines once for each item of `body.splitlines()`, naming the current item `line`.

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
out.append((name, json.loads(line.removeprefix("data: "))))
```

- `out.append((name, json.loads(line.removeprefix("data: "))))`: calling `out.append((name, json.loads(line.removeprefix("data: "))))`, which adds `(name, json.loads(line.removeprefix("data: ")))` to the end of `out`.

```python
return out
```

- `return out`: ends the function and gives back the value of `out`.

```python
def components():
```

- Defines the function `components`.

```python
model = ScriptedStreamingModel(FAST, hallucinate_every=0)
return build_components(settings(), model=model, fresh=True)
```

- `model = ScriptedStreamingModel(FAST, hallucinate_every=0)`: stores the result of calling `ScriptedStreamingModel(FAST, hallucinate_every=0)`, which is this repository's own `ScriptedStreamingModel` (in `src/streaming_assistant/infrastructure/scripted_stream.py`): async streaming with counters: tokens produced (what would be billed), cancellations and their times in `model`.
- `return build_components(settings(), model=model, fresh=True)`: ends the function and gives back the result of calling `build_components(settings(), model=model, fresh=True)`, which is this repository's own `build_components` (in `src/streaming_assistant/interfaces/wiring.py`): wire everything The named values are `model`, `fresh`..

```python
def test_ask_streams_typed_events_with_a_run_id_header():
```

- Defines the test `test_ask_streams_typed_events_with_a_run_id_header`.

```python
async def go():
```

- Defines the async function `go` (a coroutine: calling it makes a job for the event loop to run).

```python
async with client_for(components()) as client:
```

- Opens `client_for(components())` as `client` for the indented lines, and cleans it up when they end (even after an error).

```python
return await client.post("/ask", json={"question": SHIPPING}, headers=CUSTOMER)
```

- `return await client.post("/ask", json={"question": SHIPPING}, heade...`: ends the function and gives back the answer of the result of calling `client.post("/ask", json={"question": SHIPPING}, headers=CUSTOMER)`, which sends an HTTP POST request The named values are `json`, `headers`. once the wait is over.

```python
response = asyncio.run(go())
names = [name for name, _ in parse(response.text)]
assert response.status_code == 200 and response.headers["content-type"].startswith("text/event-stream")
assert response.headers["x-run-id"].startswith("run-") and response.headers["cache-control"] == "no-store"
assert names[0] == "token" and "citation" in names and names[-1] == "done"
assert (
    encode(
        __import__("streaming_assistant.application.assistant", fromlist=["Event"]).Event("token", {"text": "a"})
    )
    == 'event: token\ndata: {"text": "a"}\n\n'
)
```

- `response = asyncio.run(go())`: stores the result of calling `asyncio.run(go())`, which runs a program or a coroutine in `response`.
- `names = [name for name, _ in parse(response.text)]`: stores a list built by running `name` for each `name, _` in `parse(response.text)` in `names`.
- `assert response.status_code == 200 and response.headers["content-ty...`: checks that `response.status_code` equals `200` and `response.headers["content-type"].startswith("text/event-stream")` is true (the call asks whether `response.headers["content-type"]` begins with `"text/event-stream"`). A false check stops the test as failed.
- `assert response.headers["x-run-id"].startswith("run-") and response...`: checks that `response.headers["x-run-id"].startswith("run-")` is true (the call asks whether `response.headers["x-run-id"]` begins with `"run-"`) and `response.headers["cache-control"]` equals `"no-store"`. A false check stops the test as failed.
- `assert names[0] == "token" and "citation" in names and names[-1] ==...`: checks that `names[0]` equals `"token"` and `"citation"` is among `names` and `names[-1]` equals `"done"`. A false check stops the test as failed.
- `assert ( encode( __import__("streaming_assistant.application.assist...`: checks that `encode( __import__("streaming_assistant.application.assistant", fromlist=["Event"]).Eve...` equals `'event: token\ndata: {"text": "a"}\n\n'`. A false check stops the test as failed.

```python
def test_a_missing_or_wrong_token_is_a_401_and_a_bad_body_is_a_422():
```

- Defines the test `test_a_missing_or_wrong_token_is_a_401_and_a_bad_body_is_a_422`.

```python
async def go():
```

- Defines the async function `go` (a coroutine: calling it makes a job for the event loop to run).

```python
async with client_for(components()) as client:
```

- Opens `client_for(components())` as `client` for the indented lines, and cleans it up when they end (even after an error).

```python
return (
    (await client.post("/ask", json={"question": SHIPPING})).status_code,
    (
        await client.post("/ask", json={"question": SHIPPING}, headers={"Authorization": "Bearer nope"})
    ).status_code,
    (await client.post("/ask", json={"question": "x"}, headers=CUSTOMER)).status_code,
    (await client.get("/runs/run-1/status")).status_code,
)
```

- `return ( (await client.post("/ask", json={"question": SHIPPING})).s...`: ends the function and gives back a tuple of 4 items.

```python
assert asyncio.run(go()) == (401, 401, 422, 401)
```

- `assert asyncio.run(go()) == (401, 401, 422, 401)`: checks that `asyncio.run(go())` equals `(401, 401, 422, 401)`. A false check stops the test as failed.

```python
def test_the_whole_pause_review_resume_path_over_http_with_role_checks():
```

- Defines the test `test_the_whole_pause_review_resume_path_over_http_with_role_checks`.

```python
async def go():
```

- Defines the async function `go` (a coroutine: calling it makes a job for the event loop to run).

```python
async with client_for(components()) as client:
```

- Opens `client_for(components())` as `client` for the indented lines, and cleans it up when they end (even after an error).

```python
asked = await client.post("/ask", json={"question": LATE_REFUND}, headers=CUSTOMER)
run_id = asked.headers["x-run-id"]
customer_sees_queue = await client.get("/reviews", headers=CUSTOMER)
waiting = (await client.get("/reviews", headers=REVIEWER)).json()
early = await client.get(f"/runs/{run_id}/resume", headers=CUSTOMER)
status_before = (await client.get(f"/runs/{run_id}/status", headers=CUSTOMER)).json()["status"]
```

- `asked = await client.post("/ask", json={"question": LATE_REFUND}, h...`: stores the answer of the result of calling `client.post("/ask", json={"question": LATE_REFUND}, headers=CUSTOMER)`, which sends an HTTP POST request The named values are `json`, `headers`. once the wait is over in `asked`.
- `run_id = asked.headers["x-run-id"]`: stores the item `asked.headers["x-run-id"]` in `run_id`.
- `customer_sees_queue = await client.get("/reviews", headers=CUSTOMER)`: stores the answer of the result of calling `client.get("/reviews", headers=CUSTOMER)`, which looks up `"/reviews"` in `client`; a second value is the answer when the key is missing The named values are `headers`. once the wait is over in `customer_sees_queue`.
- `waiting = (await client.get("/reviews", headers=REVIEWER)).json()`: stores the result of calling `(await client.get("/reviews", headers=REVIEWER)).json()` in `waiting`.
- `early = await client.get(f"/runs/{run_id}/resume", headers=CUSTOMER)`: stores the answer of the result of calling `client.get(f"/runs/{run_id}/resume", headers=CUSTOMER)`, which looks up `f"/runs/{run_id}/resume"` in `client`; a second value is the answer when the key is missing The named values are `headers`. once the wait is over in `early`.
- `status_before = (await client.get(f"/runs/{run_id}/status", headers...`: stores the item `(await client.get(f"/runs/{run_id}/status", headers=CUSTOMER)).json()["status"]` in `status_before`.

```python
ref = waiting[0]["retrieved"][0]
bad = await client.post(
    f"/reviews/{run_id}/answer", headers=REVIEWER, json={"reviewer_id": "ana", "answer": "ok"}
)
missing = await client.post(
    "/reviews/run-x/answer", headers=REVIEWER, json={"reviewer_id": "ana", "answer": "ok", "no_page": True}
)
good = await client.post(
    f"/reviews/{run_id}/answer",
    headers=REVIEWER,
    json={"reviewer_id": "ana", "answer": "Store credit approved.", "cited": [ref]},
)
resumed = await client.get(f"/runs/{run_id}/resume", headers=CUSTOMER)
audit = (await client.get("/audit/verify", headers=REVIEWER)).json()
```

- `ref = waiting[0]["retrieved"][0]`: stores the item `waiting[0]["retrieved"][0]` in `ref`.
- `bad = await client.post( f"/reviews/{run_id}/answer", headers=REVIE...`: stores the answer of the result of calling `client.post( f"/reviews/{run_id}/answer", headers=REVIEWER, json={"reviewer_id": "ana",...`, which sends an HTTP POST request The named values are `headers`, `json`. once the wait is over in `bad`.
- `missing = await client.post( "/reviews/run-x/answer", headers=REVIE...`: stores the answer of the result of calling `client.post( "/reviews/run-x/answer", headers=REVIEWER, json={"reviewer_id": "ana", "an...`, which sends an HTTP POST request The named values are `headers`, `json`. once the wait is over in `missing`.
- `good = await client.post( f"/reviews/{run_id}/answer", headers=REVI...`: stores the answer of the result of calling `client.post( f"/reviews/{run_id}/answer", headers=REVIEWER, json={"reviewer_id": "ana",...`, which sends an HTTP POST request The named values are `headers`, `json`. once the wait is over in `good`.
- `resumed = await client.get(f"/runs/{run_id}/resume", headers=CUSTOMER)`: stores the answer of the result of calling `client.get(f"/runs/{run_id}/resume", headers=CUSTOMER)`, which looks up `f"/runs/{run_id}/resume"` in `client`; a second value is the answer when the key is missing The named values are `headers`. once the wait is over in `resumed`.
- `audit = (await client.get("/audit/verify", headers=REVIEWER)).json()`: stores the result of calling `(await client.get("/audit/verify", headers=REVIEWER)).json()` in `audit`.

```python
forbidden = await client.get("/audit/verify", headers=CUSTOMER)
unknown_status = await client.get("/runs/run-x/status", headers=CUSTOMER)
```

- `forbidden = await client.get("/audit/verify", headers=CUSTOMER)`: stores the answer of the result of calling `client.get("/audit/verify", headers=CUSTOMER)`, which looks up `"/audit/verify"` in `client`; a second value is the answer when the key is missing The named values are `headers`. once the wait is over in `forbidden`.
- `unknown_status = await client.get("/runs/run-x/status", headers=CUS...`: stores the answer of the result of calling `client.get("/runs/run-x/status", headers=CUSTOMER)`, which looks up `"/runs/run-x/status"` in `client`; a second value is the answer when the key is missing The named values are `headers`. once the wait is over in `unknown_status`.

```python
return (
    asked,
    customer_sees_queue,
    waiting,
    early,
    status_before,
    bad,
    missing,
    good,
    resumed,
    audit,
    forbidden,
    unknown_status,
)
```

- `return ( asked, customer_sees_queue, waiting, early, status_before,...`: ends the function and gives back a tuple of 12 items.

```python
asked, queue, waiting, early, before, bad, missing, good, resumed, audit, forbidden, unknown = asyncio.run(go())
assert [n for n, _ in parse(asked.text)] == ["paused", "done"] and queue.status_code == 403
assert waiting[0]["reason"] == "policy_exception" and early.status_code == 409 and before == "waiting"
assert bad.status_code == 422 and missing.status_code == 404 and good.json()["status"] == "answered"
text = "".join(data["text"] for name, data in parse(resumed.text) if name == "token")
assert "Store credit approved." in text and audit["first_broken_index"] is None and audit["entries"] >= 6
```

- `asked, queue, waiting, early, before, bad, missing, good, resumed, ...`: unpacks the result of calling `asyncio.run(go())`, which runs a program or a coroutine into the names `asked`, `queue`, `waiting`, `early`, `before`, `bad`, `missing`, `good`, `resumed`, `audit`, `forbidden`, `unknown`, one item each.
- `assert [n for n, _ in parse(asked.text)] == ["paused", "done"] and ...`: checks that `[n for n, _ in parse(asked.text)]` equals `["paused", "done"]` and `queue.status_code` equals `403`. A false check stops the test as failed.
- `assert waiting[0]["reason"] == "policy_exception" and early.status_...`: checks that `waiting[0]["reason"]` equals `"policy_exception"` and `early.status_code` equals `409` and `before` equals `"waiting"`. A false check stops the test as failed.
- `assert bad.status_code == 422 and missing.status_code == 404 and go...`: checks that `bad.status_code` equals `422` and `missing.status_code` equals `404` and `good.json()["status"]` equals `"answered"`. A false check stops the test as failed.
- `text = "".join(data["text"] for name, data in parse(resumed.text) i...`: stores the result of calling `"".join(data["text"] for name, data in parse(resumed.text) if name == "token")`, which glues the items of `(data["text"] for name, data in parse(resumed.text) if name == "token")` together with `""` between them in `text`.
- `assert "Store credit approved." in text and audit["first_broken_ind...`: checks that `"Store credit approved."` is among `text` and `audit["first_broken_index"]` is nothing (`None`) and `audit["entries"]` is greater than or equal to `6`. A false check stops the test as failed.

```python
assert forbidden.status_code == 403 and unknown.status_code == 404
```

- `assert forbidden.status_code == 403 and unknown.status_code == 404`: checks that `forbidden.status_code` equals `403` and `unknown.status_code` equals `404`. A false check stops the test as failed.

```python
def test_stop_returns_202_and_pages_open_with_their_anchors():
```

- Defines the test `test_stop_returns_202_and_pages_open_with_their_anchors`.

```python
async def go():
```

- Defines the async function `go` (a coroutine: calling it makes a job for the event loop to run).

```python
async with client_for(components()) as client:
```

- Opens `client_for(components())` as `client` for the indented lines, and cleans it up when they end (even after an error).

```python
stop = await client.post("/runs/run-1/stop", headers=CUSTOMER)
page = await client.get("/pages/help-01")
missing = await client.get("/pages/help-99")
home = await client.get("/")
review = await client.get("/review")
health = await client.get("/healthz")
```

- `stop = await client.post("/runs/run-1/stop", headers=CUSTOMER)`: stores the answer of the result of calling `client.post("/runs/run-1/stop", headers=CUSTOMER)`, which sends an HTTP POST request The named values are `headers`. once the wait is over in `stop`.
- `page = await client.get("/pages/help-01")`: stores the answer of the result of calling `client.get("/pages/help-01")`, which looks up `"/pages/help-01"` in `client`; a second value is the answer when the key is missing once the wait is over in `page`.
- `missing = await client.get("/pages/help-99")`: stores the answer of the result of calling `client.get("/pages/help-99")`, which looks up `"/pages/help-99"` in `client`; a second value is the answer when the key is missing once the wait is over in `missing`.
- `home = await client.get("/")`: stores the answer of the result of calling `client.get("/")`, which looks up `"/"` in `client`; a second value is the answer when the key is missing once the wait is over in `home`.
- `review = await client.get("/review")`: stores the answer of the result of calling `client.get("/review")`, which looks up `"/review"` in `client`; a second value is the answer when the key is missing once the wait is over in `review`.
- `health = await client.get("/healthz")`: stores the answer of the result of calling `client.get("/healthz")`, which looks up `"/healthz"` in `client`; a second value is the answer when the key is missing once the wait is over in `health`.

```python
return stop, page, missing, home, review, health
```

- `return stop, page, missing, home, review, health`: ends the function and gives back a tuple of 6 items.

```python
stop, page, missing, home, review, health = asyncio.run(go())
assert stop.status_code == 202 and "<section id=" in page.text and missing.status_code == 404
assert "EventSource" in home.text or "fetch(" in home.text
assert review.status_code == 200 and health.json() == {"status": "ok"}
```

- `stop, page, missing, home, review, health = asyncio.run(go())`: unpacks the result of calling `asyncio.run(go())`, which runs a program or a coroutine into the names `stop`, `page`, `missing`, `home`, `review`, `health`, one item each.
- `assert stop.status_code == 202 and "<section id=" in page.text and ...`: checks that `stop.status_code` equals `202` and `"<section id="` is among `page.text` and `missing.status_code` equals `404`. A false check stops the test as failed.
- `assert "EventSource" in home.text or "fetch(" in home.text`: checks that `"EventSource"` is among `home.text` or `"fetch("` is among `home.text`. A false check stops the test as failed.
- `assert review.status_code == 200 and health.json() == {"status": "ok"}`: checks that `review.status_code` equals `200` and `health.json()` equals `{"status": "ok"}`. A false check stops the test as failed.

```python
def test_the_database_is_detected_by_file_and_never_for_memory(tmp_path):
```

- Defines the test `test_the_database_is_detected_by_file_and_never_for_memory`.
- Parameters:
  - `tmp_path`: a fixture; a fresh empty temporary folder for this test.

```python
assert not database_exists(settings())
assert not database_exists(settings(DATABASE=str(tmp_path / "x.sqlite")))
(tmp_path / "x.sqlite").write_bytes(b"")
assert database_exists(settings(DATABASE=str(tmp_path / "x.sqlite")))
```

- `assert not database_exists(settings())`: checks that it is not the case that `database_exists(settings())` is true (the call is this repository's own `database_exists` (in `src/streaming_assistant/interfaces/wiring.py`): true when the database file is already there (an in-memory database never is: it starts empty)). A false check stops the test as failed.
- `assert not database_exists(settings(DATABASE=str(tmp_path / "x.sqli...`: checks that it is not the case that `database_exists(settings(DATABASE=str(tmp_path / "x.sqlite")))` is true (the call is this repository's own `database_exists` (in `src/streaming_assistant/interfaces/wiring.py`): true when the database file is already there (an in-memory database never is: it starts empty)). A false check stops the test as failed.
- `(tmp_path / "x.sqlite").write_bytes(b"")`: calling `(tmp_path / "x.sqlite").write_bytes(b"")`, which writes bytes to the file `tmp_path / "x.sqlite"`, replacing it.
- `assert database_exists(settings(DATABASE=str(tmp_path / "x.sqlite")))`: checks that `database_exists(settings(DATABASE=str(tmp_path / "x.sqlite")))` is true (the call is this repository's own `database_exists` (in `src/streaming_assistant/interfaces/wiring.py`): true when the database file is already there (an in-memory database never is: it starts empty)). A false check stops the test as failed.

```python
@pytest.fixture
def env(monkeypatch, tmp_path):
```

- Defines the function `env`.
- `@pytest.fixture`: marks the function as a pytest fixture.
- Parameters:
  - `monkeypatch`.
  - `tmp_path`.

```python
monkeypatch.setenv("PROJECT_ROOT", str(ROOT))
monkeypatch.setenv("DATABASE", str(tmp_path / "assistant.sqlite"))
monkeypatch.setenv("TTFT_STANDARD_MS", "0")
monkeypatch.setenv("TTFT_FAST_MS", "0")
monkeypatch.setenv("TOKEN_MS", "0")
monkeypatch.setenv("LOG_LEVEL", "WARNING")
```

- `monkeypatch.setenv("PROJECT_ROOT", str(ROOT))`: calling `monkeypatch.setenv("PROJECT_ROOT", str(ROOT))`, which sets an environment variable for the duration of the test.
- `monkeypatch.setenv("DATABASE", str(tmp_path / "assistant.sqlite"))`: calling `monkeypatch.setenv("DATABASE", str(tmp_path / "assistant.sqlite"))`, which sets an environment variable for the duration of the test.
- `monkeypatch.setenv("TTFT_STANDARD_MS", "0")`: calling `monkeypatch.setenv("TTFT_STANDARD_MS", "0")`, which sets an environment variable for the duration of the test.
- `monkeypatch.setenv("TTFT_FAST_MS", "0")`: calling `monkeypatch.setenv("TTFT_FAST_MS", "0")`, which sets an environment variable for the duration of the test.
- `monkeypatch.setenv("TOKEN_MS", "0")`: calling `monkeypatch.setenv("TOKEN_MS", "0")`, which sets an environment variable for the duration of the test.
- `monkeypatch.setenv("LOG_LEVEL", "WARNING")`: calling `monkeypatch.setenv("LOG_LEVEL", "WARNING")`, which sets an environment variable for the duration of the test.

```python
return tmp_path
```

- `return tmp_path`: ends the function and gives back the value of `tmp_path`.

```python
def test_the_commands_build_the_database_trace_a_request_and_verify_the_audit_chain(env, capsys):
```

- Defines the test `test_the_commands_build_the_database_trace_a_request_and_verify_the_audit_chain`.
- Parameters:
  - `env`: a fixture (defined in `tests/unit/interfaces/test_http_and_cli.py`).
  - `capsys`: a fixture; captures what the code prints.

```python
assert cli.main(["db"]) == 0 and (env / "assistant.sqlite").exists()
assert cli.main(["trace"]) == 0
out = capsys.readouterr().out
assert "cold" in out and "warm" in out and "stage sum" in out
assert cli.main(["tamper-demo"]) == 0
tampered = capsys.readouterr().out
```

- `assert cli.main(["db"]) == 0 and (env / "assistant.sqlite").exists()`: checks that `cli.main(["db"])` equals `0` and `(env / "assistant.sqlite").exists()` is true (the call asks whether `env / "assistant.sqlite"` exists on disk). A false check stops the test as failed.
- `assert cli.main(["trace"]) == 0`: checks that `cli.main(["trace"])` equals `0`. A false check stops the test as failed.
- `out = capsys.readouterr().out`: stores `capsys.readouterr().out` in `out`.
- `assert "cold" in out and "warm" in out and "stage sum" in out`: checks that `"cold"` is among `out` and `"warm"` is among `out` and `"stage sum"` is among `out`. A false check stops the test as failed.
- `assert cli.main(["tamper-demo"]) == 0`: checks that `cli.main(["tamper-demo"])` equals `0`. A false check stops the test as failed.
- `tampered = capsys.readouterr().out`: stores `capsys.readouterr().out` in `tampered`.

```python
assert (
    "chain intact: None" in tampered
    and "after tampering entry 1: 1" in tampered
    and "after deleting entry 1: 1" in tampered
)
assert cli.main(["verify-audit"]) == 0 and "first broken index: None" in capsys.readouterr().out
assert cli.main(["replay", "run-demo"]) == 0 and "paused" in capsys.readouterr().out
```

- `assert ( "chain intact: None" in tampered and "after tampering entr...`: checks that `"chain intact: None"` is among `tampered` and `"after tampering entry 1: 1"` is among `tampered` and `"after deleting entry 1: 1"` is among `tampered`. A false check stops the test as failed.
- `assert cli.main(["verify-audit"]) == 0 and "first broken index: Non...`: checks that `cli.main(["verify-audit"])` equals `0` and `"first broken index: None"` is among `capsys.readouterr().out`. A false check stops the test as failed.
- `assert cli.main(["replay", "run-demo"]) == 0 and "paused" in capsys...`: checks that `cli.main(["replay", "run-demo"])` equals `0` and `"paused"` is among `capsys.readouterr().out`. A false check stops the test as failed.

```python
def test_verify_audit_exits_one_when_the_chain_is_broken(env, capsys):
```

- Defines the test `test_verify_audit_exits_one_when_the_chain_is_broken`.
- Parameters:
  - `env`: a fixture (defined in `tests/unit/interfaces/test_http_and_cli.py`).
  - `capsys`: a fixture; captures what the code prints.

```python
import sqlite3

cli.main(["db"])
cli.main(["tamper-demo"])
connection = sqlite3.connect(env / "assistant.sqlite")
connection.execute("DROP TRIGGER audit_log_no_update")
connection.execute("UPDATE audit_log SET content = 'edited' WHERE seq = 2")
```

- `import sqlite3`: makes the module `sqlite3` available (the standard library's SQLite database driver).
- `cli.main(["db"])`: calling `cli.main(["db"])`.
- `cli.main(["tamper-demo"])`: calling `cli.main(["tamper-demo"])`.
- `connection = sqlite3.connect(env / "assistant.sqlite")`: stores the result of calling `sqlite3.connect(env / "assistant.sqlite")`, which opens a connection in `connection`.
- `connection.execute("DROP TRIGGER audit_log_no_update")`: calling `connection.execute("DROP TRIGGER audit_log_no_update")`, which sends the SQL statement `"DROP TRIGGER audit_log_no_update"` to the database.
- `connection.execute("UPDATE audit_log SET content = 'edited' WHERE s...`: calling `connection.execute("UPDATE audit_log SET content = 'edited' WHERE seq = 2")`, which sends the SQL statement `"UPDATE audit_log SET content = 'edited' WHERE seq = 2"` to the database.

```python
connection.commit()
connection.close()
capsys.readouterr()
assert cli.main(["verify-audit"]) == 1 and "first broken index: 1" in capsys.readouterr().out
```

- `connection.commit()`: calling `connection.commit()`, which makes the changes since the last commit permanent.
- `connection.close()`: calling `connection.close()`, which closes `connection`.
- `capsys.readouterr()`: calling `capsys.readouterr()`, which reads what was printed so far.
- `assert cli.main(["verify-audit"]) == 1 and "first broken index: 1" ...`: checks that `cli.main(["verify-audit"])` equals `1` and `"first broken index: 1"` is among `capsys.readouterr().out`. A false check stops the test as failed.

```python
def test_evaluate_reports_the_pause_and_citation_counts(env, capsys):
```

- Defines the test `test_evaluate_reports_the_pause_and_citation_counts`.
- Parameters:
  - `env`: a fixture (defined in `tests/unit/interfaces/test_http_and_cli.py`).
  - `capsys`: a fixture; captures what the code prints.

```python
assert cli.main(["evaluate"]) == 0
report = json.loads(capsys.readouterr().out)
assert report["paused_of_should"] == report["should_pause"] == 20 and report["paused_of_others"] == 0
assert report["citations_outside_retrieved"] == 0 and report["false_pause_rate"] == 0
```

- `assert cli.main(["evaluate"]) == 0`: checks that `cli.main(["evaluate"])` equals `0`. A false check stops the test as failed.
- `report = json.loads(capsys.readouterr().out)`: stores the result of calling `json.loads(capsys.readouterr().out)`, which turns the JSON text `capsys.readouterr().out` into Python values in `report`.
- `assert report["paused_of_should"] == report["should_pause"] == 20 a...`: checks that `report["paused_of_should"]` equals `report["should_pause"]` and `report["should_pause"]` equals `20` and `report["paused_of_others"]` equals `0`. A false check stops the test as failed.
- `assert report["citations_outside_retrieved"] == 0 and report["false...`: checks that `report["citations_outside_retrieved"]` equals `0` and `report["false_pause_rate"]` equals `0`. A false check stops the test as failed.

```python
def test_a_bad_environment_stops_with_exit_code_two(monkeypatch, capsys):
```

- Defines the test `test_a_bad_environment_stops_with_exit_code_two`.
- Parameters:
  - `monkeypatch`: a fixture; changes environment variables or attributes for this test only.
  - `capsys`: a fixture; captures what the code prints.

> **`monkeypatch`.** A built-in fixture that changes an environment variable or an attribute for the length of one test and restores it afterwards.

```python
monkeypatch.setenv("PORT", "eighty")
assert cli.main(["db"]) == 2 and "PORT" in capsys.readouterr().err
assert os.environ["PORT"] == "eighty"
```

- `monkeypatch.setenv("PORT", "eighty")`: calling `monkeypatch.setenv("PORT", "eighty")`, which sets an environment variable for the duration of the test.
- `assert cli.main(["db"]) == 2 and "PORT" in capsys.readouterr().err`: checks that `cli.main(["db"])` equals `2` and `"PORT"` is among `capsys.readouterr().err`. A false check stops the test as failed.
- `assert os.environ["PORT"] == "eighty"`: checks that `os.environ["PORT"]` equals `"eighty"`. A false check stops the test as failed.

<!-- /fullwalk -->

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/pytest --version
```

`pytest 9.1.1`.

```bash
.venv/bin/pytest --collect-only -q | tail -3
```

Lists the tests it would run, then a line such as `N tests collected`.

```bash
make test
```

Runs the offline tests with coverage; ends with a `passed` summary and the coverage table.

```bash
.venv/bin/pytest -m live -q
```

With no key set, the live test is skipped: the summary shows `skipped`.

## Mistakes people make

- Tests that depend on each other's order or leftover files. Each test here builds its own state (an in-memory database, a temporary folder).
- Tests that call the real network or a paid API. The model sits behind a port, and tests use a fake or a recording.
- Asserting too little, for example only that code did not crash.
- Sleeping to wait for something. The code takes the clock and the waiter as parameters so tests can fake them.
- Misspelling a marker. `--strict-markers` turns that into an error.

## Check yourself

1. How does pytest decide a function is a test?
   *Answer:* Its name starts with `test_` and it is in a file named `test_*.py` under the test paths.
2. What is a fixture?
   *Answer:* A function that prepares something a test needs; the test receives it by naming it as a parameter.
3. What does `-m "not live"` do?
   *Answer:* Runs every test except those marked `live`.
4. What does `pytest.raises` check?
   *Answer:* That a block of code raises the named exception.
5. Why use `--strict-markers`?
   *Answer:* So a typo in a marker name is an error instead of silently selecting nothing.

## Further reading

- [pytest documentation (pinned version 9.1.1)](https://docs.pytest.org/en/stable/)
- [How to write and report assertions](https://docs.pytest.org/en/stable/how-to/assert.html)
- [Fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [Markers](https://docs.pytest.org/en/stable/how-to/mark.html)
