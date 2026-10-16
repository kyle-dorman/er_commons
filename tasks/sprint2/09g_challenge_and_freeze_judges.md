# Task 09G — Document and freeze the selected judges

Status: **complete; documentation-only freeze**, as directed by Kyle on 2026-10-16.
Parent: [Task 09](09_build_evaluation_and_qualify_judges.md).

## Abstract and goal

Close judge development by binding the already selected A/G/S/C configurations,
completed evaluation evidence and cleaned production implementation into one
reproducible handoff. The full-development comparisons, repeated judgments,
failure analysis and independent cleanup reviews already satisfy the development
work. No model reruns or new prompt cycles are needed for this closeout.

This explicit scope replaces the original provisional challenge plan, including
its extra tuning/stability runs and reserved-development final-check requirement.
Those runs are not performed or claimed. Historical 09A reservations remain intact;
the 30 benchmark test cases remain untouched. The freeze establishes an operational
development configuration with known limitations, not fresh independent validation.

## Inputs

- [C/S selection and evidence](../../docs/specs/task09f_final_result.json).
- [A handoff](../../docs/specs/task09f1_a_inspect_handoff.md) and
  [G handoff](../../docs/specs/task09f1_point_grounding_handoff.md).
- [09F.2 cleanup](09f2_cleanup_production_judges.md), its
  [receipt](../../docs/specs/task09f2_cleanup_result.json), and committed production code.
- [Shared selection](../../configs/judges_selected_v1.json),
  [provider profiles](../../configs/judge_models_v1.json) and
  [production guide](../../docs/judge_maintainer_guide.md).

## Outputs and plan

1. A compact [freeze manifest](../../docs/specs/task09g_judge_freeze_v1.json)
   binding the source commit, dependency lock, selected models/prompts/schemas,
   native generation settings, component data loaders, policies and evidence pointers.
2. Reconciled task/index/sprint documentation with current defaults and explicit
   historical-versus-production boundaries.
3. A Task 10/11/12 handoff: retrieval and target generation come next; Task 12 owns
   whole-answer routing, aligned joins, denominator policy and real-output integration.

## Learning and review

Reuse the completed [native Inspect review](../../docs/specs/task09f_inspect_native.md)
and [cleanup parity review](09f2_cleanup_production_judges.md#outcome).
A documentation freeze pins what was already evaluated; repeating the same
correlated development examples would not create independent validation. Preserve
proposed-label uncertainty and observed failures instead of implying human accuracy
or a measured joint pass rate from separate component panels.

Use a bounded independent review to check that existing evidence supports closeout
and that no deferred integration work is silently claimed as complete.

## Validation and acceptance criteria

- Verify selected prompt/schema/model identities offline and bind exact file hashes.
- Verify the committed source and current runtime agree; keep prior run/result
  artifacts unchanged. No model construction or generation is needed.
- Inspect local links, changed Markdown and `git diff --check`.
- Explicitly state that no fresh reserved-development check or held-out qualification
  occurred, and retain known semantic/label issues and Ollama diagnostic limits.
- Leave Task 12's integration gates explicit. Component completion is sufficient
  for this freeze; it does not establish end-to-end evaluator correctness.

## Non-goals

Model calls, repeated comparisons, prompt or label changes, reserved/test access,
new human labeling, code changes, or implementing combined reporting.

## Outcome

The selected A/G/S/C judges are frozen at production commit `cf9b89d` with
exact implementation, dependency, policy, data-publication and evidence bindings.
The manifest also records reproducible native generation/schema hashes. Existing
component comparisons and cleanup validation supply the evidence; zero additional
model calls, reserved/test reads, prompt changes or runtime edits occurred.

Independent review found no material gaps in this documentation-only closeout.
Offline selected-identity checks, every manifest file binding, local Markdown links
and `git diff --check` passed. Current index, TODO, umbrella and sprint documentation
now reflect the completed four-component design and Task 12 integration boundary.
Task 09 is complete with the stated limitations. Task 10 retrieval is next.
