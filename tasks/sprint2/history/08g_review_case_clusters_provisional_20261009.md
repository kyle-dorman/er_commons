<!-- Historical provisional contract, superseded 2026-10-09. Relative links adjusted for this historical location. -->

# Task 08G — Review clusters across the completed case pool

Status: **Provisional contract; execution has not started.** Activate only after
all group authoring batches are complete and their handoffs are accepted.

## Abstract

Review potential similarities and dependencies across the full accepted Task 08
pool, including cases from different selection groups. Astra proposes bounded
relationships; the human reviews them one at a time in separate chats. Code
records confirmed edges and computes connected components for later splitting.

## Goal

Produce an auditable case-clustering graph whose confirmed clusters must remain
together in the development/test split. Selection groups are browsing aids, not
clusters, and at most three selections per group does not establish independence.

## Inputs

- [Task 08 umbrella](../08_curate_grouped_benchmark.md), every completed group's
  [08F handoff](../08f_review_group_answers.md), and the whole-pool completion ledger.
- [Sprint clustering boundary](../../../docs/sprints/sprint2_brisbane_draft_eir_defense.md),
  [Decision 005](../../../docs/decisions/005_task08_grouped_question_selection.md),
  [artifact contract](../../../docs/data_artifacts.md), and
  [architecture](../../../docs/architecture.md) before changing helpers.
- Stable case/comment IDs, commenter-letter membership, complete response/general
  response links, Task 05 curator-only cross-references, approved questions,
  original source text, approved answers/evidence, and warnings.

## Outputs

- A reproducible candidate-link inventory covering the entire accepted pool,
  with separate deterministic signals and versioned Astra suggestions.
- A small deterministic duplicate/near-duplicate validation fixture and results.
- Saved human decisions on suggested relationships and groupings, including
  rejected/administrative links, shared-evidence warnings, and unresolved items.
- A confirmed case graph, connected components, checksummed review handoff, and
  a leakage-audit specification for the proposed split in 08H.

## Research / learning checkpoint

Inspect primary [scikit-learn grouped cross-validation guidance](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data)
and the maintained project's relationship contracts. Explain why dependent cases
must remain together, why connected components preserve transitive dependencies,
and why shared evidence is only a review signal. If adding a similarity package,
check its official documentation and maintenance before selecting it; prefer
existing narrow helpers where sufficient. Record evidence for the choice.

## Plan / spec requirement

Write a short graph and review spec before implementation: allowed edge types,
candidate sources, stable pair IDs, duplicate-method qualification, model proposal
format, human decision semantics, and connected-component construction.

1. Verify every group is closed for authoring, including groups with fewer than
   three selections and groups yielding no accepted answers. Unresolved cases
   require explicit human deferral outside this pass under the umbrella rule;
   they are not silently accepted, rejected, or treated as completed work.
   Do not run partial
   within-group clustering during the authoring stages. Pin the accepted pool.
2. Enumerate candidates deterministically from commenter-letter membership,
   explicit response/general-response links, Task 05 curator-only response
   cross-references, and duplicate/near-duplicate source text. Preserve source
   relationships without treating every link as substantive case dependence.
3. Qualify duplicate enumeration with positive and negative fixtures covering
   exact duplication, formatting/preamble differences, paraphrased duplication,
   and distinct issues sharing boilerplate. Report misses and false-positive
   candidates; document any threshold rather than choosing it by intuition.
4. Let Astra (`gpt-6-astra`) propose similarities or groupings from supplied case
   packets. Preserve model/prompt/input/output identities and its reasons. These
   suggestions complement deterministic enumeration; they do not replace it or
   become approved edges automatically.
5. Use separate clustering chats, outside the main coordination chat. Present one
   proposed relationship or grouping at a time with the needed original text,
   frozen questions, approved answers, and relationship provenance. Include only
   relevant cases, not full unrelated batch histories. The human confirms,
   rejects, requests revision, or leaves unresolved, with a saved rationale.
6. Explicitly classify linked general responses as substantive or administrative.
   Confirmed substantive links create graph edges; administrative links remain
   recorded without joining cases. Human review owns substantive duplicate and
   dependency decisions. The helper constructs connected components mechanically.
7. Retain shared-source/evidence overlap as a warning with a human disposition.
   Task 03 adjacency, shared Draft EIR targets, graph traversal proximity, and
   response-to-Draft-EIR references never create automatic clustering edges.
8. Publish the graph and all review dispositions. Changed proposals require new
   versions; an approved grouping must resolve to explicit member IDs and edges.
   Reopening an authoring batch invalidates affected graph review and requires a
   named update before final freezing.

Keep Task 03 source cross-references, Task 05 curator response relationships, and
Task 08 case clusters separate. No manual comparison of every inventory pair is
required, but enumeration must span all accepted cases across all groups.

## Review pass

Use bounded reviews for relationship closure, duplicate-fixture coverage, and
human-decision/graph consistency. Inspect whether any automated edge rule exceeds
the accepted contract. Reconcile findings before declaring the graph accepted.

## Validation

- Check every accepted case appears exactly once as a graph node, including
  singletons, and every candidate/edge refers only to members of the pinned pool.
- Verify deterministic enumeration and component construction on fixed inputs;
  report duplicate-method misses and false positives on the fixture.
- Trace every substantive edge and every dismissed warning to its human decision.
  Confirm rejected/administrative candidates do not create hidden edges.
- Check transitive components and record unresolved relationships as blockers to
  final split approval, not implicitly negative decisions.
- Run focused tests and `make fix` / `make check` for helper changes; inspect the
  diff and run `git diff --check` for docs-only updates.

## Acceptance criteria

- All group batches have completed authoring before this stage executes.
- Deterministic and model-proposed candidates, including cross-group candidates,
  have auditable dispositions; no relevant unresolved decision is hidden.
- Confirmed clusters are reproducible from the approved graph and input identity.
- The 08H handoff includes the duplicate fixture/results, warnings, limitations,
  graph, component assignments, and exact human decision records.

## Non-goals

Selection-group redesign, answer relabeling, automatic semantic clustering,
forcing clusters to fit a size target, split freezing, or benchmark execution.

## Outcome

Not started. Record candidate/confirmed/rejected counts, components, unresolved
issues, fixture results, learning, and the exact accepted 08H graph handoff.
