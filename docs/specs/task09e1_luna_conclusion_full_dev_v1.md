# Full-development conclusion comparison

The user explicitly authorizes both unchanged conclusion prompt arms on the full
development set and requests class-imbalance-aware reporting. This supersedes
previous no-full-19 boundaries for this experiment only. Prior experiments and
their original criteria remain sealed. No test/reserved payloads, later tasks,
other models, commits or pushes.

## Scope and inputs

Use all 430 comparison-eligible answers from the 19-case 09A.3 development
publication; retain twelve exclusions and 38 clean abstentions. Verify the
09A.3 pointer before artifact reads. Build a fresh full-development panel with
an explicit opt-in maintained helper; default Dev6 behavior stays unchanged.
The trusted panel publisher may handle restricted labels for packaging, but
model inputs and experiment preparation must not inspect proposed verdicts.
Evaluation loads expectations only after both conclusion summaries exist.

Preserve the 323 original simple-baseline claim judgments on the Dev6 answers.
Generate only missing original claims on the other thirteen cases, once, using
the exact selected simple claims prompt and Luna condition from the sealed
Dev6 claims experiment. Freeze those actual decisions before either conclusion
arm. No new abstention-gate or original Dev6 claim calls; no label substitution.
Verify full input parity for all prior136 answers and frozen323 point payloads.

Run one fresh baseline and one fresh clarified conclusion pass over all430
answers. Reuse the exact prompt strings from the sealed Dev6 evidence-boundary
comparison, the same full evidence, visible frozen predictions, response schema,
validator and disagreement/0–2/N/A aggregation. Both arms receive exactly the
same frozen original claim decisions. No further prompt tuning during this run.

## Execution and stops

Only gpt-6-luna Responses generation, medium reasoning,4096 output cap and the
qualified evidence-prefix cache layout. Exact request counting, native usage
parity and credential loading inside Python remain required. Never read base.env.
Use a new external namespace:
`task_09/09e1_20261012_luna_conclusion_full_dev_v1/`.

Freeze all input/script/contract/package identities before paid dispatch. Freeze
a separate conclusion-input manifest after the missing claims finish. The answer-only inventory contains1056 points:323 reused and733 new. Verify
those counts against built packets and bind them before dispatch; cap
at733 claim calls/$12, then430 calls/$7 per conclusion arm, total ceiling1593
calls/$26. Use at mostfour concurrent samples per arm and3600seconds per phase.
These are conservative caps, not expected spend; only actually missing claims
may run. On error stop new scheduling, preserve inflight/partial artifacts, no
retry/replacement or truncation. Root alone dispatches after independent review.

## Metrics fixed before dispatch

For binary conclusion support and claim support/reviews, lead with class-macro
F1 over supported and unsupported, plus per-class precision/recall/F1 and label
counts, confusion matrices, balanced accuracy and ordinary accuracy. Report
supported-class F1 explicitly; it alone ignores true negatives. Class-macro F1
is distinct from equal-weight question averages; report both with clear names.
Primary coverage-aware macro-F1 includes every eligible gold-supported/unsupported
item: missing, invalid or null predictions use an explicit unscored column and
count as false negatives for the true class, never as unsupported predictions.
Also report standard conditional F1 on concrete predictions with coverage. Gold
clean-abstention/null cases are excluded and assessed separately. Fixed-label
macro includes both classes with zero_division=0 and absent-class/undefined flags;
balanced accuracy averages recall over gold-present classes, naming them. Empty
populations return null, not zero. These policies apply to pooled and per-case
reports. See official [precision/recall/F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html),
[balanced accuracy](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.balanced_accuracy_score.html),
and [confusion matrix](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html)
definitions; matrices use true rows and predicted columns.

Report full19, priorDev6, added13, outsideC041 and individual question results.
For final numeric0/1/2 scores report standard class-macroF1 among valid numeric
outputs and the parallel coverage-aware all-numeric-eligible version with
unscored outcomes counted as false negatives. Use fixed labels0/1/2 and the same
zero-division policy; report class counts, confusion, numeric coverage and
correct/all-numeric-eligible counts. Report correct N/A and all-answer final-state agreement separately.
Never let conditional F1 conceal unresolved disagreement or missing output.
Include original-vs-review corrections/reversals, paired conclusion changes,
quotation diagnostics, native usage/cache/cost, latency and duplicate inputs.
One pass provides no repeated-call stability estimate. Proposed synthetic labels
remain uncalibrated development targets, not established human ground truth.

Source-review changes and false acceptances with bounded independent agents:
review all changed conclusions and changed claim-review decisions, plus stable
correct controls spread across cases; group exact duplicate assertions explicitly
without concealing differences in cited evidence. Summarize remaining errors,
ambiguous interpretations and matching-label/faulty-rationale cases separately.
A higher macro-F1 is not automatic judge qualification or default promotion.
Stop after this comparison and reporting.

## Validation and learning

Use official scikit-learn metric definitions and local package-backed helpers;
prefer maintained metrics when already available, otherwise narrow standard-
library count arithmetic with independently checked fixtures. Do not add a
runtime dependency merely for elementary counts. Record the choice and source.
Focused regression tests must prove default panel compatibility, full population
boundaries, label separation, missing/null semantics and class imbalance metrics.
Run make fix, make check and git diff --check; baseline4271passed/1skipped/three
historical Task06G failures. Independently review preparation and native receipts.
Preserve prior seals, scan raw/decoded logs for credentials, publish completion
last and a small tracked result pointer. No implicit default or label changes.
