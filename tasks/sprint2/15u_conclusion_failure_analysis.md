# Task15U — Offline conclusion failure and false-accept review

Status: complete; stopping recommendation awaits user decision.

## Goal and boundaries

Explain the four leading conclusion failure reasons in the selected Task15T
results and review passing conclusions for possible false accepts, to inform
whether to stop this iteration. No paid calls, reasoning-level experiment,
code/prompt/reference changes, rescoring, commits or pushes. Preserve sealed
results; exclude MiniMax and reserved challenges. Task16 remains unstarted.

## Inputs and output

Use Task15T's294-slot selection, exact saved C packets and judgments, and the
Task15S failure inventory. Write a fresh evidence-bound review under Task15U's
external artifact directory and a compact result pointer. Conclusions are review
interpretations, not replacement labels.

## Plan and validation

1. Reconcile130 current C rejections with the128 previously reviewed and two
   newly available rejections. Group primary reasons into four non-overlapping
   categories; retain secondary issues and interpretive uncertainty.
2. Audit24 passes selected deterministically, six per model/split, plus eight
   explicitly targeted passes for coverage/contradiction risks. Read candidate,
   question and all reference points before relying on the judge rationale.
3. Independently review bounded failure and positive samples, reconcile disputed
   findings, and report false accepts separately from point-status mistakes that
   do not alter the final verdict.
4. Verify counts and identities, save a compact report with concrete examples,
   limitations and a recommendation about further effort. Run git diff --check.

## Research / learning

Follow the existing C v6 contract and provenance/reporting contracts. Sampling
both accepted and rejected answers avoids conditioning review solely on judge
failures. Keep targeted inspection separate from the stratified sample; neither
small sample nor correlated repeats establishes a precise judge accuracy rate.

## Outcome

The [review result](../../docs/specs/task15u_failure_analysis_result.json) groups
all130 selected C failures:66 missing distinct required content,41 judge/reference
boundary disputes,15 missing why/how explanation and8 conflicts/overstatements.
It reuses128 prior reviews, adds the two retry failures, and records20 newly
inspected failure packets.89 failures contain a concrete mismatch against approved
references;7 look like false rejects and34 remain unresolved.20 of the89 also have
questionable secondary objections. No scores changed.

The positive audit covers32 passes:24 deterministic stratified selections and8
explicit risk selections.28 are supported,1 is a likely false accept (Haiku C029
repeat3 categorical absence claim versus conditional continued monitoring), and3
remain disputed. This small mixed sample is not a judge-accuracy estimate. The
root independently checked representative failure and positive packets and
reconciled the C029 interpretation with the reviewer. Complete source documents
were not independently re-audited for every claim.

Recommendation: freeze this iteration as a documented fixed-context baseline and
move on when the user selects the next task. The review does not support an
immediate full higher-reasoning rerun. Such improvement remains untested, and
reference materiality cannot be resolved by spending alone. Record known judge
limitations and scope ambiguity; do not claim a near-perfect scorer. Task16 is
still unstarted and no paid calls were made. All existing seals remain preserved.

Validation: exact130-failure coverage and32 unique selected passes, packet hashes,
sample strata, category arithmetic and unchanged selected-result seal verified;
independent summary review and git diff --check passed. Learning: count primary
causes without double counting, keep disputed secondary objections, and audit
passes as well as rejections before attributing low scores to judge strictness.
