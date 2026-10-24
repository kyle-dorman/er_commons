# RC — Required-point Coverage

RC is the durable name of the accepted Task15Y diagnostic judge. Task15Y identifies
its development task; RC identifies its role in the evaluation suite. This naming
does not change the accepted `task15y.required_support_coverage.v1` prompt, schema,
model selection or limitations. Historical receipts may still use `coverage`.
See the [accepted handoff](task15y_judge_handoff_v1.md) for exact bindings.

## Standing run requirement

Every new full benchmark evaluation must include RC alongside A/G/S/C and budget
for one judgment per required reference point per eligible candidate answer.
Use the maintained `current_judges` preparation/reporting helper, which supplies
both the decision plan and a separate mandatory RC diagnostic plan. A future
runner must dispatch the diagnostic plan as well as the decision plan and report
diagnostic completion separately. Never silently omit RC to call a run complete.
Diagnostic-only or single-component experiments remain explicitly scoped as such.
Historical frozen runners and publications remain unchanged.

RC follows the existing substantive-answer route. Keep planned rows for invalid,
unavailable and skipped answers with explicit non-decision statuses. A false RC
judgment, missing result or diagnostic execution error must not change the
A/G/S/C decision chain or overall answer pass/fail. Missing results make the
diagnostic report incomplete, not the answer semantically false. Standing inclusion
does not authorize unbudgeted calls, retries, or reruns of historical results.

## Judge boundary

Each request contains the question, exactly one required reference point, and the
candidate supporting-point IDs and text. It returns binary `covered`, supporting
IDs and a brief reason. False requires empty supporting IDs; unresolved mixed
conflicts remain false. Equivalent wording and distributed coverage may count.

Hide the conclusion, separate qualifications, optional context, other reference
points, sources/citations and all other judge verdicts. G continues to judge
grounding independently. RC remains a coverage diagnostic, not an evidence-quality
verdict. Retain its accepted material-omission limitations.

## Comparison with C

Join by source run, question, candidate identity/hash, answer repeat and canonical
required-point ID. Compare RC against **C's status for that same required point**,
not C's overall Boolean: C also considers other required points, optional-point
contradictions and internal contradictions.

| RC | C required-point status | Interpretation |
|---|---|---|
| Covered | Satisfied | Required meaning appears in both answer layers. |
| Covered | Missing | Support contains the meaning; the conclusion omits it. |
| Not covered | Satisfied | Conclusion contains the meaning; support does not cover it. |
| Not covered | Missing | Neither layer provides the required meaning. |
| Covered | Contradicted | Support covers the point but the conclusion contradicts it. |
| Not covered | Contradicted | Support does not cover the point and the conclusion contradicts it. |

These are differences between support and conclusion, not automatically judge
errors. A cross-table is not a judge accuracy score. Keep C contradiction separate
from omission; never infer satisfied from `c_missing == false`. Invalid, missing
and skipped verdicts remain separate from all six cells.

Reports must retain model, split, answer repeat, both statuses/reasons, supporting
witness IDs and their G statuses. Publish all six cells and inspectable difference
rows, with separate development/test summaries and explicit unavailable counts.
No comparison is fed back into any judge or used to repair scores automatically.

The [first real-answer comparison](task15ad_rc_comparison_result.json) uses saved
15AD judgments only; it preserves the sealed run and makes no model calls.
