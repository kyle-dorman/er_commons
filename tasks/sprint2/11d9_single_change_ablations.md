# Task 11D.9 — Independent single-change prompt comparisons

Status: Complete (2026-10-19); all five stages evaluated; no combined prompt promoted.

## Abstract and goal

The user requests a fresh V6b baseline with neutralized inputs, then separate
qualification, citation, shared-summary and rewritten conclusion checks on their
relevant questions, for Luna and Haiku. Learn which changes improve the actual
answers as well as frozen judge scores. Every arm starts from the same baseline;
no arm incorporates another addition and no automatic combination is authorized.

## Inputs and outputs

Reconstruct the 11D.8 fixed-six neutral condition from sealed 11D.5 source packets
and 11D.6 locator/reference derivatives: neutral questions, unchanged passage
bodies/citation identities and publication-v5 fixed-six reference conclusions.
Use V6b's exact field contract and three examples. Read 11D.6/11D.7 preparation,
11D.8 outcomes, the 09G frozen configuration and production judge guide. No source
from the remaining 13 development cases or held-out/reserved content is needed.

The external namespace is
`pipelines/brisbane_baylands/task_11/validation_11d9_20261019`.
Preserve all requests, raw outputs, native/count receipts, identities, failures,
plans, reports, offline replay, independent reviews and accounting uncertainty.
Tracked outputs are four prompt files, this task outcome and a result pointer.

## Frozen design and hypotheses

Two fresh repeats per question per model; Luna gpt-6-luna medium reasoning and
Haiku claude-haiku-5-5 adaptive medium. Baseline has **no project summary**, either
for generation or judges. All arms retain neutral inputs and references. Models,
settings, field schema, examples, passage bodies and judge cores remain fixed.
A/G/C use frozen Luna; S uses frozen Haiku. Reference answers and evaluator
feedback never enter generation requests.

| Stage | Single difference from baseline | Fixed cases | Answers |
| --- | --- | --- | --- |
| Baseline | Exact V6b, neutral inputs, no summary | C041, C017, C019, C014, C037, C056 | 24 |
| Qualification | Exact V8 minus V6b delta: replace qualification guidance and remove superseded absence sentence | C041, C017, C037, C056 | 16 |
| Citation | Add accepted clause-level citation check only | C019, C014, C056 | 12 |
| Summary | Add existing one-sentence project summary to generation and all judges; baseline target instructions unchanged | C041 | 4 |
| Conclusion | Add rewritten conclusion/support check only | C041, C017, C014 | 12 |

The qualification arm should reduce irrelevant or unsupported gap caveats without
moving necessary assumptions out of the conclusion or support. Inspect animal
adoption/enforcement caveats, electricity accounting assumptions, wetland temporal
gaps and flood absence claims. Qualification count alone is not quality.

The citation arm should repair incomplete own-point evidence for groundwater
causal links, transportation comparisons and flooding cross-source comparisons.
Inspect the cited passages clause by clause; arithmetic/table mistakes are a
separate failure mechanism, not automatically a citation-rule failure.

The summary arm should remove animal-policy provenance caveats about whether the
passages apply to Baylands. Inspect replacement caveats and unsupported claims.
Because the same summary also goes to judges, this tests a combined context
condition, not a pure generation-only intervention.

The conclusion arm adds exactly: “Check that every fact, assumption, exclusion or
qualification needed to answer the question appears in the conclusion, with its
supporting basis in the supporting points.” Inspect animal support/optional-field
placement, electricity storage and excluded benefits, and transportation regional
growth. Do not insert these case-specific expectations into target instructions.

## Research and learning checkpoint

The local 11D.8 comparison showed bundled changes cannot identify a causal
contributor; 11D.6 establishes the neutral-input provenance boundary, and the
production judge guide establishes field-specific visibility. This design holds
all other conditions fixed and chooses subsets before seeing fresh results.
Compare each arm only to baseline answers for the same questions. Two unseeded
repeats estimate neither statistical significance nor general benchmark accuracy;
repeat numbers preserve identities, not matched random draws. Independent
single-change tests cannot establish how a future combination will interact.

## Dispatch limits, sequencing and stopping

Five conditions, two models, two repeats and the above fixed subsets: maximum
68 generations, 1,088 judge calls, 1,156 count calls; at most 16 judge items per
answer. Generation input limit 100,000 tokens, output limit 12,288 (including
reasoning where applicable); judge input limit 100,000, output limit 4,096.
Zero retries, repairs, replacement answers, extra repeats or best-of selection.
No prompt revision after the frozen preflight within this task.

Reserve $40 incremental estimated liability, using conservative retained planning
prices of $0.25/M input and $0.75/M output tokens. The maximum generation/judge
liability at these prices is $32.869024. This is not provider-enforced billing or
a claimed actual charge. Counting charges remain unknown with zero planning
allowance; preserve missing usage fields separately. A changed observed usage
or identity/accounting inconsistency stops dispatch. Prior reservations remain
historical records, not accumulated actual spending.

Maximum four hours elapsed across the staged live experiment, with 900 seconds
per generation and at most 1,800 seconds per answer evaluation. Run the complete
baseline first and review its text/scores before any arm. Then run qualification,
citation, summary and conclusion sequentially, reviewing each completed arm.
Checkpoint review does not authorize editing the frozen next arm or extra calls.
Stop globally on provider/judge execution errors, uncertain accounting, integrity
failure, exhausted call/spend reserve or elapsed-time limit. Invalid generated
content remains in denominators with no replacement. If more than 16 judge items
are needed, retain the answer and mark evaluation unavailable; never trim points.

## Implementation, validation and review

Reuse the native 11D.8 transport, with a new create-only staged runner and fresh
arm/run identities. Bind all selected source hashes, prompts, configuration,
immutable contract and implementation before dispatch. Omit project-context tags
entirely outside the summary arm. All stages share identical baseline inputs.
Replays use saved native delivery and lossless JSON normalization, never calls.

Independent preflight review covers nonadditivity, fixed subsets, target/reference
isolation, neutral-source provenance, limits and stage ordering. Offline tests
cover prompt deltas, source equality, summary routing, planned coverage, duplicate
stage rejection, stopping and receipt/report replay. Run make fix, make check and
git diff --check before calls if implementation changes; preserve logs. Perform
bounded independent final review of score denominators and qualitative findings.

## Acceptance, reporting and non-goals

Report matched-subset baseline versus treatment by model, case, repeat and A/G/S/C,
including G point-level and all-point-per-answer denominators and all planned
slots. Read candidate text and exact judge failures, distinguish genuine content
changes from judge disagreements, and preserve original scores. Publish before/
after excerpts and provisional keep/revise/reject recommendations without claiming
causal certainty from a small panel. No cross-arm overall model ranking.

No Task 10 edits, historical run mutation, judge retuning, new questions/models,
held-out content access/evaluation, remaining-13 evaluation, stronger model or 11E.
No combined prompt is promoted. Further tweaks/retries await a new user decision.

## Pre-dispatch startup recovery

The first launch did not load the local credential environment and stopped during
OpenAI client initialization. Its baseline records contain zero generation, judge
and count calls; no native dispatch or output exists. Preserve that stopped
namespace unchanged. Load credentials with the existing uv --env-file facility,
verify only their presence, and use fresh namespace
`pipelines/brisbane_baylands/task_11/validation_11d9_20261019_live` with the same
prompts, selected slots, settings and remaining full 68-generation budget. This
is a corrected startup before any model sampling, not an answer retry or budget
expansion. Rebind the contract/preflight and independently verify zero calls and
source/implementation equivalence before live dispatch.

## Outcome

All 68 planned answers were valid and fully evaluated, using 68 generation,
589 judge and 657 counting calls with zero retries or replacements. The fresh
neutral-input V6b baseline scored Luna 8/12 and Haiku 4/12 all-checks passes.
Every addition was compared only with its predefined matching baseline cases.

| Addition | Luna baseline → addition | Haiku baseline → addition |
| --- | --- | --- |
| Qualification rewrite | 6/8 → 7/8 | 4/8 → 2/8 |
| Citation clause check | 4/6 → 4/6 | 1/6 → 0/6 |
| Shared project summary | 2/2 → 2/2 | 1/2 → 1/2 |
| Rewritten conclusion/support check | 2/6 → 3/6 | 1/6 → 0/6 |

### What worked and what did not

The qualification rewrite reduced qualification counts but not consistently
unhelpful caveats. Luna restored battery assumptions in one conclusion; Haiku
introduced an unsupported claim that flooding estimates used different storms.
Electricity field-placement failures also occurred in the fresh baseline, so the
rewrite cannot be identified as their original cause. Do not restore it unchanged.

The citation check repaired a transportation project-name/number/scope citation
linkage in some outputs but did not reliably repair the same error across repeats.
Haiku continued to use neighboring points' citations and inferred relationships
not established even when citing both passages. No overall benefit demonstrated.

The summary did not reliably remove the Baylands-applicability caveat. Haiku kept
it in one repeat and substituted unsupported enforcement doubts in the other.
All answer-level component rates stayed unchanged. A single-question combined
target/judge-context test does not establish broad utility or harm; omit it from
the working control rather than treating it as a demonstrated fix.

The rewritten conclusion check supplied a genuine Luna electricity completeness
improvement in one repeat. Luna C rose 3/6→5/6, but G all-points fell 5/6→3/6.
Haiku still left storage only in supporting points in both electricity answers;
its S rate fell 5/6→3/6. Promoting caveats into the conclusion sometimes moved
unnecessary provenance doubt into the answer. This is the most concrete Luna
refinement lead, not a reliable universal addition or a combination to promote.

Retain neutral-input V6b as the working experimental control, with known failures.
None of the four additions demonstrated a reliable improvement across both models.
No qualified baseline was selected, and no combined prompt, additional repeat,
stronger model or 11E was started. Further changes await the next user decision.

### Review and validation

Independent preflight verified exact nonadditive prompt deltas, unchanged source
content, reference isolation, summary-only routing, predefined subsets and budgets.
Five stage checkpoints reviewed scores and text before advancing. Separate manual
reviews preserve all matched candidates, exact failure reasons and source paths;
independent final interpretation review confirms the matched denominators.

Some scores depend on judge/source issues: the contradictory electricity footnote,
near-versus-at wording, local absence-claim scope, and inconsistent S materiality.
Manual concerns are separate from unchanged frozen scores. Two unseeded repeats
on exposed cases support descriptive findings, not statistical significance.

Validation: make fix, make check (4,166 passed, one skipped, 71 warnings),
12 focused runner/report tests, two audit regression tests and git diff --check.
No maintained package source changed for this task. All five stages replay without
provider calls. The final audit verifies 68 identities, all 657 native message
receipts, count/usage joins, 23 unchanged passages and protected prior artifacts.

The first audit reconstructed JSON payloads in sorted-key order and therefore
failed an exact message-byte check. The corrected audit reconstructs the original
plan order and passes strict native-byte comparison; actual prompt/claim drift
still fails regression tests. A separate sub-picodollar floating-point sum-order
difference is tolerated only in cost aggregation. Original audit scripts/failure
logs remain preserved; no live output or score was changed.

Library-reported generation-plus-judge estimates total $0.45779588. Counting
billing remains unknown. All overall usage and cost receipts are present; 45
reasoning subtotals are unreported and remain unknown. The $40 reservation is a
liability bound, not actual spending. The zero-call credential startup failure
and its recovery remain separately sealed and are not answer retries.

The [result pointer](../../docs/specs/task11d9_result.json) binds complete reports,
paired text reviews, dispatch limits, raw receipts, validation and final audit.
