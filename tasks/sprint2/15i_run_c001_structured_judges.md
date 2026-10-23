# Task 15I — C001 structured judge pilot

Status: complete (2026-10-22), with reviewed point-level and validity diagnostics.

## Goal and authorization

Run the sealed Task15H 42-candidate dataset with Luna and Haiku, three epochs each,
16 connections per model, as explicitly requested. Compare overall decisions,
all eight point statuses and repeat stability. Review every disagreement/invalid.

## Inputs and execution

Use task15h_c001_structured_synthetic_result.json and explicit Task15G structured
prompt/schema with the verified Baylands overview. Freeze exact inputs/settings
before dispatch. Native Inspect owns concurrency, transport and logs. 252 logical
judgments; at most one native transport retry per call (504 attempts maximum),
4096 output tokens, 150-second sample limit, existing medium reasoning settings.
No semantic retries, prompt edits or label changes. Preserve invalids as outcomes.
Use exclusive dispatch claim; do not rerun completed work to improve results.

## Artifacts and validation

Fresh external run directory: preflight/input identities, immutable raw logs,
normalized results, overall/per-point/repeat metrics, disagreement review and seal.
Check exact 2-model × 42-candidate × 3-epoch coverage, full prompt/schema equality,
point-status vectors and quote diagnostics. Report invalids separately, raw
agreement plus majority/any/all-three agreement, dated configured-price cost
estimate and observed latency. Expectations are agent-reviewed, not human gold;
all data are one familiar question, not held-out qualification.

## Review and boundaries

Independently inspect dispatch settings and audit metrics/review findings. No
other questions, reserved challenges, MiniMax, fresh target answers, reference
edits, production promotion, commits or pushes. Next decisions follow results.

## Outcome

The [result pointer](../../docs/specs/task15i_c001_structured_judging_result.json)
selects all252 judgments, raw logs, exact settings, full metrics, per-model
exception reviews, a review browser and independent metric audit. Luna produced
126/126 valid outputs and Haiku123/126; all valid overall decisions agree with
proposed expectations. All three invalid raw Booleans also agree, but remain
invalid. Majority-of-three overall agreement is42/42 for both. No valid Boolean
flips occurred.

Full-vector agreement is103/126 Luna and115/123 valid Haiku (115/126 all calls).
Valid point agreement is972/1008 Luna and975/984 Haiku. Most Luna mismatches
concern an underspecified optional-addressedness boundary, not established factual
errors. Reviews cover all35 exception calls across20 candidates, including
optional overlap, combined-versus-incremental risk, contradiction attribution,
three invalid Haiku outputs and one quote-only defect. The external review retains
exact reasons and separates policy ambiguity from clear errors.

Both models used three epochs and16 connections each. Wall time59.70s; dated
configured-price estimates $0.04534 Luna and$0.10128 Haiku, total$0.14662, not a
billing receipt. Independent audit verified the source seal, exact identities,
raw-log metrics, costs and timing. Artifact checks and git diff --check passed;
no package code changed. No prompt/label changes or semantic retries occurred.

Next discuss optional addressedness and whether missing-point judgments may quote
partial content before expanding this pilot. No new version or production judge
selection is implied by this outcome.
