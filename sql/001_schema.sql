-- DDL for the assistant's durable state (SQLite). `make db` rebuilds db/assistant.sqlite from these scripts in order.

-- Who may call the API. Only a hash of the bearer token is stored.
CREATE TABLE api_tokens (
    token_hash TEXT PRIMARY KEY,
    role       TEXT NOT NULL CHECK (role IN ('customer', 'reviewer'))
);

-- A run that paused for a human. Everything the resumed run needs is here, so it survives a restart.
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
CREATE INDEX paused_runs_waiting ON paused_runs (created_at) WHERE status = 'waiting';

-- The audit trail: append-only, and hash-chained. Each row carries the hash of the row before it, so an edit, a removal or
-- a reorder is found by `verify-audit` even when someone with write access gets past the triggers.
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
CREATE INDEX audit_log_by_run ON audit_log (run_id, seq);
CREATE TRIGGER audit_log_no_update BEFORE UPDATE ON audit_log BEGIN SELECT RAISE(ABORT, 'the audit log is append-only'); END;
CREATE TRIGGER audit_log_no_delete BEFORE DELETE ON audit_log BEGIN SELECT RAISE(ABORT, 'the audit log is append-only'); END;
