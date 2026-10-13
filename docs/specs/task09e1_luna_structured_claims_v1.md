# Task 09E.1 — Focused structured-explanation claims test

The user authorizes a small test after the [research review](../llm_judge_learning_notes.md#research-review--2026-10-12)
and clarification that existing judging already operates at claim level. Test
whether making the interpretation explicit helps distinguish acceptable scoped
summaries from actual strengthening. This is a diagnostic pilot, not a new
decomposition architecture or judge qualification.

## Frozen comparison

Reuse the ten exact input payloads and separate diagnostic expectations from the
[scope pilot](task09e1_luna_scope_claims_result.md): four troublesome inputs
(three wordings/two issue families) and six controls. Preserve original question,
claim, linked context and own cited evidence. There are no new benchmark cases,
new labels, edited sources, reserved/test inputs or full-panel calls. Expectations
remain proposed interpretations; pet-policy expectations reflect the user's
accepted ordinary coordinated reading, not independent human calibration.

Baseline is the unchanged combined scope/absence/grammar prompt at medium
reasoning. Candidate appends an instruction requiring three concise headings in
the existing explanation string: Claim interpretation, Evidence interpretation,
Material mismatch. Capture subject/action and material scope qualifiers, compare
the complete relationship to supplied evidence, and identify missing support or
state no mismatch. Mention genuine competing scope readings. Limit the requested
explanation to 200 words, without a step-by-step reasoning trace. Retain the same
whole-claim Boolean and schema; no separately scored subclaims or new output
fields. Both full prompt strings are frozen in the external manifest.

This changes output instructions and includes reminders about faithful
interpretation. Any observed difference belongs to that bundle; it cannot be
attributed solely to formatting. Explanation fidelity requires source review;
another explanation is not proof that the verdict is correct.

Each arm receives five fresh repetitions of every input, 50 calls per arm,
100 total. Run matched ordered inputs with separate arm budgets. Concurrent
execution is not randomized causal identification. Repeatability is an input-level
diagnostic; neither repeated calls nor citation aliases count as independent
semantic cases. The existing ten inputs cover preserved/strengthened modality,
bounded absence, invented enforcement detail, uncited support, universal scope,
pet-policy paraphrases and grading timing. This is an adaptively selected failure
panel, not held-out accuracy measurement.

## Bounds and analysis

Luna Responses only, medium reasoning, qualified evidence-prefix caching, 4,096
output tokens reserved per call, exact counts and native parity checks. Maximum
$1 conservative reservations and 1,800 seconds per arm; $2 and 100 generations
overall. No automatic retries, replay, truncation, replacement calls, other models,
conclusion/gate inference, expansion, promotion, commits or pushes. Code loads
credentials from `.env` without printing them. Fresh external namespace:
`task_09/09e1_20261012_luna_structured_claims_v1/`.

Report all-call and valid-output label agreement, false acceptances/rejections,
trouble/control counts, per-input five-repeat distributions and unanimity, paired
changes, native cache usage and estimated cost. Explanation fields are optional
in the unchanged provider schema; missing headings or requested length overruns
are separate instruction-compliance diagnostics, not automatic semantic failures.
Independently inspect every candidate explanation for faithful interpretation,
retained qualifiers, citation ownership and whether its verdict follows the
stated mismatch. Report ambiguous readings separately from concrete overstatements.

A promising pilot requires all 100 outputs valid, at least three more correct
candidate trouble judgments than baseline, no per-input trouble regression, all
30 candidate controls correct, no reduction in unanimous-correct inputs, and no
source-reviewed concrete false acceptance or interpretation corruption. These
are conservative development criteria, not a significance test or calibrated
guarantee. Regardless of outcome, stop after this pilot; no larger run is authorized
by this contract. Preserve failures and set aside candidates that do not improve.

## Validation and preservation

Use the existing reviewed package stage runner through a fresh pilot-only external
launcher. Bind input, prompt, contract, launcher and implementation identities
before dispatch. Review prompts, source expectations and offline launcher guards
independently before inference; review native results and interpretation fidelity
afterward. Preserve previous completion inventories and verify their bindings.
Scan artifacts and decoded Inspect logs for credential leakage, then publish a
completion inventory and small tracked result pointer.

Run focused regression tests, `make fix`, `make check`, and `git diff --check`.
The current baseline is 4,259 passed, one skipped and three historical Task 06G
failures. No package/default-prompt changes are needed for this pilot.
