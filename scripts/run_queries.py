"""Run sql/003_queries.sql against the local database and print each result: what `make queries` shows."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Each statement is preceded by a `-- name` comment."""
    database = ROOT / "db/assistant.sqlite"
    if not database.exists():
        print("no database yet: run `make up` first", file=sys.stderr)
        return 1
    connection = sqlite3.connect(database)
    name, statement = "", []
    for line in (ROOT / "sql/003_queries.sql").read_text(encoding="utf-8").splitlines():
        if line.startswith("--"):
            name = line.removeprefix("--").strip() or name
            continue
        statement.append(line)
        if line.rstrip().endswith(";"):
            cursor = connection.execute("\n".join(statement))
            columns = [column[0] for column in cursor.description or ()]
            rows = cursor.fetchall()
            print(f"== {name}")
            print("  " + " | ".join(columns))
            for row in rows:
                print("  " + " | ".join(str(value) for value in row))
            if not rows:
                print("  (no rows)")
            statement = []
    connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
