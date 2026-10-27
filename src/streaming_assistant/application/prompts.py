"""Prompts as files: a two-fence header (version, owner), then the prompt text."""

from __future__ import annotations

from dataclasses import dataclass


class PromptFileError(ValueError):
    """A prompt file does not have the two-fence header with a version and an owner."""


@dataclass(frozen=True, slots=True)
class PromptFile:
    """A versioned prompt."""

    name: str
    version: str
    owner: str
    text: str


def parse_prompt_file(name: str, content: str) -> PromptFile:
    """Split `---`, header lines, `---`, then the prompt text; both fences are required."""
    parts = content.split("---\n", 2)
    if len(parts) != 3 or parts[0].strip():
        raise PromptFileError(f"{name}: expected a leading '---' fence, a header and a closing '---' fence")
    fields = dict(line.split(": ", 1) for line in parts[1].strip().splitlines() if ": " in line)
    for required in ("version", "owner"):
        if required not in fields:
            raise PromptFileError(f"{name}: header lacks {required}")
    return PromptFile(name, fields["version"], fields["owner"], parts[2].strip())
