# Task 07C.1: Review Response Claims and Relevance Together

Status: **Complete: seven outcomes exported and validated; six approved cases and one explicit unclear stop.**

## Abstract and goal

Replace the original 07C review workflow with one integrated step: a model
proposes what the official response claims and how each claim relates to the
comment; Kyle reviews the claim and relationship together. A faithful claim
can be irrelevant. A supporting claim can matter indirectly without answering
the comment itself. Neither classification establishes truth or evidence support.

The completed [07C](07c_review_response_assertions.md#final-reviewed-export-and-learning)
remains an immutable previous version, not a failed or deleted review. This task
prepares its replacement for the same seven cases. Evidence verification remains
07D. Do not create a separate answer-requirements review or a second relevance-only
review round: Kyle explicitly chose combined extraction and relevance review.

## Inputs

- Repository checkpoint: `da46803`, completing original 07C.
- Original comment and exact final reviewed concerns from the completed
  [07B handoff](07b_review_comment_questions.md#final-reviewed-export).
- Seven cases: O-Joint-19, I-EA-2, I-CF-4, PC-LM-2, SA-Caltrans-33,
  M-OSEC-273, O-GGBA-2. I-CJ-4 remains excluded.
- Accepted response sources from [07A.1](../../docs/specs/task07a1_final_result.json),
  with full recursive response-to-response closure, source identities, exact
  passages, pages, citations, extraction warnings and unresolved source meanings.
- Prior 07C artifacts under `ER_COMMONS_DATA_ROOT`:
  - `pipelines/brisbane_baylands/task_07_pilot/07c/reviews/seven_case_export_20260924T225154Z/`:
    seven approvals, 31 final argument blocks, including the PC-LM-2 edit.
  - `pipelines/brisbane_baylands/task_07_pilot/07c/o_joint_19_trial_v1/`:
    sealed source packet, detailed/grouped proposals and grouping map.
  - `pipelines/brisbane_baylands/task_07_pilot/07c/remaining_six_20260924_fd06/`:
    sealed packets, detailed/grouped proposals, mappings and integration index.
- Current adapter `src/er_commons/pilot_claims.py`, associated tests, and
  [Label Studio operation notes](../../configs/label_studio/README.md).
  Read architecture/data-artifact docs before implementation or artifact work.

Prior reviewed text is a useful starting point, not evidence of reviewed
relevance. Re-read complete response context to find omitted claims and mixed
arguments; do not simply assign new labels to the 31 blocks without checking.
Do not silently restore previously removed text as if Kyle had approved it.
Any restoration is an explicit new proposal with prior-edit provenance.

## Agreed review semantics

The model proposes all substantive response claims, including claims it judges
irrelevant. It must not filter the candidate list by relevance before review.
Preserve readable argument grouping rather than one item per incidental number.
Split a block when its parts need different relevance judgments or links.
Preserve qualifications, negation, attribution, quantities, time/geographic
limits, commitments and uncertainty. Claims describe what the response says.

Each claim has one proposed relationship:

| Relationship | Required target and meaning |
| --- | --- |
| Directly relevant | One or more reviewed concern IDs; the claim addresses the concern itself, rather than merely sharing its topic. |
| Supporting | One or more other claim IDs; the claim supplies reasoning or context for a relevant claim. |
| Not relevant | No relevance target required; retain it as a response claim outside the comment's scope. |
| Unclear | Preserve uncertainty and a short explanation; do not force a relevant link. |

Give a concise model rationale for each proposed relationship, especially
indirect links and exclusions. Kyle can correct the label and targets without
writing a mandatory rationale. Supporting means the role of the claim in the
response's reasoning, not verified logical or evidentiary support.

Supporting chains may pass through other supporting claims but must ultimately
reach a directly relevant claim and reviewed concern. Reject dangling targets,
self-links and cycles that manufacture relevance. A shared topic alone does not
establish relevance. Retain a genuine circular argument as source content with
an explicit warning; do not silently manufacture a valid relevance chain.

The full recursively linked response text must remain in the model packet and
UI, without a depth limit or silent truncation. Because general responses can
cover many comments, establish an explicit inventory/coverage rule in the brief
implementation plan: unrelated substantive arguments must not disappear merely
because they will be marked not relevant, while headers and repeated wording
need not become separate claims. No target claim count or hard ten-item cap.

## Minimal UI and record contract

One task per case, with original comment, reviewed concerns, complete source
context, and separately editable claim entries. Each entry presents:

- Claim text, exact source passage references and proposal quotations.
- Proposed relationship and editable concern/claim targets as applicable.
- Short model rationale, available without requiring additional user writing.
- A way to remove the entry; a way to add a new claim to the case.

Retaining a claim marked not relevant differs from removing an extraction
mistake or duplicate. Preserve original proposals and final edits in either
case. Claim removal must not silently leave dependent links pointing to nothing.
Keep case-level approved / unclear / needs-context status and an optional note;
no automatic approval. Content approval includes claim fidelity and relevance
mapping, not evidence support or answer adequacy.

Dynamic rows are not a requirement. Kyle accepts a fixed set of editable slots
with unused slots left blank if that is simpler. Blank slots must not become
claims or require labels. Provide a documented way to handle overflow without
omitting claims, forcing mergers, or losing completed edits. The exact layout,
slot count, and target-control design are implementation choices to test.

Define a versioned proposal/review schema before coding. Retain case and concern
identities, source bindings, immutable proposals, relationship targets, stable
claim identities, human edits/removals, annotation/reviewer identity and hashes.
A slot position is not a durable claim identity. Keep model suggestions separate
from human decisions; old 07C approvals cannot stand in for new relevance review.
Define how unclear claims affect downstream readiness without requiring their
removal to approve an otherwise faithfully represented case.

## Preservation and execution boundaries

- Kyle started Task 07C.1 on 2026-09-25, authorizing the brief plan and one-case
  prototype. Kyle approved the revised trial and continuation on 2026-09-25;
  the remaining six cases may now be populated.
- Future execution uses a fresh 07C.1 artifact namespace and a separate Label
  Studio project. Preserve all prior sources, proposals, comments, labels,
  exports and projects, including project 4 and its saved reviews.
- The isolated Label Studio server (8097) and PDF server (8098) were shut down
  after 07C. Consult operation notes before a needed restart; never reuse stale
  PID files as proof of process identity.
- Develop and validate exactly one case before Kyle reviews the revised UI.
  O-Joint-19 is a useful default because its source/context is already understood;
  use another eligible case if it better exercises mixed relevance.
- The old UI approval does not approve this replacement. Do not populate the
  other six cases until Kyle approves the revised trial UI.
- Preserve sealed packets in place. New proposals and revised records receive
  new identities. Do not commit or push unless requested.

## Research / learning checkpoint

Official documentation inspected during this planning discussion:

- [TextArea](https://labelstud.io/tags/textarea): editable text and per-region
  controls; multiple text submissions alone do not prove repeatable paired rows.
- [Choices](https://labelstud.io/tags/choices): single-choice and per-region/item
  controls; validate their association with each specific claim.
- [Configuration](https://labelstud.io/guide/setup): configuration and saved-label
  constraints favor a separate project for this revised schema.

Before implementation, inspect installed Community 1.23.0 behavior and choose
between native annotation controls and fixed slots. Do not promise arbitrary
add/remove paired rows from documentation alone. Avoid a custom frontend unless
simpler native approaches fail the actual required interaction. Preserve a short
learning note explaining the chosen tradeoff and remaining review burden.

## Plan, validation, and review pass

1. Verify input identities and describe the proposed schema, inventory coverage,
   relationship rules, uncertainty handling and narrow UI approach. Use a bounded
   independent review for semantic ambiguity and preservation risks.
2. Prepare one source-complete packet and model proposal that includes claims,
   relevance categories, target links and brief rationales together. Internal
   extraction/grouping passes are fine; they are not separate human review rounds.
3. Build a fresh one-case project. Verify editable text, selected relationship
   values and target links in the **actual labeling queue**, not only previews.
   Compare all displayed source text with the packet.
4. Exercise adding/removing/editing claims, relabeling, supporting chains, target
   changes after deletion, blank slots, overflow, save/reload and native export.
   Check no default case approval and exact source/proposal preservation. Test
   meaningful invalid references, cycles, empty approved records and partial work.
   Keep QA records separate and never clear a human draft to expose a prediction.
5. Run appropriate `make` checks and independent UI/provenance review. Show Kyle
   the tested trial; record explicit approval before six-case expansion.
6. After approval, prepare the remaining six cases, obtain combined human
   claim/relevance reviews, and export all seven outcomes to a new immutable
   namespace. Validate membership, bindings, edit fidelity, relationship integrity,
   unresolved accounting and unchanged prior artifacts/projects.

## Outputs and acceptance

- Versioned combined proposal/review contract, minimal tested UI and adapter.
- One approved UI trial followed by seven reviewed claim/relevance maps or
  explicit case stops, with full source context and complete proposal lineage.
- Validated native and normalized export, manifest, practical review-burden
  notes, and an explicit replacement handoff for 07D. Keep not-relevant claims
  in the export; do not silently include them in the evidence-work queue.
- Update routing only after actual acceptance. Record the old 07C as the preserved
  predecessor; label the new handoff as the replacement. Revise 07D's provisional
  scope from the reviewed output before evidence discovery begins.

## Non-goals

No evidence search or verification, truth labels, independent answer-requirement
exercise, automatic answer-adequacy grading, benchmark decisions, defense writing,
upstream mutation, or destruction of the completed 07C records. Relevance does
not establish what is necessary or sufficient for a complete answer.

## Brief implementation plan (2026-09-25)

1. Verify O-Joint-19's sealed packet, current inventory and final 07B/07C bindings;
   inventory every substantive argument in the complete response closure.
2. Define the [versioned contract](../../docs/specs/claim_relevance_review_v1.md)
   before coding; use independent review for coverage and preservation risks.
3. Add a separate native fixed-slot adapter with stable identities, editable
   relationships/targets, explicit removals, spare slots and preserved overflow.
4. Prepare one fresh proposal/project; exercise actual-queue interactions and
   exports in a separate QA project, and compare prior sources/projects unchanged.
5. Run focused checks and independent review, then hand the tested trial to Kyle.
   Stop before importing the remaining six pending explicit revised UI approval.

## One-case prototype handoff (historical, before Kyle’s review)

The brief plan and versioned contract were recorded before implementation. The
O-Joint-19 prototype is ready for Kyle's revised UI review in
[project 8, task 119](http://127.0.0.1:8097/projects/8/data?labeling=1).
It contains 13 unreviewed combined proposals and four blank addition slots.
No case status is preselected. The trial has no human annotations or drafts;
no replacement approval or 07D handoff is claimed. The other six cases were not
populated. No commit or push was performed.

### Source and proposal coverage

The sealed source packet's complete fragments, approved 07B concerns, recursive
response closure and all eight intra-volume mentions were revalidated. The
07B/07C export manifests and current inventory pointer/seals match their bindings.
Two responses, eight response passages and supplemental footnote 75 are retained
in full. No source PDF was changed or evidence search performed.

The fresh model proposal has one direct, five supporting, three not-relevant and
four unclear claims. General Response 3's energy and Bayshore traffic arguments,
absent from the prior nine-block extraction, are explicit new proposals. The
comment's displacement context makes the scope of Q3 uncertain for VMT/GHG
arguments; this is exposed for human review. These labels are not findings about
truth, evidence or adequacy. All nine prior O-Joint-19 reviewed texts match their
old proposals, so no removed human wording was silently restored.

A separate full-source review found no material omission or fidelity error. Its
coverage-note finding was resolved with passage-specific argument summaries;
headers, referral text, repeated arguments, table notes and footnote attribution
are explicitly accounted for. Exact proposal quotes match unique source substrings.

### Implementation and validation

`pilot_claim_relevance` owns the combined proposal/review adapter;
`pilot_relevance_form` generates the native form at an explicit capacity. The
[versioned contract](../../docs/specs/claim_relevance_review_v1.md) owns stable IDs,
removals, partial work, graph rules, uncertainty and overflow. The old adapter
and approved exports remain unchanged.

Validation includes:

- Actual labeling-queue checks for independently editable text, selected
  relationships and targets, exact source text (browser CRLF normalization only),
  empty unlabeled spare slots, and no default case approval.
- Separate QA edits, an addition, two removals, relabeling, a supporting chain,
  a broken link after deletion, partial save, repaired targets and reload.
  Native results and normalized exports retain the immutable proposal separately.
- Supporting-cycle, dangling/self/unknown references, empty approvals, invalid
  partial records, altered source/proposal/predecessor bindings and coverage
  accounting regression tests. Independent review caught missing predecessor
  identity checks; these are now enforced and tested.
- Native overflow migration from 17 to 21 slots in another QA project, preserving
  every existing native field, claim identity, removal and edited text. Original
  annotation/reviewer metadata remain distinct from the migrated annotation.
- `make fix` and `make check` with the five relevant pilot test modules:
  **101 tests passed**, formatting/lint passed, and strict typing passed across
  561 source files. `git diff --check` passed. No full-suite result is claimed.
- Live before/after comparison of projects 1–4, global database metadata and the
  protected packet/export hashes. All matched; no prior annotation or draft was
  removed. QA projects 5–7 are separate and explicitly excluded from human review.

### Learning and remaining review burden

Installed Community 1.23.0 supports fixed paired controls. Browser testing found
that repeated Choice values create HTML radio-name collisions across slots.
Unique internal values with friendly display labels and semantic aliases fix it;
this behavior is now covered by a regression test. Native UI completion is still
not contract acceptance: invalid links can be saved, and normalization must run
before an approved record advances. Save requests are asynchronous; export only
after the native save finishes.

The native form avoids a custom frontend, but short targets must be typed and
repaired manually after deletions. Long argument cards require scrolling or
resizing. Native autofocus can initially scroll the claim pane near its last
prefilled field; scroll that pane back to C001. The revised UI still needs Kyle's
usability approval. Unclear claims can remain in a faithfully approved case but
are explicitly withheld from evidence work; no evidence execution begins here.

### Evidence location and next action

Under `ER_COMMONS_DATA_ROOT`:

```text
pipelines/brisbane_baylands/task_07_pilot/07c1/o_joint_19_trial_20260925_v1/
  source_draft.json             # preserved initial source inventory/proposal
  proposal.json                 # fresh bound combined proposal, not human review
  protected_files.json          # sealed upstream byte identities
  protected_projects.json       # prior settings/native exports
  qa/                          # first native-control experiment, project 5
  qa_v2/                       # corrected actual-queue QA, project 6
  overflow/                    # native capacity migration, project 7
  trial/                       # clean one-case human trial, project 8
  manifest.json                # final artifact and implementation bindings
```

Review the clean trial and record explicit revised UI approval or requested
changes here. Only that approval permits the remaining six-case expansion.
The completed 07C stays the preserved predecessor until all replacement reviews
are finished and a separately validated replacement handoff is accepted.

## Revised UI approval and six-case expansion (2026-09-25)

Kyle reviewed the revised trial and said: “ok reviewed. thats still a hard case.
its a weird question. but its done for now. lets continue”. This approves the UI
and expansion; it does not approve the remaining six proposals. The saved native
O-Joint-19 annotation 123 (project 8, task 119) is Approved. Its 13 retained claims
include ten direct/supporting evidence candidates and three not-relevant claims,
with no unclear claims. Five relevance mappings changed; wording stayed unchanged.
This remains a difficult concern interpretation, not an answer-adequacy finding.

The four unused addition slots were marked not relevant and removed without
text. Normalization now preserves those actions as `unused_slot_removals`,
separate from actual `removed_claims`: 13 retained, zero removed, four unused-slot
removal actions. Native fields remain unchanged. A regression test distinguishes
an empty removed slot from a reviewer-added claim subsequently removed. Blank
addition slots require no action.

The accepted native/normalized one-case export is under:

```text
pipelines/brisbane_baylands/task_07_pilot/07c1/reviews/
  o_joint_19_approved_20260925T205026Z/
```

The earlier `o_joint_19_approved_20260925T204920Z` normalization is preserved as
superseded diagnostic evidence because it counted empty-slot actions as deletions.
The native review was never changed. `first_review_binding_v2.json` and
`first_review_validation.json` in the expansion namespace identify the accepted
export. Live task comparisons ignore only Label Studio's relative `created_ago`
display field; saved native exports compare exactly.

### Remaining review queues

All six complete source packets were reread, newly proposed and independently
reviewed for fidelity, coverage and relevance. The proposals contain **44 claims**.
They are model suggestions, not human decisions. Codex agents authored the
proposals from the sealed packets; no separate explicitly selected Astra run or
API model prediction service was invoked. The workflow label in Label Studio
identifies the proposal contract, not an independently verified model identifier.

| Case | Project / task | Proposed claims | Review queue |
| --- | --- | --- | --- |
| O-GGBA-2 | 9 / 120 | 2 | [Five shorter cases](http://127.0.0.1:8097/projects/9/data?labeling=1) |
| M-OSEC-273 | 9 / 121 | 3 | Same queue |
| SA-Caltrans-33 | 9 / 122 | 3 | Same queue |
| PC-LM-2 | 9 / 123 | 4 | Same queue |
| I-EA-2 | 9 / 124 | 5 | Same queue |
| I-CF-4 | 10 / 125 | 27 | [Longer case](http://127.0.0.1:8097/projects/10/data?labeling=1) |

The shorter forms have nine slots; I-CF-4 has 31. Each case has at least four
blank addition slots. Separate capacities avoid burdening short cases with dozens
of unused rows. I-CF-4 retains all 19 source passages, including General Response
8's referral to General Response 7; 15 proposed claims are not relevant. Coverage
notes distinguish chapter-boundary statements from the response's own arguments.
I-EA-2 retains one unclear mitigation relationship rather than inventing a
jobs/housing commitment. PC-LM-2 explicitly restores previously deleted text only
as a new, unapproved not-relevant proposal with prior-edit provenance.

Independent review found one small I-CF-4 qualification loss. `proposal_v2.json`
restores “can be very expensive” in C025; the first proposal remains preserved,
with a fresh proposal identity and unchanged stable claim IDs in the revision.
Other independent case reviews found no blocking fidelity or coverage issues.

Expansion artifacts live under:

```text
pipelines/brisbane_baylands/task_07_pilot/07c1/remaining_six_20260925_v1/
```

Case folders retain proposals and drafting validations; `short_cases/` and
`i_cf_4/` retain exact prepared tasks, native imports, forms and initial exports.
`import_index.json` owns membership. Protection snapshots bind projects 1–8 and
sealed source files, including Kyle's completed trial. The manifest and adjacent
validation receipts own browser checks and final preservation evidence.

Read-only browser validation passed for all six native review tasks: exact claim
text, independent selected relationships, targets, removal state, full original
comment and every source passage (browser CRLF normalization only), blank spare
slots, and no default approval. Both queue entry points were exercised; the other
four short tasks were opened directly in the native task editor. No preview-only
check is substituted for saved task data. All six still have zero annotations
and drafts. After browsing, the import reconciler verified unchanged projects
1–8, protected source bytes and global database metadata. Label Studio strips a
trailing newline from stored form XML; reconciliation ignores outer whitespace
only and never rewrites a project to hide that difference.

After the normalization correction, `make fix` and focused `make check` passed:
**102 tests**, formatting/lint, and strict typing across 561 source files. No
full-suite result is claimed. No commit, push or evidence search was performed.

Next: Kyle reviews the six new cases. Preserve drafts and annotations, then export
and validate all seven combined outcomes in a fresh namespace. Task 07C.1 remains
active; no seven-case replacement handoff or 07D authorization is claimed.

## Five-case review and I-CF-4 presentation order

Kyle completed project 9 and requested relevance ordering for the longer case.
Native annotations 124–128 are preserved and normalized in
`07c1/reviews/five_case_export_20260925T210734Z/`. O-GGBA-2, M-OSEC-273,
SA-Caltrans-33 and PC-LM-2 are approved without claim edits. I-EA-2 is an explicit
Unclear case stop; C004 changed from unclear to not relevant, with no case note.
Do not infer case approval from the absence of unclear individual claims.
All 17 claims are retained, with no additions, removals, drafts or validation
errors. The four approvals contribute ten candidate evidence claims; I-EA-2
contributes none. Combined with O-Joint-19, six outcomes are exported, including
five approvals and one case stop. I-CF-4 remains pending; evidence work is not
started or authorized.

Project 10's form now presents six direct claims, six supporting claims, fifteen
not-relevant claims, and four blank additions. This is presentation order only:
all 31 complete native control blocks are byte-preserved and reordered; task data,
proposal, identities, alias links, predictions and reviews are unchanged. The
order is fixed while editing, preventing cards from moving when relabeled.
No claim is collapsed or omitted. Source order is retained within each category.

The change and before/after evidence are under
`07c1/i_cf_4_order_20260925T210719Z/`. Browser validation in the actual labeling
queue checked the new positions against each stable ID, every editable value,
all 19 source passages and blank/default status behavior. All ten native project
exports compare unchanged across the presentation change. The old sealed batch
form remains historical evidence; the ordering manifest owns current project 10
presentation. No package change was needed; no unrelated tests were rerun.

## Final reviewed export and replacement handoff

Kyle completed I-CF-4 (annotation 129). All 27 claims are retained; C025 changed
from supporting to not relevant. The native form left its prior target C013
filled. After announcing the deterministic consistency repair, Codex removed
only that stale target. This is assistant cleanup, not a new human relevance
judgment. Exact native before/after records and the actor-specific correction
receipt are preserved in `07c1/i_cf_4_stale_target_20260925T211400Z/`.
The initial export attempt remains incomplete diagnostic evidence and has no
completion manifest. Native completion must still be followed by validation.

The replacement seven-case handoff is:

```text
pipelines/brisbane_baylands/task_07_pilot/07c1/reviews/
  seven_case_export_20260925T211401Z/
```

It contains exact native exports, normalized reviews, live task snapshots,
source/proposal input bindings, current project configurations, summary and a
checksummed manifest. All seven trusted tasks were rebuilt from sealed inputs.
Membership, annotation identity, source references, supporting paths, removals,
unclear accounting and unchanged previous exports validate; no drafts remain.
Projects 1–4 and sealed predecessor files remain unchanged. The native exports
for already completed projects 8 and 9 match their earlier accepted snapshots.
The correction receipt remains a separate linked provenance record; do not
attribute its target cleanup to Kyle.

| Case | Outcome | Retained claims | Evidence candidates |
| --- | --- | --- | --- |
| O-Joint-19 | Approved | 13 | 10 |
| O-GGBA-2 | Approved | 2 | 2 |
| M-OSEC-273 | Approved | 3 | 2 |
| SA-Caltrans-33 | Approved | 3 | 3 |
| PC-LM-2 | Approved | 4 | 3 |
| I-EA-2 | Unclear stop | 5 | 0 |
| I-CF-4 | Approved | 27 | 11 |
| Total | Six approved; one stop | 57 | 31 |

All 57 claims remain in the export. No substantive claims were removed. The
31 evidence candidates are only direct/supporting claims from approved cases;
I-EA-2's entire case is withheld despite its direct claim. Across the full export,
25 not-relevant claims and that stopped direct claim are outside the candidate
queue. Relevance is not evidence support, truth or answer adequacy.

The completed original 07C remains the immutable predecessor. This replacement
handoff supersedes its assertions for future 07D planning. No evidence search or
verification was performed. The provisional 07D input scope now names these six
approved cases and 31 stable claim identities; its discovery plan and UI trial
still require preparation before execution. No commit or push was performed.

Learning: complete general responses produce substantial irrelevant review work.
Ordering relevant proposals first helped without deleting source-complete content.
Preserve this distinction in future interfaces, and clear or flag stale target
fields when relationships change; native saved status alone is insufficient.

The [accepted result binding](../../docs/specs/task07c1_final_result.json) pins the
export manifest, independent audit and assistant correction manifest by hash.
Independent final review passed 64 checks: all seven normalized rebuilds match,
112 protected upstream file hashes match, the original 07C manifest closes exactly,
and the earlier completed native exports and old project settings are unchanged.
`git diff --check` passed. This artifact-only closeout required no code changes;
the earlier 102-test implementation validation remains the applicable result.
