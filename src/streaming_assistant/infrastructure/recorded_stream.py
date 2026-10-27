"""Recorded streams: a cassette maps a hash of the whole request to the text pieces and usage, so tests run offline."""

from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from streaming_assistant.application.ports import Chunk, StreamingModel, StreamRequest, TextDelta, Usage


class MissingRecordingError(LookupError):
    """No recording matches this request; the message says how to re-record."""


def request_key(model_id: str, request: StreamRequest) -> str:
    """Hash of everything that decides the stream: model, prompt version, tier, system text and user text."""
    return hashlib.sha256(
        json.dumps([model_id, request.prompt_version, request.tier, request.system, request.user]).encode()
    ).hexdigest()


class RecordedStreamingModel:
    """Replays the recorded pieces; a request with no recording fails loudly."""

    def __init__(self, path: Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        self.model_id: str = data["model"]
        self.provenance: str = data["provenance"]
        self._entries: dict[str, dict[str, Any]] = data["entries"]

    async def stream(self, request: StreamRequest) -> AsyncIterator[Chunk]:
        """The recorded text pieces, then the usage."""
        key = request_key(self.model_id, request)
        entry = self._entries.get(key)
        if entry is None:
            raise MissingRecordingError(
                f"no recording for prompt {request.prompt_version} (key {key[:12]}); re-record with `make record` (needs ANTHROPIC_API_KEY)"
            )
        for piece in entry["pieces"]:
            yield TextDelta(piece)
        yield Usage(int(entry["input_tokens"]), int(entry["output_tokens"]))


class RecordingStreamingModel:
    """Wraps a model and writes every stream it returns to a cassette."""

    def __init__(self, inner: StreamingModel, path: Path, model_id: str, provenance: str) -> None:
        self._inner = inner
        self._path = path
        self._model_id = model_id
        self._provenance = provenance
        self._entries: dict[str, dict[str, Any]] = {}

    async def stream(self, request: StreamRequest) -> AsyncIterator[Chunk]:
        """Pass the stream through, remember it and rewrite the cassette when it ends."""
        pieces: list[str] = []
        usage = Usage(0, 0)
        async for chunk in self._inner.stream(request):
            if isinstance(chunk, TextDelta):
                pieces.append(chunk.text)
            else:
                usage = chunk
            yield chunk
        self._entries[request_key(self._model_id, request)] = {
            "pieces": pieces,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
        }
        document = {"provenance": self._provenance, "model": self._model_id, "entries": self._entries}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")
