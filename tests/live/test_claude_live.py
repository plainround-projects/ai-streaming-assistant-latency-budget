"""Opt-in: streams one real answer and closes a second stream early. Run with `make test-live` (RUN_LIVE=1 and a key)."""

import asyncio
import os

import pytest

from streaming_assistant.application.ports import StreamRequest, TextDelta, Usage
from streaming_assistant.infrastructure.claude_stream import ClaudeStreamingModel

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("RUN_LIVE") != "1" or not os.environ.get("ANTHROPIC_API_KEY"),
        reason="set RUN_LIVE=1 and ANTHROPIC_API_KEY to call the real model",
    ),
]

REQUEST = StreamRequest(
    "Answer in one short sentence and cite the passage as [help-01#shipping-times].",
    "Passages:\n[help-01#shipping-times] Shipping times: Standard delivery takes three to five days.\nQuestion: How long is delivery?",
    "answer.v1",
)


def model() -> ClaudeStreamingModel:
    return ClaudeStreamingModel(
        {"standard": os.environ.get("MODEL_ID", "claude-sonnet-5-5"), "fast": "claude-haiku-5-5"},
        os.environ["ANTHROPIC_API_KEY"],
    )


def test_the_real_model_streams_text_then_usage():
    async def go():
        return [chunk async for chunk in model().stream(REQUEST)]

    chunks = asyncio.run(go())
    assert any(isinstance(c, TextDelta) and c.text for c in chunks) and isinstance(chunks[-1], Usage)
    assert "help-01#shipping-times" in "".join(c.text for c in chunks if isinstance(c, TextDelta))


def test_closing_the_stream_early_ends_the_call_without_an_error():
    async def go():
        stream = aiter(model().stream(REQUEST))
        first = await anext(stream)
        await stream.aclose()  # type: ignore[attr-defined]
        return first

    assert isinstance(asyncio.run(go()), TextDelta)
