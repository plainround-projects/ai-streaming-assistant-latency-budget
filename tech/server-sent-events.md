# Server-Sent Events (SSE)

## What it is

Server-Sent Events is a simple web standard in which a server keeps one HTTP response open and sends a stream of small text messages down it, one after another. It is how the assistant sends text word by word while the model is still writing.

## Why this repository uses it

The lesson's first requirement is that text renders as it arrives and that Stop is real. SSE is the simplest standard that does this over ordinary HTTP: five fixed event names (token, citation, state, paused, done) and nothing else to learn.

## Where it appears

| File | What it does with Server-Sent Events (SSE) |
| --- | --- |
| `src/streaming_assistant/interfaces/http.py` | `encode`, `SSE_HEADERS`, the streaming routes |
| `src/streaming_assistant/application/assistant.py` | the `Event` objects that are encoded |
| `src/streaming_assistant/interfaces/static/index.html` | reads the stream with `fetch` |

## How it works underneath

The server answers with the header `Content-Type: text/event-stream` and never ends the body until it is done. Each message is a few lines followed by an empty line:

```
event: token
data: {"text": "Hello"}

```

`event:` names the type and `data:` carries the payload (here JSON). The client reads the stream and acts on each message as it arrives. Headers such as `Cache-Control: no-store` and `X-Accel-Buffering: no` ask caches and proxies not to hold the stream back.

SSE is one-way (server to client) over ordinary HTTP. The page here reads it with `fetch` and a stream reader instead of the browser's `EventSource`, because it must send a POST body and an `Authorization` header, which `EventSource` cannot. If the browser closes the connection (the Stop button, or a closed tab), the server notices and cancels the model call.

## Walkthrough of this repository's use

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

The five event types and their data:

| Event | Data | Meaning |
| --- | --- | --- |
| `token` | `{"text": "..."}` | the next piece of the answer, with citation markers already removed |
| `citation` | `{page_id, title, section, anchor, url}` | a page that was retrieved for this request and is cited |
| `state` | `{name, message, action}` | one of the seven designed states (timeout, provider_error, rate_limited, refusal, no_evidence, low_confidence, stopped) |
| `paused` | `{run_id, reason, message}` | the question waits for a person |
| `done` | `{run_id, outcome, dropped_citations, words, usage, timings}` | the last event of every stream, with the token usage and the stage times |

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
curl -s -N -X POST localhost:8100/ask -H 'Authorization: Bearer demo-customer-token' -H 'Content-Type: application/json' -d '{"question": "Can I get a refund on an order from seventy five days ago?"}'
```

Prints `event: paused`, a `data:` line with the reason `policy_exception`, then `event: done` (needs the server running).

```bash
curl -s -D - -o /dev/null -X POST localhost:8100/ask -H 'Authorization: Bearer demo-customer-token' -H 'Content-Type: application/json' -d '{"question": "How long is delivery?"}'
```

Prints the response headers, including `content-type: text/event-stream` and `cache-control: no-store`.

```bash
make stop-test
```

Closes a stream after three tokens.

## Mistakes people make

- Proxies or servers that buffer the response, so nothing appears until the end. The headers ask them not to.
- Forgetting the blank line that ends a message.
- Using `EventSource` when a POST or custom headers are needed.
- Not handling a closed connection on the server; the model keeps running and costs money.
- Mixing event types without a clear contract. Here the event names are fixed: token, citation, state, paused, done.

## Check yourself

1. What header marks an SSE response?
   *Answer:* `Content-Type: text/event-stream`.
2. What ends one message?
   *Answer:* An empty line.
3. Is SSE one-way or two-way?
   *Answer:* One-way, from server to client.
4. Why not use `EventSource` in this page?
   *Answer:* It cannot send a POST body or an `Authorization` header.
5. What should the server do when the client disconnects?
   *Answer:* Stop work for that request, including cancelling the model call.

## Further reading

- [HTML Standard: Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [MDN: Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
