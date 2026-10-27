"""A paused run, answered by a reviewer, survives a server restart and resumes; then the audit trail is replayed.

Pass --local to use db/assistant.sqlite (rebuilt first) instead of a temporary file.

Two server processes share one database file: the first pauses the run and takes the reviewer's answer (an empty answer
and an answer that cites no page are refused first); it is stopped with SIGTERM; the second finds the run in the database
and resumes it with the validated answer in the model's context. This is what `make pause-demo` shows.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
CUSTOMER = {"Authorization": "Bearer demo-customer-token"}
REVIEWER = {"Authorization": "Bearer demo-reviewer-token"}
QUESTION = "Can I get a refund on an order from seventy five days ago?"


def free_port() -> int:
    """A port nothing is listening on."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def start(database: Path) -> tuple[subprocess.Popen[bytes], str]:
    """Start the server on a free port over the given database file and wait for /healthz."""
    port = free_port()
    env = {
        **os.environ,
        "PROJECT_ROOT": str(ROOT),
        "PORT": str(port),
        "DATABASE": str(database),
        "LOG_LEVEL": "WARNING",
    }
    process = subprocess.Popen([sys.executable, "-m", "streaming_assistant.interfaces.cli", "serve"], env=env, cwd=ROOT)
    base = f"http://127.0.0.1:{port}"
    for _ in range(300):
        try:
            if httpx.get(base + "/healthz", timeout=1).status_code == 200:
                return process, base
        except httpx.HTTPError:
            time.sleep(0.1)
    process.kill()
    raise SystemExit("the server did not start")


def events(response: httpx.Response) -> list[tuple[str, dict[str, object]]]:
    """Parse a finished server-sent-event body into (name, data) pairs."""
    parsed, name = [], ""
    for line in response.text.splitlines():
        if line.startswith("event: "):
            name = line.removeprefix("event: ")
        elif line.startswith("data: "):
            parsed.append((name, json.loads(line.removeprefix("data: "))))
    return parsed


def main() -> int:
    """Run the demonstration; returns 0 when every expected step happened."""
    # With --local the demo leaves its rows in db/assistant.sqlite so `make queries` has something to show.
    local = "--local" in sys.argv
    database = (
        ROOT / "db/assistant.sqlite" if local else Path(tempfile.mkdtemp(prefix="pause-demo-")) / "assistant.sqlite"
    )
    subprocess.run(
        [sys.executable, "-m", "streaming_assistant.interfaces.cli", "db"],
        env={**os.environ, "PROJECT_ROOT": str(ROOT), "DATABASE": str(database)},
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    first, base = start(database)
    try:
        asked = httpx.post(base + "/ask", json={"question": QUESTION}, headers=CUSTOMER, timeout=30)
        run_id = asked.headers["x-run-id"]
        names = [name for name, _ in events(asked)]
        print(f"asked: {QUESTION}\n  events: {names}")
        waiting = httpx.get(base + "/reviews", headers=REVIEWER).json()
        retrieved = waiting[0]["retrieved"]
        print(f"reviewer screen shows {len(waiting)} waiting run(s): {waiting[0]['reason']}, retrieved {retrieved}")
        empty = httpx.post(
            base + f"/reviews/{run_id}/answer", headers=REVIEWER, json={"reviewer_id": "ana", "answer": " "}
        )
        no_cite = httpx.post(
            base + f"/reviews/{run_id}/answer", headers=REVIEWER, json={"reviewer_id": "ana", "answer": "Sure."}
        )
        print(
            f"empty answer -> {empty.status_code}; answer citing no page -> {no_cite.status_code}: {no_cite.json()['detail']}"
        )
        accepted = httpx.post(
            base + f"/reviews/{run_id}/answer",
            headers=REVIEWER,
            json={
                "reviewer_id": "ana",
                "answer": "Your order is outside the 30 day window, so I approved a store credit instead of a refund.",
                "cited": retrieved[:1],
            },
        )
        print(f"valid answer -> {accepted.status_code} {accepted.json()}")
    finally:
        first.send_signal(signal.SIGTERM)
        first.wait(timeout=20)
    print("server stopped; starting a second server on the same database file")
    second, base = start(database)
    try:
        status = httpx.get(base + f"/runs/{run_id}/status", headers=CUSTOMER).json()["status"]
        resumed = httpx.get(base + f"/runs/{run_id}/resume", headers=CUSTOMER, timeout=30)
        parsed = events(resumed)
        text = "".join(str(data["text"]) for name, data in parsed if name == "token")
        print(f"after restart the run is '{status}'; resumed events: {[name for name, _ in parsed]}")
        print(f"customer saw: {text}")
        verified = httpx.get(base + "/audit/verify", headers=REVIEWER).json()
        print(f"audit chain: {verified}")
    finally:
        second.send_signal(signal.SIGTERM)
        second.wait(timeout=20)
    print("replay of the audit trail:")
    replay = subprocess.run(
        [sys.executable, "-m", "streaming_assistant.interfaces.cli", "replay", run_id],
        env={**os.environ, "PROJECT_ROOT": str(ROOT), "DATABASE": str(database)},
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    print(replay.rstrip())
    steps = [line.split()[1] for line in replay.splitlines()]
    ok = (
        names[-2:] == ["paused", "done"]
        and accepted.status_code == 200
        and empty.status_code == 422
        and status == "answered"
        and [name for name, _ in parsed][-1] == "done"
        and verified["first_broken_index"] is None
        and steps[:4] == ["received", "paused", "answered", "validated"]
        and "resumed" in steps
        and steps[-1] == "shown"
    )
    print("ok" if ok else "NOT OK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
