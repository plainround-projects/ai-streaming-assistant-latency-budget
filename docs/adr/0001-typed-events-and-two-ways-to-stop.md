# 1. Every outcome is a typed event, and Stop has two paths that end in the same cancel

Status: accepted, 2026-10-27

## Context

A streaming answer can end five ways: complete, failed, thin, paused, or stopped. A page that only sees text cannot show a designed state for each, and a Stop that only stops forwarding still bills the tokens the model keeps producing.

## Decision

The assistant yields `token`, `citation`, `state`, `paused` and `done` events (the last carrying usage and stage timings); the HTTP layer only encodes them. Closing the connection raises `CancelledError` inside the generator, and `POST /runs/{id}/stop` sets a flag the generator checks after every piece. Both paths end in `aclose()` on the upstream iterator, which closes the provider's HTTP stream; the audit log records who stopped it (`client` or `customer`).

## Alternatives considered

- **Raising exceptions for failure states:** the server would have to translate them; tests need a server to see them.
- **Only closing the connection:** a proxy can hold it open, and a Stop button should work without relying on connection semantics.

## Consequences

- Each of the seven states has a test that forces it and checks the event and the text.
- The upstream cancel is measurable: `make stop-test` shows the cancel time and that produced tokens stop growing.
