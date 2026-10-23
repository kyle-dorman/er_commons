# Task15P — Paragraph conclusions and internal-contradiction reasons

Status: complete; ready for user discussion (2026-10-22).

## Abstract and accepted decisions

The user requests replacing candidate A IDs and `contradicting_points` pairs with
ordinary paragraph input and `internal_contradictions`, an always-present list of
objects containing a nonempty `reason` (empty list when none). Only reference R/O
points have IDs. Contradiction reasons support judgment; they are not separately
matched, graded, or semantically reviewed. Evaluate overall pass/fail against
expected labels and diagnose final-versus-status/list inconsistency. A nonempty
list requires failure; empty does not imply pass. Reference contradictions and
internal contradictions may overlap. No exhaustive pair inventory is required.

## Goal, inputs and outputs

Update active rules, prompt and validation; preserve frozen previous versions for
reproducibility rather than rewriting historical runs. Use Task15O's reviewed
failures and existing development references to author 10–20 new paragraph cases,
then run Luna and Haiku three rounds each, concurrency16/model, medium reasoning.
Output fresh sealed synthetics, judge results, comparison of model-final versus
computed verdict, and review of overall errors/invalidity. Do not score reasons.
The case set targets clear prior misses rather than disputed reference meanings.

## Plan and research checkpoint

1. Implement opt-in v6 paragraph schema and reason-list output, removing candidate
   segmentation and pair validation from the current path. Retain v1–v5 as history.
2. Update current rule/maintainer/perturbation docs. Consult existing maintained
   Inspect/Pydantic integration and prior validator tests; use the same native
   adapter and shared Baylands overview. No new framework or dependency.
3. Author and independently review 16 new contradiction cases, using only existing
   development source-bound references. Freeze candidate text and overall labels
   before calls. Include isolated and combined defects, both claim orders, and
   strong same-scenario conflicts; no label perturbation or reserved challenges.
4. Validate runtime and budget gates, then execute96 calls. Carry forward the
   cumulative conservative liability$16.613221175 under original$20 cap; available
   liability$3.386778825. Reserve before dispatch, no semantic retries.
5. Report model-final and computed verdict accuracy, structural validity and
   consistency flags, cost/latency and repeatability. Reasons are unscored working
   explanations. Review overall failures and consistency issues, not reason quality.

## Validation and review

Independent runtime and dataset review; meaningful tests for plain paragraph
input, output shapes, nonempty-list/pass consistency, deterministic aggregation,
reference inventory and native/core parity. Keep structural validity separate from
logical consistency so both verdicts remain evaluable; flag inconsistencies without
semantic retry. Run make fix/check and offline execution/accounting tests. Seal
publications completion-last and preserve all planned slots.

## Boundaries and learning

This is targeted familiar-development sensitivity testing, not a full-suite or
positive-case specificity claim. Internally contradictory additions outside R/O
can now fail through the reason list; factual support/relevance are still separate.
No A/G/S change, label-reference edit, new target generation, MiniMax, reserved
challenge access, default production promotion, commits or pushes.

## Outcome

Implemented paragraph-input v6 with `internal_contradictions` reason objects in
rules, prompt, schema and consistency diagnostics. Removed candidate IDs and pair
checks from this current path; frozen historical versions remain available.
[Transformation v4](../../docs/specs/task15p_conclusion_transformations_v4.md) replaces
pair expectations for new data. The [contract](../../docs/specs/task15p_structured_conclusion_judge_v6.json)
binds prompt and schemas; the [dataset](../../docs/specs/task15p_structured_synthetic_result.json)
contains 16 new independently reviewed paragraphs across six development questions.

All 96 calls completed: Luna and Haiku each had 48/48 valid and correct overall
judgments, with 48/48 correct computed verdicts, no aggregation mismatch, and no
nonempty-list/pass inconsistency. Every list was nonempty; this is descriptive,
not semantic verification of its reasons. No reason explanations were graded or
semantically reviewed, no point-vector accuracy was computed, and no overall or
structural exceptions needed review. Labels remained fixed.

The [sealed result](../../docs/specs/task15p_structured_judging_result.json) contains
the report, raw receipts, metrics and audits. Runtime about 62 seconds; configured
cost estimate $0.07135313. New conservative liability $0.3952906, cumulative
$17.008511775 of $20, remaining $2.991488225. No retries. make fix/check passed
4527 tests with one skipped, ten offline execution tests passed, and independent
runtime, dataset, runner and result audits passed. Final inventory and diff checks
passed. No production-default promotion, commits or pushes.

The targeted negative examples support this simpler representation for these
failure mechanisms. They do not measure compatible-answer false rejection,
completeness of defect identification, or improvement on a shared prior test set.
Further testing or production promotion awaits user direction.
