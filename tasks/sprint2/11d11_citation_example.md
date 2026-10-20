# Task 11D.11 — Worked example for complete claim-local citations

Status: Complete with limitations (2026-10-19); no revision promoted.

## Goal and design

The user sets aside the qualification rewrite and authorizes testing a revised
citation example. Start from exact neutral-input V6b (11D.9 baseline), replacing
only Example 2. The new unrelated library example demonstrates a two-passage
identity-to-policy link, point-local citations, splitting a compound claim, and
an unsupported relationship that citing both passages cannot establish. Preserve
all other field instructions and examples. Do not add the separate citation-check
sentence, qualification rewrite, project summary or conclusion check.

Compare the fresh citation_example arm with sealed 11D.9 baseline and citation
arms on C019, C014 and C056 only. Both models, two repeats: 12 fresh answers plus
24 saved controls. No paid control reruns or matched-seed claim. Luna medium and
Haiku adaptive medium settings, neutral question/locator/reference publication,
passage bodies, target schema and frozen 09G A/G/C Luna and S Haiku judges remain
unchanged. Reference answers and judge feedback never enter generation requests.

Prompt: docs/prompts/task11d11_citation_example.md. Fresh artifact namespace:
pipelines/brisbane_baylands/task_11/validation_11d11_20261019. Retain exact run,
candidate, repeat and point identities, complete coverage, all native requests,
raw responses, receipts, failures, accounting uncertainty and replay reports.
Sealed 11B/11C/11D.9/11D.10 and Task 10 artifacts remain unchanged.

## Hypothesis and learning checkpoint

The saved citation-check review found one correct two-source identity/scope link
in Haiku but a missing link in its other repeat; groundwater mixed missing
citations with unsupported causal inferences. More citations alone cannot repair
an unsupported relationship or lost scope. An explicit worked example should
improve both behaviors more reliably than another general checking sentence.
The example replaces V6b's original machine-comparison illustration, so any change
also reflects that replacement; it is not an isolated test of extra prompt length.

This is a bounded follow-up to the accepted local 11D.9 experiment and its offline
citation review. The 09G maintainer guide and 11D.9 field-specific evaluation
contract own judge visibility and source semantics. No judge redesign or new
benchmark policy is introduced. Two unseeded repeats on exposed development cases
support descriptive learning, not causal certainty or benchmark generalization.

## Primary reporting and manual review

Report G supported/total points, answer-level all-G passes, supporting-point and
qualification G separately, by model/case/repeat across all three conditions.
Changing point counts and empty fields must remain visible. C and S are secondary
checks for lost necessary content when claims are shortened; A and strict joint
passes remain descriptive diagnostics, not the primary citation outcome.

Read every whole answer and its relevant cited passages. Distinguish missing
own-point citations, unsupported links between facts, lost scope/uncertainty,
table-reading errors, and disputed judge interpretations. Specifically inspect
whether compound points independently cite the entity mapping and substantive
fact; whether deleting an unsupported relationship preserves necessary information;
and whether a new error merely replaces the old one. Record exact spans and point
identities, both improvements and regressions. Preserve frozen scores separately
from manual disagreement. Do not infer that G pass proves every conclusion clause
was checked; conclusion adequacy has different visibility and semantics.

## Limits recorded before dispatch

One revision, 12 generation calls, maximum 192 judge calls and 204 count calls;
maximum 16 judge items per answer. Zero retries, repair/replacement generations,
extra repeats, cherry-picking or prompt edits after freeze. Input cap 100,000;
generation output cap 12,288 including reasoning where applicable; judge output
cap 4,096. Two-hour global timebox, 900 seconds per call and 1,800 seconds per
answer evaluation.

Reserve $8 incremental planning liability. At conservative retained planning
prices $0.25/M input and $0.75/M output, maximum generation/judge liability is
$5.800416. Counting cost is unknown, with zero planning allowance, not asserted
free. These are planning limits, not provider-enforced prices or billing promises.
Preserve unreported usage subtotals. No new cost assigned to saved controls.

Stop globally on execution, accounting or integrity failure, elapsed time or cap
exhaustion. Preserve invalid content without replacement; if an answer requires
more than 16 judge items, retain it untrimmed and stop for review with evaluation
unavailable. Every planned slot remains in reporting. Verify credential presence
without showing secrets using uv --env-file .env before provider construction.

## Validation, review and outputs

Reuse native transport unchanged in a create-only external runner. Bind sources,
controls, prompt, contract, configuration and implementation before dispatch.
Offline tests verify fixed coverage, exact prompt delta, source equality,
reference isolation, no-summary routing, zero retries/stopping, native replay and
reporting denominators. Reconstruct original plan insertion order for exact
native-byte replay; JSON-normalize semantic plan/report comparisons.

Run make fix, make check and git diff --check before live calls for implementation.
Independent preflight reviews prompt, frozen bindings, budgets and offline tests.
Root's manual dispatch gate requires approved hash-matching review plus passing
repository checks. Independent final review checks text/source interpretations,
accounting, replay and publication. Preserve rejected/audit-failed artifacts if
any. Publish task outcome, result pointer and current project routing.

## Acceptance and exclusions

Complete bounded comparison or report stopped/unavailable slots, with provisional
retain/revise/reject recommendation and specific limitations. No automatic prompt
promotion or further revision. No other 13 development cases, locked-test/reserved
content, model changes, judge retuning, Task 10 edits, new combined prompt, stronger
model or 11E. Qualification rewrite remains set aside by user decision.

## Outcome (2026-10-19)

All 12 fresh answers completed and were compared with 24 saved controls. Do not
adopt the replacement example on this evidence. Neutral-input V6b remains the
working control; the qualification rewrite remains set aside. No baseline is
qualified and no further revision, combination or 11E is started.

| Model / measure | Neutral V6b | Citation reminder | Replacement example |
| --- | --- | --- | --- |
| Luna point G | 22/23 | 20/20 | 21/21 |
| Luna all-G answers | 5/6 | 6/6 | 6/6 |
| Luna supporting-point G | 15/15 | 13/13 | 13/13 |
| Haiku point G | 35/42 | 32/41 | 38/45 |
| Haiku all-G answers | 1/6 | 0/6 | 1/6 |
| Haiku supporting-point G | 24/26 | 23/27 | 28/30 |

Haiku still has seven failed G points, the same as baseline. A slightly higher
percentage with more points is not a demonstrated improvement. Luna's one old
failed compound qualification was already absent/reworded in the reminder arm.
Per-case G (baseline → reminder → example): Luna groundwater 6/6→6/6→5/5,
transportation 11/12→7/7→9/9, flooding 5/5→7/7→7/7; Haiku groundwater
10/13→8/12→10/12, transportation 11/14→13/16→16/18, flooding14/15→11/13→12/15.

The core Haiku missing-citation pattern persists in transportation repeat 1: the
compound project-name/number/analysis-scope point cites P3 but needs P2 for the
name mapping. Its second repeat correctly cites both, as the reminder's second
repeat already did. Groundwater repeat 1 still infers that a closure-design review
makes modeled groundwater results subject to that review, precisely the kind of
unsupported relationship the example was intended to prevent. Citation completeness
and relational support remain distinct problems. Original scores are preserved.


A positive Haiku change is clearer separation of the P1 modeled decrease from the
P3 trench mechanism and restoration of geographic scope. This does not eliminate
the review-to-model inference in repeat 1. Both new groundwater conclusions also
omit P2 while referring to design review, a citation gap outside point-G. Some
penalties remain disputed: one S decision overlooks explicit Plan-area wording;
one G decision challenges a source-local absence statement; flooding includes
at/near and relevance-versus-grounding issues. All original scores remain intact.

Luna correctly cites both transportation passages in its supporting points, but
both new conclusions omit the identity-mapping citation P2. That omission existed
in one reminder conclusion, neither baseline conclusion. Point-G does not grade
conclusion citation completeness. New flooding repeat 2 also assigns the old
large-storm depth to a 100-year storm in its conclusion while its support preserves
the distinction. Clean point-G is therefore not a whole-answer citation guarantee.

Secondary results: S is Luna6/6→6/6→5/6 and Haiku6/6→5/6→5/6; C is
Luna5/6→4/6→4/6 and Haiku4/6→5/6→4/6; strict joint is Luna4/6→4/6→3/6 and
Haiku1/6→0/6→0/6. These do not override the primary mechanism review. Luna's new
flooding repeat1 S failure demands comparable storm baselines even though residual
flooding alone establishes non-elimination; manual review disputes that inference
requirement. Haiku's at/near and local absence/relevance penalties also require
separate interpretation rather than automatically blaming citation assignment.

This example replaces an existing example and removes its machine-comparison
illustration; this experiment cannot isolate extra example detail from that
replacement. Two unseeded repeats are descriptive, and no claim is made that the
example causally worsened performance. Both intended failure mechanisms remain
visible, so there is insufficient benefit to justify replacing the working prompt.

Validation: make fix and make check passed (4,166 passed, one skipped, 71 warnings),
13 independent runner/report tests passed before dispatch. Preflight found and
fixed a report-only incomplete-evaluation edge case before calls; partial reports
now remain unavailable slots with receipts and identities preserved. No frozen
inference binding changed. Final audit verified all 12 plan/report replays, 114
native receipts/count-usage joins, 15 unchanged source passages, and all 11,868
11D.9 plus 2,552 11D.10 sealed files unchanged. Independent per-model text reviews
retain exact spans, identities, source evidence and original judge disagreements.

Accounting: 12 generation, 102 judge and 114 count calls; zero retries,
replacements or execution failures. Estimated generation/judge cost $0.106343905.
All total-cost receipts are present; nine reasoning-token subtotals are missing.
Counting charges remain unknown. Saved controls incurred no new calls. The $8
reserve was a planning bound, not a provider billing guarantee.

The [result pointer](../../docs/specs/task11d11_result.json) binds reports, reviews,
validation and final artifacts. Further prompt experiments require a new bounded
comparison; no other questions or stronger models were evaluated.
