# Technology notes for ai-streaming-assistant-latency-budget

These notes teach every technology this repository uses, from zero, through the repository's own files. Each note has the same nine parts: what it is, why this repository uses it, where it appears, how it works underneath, a walkthrough of this repository's own use, commands to try, common mistakes, five questions to check yourself, and further reading.

## All files

| File | Role in this repository |
| --- | --- |
| [`python.md`](python.md) | the language of every module, test and script |
| [`bash.md`](bash.md) | the shell commands inside the Makefile recipes |
| [`make.md`](make.md) | the front door: `make up`, `run`, `test`, `lint` |
| [`git.md`](git.md) | the history and the `.gitignore` |
| [`pyproject-toml.md`](pyproject-toml.md) | the project file: dependencies, entry points, tool settings |
| [`pip-and-venv.md`](pip-and-venv.md) | the private environment and the hash-pinned lock files |
| [`uv.md`](uv.md) | generates the lock files |
| [`ruff.md`](ruff.md) | linter and formatter |
| [`mypy.md`](mypy.md) | strict type checker |
| [`import-linter.md`](import-linter.md) | enforces the layers |
| [`pytest.md`](pytest.md) | the test runner |
| [`coverage-py.md`](coverage-py.md) | measures what the tests ran |
| [`pip-audit.md`](pip-audit.md) | checks pinned packages for known vulnerabilities |
| [`github-actions.md`](github-actions.md) | the CI workflows |
| [`yaml.md`](yaml.md) | the format of the workflow files |
| [`editorconfig.md`](editorconfig.md) | editor habits |
| [`mit-license.md`](mit-license.md) | the license |
| [`dotenv.md`](dotenv.md) | settings from the environment and `.env` |
| [`argparse.md`](argparse.md) | the `streaming-assistant` command and its measurements |
| [`logging.md`](logging.md) | one logfmt line per event |
| [`hashlib.md`](hashlib.md) | the audit hash chain, token hashes, cassette keys |
| [`asyncio.md`](asyncio.md) | streaming, timeouts and cancelling the upstream call |
| [`json.md`](json.md) | the help pages and recorded streams |
| [`jsonl.md`](jsonl.md) | the 200 sample questions |
| [`markdown.md`](markdown.md) | the versioned prompt and the documents |
| [`anthropic-sdk.md`](anthropic-sdk.md) | the real streaming adapter, behind a port |
| [`fastapi.md`](fastapi.md) | the routes: ask, stop, resume, review, audit |
| [`uvicorn.md`](uvicorn.md) | the server that holds the open streams |
| [`pydantic.md`](pydantic.md) | validates the question and the reviewer's answer |
| [`httpx.md`](httpx.md) | reads the streams in tests and measurements |
| [`server-sent-events.md`](server-sent-events.md) | the wire format of the streamed answer |
| [`html.md`](html.md) | the chat page and the reviewer screen |
| [`javascript.md`](javascript.md) | the browser code that reads the stream |
| [`sqlite.md`](sqlite.md) | paused runs and the audit log |
| [`sql.md`](sql.md) | schema with triggers, tokens, queries |
| [`docker.md`](docker.md) | ships the server as an image |
| [`dockerfile.md`](dockerfile.md) | the image recipe |

## Reading order

Start with the language (`python.md`), then the tools that build and check it (`make.md`, `bash.md`, `git.md`, `pyproject-toml.md`, `pip-and-venv.md`, `uv.md`, `ruff.md`, `mypy.md`, `import-linter.md`, `pytest.md`, `coverage-py.md`, `pip-audit.md`), then the file formats (`json.md`, `yaml.md`, `markdown.md`, `editorconfig.md`, `dotenv.md`, `mit-license.md`), then the libraries and runtime pieces the code uses (`argparse.md`, `logging.md`, `hashlib.md`, `asyncio.md`, `anthropic-sdk.md`, `fastapi.md`, `uvicorn.md`, `pydantic.md`, `httpx.md`, `server-sent-events.md`, `html.md`, `javascript.md`), then the data (`sqlite.md`, `sql.md`, `jsonl.md`), then delivery (`docker.md`, `dockerfile.md`, `github-actions.md`).

## If you have ten minutes

1. [`python.md`](python.md): the language of every module, test and script
2. [`server-sent-events.md`](server-sent-events.md): the wire format of the streamed answer
3. [`asyncio.md`](asyncio.md): streaming, timeouts and cancelling the upstream call
