# The streaming assistant as an image: pinned base, non-root, health check on /healthz.
# The database is built from sql/ at image build time; it holds the fixed demo tokens only.
FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PROJECT_ROOT=/app \
    HOST=0.0.0.0 \
    PORT=8100 \
    DATABASE=/data/assistant.sqlite

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

RUN useradd --system --uid 10001 --no-create-home app && mkdir /data && chown app /data
USER app
RUN streaming-assistant db
EXPOSE 8100
HEALTHCHECK --interval=15s --timeout=5s --retries=3 CMD ["python", "-c", "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8100/healthz', timeout=3).status == 200 else 1)"]
CMD ["streaming-assistant", "serve"]
