"""The real adapter: Claude streaming through the official SDK. Leaving the stream closes the HTTP connection upstream."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import anthropic

from streaming_assistant.application.ports import Chunk, StreamRequest, TextDelta, Usage
from streaming_assistant.domain.errors import ProviderError, RateLimitedError, RefusedError
from streaming_assistant.infrastructure.environment import ConfigurationError


class ClaudeStreamingModel:
    """One streamed Messages API call. `tier` picks the model id: the fast tier uses the small model."""

    def __init__(
        self, model_ids: dict[str, str], api_key: str | None, *, timeout_seconds: float = 60.0, client: Any = None
    ) -> None:
        if client is None:
            if not api_key:
                raise ConfigurationError("ANTHROPIC_API_KEY must be set to use the Claude adapter")
            client = anthropic.AsyncAnthropic(api_key=api_key, timeout=timeout_seconds, max_retries=0)
        self._client = client
        self._model_ids = model_ids

    async def stream(self, request: StreamRequest) -> AsyncIterator[Chunk]:
        """Yield text deltas as they arrive, then the usage; map provider failures to the assistant's named errors."""
        model = self._model_ids.get(request.tier, self._model_ids["standard"])
        try:
            async with self._client.messages.stream(
                model=model, max_tokens=700, system=request.system, messages=[{"role": "user", "content": request.user}]
            ) as stream:
                async for text in stream.text_stream:
                    yield TextDelta(text)
                final = await stream.get_final_message()
        except anthropic.RateLimitError as error:
            raise RateLimitedError(str(error)) from error
        except (anthropic.APIConnectionError, anthropic.APIStatusError) as error:
            raise ProviderError(f"{type(error).__name__}: {error}") from error
        if final.stop_reason == "refusal":
            raise RefusedError("stop_reason=refusal")
        yield Usage(final.usage.input_tokens, final.usage.output_tokens)
