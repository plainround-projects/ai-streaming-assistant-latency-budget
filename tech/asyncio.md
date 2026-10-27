# asyncio (asynchronous Python)

## What it is

`asyncio` is Python's way of doing many things at once in one thread by *switching while waiting*. A function defined with `async def` can pause at an `await` (for example while waiting for the network), and the *event loop* meanwhile runs other work. It suits servers that keep many connections open, such as the streaming endpoint.

## Why this repository uses it

One process must hold many open streams, wait for a slow model without blocking the others, and be able to cancel one model call when its browser goes away. That is what an event loop does. The blocking parts (SQLite, the search) are moved to threads so they cannot stall the loop.

## Where it appears

| File | What it does with asyncio (asynchronous Python) |
| --- | --- |
| `src/streaming_assistant/application/assistant.py` | `prepare`, `stream`, `resume`, `_answer` |
| `src/streaming_assistant/infrastructure/scripted_stream.py` | an async generator that sleeps and yields pieces |
| `src/streaming_assistant/interfaces/measure.py` | the load test's driver |
| `tests/unit/application/test_assistant.py` | `asyncio.run(...)` in every test |

## How it works underneath

An `async def` function, when called, does not run; it returns a *coroutine*. `await coroutine` runs it and gives control back to the event loop whenever it must wait. `asyncio.run(main())` starts a loop and runs one coroutine to the end. `asyncio.gather(a, b)` runs several at once and waits for all. `asyncio.wait_for(x, timeout)` gives up after a time. `asyncio.to_thread(function)` runs ordinary blocking code in a worker thread so it does not freeze the loop. An `async for` loop reads an *asynchronous iterator*, such as a model's stream of text pieces; closing that iterator (`aclose()`) is how the upstream call is cancelled. When a task is cancelled, `CancelledError` is raised inside it at the next `await`.

Only one piece of Python code runs at a time in the loop; nothing else runs while a function computes without awaiting. That is why blocking calls must go to threads.

## Walkthrough of this repository's use

The helper that times a blocking call:

From `src/streaming_assistant/application/assistant.py`:

```python
def _timed[T](function: Callable[[], T]) -> tuple[T, float]:
    started = time.perf_counter()
    result = function()
    return result, (time.perf_counter() - started) * 1000
```

- `def _timed[T](function: Callable[[], T]) -> tuple[T, float]:`: A helper with a type parameter `T`: it runs `function`, measures how long it took in milliseconds, and returns the result together with the time.
- `started = time.perf_counter()`: `perf_counter()` is a high-resolution clock for measuring short durations.
- `result = function()`: Runs the function (a blocking call).
- `return result, (time.perf_counter() - started) * 1000`: Returns the result and the elapsed time in milliseconds.

`prepare` authenticates and searches, at the same time when `PARALLEL_PREP` is on:

From `src/streaming_assistant/application/assistant.py`:

```python
    async def prepare(self, run_id: str, question: str, token: str) -> Prepared:
        """Authenticate, retrieve, assemble and route; each stage is timed inside the real path.
```

- `async def prepare(self, run_id: str, question: str, token: str) -> Prepared:`: An `async def` function: when called it returns a *coroutine*, which only runs when something `await`s it or the event loop schedules it.
- `"""Authenticate, retrieve, assemble and route; each stage is timed inside the real path.`: Part of the surrounding statement or a plain assignment.

```python
        With `parallel_prep` the authentication and the retrieval run at the same time; `overlap_ms` is the time that
        saved, so the stage times still add up to the measured total.
        """
        started = time.perf_counter()
        limit = self._config.retrieval_limit
        if self._config.parallel_prep:
            (role, auth_ms), (hits, retrieval_ms) = await asyncio.gather(
                asyncio.to_thread(_timed, lambda: self._auth.role_of(token)),
                asyncio.to_thread(_timed, lambda: self._retriever.search(question, limit)),
            )
        else:
            role, auth_ms = await asyncio.to_thread(_timed, lambda: self._auth.role_of(token))
            if role is None:
                raise UnauthorizedError
```

- `` With `parallel_prep` the authentication and the retrieval run at the same time; `overlap_ms` is the time that ``: Part of the surrounding statement or a plain assignment.
- `saved, so the stage times still add up to the measured total.`: Part of the surrounding statement or a plain assignment.
- `"""`: Part of the surrounding statement or a plain assignment.
- `started = time.perf_counter()`: `perf_counter()` is a high-resolution clock for measuring short durations.
- `limit = self._config.retrieval_limit`: Part of the surrounding statement or a plain assignment.
- `if self._config.parallel_prep:`: With the `PARALLEL_PREP` setting on, the two independent steps run at the same time.
- `(role, auth_ms), (hits, retrieval_ms) = await asyncio.gather(`: `asyncio.gather(a, b)` starts both awaitables at once and waits until both are done, returning both results in order. The two results are unpacked into four names.
- `asyncio.to_thread(_timed, lambda: self._auth.role_of(token)),`: `asyncio.to_thread(function, ...)` runs an ordinary blocking function in a worker thread and gives back an awaitable, so the event loop is not blocked while it runs. Here: the token lookup in SQLite.
- `asyncio.to_thread(_timed, lambda: self._retriever.search(question, limit)),`: The same for the search over the help pages.
- `else:`: Otherwise the two steps run one after the other (the baseline for the load test).
- `role, auth_ms = await asyncio.to_thread(_timed, lambda: self._auth.role_of(token))`: `await` waits for the thread's result without blocking the loop.
- `if role is None:`: Part of the surrounding statement or a plain assignment.
- `raise UnauthorizedError`: Part of the surrounding statement or a plain assignment.

The loop that reads the model's pieces, with a timeout on each, and that cancels the upstream call:

From `src/streaming_assistant/application/assistant.py`:

```python
    async def _answer(self, prepared: Prepared) -> AsyncIterator[Event]:
        run_id, request = prepared.run_id, prepared.request
        assert request is not None
        model = self._models[request.tier]
        strip, parts = MarkerStripper(), []
        usage: Usage | None = None
        first_token_ms = None
        call_started = time.perf_counter()
        upstream = model.stream(request).__aiter__()
        failure: str | None = None
        try:
            while True:
                timeout = (
                    self._config.first_token_timeout_seconds
                    if first_token_ms is None
                    else self._config.idle_timeout_seconds
                )
                try:
                    chunk = await asyncio.wait_for(upstream.__anext__(), timeout)
                except StopAsyncIteration:
                    break
                except TimeoutError:
                    failure = "timeout"
                    break
                except RateLimitedError:
                    failure = "rate_limited"
                    break
                except RefusedError:
                    failure = "refusal"
                    break
                except ProviderError:
                    failure = "provider_error"
                    break
                if isinstance(chunk, Usage):
                    usage = chunk
                    continue
                assert isinstance(chunk, TextDelta)
                visible = strip.feed(chunk.text)
                if visible:
                    if first_token_ms is None:
                        first_token_ms = (time.perf_counter() - prepared.started) * 1000
                        prepared.timings["model_ms"] = (time.perf_counter() - call_started) * 1000
                    parts.append(visible)
                    yield Event("token", {"text": visible})
                if self._stops.is_requested(run_id):
                    await self._close(upstream)
                    self._audit.append(run_id, "stopped", "customer", "stop requested")
                    self.stats["stopped"] += 1
                    yield self._state("stopped")
                    yield self._done(prepared, usage, len("".join(parts).split()), "stopped", first_token_ms)
                    return
        except asyncio.CancelledError:
            self._audit.append(run_id, "stopped", "client", "connection closed")
            self.stats["disconnected"] += 1
            raise
        finally:
            await self._close(upstream)
            self._stops.clear(run_id)
```

- `async def _answer(self, prepared: Prepared) -> AsyncIterator[Event]:`: An `async def` function: when called it returns a *coroutine*, which only runs when something `await`s it or the event loop schedules it.
- `run_id, request = prepared.run_id, prepared.request`: Part of the surrounding statement or a plain assignment.
- `assert request is not None`: Part of the surrounding statement or a plain assignment.
- `model = self._models[request.tier]`: Part of the surrounding statement or a plain assignment.
- `strip, parts = MarkerStripper(), []`: Part of the surrounding statement or a plain assignment.
- `usage: Usage | None = None`: Part of the surrounding statement or a plain assignment.
- `first_token_ms = None`: Part of the surrounding statement or a plain assignment.
- `call_started = time.perf_counter()`: Part of the surrounding statement or a plain assignment.
- `upstream = model.stream(request).__aiter__()`: Gets the asynchronous iterator of the model's pieces.
- `failure: str | None = None`: Part of the surrounding statement or a plain assignment.
- `try:`: Part of the surrounding statement or a plain assignment.
- `while True:`: Part of the surrounding statement or a plain assignment.
- `timeout = (`: Part of the surrounding statement or a plain assignment.
- `self._config.first_token_timeout_seconds`: Part of the surrounding statement or a plain assignment.
- `if first_token_ms is None`: Part of the surrounding statement or a plain assignment.
- `else self._config.idle_timeout_seconds`: Part of the surrounding statement or a plain assignment.
- `try:`: Part of the surrounding statement or a plain assignment.
- `chunk = await asyncio.wait_for(upstream.__anext__(), timeout)`: Waits for the next piece of the answer for at most `timeout` seconds. `__anext__()` is the asynchronous 'give me the next item' call of an async iterator. `wait_for` raises `TimeoutError` when the model is too slow.
- `except StopAsyncIteration:`: The model has finished: there are no more pieces.
- `break`: Part of the surrounding statement or a plain assignment.
- `except TimeoutError:`: The model did not produce a piece in time.
- `failure = "timeout"`: Part of the surrounding statement or a plain assignment.
- `break`: Part of the surrounding statement or a plain assignment.
- `except RateLimitedError:`: Part of the surrounding statement or a plain assignment.
- `failure = "rate_limited"`: Part of the surrounding statement or a plain assignment.
- `break`: Part of the surrounding statement or a plain assignment.
- `except RefusedError:`: Part of the surrounding statement or a plain assignment.
- `failure = "refusal"`: Part of the surrounding statement or a plain assignment.
- `break`: Part of the surrounding statement or a plain assignment.
- `except ProviderError:`: Part of the surrounding statement or a plain assignment.
- `failure = "provider_error"`: Part of the surrounding statement or a plain assignment.
- `break`: Part of the surrounding statement or a plain assignment.
- `if isinstance(chunk, Usage):`: Part of the surrounding statement or a plain assignment.
- `usage = chunk`: Part of the surrounding statement or a plain assignment.
- `continue`: Part of the surrounding statement or a plain assignment.
- `assert isinstance(chunk, TextDelta)`: Part of the surrounding statement or a plain assignment.
- `visible = strip.feed(chunk.text)`: Part of the surrounding statement or a plain assignment.
- `if visible:`: Part of the surrounding statement or a plain assignment.
- `if first_token_ms is None:`: Part of the surrounding statement or a plain assignment.
- `first_token_ms = (time.perf_counter() - prepared.started) * 1000`: Part of the surrounding statement or a plain assignment.
- `prepared.timings["model_ms"] = (time.perf_counter() - call_started) * 1000`: Part of the surrounding statement or a plain assignment.
- `parts.append(visible)`: Part of the surrounding statement or a plain assignment.
- `yield Event("token", {"text": visible})`: Part of the surrounding statement or a plain assignment.
- `if self._stops.is_requested(run_id):`: Part of the surrounding statement or a plain assignment.
- `await self._close(upstream)`: Closes the upstream stream, which cancels the model call.
- `self._audit.append(run_id, "stopped", "customer", "stop requested")`: Part of the surrounding statement or a plain assignment.
- `self.stats["stopped"] += 1`: Part of the surrounding statement or a plain assignment.
- `yield self._state("stopped")`: Part of the surrounding statement or a plain assignment.
- `yield self._done(prepared, usage, len("".join(parts).split()), "stopped", first_token_ms)`: Part of the surrounding statement or a plain assignment.
- `return`: Part of the surrounding statement or a plain assignment.
- `except asyncio.CancelledError:`: The task was cancelled, which is how a closed browser connection reaches this code.
- `self._audit.append(run_id, "stopped", "client", "connection closed")`: Part of the surrounding statement or a plain assignment.
- `self.stats["disconnected"] += 1`: Part of the surrounding statement or a plain assignment.
- `raise`: Re-raises the cancellation so the task really stops.
- `finally:`: Part of the surrounding statement or a plain assignment.
- `await self._close(upstream)`: Closes the upstream stream, which cancels the model call.
- `self._stops.clear(run_id)`: Part of the surrounding statement or a plain assignment.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/python -c "import asyncio; print(asyncio.run(asyncio.sleep(0.01, 'done')))"
```

Prints `done`: `asyncio.run` runs one coroutine to its end.

```bash
make stop-test
```

Shows the upstream call cancelled within milliseconds of the client closing.

```bash
.venv/bin/pytest tests/unit/application -q -k stop
```

Runs the Stop and closed-connection tests.

## Mistakes people make

- Calling a blocking function (`time.sleep`, a database call) inside `async def`; it freezes everything. Use `await asyncio.sleep` or `to_thread`.
- Forgetting `await`: the coroutine is created but never runs.
- Swallowing `CancelledError`. It must be re-raised so cancellation works; the code records the stop and re-raises.
- Starting tasks and losing track of them.
- Not closing async iterators when you stop early.

## Check yourself

1. What does `await` do?
   *Answer:* Waits for a coroutine's result, letting the event loop run other work meanwhile.
2. What does `asyncio.to_thread` do?
   *Answer:* Runs a blocking function in a worker thread so the loop stays responsive.
3. What happens if you call `time.sleep(5)` inside `async def`?
   *Answer:* The whole event loop is blocked for 5 seconds.
4. How is a stream stopped early?
   *Answer:* By closing the async iterator (`aclose()`), which cancels the upstream call.
5. What is raised inside a cancelled task?
   *Answer:* `asyncio.CancelledError`.

## Further reading

- [asyncio](https://docs.python.org/3.12/library/asyncio.html)
- [Coroutines and tasks](https://docs.python.org/3.12/library/asyncio-task.html)
