# FastAPI

## What it is

FastAPI is a Python framework for building web servers that speak HTTP (the language of the web). You write ordinary functions and mark them with a *route*, such as `@app.post("/ask")`; FastAPI turns them into URLs that other programs can call, checks the incoming data, and turns your return values into JSON responses.

## Why this repository uses it

The lesson needs a streaming endpoint, a Stop route, a resume route and reviewer routes. FastAPI makes each a plain function, validates the bodies with Pydantic, returns a streaming response from an async generator, and `Depends` puts the role check in one place.

## Where it appears

| File | What it does with FastAPI |
| --- | --- |
| `src/streaming_assistant/interfaces/http.py` | `create_app`: the routes and the SSE encoder |
| `tests/unit/interfaces/test_http_and_cli.py` | tests the routes through `httpx`'s in-memory transport |

## How it works underneath

A web server is a program that waits for *requests* and answers with *responses*. A request has a *method* (`GET` to read, `POST` to send), a path (`/ask`), headers (name-value pairs such as `Authorization`), and sometimes a body. A response has a status code (200 OK, 401 not signed in, 404 not found, 413 too large, 422 invalid data, 504 gateway timeout) and a body.

FastAPI is built on Starlette (the part that handles the HTTP details) and Pydantic (the part that validates data). `@app.get("/healthz")` registers a route. Function parameters named in the path (`/runs/{run_id}`) are filled from the URL; a parameter typed as a Pydantic model is filled from the JSON body and rejected with status 422 if invalid; `Header()` reads a header. `Depends(function)` runs another function first and passes its result in: the code uses this for authentication.

`def` handlers run in a thread pool; `async def` handlers run on the event loop (see the notes on `asyncio` where they are used). FastAPI itself is only an application object; a separate server program (Uvicorn) accepts network connections and hands each request to it. Tests call the application in-process with an HTTP client, without opening a port.

One detail to know in this code base: in the modules that build routes inside a function, `from __future__ import annotations` is not used, because FastAPI reads the real type objects of parameters and the delayed form breaks nested dependencies.

## Walkthrough of this repository's use

### Server-Sent-Events plumbing and the request models

From `src/streaming_assistant/interfaces/http.py`:

```python
SSE_HEADERS = {"Cache-Control": "no-store", "X-Accel-Buffering": "no", "Connection": "keep-alive"}


class AskIn(BaseModel):
    """A customer question."""

    question: str = Field(min_length=3, max_length=1000)


class ReviewIn(BaseModel):
    """A reviewer's answer to a paused run."""

    reviewer_id: str = Field(min_length=1, max_length=64)
    answer: str = Field(max_length=2000)
    cited: list[str] = Field(default_factory=list, max_length=5)
    no_page: bool = False


def encode(event: Event) -> str:
    """One server-sent event."""
    return f"event: {event.name}\ndata: {json.dumps(event.data)}\n\n"
```

- `SSE_HEADERS = {"Cache-Control": "no-store", "X-Accel-Buffering": "no", "Connection": "keep-alive"}`: Headers added to every event stream. `Cache-Control: no-store` forbids caching; `X-Accel-Buffering: no` asks nginx-style proxies not to hold the stream back; `Connection: keep-alive` keeps the connection open.
- `class AskIn(BaseModel):`: (Not about SSE: the request model of `POST /ask`.)
- `"""A customer question."""`: The docstring.
- `question: str = Field(min_length=3, max_length=1000)`: The question must be 3 to 1,000 characters.
- `class ReviewIn(BaseModel):`: The request model of the reviewer's answer.
- `"""A reviewer's answer to a paused run."""`: The docstring.
- `reviewer_id: str = Field(min_length=1, max_length=64)`: Who answered (1 to 64 characters).
- `answer: str = Field(max_length=2000)`: The answer text, at most 2,000 characters (an empty answer is refused later by the review desk, with a reason).
- `cited: list[str] = Field(default_factory=list, max_length=5)`: Up to five cited sections; `default_factory=list` makes a fresh empty list per object.
- `no_page: bool = False`: A flag: the reviewer says no page covers the question.
- `def encode(event: Event) -> str:`: Turns one event into the text that goes on the wire.
- `"""One server-sent event."""`: The docstring.
- `return f"event: {event.name}\ndata: {json.dumps(event.data)}\n\n"`: The format of an SSE message: a line `event: NAME`, a line `data: JSON`, and an empty line that ends the message. For a token this is `event: token` and `data: {"text": "Hello"}`.

### The routes

Every route of the server. `create_app` builds the application from its collaborators, so tests can supply fakes. Three routes carry the lesson: `POST /ask` (a streaming response), `POST /runs/{id}/stop` (sets the stop flag) and `GET /runs/{id}/resume` (streams the resumed answer).

From `src/streaming_assistant/interfaces/http.py`:

```python
def create_app(
    assistant: Assistant, desk: ReviewDesk, catalog: PageCatalog, authenticator: Authenticator, audit: AuditLog
) -> FastAPI:
    """Build the app over the assistant and its collaborators."""
    app = FastAPI(title="Streaming support assistant", version="0.1.0")
```

- `def create_app(`: Builds the web application. The parameters (the collaborators) follow, so tests can supply fakes.
- `assistant: Assistant, desk: ReviewDesk, catalog: PageCatalog, authenticator: Authenticator, audit: AuditLog`: The field `assistant`, type `Assistant, desk: ReviewDesk, catalog: PageCatalog, authenticator: Authenticator, audit: AuditLog`.
- `) -> FastAPI:`: Closes the parameter list: the function returns a `FastAPI` application.
- `"""Build the app over the assistant and its collaborators."""`: The docstring: says what the function is for.
- `app = FastAPI(title="Streaming support assistant", version="0.1.0")`: Creates the application object; everything below registers routes on it.

```python
    def role(authorization: Annotated[str | None, Header()] = None) -> str:
        found = authenticator.role_of((authorization or "").removeprefix("Bearer ").strip())
        if found is None:
            raise HTTPException(status_code=401, detail="sign in first")
        return found
```

- `def role(authorization: Annotated[str | None, Header()] = None) -> str:`: The function `role`, returning `str`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `found = authenticator.role_of((authorization or "").removeprefix("Bearer ").strip())`: Stores `authenticator.role_of((authorization or "").removeprefix("Bearer ").strip())` in the name `found`.
- `if found is None:`: Runs the block below only when `found is None`.
- `raise HTTPException(status_code=401, detail="sign in first")`: Stops the request and answers with status 401 Unauthorized: not signed in; `detail` is the message in the JSON body.
- `return found`: Gives back `found`.

```python
    def reviewer(found: Annotated[str, Depends(role)]) -> None:
        if found != "reviewer":
            raise HTTPException(status_code=403, detail="reviewers only")
```

- `def reviewer(found: Annotated[str, Depends(role)]) -> None:`: The function `reviewer`, returning `None`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `if found != "reviewer":`: Runs the block below only when `found != "reviewer"`.
- `raise HTTPException(status_code=403, detail="reviewers only")`: Stops the request and answers with status 403 Forbidden: signed in but not allowed; `detail` is the message in the JSON body.

```python
    async def sse(events: AsyncIterator[Event]) -> AsyncIterator[str]:
        async for event in events:
            yield encode(event)
```

- `async def sse(events: AsyncIterator[Event]) -> AsyncIterator[str]:`: The function `sse`, returning `AsyncIterator[str]`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `async for event in events:`: Repeats the block below for each item the asynchronous iterator `events` produces, waiting for each.
- `yield encode(event)`: Hands `encode(event)` to the caller and pauses until the next piece is wanted (this is how a generator streams).

```python
    @app.get("/", response_class=HTMLResponse)
    def home() -> FileResponse:
        return FileResponse(STATIC / "index.html")
```

- `@app.get("/", response_class=HTMLResponse)`: A *decorator* that registers the function below as the handler for `GET /` (extra settings: `response_class=HTMLResponse`).
- `def home() -> FileResponse:`: The function `home`, returning `FileResponse`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `return FileResponse(STATIC / "index.html")`: Gives back `FileResponse(STATIC / "index.html")`.

```python
    @app.get("/review", response_class=HTMLResponse)
    def review_page() -> FileResponse:
        return FileResponse(STATIC / "review.html")
```

- `@app.get("/review", response_class=HTMLResponse)`: A *decorator* that registers the function below as the handler for `GET /review` (extra settings: `response_class=HTMLResponse`).
- `def review_page() -> FileResponse:`: The function `review_page`, returning `FileResponse`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `return FileResponse(STATIC / "review.html")`: Gives back `FileResponse(STATIC / "review.html")`.

```python
    @app.post("/ask")
    async def ask(body: AskIn, authorization: Annotated[str | None, Header()] = None) -> StreamingResponse:
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        try:
            prepared = await assistant.prepare(
                run_id, body.question, (authorization or "").removeprefix("Bearer ").strip()
            )
        except UnauthorizedError:
            raise HTTPException(status_code=401, detail="sign in first") from None
        LOGGER.info("run started", extra={"fields": {"run_id": run_id, "route": prepared.route.kind}})
        return StreamingResponse(
            sse(assistant.stream(prepared)), media_type="text/event-stream", headers={**SSE_HEADERS, "X-Run-Id": run_id}
        )
```

- `@app.post("/ask")`: A *decorator* that registers the function below as the handler for `POST /ask`.
- `async def ask(body: AskIn, authorization: Annotated[str | None, Header()] = None) -> StreamingResponse:`: The function `ask`, returning `StreamingResponse`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `run_id = f"run-{uuid.uuid4().hex[:12]}"`: Stores `f"run-{uuid.uuid4().hex[:12]}"` in the name `run_id`.
- `try:`: Starts a guarded block: the code below may raise an error that is turned into an HTTP answer.
- `prepared = await assistant.prepare(`: Stores `await assistant.prepare(` in the name `prepared`.
- `run_id, body.question, (authorization or "").removeprefix("Bearer ").strip()`: Another line of the function (a statement or a continuation of the one above).
- `except UnauthorizedError:`: Catches `UnauthorizedError`.
- `raise HTTPException(status_code=401, detail="sign in first") from None`: Stops the request and answers with status 401 Unauthorized: not signed in; `detail` is the message in the JSON body.
- `LOGGER.info("run started", extra={"fields": {"run_id": run_id, "route": prepared.route.kind}})`: Calls `LOGGER.info`.
- `return StreamingResponse(`: Returns a response whose body is produced piece by piece by a generator (used for Server-Sent Events).
- `sse(assistant.stream(prepared)), media_type="text/event-stream", headers={**SSE_HEADERS, "X-Run-Id": run_id}`: Wraps the generator of events so each event is encoded as Server-Sent-Events text.

```python
    @app.post("/runs/{run_id}/stop", status_code=202)
    def stop(run_id: str, _: Annotated[str, Depends(role)]) -> dict[str, str]:
        assistant.stops.request(run_id)
        return {"run_id": run_id, "status": "stop requested"}
```

- `@app.post("/runs/{run_id}/stop", status_code=202)`: A *decorator* that registers the function below as the handler for `POST /runs/{run_id}/stop` (extra settings: `status_code=202`); braces in the path, such as `{id}`, are *path parameters* filled from the URL.
- `def stop(run_id: str, _: Annotated[str, Depends(role)]) -> dict[str, str]:`: The function `stop`, returning `dict[str, str]`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `assistant.stops.request(run_id)`: Calls `assistant.stops.request`.
- `return {"run_id": run_id, "status": "stop requested"}`: Returns a dict; FastAPI turns it into a JSON response with status 200 unless the decorator says otherwise.

```python
    @app.get("/runs/{run_id}/status")
    def status(run_id: str, _: Annotated[str, Depends(role)]) -> dict[str, str | None]:
        try:
            return {"run_id": run_id, "status": desk.status(run_id)}
        except UnknownRunError:
            raise HTTPException(status_code=404, detail="no such run") from None
```

- `@app.get("/runs/{run_id}/status")`: A *decorator* that registers the function below as the handler for `GET /runs/{run_id}/status`; braces in the path, such as `{id}`, are *path parameters* filled from the URL.
- `def status(run_id: str, _: Annotated[str, Depends(role)]) -> dict[str, str | None]:`: The function `status`, returning `dict[str, str | None]`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `try:`: Starts a guarded block: the code below may raise an error that is turned into an HTTP answer.
- `return {"run_id": run_id, "status": desk.status(run_id)}`: Returns a dict; FastAPI turns it into a JSON response with status 200 unless the decorator says otherwise.
- `except UnknownRunError:`: Catches `UnknownRunError`.
- `raise HTTPException(status_code=404, detail="no such run") from None`: Stops the request and answers with status 404 Not Found; `detail` is the message in the JSON body.

```python
    @app.get("/runs/{run_id}/resume")
    async def resume(run_id: str, _: Annotated[str, Depends(role)]) -> StreamingResponse:
        try:
            events = assistant.resume(run_id)
            first = await events.__anext__()
        except UnknownRunError as error:
            raise HTTPException(status_code=409, detail=str(error)) from None
```

- `@app.get("/runs/{run_id}/resume")`: A *decorator* that registers the function below as the handler for `GET /runs/{run_id}/resume`; braces in the path, such as `{id}`, are *path parameters* filled from the URL.
- `async def resume(run_id: str, _: Annotated[str, Depends(role)]) -> StreamingResponse:`: The function `resume`, returning `StreamingResponse`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `try:`: Starts a guarded block: the code below may raise an error that is turned into an HTTP answer.
- `events = assistant.resume(run_id)`: Stores `assistant.resume(run_id)` in the name `events`.
- `first = await events.__anext__()`: Stores `await events.__anext__()` in the name `first`.
- `except UnknownRunError as error:`: Catches `UnknownRunError` and names it `error`.
- `raise HTTPException(status_code=409, detail=str(error)) from None`: Stops the request and answers with status 409 Conflict: the request clashes with the current state; `detail` is the message in the JSON body.

```python
        async def chained() -> AsyncIterator[Event]:
            yield first
            async for event in events:
                yield event
```

- `async def chained() -> AsyncIterator[Event]:`: The function `chained`, returning `AsyncIterator[Event]`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `yield first`: Hands `first` to the caller and pauses until the next piece is wanted (this is how a generator streams).
- `async for event in events:`: Repeats the block below for each item the asynchronous iterator `events` produces, waiting for each.
- `yield event`: Hands `event` to the caller and pauses until the next piece is wanted (this is how a generator streams).

```python
        return StreamingResponse(sse(chained()), media_type="text/event-stream", headers=SSE_HEADERS)
```

- `return StreamingResponse(sse(chained()), media_type="text/event-stream", headers=SSE_HEADERS)`: Returns a response whose body is produced piece by piece by a generator (used for Server-Sent Events).

```python
    @app.get("/reviews", dependencies=[Depends(reviewer)])
    def waiting() -> list[dict[str, object]]:
        return [
            {"run_id": r.run_id, "question": r.question, "reason": r.reason, "retrieved": list(r.retrieved)}
            for r in desk.waiting()
        ]
```

- `@app.get("/reviews", dependencies=[Depends(reviewer)])`: A *decorator* that registers the function below as the handler for `GET /reviews` (extra settings: `dependencies=[Depends(reviewer)]`).
- `def waiting() -> list[dict[str, object]]:`: The function `waiting`, returning `list[dict[str, object]]`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `return [`: Gives back `[`.
- `{"run_id": r.run_id, "question": r.question, "reason": r.reason, "retrieved": list(r.retrieved)}`: A dictionary written inline.
- `for r in desk.waiting()`: The loop part of the comprehension above: repeats for each item of `desk.waiting()`.

```python
    @app.post("/reviews/{run_id}/answer", dependencies=[Depends(reviewer)])
    def answer(run_id: str, body: ReviewIn) -> JSONResponse:
        try:
            run = desk.answer(run_id, body.reviewer_id, body.answer, body.cited, body.no_page)
        except UnknownRunError:
            raise HTTPException(status_code=404, detail="no such run") from None
        except ReviewRejectedError as error:
            raise HTTPException(status_code=422, detail=str(error)) from None
        return JSONResponse({"run_id": run.run_id, "status": run.status})
```

- `@app.post("/reviews/{run_id}/answer", dependencies=[Depends(reviewer)])`: A *decorator* that registers the function below as the handler for `POST /reviews/{run_id}/answer` (extra settings: `dependencies=[Depends(reviewer)]`); braces in the path, such as `{id}`, are *path parameters* filled from the URL.
- `def answer(run_id: str, body: ReviewIn) -> JSONResponse:`: The function `answer`, returning `JSONResponse`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `try:`: Starts a guarded block: the code below may raise an error that is turned into an HTTP answer.
- `run = desk.answer(run_id, body.reviewer_id, body.answer, body.cited, body.no_page)`: Stores `desk.answer(run_id, body.reviewer_id, body.answer, body.cited, body.no_page)` in the name `run`.
- `except UnknownRunError:`: Catches `UnknownRunError`.
- `raise HTTPException(status_code=404, detail="no such run") from None`: Stops the request and answers with status 404 Not Found; `detail` is the message in the JSON body.
- `except ReviewRejectedError as error:`: Catches `ReviewRejectedError` and names it `error`.
- `raise HTTPException(status_code=422, detail=str(error)) from None`: Stops the request and answers with status 422 Unprocessable Content: the data is well-formed but not acceptable; `detail` is the message in the JSON body.
- `return JSONResponse({"run_id": run.run_id, "status": run.status})`: Builds the response by hand so the status code and body are exactly as written.

```python
    @app.get("/audit/verify", dependencies=[Depends(reviewer)])
    def audit_verify() -> dict[str, object]:
        entries = audit.entries()
        return {"entries": len(entries), "first_broken_index": verify(entries)}
```

- `@app.get("/audit/verify", dependencies=[Depends(reviewer)])`: A *decorator* that registers the function below as the handler for `GET /audit/verify` (extra settings: `dependencies=[Depends(reviewer)]`).
- `def audit_verify() -> dict[str, object]:`: The function `audit_verify`, returning `dict[str, object]`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `entries = audit.entries()`: Stores `audit.entries()` in the name `entries`.
- `return {"entries": len(entries), "first_broken_index": verify(entries)}`: Returns a dict; FastAPI turns it into a JSON response with status 200 unless the decorator says otherwise.

```python
    @app.get("/pages/{page_id}", response_class=HTMLResponse)
    def page(page_id: str) -> HTMLResponse:
        found = catalog.page_html(page_id)
        if found is None:
            raise HTTPException(status_code=404, detail="no such page")
        return HTMLResponse(found)
```

- `@app.get("/pages/{page_id}", response_class=HTMLResponse)`: A *decorator* that registers the function below as the handler for `GET /pages/{page_id}` (extra settings: `response_class=HTMLResponse`); braces in the path, such as `{id}`, are *path parameters* filled from the URL.
- `def page(page_id: str) -> HTMLResponse:`: The function `page`, returning `HTMLResponse`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `found = catalog.page_html(page_id)`: Stores `catalog.page_html(page_id)` in the name `found`.
- `if found is None:`: Runs the block below only when `found is None`.
- `raise HTTPException(status_code=404, detail="no such page")`: Stops the request and answers with status 404 Not Found; `detail` is the message in the JSON body.
- `return HTMLResponse(found)`: Gives back `HTMLResponse(found)`.

```python
    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}
```

- `@app.get("/healthz")`: A *decorator* that registers the function below as the handler for `GET /healthz`.
- `def healthz() -> dict[str, str]:`: The function `healthz`, returning `dict[str, str]`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `return {"status": "ok"}`: Returns a dict; FastAPI turns it into a JSON response with status 200 unless the decorator says otherwise.

```python
    @app.get("/readyz")
    def readyz() -> dict[str, object]:
        return {"status": "ready", "sections": len(catalog.sections)}
```

- `@app.get("/readyz")`: A *decorator* that registers the function below as the handler for `GET /readyz`.
- `def readyz() -> dict[str, object]:`: The function `readyz`, returning `dict[str, object]`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `return {"status": "ready", "sections": len(catalog.sections)}`: Returns a dict; FastAPI turns it into a JSON response with status 200 unless the decorator says otherwise.

```python
    @app.get("/stats")
    def stats() -> dict[str, int]:
        return dict(assistant.stats)
```

- `@app.get("/stats")`: A *decorator* that registers the function below as the handler for `GET /stats`.
- `def stats() -> dict[str, int]:`: The function `stats`, returning `dict[str, int]`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `return dict(assistant.stats)`: Gives back `dict(assistant.stats)`.

```python
    return app
```

- `return app`: Hands the finished application to the caller (Uvicorn or a test client).

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
make db && make serve   # in one terminal
```

Starts the server on http://127.0.0.1:8100.

```bash
curl -s -N -X POST localhost:8100/ask -H 'Authorization: Bearer demo-customer-token' -H 'Content-Type: application/json' -d '{"question": "How long does standard delivery take?"}'
```

Prints events as they arrive: lines like `event: token` / `data: {"text": "..."}`, then `event: citation`, then `event: done`. `-N` turns off curl's buffering.

```bash
curl -s localhost:8100/healthz
```

`{"status":"ok"}`.

```bash
open http://127.0.0.1:8100/
```

Opens the chat page in your browser.

## Mistakes people make

- Trusting data in the request body without a model. Every body here is a Pydantic model or checked by hand.
- Doing slow blocking work inside an `async def` handler, which freezes every other request. Blocking calls are moved to a thread (`run_in_threadpool`, `asyncio.to_thread`).
- Returning internal errors to callers. The handlers return typed errors with a stable code and message.
- Forgetting authentication on an administrative route. Reviewer-only routes depend on a role check.
- Using string annotations (`from __future__ import annotations`) in modules that define handlers with `Depends` inside functions.

## Check yourself

1. What is a route?
   *Answer:* A URL path and method bound to a function, created with a decorator like `@app.get("/healthz")`.
2. What status code means 'invalid data'?
   *Answer:* 422.
3. What does `Depends` do?
   *Answer:* Runs another function before the handler and passes its result in.
4. What accepts the network connections for a FastAPI app?
   *Answer:* A separate server program, Uvicorn.
5. Why not run blocking code in an `async def` handler?
   *Answer:* It blocks the event loop, so no other request is served meanwhile.

## Further reading

- [FastAPI documentation (pinned version 0.162.0)](https://fastapi.tiangolo.com/)
- [Tutorial - User guide](https://fastapi.tiangolo.com/tutorial/)
- [Starlette](https://www.starlette.io/)
