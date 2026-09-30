# Task 08C — Rewrite and approve one group's questions

Status: **Provisional; execution not started.** Refine and activate from an
accepted 08B handoff before use. Parent: [Task 08](08_curate_grouped_benchmark.md).

## Abstract

After selection, Astra proposes consistent, faithful question wording and Kyle
reviews the exact text in a separate task. The actual model and human wording
packets contain original comments and comment-source warnings only, never
responses or response-derived rationales. Run in a fresh group-specific chat.

## Goal

Freeze at most one independently answerable question per selected comment,
preserving its meaning without learning the ask from the official answer.

## Inputs

- Accepted [08B](08b_select_group_candidates.md) selected IDs and input bindings.
  A preparation boundary extracts original comments and comment-source warnings
  into a standalone packet before the wording chat/model call begins.
- [Human review process](../../docs/response_comment_human_review_process.md),
  [Sprint 2 question boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#task-08-eligibility-clustering-and-split-boundary),
  and umbrella batch/provenance rules.
- [Artifact rules](../../docs/data_artifacts.md) and, before implementation,
  [architecture](../../docs/architecture.md).

Do not pass the 08A ranking, response text, response-derived selection reasons,
pilot answers/questions, claims, or evidence into the wording model's context.
Do not fork the selection chat for this stage. The minimal handoff preserves
selection provenance by ID/hash without including its response-bearing content.

## Outputs

- Comment-only input packet, Astra wording proposals and prompt/model versions.
- One group-specific Label Studio project from the shared wording template,
  displaying the original comment beside proposed/edited text.
- Versioned human approvals, edits, exclusions or unresolved stops; exact frozen
  question IDs/text/hashes; and validated handoff to
  [08D](08d_review_group_claims.md).

## Research / learning checkpoint

Inspect Label Studio [configuration](https://labelstud.io/guide/setup),
[preannotations](https://labelstud.io/guide/predictions), and
[export](https://labelstud.io/guide/export) guidance plus the pilot question
review's saved-export lessons. Preserve why prefilled wording is a proposal,
why exact exported text matters, and why a response-hidden screen alone cannot
prevent leakage if the drafting model already received response context.

## Plan / spec requirement

Before first use, define a shared versioned wording prompt, template, packet
schema, exporter, and validators. Verify actual queue behavior and saved exports
for approval, human edits, rejection, and unresolved cases using separate test
records. Later groups generate data and create projects with this template;
shared revisions must be explicit, tested, and assessed for prior-batch impact.

1. Validate that the actual model input contains only this group's selected
   original comments, comment-source warnings, neutral IDs and wording rules.
2. Astra (`gpt-6-astra`) proposes one clear question per comment when faithful
   wording is possible. Preserve central issue, scope, uncertainty, attribution,
   negation and material qualifications; do not add calculations or an ask.
3. Reject forced simplification: multiple independent asks cannot be hidden in
   one compound sentence, split into several cases, or salvaged by deleting a
   difficult qualification. Flag the issue for human disposition.
4. Kyle approves the exact proposal, edits and approves exact replacement text,
   rejects, or leaves unresolved. Display only original comment, comment-source
   warnings and wording proposal. Preserve rewrite/stop reasons and all versions.
5. Export, validate, and freeze approved text. Downstream discovery, generation,
   and evaluation reuse that question unchanged. A later wording change requires
   a new explicit version and revalidation of dependent claims/evidence/answers.

Selected pilot cases follow this fresh review using original comments. Do not
reuse their sealed wording approvals as Task 08 approval or mutate old artifacts.
Rejected cases stop; no automatic replacement from the group's unseen pool.

## Validation

Inspect the actual prompt payload and fresh-chat input for excluded response
material, not only the UI. Confirm one question per source, exact original text,
nonempty approvals, actual saved edited text, reviewer/version bindings and
source hashes. Check unresolved/rejected cases cannot advance and repeated
export preserves approved text. Use applicable `make` checks for implementation
and `git diff --check` for documentation.

## Acceptance criteria

- Every advancing question has exact human-approved wording and source binding.
- Comment-only drafting/review inputs are auditable and independent of responses.
- No forced rewrite, hidden multi-ask case, or automatic pilot-label carryover.
- The handoff permits 08D to restore response context through authoritative
  source IDs while retaining the frozen question; group completion is recorded.

## Review pass

Use separate input-isolation and export-integrity checks. Human review owns
semantic faithfulness; technical checks cannot certify that meaning was retained.

## Non-goals

Candidate selection, response-based reinterpretation, claim extraction, final
eligibility, clustering, evidence labeling, or automatically revising frozen
questions downstream.
