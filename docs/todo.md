# Project TODO

## Current state

**No task is active.** Tasks 02–12 and the
[12A reporting maintenance pass](../tasks/sprint2/12a_reporting_code_quality.md)
are complete within their recorded scopes and limitations. Task 11 is fully
closed. The [index](index.md) routes accepted inputs and historical outcomes.

The current reporting pipeline and final development gallery are ready. All 19
development questions are reported together; the next 30-question test report
will be the main model-results evidence. Synthetic judge accuracy stays separate.

## Next: Task 13, provisional

[Task 13 — Locked evaluation](../tasks/sprint2/13_run_locked_test.md) requires
separate activation before locked inputs or calls are permitted.

Before execution:

- Bind the accepted 11E model/prompt/input configuration, 09G judges and current
  Task 12 reporting definitions and implementation.
- Specify generation/judge/counting/retry, time, token and spending caps, plus
  interruption and stopping rules. The 180 planned slots are not a call budget.
- Implement and validate a locked-only adapter using offline fixtures and
  development replay. Do not repurpose the development-only reporting loader.
- Complete the bounded preflight review before dispatch.

Run both frozen models × 30 test questions × three fresh answers. Account for
all slots, preserve failures and exact identities, and publish a separate sealed
run plus a clean figures/tables folder. No prompt/judge tuning or best-repeat
selection based on test outcomes.

## Following queue

| Task | Status and finish line |
| --- | --- |
| [13 — Locked evaluation](../tasks/sprint2/13_run_locked_test.md) | Provisional; 180 planned slots, sealed artifacts and offline replay. |
| [14 — Selective failure review](../tasks/sprint2/14_selective_failure_review.md) | Provisional, after 13; bounded examples and evaluator disagreements. |
| [15 — Methods/results](../tasks/sprint2/15_write_methods_and_results.md) | Provisional; short report covering dataset, methods, test results and limitations. |

Agentic search and new model/prompt conditions require separately scoped work.
Held-out results must not be used to retroactively tune this frozen condition.
For reporting edits or future comparisons, use the
[maintainer guide](reporting_maintainer_guide.md).
