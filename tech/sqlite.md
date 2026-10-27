# SQLite and Python's sqlite3 module

## What it is

SQLite is a database that is a library, not a server: the whole database is one file, and the program that uses it reads and writes that file directly. Python's standard `sqlite3` module talks to it. There is nothing to install or start, which makes it a good fit for a teaching repository.

## Why this repository uses it

Paused runs must survive a server restart, and the audit trail must be append-only. A SQLite file does both, with triggers and constraints as a second guard behind the code.

## Where it appears

| File | What it does with SQLite and Python's sqlite3 module |
| --- | --- |
| `src/streaming_assistant/infrastructure/sqlite_store.py` | `Database`, the token check, the paused-run store, the audit log |
| `sql/*.sql` | schema (with triggers), tokens, queries |
| `db/assistant.sqlite` | the database file (not committed) |

## How it works underneath

`sqlite3.connect("db/agent.sqlite")` opens (or creates) the file and returns a *connection*. `connection.execute("SELECT ... WHERE id = ?", (value,))` runs SQL; the `?` marks a place for a *parameter*, so data is never mixed into the SQL text. `fetchall()` returns rows as tuples. `executescript(text)` runs many statements at once (used for the numbered SQL files). A *transaction* starts on the first change and ends with `commit()` (keep) or `rollback()` (undo); `with connection:` commits on success and rolls back on an exception.

SQLite checks `FOREIGN KEY` rules only when `PRAGMA foreign_keys = ON` is run on that connection. `:memory:` as the file name makes a private database in RAM that disappears when the connection closes; the tests use it so they need no files. SQLite stores any value in a column with a loose type, which is why the `CHECK` constraints in this repository matter. One writer at a time: while a writing transaction is open, other writers wait.

## Walkthrough of this repository's use

The database object: one connection behind a lock, rebuilt from the SQL scripts on request.

From `src/streaming_assistant/infrastructure/sqlite_store.py`:

```python
class Database:
    """One SQLite file behind a lock; every operation is a short transaction."""
```

- `class Database:`: A class that wraps one table or one concern of the database.
- `"""One SQLite file behind a lock; every operation is a short transaction."""`: The docstring.

```python
    def __init__(self, path: Path | str) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.lock = threading.RLock()
```

- `def __init__(self, path: Path | str) -> None:`: The method `__init__`.
- `if str(path) != ":memory:":`: Only when `str(path) != ":memory:"`.
- `Path(path).parent.mkdir(parents=True, exist_ok=True)`: Creates the database file's folder (and its parents) if it is missing, without an error if it exists.
- `self._connection = sqlite3.connect(path, check_same_thread=False, isolation_level=None)`: Opens the database. `check_same_thread=False` lets other threads use the connection (the lock guards it). `isolation_level=None` turns off the module's automatic transactions, so the code controls them itself.
- `self.lock = threading.RLock()`: A re-entrant lock: the same thread may take it twice. One connection must not be used by two threads at once.

```python
    def apply_scripts(self, sql_dir: Path) -> list[str]:
        """Run the numbered scripts (DDL, then seed); returns the names that ran."""
        with self.lock:
            for table in ("audit_log", "paused_runs", "api_tokens"):
                self._connection.execute(f"DROP TABLE IF EXISTS {table}")
            for name in SCRIPTS:
                self._connection.executescript((sql_dir / name).read_text(encoding="utf-8"))
        return list(SCRIPTS)
```

- `def apply_scripts(self, sql_dir: Path) -> list[str]:`: The method `apply_scripts`.
- `"""Run the numbered scripts (DDL, then seed); returns the names that ran."""`: The docstring.
- `with self.lock:`: Runs the block with `self.lock` managed: it is released or committed when the block ends.
- `for table in ("audit_log", "paused_runs", "api_tokens"):`: Repeats for each item of `("audit_log", "paused_runs", "api_tokens")`.
- `self._connection.execute(f"DROP TABLE IF EXISTS {table}")`: Calls `self._connection.execute`.
- `for name in SCRIPTS:`: Repeats for each item of `SCRIPTS`.
- `self._connection.executescript((sql_dir / name).read_text(encoding="utf-8"))`: Calls `self._connection.executescript`.
- `return list(SCRIPTS)`: Gives back `list(SCRIPTS)`.

```python
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
```

- `def execute(self, sql: str, parameters: Sequence[object] = ()) -> list[tuple[object, ...]]:`: The method `execute`.
- `"""Run one statement in a transaction and return its rows."""`: The docstring.
- `with self.lock:`: Runs the block with `self.lock` managed: it is released or committed when the block ends.
- `self._connection.execute("BEGIN IMMEDIATE")`: Calls `self._connection.execute`.
- `try:`: Starts a guarded block.
- `rows = self._connection.execute(sql, tuple(parameters)).fetchall()`: Stores `self._connection.execute(sql, tuple(parameters)).fetchall()` in `rows`.
- `except BaseException:`: Handles `BaseException`.
- `self._connection.execute("ROLLBACK")`: Calls `self._connection.execute`.
- `raise`: Re-raises the same error, so the caller sees the real failure.
- `self._connection.execute("COMMIT")`: Calls `self._connection.execute`.
- `return rows`: Gives back `rows`.

```python
    def close(self) -> None:
        """Close the connection."""
        with self.lock:
            self._connection.close()
```

- `def close(self) -> None:`: The method `close`.
- `"""Close the connection."""`: The docstring.
- `with self.lock:`: Runs the block with `self.lock` managed: it is released or committed when the block ends.
- `self._connection.close()`: Calls `self._connection.close`.

Appending to the hash chain: read the last hash and insert the next entry while holding the lock, so the chain cannot fork.

From `src/streaming_assistant/infrastructure/sqlite_store.py`:

```python
class SqliteAudit:
    """The audit log. Appending reads the last hash and inserts in one transaction, so the chain has no fork."""
```

- `class SqliteAudit:`: A class that wraps one table or one concern of the database.
- `"""The audit log. Appending reads the last hash and inserts in one transaction, so the chain has no fork."""`: The docstring.

```python
    def __init__(self, database: Database, clock: SystemClock | None = None) -> None:
        self._database = database
        self._clock = clock or SystemClock()
```

- `def __init__(self, database: Database, clock: SystemClock | None = None) -> None:`: The method `__init__`.
- `self._database = database`: Stores `database` in `self._database`.
- `self._clock = clock or SystemClock()`: Stores `clock or SystemClock()` in `self._clock`.

```python
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
```

- `def append(self, run: str, step: str, actor: str, content: str) -> AuditEntry:`: The method `append`.
- `"""Add one step to the chain."""`: The docstring.
- `with self._database.lock:`: Runs the block with `self._database.lock` managed: it is released or committed when the block ends.
- `last = self._database.execute("SELECT hash FROM audit_log ORDER BY seq DESC LIMIT 1")`: Stores `self._database.execute("SELECT hash FROM audit_log ORDER BY seq DESC LIMIT 1")` in `last`.
- `entry = make_entry(str(last[0][0]) if last else None, run, step, actor, self._clock.now(), content)`: Stores `make_entry(str(last[0][0]) if last else None, run, step, actor, self._clock.now(), content)` in `entry`.
- `self._database.execute(`: Runs a SQL statement (inside the database object's own transaction); the SQL text and its parameters follow.
- `"INSERT INTO audit_log (run_id, step, actor, at, content, previous, hash) VALUES (?, ?, ?, ?, ?, ?, ?)",`: The SQL text of a INSERT; each `?` is a parameter placeholder.
- `(entry.run, entry.step, entry.actor, entry.at, entry.content, entry.previous, entry.hash),`: The parameter tuple: the values for the `?` marks, in order.
- `return entry`: Gives back `entry`.

### The rest of the module

#### `src/streaming_assistant/infrastructure/sqlite_store.py`

The module's docstring says: *SQLite adapters: API tokens, paused runs (durable across a restart) and the hash-chained audit log.*

- `class Database:` (class): One SQLite file behind a lock; every operation is a short transaction.
  - `def __init__(self, path: Path | str) -> None:`
  - `def apply_scripts(self, sql_dir: Path) -> list[str]:`: Run the numbered scripts (DDL, then seed); returns the names that ran.
  - `def execute(self, sql: str, parameters: Sequence[object] = ()) -> list[tuple[object, ...]]:`: Run one statement in a transaction and return its rows.
  - `def close(self) -> None:`: Close the connection.
- `def token_hash(token: str) -> str:`: The stored form of a bearer token.
- `class SqliteAuthenticator:` (class): Looks a bearer token up by its hash.
  - `def __init__(self, database: Database) -> None:`
  - `def role_of(self, token: str) -> str | None:`: 'customer', 'reviewer' or None.
- `class SqliteRunStore:` (class): Paused runs.
  - `def __init__(self, database: Database) -> None:`
  - `def save_pause(self, run: PausedRun, at: datetime) -> None:`: Store a new paused run (waiting).
  - `def get(self, run_id: str) -> PausedRun | None:`: One run, or None.
  - `def waiting(self, limit: int) -> Sequence[PausedRun]:`: Runs waiting for a reviewer, oldest first.
  - `def record_answer( self, run_id: str, reviewer_id: str, answer: str, cited: Sequence[str], no_page: bool, at: datetime ) -> None:`: Store a validated answer and move the run to `answered`.
  - `def mark_resumed(self, run_id: str, at: datetime) -> None:`: Move the run to `resumed`.
  - `def _row(row: tuple[object, ...]) -> PausedRun:`
- `class SqliteAudit:` (class): The audit log. Appending reads the last hash and inserts in one transaction, so the chain has no fork.
  - `def __init__(self, database: Database, clock: SystemClock | None = None) -> None:`
  - `def append(self, run: str, step: str, actor: str, content: str) -> AuditEntry:`: Add one step to the chain.
  - `def entries(self, run: str | None = None) -> Sequence[AuditEntry]:`: The whole chain in order, or the steps of one run.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
make db
```

Prints `applied 001_schema.sql, 002_seed.sql to .../db/assistant.sqlite`.

```bash
sqlite3 db/assistant.sqlite '.tables'
```

Lists `api_tokens`, `audit_log`, `paused_runs`.

```bash
sqlite3 db/assistant.sqlite "update audit_log set content='x'"
```

Fails with `the audit log is append-only`: the trigger refuses it.

```bash
make verify-audit
```

Prints the number of entries and `first broken index: None`.

## Mistakes people make

- Forgetting `PRAGMA foreign_keys = ON`; the rules are then silently ignored.
- Sharing one connection between threads without a lock. The code serialises access with a lock.
- Leaving transactions open, which blocks other writers.
- Using string formatting to build SQL.
- Expecting a file database to survive `make down`; it deletes the `db/` folder, and `make up` rebuilds it from `sql/`.

## Check yourself

1. Is SQLite a server?
   *Answer:* No. It is a library that reads and writes one file.
2. What does `:memory:` mean as a database name?
   *Answer:* A temporary database held in RAM that vanishes when the connection closes.
3. What is `?` in `WHERE id = ?`?
   *Answer:* A parameter placeholder; the value is passed separately.
4. What does `with connection:` do?
   *Answer:* Commits the transaction on success and rolls it back on an exception.
5. How do you make SQLite enforce foreign keys?
   *Answer:* Run `PRAGMA foreign_keys = ON;` on each connection.

## Further reading

- [SQLite documentation](https://www.sqlite.org/docs.html)
- [Python sqlite3 module](https://docs.python.org/3.12/library/sqlite3.html)
- [SQLite foreign keys](https://www.sqlite.org/foreignkeys.html)
