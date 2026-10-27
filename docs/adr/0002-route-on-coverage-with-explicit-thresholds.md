# 2. Route on retrieval coverage with two explicit thresholds and one policy rule

Status: accepted, 2026-10-27

## Context

The assistant must answer, say it is unsure, say nothing was found, or pause for a person, and the pause rate on ordinary questions must stay at an agreed small rate (5%).

## Decision

Coverage is the idf-weighted share of the question's words that the best section contains; a word found nowhere in the help center weighs as much as the rarest known word. Below 0.4 the run pauses; between 0.4 and 0.6 the answer is called thin (`low_confidence`, with an offer to rephrase); above 0.6 it is answered. A separate policy rule pauses a refund asked for more than 30 days after delivery (digits or words: "seventy five days ago") and any legal threat, whatever the coverage. Thresholds live in one dataclass.

## Alternatives considered

- **The model's own confidence:** not available before the first token, and unreliable.
- **A classifier for "needs a person":** another model to evaluate; a plain rule is testable.

## Consequences

- On the 200 questions all 20 should-pause questions pause and none of the 180 others does. The set is synthetic: the ordinary questions quote the help pages, so they score 1.0, and the off-topic ones score below 0.4. The thresholds sit in a wide gap on this set; a real set needs its own calibration.
- Changing a threshold is a one-line change that the 200-question evaluation checks.
