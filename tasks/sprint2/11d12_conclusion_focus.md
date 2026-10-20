# Task 11D.12 — Focused conclusion condition and exclusion check

Status: Complete with limitations; user promoted this working prompt on 2026-10-19. See acceptance below; experimental results remain unchanged.

## Goal and design

The user authorizes refining the conclusion check after its targeted analysis.
Test whether a focused transfer of material assumptions, conditions and exclusions
improves conclusion completeness while preserving an explicit supporting basis,
without promoting unnecessary caveats or expanding unrelated detail.

Start from exact neutral-input V6b plus a replacement for the single 11D.9
conclusion-check sentence. New text:

> Before returning, identify any assumption, condition or exclusion in the supporting points or qualifications whose omission would make the conclusion misleading or change the answer. Include it in the conclusion, and state its supporting basis explicitly in the supporting points. Do not copy other details or caveats merely because they appear elsewhere in the answer.

Preserve all other baseline bytes and original three examples. No qualification
rewrite, citation reminder/replacement example, shared project summary or other
addition. Prompt: docs/prompts/task11d12_conclusion_focus.md.

Fresh conclusion_focus arm: C041, C017 and C014, Luna and Haiku, two repeats each,
12 fresh answers. Compare with all 24 saved answers for the same cases/models/
repeats in sealed 11D.9 baseline and conclusion arms. No control reruns, matched-seed
claims or best-of selection. Hold neutral input/reference publication, passages,
citation IDs, target schema, models and reasoning settings fixed. Luna uses medium,
Haiku adaptive medium. Frozen 09G Luna A/G/C and Haiku S settings/cores are unchanged.
Reference answers and evaluator feedback remain absent from generation requests.

External namespace: pipelines/brisbane_baylands/task_11/validation_11d12_20261019.
Preserve all native requests, raw outputs/judgments, exact run/candidate/repeat/point
identities, receipts, failures and accounting uncertainty. Sealed old runs and
Task 10 artifacts remain unchanged.

## Hypothesis and learning checkpoint

The 11D.9 offline review found Luna conclusion adequacy C improved 3/6 to5/6;
one electricity answer genuinely moved material assumptions/exclusions into its
conclusion. Haiku improved1/6 to2/6 but still left a necessary condition solely in
support in both electricity repeats. Some other gains depend on interpretive judge
thresholds; expanded conclusions sometimes lacked a supporting-point basis or
promoted distracting caveats. These findings motivate a narrower selection rule
and explicit destination for support, not case-specific answer hints.

The revised check should transfer answer-changing conditions/exclusions and retain
support, while leaving peripheral details out. This is one replacement instruction
and cannot isolate its selection, transfer and support-placement clauses. Two
unseeded repeats on exposed development cases provide descriptive evidence, not
causal certainty or benchmark generalization. The local 09G maintainer guide and
11D.9 contract own judge visibility; no scoring policy changes are introduced.

## Primary evaluation and review

Primary automatic results: C conclusion adequacy and S supporting sufficiency,
by model, case and repeat across three conditions, with all planned answers in
coverage. Secondary G supported/total and fail-free answers, supporting/qualification
fields separately, A and strict joint diagnostics. Show changing point counts and
empty fields. G does not establish conclusion citation completeness.

Read all complete answers and cited evidence. Track whether necessary conditions
and exclusions reach the conclusion and retain an explicit supporting-point basis;
distinguish actual transfer from deletion or paraphrase. Inspect unnecessary caveat
promotion, unsupported relations, scope changes and missing citations across fields.
Preserve exact spans/identities and separate genuine improvements, persistent
failures and disputed judge interpretations without overriding scores. Do not
attribute every new output defect to the instruction from two unseeded repeats.

## Limits recorded before dispatch

One revision, maximum12 generation,192 judge and204 count calls; at most16 judge
items per answer. Zero retries, repairs, replacements, extra repeats or edits after
freeze. Input100,000 tokens, target output12,288 including reasoning where
applicable, judge output4,096. Global2h, per-call900s, per-answer evaluation1,800s.

Reserve $8 incremental planning liability. At retained conservative planning
prices $0.25/M input and $0.75/M output, maximum generation/judge liability is
$5.800416. Counting charges are unknown with zero planning allowance, not asserted
free. These are planning limits, not provider billing guarantees. Preserve missing
usage subtotals and do not assign fresh costs to saved controls.

Stop globally on execution/accounting/integrity failure, elapsed time or cap
exhaustion. Invalid outputs stay in denominators without replacement. If more than
16 judge items are needed, retain the untrimmed answer and stop for review with
evaluation unavailable. Preserve every planned slot and unavailable reason. Verify
credential presence without exposing values using uv --env-file .env before calls.

## Implementation, validation and review

Reuse native transport unchanged with a fresh create-only external runner. Bind
prompt, immutable contract snapshot, selected sources, controls, model/judge
configuration and implementation before dispatch. Offline tests verify exact prompt
delta, source equality, reference isolation, fixed coverage, stop/create-only
behavior, partial reporting/accounting and native replay. Exact native replay must
reconstruct original plan insertion order; JSON normalization applies only to
semantic saved plan/report comparisons.

Run make fix, make check and git diff --check before live calls. Independent
preflight verifies frozen inputs, budgets and offline tests. Root manually verifies
approved review hashes and passing checks before dispatch. Final independent
per-model text review, accounting/native audit and publication review precede
result sealing. Preserve any failed validation artifacts and repairs. Publish task
outcome, result pointer and project routing.

## Acceptance and non-goals

Complete bounded comparison or document stops/unavailable slots; recommend retain,
revise or reject with limitations. No automatic prompt promotion or further cycles.
No remaining13 development cases, locked-test/reserved content, Task10 changes,
judge retuning, model/settings changes, stronger model, or11E. Qualification rewrite
and citation-example replacement remain set aside by user decision.

## Outcome (2026-10-19)

Completed all12 fresh answers and compared all24 saved controls. Preserve this
focused check as a promising experimental variant, but do not replace neutral-input
V6b or select a qualified baseline. It improves a specific intended behavior for
Luna and Haiku supporting sufficiency, without a general conclusion-coverage gain
over the prior check. No combined prompt, further cycle or11E is started.

| Model / primary measure | Baseline | Prior conclusion check | Focused check |
| --- | --- | --- | --- |
| Luna C | 3/6 | 5/6 | 5/6 |
| Luna S | 5/6 | 5/6 | 4/6 |
| Haiku C | 1/6 | 2/6 | 2/6 |
| Haiku S | 5/6 | 3/6 | 6/6 |

The clearest intended gain is Luna electricity C0/2→1/2→2/2. Both new conclusions
include sufficient distributed storage and exclusion of uncertain utility-scale
battery benefits, and both now explicitly state these in supporting points. This
is actual transfer and support placement, not merely a changed judge threshold.
Repeat2 is a clean C/S pass. Repeat1 nonetheless applies the2.5% rate to remaining
net demand in its conclusion versus overall demand in support; its2045 claim still
has a basis only in qualifications. Preserve that S failure separately from the
coverage improvement.

Luna transportation C1/2→2/2→1/2 offsets the electricity gain. Repeat1 omits the
topic-specific cumulative scopes entirely. Repeat2 adds a supporting basis for
the interchange restriction, but a topic-name/TRA-number mapping is not explained
in support. Its listed-versus-projections-based distinction is imprecise for TRA4;
similar wording passed before, so do not label every changed score a new factual
harm. Animals stay C2/2 across conditions. Full text/source review records these
mechanisms and a persistent conclusion citation omission separately from point G.

Haiku electricity remains C0/2 across all three conditions: both new answers still
leave sufficient distributed storage outside the conclusion despite stating it in
support. Haiku transportation C0/2→1/2→2/2, but some improvement depends on accepting
implicit general cumulative assumptions rather than explicit broader regional
growth. Animals C1/2→1/2→0/2 because applicability doubts appear in both conclusions.
The rule has not reliably selected which qualifications belong in a direct answer.
Haiku S improves to6/6; exact repaired premises and judge-threshold limitations are
preserved in the independent Haiku review rather than attributed wholesale to the
new instruction.


The three Haiku S recoveries versus the previous check have identifiable changes.
Electricity repeat1 removes unsupported percentages from its conclusion and supplies
the generation/consumption pairs in support. Transportation repeat1 uses matching
TRA identifiers in conclusion/support instead of naming categories without mapping
them; repeat2 aligns the project-group wording and avoids the prior disputed
analysis-geography/project-origin distinction. These are partly clearer or narrower
claims rather than more material facts reaching the conclusion. The animal S gain
versus baseline is more interpretation-dependent. Thus6/6S is encouraging but not
proof of complete answers or universally improved source fidelity.

Grounding guardrails: Luna27/28→22/25→23/24 supported G points, Haiku41/49→46/53→44/49.
Strict joint results are Luna2/6→3/6→3/6 and Haiku1/6→0/6→0/6. These do not erase the
targeted coverage/support improvements. C completeness can pass while S detects an
internal mismatch; G does not establish conclusion citation completeness. Preserve
all original scores and distinguish manual judge disagreement from model error.
Two unseeded repeats cannot establish causal effects for every changed output.

Validation: make fix and make check passed (4,166 passed, one skipped,71warnings),
13 independent runner/report tests passed prelive. A copied task-path error was
caught/fixed offline and its failure record retained before preflight freeze.
Independent prompt/contract review approved exact isolated delta. Final audit
verified12 plan/report replays,121 native/count/usage receipts,9 unchanged source
passages,11,868 sealed11D.9 and1,959 sealed11D.11 files unchanged. No execution
failures, retries or replacements. Per-model independent text reviews and final
publication review preserve identities, exact spans, evidence and limitations.

Accounting:12generation,109judge,121count calls. Estimated generation/judge cost
$0.108671075; no missing total-cost receipts or count/usage discrepancies. Five
reasoning-token subtotals are missing; counting charges remain unknown. Saved
controls incurred no new calls. The$8 reserve was a planning bound, not a billing
guarantee. No other questions, held-out content or stronger models were evaluated.

The [result pointer](../../docs/specs/task11d12_result.json) binds all artifacts.
Further refinement requires a new bounded comparison. Qualification and citation
rewrites remain set aside; neutral-input V6b remains the working control.

## Subsequent user acceptance (2026-10-19)

After reviewing these results and limitations, the user explicitly requested
promotion. The focused conclusion-check prompt is now the accepted working prompt
for subsequent Task11 development. The [working selection](../../docs/specs/task11_working_prompt.json)
binds its exact text and historical result. The outcome above records the prior
experimental recommendation; sealed results remain unchanged. Qualification and
citation rewrites stay excluded. No all-19 validation is claimed and11E remains
unstarted. The next task is the offline [provenance review](11d13_provenance_caveat_review.md).
