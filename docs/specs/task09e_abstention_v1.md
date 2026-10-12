# Task 09E — Answer-only abstention gate

Status: implemented; Dev3 abstention-only check complete, October 11, 2026. User review pending.

## Purpose and boundary

The prior conclusion checker misclassified clean abstention by evaluating the
question premise. A separate first call asks only whether the answer makes any
substantive assertions. It sees every nonempty original answer point ID/text,
including qualifications and optional context, without question, evidence,
citations, status flag, references, expected labels or automatic metrics.
Original text is retained; no lexical shortcut determines the result.

The prompt returns `clean_abstention`, `substantive`, or `ambiguous`, plus a concise
explanation. An inability statement with factual additions is substantive. It does
not assess truth, relevance, completeness or evidence support. Ambiguity is not a
clean abstention. Invalid outputs remain evaluation failures.

## Routing and interfaces

With the optional staged gate enabled, clean abstention returns N/A and skips point
and conclusion calls. Ambiguity returns `unresolved_abstention`, score null; invalid
output also skips downstream calls. Substantive answers continue through the
[point/conclusion pipeline](task09e_staged_grounding_v1.md).

`grounding_run --pipeline abstention` runs only this classifier;
`--pipeline staged_with_abstention` enables the full gated pipeline. Existing
single and staged defaults remain preserved for reproducibility. The maintained
`make evaluate-abstention-panel` target accepts the existing explicit panel,
settings, exact-counter and output arguments. No new dependencies are introduced.

## Authorized experiment and validation

Run exactly the unchanged twelve saved Dev3 answers (C041/C037/C014), using the
existing Qwen3.5 0.8B F16, 49,152 context and 3,000 output allowance. Inspect owns
execution, logs, sample records and aggregation. Reuse shared native transport and
exact local model-specific request counting; every request is checked before
inference. Missing local assets block execution without downloads. One transient
retry is permitted; no semantic retries. A detected counter mismatch halts dispatch.
No live invented, point or conclusion calls in this experiment. No Dev6, 9B,
full-development, reserved/test evaluation, target generation, commits or pushes.

Save a fresh external namespace, bound prompt/schema/source identities, exact
requests/preflights, raw outputs, parsed classifications and Inspect summaries.
Whole-answer synthetic N/A expectations provide diagnostic comparisons only;
non-N/A proposals are not independently adjudicated abstention labels. Review
actual answer text, keep labels outside requests, and do not call agreement accuracy.

Offline tests cover all answer containers, input isolation, mixed assertions,
strict output validation, every route, counter guards and Inspect aggregation.
Run focused tests, make fix, make check and git diff --check. Independent review
checks the boundary and results. Stop after the classifier-only panel for review;
the full gated pipeline is tested offline but not run live here.

## Observed checkpoint

All twelve responses validated: one clean abstention, eleven substantive, zero
ambiguous, zero failures/retries/output limits. The clean example is the unchanged
C037 R01 answer, “I cannot determine the answer from the supplied evidence.”
It previously received grounding 0; the isolated classifier now recognizes it as
clean abstention. C014 O01 remains substantive despite containing only a conclusion.
All twelve exact preflight counts matched native input usage. Inspect measured
6,748 input and 1,444 output tokens over 36.26 seconds of sample execution.

The twelve classifications agree with the synthetic N/A/non-N/A proposals; this
is a diagnostic comparison on a tiny panel with only one clean example, not
calibrated accuracy. No ambiguous or mixed-abstention live examples were added.
Full gate routing is covered offline; this run produced classifications only,
without new grounding scores or point/conclusion calls. Source-linked grounding
errors from the preceding experiment remain unresolved.
