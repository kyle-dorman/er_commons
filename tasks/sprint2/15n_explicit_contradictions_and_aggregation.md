# Task15N — Explicit contradictions and independent aggregation

Status: complete; results ready for discussion (2026-10-22).

## Authorization and question

Following Task15M, the user requests an explicit contradiction representation,
updated synthetic expectations, rules and prompt, and repeated Luna/Haiku judging.
Report both the model's final Boolean and deterministic aggregation of per-point
predictions. Preserve the prior publications and scores. The user accepts the
Haiku queue-growth error but regards C017 renewable-plan equivalence as debatable;
that example must no longer be presented as an unqualified clear mistake in new
reports. The sealed Task15M interpretation remains historical.

The user confirmed candidate/candidate pairs. Inputs retain the original conclusion
and add exact numbered sentence spans A1, A2, ... . Output adds
`contradicting_points`, a list of pairs such as `["A2", "A3"]`. These identify
mutually incompatible statements under the same circumstances, not reference IDs.
Reference-point contradiction statuses remain necessary even when a candidate
contains only one incorrect claim and therefore no internal pair. Empty pair lists
mean no detected pair, not verified truth. Explicit internal contradictions cause
failure even if their subject lies outside R/O coverage; factual support and
relevance otherwise remain outside C's scope.

Keep all 378 existing candidate texts, original Boolean labels and R/O vectors for
a paired comparison; add reviewed expected pair lists. New reports identify C017
as disputed without retroactively altering Task15M scores. Any ambiguous internal
pair expectations must be disclosed and excluded from pair-specific accuracy
rather than forced into a confident gold label.

## Bounded plan

1. Resolve contradiction ID semantics and define a versioned input/output contract.
   Keep references and candidate meaning fixed; any segmentation must preserve text.
2. Implement the explicit contradiction output, rules and prompt under a new
   opt-in version. Preserve all prior versions and shared Baylands overview.
3. Separate structurally valid output from final/point aggregation agreement.
   Compute a deterministic verdict from complete point predictions and the agreed
   contradiction field. Never infer missing rows as satisfied or not addressed.
   Report incomplete coverage, model-final agreement and aggregate agreement
   separately. Retain model-final/aggregate disagreement rather than discarding it.
4. Version the 19-question synthetic suite with reviewed contradiction expectations;
   preserve original labels and texts as provenance, record any deliberate changes.
   Review representation/expectation changes independently before provider calls.
5. Run Luna and Haiku three rounds each, concurrency16/model, medium reasoning.
   Carry forward the original shared $20 cap conservatively: Task15M retained
   $7.46173015, leaving at most $12.53826985 for this continuation. Do not reset the
   ledger or exceed the cap; stop before unaffordable chunks and report partials.
6. Compare model-final and deterministic-aggregate accuracy/agreement, validity,
   point/contradiction detection, repeatability, cost and latency. Review failures
   and seal receipts plus a report without outcome-driven relabeling.

## Validation and limits

Inspect the existing native Inspect adapter and strict structured-C schemas before
changes. Use explicit typed fields and deterministic aggregation with tests for
contradictory optional content, correct-plus-incorrect claims, missing point rows,
and disagreement between model-final and point aggregate. Check provider schema
compatibility, preserved predecessor prompts and shared context. Run make fix/check
and focused tests; independently review changed behavior and expected labels.

No A/G/S changes, reference meaning changes, generation-prompt updates, fresh
benchmark answers, MiniMax, reserved challenges, commits or pushes. This remains a
familiar development comparison. A second computation over returned judgments is
not a second model call and cannot repair missed semantic contradictions.

## Pre-dispatch preparation

V4 is implemented as an opt-in; prior prompts and validators remain unchanged.
The paired synthetic release contains the same378 candidates and1,166 exact
statement spans. Independent review accepted71 definite pairs in65 candidates;
359 candidates are scored for exact pairs,19 remain pair-unscored because of
scope/context or segmentation ambiguity. All378 retain their original overall
and reference-point labels. The [synthetic pointer](../../docs/specs/task15n_structured_synthetic_result.json)
and [contract](../../docs/specs/task15n_structured_conclusion_judge_v4.json) bind
these inputs. The runtime preserves model-final disagreement and computes the
aggregate without another model call. The runner's independent review and12
offline tests pass; its preflight binds the sealed predecessor budget and inputs.
No dispatch occurs until required validation completes.

Required validation completed: make fix/check passed (4,512 tests passed, one
skipped); the initial missing-v4-field context test fixture was corrected and the
full suite rerun. Native dispatch began2026-10-22 after independent runner review,
using structured_judging_pairs_19_20261022_v1_working. No label or prompt changes
are permitted during this run. Retain all output disagreements for analysis.

## Outcome

V4 rules, prompt, schema and reviewed pair labels are implemented. All2,268 calls
completed without transport retries; all243 exception calls were reviewed. The
[result pointer](../../docs/specs/task15n_structured_judging_result.json) selects the
sealed report, native receipts, independent audit and comparison diagnostics.
Original378 candidate texts/questions/R/O points and overall/status labels remain
unchanged;71 definite pairs were added, with19 cases excluded only from exact-pair
scoring. No default judge was promoted.

| Measure | Luna | Haiku |
| --- | ---: | ---: |
| Model-final agreement |1123/1134 (99.03%)|1129/1134 (99.56%)|
| Deterministic aggregate agreement |1123/1134 (99.03%)|1130/1134 (99.65%)|
| Model/aggregate disagreements |0|5|
| Invalid outputs |0|1|
| Pair precision / recall, scored valid outputs |98.28% /95.00%|93.65% /98.33%|

Haiku aggregation repairs three errors and introduces two from wrong point statuses
whose explanations are correct. It cannot repair a contradiction missed by both
the point status and final Boolean. Pair detection changes zero verdicts beyond
point-only aggregation in this run; its potential effect on reference statuses is
not isolated. Both models correctly reject C056-CP-01 in all three rounds with the
A3/A4 pair, where prior Luna missed a contradiction or returned inconsistent output.
C029-CT-02 and C008-OC-02 also receive expected verdicts in all six calls. C017-ME-01
passes all six, but remains interpretation-sensitive per the user's discussion.

The offline prior-run diagnostic computes1119→1121/1134 for Luna by applying the
point rule to two complete but inconsistent v3 outputs. Haiku remains1127/1134;
four incomplete inventories are not repaired. This adds analysis only, preserving
sealed prior scores and native outputs.

New-run configured cost estimate:$1.1749 (Luna$0.4495, Haiku$0.7254), not an invoice.
Wall time772.91seconds. New conservative liability$7.6584 plus previous$7.4617 gives
$15.1201 under the original$20 cap; all reservations reconciled. No additional paid
calls are scheduled. Validation passed4,512 repository tests/one skip,12 offline
runner tests, independent dataset/runner review, full result/budget recomputation,
and exhaustive exception review. No commits/pushes or changes to A/G/S, historical
publications, MiniMax, reserved challenges or generation prompts.

Learning: explicit candidate IDs expose internal conflicts and make them auditable,
but exhaustive pair inventories add scope/segmentation ambiguities. Deterministic
aggregation guarantees execution of the selected logical rule, not correctness of
the model's component statuses. Keep separate final/aggregate accuracy, structural
coverage, pair precision/recall and explanation/status disagreements. Better scores
on these familiar synthetics do not establish held-out judging accuracy.

Next: user discussion of whether to retain v4/pair reporting and which overall
verdict policy to use. Further tuning or generation remains separately gated by
the accepted Task15M plan; no automatic follow-up run.
