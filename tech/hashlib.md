# Hashing with SHA-256 (hashlib)

## What it is

A *hash function* turns any data into a short fixed-size fingerprint. SHA-256 gives 64 hexadecimal characters. The same input always gives the same fingerprint; a one-character change gives a completely different one; and you cannot get the input back from the fingerprint. Python's `hashlib` module provides it.

## Why this repository uses it

Three jobs need a fingerprint. The audit log: each entry carries the SHA-256 of the entry before it, so editing, removing or reordering an entry breaks every later link. Sign-in tokens: only the SHA-256 of a token is stored in the database, never the token. The recorded streams: a hash of the whole request is the key under which a stream is stored.

## Where it appears

| File | What it does with Hashing with SHA-256 (hashlib) |
| --- | --- |
| `src/streaming_assistant/application/assistant.py` | hashes text with SHA-256 |
| `src/streaming_assistant/domain/audit.py` | hashes text with SHA-256 |
| `src/streaming_assistant/infrastructure/recorded_stream.py` | hashes text with SHA-256 |
| `src/streaming_assistant/infrastructure/scripted_stream.py` | hashes text with SHA-256 |
| `src/streaming_assistant/infrastructure/sqlite_store.py` | hashes text with SHA-256 |

## How it works underneath

`hashlib.sha256(data).hexdigest()` takes bytes (not text; text is encoded first, here as UTF-8) and returns the fingerprint as text. Because the output is fixed-size and practically unique, programs use hashes for several jobs: to detect that a file changed, to key a cache by its input, to chain records so that editing one breaks all later ones, and to store a password-like token without keeping the token itself.

Every repository here uses SHA-256 for the purposes shown in the walkthrough. A hash is not encryption (nothing is hidden or recoverable) and not, by itself, proof of who wrote the data; for that a *keyed* hash such as HMAC is used (see the HMAC note where it applies).

## Walkthrough of this repository's use

### `src/streaming_assistant/application/assistant.py`

The function's docstring (left out of the listing) says: *Typed events for one run. The stream always ends with `done`, `paused` or a `state` followed by `done`.*

```python
    async def stream(self, prepared: Prepared) -> AsyncIterator[Event]:
        run_id = prepared.run_id
        self._audit.append(
            run_id,
            "received",
            "customer",
            "question sha256:" + hashlib.sha256(prepared.question.encode()).hexdigest()[:12],
        )
        route = prepared.route
        if route.kind == PAUSE:
            self._runs.save_pause(
                PausedRun(
                    run_id, prepared.question, tuple(hit.section.ref for hit in prepared.hits), route.reason, "waiting"
                ),
                self._clock.now(),
            )
            self._audit.append(run_id, "paused", "assistant", route.reason)
            self.stats["paused"] += 1
            yield Event(
                "paused",
                {
                    "run_id": run_id,
                    "reason": route.reason,
                    "message": "A person on the team will check this and the answer will appear here.",
                },
            )
            yield self._done(prepared, None, 0, "paused")
            return
        if route.kind in (LOW_CONFIDENCE, NO_EVIDENCE):
            self._audit.append(run_id, "state", "assistant", route.kind)
            self.stats[route.kind] += 1
            yield self._state(route.kind)
            yield self._done(prepared, None, 0, route.kind)
            return
        async for event in self._answer(prepared):
            yield event
```

- `async def stream(self, prepared: Prepared) -> AsyncIterator[Event]:`: Another line of the function (a statement or a continuation of the one above).
- `run_id = prepared.run_id`: Stores `prepared.run_id` in `run_id`.
- `self._audit.append(`: Another line of the function (a statement or a continuation of the one above).
- `run_id,`: Another line of the function (a statement or a continuation of the one above).
- `"received",`: Another line of the function (a statement or a continuation of the one above).
- `"customer",`: Another line of the function (a statement or a continuation of the one above).
- `"question sha256:" + hashlib.sha256(prepared.question.encode()).hexdigest()[:12],`: Another line of the function (a statement or a continuation of the one above).
- `route = prepared.route`: Stores `prepared.route` in `route`.
- `if route.kind == PAUSE:`: Another line of the function (a statement or a continuation of the one above).
- `self._runs.save_pause(`: Another line of the function (a statement or a continuation of the one above).
- `PausedRun(`: Another line of the function (a statement or a continuation of the one above).
- `run_id, prepared.question, tuple(hit.section.ref for hit in prepared.hits), route.reason, "waiting"`: Another line of the function (a statement or a continuation of the one above).
- `self._clock.now(),`: Another line of the function (a statement or a continuation of the one above).
- `self._audit.append(run_id, "paused", "assistant", route.reason)`: Another line of the function (a statement or a continuation of the one above).
- `self.stats["paused"] += 1`: Another line of the function (a statement or a continuation of the one above).
- `yield Event(`: Another line of the function (a statement or a continuation of the one above).
- `"paused",`: Another line of the function (a statement or a continuation of the one above).
- `{`: Another line of the function (a statement or a continuation of the one above).
- `"run_id": run_id,`: Another line of the function (a statement or a continuation of the one above).
- `"reason": route.reason,`: Another line of the function (a statement or a continuation of the one above).
- `"message": "A person on the team will check this and the answer will appear here.",`: Another line of the function (a statement or a continuation of the one above).
- `yield self._done(prepared, None, 0, "paused")`: Another line of the function (a statement or a continuation of the one above).
- `return`: Another line of the function (a statement or a continuation of the one above).
- `if route.kind in (LOW_CONFIDENCE, NO_EVIDENCE):`: Another line of the function (a statement or a continuation of the one above).
- `self._audit.append(run_id, "state", "assistant", route.kind)`: Another line of the function (a statement or a continuation of the one above).
- `self.stats[route.kind] += 1`: Another line of the function (a statement or a continuation of the one above).
- `yield self._state(route.kind)`: Another line of the function (a statement or a continuation of the one above).
- `yield self._done(prepared, None, 0, route.kind)`: Another line of the function (a statement or a continuation of the one above).
- `return`: Another line of the function (a statement or a continuation of the one above).
- `async for event in self._answer(prepared):`: Another line of the function (a statement or a continuation of the one above).
- `yield event`: Another line of the function (a statement or a continuation of the one above).

### `src/streaming_assistant/domain/audit.py`

The function's docstring (left out of the listing) says: *SHA-256 over the six fields, in a fixed order, joined by a separator that text does not contain.*

```python
def digest(previous: str, run: str, step: str, actor: str, at: str, content: str) -> str:
    return hashlib.sha256(SEPARATOR.join((previous, run, step, actor, at, content)).encode()).hexdigest()
```

- `def digest(previous: str, run: str, step: str, actor: str, at: str, content: str) -> str:`: The function `digest`.
- `return hashlib.sha256(SEPARATOR.join((previous, run, step, actor, at, content)).encode()).hexdigest()`: `hashlib.sha256(DATA)` computes the SHA-256 hash of the bytes `DATA`; `.hexdigest()` writes it as 64 hexadecimal characters. `DATA` here is `SEPARATOR.join((previous, run, step, actor, at, content)).encode()`.

### `src/streaming_assistant/infrastructure/recorded_stream.py`

The function's docstring (left out of the listing) says: *Hash of everything that decides the stream: model, prompt version, tier, system text and user text.*

```python
def request_key(model_id: str, request: StreamRequest) -> str:
    return hashlib.sha256(
        json.dumps([model_id, request.prompt_version, request.tier, request.system, request.user]).encode()
    ).hexdigest()
```

- `def request_key(model_id: str, request: StreamRequest) -> str:`: The function `request_key`.
- `return hashlib.sha256(`: Gives back `hashlib.sha256(`.
- `json.dumps([model_id, request.prompt_version, request.tier, request.system, request.user]).encode()`: Another line of the function (a statement or a continuation of the one above).
- `).hexdigest()`: Another line of the function (a statement or a continuation of the one above).

### `src/streaming_assistant/infrastructure/sqlite_store.py`

The function's docstring (left out of the listing) says: *The stored form of a bearer token.*

```python
def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
```

- `def token_hash(token: str) -> str:`: The function `token_hash`.
- `return hashlib.sha256(token.encode()).hexdigest()`: `hashlib.sha256(DATA)` computes the SHA-256 hash of the bytes `DATA`; `.hexdigest()` writes it as 64 hexadecimal characters. `DATA` here is `token.encode()`.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
python3 -c "import hashlib; print(hashlib.sha256(b'abc').hexdigest())"
```

Prints `ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`, the well-known SHA-256 of the three bytes `abc`. Run it twice: always the same.

```bash
python3 -c "import hashlib; print(hashlib.sha256(b'abd').hexdigest())"
```

One character different, a completely different fingerprint.

## Mistakes people make

- Hashing text without fixing the encoding. The code encodes explicitly to UTF-8.
- Joining fields without a separator, so different field splits give the same text (`ab`+`c` and `a`+`bc`). The audit chain uses a separator character that data cannot contain.
- Thinking a short truncated hash is as safe as the full one. Truncated hashes shown in reports are labels for people, not security.
- Using a hash alone to protect a password. Real password storage needs a slow, salted hash.
- Comparing hashes with a timing-leaky check where an attacker could exploit it (the signature check uses a constant-time comparison).

## Check yourself

1. Can you recover the input from a SHA-256 hash?
   *Answer:* No. It is a one-way function.
2. What changes if one character of the input changes?
   *Answer:* The whole hash changes.
3. Why must you encode text to bytes first?
   *Answer:* Hash functions work on bytes, and different encodings give different bytes.
4. What is a hash chain?
   *Answer:* Records where each one includes the hash of the previous one, so any edit breaks every later link.
5. Is a hash the same as encryption?
   *Answer:* No. Nothing is hidden and nothing can be decrypted.

## Further reading

- [hashlib](https://docs.python.org/3.12/library/hashlib.html)
- [FIPS 180-4, the SHA standard](https://csrc.nist.gov/pubs/fips/180-4/upd1/final)
