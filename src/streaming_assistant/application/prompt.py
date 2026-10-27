"""Prompt assembly: where the stable text goes decides whether a provider's prefix cache can help."""

from __future__ import annotations

from collections.abc import Sequence

from streaming_assistant.application.ports import StreamRequest
from streaming_assistant.domain.retrieval import Hit

PROMPT_VERSION = "answer.v1"


def passages(hits: Sequence[Hit]) -> str:
    """The retrieved sections as numbered passages that carry their citation refs."""
    return "\n".join(f"[{hit.section.ref}] {hit.section.heading}: {hit.section.text}" for hit in hits)


def assemble(
    stable: str,
    hits: Sequence[Hit],
    question: str,
    *,
    stable_first: bool,
    tier: str,
    reviewer_answer: str | None = None,
) -> StreamRequest:
    """Stable instructions first (cacheable, the same for every request), then the passages and the question.

    With `stable_first=False` the passages come before the instructions, so the start of the prompt differs on every
    request and no prefix cache can apply (the baseline the load test compares against).
    """
    tail = f"Passages:\n{passages(hits)}\nQuestion: {question}"
    if reviewer_answer is not None:
        tail += f"\nReviewer-validated answer: {reviewer_answer}"
    if stable_first:
        return StreamRequest(stable, tail, PROMPT_VERSION, tier)
    return StreamRequest(f"Passages:\n{passages(hits)}\n\n{stable}", f"Question: {question}", PROMPT_VERSION, tier)
