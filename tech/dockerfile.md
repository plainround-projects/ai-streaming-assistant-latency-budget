# Dockerfile

## What it is

A Dockerfile is the recipe for building a Docker image: a text file with one instruction per line (`FROM`, `COPY`, `RUN`, `ENV`, `USER`, `CMD`...), read from top to bottom.

## Why this repository uses it

The server is packaged as an image: pinned base, non-root user, a database built at image build time, a health check on `/healthz`.

## Where it appears

| File | What it does with Dockerfile |
| --- | --- |
| `Dockerfile` | the recipe |
| `.dockerignore` | keeps tests, docs and caches out |
| `Makefile` (`docker-build`) | builds it |

## How it works underneath

`FROM image` chooses the starting image. `COPY src dest` copies files from the build folder (the *build context*) into the image. `RUN command` runs a command while building and saves the result as a layer. `ENV NAME=value` sets an environment variable that stays in the image. `WORKDIR` sets the current folder. `USER` chooses who later steps and the container run as. `EXPOSE` documents a port. `HEALTHCHECK` defines a command Docker runs repeatedly to see if the program is healthy. `CMD` is what the container runs when it starts. A trailing `\` continues an instruction on the next line.

*Multi-stage* builds use several `FROM ... AS name` lines; a later stage can start from an earlier one, and `docker build --target name` builds only up to that stage. `.dockerignore` lists files kept out of the build context.

Each `RUN` or `COPY` is a layer, so order matters for caching: things that change rarely go first.

## Walkthrough of this repository's use

```dockerfile
# The streaming assistant as an image: pinned base, non-root, health check on /healthz.
# The database is built from sql/ at image build time; it holds the fixed demo tokens only.
FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0
```

- `# The streaming assistant as an image: pinned base, non-root, health check on /healthz.`: A comment. Everything after the `#` is for people; the tool ignores it.
- `# The database is built from sql/ at image build time; it holds the fixed demo tokens only.`: A comment. Everything after the `#` is for people; the tool ignores it.
- `FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0`: Start from an existing image: official Python 3.12.8 on the slim edition of Debian 12 (`bookworm`). The `@sha256:` part pins the exact bytes of that image, so a later re-publication of the same tag cannot change what is built. `AS name` (when present) names this build stage so later stages can start from it.

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PROJECT_ROOT=/app \
    HOST=0.0.0.0 \
    PORT=8100 \
    DATABASE=/data/assistant.sqlite
```

- `ENV PYTHONDONTWRITEBYTECODE=1 \`: `ENV` sets environment variables inside the image. `PYTHONDONTWRITEBYTECODE=1` stops Python writing `.pyc` files. The `\` at the end of the line continues the instruction on the next line.
- `PYTHONUNBUFFERED=1 \`: Python prints to the terminal at once instead of holding output in a buffer, so `docker logs` shows lines as they happen.
- `PIP_NO_CACHE_DIR=1 \`: `pip` does not keep a download cache, which keeps the image smaller.
- `PIP_DISABLE_PIP_VERSION_CHECK=1 \`: `pip` does not call the internet to check for a newer `pip`.
- `PROJECT_ROOT=/app \`: The program reads this variable to find its data folders: `/app` inside the image.
- `HOST=0.0.0.0 \`: Listen on all network interfaces inside the container, so the published port can reach the server. (`127.0.0.1` would be reachable only from inside.)
- `PORT=8100 \`: The port the server listens on: 8100.
- `DATABASE=/data/assistant.sqlite`: Where the SQLite database file lives inside the container.

```dockerfile
WORKDIR /app
COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps .
COPY sql ./sql
COPY data ./data
COPY prompts ./prompts
COPY tests/fixtures/cassettes ./tests/fixtures/cassettes
```

- `WORKDIR /app`: Make `/app` the current folder for the instructions that follow, and create it.
- `COPY requirements.lock ./`: Copy the hash-pinned list of runtime packages into the image first.
- `RUN pip install --require-hashes -r requirements.lock`: Run a command while building. `pip install -r FILE` installs every package in the file. `--require-hashes` makes `pip` refuse any package whose file does not match the SHA-256 hash recorded in the file, so a tampered download cannot get in. This step comes before the code is copied so Docker can reuse it from its cache when only the code changes.
- `COPY pyproject.toml README.md ./`: Copy the project description and the README (the build reads both).
- `COPY src ./src`: Copy the source code.
- `RUN pip install --no-deps .`: Install this project itself. `--no-deps` means: do not install its dependencies again; they are already installed and verified.
- `COPY sql ./sql`: Copy the folder `sql` into the image.
- `COPY data ./data`: Copy the help pages and questions that the program reads.
- `COPY prompts ./prompts`: Copy the folder `prompts` into the image.
- `COPY tests/fixtures/cassettes ./tests/fixtures/cassettes`: Copy only the recorded-model files from the tests, because the offline model reads them.

```dockerfile
RUN useradd --system --uid 10001 --no-create-home app && mkdir /data && chown app /data
USER app
RUN streaming-assistant db
EXPOSE 8100
HEALTHCHECK --interval=15s --timeout=5s --retries=3 CMD ["python", "-c", "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8100/healthz', timeout=3).status == 200 else 1)"]
CMD ["streaming-assistant", "serve"]
```

- `RUN useradd --system --uid 10001 --no-create-home app && mkdir /data && chown app /data`: Create the unprivileged `app` user (system account, number 10001, no home folder), then the `/data` folder, then give `app` ownership of it. `&&` runs the next command only if the previous one succeeded.
- `USER app`: From here on, build steps and the running container use the `app` user.
- `RUN streaming-assistant db`: Run the project's own console command `db` to build the SQLite database from the SQL files while the image is built.
- `EXPOSE 8100`: Documents that the program listens on port 8100. (It does not publish the port; `docker run -p` or compose does.)
- `HEALTHCHECK --interval=15s --timeout=5s --retries=3 CMD ["python", "-c", "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8100/healthz', timeout=3).status == 200 else 1)"]`: Docker runs this command every 15 seconds inside the container: a tiny Python program that asks the server's health URL and exits 0 for HTTP 200, 1 otherwise. Three failures in a row mark the container unhealthy.
- `CMD ["streaming-assistant", "serve"]`: The command that starts when the container runs: `streaming-assistant serve`, the console command that `pip install` created from `[project.scripts]`.

**Verification status.** The Docker daemon on the build machine failed before this image could be built, so the Dockerfile is untested. Pending capacity: run `make docker-build` after Docker Desktop is restarted with free disk (Docker.raw was at its 60 GiB cap on 2026-10-28).


<!-- extras -->
### `.dockerignore`, every line

When Docker builds an image it first sends a folder (the *build context*) to the builder. `.dockerignore` lists paths that must not be sent. That keeps the image small, keeps secrets out, and stops a change in an ignored file from invalidating the build cache. Each line is a path pattern; a leading `#` starts a comment.

```text
.git
.venv
.env
docs
**/__pycache__
.mypy_cache
.ruff_cache
.pytest_cache
.coverage
tests/unit
tests/e2e
tests/integration
tests/live
```

- `.git`: leaves out the repository's history; the image does not need it.
- `.venv`: leaves out the local Python environment; the image builds its own.
- `.env`: leaves out local settings and secrets must never be baked into an image.
- `docs`: leaves out documentation is not needed to run the program.
- `**/__pycache__`: leaves out the paths matching this pattern from the build context.
- `.mypy_cache`: leaves out mypy's cache.
- `.ruff_cache`: leaves out ruff's cache.
- `.pytest_cache`: leaves out pytest's cache.
- `.coverage`: leaves out the coverage data file.
- `tests/unit`: leaves out the paths matching this pattern from the build context.
- `tests/e2e`: leaves out the paths matching this pattern from the build context.
- `tests/integration`: leaves out the paths matching this pattern from the build context.
- `tests/live`: leaves out the paths matching this pattern from the build context.

<!-- /extras -->

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
make docker-build
```

Builds `ai-streaming-assistant-latency-budget:dev` (pending capacity).

```bash
docker run --rm -p 8100:8100 ai-streaming-assistant-latency-budget:dev
```

Starts the server; `curl localhost:8100/healthz` then answers.

```bash
docker run --rm --entrypoint id ai-streaming-assistant-latency-budget:dev
```

Prints `uid=10001(app)`.

## Mistakes people make

- Copying the whole folder before installing dependencies.
- Using `ENV` for build-only settings; they stay in the final image.
- Several `RUN` lines where one would do, creating needless layers.
- Forgetting `.dockerignore`, so large or secret files enter the context. Tests and caches are excluded here.
- Starting the app with a shell form `CMD python app.py`; the list form avoids an extra shell and passes signals to the program.

## Check yourself

1. What does `FROM` do?
   *Answer:* Chooses the image to start from.
2. What is the build context?
   *Answer:* The folder whose files `COPY` can copy from.
3. What is a multi-stage build?
   *Answer:* A Dockerfile with several `FROM` lines, letting one file build several related images.
4. What does `HEALTHCHECK` do?
   *Answer:* Defines a command Docker runs repeatedly to decide if the container is healthy.
5. What does `.dockerignore` do?
   *Answer:* Lists files that are left out of the build context.

## Further reading

- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
