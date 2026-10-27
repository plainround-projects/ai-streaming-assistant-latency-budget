-- The queries the lesson's steps run against the durable state. Each statement is preceded by a one-line comment.
-- Runs waiting for a reviewer, oldest first
SELECT run_id, reason, created_at FROM paused_runs WHERE status = 'waiting' ORDER BY created_at;
-- Paused runs by status and reason
SELECT status, reason, COUNT(*) AS runs FROM paused_runs GROUP BY status, reason ORDER BY status, reason;
-- Steps recorded per kind
SELECT step, COUNT(*) AS entries FROM audit_log GROUP BY step ORDER BY entries DESC, step;
-- The audit trail of the most recently paused run, in chain order
SELECT seq, step, actor, content FROM audit_log WHERE run_id = (SELECT run_id FROM paused_runs ORDER BY created_at DESC LIMIT 1) ORDER BY seq;
-- Who approved what: reviewer answers with the run they resolved
SELECT run_id, reviewer_id, substr(answer, 1, 60) AS answer_start, cited FROM paused_runs WHERE status <> 'waiting' ORDER BY answered_at;
-- Chain links that do not point at the hash before them (must be empty)
SELECT a.seq FROM audit_log a LEFT JOIN audit_log b ON b.seq = (SELECT MAX(seq) FROM audit_log WHERE seq < a.seq) WHERE a.previous <> COALESCE(b.hash, 'start');
