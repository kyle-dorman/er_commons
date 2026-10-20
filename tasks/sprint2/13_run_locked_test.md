# Task 13 — Run the frozen locked-test evaluation

Status: provisional; not active. Refresh from accepted Task 12 before execution.
This document plans the run; it does not open locked content or authorize calls now.

## Abstract and goal

Evaluate both frozen target models, Luna and Haiku, on all 30 locked questions,
with three fresh answers per question/model. Use Task 12's frozen reporting rules
and export its tables/charts without selecting favorable repeats or retuning.

## Inputs and outputs

Inputs: [Task 12](12_integrate_evaluation_and_reporting.md) reporting/readiness
handoff, [11E configuration](../../docs/specs/task11e_frozen_generation_v1.json),
accepted Task 10 input publication and 09G judges. Preserve the accepted prompt,
examples, focused conclusion check, shared overview and neutral input projection.

Outputs: a new sealed run containing all 180 planned target-answer slots, raw
requests/responses, generation and judge receipts, failures, accounting, exact
identities and replayable result tables/charts. Development and test reports stay
separate. Provide a compact handoff to [Task 14](14_selective_failure_review.md).

## Plan and research checkpoint

1. Accept Task 12 readiness and freeze model/prompt/schema/input/judge/reporting
   identities and three-repeat policy before reading test outcomes. Resolve any
   projection/readiness gap explicitly rather than adapting it after results.
2. Record concrete generation, judge, count, retry, time, token and spending caps
   before dispatch. 180 target slots are the planned denominator, not an inherited
   budget authorization. Judge fanout depends on generated points; set conservative
   bounds and stopping policy before calls. Preserve interrupted/uncertain attempts.
3. Validate using offline fixtures and development-only replay. Preserve source
   separation: no references or evaluator feedback enter generation requests.
4. Run complete planned coverage under the fixed policy. Every repeat is a new
   answer, not an independent rejudging of a saved answer. Never replace a semantic
   failure or choose the best output. Account for every unattempted/error slot.
5. Reuse Task 12 reporting for both models, per-component/automatic/joint outcomes,
   at-least-once/every-time results and Luna citation/section/document associations.
   Reuse frozen bins/denominators; do not optimize plots or model choice on test.
6. Seal artifacts, verify no-network replay and document costs and limitations.
   Task 14 handles selective manual diagnosis; Task 15 writes the short report.

Use Task 12's researched reporting definitions. Explain that repeats expose
observed variability but do not provide independent questions or isolate judge
variance from generation variance. The source project remains a limited setting.

## Validation, review and acceptance

Bounded independent review of preflight identities/budgets and final coverage,
receipt joins and reporting. All 180 slots accounted for, each result replayable,
no unreported retries or silent exclusions. Follow repository code checks if code
changes; otherwise verify artifact seals and `git diff --check` for documentation.

## Non-goals

Prompt or judge tuning, reference correction based on test success, new models,
search-agent evaluation, broad human annotation, methods/results writeup, commit
or push. Changes motivated by locked outcomes require a new future condition and
cannot retroactively improve this run's frozen results.

## Outcome

Planning only. No locked content inspected and no calls made. Task 12 is next;
Task 13 activation follows its accepted readiness decision.
