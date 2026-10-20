# Task 11D.15 — Accepted prompt fixed-six consolidation

Status: Complete with limitations; all 36 planned answers fully evaluated.

## Goal and frozen inputs

Run the accepted working configuration without edits on the fixed development
panel C041, C017, C019, C014, C037 and C056. Produce 36 answers: three independent
unseeded repeats per question for Luna and Haiku. This is consolidation on exposed
tuning questions, not the locked test set or Task 11E.

Use the exact 11D.12 focused conclusion prompt and 11D.14 document overview bound
by docs/specs/task11_working_prompt.json. Preserve the overview's native system
prefix on generation and all judges. Keep original V6b examples; qualification
rewrite, extra citation check and replacement citation example remain excluded.
Use sealed 11D.9 neutral baseline packets, mappings and references for these six
only. Reference answers and evaluator feedback never enter generation requests.
Keep Luna medium, Haiku adaptive medium, schema and evidence unchanged; frozen
09G Luna A/G/C and Haiku S cores remain unchanged. Review the catalog's K2 edition
exception against fixed-panel metadata before dispatch; no new content inspection.
Metadata review found no K2 passages, but C014 P4/P5 originate in
feir_appendix_f1. The accepted overview therefore describes the document family
and review setting; its literal all-draft wording is an acknowledged input
limitation. Preserve the exact authorized configuration and assess effects; do
not silently recast final-edition source metadata as draft.

Hypothesis: the accepted focused check retains necessary conditions in conclusions,
while shared document context suppresses spurious project-applicability doubts.
This run measures repeat consistency and remaining failures across the six; it
does not isolate the contributions of either addition. Saved 11D.9/12/14 results
are historical context, not seeded or newly paired controls. Preserve prior seals,
including 11B/11C, and Task 10 artifacts.

## Pre-dispatch limits and stopping

One fixed configuration, zero revisions during execution. Exactly 36 planned
generation slots, at most 576 judge calls and 612 count calls. At most 16 judge
items per answer. Three repeats per model/question; zero retries, repairs,
replacement outputs or additional repeats. Retain invalid content without
replacement. If an answer requires more than 16 judge items, preserve it untrimmed,
mark evaluation unavailable and stop for review.

Input cap 100,000 tokens; target output cap 12,288 including reasoning where
applicable; judge output cap 4,096. Per-call timeout 900 seconds, per-answer
evaluation timeout 1,800 seconds, global wall-time limit three hours from dispatch.
Reserve $20 incremental planning liability. Retained conservative planning prices
of $0.25/M input and $0.75/M output give a $17.401248 generation/judge maximum.
Count billing remains unknown with zero planning allowance, not asserted free.
These limits are not provider-enforced billing guarantees. Record missing usage
subtotals, receipts and any uncertainty; saved results incur no new calls.

Stop globally on execution, accounting or integrity failure, elapsed-time expiry
or exhausted cap. Preserve every dispatched request, raw response, receipt and
failure, including unavailable planned slots. No cherry-picking or score-triggered
expansion. Verify credential presence without revealing values.

## Artifacts, validation and review

External namespace: pipelines/brisbane_baylands/task_11/validation_11d15_20261019.
Bind immutable contract, prompts, source seals, implementation and all 36 identities
before dispatch. Adapt the proven 11D.14 runner and native transport; no new
framework. Reuse its reference separation, source binding, count/usage joins and
exact native-request replay. Include nested completion files in the final seal.

Run meaningful offline runner/report tests, make fix, make check and git diff
--check before live calls. Independent preflight checks scope, context delivery,
caps, references and exact configuration. Final independent audits replay every
plan/report, verify native requests and receipts, and review answer text and
failure rationales. Manual disagreements remain separate from frozen scores.

Report by model, question and judge A/G/S/C, automatic validity and strict joint
passes; show denominators and missing slots. G is point-level and must not be
confused with answer-level C/S. Show three-repeat consistency and question coverage,
not just overall totals. Inspect conclusion transfer, provenance caveats, unsupported
scope/absence claims and table-reading issues. Retain unflagged substantive errors.
Publish outcome, replayable reports, result pointer and current routing.

## Learning and acceptance

The existing Task 11 umbrella and 11D.12–14 outcomes own methodological guidance:
separate generation from reference-aware scoring, keep identities and raw outputs,
and audit text as well as automated scores. Three repeats provide descriptive
stability evidence on an exposed panel, not a generalization estimate. Shared
overview changes both generation and evaluator context; historical comparisons
cannot attribute causal effects. No new benchmark policy or judge design is added.

Finish with complete coverage or explicitly recorded stopped/unavailable slots and
documented limitations. Preserve the user-accepted working selection; do not claim
all-19 qualification from this run. No remaining 13 development cases, locked-test
or reserved content, judge retuning, stronger models, Task 10 changes or Task 11E.

## Outcome (2026-10-19)

Completed all 36 planned answers with full evaluation and no retries, replacements,
execution failures or unavailable slots. The exact user-accepted focused-check plus
shared-overview configuration remains the working selection. Results support
retaining it with limitations, not declaring the task solved or advancing to 11E.

| Model | A | C conclusion | S support | G points | All checks |
| --- | --- | --- | --- | --- | --- |
| Luna | 18/18 | 16/18 | 18/18 | 63/64 | 15/18 |
| Haiku | 18/18 | 15/18 | 18/18 | 115/134 | 6/18 |

All-checks is the descriptive conjunction of automatic validity and all A/G/S/C
passes, not a substitute for Task 12's final reporting contract. G counts points;
all other columns count answers. All 36 answers passed automatic validation.

| Question | Luna all checks | Haiku all checks |
| --- | --- | --- |
| C041 animals | 3/3 | 2/3 |
| C017 electricity | 2/3 | 0/3 |
| C019 groundwater | 3/3 | 2/3 |
| C014 transportation | 1/3 | 0/3 |
| C037 wetlands | 3/3 | 2/3 |
| C056 flooding | 3/3 | 0/3 |

Luna passes five of six in each repeat, with different failures. Four questions
pass all three repeats; electricity passes twice, transportation once. Thus Luna
has at least one full pass for every question, but no single repeat passes all six.
Haiku passes 2/6, 3/6 and 1/6 across repeats and adds no question coverage beyond
Luna. Every planned output remains in the report; this is not best-of selection.

Compared descriptively with the saved neutral V6b baseline, Luna all-checks rises
from 8/12 (66.7%) to 15/18 (83.3%); C rises from 9/12 to 16/18. Haiku all-checks
remains 33.3% (4/12 to 6/18), while C rises from 7/12 to 15/18. Luna G remains high
(47/48 to 63/64), and Haiku G is similar (77/89 to 115/134). Unequal small unseeded
repeat counts, two combined additions and shared judge context prevent causal
attribution. All six are repeatedly exposed development questions.

Full independent text/source/judge review separates observed gains from score
limitations. Neither model expresses project-applicability doubt on C041 in any
of its three repeats. Both transfer the electricity storage assumption into the
conclusion in two repeats and leave it in support in one. This is promising but
inconsistent. All S passes therefore do not establish sufficient conclusion
coverage. Luna's remaining frozen failures are the C017 conclusion omission,
C014 incomplete scope/regional-growth coverage, and C014 unsupported contrast in
a supporting point. No clear Luna table-reading error was observed.

Haiku still produces unsupported absence/ambiguity caveats and citation-scope
errors. Examples include electricity opt-out ambiguity, a reversed grid-supply
claim, groundwater-model scope inferred from closure-plan design gaps, transport
citations missing the separate interchange basis, and flood-event/freeboard scope
errors. Some C014 regional-growth judgments and C041 enforcement-caveat judgments
remain disputed. Manual concerns also catch passing answers' cat-to-feral-animal
scope expansion and missing conclusion citations. Preserve all original scores;
manual review does not relabel results.

The overview has a documented edition limitation: fixed-six C014 P4/P5 originate
in feir_appendix_f1 despite its draft-document framing. No K2 passages occur in
this panel, but its separate catalog exception remains relevant to wider use.
No prompt, source metadata, reference or judge core was changed for this run.

Validation: make fix and make check passed (4,166 passed, one skipped, 71 warnings),
16 independent runner/report tests passed before calls, and git diff --check passed.
A reporting-only offline NameError was repaired and documented before freeze.
Final native audit replays all 36 plans/reports and 342 receipts, verifies all 23
source passages unchanged, and verifies the complete historical 11D.9 and 11D.14
seals (11,868 and 716 files). Independent full-answer reviews retain exact
candidate/run/repeat/point identities and quoted evidence.

Accounting: 36 generation, 306 judge and 342 count calls; zero retries or missing
cost receipts. Estimated generation/judge cost $0.258339835, with 1,843,684 effective
input tokens and 199,855 output tokens. Eight receipts lack reasoning subtotals;
no count/usage differences were found. Counting charges remain unknown. The $20
reservation was a planning bound, not a provider billing guarantee.

The [result pointer](../../docs/specs/task11d15_result.json) binds reports, historical comparison, full manual reviews,
receipts, offline validation, native audit and the final artifact seal. No other
13 development questions, locked/reserved content, stronger models, judge retuning,
Task 10 mutation or Task 11E execution occurred. Stop this authorized experiment
here; any further prompt revision or broader run needs its own bounded scope.
