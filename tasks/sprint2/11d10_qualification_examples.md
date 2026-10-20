# Task 11D.10 — Whole-answer qualification rule with invented examples

Status: Complete with limitations (2026-10-19); no revision promoted.

## Abstract and goal

The user accepts a whole-answer caveat rule with unrelated include/omit examples
and asks to compare it with the baseline and the preceding qualification rewrite.
Test whether it improves qualification grounding and relevance without moving
unsupported caveats into supporting points, conclusions or optional context.

## Inputs, design and outputs

Use sealed 11D.9 neutral-input V6b baseline and qualification-only runs as saved
comparators. Generate one fresh condition on the same C041, C017, C037 and C056
questions, both Luna and Haiku, two repeats each: 16 new answers. Do not rerun
controls, reinterpret repeat numbers as matched random seeds, or select best
answers. Historical controls and the new condition are development diagnostics.

New prompt: docs/prompts/task11d10_qualification_examples.md. Start from the exact
11D.9 qualification prompt (V8 delta from V6b), replace only its three-sentence
qualification block with the approved whole-answer rule, then append four
unrelated invented include/omit illustrations. Keep V6b's field contract and
original three examples. Examples address necessary conditions versus unrequested
unknowns; explicit limitations versus unsupported consequences; missing requested
data versus irrelevant missing details; and unspecified versus different. They
contain no benchmark entities, source facts, labels or evaluator feedback.

Keep neutral questions, passage bodies, citation IDs, locators, fixed-six reference
publication, target schema and model/reasoning settings unchanged. Luna uses
medium reasoning; Haiku uses adaptive medium effort. No project summary, added
citation-check sentence or rewritten conclusion-check sentence. Frozen A/G/C use
Luna and S uses Haiku; all judge cores and contexts remain unchanged from the two
saved comparison arms. Reference answers never enter generation.

Fresh external namespace:
`pipelines/brisbane_baylands/task_11/validation_11d10_20261019`.
Retain native requests, raw answers and judgments, receipts, failures, all exact
condition/run/candidate/repeat/point joins, offline replay, comparative reports,
manual reviews and accounting uncertainty. Repository artifacts are this contract,
the new prompt and a result pointer; sealed 11D.9 files remain untouched.

## Hypotheses and primary reporting

The whole-answer rule and concrete yes/no examples should reduce unsupported or
unrequested caveats throughout all fields, while retaining material assumptions
and evidence limitations. This combined rule-plus-examples revision cannot isolate
which part causes any observed effect.

Primary automatic measure: frozen G on points actually in qualifications, joined
by candidate point identity rather than a Q-prefix assumption. Show supported/total
points, failed points, qualification counts, answers with no qualification points,
and answers with no failed qualification. Empty fields do not demonstrate grounding
skill. Compare the same four questions by model, case and repeat across all three
conditions. The saved counts are Luna 9/9 baseline and 7/7 prior rewrite; Haiku
19/24 baseline and 18/20 prior rewrite. Prior Haiku support grounding changed from
37/38 to 34/38, so qualification-only gains are not sufficient.

Primary manual review: read every complete answer and relevant own-point sources;
classify caveats as material, supported but unnecessary, unsupported, or disputed.
Preserve exact spans and reasons and record field location. Relevance is not a
frozen G judgment. Inspect conclusion/support/optional fields for displaced gap
claims and preserve useful assumptions; do not reward merely shortening answers.
Use explicit uncertainty for borderline cases, not invented authoritative labels.

Secondary measures: G for supporting points and all judged points, A/S/C and strict
whole-answer diagnostic. Show failures and regressions, but do not let whole-answer
conjunction override a targeted improvement without reading its cause. Do not
change scores for manual disagreement. No new judge or relevance grader is added.

## Learning checkpoint

11D.9's targeted follow-up showed Haiku qualification G improved 19/24→18/20 even
while whole-answer scores declined. G does not measure whether a caveat is useful,
and unsupported assertions can move to another field. The earlier invented V6b
examples improved observed application more than extra verification prose; this
motivates unrelated include/omit demonstrations, not case-specific answer hints.
The storm review distinguishes explicit different scenarios from an unspecified
baseline return period: missing identity does not establish difference. The new
printer example teaches that general distinction without inserting storm details.

## Limits and stopping recorded before dispatch

One fresh prompt, 16 generations, maximum 256 judge calls and 272 count calls,
16 judge items per answer. Zero retries, repair generations, replacement answers,
extra repeats or prompt revisions after preflight. Maximum 100,000 input tokens,
12,288 generation output tokens (including reasoning where applicable), and 4,096
judge output tokens. Two-hour total timebox, 900-second per-call timeout and
1,800-second per-answer evaluation ceiling.

Reserve $10 incremental planning liability. At retained conservative planning
prices of $0.25/M input and $0.75/M output, maximum generation/judge liability is
$7.733888. This is not a provider-enforced cap or a billing guarantee. Count billing
remains unknown with zero planning allowance, not claimed free. Preserve missing
usage subtotals rather than treating them as zero. No new cost attributed to saved
controls. Stop globally for execution/accounting/integrity failure, elapsed-time
or call-cap exhaustion. Keep every planned slot and unavailable reason. Invalid
content is retained without replacement; if more than 16 judge items are needed,
mark evaluation unavailable without trimming and stop for review.

Load the local environment through uv --env-file .env; offline verify provider-key
presence without printing secrets before dispatch. The prior zero-call startup
failure is not a reason to weaken the no-retry policy.

## Implementation, validation and review

Reuse the native transport unchanged with a fresh create-only runner. Verify source
and comparator seals, frozen prompt/model/schema identities and native delivery.
Offline tests cover exact prompt change, unrelated examples, no summary/reference
leakage, fixed 16-slot coverage, failure/stop policy, correct qualification joins
and empty/missing denominators. Replays use original plan insertion order for exact
native-byte checks and lossless JSON normalization for saved plan/report equality.

Run make fix, make check and git diff --check for implementation work before live
calls. Bounded independent preflight reviews the prompt and limits. Bounded final
review checks receipts, primary score calculations, manual caveat assessment and
all-field migration. Keep original failed tests/audits if any repairs are needed.

## Acceptance and non-goals

Complete and report all planned attempts within limits, including failure reasons;
compare primary and secondary outcomes with both saved controls and provide a
provisional retain/revise/reject judgment with small-sample limits. No universal
claim or baseline promotion solely from this panel. No extra questions, remaining
13, held-out/reserved content inspection, source edits, Task 10 edits, judge
retuning, stronger models, combined unrelated prompt additions or 11E.

## Outcome (2026-10-19)

Completed all 16 fresh answers and all 32 saved-control comparisons. No revision
is selected for promotion. Retain neutral-input V6b as the working control; retain
the earlier qualification rewrite and this refinement as separate experiments.
The new combined whole-answer rule plus examples does not reliably improve the
qualification boundary across models/questions. Do not combine additions or begin
11E on this evidence. Result pointer: [11D.10](../../docs/specs/task11d10_result.json).

| Model / measure | Neutral V6b | Prior rewrite | Rule + examples |
| --- | --- | --- | --- |
| Luna qualification G | 9/9 | 7/7 | 5/5 |
| Luna empty qualification answers | 1/8 | 2/8 | 3/8 |
| Luna supporting-point G | 21/21 | 23/23 | 22/23 |
| Haiku qualification G | 19/24 | 18/20 | 14/18 |
| Haiku qualification-failure-free answers | 4/8 | 6/8 | 5/8 |
| Haiku supporting-point G | 37/38 | 34/38 | 37/39 |

All Haiku answers have qualifications. Luna has no qualification grounding gain;
one new electricity answer omits the useful regional-battery exclusion entirely.
Haiku animal qualifications improve in relevance (no provenance/fine-amount doubts)
and electricity loses manufactured gross/net ambiguity. Its qualification G by
case is animals 4/5→4/4→2/2, electricity 6/9→6/7→7/7, wetlands 4/4→4/4→4/5,
and flooding 5/6→4/5→1/4. These variable point denominators are descriptive,
not independent trials or a causal estimate of the examples alone.

The flooding regression includes an unsupported categorical intersection-location
claim in both support and qualifications, plus a claim of no independent
verification. Removing a caveat can replace uncertainty with unsupported certainty.
The different-storm assertion disappears, but comparable-storm wording remains
ambiguous. Wetlands introduces one overly broad claim that function during
restoration is not established despite discussing evidence of potential losses.
Some missing-result/method caveats persist across fields. Animal enforcement-agent
gaps are borderline relevant to the enforcement question, not automatically wrong.

Manual disagreement is kept separate from frozen scores: Haiku flooding repeat 2
says “1.2-foot reduction figure,” which G reads as reduction by rather than to
1.2 feet despite correct wording elsewhere; Luna wetland repeat 1's C failure
appears to conflate restoration timing with functional-loss duration. Neither
score is overridden. Legitimate wetland limits moved into support appropriately;
field movement alone is not an error. Exact spans, sources, identities and all
three answers are preserved in the two model-specific manual reviews.

Secondary strict passes are Luna 6/8→7/8→5/8 and Haiku 4/8→2/8→2/8. They do not
replace targeted qualification findings. The learning is to evaluate both evidence
support and relevance, count useful omissions, and inspect every field. Grounding
alone cannot measure whether a caveat belongs. The prompt package combines rule
and examples, so this run cannot attribute changes to either separately.

Validation: make fix and make check passed (4,166 tests, one skipped, 71 warnings);
11 runner/report offline tests passed before dispatch. Independent prompt/contract
review approved. Final native delivery audit verified 149 receipts, all 16 plan and
report replays, 13 unchanged source passages and the complete 11,868-file prior
11D.9 seal. Zero retries, replacements or execution failures. Final documentation
diff validation and publication review are bound in the result pointer.

Accounting: 16 generation, 133 judge and 149 count calls. Estimated generation/judge
cost $0.0682024; count billing remains unknown. Total usage receipts are present;
13 omit reasoning-token subtotals. The $10 reserve was a planning bound, not a
provider billing guarantee. No new cost is attributed to saved controls.
