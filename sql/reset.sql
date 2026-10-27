-- Empty the paused runs and the audit log (the triggers forbid DELETE, so the tables are dropped and recreated by
-- `make db`; this file is the documented way to start over).
DROP TABLE IF EXISTS paused_runs;
DROP TABLE IF EXISTS audit_log;
