# Task 07A screening UI

`task07a_screening_v1.xml` is the native Label Studio form. The approved project
uses Community 1.23.0 and all 50 selected comments, with no model predictions.
Kyle approved the one-case interface before the remaining 49 were imported.
The sample and source inventory remain unchanged. All 50 labels are now exported;
see [Task 07A](../../tasks/sprint2/07a_screen_pilot_candidates.md#completed-human-screening-export).
Keep this completed project unchanged during future linking repairs.

## Design

Comment and direct response sit beside one another when space permits; narrow
reading areas stack them. The fit card stays beside the reading area. Linked
responses and citation limitations expand below the main pair. Original text
and PDF page links remain available. Figure extraction is separated from prose;
this presentation does not make visual evidence eligible. Great/OK/Skip is
required; Skip reasons are optional, fixed choices. No typing is required.

Use Label Studio's **Label All Tasks** view, not the data-table preview, for
reading. Collapse its unused right-hand region-panel group using its chevron;
this preference is remembered in the preview browser. Native Submit saves the
rating; the native Postpone action leaves the case pending.

## Current projects and archived history

After user-authorized cleanup on 2026-09-28, only projects **25, 29, 30, 33, 35,
36** remain live. See [current review queues](#task-07d-evidence-review-queues).
Other project links below describe historical trials and no longer open live
projects. Their configurations, full task snapshots, exports, annotations and
drafts are preserved in the cleanup backup, alongside the earlier sealed artifacts.

The backup is under the artifact root at
`pipelines/brisbane_baylands/task_07_pilot/maintenance/label_studio_cleanup_20260928T192837Z/`.
It contains a verified full `before.sqlite3` database backup, per-project exports,
before/after current-task snapshots, and a checksummed manifest. Treat the database
backup as sensitive local data; it contains account/settings data as well as reviews.
Restore into a separate isolated instance for historical inspection rather than
replacing the active database and losing newer reviews.

## Isolated local trial

Under the configured `ER_COMMONS_DATA_ROOT`:

```text
pipelines/brisbane_baylands/task_07_pilot/07a/label_studio_trial/
  runtime/                  # separate Label Studio 1.23.0 environment
  data/                     # separate SQLite database and media
  assets/source.pdf         # link to the unchanged Volume 4 PDF
  local_credentials.json    # local-only account; mode 0600, never tracked
  trial_task_v3.json         # one imported case, no ratings
  qa_*.json                 # test annotations/exports, not curator decisions
  ui_preview.png            # tested interface
```

Label Studio listens only on `127.0.0.1:8097`; its source-PDF server listens only
on `127.0.0.1:8098`. The existing global Label Studio data directory was not
used or migrated. The trial's `server.pid`, `assets.pid`, and logs identify its
own processes. Do not stop unrelated Label Studio processes or delete projects.

If a restart is needed, from a shell with `ER_COMMONS_DATA_ROOT` set, run these
in separate terminals (only when these ports are free):

```bash
trial="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_07_pilot/07a/label_studio_trial"
LABEL_STUDIO_BASE_DATA_DIR="$trial/data" \
LABEL_STUDIO_DATABASE="$trial/data/label_studio.sqlite3" \
COLLECT_ANALYTICS=false SENTRY_DSN= FRONTEND_SENTRY_DSN= \
DISABLE_SIGNUP_WITHOUT_LINK=true \
"$trial/runtime/bin/label-studio" start --no-browser \
  --internal-host 127.0.0.1 --port 8097 --data-dir "$trial/data"
```

```bash
trial="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_07_pilot/07a/label_studio_trial"
"$trial/runtime/bin/python" -m http.server 8098 --bind 127.0.0.1 \
  --directory "$trial/assets"
```

Both isolated servers were restarted at reduced process priority for human
review. No additional packages were installed. The saved screenshot remains
available for lightweight reference.

When running, the preview is at
[the isolated project](http://127.0.0.1:8097/projects/1/data?tab=1&labeling=1).
The local account is separate from any existing account. No global password
was read or changed.

## Preparation and review boundary

`python -m er_commons.pilot_screening` requires an explicit sample root, comment
ID and new output path. It writes exactly one task and has no import/API or
bulk mode. Optional `--source-base-url` supplies the source PDF URL. It verifies
pinned input hashes, escapes source HTML, retains complete response IDs, and
keeps exact original extraction alongside conservative reading cleanup.

The UI trial tested native JSON export, stable IDs, multiple skip reasons,
Skip without reasons, and switching from Skip to Great. Conditional reasons
are omitted from the saved Great result. Temporary test annotations were
exported separately and cleared from this one trial task. They are not human
screening decisions. Later production export conversion must still validate
fit/reason consistency and bind decisions to this sample and the final form.

Maintainer guidance:
[isolated data directory and port](https://labelstud.io/guide/start),
[Choices](https://labelstud.io/tags/choices),
[HyperText](https://labelstud.io/tags/hypertext),
[Style](https://labelstud.io/tags/style), and
[JSON export](https://labelstud.io/guide/export).

The approved full import is recorded in `screening_import_manifest.json`, with
50 task/comment mappings and the form hash. `screening_50_tasks.json` retains
the complete import data; `screening_initial_export.json` records the unrated
handoff. Do not repeat the 49-case import or remove human annotations. Report
citations are listed with resolution status; direct cited-report PDF navigation
is not implemented in this approved form.


## Verified replacement after Task 07A.1

Use [project 2](http://127.0.0.1:8097/projects/2/data?tab=1&labeling=1), titled
`Task 07A.1 · Repaired links · 50 saved decisions`, for the repaired context.
All 50 original annotations are complete and verified. Project 1 remains
unchanged historical evidence; the isolated servers and source-PDF URL are the
same. No global Label Studio projects were modified.

The [07A.1 outcome](../../tasks/sprint2/07a1_repair_response_list_links.md) owns
migration identity, validation and the five optional follow-up cases. The fixed
replacement sample and checksummed export/map are under
`pipelines/brisbane_baylands/task_07_pilot/07a1/sample_repaired_v1/` and
`pipelines/brisbane_baylands/task_07_pilot/07a1/migration/` respectively. Original
annotation metadata remains distinct from new Label Studio IDs/timestamps.
Do not rerun imports blindly: the recorded driver exports and reconciles by
comment ID before appending only missing tasks.


## Task 07B one-case question review

`task07b_questions_v1.xml` is the separate three-field comment-question form.
[Project 3](http://127.0.0.1:8097/projects/3/data?tab=2&labeling=1) now contains all
eight selected comments. O-Joint-19 (task 101) is approved unchanged in
annotation 105. All eight reviews are saved: seven approved and I-CJ-4 unclear
and skipped. The [final export](../../tasks/sprint2/07b_review_comment_questions.md#final-reviewed-export)
is validated. It uses the same approved
form, isolated server, and local account. Preserve screening projects 1 and 2,
and the first human review in project 3.

The original comment and initial proposal are read-only; the numbered list is
prefilled through a prediction and remains editable. Source line wrapping is
visual only. Review status has no default. Use native Submit to save; after a
saved review, Previous task reopens the completed case for editing. Unclear or
Needs context holds the case from advancement. The source note remains visible. Nonempty drafting notes appear inside
**Initial proposal · unchanged**; expand that panel for M-OSEC-273. Such notes
do not assign a human status.

Use the shared prediction `model_version` `task07b.questions.v1` and set the
project's selected `model_version` to that exact value. Per-case proposal
versions remain in `original_proposal`. The normal labeling queue filters
predictions by this project setting; a task-detail preview alone cannot verify
prefill. Never clear an existing draft to force a prediction to appear.

One-case preparation uses:

```bash
uv run python -m er_commons.pilot_questions prepare \
  --drafting-dir "$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_07_pilot/07b/o_joint_19_trial_v1/drafting" \
  --output /path/to/new-trial-import.json
```

The helper verifies packet hashes and proposal identity, accepts no response
context, and refuses to overwrite its output. It does not import into Label
Studio. The historical external `ui/trial_driver.py` handles only the original
one-case trial and must not be rerun against the expanded project. The saved
`remaining_seven_20260924_v1/import/load_seven.py` records the bounded batch
import, reconciling live stable IDs before appending missing cases. Stop using
that import driver once human review starts; preserve all later annotations.
Reviewed exports must remain no-clobber.

For export normalization, supply the native task and its saved annotation to
`normalize_review(task, annotation, expected_task=build_trial_task(drafting_dir))`.
The trusted comparison catches changes to original text, spans, and proposal.
Do not treat a native completed-task count as 07B acceptance: the native form
can save an empty Approved list, which this validator rejects. Empty unresolved
records remain valid. No automatic progression or model backend is installed.

The [07B outcome](../../tasks/sprint2/07b_review_comment_questions.md#one-case-trial-outcome)
owns tests, temporary annotation cleanup, preservation checks, and external
artifact locations. At the trial handoff there were zero human annotations;
Kyle has since saved approved annotation 105. QA exports remain separate test evidence. Never rerun
the historical QA cleanup against the accepted human annotation.


## Task 07C one-case claim review

[Project 4](http://127.0.0.1:8097/projects/4/data?tab=3&labeling=1),
`Task 07C · O-Joint-19 · Claim review`, retains its trial title and uses
`task07c_claims_v1.xml` for all seven cases (tasks 109–115). The UI is approved;
all seven cases are now approved and exported (31 final blocks). Projects 1–3,
the sealed drafting packet, returned proposal, and reviewed exports are protected.

The left panel contains Q1–Q3 and the complete individual/general response texts
plus footnote 75. Scroll within the source panel; short passage references and
pages match the editable list. Expand the original proposal for its unchanged
quotations, or the other panels for coverage notes and source limits. Source
line breaks are retained to avoid flattening extracted tables.

The right panel shows two preserved ambiguities and nine prefilled argument blocks.
Supporting details stay with their argument. Each
block starts with `C001 | Q1,Q2 | R01-P01,R01-P02`, followed by the claim wording.
Separate blocks with a blank line; internal paragraph breaks are allowed because
new C-ID headers define block boundaries. Use an unused C-number when adding or splitting,
`unassigned` for no concern link, and update source references when changing
attribution. The original proposal stays unchanged. Export binds edited claims
to full source passages, not automatically to the original quotation selections.
Exact per-claim split/merge ancestry is not collected; whole-proposal provenance
and final edits remain available.

Review status is required and has no default. Approval concerns faithful,
relevant extraction, not truth or evidence support. Unclear and Needs context
retain partial work but cannot advance. Source ambiguity can remain faithfully
represented; choose an unresolved status when interpretation itself is blocked.
Native Submit saves, and Go to Previous Task reopens a completed case. A reload
of a completed queue may show no remaining tasks; use Go to Previous Task.

Preparation (explicit paths, fresh output only):

```bash
uv run python -m er_commons.pilot_claims prepare \
  --drafting-dir /path/to/sealed/drafting \
  --proposal /path/to/returned_proposal_v1/proposal.json \
  --output /path/to/new-trial-import.json
```

Use the shared prediction `model_version` `task07c.claims.v2` and select the same
version in project settings. Verify prefill through the actual labeling queue;
a preview is insufficient. Never delete existing drafts to expose a prediction.

Normalize each saved annotation with
`normalize_review(task, annotation, expected_task=build_trial_task(drafting_dir, proposal_path), export_lineage=unique_export_identity)`.
The expected task must come from verified local inputs, not from the export.
Export rejects empty/malformed approved lists, unknown or duplicate IDs, invalid
references, and footnote-only claims. The native form can still save such invalid
approvals, so native completion counts alone never establish acceptance.

The external trial `ui/` directory contains the bounded execution driver,
preservation snapshots, QA exports, queue checks, and screenshots. QA annotation
113 was removed after exact evidence matching; no human label existed at handoff.
That completed QA cleanup must never be reused against later reviews.
The [07C outcome](../../tasks/sprint2/07c_review_response_assertions.md#one-case-ui-handoff)
owns validation details and the UI-approval boundary.

Current trial proposal: `returned_proposal_v2/proposal.json`. The 19-claim V1
proposal and its old prediction remain preserved; the project selector shows
only the new nine-block prediction. `ui_v2/` owns this update's snapshots and
actual-queue verification. Use V2 when rebuilding expected task data for exports.
The old `ui/trial_driver.py` targets V1 and is historical; do not rerun it.

Kyle has now approved task 109 in annotation 114, exported as recorded in the
[07C approved-content handoff](../../tasks/sprint2/07c_review_response_assertions.md#approved-o-joint-19-content).
Preserve this human annotation. The case is completed; use Go to Previous Task
if the normal queue has no remaining tasks. The UI is approved and tasks 110–115 now contain the six grouped proposals.
All six prefills and complete source text were verified in the actual queue;
no human annotations were created. Five exact-prefill drafts created by QA
Postpone navigation were preserved separately and removed after matching their
identities and content; all six tasks are pending with no drafts.

Final 07C reviews are complete: annotations 114–120, no drafts or pending cases.
PC-LM-2 has two final blocks after Kyle's edit. Use the
[final handoff](../../tasks/sprint2/07c_review_response_assertions.md#final-reviewed-export-and-learning)
for all seven normalized reviews. Earlier pending-state descriptions above are
integration history; never rerun imports or QA cleanup against saved reviews.


## Task 07C.1 combined review

Kyle approved the revised UI and saved the
[Project 8 · O-Joint-19 combined review](http://127.0.0.1:8097/projects/8/data?labeling=1).
Preserve task 119, annotation 123. Its validated export is under
`07c1/reviews/o_joint_19_approved_20260925T205026Z/` within the Task 07 pilot
artifact root: 13 retained claims, no substantive removals, four unused-slot
removal actions, 10 candidate evidence claims, and no unclear claims. This is
the first accepted case. Evidence execution is separate from review completion. Project 9 is now reviewed and exported: four approved, I-EA-2 unclear.
I-CF-4 is now approved (annotation 129); all seven outcomes are exported in
`07c1/reviews/seven_case_export_20260925T211401Z/`. Six cases are approved;
I-EA-2 remains an explicit Unclear stop. The 57 retained claims include 31
candidates for future evidence review. See the final task outcome for the
provenance of the assistant-cleared stale C025 target.

Project 4 and its seven approved 07C reviews remain unchanged. Projects 5–7
are marked QA and must never supply human decisions. The verified remaining
queues originally contained 44 proposals across six cases:

- [Five shorter cases · Project 9](http://127.0.0.1:8097/projects/9/data?labeling=1):
  O-GGBA-2 (task 120), M-OSEC-273 (121), SA-Caltrans-33 (122), PC-LM-2 (123),
  and I-EA-2 (124).
- [I-CF-4 · Project 10](http://127.0.0.1:8097/projects/10/data?labeling=1): task 125,
  with its complete longer response context and matching slot capacity.

Project 9 annotations 124–128 are exported under
`07c1/reviews/five_case_export_20260925T210734Z/`: four approved outcomes and
I-EA-2 unclear, with 17 retained claims and no validation errors. The PC-LM-2
restoration was explicitly presented and is now approved. I-EA-2 remains a case
stop even though its C004 was relabeled not relevant.

Project 10 now presents six direct, six supporting, then 15 not-relevant claims,
followed by four blank slots. Ordering is fixed from the proposal; changing a
relationship does not move a card mid-review. IDs remain unchanged, so their
numbers are intentionally nonconsecutive on screen. Only XML card order changed;
all task data, native controls and saved reviews remain identical. Do not rerun
the old import configuration over this approved presentation change.

Review the wording, relation and targets in each card. Direct links use Q IDs;
supporting links use C IDs. Leave targets blank for Not relevant and Unclear.
Expand the card's model panel for rationale, initial wording, exact quotations
and prior-edit notes. Not relevant retains a claim; the removal checkbox deletes
an extraction mistake or duplicate. Repair dependent targets after removal.

Open Original comment for its complete text. Reviewed concerns and the full
response reader remain beside the claims. The two readers scroll independently.
Native autofocus may open the claims pane near its last prefilled field: scroll
that pane to C001 to start. Text boxes can be resized for longer arguments.
Unused addition slots need no action: leave every field blank. A removal click
on an empty addition slot is retained as `unused_slot_removals`, not a deleted
substantive claim; selected labels and other native fields remain preserved.
Save partial work as Needs context. Native
Submit/Update saves asynchronously; wait for completion before exporting. After
completion, Go to Previous Task reopens the saved review.

The [versioned contract](../../docs/specs/claim_relevance_review_v1.md) and
[task outcome](../../tasks/sprint2/07c1_review_claims_and_relevance.md#final-reviewed-export-and-replacement-handoff)
own readiness, validation and provenance. The native form can save structurally
invalid links; normalized export rejects invalid approvals. Faithfully unclear
claims can remain in an approved case but are held from evidence work.

Prepare one task with `python -m er_commons.pilot_claim_relevance prepare`, using
explicit `--drafting-dir`, `--predecessor-proposal`, `--proposal`, `--output`, and
optional `--slots`. Generate the matching form with
`python -m er_commons.pilot_relevance_form --slots N --output /new/form.xml`.
Both commands refuse overwrites. The shared prediction selector must be
`task07c1.claim_relevance.v1`. Bind the generated form and trusted prepared task
in the execution manifest. Normalize native annotations against that trusted
rebuild using `normalize_review(..., export_lineage=...)`.

For overflow, preserve native exports and drafts first, prepare a larger task
with `expand_task`, and create a separate project with a larger generated form.
Import/rebind the preserved native annotation explicitly; `migration` is provenance,
not an automatically loaded annotation. Compare every old field, claim identity
and reviewer binding after reload. Never clear a draft or overwrite the old form
to make space. The external `overflow/` evidence demonstrates 17-to-21-slot
migration with edited text, relationships, an addition and removals intact.


## Task 07D evidence-review queues

All 31 claims (including the three SA-Caltrans-33 prototype claims) are submitted.
The [final case exports](../../docs/specs/task07d_final_result.json) are complete
with accepted MVP warnings. These five projects hold the 28 expansion reviews:

| Case | Claim tasks | Review |
| --- | ---: | --- |
| I-CF-4 | 11 | [Open project 36](http://127.0.0.1:8097/projects/36/data?labeling=1) |
| M-OSEC-273 | 2 | [Open project 30](http://127.0.0.1:8097/projects/30/data?labeling=1) |
| O-GGBA-2 | 2 | [Open project 29](http://127.0.0.1:8097/projects/29/data?labeling=1) |
| O-Joint-19 | 10 | [Open project 35](http://127.0.0.1:8097/projects/35/data?labeling=1) |
| PC-LM-2 | 3 | [Open project 33](http://127.0.0.1:8097/projects/33/data?labeling=1) |

Read the exact claim and reviewed question first. Source excerpts are on the right;
reviewer notes and controls are on the left. Judge each displayed source, then use
**Overall outcome for this claim**. Submit advances to the next claim. Citation repetition across claims is intentional;
the final case export deduplicates canonical units and retains support over context.

Narrative citations stop at the next actual section heading. Complete tables retain
notes; unresolved boundaries are gaps rather than invented units. PDF links use
physical pages, separate from printed labels. Figure links point to source locations;
they do not supply model-interpreted figure evidence. Reviewer notes never form part
of the quoted source. Use Unresolved and explain when sources cannot settle a claim.

I-CJ-4 project 26 is an archived
historical catch-up queue: Kyle excluded I-CJ-4 again on 2026-09-28, so no further
review is required. Its history is preserved. [SA-Caltrans-33 project 25](http://127.0.0.1:8097/projects/25/data?labeling=1)
has three submitted prototype reviews. Kyle clarified task164’s partial source
as context in a separate export overlay; native judgments remain unchanged.

`pilot_evidence.prepare_claim_tasks` validates packets and anchors;
`build_claim_form` renders the shared form; `normalize_claim_review` validates
saved reviews against trusted tasks. Projects 27, 28, 31, 32 and 34 are synthetic
QA only. Earlier QA and human prototype projects remain preserved.
See the [queue handoff](../../docs/specs/task07d_remaining_result.json),
[07D task](../../tasks/sprint2/07d_discover_and_review_evidence.md) and
[record contract](../../docs/specs/evidence_review_v1.md) before changes.


## Task 08B shared candidate selection

`task08b_selection_v2.xml` is the current qualified shared form; the
[selection contract](../../docs/specs/task08b_selection_v2.md) owns selection-only
advancement, schemas and export validation. Use health-risk
[project 41](http://127.0.0.1:8097/projects/41/data?tab=40&labeling=1).
Health-risk project 41 is complete: M-OSEC-241 and O-Joint-44 selected, 243/244
excluded; see the [validated result](../../docs/specs/task08b_health_risk_result.json).
Project 39 is superseded; it has no submitted annotations and its one unsaved
draft remains preserved without migration. Projects 37, 38 and 40 are synthetic
software qualification, not human dataset reviews.

Read the original comment and scroll through complete linked responses. Save a
selection and reason; notes are optional except for Other. Source/eligibility
concerns may go in the reason or notes. The maximum is three selections, and fewer
are welcome. No eligibility or stopping field appears. Leave unanswered candidates
untouched. When requesting export, confirm in chat that you have finished.
Selection is the only 08B human label gate; evidence-based eligibility remains at
08E. All removed warning/ranking material remains in the
underlying provenance; no new narrative or reranking was generated.

## Task 08C wording review

`task08c_wording_v1.xml` is the preserved historical comment-only wording form.
Current 08C review uses [versioned chat review](../../docs/specs/task08c_chat_review_v1.md);
this form is no longer required and project 44 is not the chat approval authority. It shows the
original comment, applicable existing comment-source warnings, editable proposal,
and explicit approval/rejection/unresolved controls. The
[shared specification](../../docs/specs/task08c_wording_v1.md) owns preparation,
qualification and exact saved-text export. Predictions prefill wording only;
never prefill a human decision. Synthetic projects remain separate from dataset
review, and no dataset question freezes until the curator saves its approval.

## Task 08D health-risk claim review

[Project 49 — health-risk claims](http://127.0.0.1:8097/projects/49/data?tab=48&labeling=1)
is prepared for M-OSEC-241 and O-Joint-44 only. Shared
[`task08d.claim_review.v2`](../../docs/specs/task08d_claim_review_v2.md) keeps
frozen questions unchanged and shows direct claims first. Review each current
claim's text, quoted source, relationship, target and explanation, then choose
Approve, Reject or Unresolved. Approving means faithful response assertion and
relevance, not truth or evidence support. Leave unused addition cards blank.

Use the question-parts panel to inspect unanswered scope. Mark the whole case
Ready only after resolving essential gaps and confirming the current links after
all edits; otherwise save Unresolved or Stop with a note. All unresolved claims
hold the case. Click outside an edited text box before Submit/Update so the native
form registers the edit; wait for save completion. Native autofocus may leave the
claims pane scrolled down: scroll it to the first claim to begin. The source and
claim panes scroll separately. Tell this chat when saved decisions are ready for
export. Projects 45/46 contain only synthetic qualification decisions.

V2 removes the source-passage ID input and enlarges claim/explanation editors.
Exact source anchors remain fixed in trusted records. Project 47 and its unsaved
draft are preserved without migration; project 48 is source-free v2 qualification.

Task 08E source-free qualification uses `group_evidence.claim_form` around the
maintained evidence controls and a separate `group_evidence.eligibility_form`.
Generated form snapshots are versioned and hashed in the external qualification
run. See [08E preparation](../../docs/specs/task08e_evidence_review_v1.md).
These synthetic projects never constitute health-risk evidence or human approval.
