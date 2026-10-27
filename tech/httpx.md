# HTTPX

## What it is

HTTPX is a Python library for making HTTP requests: it is the 'browser' side, where FastAPI and Uvicorn are the 'server' side. It has a synchronous client and an asynchronous one, and it can also call a Python web application directly in memory, which is how FastAPI's test client works.

## Why this repository uses it

The server is tested and measured over real HTTP: the unit tests call the app through HTTPX's in-memory transport, and the Stop test and the load test read the Server-Sent-Events stream from a real socket with HTTPX's streaming client.

## Where it appears

| File | What it does with HTTPX |
| --- | --- |
| `tests/unit/interfaces/test_http_and_cli.py` | `httpx.AsyncClient` with `ASGITransport` |
| `src/streaming_assistant/interfaces/measure.py` | streaming reads for the Stop test and the load test |
| `scripts/pause_demo.py` | drives two real servers with `httpx` |

## How it works underneath

`httpx.get(url)` or `client.post(url, json=...)` opens a connection, sends the request, and returns a response with `.status_code`, `.headers`, `.text` and `.json()`. A streaming call (`client.stream(...)`) yields the body in pieces as it arrives, which this repository uses to read server-sent events. A `timeout` limits how long to wait. With `httpx.ASGITransport(app=app)` the client skips the network and runs the ASGI app in the same process, so tests need no open port.

In this repository HTTPX appears in tests (calling the apps), in the demo and measurement code (calling real servers on a free port), and as a declared dependency of FastAPI's test tools.

## Walkthrough of this repository's use

Measuring the time to the first token over a real connection:

From `src/streaming_assistant/interfaces/measure.py`:

```python
async def first_event(client: httpx.AsyncClient, question: str) -> float:
    """Seconds from sending the request until the first `token` event line arrives."""
    started = time.perf_counter()
    elapsed = float("nan")
    async with client.stream("POST", "/ask", json={"question": question}, headers=CUSTOMER) as response:
        async for line in response.aiter_lines():  # read to the end so the connection closes cleanly
            if line == "event: token" and elapsed != elapsed:  # NaN until the first token line
                elapsed = time.perf_counter() - started
    return elapsed
```

- `async def first_event(client: httpx.AsyncClient, question: str) -> float:`: An `async def` helper.
- `` """Seconds from sending the request until the first `token` event line arrives.""" ``: The docstring.
- `started = time.perf_counter()`: Starts a stopwatch.
- `elapsed = float("nan")`: `nan` ('not a number') stands for 'no token seen yet'.
- `async with client.stream("POST", "/ask", json={"question": question}, headers=CUSTOMER) as response:`: Sends `POST /ask` with a JSON body and reads the response as a stream: the body arrives in pieces and is not loaded all at once.
- `async for line in response.aiter_lines():  # read to the end so the connection closes cleanly`: Receives the response one text line at a time as it arrives.
- `if line == "event: token" and elapsed != elapsed:  # NaN until the first token line`: The first line that says `event: token` marks the first piece of the answer. (`elapsed != elapsed` is true only for `nan`, so only the first token sets the time.)
- `elapsed = time.perf_counter() - started`: The time from sending the request to the first token.
- `return elapsed`: Returns the time in seconds.

### In the tests

The tests build a client that talks to the app in memory:

From `tests/unit/interfaces/test_http_and_cli.py`:

```python
def client_for(components):
    app = create_app(
        components.assistant, components.desk, components.catalog, components.authenticator, components.audit
    )
```

- `def client_for(components):`: Part of the surrounding statement.
- `app = create_app(`: Part of the surrounding statement.
- `components.assistant, components.desk, components.catalog, components.authenticator, components.audit`: Part of the surrounding statement.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/python -c "import httpx; print(httpx.__version__)"
```

Prints the pinned version.

```bash
make stop-test
```

Uses the streaming client against a real server and prints `upstream_cancelled_after_ms`.

```bash
.venv/bin/pytest tests/unit/interfaces -q
```

Runs the route tests.

## Mistakes people make

- No timeout; a hung server then hangs the caller forever.
- Reading a streamed response twice. A stream can be consumed once; the code reads it to the end in one loop.
- Not closing responses and clients; the code uses `with` / `async with` blocks.
- Testing against a fixed port that another program may already hold.
- Assuming the in-memory transport behaves exactly like the network (it skips real sockets).

## Check yourself

1. What does `response.status_code` hold?
   *Answer:* The HTTP status number, such as 200 or 404.
2. How can tests call an app without opening a port?
   *Answer:* With `httpx.ASGITransport(app=app)`.
3. What is a streamed response?
   *Answer:* One whose body is read in pieces as it arrives.
4. Why set a timeout?
   *Answer:* So a hung server cannot hang the caller.
5. Can you read a streamed response body twice?
   *Answer:* No.

## Further reading

- [HTTPX documentation (pinned version 0.28.1)](https://www.python-httpx.org/)
- [Async support](https://www.python-httpx.org/async/)
- [Calling the app directly](https://www.python-httpx.org/advanced/transports/)
