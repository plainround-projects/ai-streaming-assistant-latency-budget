"""Record the streams for eight sample questions into a cassette that the recorded adapter replays offline.

python scripts/record_streams.py --author   # write tests/fixtures/cassettes/stream-v1.json from the scripted model (not a model recording)
python scripts/record_streams.py            # MODEL_ADAPTER=claude: call the real model, write tests/fixtures/cassettes/live-v1.json (needs a key)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

from streaming_assistant.infrastructure.recorded_stream import RecordingStreamingModel
from streaming_assistant.infrastructure.scripted_stream import Pace, ScriptedStreamingModel
from streaming_assistant.infrastructure.settings import Settings
from streaming_assistant.interfaces.measure import collect
from streaming_assistant.interfaces.wiring import build_components, build_model

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = 8


def questions() -> list[str]:
    """The first eight questions that should be answered, in file order."""
    rows = (json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines())
    return [row["question"] for row in rows if not row["should_pause"]][:SAMPLE]


async def record(settings: Settings, author: bool) -> Path:
    """Run the questions through the real path with the wrapped model and return the cassette path."""
    if author:
        inner = ScriptedStreamingModel(Pace(0, 0, 0, 0, jitter=0))
        path = ROOT / "tests/fixtures/cassettes/stream-v1.json"
        provenance = "authored by scripts/record_streams.py --author from the scripted streaming model; not a model recording. Replace with `make record`."
        model_id = "authored-scripted-stream"
    else:
        inner = build_model(settings)
        path = ROOT / "tests/fixtures/cassettes/live-v1.json"
        provenance = f"recorded from {settings.model_ids['standard']} through scripts/record_streams.py"
        model_id = settings.model_ids["standard"]
    recorder = RecordingStreamingModel(inner, path, model_id, provenance)
    components = build_components(replace(settings, database=":memory:"), model=recorder, fresh=True)
    for number, question in enumerate(questions()):
        await collect(components, f"record-{number}", question)
    return path


def main() -> int:
    """Entry point."""
    author = "--author" in sys.argv
    settings = Settings.from_environ({**os.environ, "PROJECT_ROOT": str(ROOT)})
    if not author and settings.model_adapter != "claude":
        print(
            "set MODEL_ADAPTER=claude and ANTHROPIC_API_KEY to record from the real model, or pass --author",
            file=sys.stderr,
        )
        return 2
    path = asyncio.run(record(settings, author))
    print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
