# Task 11D.14 — Document overview on accepted focused-check baseline

Status: Complete with limitations; user promoted the overview on 2026-10-19.

## Goal, inputs and design

The user authorizes testing the approved CEQA document overview and appendix list
on top of the accepted 11D.12 focused conclusion check. The baseline is the exact
hash-bound working prompt in docs/specs/task11_working_prompt.json. No qualification
or citation rewrite is added. New context is exactly
 docs/prompts/task11d14_document_overview.md, based on the approved writing block.

Use C041, the fixed-panel animal-policy question exhibiting project-provenance
doubt, both Luna and Haiku twice: four fresh answers. Compare with the four saved
11D.12 conclusion_focus answers. No paid control reruns, new cases, matched-seed
claims, replacement outputs or best-of selection. This follows the earlier one-case
summary ablation; do not infer general benefit from this diagnostic.

Supply the same document overview to target and all judge contexts, consistent
with the user's earlier instruction that the project summary also go to judges.
Keep frozen judge cores unchanged. This tests combined context availability,
not a pure generation intervention; manual answer-text review is necessary to
separate disappeared caveats from changed grading. The appendix map is context,
not a new cited passage or reference answer. No instruction about citability is
added. Reference answers and evaluator feedback never enter generation requests.

Hold neutral question, source passages/citation IDs/locators, reference publication,
target schema and model settings fixed: Luna medium, Haiku adaptive medium. Use
09G Luna A/G/C and Haiku S cores. Summary says draft EIR document-set stage; it
includes existing approval records and does not assert every underlying document
is a draft, or every measure is adopted/implemented. The source catalog records
a separate edition exception for one K2 part outside this test; review that
provenance before deploying this overview across the wider corpus. No K2 content
is inspected here. C041 uses Appendix A and the main EIR.

External namespace: pipelines/brisbane_baylands/task_11/validation_11d14_20261019.
Preserve exact candidate/run/repeat/point identities, native requests/raw responses,
receipts, failures, complete coverage and accounting uncertainty. Sealed controls,
11B/11C and Task10 artifacts remain unchanged.

## Hypothesis and learning checkpoint

11D.13 found project applicability doubt in 7/12 Haiku C041 answers and no Luna
answers. P1's neutral title omits Baylands, although the repository source catalog
names Appendix A as the Baylands Specific Plan. The old generic summary described
the project without linking its documents. Explicit common provenance plus an
appendix map should remove that identity doubt while retaining genuine scope
limitations. Draft-review wording might instead encourage adoption/implementation
caveats; inspect that possibility without assuming it will occur.

The source inventory owns appendix labels. The accepted 11D.12 outcome and 11D.13
source/judge review own the local hypothesis and evaluation limits. No new judge
policy, research benchmark or CEQA legal interpretation is introduced. The context
bundles project identity, document map and review stage; effects of those parts
cannot be isolated here. Two unseeded repeats are descriptive evidence only.

## Primary reporting and review

Primary manual measure: project/document applicability caveat occurrence, exact
field and text, across all eight answers. Distinguish literal passage non-naming
from doubt about applicability; inspect whether control measures reach conclusion.
Primary automatic C adequacy, with S and G by field as guardrails. Preserve all
original scores and source/judge disagreements. Count adoption, verification,
enforcement-gap or unrelated qualifiers separately rather than calling them all
provenance failures. Inspect unsupported inferences and whether table/overview
facts are substituted for passage evidence. Show all planned identities and missing
slots; no cherry-picking. No score-based automatic expansion.

## Limits recorded before dispatch

One context revision, four generations, maximum64 judge and68 count calls;
maximum16 judge items per answer. Zero retries, repairs, replacements, extra repeats
or prompt/context edits after freeze. Input100,000; generation output12,288 including
reasoning where applicable; judge output4,096. Global1h, per-call900s and per-answer
evaluation1,800s.

Reserve $3 incremental planning liability. Retained conservative prices $0.25/M
input and $0.75/M output yield maximum generation/judge liability $1.933472.
Counting charges remain unknown with zero planning allowance, not claimed free.
These are planning bounds, not provider billing guarantees. Preserve missing usage
subtotals; saved controls incur no new calls.

Stop globally on execution/accounting/integrity failure, elapsed time or cap
exhaustion. Invalid content remains without replacement. More than16 judge items
means retain untrimmed answer and stop for review with evaluation unavailable.
Verify credential presence only, using uv --env-file .env before dispatch.

## Implementation, validation and review

Fresh create-only runner reuses native transport, adapting proven 11D.9 summary
routing to the accepted focused baseline. Bind selected controls/sources, original
prompt, context, immutable contract, core judge settings and implementation.
Offline tests cover target/all-judge context routing, exact native messages/schema,
reference isolation, unchanged source payloads, fixed coverage, zero retries,
create-only/stopping, and partial-result accounting/reporting. Reconstruct original
plan order for native-byte replay; normalize only semantic JSON comparisons.

Run make fix, make check and git diff --check before live calls. Independent
preflight approves hash bindings/tests; root verifies approval plus repository
checks before dispatch. Final review checks all answer text, judge inputs, receipts,
accounting and replay before publication. Preserve offline failures/repairs.
Publish outcome, result pointer and routing without changing accepted working
selection unless the user subsequently accepts the addition.

## Acceptance and exclusions

Complete bounded comparison or document unavailable slots/stops; report occurrence,
C/S/G and text changes with provisional recommendation. No automatic adoption or
further calls. No other13 development cases, locked/reserved content, Task10 edits,
judge retuning, stronger models, new combined instructions or11E.

## Outcome (2026-10-19)

Completed four fresh C041 answers and compared all four saved focused-check
controls. The overview is a promising targeted provenance-context addition:
Haiku project-applicability doubt disappears in both repeats across all fields,
while Luna remains free of it. No automatic adoption or general accuracy claim.
The focused conclusion check remains the accepted working baseline; this context
addition awaits user acceptance or a further bounded comparison.

| Model / measure | Focused-check baseline | Plus overview |
| --- | --- | --- |
| Luna provenance caveats | 0/2 | 0/2 |
| Haiku provenance caveats | 2/2 | 0/2 |
| Luna C / S | 2/2 / 2/2 | 2/2 / 2/2 |
| Haiku C / S | 0/2 / 2/2 | 1/2 / 2/2 |
| Luna point G | 7/7 | 7/8 |
| Haiku point G | 14/15 | 13/14 |

Full manual review finds no migration of the provenance doubt to another field.
Both new Haiku answers apply the feeding-station restrictions to the project;
there is no longer a statement that the excerpt's failure to name Baylands makes
its applicability unestablished. This is a text-level improvement, not merely a
changed judge verdict. Both Haiku answers retain proposed/not-implemented caveats,
so the overview does not solve general qualification selection. They do not claim
that all approval-record appendices are unapproved.

Remaining failures have distinct causes. Haiku repeat1's qualification broadly
says no enforcement procedures are stated for pet-policy violations; the source
actually describes CC&R/HOA enforcement, making the G failure defensible. Repeat2's
C failure is a lease-enforcer caveat that G accepts; the reference's broad lease-
provision account and the narrower source phrasing admit a materiality/scope
interpretation dispute. This is not a provenance relapse. Repeat2 also adds
"other wildlife attractants" to the prohibition in its conclusion, although the
source prohibits feeding stations for feral cats; frozen judges do not flag that
scope expansion. Manual concerns do not override scores. Both fresh Luna conclusions also use
broader feral-animal wording around the feeding-station prohibition; retain this
as a precision concern relative to the source's feral-cat wording.

Luna repeat2's failed G qualification appears to discuss trapping enforcement,
but the judge reads it as denying pet-policy enforcement described elsewhere in
the passage. The conclusion explicitly limits the uncertainty to trapping, making
this a plausible scope-overreach dispute. Both Luna C and S answers pass. Strict
joint scores are Luna2/2→1/2 and Haiku0/2→0/2; those do not erase the targeted
removal of provenance caveats.

The overview was supplied to generation and all judges. Score changes therefore
combine answer changes and evaluator-context changes. The overview bundles project
identity, document inventory and draft-review stage; this comparison cannot say
which part was necessary. Two unseeded repeats on one exposed question establish
neither causal certainty nor performance on the rest of the panel. Before broader
use, review the documented source-catalog edition exception outside this test;
this task inspected no affected K2 content and modified no source metadata.

Validation: make fix and make check passed (4,166 passed, one skipped,71warnings),
13 independent runner/report tests passed prelive. Initial offline binding to an
unlisted nested completion was fixed by binding the sealed control summary; original
failure/repair records retained. Approved overview and exact accepted base were
verified in all native target/judge contexts. Final native audit passed all four
plan/report replays,38 receipts and count/usage joins, and both unchanged source
passages. Full inventories of11,868 sealed11D.9 and2,069 sealed11D.12 files remain
unchanged. Independent full-answer and publication review retained exact identities,
source spans and disagreements. Final docs validation uses git diff --check.

Accounting:4generation,34judge,38count calls, zero retries/replacements/execution
failures. Estimated generation/judge cost $0.01464291; counting charges remain
unknown. No missing reasoning subtotals or count/usage discrepancies. Saved controls
incurred no new calls. The$3 reserve was a planning limit, not a billing guarantee.

The [result pointer](../../docs/specs/task11d14_result.json) binds full reports,
manual review, receipts and validation. No additional questions, remaining13 cases,
held-out content, judge retuning, Task10 changes, stronger model or11E.

## Subsequent user acceptance (2026-10-19)

The user explicitly promoted this context addition after reviewing the comparison.
The [working selection](../../docs/specs/task11_working_prompt.json) now binds the
focused conclusion prompt plus the exact overview and appendix list, delivered to
target and all judge contexts with unchanged judge cores. The earlier outcome
records the experimental recommendation; sealed results remain unchanged.
The combined stack has been tested only on C041. A fixed-six consolidation check
is recommended before further tuning or broader validation, but is not started.
No other13 development cases, held-out run or11E is authorized by this acceptance.
