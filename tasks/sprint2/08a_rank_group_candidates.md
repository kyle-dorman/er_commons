# Task 08A — Prepare and rank one group's candidates

Status: **Active contract; execution not started.** Documentation preparation
alone does not run this stage. Parent: [Task 08](08_curate_grouped_benchmark.md).

## Abstract

Prepare a complete, revisitable browsing order for one accepted exclusive group.
Astra ranks question and response quality; Kyle alone selects candidates and
judges eligibility in 08B. Run this reusable stage in its own group-specific chat,
not the planning chat, starting with the health-risk priority group.

## Goal

Give the reviewer a useful order, faithful source context, and explicit concerns
without hiding candidates or converting model preferences into eligibility.

## Inputs

- [Decision 005](../../docs/decisions/005_task08_grouped_question_selection.md):
  accepted group assignment, hashes, exceptions, and priority group.
- [Human review process](../../docs/response_comment_human_review_process.md),
  [Sprint 2 eligibility boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#task-08-eligibility-clustering-and-split-boundary),
  and the umbrella's batch/provenance contract.
- Current [response inventory](../../docs/specs/task07a1_final_result.json),
  exact original comments, complete linked response closure, source warnings,
  and one explicitly identified group.
- [Data/artifact rules](../../docs/data_artifacts.md); read
  [architecture](../../docs/architecture.md) before any later implementation.

## Outputs

- A fresh external Task 08 group/stage artifact containing all group candidates,
  their exact source bindings, complete resolved responses, retained flags,
  saved rank, and short question-quality and response-quality rationales.
- A manifest binding group/input hashes, prompt version, actual model identity,
  proposal versions, ranking policy, and deterministic tie-break rules.
- A validated handoff to [08B](08b_select_group_candidates.md), with no human
  decisions inferred from rank. No Label Studio project is required here.

## Research / learning checkpoint

Inspect the accepted inventory's closure contract and Decision 005's distinction
between assignment and quality order. Explain why saved model ordering is
revisitable but rerunning a model is not guaranteed to reproduce that order.
Before implementation, inspect existing package-backed preparation helpers and
preserve their source/link validation rather than build a new workflow engine.
Record the narrow reuse decision and limits in the outcome.

## Plan / spec requirement

Write a brief ranking/input specification before first execution. Define once
and version the reusable record schema, ranking prompt, validation, and handoff.
Each later group uses these components and generates data only. A proposed
change requires an explicit shared version revision and an assessment of prior
batches; do not customize the policy privately for one group.

1. Verify the accepted grouping identity and select exactly one group. Retain
   all group members and inherited flags; do not silently regroup or refilter.
2. Resolve complete response closure and source text before ranking. Missing or
   unusable sources remain flagged and block unsupported quality assertions.
3. Have Astra (`gpt-6-astra`) read original comments and complete responses.
   Favor clear, independently answerable concerns and substantive rebuttals;
   deprioritize rant-like material, revision-dependent answers, empty referrals,
   and nonanswers. Preserve difficult qualifications and distinguish an awkward
   writing style from a substantive concern. Do not rewrite questions here.
4. Record reasons and a total order, breaking residual ties by stable comment
   ID. Retain every candidate; model ranking is advice, not an eligibility label.
   Preserve O-Joint-44's incidental-revision exception and the health-risk
   group's potential-table status; never invent a calculation requirement.
5. Save and validate the order once for this group. Reranking creates a new
   version with a reason; it never overwrites reviewed order or decisions.

The six approved pilot cases reenter from original source material with fresh
Task 08 histories wherever their accepted groups place them. Do not import old
approvals, claims, or answers as new labels. Preserve the sealed pilot, its
limitations, and existing I-CJ-4/I-EA-2 stops.

## Validation

Verify exact group coverage with no omissions/duplicates; source/link closure;
stable IDs, input hashes, rank uniqueness, complete rationales and flags; and
manifest-to-output closure. Check the four named priority candidates against
Decision 005. Inspect saved data for invented rewrites or model eligibility
labels. For implementation use targeted meaningful tests and `make fix` /
`make check`; for documentation only, inspect the diff and `git diff --check`.

## Acceptance criteria

- One group's full ordered packet and provenance validate, with no hidden drops.
- A future chat can resume 08B from the handoff without the ranking conversation.
- Ranking is explicitly advisory and no selection or labeling has occurred.
- Completion is recorded for this group only; the reusable stage remains
  available for later groups under the umbrella's batch registry.

## Review pass

Use bounded independent checks for source/closure integrity and ranking-policy
faithfulness. Reconcile concerns before handing the packet to the human reviewer.

## Non-goals

Human selection, eligibility decisions, question rewriting, evidence discovery,
clustering, final split allocation, or automatically processing all 42 groups.
