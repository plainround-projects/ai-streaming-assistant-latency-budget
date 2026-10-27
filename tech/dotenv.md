# Environment variables and the .env file

## What it is

An *environment variable* is a named value (such as `PORT=8080`) that every program started from a shell can read. Programs use them for settings that differ between machines and must not be written into the code: ports, file locations, and secrets such as API keys. A `.env` file is a plain text file of `NAME=value` lines used to set a batch of them at once.

## Why this repository uses it

Ports, file locations, the model adapter and the optional API key differ per machine and must not be written into the code. The program reads them from the environment once at start-up and refuses to start, naming the variable, if one is wrong.

## Where it appears

| File | What it does with Environment variables and the .env file |
| --- | --- |
| `.env.example` | the committed template of safe values |
| `.env` | your private copy (ignored by Git) |
| `Makefile` (`env`, `-include .env`, `export`) | creates and loads it |
| `src/streaming_assistant/infrastructure/settings.py` | reads and validates the variables |
| `src/streaming_assistant/infrastructure/environment.py` | the small reading helpers |

## How it works underneath

Each process has an *environment*, a table of names and text values that it inherits from the process that started it. In Python it is `os.environ`. The program here reads all its settings once at start-up through small helper functions that check the type and range and stop with a clear message naming the variable if it is wrong (the *twelve-factor* style: configuration lives in the environment).

`.env.example` is the committed template, with safe values. `make env` copies it to `.env` when `.env` does not exist. The Makefile line `-include .env` reads `.env` as make variables and `export` passes them on to every command. `.env` itself is in `.gitignore` because it may hold a real key. Nothing in this repository stores or asks for a secret; the real-model adapter reads `ANTHROPIC_API_KEY` from the environment only when you set it.

## Walkthrough of this repository's use

### The variables the program reads

Found in `src/streaming_assistant/infrastructure/settings.py`: each call names the variable and its default.

| Variable | Default in code | Meaning |
| --- | --- | --- |
| `LOG_LEVEL` | `"INFO"` | How much the program logs: DEBUG, INFO, WARNING or ERROR. |
| `PROJECT_ROOT` | `"."` | The folder that holds `sql/`, `prompts/`, `data/` and the other files the program reads. `.` means the current folder. |
| `DATABASE` | `"db/assistant.sqlite"` | The SQLite database file (relative to `PROJECT_ROOT`), or `:memory:` for a throw-away one. |
| `MODEL_ADAPTER` | `"scripted"` | Which model implementation to use. The default is an offline stand-in; `claude` uses the real API and needs a key. |
| `MODEL_ID` | `"claude-sonnet-5-5"` | The model name sent to the real API. |
| `FAST_MODEL_ID` | `"claude-haiku-5-5"` | The smaller model name used for easy questions. |
| `ANTHROPIC_API_KEY` | `(none)` | The key for the real API. Optional; only the real adapter reads it. Never committed. |
| `CASSETTE` | `"tests/fixtures/cassettes/stream-v1.json"` | The recorded-answers file that the `recorded` adapter replays. |
| `HOST` | `"127.0.0.1"` | The network address the server binds to. |
| `PORT` | `8100` | The port the server listens on. |
| `FIRST_TOKEN_TIMEOUT_SECONDS` | `3.0` | How long to wait for the first piece of the answer. |
| `IDLE_TIMEOUT_SECONDS` | `5.0` | How long a stream may stay silent. |
| `SCRIPTED_TTFT_STANDARD_MS` | `300.0` | (see `settings.py`) |
| `SCRIPTED_TTFT_FAST_MS` | `100.0` | (see `settings.py`) |
| `SCRIPTED_TOKEN_MS` | `15.0` | (see `settings.py`) |
| `FIRST_TOKEN_BUDGET_MS` | `1500.0` | The latency budget the load test is judged against. |

### How they are read

From `src/streaming_assistant/infrastructure/environment.py`:

```python
"""Configuration helpers: read and validate environment variables once at startup (twelve-factor)."""

from __future__ import annotations

from collections.abc import Mapping


class ConfigurationError(ValueError):
    """An environment variable is missing or has an unusable value."""


def read_text(environ: Mapping[str, str], name: str, default: str | None = None) -> str:
    """A non-empty string variable, or `default`."""
    value = environ.get(name, default if default is not None else "").strip()
    if not value:
        raise ConfigurationError(f"{name} must be set and not empty")
    return value


def read_optional(environ: Mapping[str, str], name: str) -> str | None:
    """A string variable that may be absent or empty (for example an API key)."""
    value = environ.get(name, "").strip()
    return value or None


def read_int(environ: Mapping[str, str], name: str, default: int, minimum: int = 1) -> int:
    """An integer variable of at least `minimum`."""
    raw = environ.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        raise ConfigurationError(f"{name} must be an integer, got {raw!r}") from None
    if value < minimum:
        raise ConfigurationError(f"{name} must be at least {minimum}, got {value}")
    return value


def read_float(environ: Mapping[str, str], name: str, default: float, minimum: float = 0.0) -> float:
    """A float variable of at least `minimum`."""
    raw = environ.get(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError:
        raise ConfigurationError(f"{name} must be a number, got {raw!r}") from None
    if value < minimum:
        raise ConfigurationError(f"{name} must be at least {minimum}, got {value}")
    return value


def read_choice(environ: Mapping[str, str], name: str, default: str, choices: frozenset[str]) -> str:
```

- `"""Configuration helpers: read and validate environment variables once at startup (twelve-factor)."""`: The module docstring: these helpers read and validate environment variables once at start-up.
- `from __future__ import annotations`: Stores type hints as text (see the logging note).
- `from collections.abc import Mapping`: `Mapping` is the type of any read-only key-to-value collection. `os.environ` is one, and so is the plain dict that tests pass in.
- `class ConfigurationError(ValueError):`: A new kind of error, named for what went wrong. It inherits from `ValueError`, so code that catches `ValueError` also catches it.
- `"""An environment variable is missing or has an unusable value."""`: The docstring.
- `def read_text(environ: Mapping[str, str], name: str, default: str | None = None) -> str:`: Reads a text setting. `environ` is the table of variables, `name` the variable, `default` a fallback (`str | None` means text or nothing).
- `` """A non-empty string variable, or `default`.""" ``: The docstring.
- `value = environ.get(name, default if default is not None else "").strip()`: Looks the name up; if it is missing, uses the default (or empty text if there is none). `.strip()` removes spaces at both ends.
- `if not value:`: Empty text counts as 'false' in Python, so this means: no value at all.
- `raise ConfigurationError(f"{name} must be set and not empty")`: Stops with an error that names the variable.
- `return value`: Gives back the cleaned text.
- `def read_optional(environ: Mapping[str, str], name: str) -> str | None:`: Reads a setting that is allowed to be absent, such as an API key.
- `"""A string variable that may be absent or empty (for example an API key)."""`: The docstring.
- `value = environ.get(name, "").strip()`: Looks it up with empty text as the fallback.
- `return value or None`: Gives back the cleaned text.
- `def read_int(environ: Mapping[str, str], name: str, default: int, minimum: int = 1) -> int:`: Reads a whole-number setting. `minimum` is the smallest allowed value.
- `` """An integer variable of at least `minimum`.""" ``: The docstring.
- `raw = environ.get(name, str(default)).strip()`: Gets the text of the variable, or the default turned into text.
- `try:`: Starts a block in which an error may happen and be handled.
- `value = int(raw)`: Converts the text to an integer. It raises `ValueError` if the text is not one.
- `except ValueError:`: Runs only if the conversion failed.
- `raise ConfigurationError(f"{name} must be an integer, got {raw!r}") from None`: Raises the repository's own error with a clear message. `{raw!r}` shows the bad value with quotes. `from None` hides the original error so the message is not cluttered.
- `if value < minimum:`: Rejects numbers below the allowed minimum.
- `raise ConfigurationError(f"{name} must be at least {minimum}, got {value}")`: Says the minimum and the value that was given.
- `return value`: Gives back the cleaned text.
- `def read_float(environ: Mapping[str, str], name: str, default: float, minimum: float = 0.0) -> float:`: The same for decimal numbers.
- `` """A float variable of at least `minimum`.""" ``: The docstring.
- `raw = environ.get(name, str(default)).strip()`: Gets the text of the variable, or the default turned into text.
- `try:`: Starts a block in which an error may happen and be handled.
- `value = float(raw)`: Converts the text to a decimal number.
- `except ValueError:`: Runs only if the conversion failed.
- `raise ConfigurationError(f"{name} must be a number, got {raw!r}") from None`: Names the variable and the bad value.
- `if value < minimum:`: Rejects numbers below the allowed minimum.
- `raise ConfigurationError(f"{name} must be at least {minimum}, got {value}")`: Says the minimum and the value that was given.
- `return value`: Gives back the cleaned text.
- `def read_choice(environ: Mapping[str, str], name: str, default: str, choices: frozenset[str]) -> str:`: Reads a setting that must be one of a fixed set, such as the log level.

### How `.env` reaches the program

```make
env:
	@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }
```

- `env:`: A target with no prerequisites and a help-free definition.
- `@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }`: The `@` stops make from printing the command itself. `[ -f .env ]` tests that the file exists. `||` runs the right side only if the test failed: copy the template to `.env` and print a message. The braces group the two commands.

```make
-include .env
export
```

- `-include .env`: Read the file `.env` and treat each `NAME=value` line as a make variable. The leading `-` means: do not fail if the file does not exist.
- `export`: Pass every make variable to the commands that make runs, as environment variables. This is how settings in `.env` reach the Python programs.


<!-- extras -->
### `.env.example`, every line

This file is a template. `make` copies it to `.env` the first time, and the program reads `.env` for its settings. A line `NAME=value` sets one environment variable; a line starting with `#` is a comment. Nothing secret is stored in the template: the line for the API key is empty on purpose.

```dotenv
# Copy to .env (make up does it). Nothing here is a secret.
LOG_LEVEL=INFO
# scripted: an offline model with configurable latency; recorded: tests/fixtures/cassettes; claude: the real API
MODEL_ADAPTER=scripted
CASSETTE=tests/fixtures/cassettes/stream-v1.json
MODEL_ID=claude-sonnet-5-5
FAST_MODEL_ID=claude-haiku-5-5
# Only for MODEL_ADAPTER=claude and make test-live. Never commit a real key.
ANTHROPIC_API_KEY=
DATABASE=db/assistant.sqlite
HOST=127.0.0.1
PORT=8100
```

- `LOG_LEVEL=INFO`: sets the environment variable `LOG_LEVEL` to the value `INFO`. The comment above it says: *Copy to .env (make up does it). Nothing here is a secret.*
- `MODEL_ADAPTER=scripted`: sets the environment variable `MODEL_ADAPTER` to the value `scripted`. The comment above it says: *scripted: an offline model with configurable latency; recorded: tests/fixtures/cassettes; claude: the real API*
- `CASSETTE=tests/fixtures/cassettes/stream-v1.json`: sets the environment variable `CASSETTE` to the value `tests/fixtures/cassettes/stream-v1.json`.
- `MODEL_ID=claude-sonnet-5-5`: sets the environment variable `MODEL_ID` to the value `claude-sonnet-5-5`.
- `FAST_MODEL_ID=claude-haiku-5-5`: sets the environment variable `FAST_MODEL_ID` to the value `claude-haiku-5-5`.
- `ANTHROPIC_API_KEY=`: sets the environment variable `ANTHROPIC_API_KEY` to an empty value (nothing is set). The comment above it says: *Only for MODEL_ADAPTER=claude and make test-live. Never commit a real key.*
- `DATABASE=db/assistant.sqlite`: sets the environment variable `DATABASE` to the value `db/assistant.sqlite`.
- `HOST=127.0.0.1`: sets the environment variable `HOST` to the value `127.0.0.1`.
- `PORT=8100`: sets the environment variable `PORT` to the value `8100`.

```dotenv
FIRST_TOKEN_TIMEOUT_SECONDS=3
IDLE_TIMEOUT_SECONDS=5
# The first-token budget the load test reports against (p95), in milliseconds
FIRST_TOKEN_BUDGET_MS=1500
# on/off switches; the load test flips them per configuration
PAUSE=on
STABLE_PREFIX_FIRST=on
PARALLEL_PREP=on
CACHE_RETRIEVAL=on
ROUTE_EASY_TO_FAST=off
WARM_INDEX=on
# Latency of the scripted model (settings, not measurements of a provider)
SCRIPTED_TTFT_STANDARD_MS=1300
```

- `FIRST_TOKEN_TIMEOUT_SECONDS=3`: sets the environment variable `FIRST_TOKEN_TIMEOUT_SECONDS` to the value `3`.
- `IDLE_TIMEOUT_SECONDS=5`: sets the environment variable `IDLE_TIMEOUT_SECONDS` to the value `5`.
- `FIRST_TOKEN_BUDGET_MS=1500`: sets the environment variable `FIRST_TOKEN_BUDGET_MS` to the value `1500`. The comment above it says: *The first-token budget the load test reports against (p95), in milliseconds*
- `PAUSE=on`: sets the environment variable `PAUSE` to the value `on`. The comment above it says: *on/off switches; the load test flips them per configuration*
- `STABLE_PREFIX_FIRST=on`: sets the environment variable `STABLE_PREFIX_FIRST` to the value `on`.
- `PARALLEL_PREP=on`: sets the environment variable `PARALLEL_PREP` to the value `on`.
- `CACHE_RETRIEVAL=on`: sets the environment variable `CACHE_RETRIEVAL` to the value `on`.
- `ROUTE_EASY_TO_FAST=off`: sets the environment variable `ROUTE_EASY_TO_FAST` to the value `off`.
- `WARM_INDEX=on`: sets the environment variable `WARM_INDEX` to the value `on`.
- `SCRIPTED_TTFT_STANDARD_MS=1300`: sets the environment variable `SCRIPTED_TTFT_STANDARD_MS` to the value `1300`. The comment above it says: *Latency of the scripted model (settings, not measurements of a provider)*

```dotenv
SCRIPTED_TTFT_FAST_MS=350
SCRIPTED_TOKEN_MS=15
```

- `SCRIPTED_TTFT_FAST_MS=350`: sets the environment variable `SCRIPTED_TTFT_FAST_MS` to the value `350`.
- `SCRIPTED_TOKEN_MS=15`: sets the environment variable `SCRIPTED_TOKEN_MS` to the value `15`.

<!-- /extras -->

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
make env
```

Prints `created .env from .env.example` the first time and nothing after.

```bash
grep -v '^#' .env | head
```

Shows your local variable assignments, without comment lines. (`.env` may hold secrets; never commit it.)

```bash
PORT=eighty .venv/bin/python -m streaming_assistant.interfaces.cli --help >/dev/null; echo $?
```

Shows that a help request still works; a bad value is reported only when settings are read (see the tests).

```bash
env | grep -c ANTHROPIC_API_KEY || true
```

Prints `0` unless you exported a key. Nothing in the repository needs one.

## Mistakes people make

- Committing `.env`. It is ignored; only `.env.example` is committed.
- Putting a real secret into `.env.example`.
- Spelling a variable differently in code and in the file; the settings reader names the first bad variable.
- Assuming a variable is a number. Environment values are always text; the readers convert and range-check them.
- Relying on a hidden default. The defaults are written in the settings code and the README.

## Check yourself

1. What is an environment variable?
   *Answer:* A named text value that a process inherits and can read.
2. Why is `.env` not committed?
   *Answer:* It is machine-specific and may contain secrets.
3. What does `make env` do?
   *Answer:* Copies `.env.example` to `.env` if `.env` does not exist.
4. How does `export` in the Makefile help?
   *Answer:* It passes the make variables, including those read from `.env`, to the programs make runs.
5. What type are environment values?
   *Answer:* Always text.

## Further reading

- [The Twelve-Factor App: Config](https://12factor.net/config)
- [Python os.environ](https://docs.python.org/3.12/library/os.html#os.environ)
- [GNU Make: include](https://www.gnu.org/software/make/manual/html_node/Include.html)
