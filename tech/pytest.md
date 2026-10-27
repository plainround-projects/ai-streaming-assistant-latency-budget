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
