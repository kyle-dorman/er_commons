# Task 15F — Evidence-based reference-conclusion cleanup

Status: batch review complete (2026-10-21); individual human adjudication pending.

## Goal and authorization

The user requested review of all49 label conclusions against their questions and
evidence, without looking at predicted answers. Complete the batch now, then
review suggestions with the user one question at a time. Propose pruning or
affirming details; do not change approved labels before human adjudication.

This is a final reference-conclusion cleanup intended for the methods and a
conclusion-pitfalls appendix. Prior experiments motivated general issue categories,
so this is prediction-excluded review, not an independent blind audit. The lead
has prior exposure. Fresh-context batch reviewers receive only projected labels,
questions, evidence and the general rubric, never predictions, scores or case-level
failure records. All49 labels include the30 originally designated test questions:
preserve original results and disclose their later curation exposure. Original
reserved judge challenges remain unopened; they are a separate population.

## Inputs and review boundary

Use the sealed `task09f_20261014_v2` release selected by its tracked result pointer.
Verify completion and exact case hashes before projecting question, original
label conclusion, label support/qualifications and citation occurrences containing
full source text and tables. Exclude model/edit histories, previous evaluation
records, predictions and synthetic examples. Record the projection and inventory.
Review all49 in fixed case order, not selected by model performance or split.

For each conclusion assess every substantive claim/detail: required direct answer,
necessary why/how explanation, material scope/condition, alternative sufficient
formulation, optional supporting detail, or unresolved/source-limited claim.
Use question semantics and evidence, never a target pass-rate objective. Preserve
real distinctions, list completeness when asked, modality, entity/location,
quantities and conditions where material. Do not shorten away an explanatory
finding or turn qualified evidence into a guarantee. Flag unsupported conclusions
or unanswerable scope rather than inventing an easier answer.

## Artifacts and workflow

Under a fresh external Task15 directory, prepare one immutable review packet per
question and one proposed review per case. Each suggestion contains exact original
conclusion, proposed conclusion (identical for keep), required answer meanings,
detail dispositions, evidence occurrence IDs with exact quotes/locators, rationale,
uncertainty, issue tags and a focused question for human review. All dispositions
remain `pending_user_review`; no new human approval is inferred.

1. Update task routing and downstream dependency plan before batch work.
2. Pin49 projected inputs; use fresh-context bounded reviewers for all cases.
3. Independently challenge proposals in a second pass, checking removed meaning,
   evidence anchors and uncertainty. Retain differing views rather than force edits.
4. Validate exact49 coverage, source/quote bindings, unchanged originals and no
   prediction inputs; publish review browser, summary and result pointer.
5. Save a methods-ready procedure/exposure note, a concrete pitfalls appendix
   draft and an empty human decision journal/queue. Stop for one-at-a-time review.

## Accepted C rules (2026-10-22)

The user accepted the [structured-reference C rules](../../docs/specs/adequacy_labeling_rules.md#3-conclusion-check-c)
after C001 discussion. Use required R points and optional O points, with logically
complete bullets and separate original supporting points. Return one judgment per
reference point and an overall pass/fail; there is no separate additions category.
The policy owns exact statuses and aggregation. C001 text remains a discussed
draft, not a newly published label; accepting rules does not approve all49 labels.

[Task15G](15g_implement_structured_conclusion_judge.md) implements the accepted
prompt/input/output contract and shared Baylands overview. Next: prepare and review
C001-only synthetic candidate answers and test stability before expanding. Provider
dispatch, synthetic regeneration and frozen labels remain unchanged. Preserve all
sealed batches.

## Downstream dependency reset

After user adjudication: publish a new versioned reference release; reconcile any
approved policy/prompt changes; regenerate synthetic C cases against that release
and independently review them; retest/reselect the judge (current preference Luna,
one shot); align the target-generation prompt; rerun fresh generation and all
applicable evaluation/reporting stages; conduct result review and only then write
Task16 methods/results. Earlier Task15 experiments remain historical diagnostics,
not qualification of changed labels. This task does not execute those later stages.

## Learning, validation and limitations

Separate source support from answer necessity: evidence may support a detail that
is not required by the question. Keep alternate sufficient explanations distinct
from exhaustive reference checklists. Source-free C cannot resolve hidden evidence
ambiguity; record that limitation instead of encoding an undocumented requirement.
Use existing source/label contracts and standard JSON/Markdown/HTML artifacts, no
new provider runtime. Automated checks verify exact quotes/IDs and coverage;
independent reasoning review checks substance. Text/table evidence inherits the
release's extraction limits; unresolved visual issues are explicitly flagged.

No API/model-provider calls, predicted-answer reads, reserved challenge access,
synthetic generation, prompt/code/approved-label changes, commits or pushes.
Discussion-informed agent proposals are not human gold. Run `git diff --check`
and artifact validation; no unrelated package tests needed for this review work.

## Outcome

The [result pointer](../../docs/specs/task15f_reference_conclusion_review_result.json)
selects the sealed batch, review browser, methods note, pitfalls appendix and
separate mutable human queue/journal. All49 references received a proposal and an
independent challenge: 27 keep, 4 prune, 17 clarify, 1 evidence hold (C025).
These are proposed dispositions, not accepted changes. Seven scope/support
disagreements remain explicit for user discussion. Four proposals were repaired
after challenge; their initial versions and findings are retained.

Validation passed exact49 coverage, unchanged originals, projected input hashes,
verbatim quote/source-ID checks, current independent-review hashes and distinct
reviewer identities. Source release/case hashes remain unchanged. The browser
renders all49 case views in a JavaScript DOM-stub check; visual layout was not
independently verified. No predictions were opened, provider calls made, or
approved labels changed. Reserved challenges remain unopened; MiniMax excluded.

Next: follow the accepted-rules implementation and C001 pilot sequence above. Record explicit decisions,
accepted wording and unresolved questions in the separate journal before advancing.
The methods draft discloses lead prior exposure and additional curation exposure
of all30 original test references. Human discussion has begun; final label adjudication and downstream stages
remain pending.
