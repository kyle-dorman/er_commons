# Task 08B — Select one group's candidates

Status: **All 42 groups explicitly closed; 57 saved Selected candidates exported.**
Parent: [Task 08](08_curate_grouped_benchmark.md).

## Abstract

Kyle reviews original comments and complete linked responses in the saved 08A
order, selecting promising cases. The 2026-10-01 closeout amendment below
accepts all saved Selected candidates, including more than three per group. Selection and its reason are the
only 08B human gate to 08C. Evidence-based eligibility remains a later human
review at 08E. Use a separate group-specific project; no labeling belongs in the
coordination chat.

## Goal

Select useful candidates without quotas, model acceptance, question rewriting,
or treating unanswered candidates as rejections.

## Inputs

- Accepted [08A](08a_rank_group_candidates.md) packet and saved order for one group.
- [Human review process](../../docs/response_comment_human_review_process.md),
  [Decision 005](../../docs/decisions/005_task08_grouped_question_selection.md),
  and [Sprint 2 criteria](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#task-08-eligibility-clustering-and-split-boundary).
- [Shared v2 contract](../../docs/specs/task08b_selection_v2.md), umbrella provenance
  contract, [artifact rules](../../docs/data_artifacts.md), and
  [architecture](../../docs/architecture.md).

## Outputs

- One group-specific project using `task08b.selection.v2` and process revision
  `task08.selection_gate.v2`.
- Versioned selections/reasons, reviewed skips/exclusions, unresolved decisions,
  untouched candidates, and a separately saved chat completion confirmation.
- Validated full-inventory export and selected-case coordination handoff, retaining
  response context and rationale separately from future comment-only 08C inputs.

## Research / learning checkpoint

Inspect maintained Label Studio [configuration](https://labelstud.io/guide/setup.html)
and [export](https://labelstud.io/guide/export.html) guidance. Native selection
controls plus full-inventory export preserve unanswered cases without a custom
stopping UI. Selection does not establish final eligibility; the later evidence
review remains. Test actual queue/save/export behavior, not just previews.

## Plan / spec requirement

1. Reuse and verify sealed 08A input/proposal identities and saved order. Do not
   rerank or regenerate 08A. Display original comment and complete linked responses
   including source footnotes. Preserve all existing provenance underneath, but
   do not display or generate narratives for removed warning/advisory sections.
2. Use shared versioned input/decision schemas, form and validators. Record only
   selection, selection reason and optional notes; no provisional-eligibility or
   continue/stop controls. Relevant source/eligibility concerns can be reasons.
3. Reconcile every saved annotation against the complete inventory. Leave
   unanswered candidates unreviewed. Keep drafts, cancellations, reviewed skips,
   exclusions and unresolved decisions distinct. Enforce at most three selected
   candidates; fewer are welcome. No automatic downstream backfilling.
4. When export is requested, confirm in chat that Kyle has finished. Bind the
   actual statement and reviewer/time/chat provenance to the current saved export.
   Never infer completion from selection count or queue exhaustion.
5. Export only after human review. Explicit selection is the single label gate to
   08C, with finalized export requiring chat confirmation. Preserve nonselected
   records and unresolved outcomes. Do not begin 08C in this chat.

## Authorized v2 implementation plan — 2026-09-30

Kyle requested a new project before saving annotations. Verify and preserve the
old project's state; retain its one unsaved draft without migration. Preserve v1
artifacts. Revise the reusable shared form, schemas, adapters and active process
docs. Independently review changed validation. Qualify v2 using separate source-free
fixtures through actual queue, source display, save/reload and all-task export.
Create the new blank health-risk project only after qualification, mark project 39
superseded, then update current routes and batch register. Include both template
and process revisions in the eventual coordination handoff.

Use fresh `task_08/health_risk/08b/selection_v2/` and
`task_08/qualification/08b_selection_v2/` namespaces beneath
`ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/`. Other groups and sealed
historical artifacts remain untouched. No paid/model execution is needed.

## Validation and acceptance criteria

- Exact saved order and complete unchanged comment/response/footnote display.
- Removed sections and controls absent; no imported selections or predictions.
- Saved source-bound decisions reproduce in native export, with reviewer/time IDs.
- Strict full-candidate closure, accurate unanswered status, maximum three selected.
- No advancing handoff without chat completion confirmation; only explicit selected
  cases advance. Later evidence eligibility remains required.
- 08C can construct strictly comment-only inputs without response or rationale.
- Applicable `make` checks and `git diff --check`; report the three historical
  Task06G commit-pin failures separately from current checks.

## Review pass

Independently check source completeness, human/model separation, removed controls,
chat-confirmation binding, full-inventory reconciliation, and export fidelity.

## Non-goals

Question rewriting, 08C execution, eligibility acceptance, filling quotas,
backfilling, human selection during setup, clustering, answer drafting, or benchmark splitting.

## Historical v1 preparation

V1 qualified the original four-candidate project 39 with no submitted annotations.
Its first-pass eligibility and stopping controls are superseded by the explicit
v2 process amendment. Preserve its source, proposal, form, code snapshots,
qualification, initial exports and unsaved draft in place. The original readiness
record is copied into the v2 namespace as `predecessor_result.json`; the
[v1 specification](../../docs/specs/task08b_selection_v1.md) is historical only.
V1 validation recorded 2,863 passed, 1 skipped and the three historical Task06G
commit-pin failures. Current v2 checks are recorded separately.


## V2 readiness — before human review

The shared `task08b.selection.v2` form and `task08.selection_gate.v2` process are
qualified. Use [health-risk project 41](http://127.0.0.1:8097/projects/41/data?tab=40&labeling=1).
Project 39 is marked superseded; its zero submitted annotations and one unsaved
draft remain preserved, with no migration. The new project has four blank tasks
in unchanged saved order. Browser verification confirmed complete original text,
all linked responses/footnotes, removed sections absent and no prefilled decisions.
Existing provenance fields match v1 exactly; 08A was not reranked or regenerated.

Synthetic project 40 tested selection, skip, exclusion, unresolved and unanswered
cases through the actual queue, save, reload and export. An unconfirmed export
advances no cases; the synthetic confirmed export advances only the selected
case, preserving the unresolved and unanswered records. Independent review found
no actionable issues. `make fix`, formatting, lint and types passed; all 81 targeted
tests passed. Full checks reported 2,887 passed, 1 skipped and the same three
historical Task06G commit-pin failures.

The [current readiness record](../../docs/specs/task08b_health_risk_result.json)
binds the exact artifacts and coordination-readiness record. Wait for Kyle's
review; at export confirm he has finished in chat. The eventual final coordination
handoff must include both template/process revisions, saved completion statement,
exact native export/input bindings, current/superseded project IDs and all candidate
dispositions. No accepted selections have been exported and 08C has not started.


## Final health-risk outcome

Kyle confirmed completion in chat: “ok done with labeling. chose just 2 tasks”.
The maintained exporter validated the complete native export from project 41,
with all source/input/form/import identities retained:

| Candidate | Saved selection | Saved reason |
| --- | --- | --- |
| M-OSEC-241 | Selected | Clear scoped concern |
| O-Joint-44 | Selected | Clear scoped concern |
| M-OSEC-243 | Excluded | Weaker candidate |
| M-OSEC-244 | Excluded | Weaker candidate |

All four are reviewed: two selected/advancing and two excluded, with zero skips,
unresolved decisions, unanswered candidates, drafts or cancellations. The last
reviewed rank is four; completion is bound to the chat statement, not inferred
from that position or the selection count. No provisional eligibility was added.

The [completion record](../../docs/specs/task08b_health_risk_result.json) binds
`selection_v2/exports/review_v1/`: native export, normalized decisions, completion
confirmation, separate restricted provenance, minimal handoff, checksummed manifest
and completion seal. Independent read-only review reproduced the decisions
byte-for-byte and verified the two selected identities. A final live check found
saved decisions unchanged. Documentation passed `git diff --check`.

The handoff includes `task08b.selection.v2` and `task08.selection_gate.v2`,
current/superseded project references, exact artifact hashes and complete counts.
Response context and screening reasons remain outside the minimal handoff in
separately referenced provenance. No wording packet or question rewrite was
created. A separately requested 08C must extract only selected original comments
and comment-source warnings before a fresh wording chat. Later evidence-based
eligibility remains required, and no attrition backfilling is automatic.

The recorded shared-v2 checks remain 2,887 passed, 1 skipped and three historical
Task06G commit-pin failures, with 81 targeted tests passed. Those implementation
checks were not rerun for this export-only completion. No other group was processed
and 08C remains unstarted.

## Authorized remaining-group setup — 2026-09-30

Kyle explicitly authorized shared v2 intake qualification and separate blank
projects for all remaining groups, ahead of later human selection. This supersedes
the original single-group setup scope only. Do not start selection, 08C, other
Codex chats, model ranking, dataset annotations, or commits/pushes.

1. Verify the completed 08A result, pinned index and every indexed artifact;
   independently audit all 42 groups and 606 candidates. Report invalid groups
   separately and continue with valid groups.
2. Qualify named adapter/display revision `task08b.intake.v2` for v1 and v2
   handoffs, including model-ranked and deterministic small groups. Keep the
   shared XML `task08b.selection.v2` and `task08.selection_gate.v2` controls.
   Absent ranking reasons remain absent. Label complete source-page supplements
   accurately as page context rather than footnotes; preserve every source byte.
3. Assess historical prepared queues explicitly: health-risk's original source
   display and replay must remain identical, with its saved form, code snapshots,
   exports, annotations and superseded draft preserved.
4. Inspect live projects and register; reuse exact compatible queues. Create only
   missing projects, with source-bound receipts and saved-order views. Independently
   verify coverage, source display, bindings, blank controls and template identity.
5. Save a compact link/status index and restartable setup receipts under
   `task_08/selection_setup_20260930_v2/`. Merge only relevant 08B register rows
   into the latest bytes, preserving concurrent health-risk 08E updates. Record
   readiness rather than human completion.

Qualification uses source-free synthetic browser/save/export checks in
`task_08/qualification/08b_intake_v2/`, focused tests and repository checks.
Report the three historical Task06G commit-pin failures separately. Maintained
[configuration](https://labelstud.io/guide/setup.html) and
[export](https://labelstud.io/guide/export.html) guidance was rechecked: preserve
existing annotated configurations and reconcile all-task JSON exports.

## Remaining-group setup outcome

The [saved setup result](../../docs/specs/task08b_remaining_groups_result.json)
binds a compact group/count/review-link/status index: **41 newly created, zero
reused, one already completed (health-risk), zero blocked**. All 42 indexed
handoffs and 606 unique candidates passed source/hash validation; the new queues
contain all 602 remaining candidates in their unchanged handoff order.

Shared `task08b.intake.v2` handles model-ranked and deterministic v2 proposals
without fabricated ranking explanations. It associates full response-page context
through pinned source spans, including pages stored under another unit's ID.
Two candidates with no linked responses retain empty source records and a neutral
display; neither is silently excluded. The selection form/process are unchanged.

Native synthetic qualification checked full source display, blank controls,
save/reload, ordered queue, unanswered records and no advancement without explicit
completion. Read-only browser checks covered a large group, a one-candidate group
and empty response context. Existing health-risk tasks replay byte-for-byte.

The initial native setup detected Label Studio's removal of the XML's final
newline before importing tasks. Exact outer-whitespace normalization was tested;
interior form changes still fail. Restart recovered the 27 already-created empty
projects by saved IDs and created the remaining 14, without duplicates or resets.
Receipts retain original creation status, canonical and server form hashes.

Validation: **122 focused tests passed**. `make fix`, formatting, lint and types
passed; final `make check` reported **3,111 passed, one skipped, and only the three
recorded historical Task06G commit-pin failures**. No new test failures remain.
The independent review and exact native/browser evidence are bound in the result.

The register retains completed health-risk and concurrent 08E rows, with prior
bytes saved. Every new row is `prepared_awaiting_human_review`; setup creates no
dataset annotation, selection or completion confirmation. Wait for Kyle's review.
Future exports must reconcile the full inventory and bind his explicit group
completion. No 08C, other Codex chats, sealed-input edits, commits or pushes.

Learning: an upstream page's storage owner is not its complete response
membership. Resolve display coverage through verified source spans; qualify
native server serialization as well as local template bytes before scaling.

## Authorized all-group closeout — 2026-10-01

Kyle confirmed: “i consider all of them finished. can you export and then tell me
how many questions we have. also for some groups i included more than 3 questions
and i think thats ok. so just take everything that is marked Selected”. This
explicit instruction supersedes the three-selection maximum for this closeout.
The preceding message explains that native Label Studio Skip was used for
unpromising candidates. Preserve those native skips separately; do not fabricate
form reasons or turn untouched candidates into rejections.

Plan: capture complete native exports and task details read-only; verify all
source/template/task identities against prepared inventories; qualify the named
`task08.selection_closeout.v1` policy with source-free tests; bind the actual
statement to each group's exact export. Publish all explicitly saved, noncancelled
Selected candidates, with no numerical cap. Native skips and draft-only records
remain distinguishable nonselected states; never promote draft choices. Preserve
old normalizers and health-risk releases so their original byte replay remains
valid. Independently check selection counts and full-inventory reconciliation,
then merge only remaining-group 08B register rows into current bytes. No server
annotation edits, 08C execution, sealed-input edits, commits or pushes.

## All-group export outcome — 2026-10-01

[The saved result](../../docs/specs/task08b_all_groups_export_result.json) binds
42 complete group exports covering all 606 original candidates. There are
**57 selected candidates in 28 groups: 55 newly exported plus the two preserved
health-risk selections**. Four groups exceed the former cap (4, 4, 5, 6); none was
truncated. Other dispositions are 91 excluded, two form Reviewed skip, 46 native
skips and 410 unanswered/unreviewed. No drafts or ambiguous multiple annotations
were present. Fourteen groups close with zero selections.

Three nonselected Other reasons lack notes; retained diagnostics record that
absence without inventing notes or blocking valid selections. Selected records
retain strict reason/provenance validation. Raw native exports and task-detail
responses are saved unchanged; confirmations bind Kyle's actual statement and
the all-selected policy to each exact full-inventory export. The independent
review verifies the 57 selected identities and complete 606-candidate accounting.

Final artifacts live under `task_08/selection_exports_20261001_v1/`, with per-group
`closeout_v1/` handoffs and an aggregate summary/CSV. Earlier partial normalization
files remain diagnostic attempts only; the aggregate summary's references own
the final records. Historical health-risk exports and later-stage work remain
unchanged, and its two cases are counted once. All 41 remaining register rows
close 08B; no server annotations, new wording, commits or pushes.

The new `task08b.handoff.v3` records the closeout policy explicitly; future 08C
intake must qualify it and groups larger than three before preparing strictly
comment-only wording packets. The historical 08C path remains untouched.

Closeout validation: 96 focused tests passed; formatting, lint and types passed.
Full `make check`: 3,162 passed, one skipped, and only the three recorded historical
Task06G commit-pin failures. Independent replay reproduced all 42 final exports
and verified 546 artifact references. `git diff --check` passed.

## Advisory similarity pass — 2026-10-01

Kyle requested an early within-group and cross-group review of the selected
comments for material redundancy. This authorizes advisory comparison before
wording, without applying exclusions or activating final 08G leakage clustering.
The [saved review](../../docs/specs/task08b_similarity_review_result.json) binds
all 57 original comments to the completed selection export. No responses or
proposed answers were used. Independent within-group, cross-group and challenge
reads reviewed the central asks; deterministic enumeration covered 53 within-group
and 1,543 cross-group pairs as a review aid, without a filtering threshold.

There are no verbatim duplicate sets or unconditional exclusions. The strongest
conditional consolidation is to retain O-Joint-54 and consider filtering
M-CSSC-38, provided the retained wording covers overall residential Caltrain-noise
protection rather than vegetation alone. Approval would reduce 57 to 56. Traffic
diversion, sanitary-district flooding, butterfly connectivity and other overlaps
retain distinct requests and should not be collapsed merely for shared topics.
All 57 selections, native labels, batch-register rows and health-risk work remain
unchanged. Final answer/evidence dependencies still require the later 08G review.
