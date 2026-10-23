# Task 15J — Refine and repeat the C001 structured pilot

Status: complete (2026-10-22), with remaining point-level issues for discussion.

## Authorization and scope

The user authorized rules, prompt and synthetic-guidance updates, revised/new
C001 candidates, and a repeat of the two-model evaluation. Use Luna and Haiku,
three epochs each, concurrency 16 per model. Preserve all prior artifacts,
reference/question text, frozen defaults and reserved challenges. No MiniMax,
commits or pushes.

## Accepted corrections

Numerical optional details are addressed only by relevant numerical values;
general below-threshold statements do not address modeled values. Partial
numerical coverage remains permissible. Qualifications are addressed by their
limitation, not merely contextual restatements of the claim being qualified.
C001-OC-02 therefore does not address O4: the prior synthetic expectation was
wrong, not the models. Explicit contradictions always take precedence.

Missing/not-addressed judgments may quote relevant incomplete content. Preserve
exact-quote diagnostics, nonempty quotes for other statuses, exact point coverage
and Boolean consistency. Ask judges to reconcile each status with its explanation
before deriving the overall result. CP-02's R1 missing status was wrong; EX-02's
R2 missing status was correct. Relaxed validation does not repair semantic errors.

## Plan and validation

1. Version the prompt/validator while retaining the v1 contract and defaults.
2. Clarify maintained C rules and publish transformation guidance v2.
3. Review all old candidate vectors under the accepted boundaries; add bounded
   controls where coverage is absent. Preserve reference bytes and lineage.
4. Independently review expectations before sealing and dispatch. Pin exact
   prompt/schema/context and dataset identities. No adaptive relabeling in-run.
5. Run native Inspect with three epochs per model, 16 connections per model,
   medium reasoning, 4096 output tokens, existing 150-second sample limit and
   at most one transport retry. No semantic retries.
6. Review every mismatch/invalid/quote diagnostic; report overall and point-level
   agreement, repeat stability, cost and latency. Distinguish label ambiguity
   from judge error. Seal new artifacts and update routing.

Use existing Pydantic and Inspect boundaries. Mechanical validation checks shape
and aggregation, not semantic truth. This familiar single-question development
suite with agent-reviewed expectations is not held-out qualification or human gold.
Run focused regressions and make fix/check for package changes; inspect docs diff.

## Implementation and preflight

The explicit v2 contract preserves exact v1 prompt/schema identities and frozen
runtime defaults. Focused tests cover both versions, both providers, shared real
and synthetic context, and quote-policy distinctions. make fix/check passed:
4,486 tests passed, one skipped; Ruff and mypy passed. Existing Inspect warnings
remain. The independent runner review verified the explicit v2 selection,
three epochs, concurrency16 per model and no semantic repair retries.

The independently reviewed v2 dataset contains 52 candidates (27 expected pass,
25 fail): all42 original candidate texts plus10 new controls. Only OC02/O4 changed
among inherited expectations. All416 expected statuses passed independent review
before dispatch. The exact reference bytes are unchanged. Dataset and run pointers
are separate; prior scores are historical and must not be silently recomputed.

## Outcome

Published the [v2 contract](../../docs/specs/task15j_structured_conclusion_judge_v2.json),
[transformations](../../docs/specs/task15j_conclusion_transformations_v2.md),
[synthetic set](../../docs/specs/task15j_c001_structured_synthetic_result.json), and
[run result](../../docs/specs/task15j_c001_structured_judging_result.json).
Both models produced156/156 valid outputs and156/156 matching overall decisions.
Each matched1242/1248 point statuses and150/156 full vectors. All52 candidates
matched overall in every round; full-vector all-three agreement was49/52 Luna
and48/52 Haiku. No semantic/transport retries were used.

All14 exception calls were reviewed:12 point-status disagreements and two quote-only
calls. Remaining issues are contextual buildout text counted as the construction
qualification (Luna2,Haiku1); combined versus project-increment risk confusion
(Luna4,Haiku1); missed O1 contradiction without numerical coverage (Haiku3); and
one defensible residential-only/worker-exclusion scope interpretation (Haiku1).
Quote diagnostics caught one typo and capitalization-only differences. The prior
CP02/CT05/EX02 problems did not recur in this run. EX02's incomplete-content quotes
are now valid. Original OC02 is fully correct under the user's corrected label;
new OC14 shows qualification addressedness remains unstable with explicit context.

Configured-price estimates: Luna$0.06343, Haiku$0.13680, total$0.20023, not a billing
receipt. Wall98.71s; median model-output time5.56s and5.73s respectively. Independent
metric/identity audit and per-model exception reviews are saved with raw logs.
Prior results remain unchanged; suite size and one expectation changed, so raw
before/after rates do not isolate a prompt effect. No post-run labels/prompt edits,
production promotion, commits or pushes. Next discuss remaining boundaries before
broader label rollout and downstream regeneration. Task16 remains provisional.
