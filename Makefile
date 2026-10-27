# make up | run | load-test | stop-test | test | lint | check | audit | down   (make help lists all)
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed
PKG := streaming_assistant

-include .env
export

$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@

install: $(STAMP) ## create .venv from the hash-pinned lock file

env:
	@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }

lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports

format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .

audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock

lock: ## re-resolve requirements.lock and requirements-dev.lock with hashes (needs uv)
	uv pip compile pyproject.toml --universal --generate-hashes -q -o requirements.lock
	uv pip compile pyproject.toml --universal --extra dev --generate-hashes -q -o requirements-dev.lock

.PHONY: help install env up db generate serve run trace evaluate stop-test load-test pause-demo tamper-demo verify-audit queries record test \
        test-live lint format audit check docker-build down clean

help: ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort

ASSISTANT := $(PY) -m streaming_assistant.interfaces.cli

up: env install ## prepare the environment: .env, .venv, and db/assistant.sqlite from the SQL scripts
	$(MAKE) --no-print-directory db

db: install ## rebuild db/assistant.sqlite from sql/001_schema.sql and sql/002_seed.sql
	$(ASSISTANT) db

generate: install ## regenerate data/help_pages.json and data/questions.jsonl from the seed (the committed files are what it writes)
	$(PY) scripts/generate_data.py

queries: install ## run sql/003_queries.sql against db/assistant.sqlite
	$(PY) scripts/run_queries.py

serve: install ## start the server on PORT with the chat page at / and the review screen at /review
	$(ASSISTANT) serve

trace: install ## one request's stage times (auth, retrieval, assembly, model) cold and warm; the sum equals the first-token time
	$(ASSISTANT) trace

evaluate: install ## the 200 questions: all 20 should-pause questions pause, the false-pause rate, citations outside the retrieved set
	$(ASSISTANT) evaluate

stop-test: install ## close the stream after 3 tokens: the upstream call is cancelled, billed tokens stop, the next request is timed
	$(ASSISTANT) stop-test

pause-demo: install ## a paused run answered by a reviewer, the server restarted, the run resumed, the audit trail replayed
	$(PY) scripts/pause_demo.py --local

tamper-demo: install ## edit and delete entries of the hash chain and watch verify point at the right index
	$(ASSISTANT) tamper-demo

verify-audit: install ## verify the hash chain of db/assistant.sqlite
	$(ASSISTANT) verify-audit

load-test: install ## 200 requests at 5 a second against four configurations; p50 and p95 first-token times against the budget
	$(ASSISTANT) load-test

run: install ## trace, evaluate, stop-test, pause demo and tamper demo in one go (the load test is its own target)
	$(ASSISTANT) trace
	$(ASSISTANT) evaluate
	$(ASSISTANT) stop-test
	$(PY) scripts/pause_demo.py --local
	$(ASSISTANT) tamper-demo

record: install ## record the sample questions with the real model into tests/fixtures/cassettes/live-v1.json (needs ANTHROPIC_API_KEY)
	MODEL_ADAPTER=claude $(PY) scripts/record_streams.py

test: install ## offline tests with coverage; domain and application stay at 95% or more
	$(PY) -m pytest tests -m "not live" --cov=$(PKG) --cov-report=term
	$(PY) -m coverage report --include='src/$(PKG)/domain/*,src/$(PKG)/application/*' --fail-under=95

test-live: install ## the opt-in test that calls the real model (needs ANTHROPIC_API_KEY)
	RUN_LIVE=1 $(PY) -m pytest tests/live -m live

check: lint test ## everything that needs no key and no network

docker-build: ## build the server image
	docker build -t ai-streaming-assistant-latency-budget:dev .

down: ## remove the local database
	rm -rf db

clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage coverage.xml
