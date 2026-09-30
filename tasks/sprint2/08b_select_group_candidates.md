# Task 08B — Select one group's candidates

Status: **Provisional; execution not started.** Refine and activate from an
accepted 08A handoff before use. Parent: [Task 08](08_curate_grouped_benchmark.md).

## Abstract

Kyle reviews ranked original comments and complete official responses, selecting
up to three promising cases from one group. This is the first human eligibility
pass, before question rewriting. Run it in a separate group-specific chat/project
with an explicit saved handoff; no labeling belongs in the main planning chat.

## Goal

Select strong rebuttal candidates without quotas, model acceptance decisions,
or turning unreviewed candidates into rejections.

## Inputs

- Accepted [08A](08a_rank_group_candidates.md) packet and saved order for one group.
- [Human review process](../../docs/response_comment_human_review_process.md),
  [Decision 005](../../docs/decisions/005_task08_grouped_question_selection.md),
  and [Sprint 2 eligibility criteria](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#task-08-eligibility-clustering-and-split-boundary).
- Umbrella batch/provenance contract and [artifact rules](../../docs/data_artifacts.md).
  Read [architecture](../../docs/architecture.md) before implementation.

## Outputs

- One group-specific Label Studio project using the shared stage template.
- Versioned human selections, reviewed skips/exclusions, provisional eligibility
  and reasons, unresolved decisions, untouched candidates, and stopping point.
- Validated export and a selected-case handoff to
  [08C](08c_review_group_questions.md), with original source provenance separated
  from later comment-only wording inputs.

## Research / learning checkpoint

Inspect maintained Label Studio [configuration](https://labelstud.io/guide/setup)
and [export](https://labelstud.io/guide/export) guidance and reusable pilot
screening helpers. Explain why human decisions must be distinct from proposals
and why an unsaved or unseen record is not a negative label. Preserve the actual
queue-to-export verification lesson, not merely a screenshot of the interface.

## Plan / spec requirement

Before first use, define or adapt one versioned shared selection template,
input/output schema, reason codes, exporter, and validators. Test synthetic
selection, skip, unresolved, and unreviewed cases through the real task queue
and saved export. Keep test annotations separate from dataset decisions.
Subsequent batch chats supply validated data and create a new project from this
existing template. Template changes require an explicit shared revision and
prior-batch impact decision; no per-group interface forks.

1. Import the saved order and complete source packet. Show original comments,
   complete linked responses, source warnings, and advisory rank reasons.
   Do not present a rewritten question or prefill human eligibility.
2. Kyle selects or skips candidates and gives a reason. Separately record the
   first-pass provisional eligibility judgment against the original scoped
   concern; selection is not final acceptance. Favor substantive rebuttals.
3. Exclude cases whose answer materially depends on later revisions, new Final
   EIR analysis, external evidence, mitigation changes, unusable content, or
   visual evidence unavailable to the target. Apply the documented incidental
   revision exception without hiding its warning. Ambiguity can remain unresolved.
4. Stop at three selected cases, earlier if Kyle chooses, or on exhaustion.
   Fewer are acceptable. Save the last reviewed position and group disposition;
   unseen candidates remain unreviewed. Do not replace downstream attrition
   automatically or reopen a completed group silently.
5. Export explicit human decisions bound to exact input versions and validate
   the selected handoff. Advance only selected, provisionally eligible cases;
   unresolved eligibility stays pending and excluded cases cannot advance. A group with zero selections closes with its reasons.

Pilot cases receive fresh Task 08 screening, not carried-over acceptance. Their
sealed historical labels remain untouched. Work one group at a time; no minimum
pool of 35 is required before moving this group to question wording.

## Validation

Verify actual queue ordering and full response display; saved human decisions,
reviewer/time/input identity and reason codes; at most three selections; no
empty approvals; accurate reviewed/unreviewed partition and stopping point;
and unchanged source text. Reconcile counts from records for the attrition
waterfall without treating unseen cases as exclusions. Run applicable `make`
checks for implementation and `git diff --check` for documentation.

## Acceptance criteria

- Every advanced case has explicit selection and a positive first-pass human
  eligibility decision.
- All reviewed and unseen candidates have accurate, distinguishable statuses.
- Exported decisions reproduce what Kyle saved and bind to this group's packet.
- 08C can build its comment-only packet without importing response context or
  screening rationales; the group completion is recorded independently of
  overall stage completion.

## Review pass

Independently check human/model separation, response closure, stopping semantics,
and saved-export fidelity. Keep review of software separate from human labels.

## Non-goals

Question rewriting or wording approval, final eligibility, filling quotas,
replacing dropped cases, clustering, answer drafting, or benchmark splitting.
