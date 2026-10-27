# HTML

## What it is

HTML (HyperText Markup Language) is the language of web pages. A browser reads an `.html` file and shows it. Tags such as `<h1>` (a heading), `<button>` (a button), `<textarea>` and `<form>` describe the parts of the page; `<style>` adds looks and `<script>` adds behaviour.

## Why this repository uses it

The lesson asks for a small page where text renders as it arrives, Stop works, citations open the cited section and failure states have their own design, plus a review screen for the person who answers paused questions. Two plain HTML files served by the server itself need no build step and no framework.

## Where it appears

| File | What it does with HTML |
| --- | --- |
| `src/streaming_assistant/interfaces/static/index.html` | the chat page |
| `src/streaming_assistant/interfaces/static/review.html` | the reviewer screen |
| `src/streaming_assistant/interfaces/http.py` | serves them at `/` and `/review`; serves help pages with `id` anchors at `/pages/{id}` |
| `src/streaming_assistant/infrastructure/catalog.py` | `page_html` writes a help page with an `id` on every section, so `#anchor` opens at the cited section |

## How it works underneath

The browser parses the file into a tree of *elements* called the DOM (Document Object Model). Elements have *attributes* (`id="ask"` names an element, `type="button"` sets a kind). CSS rules in `<style>` set how elements look. JavaScript in `<script>` can find an element by its `id`, change its text, listen for clicks, and call the server with `fetch`. This repository's two pages (the chat page and the reviewer screen) are single files with their style and script inline, served by the server itself at `/` and `/review`, so there is nothing to build.

## Walkthrough of this repository's use

### The chat page

From `src/streaming_assistant/interfaces/static/index.html`:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Support assistant</title>
```

The first lines.

- `<!doctype html>` tells the browser this is a modern HTML page.
- `<html lang="en">` is the root element; `lang="en"` says the text is English (screen readers use it).
- `<head>` holds information about the page, not shown in it. `<meta charset="utf-8">` sets the text encoding. `<meta name="viewport" ...>` makes the page fit a phone screen instead of being drawn tiny.
- `<title>` is the text on the browser tab.

```html
<style>
  :root { color-scheme: light dark; --bg:#fff; --fg:#1b1f24; --muted:#59636e; --line:#d0d7de; --accent:#0b57d0; --warn:#9a6700; }
  @media (prefers-color-scheme: dark) { :root { --bg:#0d1117; --fg:#e6edf3; --muted:#9198a1; --line:#30363d; --accent:#79b8ff; --warn:#d29922; } }
  body { background:var(--bg); color:var(--fg); font:16px/1.5 system-ui, sans-serif; margin:0; }
  main { max-width:42rem; margin:0 auto; padding:1rem; }
  textarea { width:100%; box-sizing:border-box; font:inherit; padding:.5rem; background:var(--bg); color:var(--fg); border:1px solid var(--line); border-radius:6px; }
  button { font:inherit; padding:.5rem 1rem; border-radius:6px; border:1px solid var(--line); background:var(--bg); color:var(--fg); cursor:pointer; }
  button.primary { background:var(--accent); color:#fff; border-color:var(--accent); }
  button:focus-visible, textarea:focus-visible, a:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
  #answer { white-space:pre-wrap; min-height:3rem; margin:1rem 0; }
  #state, #paused { border:1px solid var(--warn); border-radius:6px; padding:.75rem; margin:1rem 0; }
  [hidden] { display:none !important; }
  .muted { color:var(--muted); font-size:.9rem; }
  @media (prefers-reduced-motion: reduce) { * { scroll-behavior:auto !important; } }
</style>
</head>
```

The CSS (Cascading Style Sheets): rules that say how elements look. A rule is `selector { property: value; ... }`.

- `:root { color-scheme: light dark; --bg:#fff; ... }` : `:root` is the whole page. `color-scheme: light dark` lets the browser use its light or dark default controls. The names starting with `--` are *custom properties* (variables): colours defined once and used below as `var(--bg)`.
- `@media (prefers-color-scheme: dark) { :root { ... } }`: when the operating system is in dark mode, the variables get dark colours.
- `body { background:var(--bg); color:var(--fg); font:16px/1.5 system-ui, sans-serif; margin:0; }`: page colours from the variables; a 16-pixel system font with line height 1.5; no outer margin.
- `main { max-width:42rem; margin:0 auto; padding:1rem; }`: a centred column at most 42 `rem` wide (1 rem is the base font size) with some padding.
- `textarea { width:100%; box-sizing:border-box; ... }`: the question box fills the width; `border-box` counts padding and border inside the width.
- `button { ... }` and `button.primary { ... }`: the look of buttons, and the filled look of the one with `class="primary"`.
- `button:focus-visible, textarea:focus-visible, a:focus-visible { outline:2px solid var(--accent); ... }`: when a control has keyboard focus, draw a visible outline. This is for people who navigate with the keyboard.
- `#answer { white-space:pre-wrap; min-height:3rem; margin:1rem 0; }`: `#answer` selects the element with `id="answer"`. `pre-wrap` keeps line breaks in the answer text.
- `#state, #paused { border:1px solid var(--warn); ... }`: the boxes for failure states and for the paused message.
- `[hidden] { display:none !important; }`: elements with the `hidden` attribute are not shown, whatever other rules say.
- `.muted { ... }`: a class for small grey text.
- `@media (prefers-reduced-motion: reduce) { * { scroll-behavior:auto !important; } }`: for people who asked their system for less motion, turn off smooth scrolling.

```html
<body>
<main>
  <h1>Ask the help center</h1>
  <label for="question">Your question</label>
  <textarea id="question" rows="3" placeholder="For example: how long does standard delivery take?"></textarea>
  <p>
    <button id="ask" class="primary" type="button">Ask</button>
    <button id="stop" type="button" disabled>Stop</button>
  </p>
  <div id="answer" role="status" aria-live="polite"></div>
  <ul id="citations"></ul>
  <div id="state" hidden>
    <p id="state-message"></p>
    <button id="state-action" type="button"></button>
  </div>
  <div id="paused" hidden><p id="paused-message"></p></div>
  <p class="muted" id="timing"></p>
</main>
```

The visible page.

- `<main>` is the main content area. `<h1>` is the page heading.
- `<label for="question">` is the caption of the box whose `id` is `question`; clicking it focuses the box, and screen readers read it.
- `<textarea id="question" rows="3" placeholder="...">` is a multi-line text box, three lines tall, with grey hint text.
- `<button id="ask" class="primary" type="button">Ask</button>` and `<button id="stop" type="button" disabled>`: the two buttons. `type="button"` stops them from submitting a form. `disabled` makes Stop unusable until a request is running.
- `<div id="answer" role="status" aria-live="polite">`: where the answer text appears. `role="status"` and `aria-live="polite"` tell screen readers to announce changes without interrupting.
- `<ul id="citations">`: the list of cited help pages.
- `<div id="state" hidden>` with `<p id="state-message">` and `<button id="state-action">`: the box for the seven failure states; hidden until needed.
- `<div id="paused" hidden><p id="paused-message"></p></div>`: the message shown when the question is waiting for a person.
- `<p class="muted" id="timing">`: a line that reports the time to the first word.

```html
<script>
const token = new URLSearchParams(location.search).get("token") || "demo-customer-token";
const $ = (id) => document.getElementById(id);
let controller = null, runId = null;
```

The start of the script and its shared values (JavaScript).

- `const token = new URLSearchParams(location.search).get("token") || "demo-customer-token";`: `location.search` is the part of the address after `?`. `URLSearchParams` reads it; `.get("token")` takes the value of `token`. `||` means 'or else': if there is none, use the fixed demo token. (A real site would never put a token in the address; this is a local demo.) `const` declares a name that is not reassigned.
- `const $ = (id) => document.getElementById(id);`: defines a tiny function named `$` (a valid name) that finds the element with that `id`. `(id) => ...` is an *arrow function*.
- `let controller = null, runId = null;`: two variables that change: the request's `AbortController` and the id of the current run. `let` is for names that are reassigned.

```html
function reset() {
  $("answer").textContent = ""; $("citations").innerHTML = "";
  $("state").hidden = true; $("paused").hidden = true; $("timing").textContent = "";
}
function setRunning(running) { $("ask").disabled = running; $("stop").disabled = !running; }
```

Two helper functions.

- `reset()` clears the previous answer: sets the answer's `textContent` to empty (text only, no markup), empties the citation list with `innerHTML = ""`, hides the two boxes and clears the timing line.
- `setRunning(running)` enables or disables the buttons: while a request runs, Ask is disabled and Stop is enabled.

```html
async function readEvents(response) {
  const reader = response.body.getReader(), decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let end;
    while ((end = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, end); buffer = buffer.slice(end + 2);
      const name = (block.match(/^event: (.*)$/m) || [])[1];
      const data = JSON.parse((block.match(/^data: (.*)$/m) || [, "{}"])[1]);
      handle(name, data);
    }
  }
}
```

`readEvents` reads the streamed response and splits it into events.

- `async function` can use `await`.
- `response.body.getReader()` gives a reader for the body as a stream of byte chunks; `new TextDecoder()` turns bytes into text.
- `let buffer = "";` collects text until a whole event has arrived.
- `for (;;) { ... }` is a loop with no condition: it runs until `break`.
- `const { value, done } = await reader.read();` waits for the next chunk. `done` is true at the end of the stream.
- `buffer += decoder.decode(value, { stream: true });` adds the new text. `stream: true` tells the decoder that a character may be split across chunks and to wait for its rest.
- `while ((end = buffer.indexOf("\n\n")) >= 0) { ... }`: an event ends with a blank line (`\n\n`). While the buffer contains one, cut out the complete event (`buffer.slice(0, end)`), keep the rest, and handle it.
- `block.match(/^event: (.*)$/m)` finds the line `event: NAME` with a regular expression (`m` makes `^` and `$` match at line starts and ends) and `[1]` takes the captured name. `JSON.parse(...)` turns the `data:` line's JSON into an object.
- `handle(name, data)` acts on the event.

```html
function handle(name, data) {
  if (name === "token") $("answer").textContent += data.text;
  else if (name === "citation") {
    const item = document.createElement("li"), link = document.createElement("a");
    link.href = data.url; link.textContent = data.title + ": " + data.section; link.target = "_blank"; link.rel = "noopener";
    item.append(link); $("citations").append(item);
  } else if (name === "state") {
    $("state-message").textContent = data.message; $("state").hidden = false;
    const button = $("state-action");
    button.textContent = { retry: "Try again", rephrase: "Rephrase", contact: "Contact a person" }[data.action];
    button.onclick = () => data.action === "contact" ? (location.href = "mailto:support@example.com") : (data.action === "retry" ? ask() : $("question").focus());
  } else if (name === "paused") {
    $("paused-message").textContent = data.message; $("paused").hidden = false; runId = data.run_id; poll();
  } else if (name === "done" && data.timings && data.timings.first_token_ms) {
    $("timing").textContent = "First word after " + Math.round(data.timings.first_token_ms) + " ms.";
  }
}
```

`handle(name, data)` reacts to each kind of event.

- `token`: appends the text piece to the answer with `textContent +=`.
- `citation`: builds a list item with a link: `document.createElement` makes elements, `link.href` is the page-and-section address, `link.textContent` the visible words (page title and section), `link.target = "_blank"` opens a new tab, and `rel = "noopener"` stops the new page from controlling this one.
- `state`: shows the designed message and sets the action button's label from a small table (retry, rephrase or contact a person). Its `onclick` either opens a mail link, asks again, or focuses the question box.
- `paused`: shows the waiting message, remembers the run id and starts polling for the reviewer's answer.
- `done`: if timings are present, shows 'First word after N ms.' (`Math.round` rounds to a whole number).

```html
async function ask() {
  reset(); setRunning(true); controller = new AbortController();
  try {
    const response = await fetch("/ask", { method: "POST", signal: controller.signal,
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + token }, body: JSON.stringify({ question: $("question").value }) });
    if (!response.ok) { handle("state", { message: "Sign in again to ask a question.", action: "retry" }); return; }
    runId = response.headers.get("X-Run-Id");
    await readEvents(response);
  } catch (error) {
    if (error.name !== "AbortError") handle("state", { message: "The connection was lost.", action: "retry" });
  } finally { setRunning(false); }
}
```

`ask()` starts a question.

- `reset(); setRunning(true); controller = new AbortController();` clears the page, disables Ask and creates an `AbortController` whose `signal` is attached to the request. (This page's Stop button uses the server's stop endpoint, see below; the controller is the hook for cancelling from the browser side.)
- `fetch("/ask", { method: "POST", signal, headers, body })` sends the question. `headers` carries `Content-Type: application/json` and `Authorization: Bearer <token>`; `body` is `JSON.stringify({ question: ... })`.
- `if (!response.ok)` handles a non-2xx status (for example 401) with a designed message and a retry action.
- `runId = response.headers.get("X-Run-Id");` reads the run id the server put in a header, so Stop knows which run to stop.
- `await readEvents(response);` reads the stream to its end.
- `catch (error) { if (error.name !== "AbortError") ... }` shows 'The connection was lost' for network failures; an abort is not an error.
- `finally { setRunning(false); }` re-enables Ask whatever happened.

```html
async function stop() {
  if (runId) await fetch("/runs/" + runId + "/stop", { method: "POST", headers: { Authorization: "Bearer " + token } });
}
```

`stop()` sends `POST /runs/<id>/stop` with the token. The server marks the run as stopped; its stream checks the mark after each piece, cancels the model call and sends the `stopped` state.

```html
async function poll() {
  for (let attempt = 0; attempt < 120; attempt++) {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    const status = await (await fetch("/runs/" + runId + "/status", { headers: { Authorization: "Bearer " + token } })).json();
    if (status.status === "answered") {
      $("paused").hidden = true;
      const response = await fetch("/runs/" + runId + "/resume", { headers: { Authorization: "Bearer " + token } });
      await readEvents(response); return;
    }
  }
}
```

`poll()` waits for a reviewer.

- A loop of up to 120 attempts, two seconds apart: `await new Promise((resolve) => setTimeout(resolve, 2000))` is the JavaScript way to sleep without blocking.
- Each time it asks `GET /runs/<id>/status`. When the status is `answered`, it hides the waiting message, calls `GET /runs/<id>/resume` and reads that stream with `readEvents` — the answer then appears like any other.

```html
$("ask").addEventListener("click", ask);
$("stop").addEventListener("click", stop);
</script>
</body>
</html>
```

The last lines connect the buttons: `addEventListener("click", fn)` runs `fn` when the button is clicked. `</script>`, `</body>` and `</html>` close the page.

### The reviewer screen

From `src/streaming_assistant/interfaces/static/review.html`:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Review queue</title>
```

The same opening as the chat page: doctype, language, encoding, viewport, title.

```html
<style>
  :root { color-scheme: light dark; }
  body { font:16px/1.5 system-ui, sans-serif; max-width:42rem; margin:0 auto; padding:1rem; }
  article { border:1px solid #8888; border-radius:6px; padding:.75rem; margin:1rem 0; }
  textarea, input { width:100%; box-sizing:border-box; font:inherit; margin:.25rem 0; }
  button:focus-visible, textarea:focus-visible, input:focus-visible { outline:2px solid #0b57d0; outline-offset:2px; }
</style>
</head>
```

Shorter CSS.

- `article { border:1px solid #8888; border-radius:6px; ... }`: each waiting question is an `<article>` card with a faint border (`#8888` is grey with some transparency) and rounded corners.
- `textarea, input { width:100%; box-sizing:border-box; font:inherit; margin:.25rem 0; }`: form controls fill the width and use the page font.
- the `:focus-visible` rule draws an outline on a keyboard-focused control.

```html
<body>
<h1>Paused questions</h1>
<p>Answer, then cite a help section (for example help-07#refund-timing) or tick that no page covers it.</p>
<div id="list" role="region" aria-live="polite"></div>
```

The static part of the page: a heading, a hint (cite a section like `help-07#refund-timing` or tick that no page covers it), and `<div id="list" role="region" aria-live="polite">` where the cards are built.

```html
<script>
const token = new URLSearchParams(location.search).get("token") || "demo-reviewer-token";
const headers = { "Content-Type": "application/json", Authorization: "Bearer " + token };
async function load() {
  const runs = await (await fetch("/reviews", { headers })).json();
  const list = document.getElementById("list"); list.textContent = runs.length ? "" : "Nothing is waiting.";
  for (const run of runs) {
    const card = document.createElement("article");
    card.innerHTML = "<p><strong></strong></p><p class='why'></p><label>Your answer<textarea rows='3'></textarea></label>" +
      "<label>Cited section<input placeholder='help-07#refund-timing'></label><label><input type='checkbox'> No page covers this</label>" +
      "<label>Your id<input value='reviewer-1'></label><button type='button'>Send</button><p class='result' role='status'></p>";
    card.querySelector("strong").textContent = run.question;
    card.querySelector(".why").textContent = "Why it paused: " + run.reason + ". Retrieved: " + run.retrieved.join(", ");
    const [answer] = card.querySelectorAll("textarea"), [cite, , reviewer] = card.querySelectorAll("input"), box = card.querySelectorAll("input")[1];
    card.querySelector("button").addEventListener("click", async () => {
      const response = await fetch("/reviews/" + run.run_id + "/answer", { method: "POST", headers,
        body: JSON.stringify({ reviewer_id: reviewer.value, answer: answer.value, cited: cite.value ? [cite.value] : [], no_page: box.checked }) });
      card.querySelector(".result").textContent = response.ok ? "Saved. The customer's page will resume." : (await response.json()).detail;
      if (response.ok) setTimeout(load, 800);
    });
    list.append(card);
  }
}
load();
</script>
</body>
</html>
```

The script.

- `token` is read from `?token=` or falls back to the fixed demo reviewer token; `headers` is built once with the JSON content type and the `Authorization` header.
- `load()` is an `async` function. `await (await fetch("/reviews", { headers })).json()` fetches the waiting runs and parses the JSON (two awaits: one for the response, one for its body).
- `list.textContent = runs.length ? "" : "Nothing is waiting."` clears the list or shows an empty-state message. `condition ? a : b` is the conditional expression.
- For each run, a card is built. `card.innerHTML = "<p><strong></strong></p>..."` fills it with **fixed** markup only (empty elements and labels); the server's text is then put in with `textContent` (`card.querySelector("strong").textContent = run.question;` and the 'Why it paused' line), so a question that contains markup is shown as text and never run.
- `const [answer] = card.querySelectorAll("textarea"), [cite, , reviewer] = card.querySelectorAll("input"), box = card.querySelectorAll("input")[1];` uses *destructuring* to pick the form controls out of the lists by position: the answer box, the section input, the checkbox and the reviewer id.
- The Send button's click handler posts to `/reviews/<run id>/answer` with `reviewer_id`, `answer`, `cited` (a list with the section, or empty) and `no_page`. If the server answers 2xx it shows 'Saved' and reloads the list after 0.8 seconds; otherwise it shows the server's `detail` (for example 'cite a help section, or say that no page covers this question').
- `load();` runs it once when the page opens.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
curl -s localhost:8100/ | head -12
```

Prints the top of the chat page (needs the server running).

```bash
curl -s localhost:8100/pages/help-04 | head -c 400
```

Prints a help page in HTML with `<section id="...">` elements.

```bash
open 'http://127.0.0.1:8100/pages/help-04#a-refund-usually-appears'
```

Opens the page scrolled to the cited section, which `:target` highlights in yellow.

## Mistakes people make

- Inserting server text with `innerHTML`, which can run injected markup. The pages build their markup from fixed strings and put every piece of server text in with `textContent`, which treats text as text.
- Relying on colour alone to show state.
- A page that works only with a mouse. The controls are real buttons.
- Forgetting the viewport meta tag, so the page is tiny on a phone.
- Mixing structure and script in ways that are hard to read; the script here is short and in one block.

## Check yourself

1. What is the DOM?
   *Answer:* The tree of elements the browser builds from the HTML.
2. What does an `id` attribute do?
   *Answer:* Names one element so script and style can find it.
3. Why use `textContent` instead of `innerHTML` for server text?
   *Answer:* `textContent` never interprets the text as markup, so injected tags cannot run.
4. Where does the page come from?
   *Answer:* The server returns the file at `/` and `/review`.
5. What does `<button>` give you over a clickable `<div>`?
   *Answer:* Keyboard use and correct behaviour for assistive technology.

## Further reading

- [MDN: HTML](https://developer.mozilla.org/en-US/docs/Web/HTML)
- [HTML Living Standard](https://html.spec.whatwg.org/multipage/)
