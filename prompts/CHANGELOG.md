# Prompt changelog

A change to a prompt goes into a new file (`answer.v2.md`) so recorded streams keyed by the prompt version stop matching
and must be re-recorded.

## answer.v1 (2026-10-27)

First version. Cite every fact with its `[page#section]` marker; the service drops any marker that was not retrieved for
the request and counts it.
