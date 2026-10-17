# Task 11C — Integrate development evaluation

Status: Complete with documented limitations (2026-10-17); refreshed from accepted 11A/11B before implementation.

## Abstract

Connect automatic checks and frozen judges before any prompt-comparison cycle.

## Goal

Produce trustworthy per-question diagnostics from saved Luna answers using existing evaluation components.

## Inputs

Accepted 11B candidates/receipts, 11A panel, [09G freeze](../../docs/specs/task09g_judge_freeze_v1.json), judge guide, Task 10 mappings and [Task 12 reporting contract](12_integrate_evaluation_and_reporting.md).

## Outputs

A reusable evaluation command, exact candidate/point joins, routing specification, offline fixtures and compact per-question reports retaining automatic checks, A/G/S/C decisions, explanations and errors.

## Plan / spec requirement

Use this contract as the brief plan; record concrete interfaces and limits before implementation.

1. Specify generation/evaluation separation and joins keyed by complete candidate hash plus run/repeat and point identities; reject duplicates, orphan judgments, cross-answer joins and missing required coverage.
2. Integrate automatic schema/citation checks and final-citation precision/recall/F1 using canonical mappings and actual delivered evidence. Retrieval recall is not applicable, not perfect recall.
3. Apply frozen A no-answer routing to the conclusion, then check other answer prose before accepting clean abstention. Clean abstentions skip G/S/C; mixed, invalid and ambiguous outcomes remain explicit. Do not trust a target status flag or permit empty support to pass vacuously.
4. Before G, fail required uncited points and unresolved citations automatically, separately from artifact errors. Preserve G's point-owned evidence, S's original reasoning/qualifications and C's frozen question/candidate/reference projection. Do not add conclusion-grounding calls or feed judge verdicts across components.
5. Keep frozen Luna A/G/C and Haiku S configurations. Using Luna as the target does not replace S or retune judges. Preserve known calibration limits and possible correlated target/judge errors.
6. Define per-case availability/failure statuses before comparing prompts. Show automatic checks, per-point G, S/C, abstention and explanations; retain failures when another component is missing. Do not optimize an undeclared aggregate score.
7. Validate fixtures, then evaluate the bounded saved three-question smoke outputs with declared judge call/retry limits. Save all receipts for replay. Task 12 audits and finalizes aggregate denominators and strict joint reporting using this integration.

## Accepted execution contract

Evaluate only the three sealed candidates identified by
[`task11b_final_result.json`](../../docs/specs/task11b_final_result.json): C041,
C017 and C019, attempt 1 / repeat 1. Verify the result pointer, run/attempt seals,
candidate bytes, original delivered payload and Task 10 development mappings.
Read reference conclusions only from the bound development release. Preserve the
six-question panel, all upstream artifacts and every original point identity.

The pure evaluation adapter prepares isolated frozen component packets and
canonical citation diagnostics. The executor calls A first; only a substantive
classification proceeds to G/S/C. An abstaining conclusion requires the separate
empty-other-prose guard. Mixed or unavailable routing remains unresolved with
explicit skipped components. Required G coverage includes every support and
qualification; missing/unresolved citations fail automatically. Optional context
is reported separately, and no conclusion-grounding call is added. Missing,
duplicate, orphan or cross-candidate judgments cannot become complete evaluation.
S receives original premises and C the original conclusion/reference projection.

Before live dispatch, pass invented offline routing/identity/provider fixtures and
independent boundary review. Use native Inspect generation and the frozen 09G
semantic configurations. Record operational overrides of zero retries and one
connection separately; preserve prompts, schemas, medium reasoning and 4,096-token
output cap. No semantic rerolls, target generation, prompt editing or judge tuning.

Prospective ceiling: **36 judge attempts, 36 input-token-count requests, zero
transport retries, zero semantic retries, 4,096 output tokens including reasoning,
32,768 input tokens per request, sequential execution, 30 minutes, USD 12**.
The saved answers require at most **21 judgments**: 7 for C041 (4 G), 9 for C017
(6 G), and 5 for C019 (2 G), including A/S/C once each. Routing may reduce calls,
never required point coverage. Record exact fan-out and reserve before dispatch.

For both providers, reserve USD 0.25/M input (including cache writes) and 0.75/M
output, plus **USD 0.30 per counting request**. The 36-call ceiling reserves
USD 11.205504; the 21-call plan reserves USD 6.536544. Rates conservatively exceed
verified standard short-context prices. Counting cost is an explicit unknown;
the allowance is not a provider billing guarantee and uncertain liability is not
refunded. Disable tools and premium service tiers. Count the exact native request,
including schema and framing, before generation; unsupported counting or omitted
count fields block dispatch. Save request/count/raw response/status/usage receipts
without credentials. Preserve failed/unknown attempts without automatic redispatch.

Produce JSON and readable per-question reports in a fresh external Task 11
namespace, with exact candidate/run/repeat/point, input, policy and implementation
hashes. Replaying sealed artifacts must recompute reports with no provider or target
calls. Keep known semantic failures visible alongside unavailable components.
Task 12 retains final aggregate denominators and strict combined reporting.

## Current commands

```bash
make evaluate-development-smoke \
  EVALUATION_OUTPUT="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_11/11c_evaluation_20261017_v1"
make evaluate-development-smoke \
  EVALUATION_OUTPUT="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_11/11c_evaluation_20261017_v1" \
  EVALUATION_OPTIONS="--replay --allow-replay-source-change"
```

The first command requires a fresh namespace. The second verifies saved inputs,
seals and judgments and recomputes reports without network access. The explicit
source-change flag is needed for this sealed run because a post-run repair changed
only replay serialization comparison. It preserves and reports original execution
and current replay implementation hashes; all input/configuration bindings must
still match. Future runs made with the repaired implementation need only `--replay`.
An existing incomplete namespace cannot be used to redispatch uncertain attempts.

## Research / learning checkpoint

Reviewed 2026-10-17: [Inspect scorers](https://inspect.aisi.org.uk/scorers.html) and
[logs](https://inspect.aisi.org.uk/eval-logs.html) support separating saved outputs
from scoring and retaining per-sample evidence. Reuse installed native APIs and
strict component parsers. [Luna prices](https://developers.openai.com/api/docs/models/gpt-6-luna)
and [Haiku prices](https://platform.claude.com/docs/en/about-claude/pricing) were checked
before setting the conservative accounting reserve. No new dependency is needed. Explain why judge agreement is diagnostic rather than proof and why independent inputs do not guarantee independent errors.

## Validation

Exercise clean/mixed abstention, empty/malformed answers, missing/unresolved citations, missing/duplicate/cross-answer judgments, partial evaluation and candidate repeats. Verify component projections and source-to-report hashes. Run make fix, make check and git diff --check.

## Acceptance criteria

Every attempted smoke candidate has a report or explicit failure; evaluation can be replayed without target generation. The three-question prompt loop can inspect automatic checks and frozen judge results together.

## Review pass

Independent review of routing, join identity, point coverage, leakage and error/status handling.

## Non-goals

No target prompt cycles yet, judge retuning, new labeling pass, test evaluation or final benchmark performance claims.

## Shared boundaries

Follow the [Task 11 umbrella](11_build_and_freeze_target_generation.md). Use only
the 19 development cases; no locked-test or reserved judge-challenge access.
Preserve Task 10 packets and frozen A/G/S/C judge policies. Keep references and
judge feedback outside target requests. Generated runs and reports belong under
`ER_COMMONS_DATA_ROOT`, with exact input/configuration hashes and fresh namespaces.

## Outcome

Integrated saved-candidate automatic checks and frozen A/G/S/C evaluation, then
completed one bounded evaluation of the three sealed 11B candidates. Each has a
JSON and compact readable report with exact candidate/run/repeat/point identities,
canonical citation diagnostics, component explanations, errors and full required
point coverage. The [result pointer](../../docs/specs/task11c_final_result.json)
binds the sealed evaluation and external validation evidence. No provider blocker
occurred; no target generation, prompt iteration or judge tuning ran.

| Case | A route | Required G supported | S | C | Citation precision / recall / F1 |
| --- | --- | --- | --- | --- | --- |
| C041 | Substantive | 4 / 4 | True | True | 1 / 1 / 1 |
| C017 | Substantive | 6 / 6 | True | **False** | 1 / 1 / 1 |
| C019 | Substantive | 2 / 2 | **False** | True | 1 / 1 / 1 |

All 21 judgments are valid and all three reports have complete coverage. C017's
frozen C judge flagged the conclusion's renewable-grid characterization and missing
storage qualifications. C019's frozen S judge flagged an insufficient stated basis
for the comparison to today's levels. These are preserved judge diagnoses, not
new human labels or permission to repair the candidates. Correct citation matches
and supported premises do not imply sufficient reasoning or an adequate conclusion.
No prompt is promoted by this task. Task 12 still owns strict aggregate reporting.

The run used **21 judge calls, 21 exact-input count calls, zero retries and zero
target calls**. All provider responses were HTTP 200, all count values matched
cache-inclusive reported input usage, and no request/output ceiling was exceeded.
Total reported usage was 36,704 input tokens including cache and 5,997 output tokens
including reasoning. Judgment cost estimated using the checked dated provider rates
was **USD 0.00655593**. Counting cost is unknown: USD 6.30 remains reserved, within
the prospective USD 6.536544 liability and USD 12 accounting ceiling. None of these
figures is a provider-enforced billing guarantee.

Thirty-five focused offline fixtures precede live dispatch. Coverage includes
clean/mixed/ambiguous abstention, malformed answers, empty support, missing and
unresolved citations, source-read errors, candidate repeats, missing/duplicate/orphan
judgments, nested table ownership, original S/C inputs, and actual native SDK
serialization/count parity for both providers. Independent reviews resolved routing,
fan-out accounting, replay-orphan, cache-usage and request-header issues. A separate
actual-input audit verified all twelve exact point projections and component prose.
All seventeen frozen judge source/configuration bindings remain unchanged.

The first live-artifact replay exposed a tuple/list serialization mismatch in G
metadata. The saved reports were already JSON-equivalent. A narrow reviewed repair
compares canonical JSON and adds an explicit replay-only source-change flag;
it retains every input/configuration binding, returns original/current implementation
hashes, and cannot authorize dispatch. The original execution source snapshot and
sealed run remain unchanged. Repaired replay recomputed every report with **zero
new calls**. Regression fixtures cover the representation change, default rejection
of changed code, explicit code-only replay and continued input-drift rejection.

`make fix`, `make check` (**4,056 passed, one skipped**) and `git diff --check`
passed; final checks were repeated for the replay repair. The external validation
directory retains initial and final logs, pre-dispatch source, independent review,
input/receipt audits and failed/successful replay logs. Frozen Task 10 files, the
six-question panel and sealed 11B run are unchanged; no locked-test or reserved
challenge content was accessed.

The new code is narrow glue around native Inspect/provider clients, existing strict
judge parsers and canonical metric arithmetic. Separating inputs prevents verdict
leakage but cannot make correlated target/Luna judge errors independent. The models
remain provider aliases and development-selected judges with known calibration
limits. The three cases establish integration, not benchmark performance.

Next: refresh provisional 11D from this outcome before any prompt cycles.
**11D has not begun.** Task 12 later audits the same reports and finalizes aggregate
availability, abstention denominators and strict joint results.


## Maintenance

The [11C.1 cleanup](11c1_cleanup_development_evaluation.md) separates verified
inputs, provider mechanics and run/replay orchestration, with named core processing
steps. It preserves the sealed 11C evidence and exact report behavior. The
[architecture map](../../docs/architecture.md#saved-development-evaluation) identifies
where to edit each responsibility; the Make command above remains current.
