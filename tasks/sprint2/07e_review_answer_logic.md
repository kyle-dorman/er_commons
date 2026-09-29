# Task 07E: Review Reference Answers and Reasoning

Status: **Updated plan approved 2026-09-29; combines former 07E and 07F into one
human labeling pass. Prototype and execution contract still to be finalized.**

## Goal and boundary

Review one concise reference answer per case, with its reasoning expressed in
the answer itself. It states the direct conclusion, necessary evidence-based
explanation, essential conditions and remaining uncertainty. Do not separately
label an outline, reasoning steps, sentence-to-citation mappings, or a later
polished defense. The former 07F deliverable is produced here.

This is dataset authoring, not benchmark grading. The
[Sprint 2 evaluation contract](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary)
owns two automatic citation checks and two judged dimensions. The reference
answer informs **answer adequacy**; **grounded correctness** is judged against
source evidence with this reference hidden. Reference wording is not the only
valid answer, and an official response is never independent evidence.

## Inputs and selection

- Bind the accepted 07B questions, 07C.1 claims/relevance and sealed 07D case
  exports, including the user-approved MVP warnings and source limitations.
- For the next authoring pass, each comment yields at most one faithful, clear,
  independently answerable question. Rewrite only when it preserves the central
  concern and qualifications; otherwise skip. Do not split a comment into more
  cases or invest in salvaging weak examples. Preserve original-comment provenance.
- Freeze the same question for retrieval, target generation and both judge stages.
  Preserve the current six-case MVP and 31 claims. Any change to an existing
  reviewed question requires an explicit versioned scope decision before use;
  it is not authorized by a formatting or answer-drafting change.

## Proposed single review

Show the scoped question, one editable proposed reference answer and expandable
reviewed sources with mechanically rendered citation labels. Keep support/context
citations separate from the claim list and preserve exact anchors. The answer
need not repeat every retained claim or cite every reference source; no claim
records are deleted by drafting a concise answer.

Codex may use an outline internally, but the curator reviews one artifact and
one disposition: approve, needs revision, or insufficient evidence/unsuitable
case. A reference answer may be a short paragraph or clear bullets. Do not create
another style-polishing approval gate or mandatory per-claim mapping checklist.
Preserve model proposals and human edits separately.

## Prototype, validation and acceptance

Before implementation, select one case and present its proposed question/answer
layout and input bindings. Trial one labeling task, then expand only after Kyle
reviews the workflow. Finalize schema/version, source-ID validation, edit/export
round-trip and maintainability checks in that bounded contract.

Review whether the answer addresses its actual question, whether the sources
justify the claims and conclusion, and whether essential conditions/limits are
present. Do not merely reproduce the official response or assume that inclusion
in the noisy MVP claim list establishes relevance or support. No additional claim
relabeling is part of this pass. Preserve unresolved issues and explicit stops.

Output one human-reviewed reference-answer record or explicit stop per case,
with question/input identity, citation pool, source provenance and native review
history. This single artifact replaces the separately approved logic summary and
final defense. It is not supplied to the target model or the grounded-correctness
judge; no new model run, labeling project or benchmark eligibility decision is
created by this planning update.
