# GNU Make

## What it is

`make` is a command-line tool that runs named recipes. You describe, in a file called `Makefile`, which *targets* exist, what each one needs first (its *prerequisites*), and the shell commands that produce it (its *recipe*). Then `make target` does the minimum needed. This repository uses it as the one front door: `make up`, `make run`, `make test`, `make lint`, `make down`.

## Why this repository uses it

The repository promises one front door: `make up`, `make run`, `make test`, `make lint`, `make down`. `make` is installed everywhere developers work, needs no language runtime of its own, and its rules express 'rebuild only when something changed', which is exactly what creating the virtual environment needs.

## Where it appears

| File | What it does with GNU Make |
| --- | --- |
| `Makefile` | every command a reader or CI runs |
| `.github/workflows/ci.yml` | calls `make check`, `make audit` and other targets |
| `README.md` | documents the targets and what each proves |

## How it works underneath

A Makefile is made of *rules*:

```
target: prerequisite1 prerequisite2
<TAB>command that builds the target
```

The recipe lines start with a *tab* character, not spaces. `make` first checks whether the target is a file. If the file exists and is newer than all its prerequisites, there is nothing to do. If not, `make` first builds each prerequisite (recursively), then runs the recipe. A target that is not really a file (like `test`) is declared in `.PHONY`, so it always runs.

Variables are written `NAME := value` (set once) or `NAME ?= value` (only if not set) and used as `$(NAME)`. Make also reads environment variables as variables, and `export` hands its variables to the commands it runs. A `@` before a command hides the command line itself; a `-` before `include` ignores a missing file. Inside a recipe `$@` is the target name.

Make runs each recipe line in a fresh `sh -c`. If a line exits non-zero, make stops and reports an error. The text after `##` on a rule line is just a comment; the `help` target here finds those comments with `grep` and prints them.

## Walkthrough of this repository's use

Here is the whole `Makefile`, in blocks, with every line explained. Blocks are separated by blank lines.

```make
# make up | run | load-test | stop-test | test | lint | check | audit | down   (make help lists all)
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed
PKG := streaming_assistant
```

- `# make up | run | load-test | stop-test | test | lint | check | audit | down   (make help lists all)`: A comment: the short list of the most used targets.
- `PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)`: `?=` sets the variable only if it is not already set. `$(shell ...)` runs a shell command and uses its output. `command -v NAME` prints where `NAME` is found and fails if it is not found. `||` means: if the left command failed, try the right one. So `PYTHON` becomes the first of `python3.13`, `python3.12`, `python3` that exists.
- `VENV := .venv`: `:=` sets a variable once, right now. `VENV` is the name of the virtual-environment folder.
- `PY := $(VENV)/bin/python`: `$(VENV)` is replaced by the variable's value. `PY` is the path of the Python inside the virtual environment.
- `STAMP := $(VENV)/.installed`: `STAMP` is the path of an empty file that records that the installation finished.
- `PKG := streaming_assistant`: `PKG` is the name of this project's Python package, `streaming_assistant`, used in test and coverage commands.

```make
-include .env
export
```

- `-include .env`: Read the file `.env` and treat each `NAME=value` line as a make variable. The leading `-` means: do not fail if the file does not exist.
- `export`: Pass every make variable to the commands that make runs, as environment variables. This is how settings in `.env` reach the Python programs.

```make
$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@
```

- `$(STAMP): requirements-dev.lock pyproject.toml`: A rule. The target is the stamp file. After the colon are its prerequisites: if either file is newer than the stamp, the stamp is out of date and the commands below must run again.
- `$(PYTHON) -m venv $(VENV)`: Create the virtual environment: a folder with its own Python and its own installed packages, so this project's packages do not mix with any others. `-m venv` runs Python's `venv` module.
- `$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock`: Install every package listed in the lock file. `-q` is quiet. `--require-hashes` refuses a package whose file hash differs from the one in the lock file.
- `$(VENV)/bin/pip install -q --no-deps -e .`: Install this project itself in editable mode (`-e`): the installed copy points at the source files, so edits take effect at once. `--no-deps` skips dependencies; they are already installed.
- `touch $@`: Create or update the stamp file. `$@` is make's name for the target of the rule.

```make
install: $(STAMP) ## create .venv from the hash-pinned lock file
```

- `install: $(STAMP) ## create .venv from the hash-pinned lock file`: A target. Its only prerequisite is the stamp, so running `make install` runs the installation only when needed. The text after `##` is the help text that `make help` prints.

```make
env:
	@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }
```

- `env:`: A target with no prerequisites and a help-free definition.
- `@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }`: The `@` stops make from printing the command itself. `[ -f .env ]` tests that the file exists. `||` runs the right side only if the test failed: copy the template to `.env` and print a message. The braces group the two commands.

```make
lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports
```

- `lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter`: A target that needs the installation first.
- `$(VENV)/bin/ruff check .`: Run the linter on the whole folder (`.`). A non-zero exit code means it found problems, and make stops.
- `$(VENV)/bin/ruff format --check .`: Check that the code is formatted the way the formatter would write it, without changing any file.
- `$(VENV)/bin/mypy`: Run the type checker. Its settings (which folders, strict mode) are in `pyproject.toml`.
- `$(VENV)/bin/lint-imports`: Run import-linter: it checks the contracts in `pyproject.toml`.

```make
format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .
```

- `format: $(STAMP) ## apply ruff's formatting and safe fixes`: A target that rewrites files.
- `$(VENV)/bin/ruff check --fix .`: Run the linter and apply the fixes it can make safely.
- `$(VENV)/bin/ruff format .`: Rewrite the files in the standard format.

```make
audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock
```

- `audit: $(STAMP) ## check the locked dependencies for known vulnerabilities`: A target that checks the pinned packages.
- `$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock`: Look up every pinned package and version in a database of known security problems. `--no-deps` and `--disable-pip` stop it from resolving or installing anything: it only reads the lock file.

```make
lock: ## re-resolve requirements.lock and requirements-dev.lock with hashes (needs uv)
	uv pip compile pyproject.toml --universal --generate-hashes -q -o requirements.lock
	uv pip compile pyproject.toml --universal --extra dev --generate-hashes -q -o requirements-dev.lock
```

- `lock: ## re-resolve requirements.lock and requirements-dev.lock with hashes (needs uv)`: A target with no prerequisites.
- `uv pip compile pyproject.toml --universal --generate-hashes -q -o requirements.lock`: `uv` works out exact versions for the runtime dependencies. `--universal` makes the result valid on every operating system, `--generate-hashes` records each file's hash, `-q` is quiet, `-o` names the output file.
- `uv pip compile pyproject.toml --universal --extra dev --generate-hashes -q -o requirements-dev.lock`: The same, including the `dev` group, written to `requirements-dev.lock`.

```make
.PHONY: help install env up db generate serve run trace evaluate stop-test load-test pause-demo tamper-demo verify-audit queries record test \
        test-live lint format audit check docker-build down clean
```

- `.PHONY: help install env up db generate serve run trace evaluate stop-test load-test pause-demo tamper-demo verify-audit queries record test \`: Names of targets that are commands, not files. Without this line, a file called `test` or `docs` in the folder would make `make test` think there is nothing to do.
- `test-live lint format audit check docker-build down clean`: The last line of the `.PHONY` list.

```make
help: ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort
```

- `help: ## list the targets`: The `help` target.
- `@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort`: `grep -E` picks the lines of this Makefile that look like `name: ... ## text`. `$(MAKEFILE_LIST)` is the list of Makefiles read. The pipe `|` sends grep's output to `sed`, which replaces everything between the colon and `##` with a tab. `sort` orders the lines. That is the help screen.

```make
ASSISTANT := $(PY) -m streaming_assistant.interfaces.cli
```

- `ASSISTANT := $(PY) -m streaming_assistant.interfaces.cli`: `ASSISTANT` is a shortcut for running the project's command-line module `streaming_assistant.interfaces.cli` with the virtual environment's Python.

```make
up: env install ## prepare the environment: .env, .venv, and db/assistant.sqlite from the SQL scripts
	$(MAKE) --no-print-directory db
```

- `up: env install ## prepare the environment: .env, .venv, and db/assistant.sqlite from the SQL scripts`: A target named `up`. After the colon are the targets it needs first (`env install`). The text after `##` is the help text.
- `$(MAKE) --no-print-directory db`: Run make again, as a sub-step, for the target(s) `db`. `--no-print-directory` suppresses the noisy 'entering directory' lines.

```make
db: install ## rebuild db/assistant.sqlite from sql/001_schema.sql and sql/002_seed.sql
	$(ASSISTANT) db
```

- `db: install ## rebuild db/assistant.sqlite from sql/001_schema.sql and sql/002_seed.sql`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(ASSISTANT) db`: Run the project's command `ASSISTANT` (defined at the top) with the subcommand `db`.

```make
generate: install ## regenerate data/help_pages.json and data/questions.jsonl from the seed (the committed files are what it writes)
	$(PY) scripts/generate_data.py
```

- `generate: install ## regenerate data/help_pages.json and data/questions.jsonl from the seed (the committed files are what it writes)`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(PY) scripts/generate_data.py`: Run the helper script `scripts/generate_data.py` with the virtual environment's Python.

```make
queries: install ## run sql/003_queries.sql against db/assistant.sqlite
	$(PY) scripts/run_queries.py
```

- `queries: install ## run sql/003_queries.sql against db/assistant.sqlite`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(PY) scripts/run_queries.py`: Run the helper script `scripts/run_queries.py` with the virtual environment's Python.

```make
serve: install ## start the server on PORT with the chat page at / and the review screen at /review
	$(ASSISTANT) serve
```

- `serve: install ## start the server on PORT with the chat page at / and the review screen at /review`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(ASSISTANT) serve`: Run the project's command `ASSISTANT` (defined at the top) with the subcommand `serve`.

```make
trace: install ## one request's stage times (auth, retrieval, assembly, model) cold and warm; the sum equals the first-token time
	$(ASSISTANT) trace
```

- `trace: install ## one request's stage times (auth, retrieval, assembly, model) cold and warm; the sum equals the first-token time`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(ASSISTANT) trace`: Run the project's command `ASSISTANT` (defined at the top) with the subcommand `trace`.

```make
evaluate: install ## the 200 questions: all 20 should-pause questions pause, the false-pause rate, citations outside the retrieved set
	$(ASSISTANT) evaluate
```

- `evaluate: install ## the 200 questions: all 20 should-pause questions pause, the false-pause rate, citations outside the retrieved set`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(ASSISTANT) evaluate`: Run the project's command `ASSISTANT` (defined at the top) with the subcommand `evaluate`.

```make
stop-test: install ## close the stream after 3 tokens: the upstream call is cancelled, billed tokens stop, the next request is timed
	$(ASSISTANT) stop-test
```

- `stop-test: install ## close the stream after 3 tokens: the upstream call is cancelled, billed tokens stop, the next request is timed`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(ASSISTANT) stop-test`: Run the project's command `ASSISTANT` (defined at the top) with the subcommand `stop-test`.

```make
pause-demo: install ## a paused run answered by a reviewer, the server restarted, the run resumed, the audit trail replayed
	$(PY) scripts/pause_demo.py --local
```

- `pause-demo: install ## a paused run answered by a reviewer, the server restarted, the run resumed, the audit trail replayed`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(PY) scripts/pause_demo.py --local`: Run the helper script `scripts/pause_demo.py` --local with the virtual environment's Python.

```make
tamper-demo: install ## edit and delete entries of the hash chain and watch verify point at the right index
	$(ASSISTANT) tamper-demo
```

- `tamper-demo: install ## edit and delete entries of the hash chain and watch verify point at the right index`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(ASSISTANT) tamper-demo`: Run the project's command `ASSISTANT` (defined at the top) with the subcommand `tamper-demo`.

```make
verify-audit: install ## verify the hash chain of db/assistant.sqlite
	$(ASSISTANT) verify-audit
```

- `verify-audit: install ## verify the hash chain of db/assistant.sqlite`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(ASSISTANT) verify-audit`: Run the project's command `ASSISTANT` (defined at the top) with the subcommand `verify-audit`.

```make
load-test: install ## 200 requests at 5 a second against four configurations; p50 and p95 first-token times against the budget
	$(ASSISTANT) load-test
```

- `load-test: install ## 200 requests at 5 a second against four configurations; p50 and p95 first-token times against the budget`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(ASSISTANT) load-test`: Run the project's command `ASSISTANT` (defined at the top) with the subcommand `load-test`.

```make
run: install ## trace, evaluate, stop-test, pause demo and tamper demo in one go (the load test is its own target)
	$(ASSISTANT) trace
	$(ASSISTANT) evaluate
	$(ASSISTANT) stop-test
	$(PY) scripts/pause_demo.py --local
	$(ASSISTANT) tamper-demo
```

- `run: install ## trace, evaluate, stop-test, pause demo and tamper demo in one go (the load test is its own target)`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(ASSISTANT) trace`: Run the project's command `ASSISTANT` (defined at the top) with the subcommand `trace`.
- `$(ASSISTANT) evaluate`: Run the project's command `ASSISTANT` (defined at the top) with the subcommand `evaluate`.
- `$(ASSISTANT) stop-test`: Run the project's command `ASSISTANT` (defined at the top) with the subcommand `stop-test`.
- `$(PY) scripts/pause_demo.py --local`: Run the helper script `scripts/pause_demo.py` --local with the virtual environment's Python.
- `$(ASSISTANT) tamper-demo`: Run the project's command `ASSISTANT` (defined at the top) with the subcommand `tamper-demo`.

```make
record: install ## record the sample questions with the real model into tests/fixtures/cassettes/live-v1.json (needs ANTHROPIC_API_KEY)
	MODEL_ADAPTER=claude $(PY) scripts/record_streams.py
```

- `record: install ## record the sample questions with the real model into tests/fixtures/cassettes/live-v1.json (needs ANTHROPIC_API_KEY)`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `MODEL_ADAPTER=claude $(PY) scripts/record_streams.py`: Run `scripts/record_streams.py` with `MODEL_ADAPTER=claude` set for this command only: use the real model (this needs an API key).

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

```make
check: lint test ## everything that needs no key and no network
```

- `check: lint test ## everything that needs no key and no network`: A target named `check`. After the colon are the targets it needs first (`lint test`). The text after `##` is the help text.

```make
docker-build: ## build the server image
	docker build -t ai-streaming-assistant-latency-budget:dev .
```

- `docker-build: ## build the server image`: A target named `docker-build` that needs nothing first.
- `docker build -t ai-streaming-assistant-latency-budget:dev .`: Build a Docker image: `-t ai-streaming-assistant-latency-budget:dev .`.

```make
down: ## remove the local database
	rm -rf db
```

- `down: ## remove the local database`: A target named `down` that needs nothing first.
- `rm -rf db`: The last line of the `.PHONY` list.

```make
clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage coverage.xml
```

- `clean: down`: A target that first runs `down`, then its own commands.
- `rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage coverage.xml`: Delete `$(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage coverage.xml`, and everything inside, without asking and without an error if it is missing.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
make help
```

Prints one line per target: the target name, a tab, and its help text taken from the `##` comment. For example `install` followed by `create .venv from the hash-pinned lock file`.

```bash
make -n lint
```

`-n` prints the commands that `lint` would run without running them: the four tool commands (`ruff check .`, `ruff format --check .`, `mypy`, `lint-imports`).

```bash
make -n test
```

Prints the pytest and coverage commands without running them.

```bash
make --version
```

Prints `GNU Make 3.81` on macOS (the old version Apple ships); the Makefile uses only features that version has.

## Mistakes people make

- Using spaces instead of a tab at the start of a recipe line. Make then says `missing separator`.
- Forgetting `.PHONY`. A file named `test` would make `make test` do nothing.
- Assuming `cd` on one recipe line carries to the next. Each line is its own shell.
- Writing `$VAR` for a make variable. Make needs `$(VAR)`; a single `$` belongs to the shell and must be doubled (`$$VAR`) to reach it.
- Hiding long pipelines inside a Makefile. This repository keeps long logic in Python scripts and keeps the Makefile as a list of short commands.

## Check yourself

1. What character must a recipe line start with?
   *Answer:* A tab.
2. When does `make install` skip its recipe?
   *Answer:* When the target file already exists and is newer than all its prerequisites. Here the stamp file `.venv/.installed` plays that role.
3. What does `.PHONY` do?
   *Answer:* It marks targets as commands, not files, so they always run.
4. What is `$@`?
   *Answer:* The name of the target being built.
5. What does `@` at the start of a recipe line do?
   *Answer:* It stops make from printing the command before running it.

## Further reading

- [GNU Make manual](https://www.gnu.org/software/make/manual/make.html)
- [Make: writing rules](https://www.gnu.org/software/make/manual/html_node/Rules.html)
