# SQL

## What it is

SQL (Structured Query Language) is the language for talking to relational databases. A *relational database* stores data in *tables*: grids where each row is one record and each column is one kind of value. SQL lets you create tables, add rows, change or delete them, and ask questions (queries) about them.

## Why this repository uses it

The durable state is three tables and two triggers, written as SQL files so the database can be rebuilt from nothing and the audit trail read with plain queries.

## Where it appears

| File | What it does with SQL |
| --- | --- |
| `sql/001_schema.sql` | tables, indexes and the two append-only triggers |
| `sql/002_seed.sql` | the two demo tokens as hashes |
| `sql/003_queries.sql` | the report queries |
| `sql/reset.sql` | drops the paused-run and audit tables (triggers forbid DELETE) |

## How it works underneath

Statements end with `;`. The main ones:

- `CREATE TABLE name (...)` defines a table and its columns, each with a type and rules (*constraints*). `PRIMARY KEY` identifies a row; `NOT NULL` requires a value; `UNIQUE` forbids repeats; `CHECK (...)` rejects rows that break a condition; `REFERENCES other (column)` is a *foreign key*, which forces the value to exist in another table.
- `INSERT INTO t (columns) VALUES (...)` adds rows. `UPDATE` changes rows. `DELETE FROM t WHERE ...` removes rows.
- `SELECT columns FROM t WHERE condition GROUP BY ... ORDER BY ...` reads rows. `WHERE` filters rows; `GROUP BY` groups them so functions like `COUNT(*)` and `SUM(x)` work per group; `ORDER BY` sorts.
- `CREATE INDEX` builds a sorted structure so lookups by some columns are fast. A *unique index* also forbids repeats; a *partial index* (`WHERE ...`) covers only some rows.
- A *transaction* groups statements so they all happen or none do.

The database engine (here SQLite or PostgreSQL) parses the text, plans how to read the data, and does it. The same statements work in both with small differences, which the files point out.

The SQL files here are numbered: `001_schema.sql` (the structure), `002_seed.sql` (starting data), `003_queries.sql` (the questions the lesson asks), and `reset.sql` (empties the data). `make db` runs the first two in order on an empty database, so the structure is always rebuilt from the files, never edited by hand.

## Walkthrough of this repository's use

### `sql/001_schema.sql`

```sql
-- DDL for the assistant's durable state (SQLite). `make db` rebuilds db/assistant.sqlite from these scripts in order.
-- Who may call the API. Only a hash of the bearer token is stored.
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: DDL for the assistant's durable state (SQLite). `make db` rebuilds db/assistant.sqlite from these scripts in order. Who may call the API. Only a hash of the bearer token is stored.

```sql
CREATE TABLE api_tokens (
    token_hash TEXT PRIMARY KEY,
    role       TEXT NOT NULL CHECK (role IN ('customer', 'reviewer'))
);
```

- `CREATE TABLE api_tokens (`: creates a table named `api_tokens`: a grid in which every row is one record and every column one named kind of value. The columns are listed in the lines below.
- `token_hash TEXT PRIMARY KEY,`: A column `token_hash`, text (any length of characters); it is the primary key: the value that identifies a row, unique and never empty.
- `role       TEXT NOT NULL CHECK (role IN ('customer', 'reviewer'))`: A column `role`, text (any length of characters); `NOT NULL` means a value is required; `CHECK`: `role` must be one of the listed values: 'customer', 'reviewer'.
- `);`: ends the column list and the statement.

```sql
-- A run that paused for a human. Everything the resumed run needs is here, so it survives a restart.
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: A run that paused for a human. Everything the resumed run needs is here, so it survives a restart.

```sql
CREATE TABLE paused_runs (
    run_id       TEXT PRIMARY KEY,
    question     TEXT NOT NULL,
    retrieved    TEXT NOT NULL,                  -- JSON list of the section refs retrieved for the question
    reason       TEXT NOT NULL CHECK (reason IN ('policy_exception', 'no_page_covers')),
    status       TEXT NOT NULL DEFAULT 'waiting' CHECK (status IN ('waiting', 'answered', 'resumed')),
    reviewer_id  TEXT,
    answer       TEXT,
    cited        TEXT NOT NULL DEFAULT '[]',     -- JSON list of the section refs the reviewer cited
    no_page      INTEGER NOT NULL DEFAULT 0 CHECK (no_page IN (0, 1)),
    created_at   TEXT NOT NULL,
    answered_at  TEXT,
    resumed_at   TEXT,
    CHECK (status = 'waiting' OR (reviewer_id IS NOT NULL AND length(trim(answer)) > 0))
);
```

- `CREATE TABLE paused_runs (`: creates a table named `paused_runs`: a grid in which every row is one record and every column one named kind of value. The columns are listed in the lines below.
- `run_id       TEXT PRIMARY KEY,`: A column `run_id`, text (any length of characters); it is the primary key: the value that identifies a row, unique and never empty.
- `question     TEXT NOT NULL,`: A column `question`, text (any length of characters); `NOT NULL` means a value is required.
- `retrieved    TEXT NOT NULL,                  -- JSON list of the section refs retrieved for the question`: A column `retrieved`, text (any length of characters); `NOT NULL` means a value is required. The comment says: JSON list of the section refs retrieved for the question
- `reason       TEXT NOT NULL CHECK (reason IN ('policy_exception', 'no_page_covers')),`: A column `reason`, text (any length of characters); `NOT NULL` means a value is required; `CHECK`: `reason` must be one of the listed values: 'policy_exception', 'no_page_covers'.
- `status       TEXT NOT NULL DEFAULT 'waiting' CHECK (status IN ('waiting', 'answered', 'resumed')),`: A column `status`, text (any length of characters); `NOT NULL` means a value is required; `DEFAULT 'waiting'` is used when an insert gives no value; `CHECK`: `status` must be one of the listed values: 'waiting', 'answered', 'resumed'.
- `reviewer_id  TEXT,`: A column `reviewer_id`, text (any length of characters).
- `answer       TEXT,`: A column `answer`, text (any length of characters).
- `cited        TEXT NOT NULL DEFAULT '[]',     -- JSON list of the section refs the reviewer cited`: A column `cited`, text (any length of characters); `NOT NULL` means a value is required; `DEFAULT '[]'` is used when an insert gives no value. The comment says: JSON list of the section refs the reviewer cited
- `no_page      INTEGER NOT NULL DEFAULT 0 CHECK (no_page IN (0, 1)),`: A column `no_page`, a whole number; `NOT NULL` means a value is required; `DEFAULT 0` is used when an insert gives no value; `CHECK`: `no_page` must be one of the listed values: 0, 1.
- `created_at   TEXT NOT NULL,`: A column `created_at`, text (any length of characters); `NOT NULL` means a value is required.
- `answered_at  TEXT,`: A column `answered_at`, text (any length of characters).
- `resumed_at   TEXT,`: A column `resumed_at`, text (any length of characters).
- `CHECK (status = 'waiting' OR (reviewer_id IS NOT NULL AND length(trim(answer)) > 0))`: A table-level `CHECK` that spans several columns: a row is rejected unless this is true: `status = 'waiting' OR (reviewer_id IS NOT NULL AND length(trim(answer)) > 0)`
- `);`: ends the column list and the statement.

```sql
CREATE INDEX paused_runs_waiting ON paused_runs (created_at) WHERE status = 'waiting';
```

Creates an index named `paused_runs_waiting` on table `paused_runs` over (created_at). An index is a sorted side-structure the database keeps so it can find rows by these columns without reading the whole table. `WHERE status = 'waiting'` makes it a partial index: only rows for which that is true are indexed and (for a unique index) compared.

```sql
-- The audit trail: append-only, and hash-chained. Each row carries the hash of the row before it, so an edit, a removal or
-- a reorder is found by `verify-audit` even when someone with write access gets past the triggers.
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: The audit trail: append-only, and hash-chained. Each row carries the hash of the row before it, so an edit, a removal or a reorder is found by `verify-audit` even when someone with write access gets past the triggers.

```sql
CREATE TABLE audit_log (
    seq      INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id   TEXT NOT NULL,
    step     TEXT NOT NULL,
    actor    TEXT NOT NULL,
    at       TEXT NOT NULL,
    content  TEXT NOT NULL,
    previous TEXT NOT NULL,
    hash     TEXT NOT NULL UNIQUE
);
```

- `CREATE TABLE audit_log (`: creates a table named `audit_log`: a grid in which every row is one record and every column one named kind of value. The columns are listed in the lines below.
- `seq      INTEGER PRIMARY KEY AUTOINCREMENT,`: A column `seq`, a whole number; it is the primary key: the value that identifies a row, unique and never empty; SQLite fills it with the next number automatically (`AUTOINCREMENT` never reuses a number).
- `run_id   TEXT NOT NULL,`: A column `run_id`, text (any length of characters); `NOT NULL` means a value is required.
- `step     TEXT NOT NULL,`: A column `step`, text (any length of characters); `NOT NULL` means a value is required.
- `actor    TEXT NOT NULL,`: A column `actor`, text (any length of characters); `NOT NULL` means a value is required.
- `at       TEXT NOT NULL,`: A column `at`, text (any length of characters); `NOT NULL` means a value is required.
- `content  TEXT NOT NULL,`: A column `content`, text (any length of characters); `NOT NULL` means a value is required.
- `previous TEXT NOT NULL,`: A column `previous`, text (any length of characters); `NOT NULL` means a value is required.
- `hash     TEXT NOT NULL UNIQUE`: A column `hash`, text (any length of characters); `NOT NULL` means a value is required; `UNIQUE`: no two rows may have the same value.
- `);`: ends the column list and the statement.

```sql
CREATE INDEX audit_log_by_run ON audit_log (run_id, seq);
```

Creates an index named `audit_log_by_run` on table `audit_log` over (run_id, seq). An index is a sorted side-structure the database keeps so it can find rows by these columns without reading the whole table.

```sql
CREATE TRIGGER audit_log_no_update BEFORE UPDATE ON audit_log BEGIN SELECT RAISE(ABORT, 'the audit log is append-only'); END;
```

A trigger is code the database runs by itself when an event happens. `audit_log_no_update` runs `BEFORE UPDATE` on `audit_log`; `RAISE(ABORT, 'the audit log is append-only')` cancels the statement with that error message. So no one can update a row through normal SQL.

```sql
CREATE TRIGGER audit_log_no_delete BEFORE DELETE ON audit_log BEGIN SELECT RAISE(ABORT, 'the audit log is append-only'); END;
```

A trigger is code the database runs by itself when an event happens. `audit_log_no_delete` runs `BEFORE DELETE` on `audit_log`; `RAISE(ABORT, 'the audit log is append-only')` cancels the statement with that error message. So no one can delete a row through normal SQL.

### `sql/002_seed.sql`

```sql
-- DML: demo sign-in tokens, stored as SHA-256 hashes. The clear-text demo values are customer: demo-customer-token and
-- reviewer: demo-reviewer-token (fixed demo strings for the local server, not secrets).
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: DML: demo sign-in tokens, stored as SHA-256 hashes. The clear-text demo values are customer: demo-customer-token and reviewer: demo-reviewer-token (fixed demo strings for the local server, not secrets).

```sql
INSERT INTO api_tokens (token_hash, role) VALUES
    ('2159e4031044c95b13fe9b2fb9a1c01841f958d6627dd267a357d2401ad419be', 'customer'),
    ('62af8af38d61c9ea36734d3493487a1cd268c8ad9e3ca6f7ff7a7469b400ccbc', 'reviewer');
```

`INSERT INTO api_tokens (token_hash, role) VALUES ...` adds rows to the table. Each parenthesised line is one row; its values are in the order of the column list. This statement adds 2 row(s). The last row ends with `;`, which ends the statement; the others end with a comma.

### `sql/003_queries.sql`

```sql
-- The queries the lesson's steps run against the durable state. Each statement is preceded by a one-line comment.
-- Runs waiting for a reviewer, oldest first
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: The queries the lesson's steps run against the durable state. Each statement is preceded by a one-line comment. Runs waiting for a reviewer, oldest first

```sql
SELECT run_id, reason, created_at FROM paused_runs WHERE status = 'waiting' ORDER BY created_at;
```

- `SELECT` names the columns or calculations to return: `run_id, reason, created_at`
- `FROM` names the table (or the subquery) to read from: `paused_runs`
- `WHERE` keeps only the rows for which this is true: `status = 'waiting'`
- `ORDER BY` sorts the result (`DESC` means largest first): `created_at`

```sql
-- Paused runs by status and reason
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: Paused runs by status and reason

```sql
SELECT status, reason, COUNT(*) AS runs FROM paused_runs GROUP BY status, reason ORDER BY status, reason;
```

- `SELECT` names the columns or calculations to return: `status, reason, COUNT(*) AS runs`
- `FROM` names the table (or the subquery) to read from: `paused_runs`
- `GROUP BY` makes one output row per distinct combination of these columns, so aggregate functions count or add within each group: `status, reason`
- `ORDER BY` sorts the result (`DESC` means largest first): `status, reason`
- Terms used: `COUNT(*)` counts rows.

```sql
-- Steps recorded per kind
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: Steps recorded per kind

```sql
SELECT step, COUNT(*) AS entries FROM audit_log GROUP BY step ORDER BY entries DESC, step;
```

- `SELECT` names the columns or calculations to return: `step, COUNT(*) AS entries`
- `FROM` names the table (or the subquery) to read from: `audit_log`
- `GROUP BY` makes one output row per distinct combination of these columns, so aggregate functions count or add within each group: `step`
- `ORDER BY` sorts the result (`DESC` means largest first): `entries DESC, step`
- Terms used: `COUNT(*)` counts rows.

```sql
-- The audit trail of the most recently paused run, in chain order
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: The audit trail of the most recently paused run, in chain order

```sql
SELECT seq, step, actor, content FROM audit_log WHERE run_id = (SELECT run_id FROM paused_runs ORDER BY created_at DESC LIMIT 1) ORDER BY seq;
```

- `SELECT` names the columns or calculations to return: `seq, step, actor, content`
- `FROM` names the table (or the subquery) to read from: `audit_log`
- `WHERE` keeps only the rows for which this is true: `run_id = (SELECT run_id FROM paused_runs ORDER BY created_at DESC LIMIT 1)`
- `ORDER BY` sorts the result (`DESC` means largest first): `seq`
- A subquery (a query inside parentheses that produces a value or a table for the outer query): `SELECT run_id FROM paused_runs ORDER BY created_at DESC LIMIT 1`. It means:
  - `SELECT` names the columns or calculations to return: `run_id`
  - `FROM` names the table (or the subquery) to read from: `paused_runs`
  - `ORDER BY` sorts the result (`DESC` means largest first): `created_at DESC`
  - `LIMIT` keeps only the first rows: `1`

```sql
-- Who approved what: reviewer answers with the run they resolved
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: Who approved what: reviewer answers with the run they resolved

```sql
SELECT run_id, reviewer_id, substr(answer, 1, 60) AS answer_start, cited FROM paused_runs WHERE status <> 'waiting' ORDER BY answered_at;
```

- `SELECT` names the columns or calculations to return: `run_id, reviewer_id, substr(answer, 1, 60) AS answer_start, cited`
- `FROM` names the table (or the subquery) to read from: `paused_runs`
- `WHERE` keeps only the rows for which this is true: `status <> 'waiting'`
- `ORDER BY` sorts the result (`DESC` means largest first): `answered_at`

```sql
-- Chain links that do not point at the hash before them (must be empty)
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: Chain links that do not point at the hash before them (must be empty)

```sql
SELECT a.seq FROM audit_log a LEFT JOIN audit_log b ON b.seq = (SELECT MAX(seq) FROM audit_log WHERE seq < a.seq) WHERE a.previous <> COALESCE(b.hash, 'start');
```

- `SELECT` names the columns or calculations to return: `a.seq`
- `FROM` names the table (or the subquery) to read from: `audit_log a`
- `LEFT JOIN` adds the rows of another table and keeps the left rows even when nothing matches: ``
- `JOIN` adds the rows of another table: `audit_log b`
- `ON` is the condition that pairs the rows of the two tables: `b.seq = (SELECT MAX(seq) FROM audit_log WHERE seq < a.seq)`
- `WHERE` keeps only the rows for which this is true: `a.previous <> COALESCE(b.hash, 'start')`
- Terms used: `MAX(x)` is the largest value; `COALESCE(a, b)` gives the first value that is not NULL; `JOIN` combines rows of two tables where the `ON` condition holds.
- A subquery (a query inside parentheses that produces a value or a table for the outer query): `SELECT MAX(seq) FROM audit_log WHERE seq < a.seq`. It means:
  - `SELECT` names the columns or calculations to return: `MAX(seq)`
  - `FROM` names the table (or the subquery) to read from: `audit_log`
  - `WHERE` keeps only the rows for which this is true: `seq < a.seq`
  - Terms used: `MAX(x)` is the largest value.

### `sql/reset.sql`

```sql
-- Empty the paused runs and the audit log (the triggers forbid DELETE, so the tables are dropped and recreated by
-- `make db`; this file is the documented way to start over).
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: Empty the paused runs and the audit log (the triggers forbid DELETE, so the tables are dropped and recreated by `make db`; this file is the documented way to start over).

```sql
DROP TABLE IF EXISTS paused_runs;
```

Removes the table `paused_runs` and its rows; `IF EXISTS` means no error if it is not there.

```sql
DROP TABLE IF EXISTS audit_log;
```

Removes the table `audit_log` and its rows; `IF EXISTS` means no error if it is not there.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
sqlite3 :memory: < sql/001_schema.sql && echo ok
```

Prints `ok`.

```bash
make queries
```

Prints each report query and its rows.

```bash
sqlite3 db/assistant.sqlite 'select seq, step, actor from audit_log order by seq limit 5'
```

Shows the first audit entries.

## Mistakes people make

- Building SQL by joining strings with user input. That allows *SQL injection*. The code passes values as parameters (`?` or `%s`), and the database never treats them as SQL.
- Storing money as floating-point. Amounts here are text or exact decimals and are converted when compared.
- Relying on application code alone to keep data valid. The `CHECK`, `UNIQUE` and foreign-key rules make the database refuse bad rows even if the code has a bug.
- Forgetting an index for a column that is searched often.
- Running `DELETE` without `WHERE` by accident. The only unconditional deletes are in the reset scripts.

## Check yourself

1. What is a primary key?
   *Answer:* The column (or columns) whose value identifies each row; it is unique and never empty.
2. What does a foreign key do?
   *Answer:* Forces a value to exist in another table's column.
3. What does `GROUP BY status` with `COUNT(*)` give?
   *Answer:* One row per distinct status, with the number of rows in each.
4. What is an index for?
   *Answer:* To find rows by some columns quickly without reading the whole table.
5. Why pass values as parameters instead of building SQL text?
   *Answer:* To prevent SQL injection: values are never interpreted as SQL.

## Further reading

- [SQLite SQL language reference](https://www.sqlite.org/lang.html)
- [PostgreSQL 16 SQL commands](https://www.postgresql.org/docs/16/sql-commands.html)
