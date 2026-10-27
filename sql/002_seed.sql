-- DML: demo sign-in tokens, stored as SHA-256 hashes. The clear-text demo values are customer: demo-customer-token and
-- reviewer: demo-reviewer-token (fixed demo strings for the local server, not secrets).
INSERT INTO api_tokens (token_hash, role) VALUES
    ('2159e4031044c95b13fe9b2fb9a1c01841f958d6627dd267a357d2401ad419be', 'customer'),
    ('62af8af38d61c9ea36734d3493487a1cd268c8ad9e3ca6f7ff7a7469b400ccbc', 'reviewer');
