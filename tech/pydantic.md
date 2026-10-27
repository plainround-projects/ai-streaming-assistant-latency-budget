# Pydantic

## What it is

Pydantic is a library that validates data against a description written as a Python class with type hints. You declare the fields and their types, for example `question: str = Field(min_length=3)`; Pydantic checks incoming data against it and either gives you a clean object or a precise error. FastAPI uses it for request and response bodies.

## Why this repository uses it

The two bodies the server accepts from outside, a question and a reviewer's answer, are the first places untrusted data enters. Pydantic models limit lengths and types before any application code runs.

## Where it appears

| File | What it does with Pydantic |
| --- | --- |
| `src/streaming_assistant/interfaces/http.py` | `AskIn` and `ReviewIn` |

## How it works underneath

A class that inherits from `BaseModel` becomes a *schema*. Creating an instance with data runs validation: types are checked or converted (the text `"5"` becomes the integer 5 where the field is `int`), constraints from `Field(...)` are enforced (`min_length`, `max_length`, `max_length` on lists), and defaults fill missing fields. A failure raises `ValidationError` listing each bad field; FastAPI turns that into HTTP status 422. The check happens at the edge of the program, so the inner code can trust the data.

Pydantic is installed because FastAPI needs it. This repository declares it directly only where it defines its own request models.

## Walkthrough of this repository's use

The two models are explained line by line in `fastapi.md` (section 'Server-Sent-Events plumbing and the request models'). In short: `AskIn.question` is 3 to 1,000 characters; `ReviewIn` has `reviewer_id` (1 to 64), `answer` (up to 2,000), `cited` (a list of at most 5), and `no_page` (a boolean, default false). A body that breaks any rule is answered with status 422 and a list of the problems, and the handler never runs. This repository's FastAPI module deliberately omits `from __future__ import annotations`, because the dependency functions are defined inside `create_app` and FastAPI must see real annotation objects.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/python -c "from streaming_assistant.interfaces.http import AskIn; print(AskIn(question='How long?'))"
```

Prints `question='How long?'`.

```bash
.venv/bin/python -c "from streaming_assistant.interfaces.http import AskIn; AskIn(question='hi')"
```

Fails: String should have at least 3 characters.

```bash
curl -s -X POST localhost:8100/ask -H 'Authorization: Bearer demo-customer-token' -H 'Content-Type: application/json' -d '{}'
```

A 422 answer that names the missing `question` field (needs the server running).

## Mistakes people make

- Skipping validation at the boundary and checking values deep inside the code.
- Over-trusting the type conversion: `"5"` converts to 5. Where that matters the code checks the raw input.
- Allowing unbounded text or lists. The models set maximum lengths.
- Using one model for requests and responses; they usually need different fields.
- Forgetting that validation errors reveal field names; the messages are fine for callers but should never contain secrets.

## Check yourself

1. What does a `BaseModel` class describe?
   *Answer:* The fields and types of some data, which Pydantic can validate.
2. What happens on invalid data?
   *Answer:* A `ValidationError` is raised, and FastAPI answers 422.
3. What does `Field(min_length=3)` do?
   *Answer:* Requires text of at least three characters.
4. Where should validation happen?
   *Answer:* At the edge of the program, where outside data comes in.
5. Why is Pydantic installed in a project that never installs it directly?
   *Answer:* FastAPI depends on it.

## Further reading

- [Pydantic documentation (pinned version 2.14.1)](https://docs.pydantic.dev/latest/)
- [Models](https://docs.pydantic.dev/latest/concepts/models/)
