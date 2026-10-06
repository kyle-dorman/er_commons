# Task 08C — Review and approve selected question wording

Status: **Done — 2026-10-05. All 57 selected comments reviewed: 53 approved, 4 deferred, 0 excluded, 0 pending.**
Reviewed all saved selections in export order, one question at a time, including
both historically approved health-risk cases. Original group membership is
provenance only. The [combined process](../../docs/specs/task08c_combined_chat_review_v1.md)
owns this pass and overrides historical per-group limits below. Historical
health-risk approvals and downstream work remain unchanged. Parent:
[Task 08](08_curate_grouped_benchmark.md).

## Combined pass outcome

All 57 selections received an explicit disposition in saved export order.
C013, C023, C038 and C057 are deferred; the other 53 have frozen exact question
versions. The [current checkpoint](../../docs/specs/task08c_combined_review_result.json)
binds the complete journal, validated decisions export and preservation records.
All journal snapshots replayed; the maintained exporter reproduces the final
progress record byte-for-byte. Citation clues, response/context supplements and
scope limits must accompany later intake. Historical health-risk approvals and
downstream work remain unchanged, with reconciliation requirements preserved.
Kyle explicitly closed Task 08C on 2026-10-05. The four deferrals are recorded
outcomes, not unfinished 08C reviews; they do not advance unless explicitly
reopened. No later stages, projects/chats, commits or pushes were started.

| Deferred case | Original comment | Topic |
| --- | --- | --- |
| C013 | M-OSEC-202 | Bay checkerspot occurrence and dispersal |
| C023 | I-CF-14 | Bicycle activity data and tracking |
| C038 | O-Joint-54 | Vegetative noise barriers |
| C057 | SD-BSD-5 | Pump-station flooding and access; overlap with C056 |

The result record’s `final_decisions_export` contains all 57 outcomes and frozen
text for the 53 approvals. Its `supporting_review_inventory` retains 547 source,
revision, response and context files; `completion_receipt` records validation.
The separate task closeout records Kyle’s explicit completion instruction.

## Combined pass preparation outcome

The [current checkpoint](../../docs/specs/task08c_combined_review_result.json)
binds the qualified v3 intake, saved order, all 57 sources, historical questions,
and immutable review journal. All 42 group closeouts replayed. The first display
is M-OSEC-241's unchanged historically approved wording, now C001-v1 in this pass;
zero new approvals are inferred. Input v3 preserves earlier preparation attempts.
Focused checks: 29 passed; independent review passed. Full checks: 3,191 passed,
1 skipped, and only the three known Task06G commit-pin failures. Historical
health-risk approvals/downstream artifacts and existing work remain unchanged.
No project/chat creation, later-stage execution, commit or push occurred.

## Abstract

After selection, Astra proposes faithful questions from original comments only.
Kyle iterates and decides in the group's wording chat. Shared process
`task08c.chat_review.v1` replaces the mandatory Label Studio wording step; preserve
all existing source bindings, proposals and qualification history.

## Goal

Freeze at most one independently answerable question per selected comment after
explicit approval of the exact displayed version, without learning the ask from
an official response or adding unsupported intent.

## Inputs

- Accepted 08B handoff under `task08.selection_gate.v2`: selection with a reason
  is the sole entry gate. No provisional eligibility; eligibility remains at 08E.
- Verified comment-only packet, exact original-comment hashes, existing source
  warnings and initial Astra proposals, all preserved from `wording_v1/`.
- [Shared chat process](../../docs/specs/task08c_chat_review_v1.md),
  [chat prompt](../../docs/prompts/task08c_chat_review_v1.md),
  [human review process](../../docs/response_comment_human_review_process.md),
  [sprint boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#task-08-eligibility-clustering-and-split-boundary),
  [artifact rules](../../docs/data_artifacts.md) and
  [architecture](../../docs/architecture.md).

Keep restricted provenance separately by reference. Do not consult responses,
rankings/reasons, selection rationales, claims, evidence, or historical answers
when drafting/revising. Continue in this isolated wording chat, not the selection
or coordination chat. Source-only version history and current feedback are allowed.

## Outputs

- Versioned displays containing original comment and exact proposed question/null.
- Verbatim human feedback and explicit version-bound approval/exclusion/unresolved
  decisions; preserved proposal versions and source-support flags.
- Validated export of only approved exact text, all nonadvancing states, and a
  coordination handoff naming `task08c.chat_review.v1`. No 08D execution.

## Research / learning checkpoint

Use versioned entities and attributable decisions as described by
[W3C PROV](https://www.w3.org/TR/prov-overview/), with narrow JSON records and
existing hashing/validation helpers. Exact displayed text, its source and human
approval must remain linked. Saved feedback is not approval. No dependency or
historical case-content reading is needed to establish this boundary.

## Plan / spec requirement

1. Preserve the existing packet/proposal and Label Studio artifacts unchanged.
   Establish shared chat prompt, schema, event replay/export helper and fixtures.
2. Present each original comment separately with its current question/version.
   Explain a null proposal briefly and discuss it before any disposition.
3. Save feedback and revised displays. Flag clarification unsupported by source
   rather than silently adding it. Preserve uncertainty, attribution, negation,
   scope and all material qualifications; never force independent asks together.
4. Record only explicit human decisions against exact displayed versions. Changes
   and further feedback invalidate stale approval. User may exclude or leave
   unresolved; a model stop is never an automatic exclusion.
5. After explicit approvals, validate and freeze exact approved text. Preserve
   exclusions and unresolved cases without backfilling. Include the shared process
   revision in the batch register and coordination handoff.

## Validation

Source-free checks exercise feedback/revision, latest-version exact approval,
null proposals, exclusions/unresolved states, source hash mismatch, stale/blank
approval and repeatable export. Independently review input isolation and export
fidelity. Preserve chat statements and display artifacts for semantic review.
Run applicable `make` checks and `git diff --check`; report the three recorded
historical Task06G commit-pin failures separately from new validation results.

## Acceptance criteria

- Each advancing question has explicit approval of its exact displayed version.
- Original sources/proposals and every revision/feedback remain bound and auditable.
- No response context, unsupported user-added intent, forced compound ask,
  automatic model exclusion, stale approval or automatic replacement advances.
- Shared process revision accompanies validated export and coordination handoff.
- Unresolved cases do not advance and remain distinct from exclusions.

## Review pass

Use bounded independent approval/export and workflow-documentation reviews.
Deterministic validation does not certify semantic faithfulness or the truth of
transcribed approval; the actual chat and source text remain review evidence.

## Non-goals

Candidate reselection, response interpretation, claims/evidence work, final
eligibility, forced questions, backfilling, or starting later stages.

## Accepted workflow amendment

Kyle explicitly requested chat review after Label Studio preparation. The shared
chat process supersedes that review requirement, with no approvals inferred from
this workflow request. Both cases subsequently completed human discussion and
explicit approval as recorded below.
Existing project 44 is retained as historical preparation evidence, not consulted
for chat decisions. The original proposal containing no question remains an
unresolved proposal outcome, not a rejection.

## Final health-risk outcome

Both selected comments are approved under `task08c.chat_review.v1`:
M-OSEC-241 C001-v2 and O-Joint-44 C002-v2. Kyle approved the first with
“yes this is a good reframing. next” and the second with “yes thats good.”
The exact displayed question versions, verbatim feedback/approvals, source hashes,
Astra revision provenance and all earlier null proposals remain preserved.
No case was excluded or left unresolved, and no replacements were added.

The [completion record](../../docs/specs/task08c_health_risk_result.json) binds the
final `chat_review_v1/journal_v6.json`, exact approved questions, validated export,
source references and final coordination handoff. All six journal snapshots replay;
repeat export is identical and the first frozen question is unchanged. Only
approved exact text advances. The review used one active comment at a time within
this batch chat. Existing Label Studio and sealed upstream artifacts are unchanged.

No implementation changed during final approval/export. Prior implementation
checks remain recorded: 44 targeted tests and 20 independent checks passed;
full suite 2,931 passed, 1 skipped, with three historical Task06G commit-pin failures.
Final artifact/source/version replay and independent export fidelity are checked
separately. No new full-suite run is claimed for this data-only closure.

Final handoff:
`/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_08/health_risk/08c/chat_review_v1/exports/review_v1/handoff.json`

08D remains unstarted and requires a separate request. Evidence-based eligibility
remains at 08E. No commit or push was made.

## Post-completion wording learning

Recommendation-shaped comments may need an adoption/consideration question rather
than an information request or an assumed rejection. The reusable
[learning note](../../docs/response_comment_human_review_process.md#learning-recommendation-shaped-comments)
and [prospective v2 prompt](../../docs/prompts/task08c_chat_review_v2.md) preserve
this distinction and the independent-ask guardrail. Existing approved questions,
v1 prompt bindings, final handoff and upstream records remain unchanged.
Documentation-only follow-up; no new model run or 08D work.

## Initial chat-review implementation checkpoint

The shared `group_wording_chat` validator and closed journal schema preserve
versioned displays, verbatim feedback and explicit dispositions. A null original
proposal remains pending. Source-free qualification covers exact approval,
feedback invalidation, stale or unsupported approval rejection, exclusions,
unresolved cases, predecessor immutability and stable repeated export.

The health-risk journal begins with `C001-v1` and `C002-v1`, both bound to the
unchanged initial proposal. Neither has a human disposition. The second display
records no question and invites discussion before exclusion or any other decision.
Current artifacts live in `health_risk/08c/chat_review_v1/`; the original
`wording_v1/` directory and project 44 remain preserved. The initial coordination
handoff named `task08c.chat_review.v1` and awaited discussion/explicit approvals;
the final handoff above supersedes that pending status.

Validation of the chat revision: 44 targeted wording tests and 20 independent
checks passed. Format/lint and MyPy passed (577 source files). Final full check:
2,931 passed, 1 skipped, and only the three historical Task06G commit-pin failures.
An interim run caught the support-resolution regression during implementation;
the corrected final run passes it. Logs remain in the chat-review namespace.

## Historical Label Studio preparation plan (superseded review route)

1. Deterministically verify the accepted 08B v2 handoff and extract only the two
   selected original comments and existing comment-source warnings. Bind neutral
   IDs and hashes; retain restricted provenance separately by reference.
2. Inspect reusable preparation/export components and native form controls without
   reading historical case payloads. Establish `task08c.wording.v1` prompt, input/
   proposal/review schemas, form, preparation helper and strict saved exporter.
3. Use source-free fixtures to qualify the real Label Studio queue, proposal
   prefilling, editing, explicit approval/rejection/unresolved decisions, reload
   and native export. Independently review input isolation and export fidelity.
4. Give an isolated Astra worker only the validated comment-only packet and
   versioned wording rules. Validate proposals and create the two-record review
   project only after qualification. Preserve all versions and exact bindings.
5. Await Kyle's saved decisions. Only then export explicitly approved exact text,
   preserve stops and unresolved cases, and publish a validated downstream handoff.
   Update the batch register with preserved predecessor bytes at each transition.

No 08D work, other groups, additional chats, or upstream mutations are authorized.
Carry forward the three recorded historical Task06G commit-pin test failures;
report current checks separately from this inherited baseline.

## Historical health-risk Label Studio preparation — 2026-09-30

Shared preparation is complete; the two-comment batch remains open for Kyle's
saved decisions. [Project 44](http://127.0.0.1:8097/projects/44/data?tab=43&labeling=1)
contains one proposed question and one blank proposal following Astra's multi-ask
stop. No model stop is a human rejection, and zero questions are frozen. The
[compact readiness record](../../docs/specs/task08c_health_risk_result.json) owns
exact packet, proposal, interface, qualification, project and coordination hashes.

Deterministic extraction verified both original-comment hashes against the pinned
08B handoff and reproduced the saved selection gate. Only exact comments, existing
comment-source warnings, neutral IDs and hashes entered wording input. Restricted
provenance remains separate. Shared code uses native Label Studio controls and
strict saved-text normalization rather than a model backend or custom UI.

The agent service refused a fresh isolated worker at its thread limit. Wording
therefore used an ephemeral `codex exec` run explicitly configured for
`gpt-6-astra`, with a fresh empty directory, ignored user configuration, project
instructions and memory disabled, and external tools disabled. Exact request,
invocation, events, proposal and hashes are saved in `drafting_v1/`. No tool calls
occurred. The independent input audit verified exact request reconstruction and
recorded the observable audit limits; it does not claim access to hidden service
context. This uses the documented [non-interactive ephemeral mode](https://learn.chatgpt.com/docs/non-interactive-mode)
and creates no additional persistent review chat.

Synthetic projects 42 and 43 qualified actual queue prefilling, blank decisions,
unedited and edited approval, rejection, unresolved and untouched states, saved
reload and repeated exports. Independent export review passed 14 fidelity and
adversarial checks. Dataset project imports and both displayed proposals were
checked without submitting or editing; native verification found zero annotations
and drafts. The read-only browser check initially counted Label Studio's own
view-mode radio buttons, then correctly scoped assertions to the three decision
controls; no source or decision data changed.

Validation: `make fix` passed; format, lint and strict MyPy passed (576 source
files); 30 targeted tests passed. Full `make check` reached pytest and reported
2,917 passed, 1 skipped and the same three historical Task06G commit-pin failures:

- `test_collection_generator_preserves_historical_v38_owner_packet`
- `test_task06g_v38_generation_remains_immutable_after_finalization_amendment`
- `test_task06g_templates_are_executable_and_source_free`

Full logs and qualification evidence remain external. Current checks do not
constitute a clean full-suite pass. The batch register preserves its preceding
bytes and now records `awaiting_saved_human_wording_decisions`. Other groups,
08D and all sealed upstream artifacts remain untouched. No commit or push made.
