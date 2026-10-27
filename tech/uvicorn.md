# Uvicorn

## What it is

Uvicorn is a web server for Python programs. It listens on a network *port*, accepts connections, reads each HTTP request, hands it to the application (here a FastAPI app) through a standard interface called ASGI, and sends the answer back.

## Why this repository uses it

Streaming needs a server that keeps connections open and notices when a client goes away. Uvicorn is an ASGI server built on an event loop; `serve` starts it with a graceful-shutdown period so running streams can finish.

## Where it appears

| File | What it does with Uvicorn |
| --- | --- |
| `src/streaming_assistant/interfaces/cli.py` | `serve` calls `uvicorn.run` |
| `src/streaming_assistant/interfaces/measure.py` | `RunningServer` runs Uvicorn in a thread for the Stop test |
| `Dockerfile` | `CMD ["streaming-assistant", "serve"]` with `HOST=0.0.0.0` |

## How it works underneath

A *port* is a number (0 to 65535) that identifies one listening program on a machine; the pair *host* and port, for example `127.0.0.1:8080`, is an address. `127.0.0.1` means 'this machine only'; `0.0.0.0` means 'every network interface', needed inside a container so the published port can reach the server.

ASGI (Asynchronous Server Gateway Interface) is the contract between the server and the app: the app is an `async` function that receives the request as a dictionary plus two channels for incoming and outgoing messages. Uvicorn runs an event loop, so one process can keep thousands of connections open at once, which is what makes streaming responses possible.

`uvicorn.run(app, host=..., port=...)` starts it from Python. It installs signal handlers: on SIGTERM or SIGINT (the polite 'please stop' signals) it stops accepting new connections, lets running requests finish (up to `timeout_graceful_shutdown`), and exits. When the signal came from the outside, Uvicorn re-raises it at the end, so the process may report an exit status of -15 (killed by signal 15, SIGTERM) even though the shutdown was clean.

## Walkthrough of this repository's use

The `serve` branch of the command:

From `src/streaming_assistant/interfaces/cli.py`:

```python
        elif arguments.command == "serve":
            import uvicorn
```

- `elif arguments.command == "serve":`: Otherwise, when `arguments.command == "serve"`.
- `import uvicorn`: Another line of the function (a statement or a continuation of the one above).

```python
            from streaming_assistant.interfaces.http import create_app
```

- `from streaming_assistant.interfaces.http import create_app`: Another line of the function (a statement or a continuation of the one above).

```python
            app = create_app(
                components.assistant, components.desk, components.catalog, components.authenticator, components.audit
            )
            uvicorn.run(
                app,
                host=settings.host,
                port=settings.port,
                log_level=settings.log_level.lower(),
                timeout_graceful_shutdown=10,
```

- `app = create_app(`: Stores `create_app(` in the name `app`.
- `components.assistant, components.desk, components.catalog, components.authenticator, components.audit`: Another line of the function (a statement or a continuation of the one above).
- `uvicorn.run(`: Another line of the function (a statement or a continuation of the one above).
- `app,`: Another line of the function (a statement or a continuation of the one above).
- `host=settings.host,`: The argument `host` of the call above.
- `port=settings.port,`: The argument `port` of the call above.
- `log_level=settings.log_level.lower(),`: The argument `log_level` of the call above.
- `timeout_graceful_shutdown=10,`: The argument `timeout_graceful_shutdown` of the call above.

### The server inside the Stop test

The Stop test needs a real socket, so it runs Uvicorn in a background thread:

From `src/streaming_assistant/interfaces/measure.py`:

```python
class RunningServer:
    """uvicorn in a thread, for tests of behavior over a real socket."""
```

- `class RunningServer:`: Another line of the function (a statement or a continuation of the one above).
- `"""uvicorn in a thread, for tests of behavior over a real socket."""`: The docstring: says what the function is for.

```python
    def __init__(self, components: Components, port: int) -> None:
        app = create_app(
            components.assistant, components.desk, components.catalog, components.authenticator, components.audit
        )
        self._server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self.base = f"http://127.0.0.1:{port}"
```

- `def __init__(self, components: Components, port: int) -> None:`: The function `__init__`, returning `None`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `app = create_app(`: Stores `create_app(` in the name `app`.
- `components.assistant, components.desk, components.catalog, components.authenticator, components.audit`: Another line of the function (a statement or a continuation of the one above).
- `self._server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))`: Another line of the function (a statement or a continuation of the one above).
- `self._thread = threading.Thread(target=self._server.run, daemon=True)`: Another line of the function (a statement or a continuation of the one above).
- `self.base = f"http://127.0.0.1:{port}"`: Another line of the function (a statement or a continuation of the one above).

```python
    def __enter__(self) -> "RunningServer":
        self._thread.start()
        for _ in range(100):
            try:
                if httpx.get(self.base + "/healthz", timeout=1).status_code == 200:
                    return self
            except httpx.HTTPError:
                time.sleep(0.05)
        raise RuntimeError("server did not start")
```

- `def __enter__(self) -> "RunningServer":`: The function `__enter__`, returning `"RunningServer"`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `self._thread.start()`: Calls `self._thread.start`.
- `for _ in range(100):`: Repeats the block below for each item of `range(100)`.
- `try:`: Starts a guarded block: the code below may raise an error that is turned into an HTTP answer.
- `if httpx.get(self.base + "/healthz", timeout=1).status_code == 200:`: Runs the block below only when `httpx.get(self.base + "/healthz", timeout=1).status_code == 200`.
- `return self`: Gives back `self`.
- `except httpx.HTTPError:`: Another line of the function (a statement or a continuation of the one above).
- `time.sleep(0.05)`: Calls `time.sleep`.
- `raise RuntimeError("server did not start")`: Raises `RuntimeError("server did not start")`.

```python
    def __exit__(self, *exc: object) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=10)
```

- `def __exit__(self, *exc: object) -> None:`: The function `__exit__`, returning `None`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `self._server.should_exit = True`: Another line of the function (a statement or a continuation of the one above).
- `self._thread.join(timeout=10)`: Calls `self._thread.join`.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
make serve
```

Prints `Uvicorn running on http://127.0.0.1:8100`.

```bash
PORT=8199 make serve
```

The same on another port.

```bash
lsof -nP -iTCP:8100 -sTCP:LISTEN
```

Shows which process holds port 8100.

## Mistakes people make

- Binding to `127.0.0.1` inside a container; the published port then cannot reach it.
- A port that is already taken by another program on the machine. The measurement code asks the operating system for a free port instead of a fixed one.
- Treating exit status -15 as a crash. After a polite SIGTERM it is the normal result.
- Running with auto-reload in production. Not used here.
- Killing the server with SIGKILL, which gives no chance to finish requests.

## Check yourself

1. What is a port?
   *Answer:* A number that identifies which listening program on a machine should get a connection.
2. What does host `0.0.0.0` mean?
   *Answer:* Listen on every network interface.
3. What is ASGI?
   *Answer:* The standard interface between an async Python web server and an application.
4. What does the server do on SIGTERM?
   *Answer:* Stops accepting connections, lets in-flight requests finish, and exits.
5. Why can one process hold many connections?
   *Answer:* It runs an event loop, switching between connections whenever one waits.

## Further reading

- [Uvicorn documentation (pinned version 0.54.0)](https://www.uvicorn.org/)
- [ASGI specification](https://asgi.readthedocs.io/en/latest/)
