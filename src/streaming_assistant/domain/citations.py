"""Citations: a citation is a section that was retrieved for this request. Anything else is dropped and counted."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from streaming_assistant.domain.retrieval import Section

_CITATION = re.compile(r"\[(help-\d+#[a-z0-9-]+)\]")


class MarkerStripper:
    """Removes `[page#section]` markers from a stream of text pieces, even when a marker is split across pieces, and
    remembers the refs it saw. A bracket that never closes within 40 characters is released as ordinary text."""

    def __init__(self) -> None:
        self._held = ""
        self.refs: list[str] = []

    def feed(self, piece: str) -> str:
        """Text that is safe to show now."""
        text = self._held + piece
        self._held = ""
        out: list[str] = []
        while text:
            start = text.find("[")
            if start < 0:
                out.append(text)
                break
            out.append(text[:start])
            end = text.find("]", start)
            if end < 0:
                if len(text) - start > 40:
                    out.append(text[start])
                    text = text[start + 1 :]
                    continue
                self._held = text[start:]
                break
            marker = text[start : end + 1]
            ref = marker[1:-1]
            if _CITATION.fullmatch(marker):
                if ref not in self.refs:
                    self.refs.append(ref)
            else:
                out.append(marker)
            text = text[end + 1 :]
        return "".join(out)

    def finish(self) -> str:
        """Whatever was held back at the end of the stream."""
        held, self._held = self._held, ""
        return held


def check_refs(refs: Sequence[str], allowed: Mapping[str, Section]) -> tuple[tuple[Section, ...], int]:
    """(sections that may be shown, number dropped). A ref counts only when it is one of the sections allowed for this
    request: the ones retrieved for it, plus the ones a reviewer cited."""
    shown = tuple(allowed[ref] for ref in refs if ref in allowed)
    return shown, len(refs) - len(shown)
