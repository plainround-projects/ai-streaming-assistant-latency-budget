"""SQLite adapters: API tokens, paused runs (durable across a restart) and the hash-chained audit log."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from streaming_assistant.application.ports import PausedRun
from streaming_assistant.domain.audit import AuditEntry, make_entry
from streaming_assistant.infrastructure.clock import SystemClock

SCRIPTS = ("001_schema.sql", "002_seed.sql")


class Database:
    """One SQLite file behind a lock; every operation is a short transaction."""

    def __init__(self, path: Path | str) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.lock = threading.RLock()

    def apply_scripts(self, sql_dir: Path) -> list[str]:
        """Run the numbered scripts (DDL, then seed); returns the names that ran."""
        with self.lock:
            for table in ("audit_log", "paused_runs", "api_tokens"):
                self._connection.execute(f"DROP TABLE IF EXISTS {table}")
            for name in SCRIPTS:
                self._connection.executescript((sql_dir / name).read_text(encoding="utf-8"))
        return list(SCRIPTS)

    def execute(self, sql: str, parameters: Sequence[object] = ()) -> list[tuple[object, ...]]:
        """Run one statement in a transaction and return its rows."""
        with self.lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                rows = self._connection.execute(sql, tuple(parameters)).fetchall()
            except BaseException:
                self._connection.execute("ROLLBACK")
                raise
            self._connection.execute("COMMIT")
        return rows

    def close(self) -> None:
        """Close the connection."""
        with self.lock:
            self._connection.close()


def token_hash(token: str) -> str:
    """The stored form of a bearer token."""
    return hashlib.sha256(token.encode()).hexdigest()


class SqliteAuthenticator:
    """Looks a bearer token up by its hash."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def role_of(self, token: str) -> str | None:
        """'customer', 'reviewer' or None."""
        rows = self._database.execute("SELECT role FROM api_tokens WHERE token_hash = ?", (token_hash(token),))
        return str(rows[0][0]) if rows else None


class SqliteRunStore:
    """Paused runs."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def save_pause(self, run: PausedRun, at: datetime) -> None:
        """Store a new paused run (waiting)."""
        self._database.execute(
            "INSERT OR REPLACE INTO paused_runs (run_id, question, retrieved, reason, status, created_at) VALUES (?, ?, ?, ?, 'waiting', ?)",
            (run.run_id, run.question, json.dumps(list(run.retrieved)), run.reason, at.isoformat()),
        )

    def get(self, run_id: str) -> PausedRun | None:
        """One run, or None."""
        rows = self._database.execute(
            "SELECT run_id, question, retrieved, reason, status, reviewer_id, answer, cited, no_page FROM paused_runs WHERE run_id = ?",
            (run_id,),
        )
        return self._row(rows[0]) if rows else None

    def waiting(self, limit: int) -> Sequence[PausedRun]:
        """Runs waiting for a reviewer, oldest first."""
        rows = self._database.execute(
            "SELECT run_id, question, retrieved, reason, status, reviewer_id, answer, cited, no_page FROM paused_runs "
            "WHERE status = 'waiting' ORDER BY created_at, run_id LIMIT ?",
            (limit,),
        )
        return [self._row(row) for row in rows]

    def record_answer(
        self, run_id: str, reviewer_id: str, answer: str, cited: Sequence[str], no_page: bool, at: datetime
    ) -> None:
        """Store a validated answer and move the run to `answered`."""
        self._database.execute(
            "UPDATE paused_runs SET status = 'answered', reviewer_id = ?, answer = ?, cited = ?, no_page = ?, answered_at = ? "
            "WHERE run_id = ? AND status = 'waiting'",
            (reviewer_id, answer, json.dumps(list(cited)), int(no_page), at.isoformat(), run_id),
        )

    def mark_resumed(self, run_id: str, at: datetime) -> None:
        """Move the run to `resumed`."""
        self._database.execute(
            "UPDATE paused_runs SET status = 'resumed', resumed_at = ? WHERE run_id = ?", (at.isoformat(), run_id)
        )

    @staticmethod
    def _row(row: tuple[object, ...]) -> PausedRun:
        return PausedRun(
            str(row[0]),
            str(row[1]),
            tuple(json.loads(str(row[2]))),
            str(row[3]),
            str(row[4]),
            None if row[5] is None else str(row[5]),
            None if row[6] is None else str(row[6]),
            tuple(json.loads(str(row[7]))),
            bool(row[8]),
        )


class SqliteAudit:
    """The audit log. Appending reads the last hash and inserts in one transaction, so the chain has no fork."""

    def __init__(self, database: Database, clock: SystemClock | None = None) -> None:
        self._database = database
        self._clock = clock or SystemClock()

    def append(self, run: str, step: str, actor: str, content: str) -> AuditEntry:
        """Add one step to the chain."""
        with self._database.lock:
            last = self._database.execute("SELECT hash FROM audit_log ORDER BY seq DESC LIMIT 1")
            entry = make_entry(str(last[0][0]) if last else None, run, step, actor, self._clock.now(), content)
            self._database.execute(
                "INSERT INTO audit_log (run_id, step, actor, at, content, previous, hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (entry.run, entry.step, entry.actor, entry.at, entry.content, entry.previous, entry.hash),
            )
        return entry

    def entries(self, run: str | None = None) -> Sequence[AuditEntry]:
        """The whole chain in order, or the steps of one run."""
        sql = "SELECT previous, run_id, step, actor, at, content, hash FROM audit_log"
        rows = self._database.execute(
            sql + (" WHERE run_id = ?" if run else "") + " ORDER BY seq", (run,) if run else ()
        )
        return [AuditEntry(*(str(cell) for cell in row)) for row in rows]
