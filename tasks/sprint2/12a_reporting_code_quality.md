# Task 12A — Reporting maintenance

Status: Complete. User-authorized offline quality pass after Task 12.

## Goal and boundary

Keep reporting simple to edit and reuse for new model comparisons. Preserve the
accepted Task 12 score definitions, three-repeat protocol, exact identities and
sealed artifacts. No inference, counting calls, locked/reserved-content access,
new judge history, commits or pushes.

## Inputs and outputs

Use Task 12's current v1–v4 reporting definitions and maintained reporting modules.
Deliver clearer pure table preparation versus source loading and publication,
explicit model selection, arbitrary comparison-model presentation, regression
coverage for publication and future model labels, and a compact maintainer guide.

## Plan and learning checkpoint

1. Independently inspect reducers, charts and publication boundaries; fix concrete
   reuse hazards before stylistic changes.
2. Keep historical Task 11E/09G adapters explicit. Generic presentation must not
   silently reopen project-specific history. Use keyword parameters for the few
   actual presentation choices, not a new configuration framework.
3. Reuse standard-library JSON/path/tempfile and installed Matplotlib interfaces.
   Inspect local library signatures/docs and existing project publication patterns
   offline; add no dependency. Pure transformations permit source-free regression
   tests, while staged publication prevents partial user-facing results.
4. Verify current metrics against saved sealed tables and use invented fixtures
   for new models, missing rows and publication failures.

## Validation and acceptance

Bounded independent review, appropriate offline tests, `make fix`, `make check`,
`git diff --check`; replay the current report into a fresh external namespace.
No changed current score/count tables without an explained correction. Document
where to edit metrics, charts, historical adapters and output selection. Keep
Task 13 provisional and three repeats explicit; new execution adapters remain
outside this cleanup.

## Outcome

The quality pass separates pure response-unit counting and presentation preparation
from the historical input adapters and saved-report publication. Export now uses
its supplied sealed judge tables by default; loading legacy 09G records requires
an explicit `--judge-repo`. API and CLI callers both receive persisted provenance,
with fresh-destination checks and cleanup on caught publication failure.

Charts use every supplied comparison-model label and an explicit primary model,
validate consistent model rosters and contain Matplotlib style settings locally.
The three-repeat contract and existing filenames remain deliberate compatibility
boundaries. Reducers now avoid duplicate aggregate rows for already-pooled inputs,
reject conflicting nested identities and distinguish actual invalid IDs from
ambiguous/unavailable references. These corrections do not change the complete
accepted development results. Pure preparation copies its source and preserves
normalized counts even without raw citation attempts.

The [maintainer guide](../../docs/reporting_maintainer_guide.md) maps edit points,
comparison-arm naming, expected adapter boundaries and replay commands. Standard
library publication and Matplotlib APIs were inspected locally; no package was
added. Separate functions/modules address real callers without a workflow engine
or arbitrary repeat-configuration framework. Historical adapters remain specific
rather than pretending to be generic importers for unknown future run schemas.

Independent review found no blocking issues. An independent full offline replay
of 114 saved answers reproduced accepted model/point/question/repeat/citation
results. A fresh presentation reproduced all eleven current CSV files byte for
byte; the revised model chart was visually checked. Original publications and
source artifacts remain sealed. Synthetic fixtures cover new model labels,
missing model rosters, primary-model selection, duplicate groups, identity
conflicts, seal tampering, normalized counts, output conflicts and failures.

Validation: `make fix`, `make check` (4,255 passed, one skipped; 89 existing
dependency warnings), and `git diff --check` passed. Current review provenance
and its adjacent validation log record the refresh. No calls, locked-content
access, commits or pushes occurred. Task 13 remains provisional.
