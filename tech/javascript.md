# JavaScript in the browser (fetch and streams)

## What it is

JavaScript is the programming language browsers run inside web pages. The two pages here use a few lines of it to send the question to the server, read the streamed answer piece by piece, show it, and react to the Stop button.

## Why this repository uses it

Reading a streamed response, showing each state, and Stop need a little code in the browser. About sixty lines of plain JavaScript in the page do it with the standard `fetch` API, with no library and no build.

## Where it appears

| File | What it does with JavaScript in the browser (fetch and streams) |
| --- | --- |
| `src/streaming_assistant/interfaces/static/index.html` | the chat page's script |
| `src/streaming_assistant/interfaces/static/review.html` | the review screen's script |

## How it works underneath

`fetch(url, options)` sends an HTTP request and returns a *promise* (a value that arrives later); `await` waits for it inside an `async` function. A response has a `body` that can be read as a *stream*: `response.body.getReader()` returns a reader, and `await reader.read()` gives the next chunk of bytes (and a `done` flag). A `TextDecoder` turns bytes into text. The page splits the text at blank lines to get SSE messages, then handles each by its `event:` name. An `AbortController` lets the page cancel the request: calling `controller.abort()` closes the connection, and the server sees the disconnect. `document.getElementById(id)` finds an element; `addEventListener("click", handler)` runs a function on click.

## Walkthrough of this repository's use

The script of the chat page is explained, chunk by chunk, in the **html.md** walkthrough (the chunks starting at `<script>`). The language features it uses, with the lines where they appear:

- **Arrow functions** `(id) => document.getElementById(id)` in `const $ = ...`.
- **`async` / `await`** in `readEvents`, `ask`, `stop`, `poll`: `await` pauses the function until a promise (a value that will arrive) resolves, without freezing the page.
- **Streams**: `response.body.getReader()`, `reader.read()`, `new TextDecoder()` in `readEvents`.
- **Regular expressions**: `/^event: (.*)$/m` in `readEvents`.
- **Destructuring**: `const { value, done } = await reader.read();` and, in the review script, `const [answer] = card.querySelectorAll("textarea")`.
- **`fetch` with options**: `method`, `headers`, `body`, `signal`.
- **`try` / `catch` / `finally`** in `ask`.
- **Template of events**: the `handle` function is a chain of `if (name === ...)` branches, one per event type.
- **DOM updates**: `textContent`, `hidden`, `disabled`, `createElement`, `append`, `addEventListener`.

The security-relevant habit is that every piece of server text goes in with `textContent`, never `innerHTML`.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
curl -s localhost:8100/ | sed -n '/<script>/,/<\/script>/p' | head -20
```

Prints the first lines of the page's script (needs the server running).

```bash
open http://127.0.0.1:8100/
```

Open the browser's developer tools (Network tab) to watch the `/ask` request stay open while text arrives.

```bash
grep -c 'textContent' src/streaming_assistant/interfaces/static/index.html
```

Counts uses of `textContent` in the chat page.

## Mistakes people make

- Forgetting `await`, so code runs before the data arrives.
- Decoding each chunk separately when a character can be split across chunks; `TextDecoder` with `stream: true` handles it.
- Not handling errors from `fetch`; a failed request must show a designed state.
- Keeping a token in the page source. The demo token is a fixed demo value, not a secret.
- Leaving the Stop button enabled when nothing runs.

## Check yourself

1. What does `fetch` return?
   *Answer:* A promise of a response.
2. What does `AbortController.abort()` do?
   *Answer:* Cancels the request and closes the connection.
3. Why use a stream reader?
   *Answer:* To show text as it arrives, not after the whole response.
4. What is a promise?
   *Answer:* A value that will be available later.
5. How does the page find a button?
   *Answer:* With `document.getElementById("stop")`, for an element with that `id`.

## Further reading

- [MDN: Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [MDN: ReadableStream](https://developer.mozilla.org/en-US/docs/Web/API/ReadableStream)
- [MDN: AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
