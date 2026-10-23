# Task 15K — Contradiction-first clarification and targeted retest

Status: complete (2026-10-22); targeted limitation persists.

User authorizes the exact numerical-coverage clarification in rules/prompt and
retesting affected cases with both judges. Publish explicit v3 preserving v1/v2
identities and frozen defaults; schema and validator stay identical to v2.
Contradiction checking precedes addressedness. Numerical coverage distinguishes
only Not addressed from Addressed without contradiction; it never prevents
Contradicted. No case-specific examples or further policy changes.

Retest unchanged C001-CT-01 and C001-CD-02 from the sealed v2 dataset with Luna and
Haiku, three epochs/model, concurrency16/model (12 logical judgments). Use the
shared Baylands overview, medium reasoning,4096 output tokens,150-second sample
limit and at most one transport retry; no semantic retries. No new candidates,
labels, other questions, reserved challenges, MiniMax, commits or pushes.

Validate prior identities, new prompt parity, exact subset/label selection and
all eight point judgments. Review every output including reasons and quotes;
report O1 targeted outcome separately from O2 combined/incremental-risk errors.
Run focused regressions and make fix/check; independently review the run.
Seal new artifacts with source hashes and a result pointer. This is a targeted
regression on familiar cases, not full-suite qualification or production promotion.
Close this bounded C001 iteration with remaining limitations recorded; broader
reference rollout and downstream regeneration remain separate Task15 work.

## Outcome

The [v3 contract](../../docs/specs/task15k_structured_conclusion_judge_v3.json)
preserves v1/v2 identities and reuses v2 input/output schemas. Shared context parity
and both providers are tested. make fix/check passed4495tests,1skipped; focused66
passed. Ruff,mypy and diff checks passed.

The [targeted result](../../docs/specs/task15k_contradiction_retest_result.json)
records all12 outputs and independent review. Both models matched6/6 overall
judgments, with no invalid outputs, retries or quote defects. O1 contradiction
was detected5/6 times by Luna and4/6 by Haiku: the new line did not reliably fix
the numerical-coverage mistake. Full-vector agreement was1/6 Luna and4/6 Haiku.
Luna additionally overflagged O2 four times and O4 once by conflating combined
risk with project increment or inferring a nonzero index absent from that point.
Point agreement was42/48 Luna and46/48 Haiku. No post-run prompt or label edits.

Wall22.33s; configured estimated cost$0.01180 total (not a billing receipt).
This closes the authorized targeted pilot iteration with remaining limitations
recorded. It is not a clean point-level validation, full-suite v3 evaluation or
production promotion. Broader Task15 labels and downstream reruns remain pending.
No commit or push.
