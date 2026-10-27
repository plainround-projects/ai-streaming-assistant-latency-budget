# 3. A scripted streaming model whose latencies are settings

Status: accepted, 2026-10-27

## Context

The lesson asks for first-token times measured against a budget and a fix named with its before and after. No key was available, and a real provider's latency varies with load and region.

## Decision

`ScriptedStreamingModel` takes a time to first token (standard and fast tiers), a prefill cost per 1,000 uncached prompt tokens, a pace per token, a jitter, and a failure mode. It keeps a set of seen prompt prefixes, so a prompt that starts with the same stable text pays prefill only for the new part (a prefix-cache simulation). It writes its answer from the first retrieved passage and cites it, and now and then adds an invented citation to exercise the drop. It counts tokens produced and the time of each cancellation.

## Alternatives considered

- **Sleeping for fixed times in the tests:** hides the structure of the budget.
- **Recording a real provider:** needs a key and varies run to run.

## Consequences

- The load test shows which levers matter in this model of the world: routing easy questions to the small model moved p95 from about 1.57 s to about 0.50 s; the other levers moved it by less than the jitter. That says the method works; it does not say those numbers hold for a real provider.
- The recorded adapter and its cassette (`stream-v1.json`) are authored from this model and say so in their `provenance` field.
