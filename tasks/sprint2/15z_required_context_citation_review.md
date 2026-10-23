# Task15Z — Review citations for required conclusion content versus context

Status: provisional; task specification only. User has not activated cleanup.

## Abstract and goal

Review the reference citation mappings against the approved required/optional
conclusion points. Distinguish evidence directly supporting required answer
content from evidence supplying optional detail, explanation or context. The
user suspects many citations are contextual relative to required conclusions;
treat this as a hypothesis to audit, not a predetermined relabeling outcome.

This is follow-up2 of3, after15Y and before
[15AD final end-to-end run](15ad_final_end_to_end_run.md).

## Inputs

- Structured references and citation anchors selected by
  `docs/specs/task15ac_reference_result.json` (all49 questions).
- Source-bound review packets and support-point citations via the Task15F/15L
  pointers; retain source editions, exact excerpts and table context.
- `docs/specs/adequacy_labeling_rules.md`, especially citation-role semantics;
  `docs/data_artifacts.md` and the existing reference publication contract.
- Task15AA decisions are published: C017 storage is optional; C014 VMT content
  is removed from the conclusion reference.15AC includes provenance-only anchor
  repairs for C014/C032/C011/C052; these do not settle the wider citation-role audit.


## Outputs and plan

Prepare an evidence-first review of all49 reference cases without reading model
predictions to choose edits. For each citation, map the particular source passage
or table row to the required and/or optional points it actually supports. Classify
its relation as direct required-content support, optional-detail/context support,
mixed, or unresolved, with short rationale and exact evidence anchors. These are
review classifications, not automatic changes to runtime citation-role enums.

A source can support both required and optional content; a citation may support
only one clause of a point or work jointly with other citations. Do not force
whole documents into mutually exclusive roles. Optional explanation can have
real evidentiary value; not required by C does not mean irrelevant, unsupported,
or removable from the evidence supplied to a target model.

Identify mismatched anchors, excessive citation bundles and contextual details
embedded in required points. Propose per-case mapping cleanup and separately flag
required/optional policy changes for user adjudication. Preserve existing support
points as labeling provenance. Show question, reference point, source passage,
proposed change and uncertainty for each decision. Do not silently prune citations,
source packets, support points or required meaning to match predictions.

After user review, publish only accepted changes in a fresh version if authorized.
Record downstream impact on synthetic expectations, C qualification, Task15Y
coverage diagnostics and later evaluations; do not regenerate or rerun them
implicitly. Task15Y may use the current frozen references independently, but must
identify that version and not mix results across any later accepted cleanup.

## Research / learning checkpoint

Inspect the existing citation policy and source anchoring/provenance contracts.
Explain the distinction between a citation's role relative to required conclusion
content and its role in grounding a supporting or optional claim. Check primary
annotation/provenance guidance where it helps settle the mapping convention;
record the rationale before adopting a new schema.

## Validation, review and acceptance

- All49 cases accounted for; exact citation IDs, editions and source anchors
  verified, with unresolved mappings retained rather than guessed.
- Required meaning remains supported, including qualifications and how/why
  mechanisms; joint and mixed-purpose citations remain representable.
- Independent bounded review checks the proposed classifications against evidence,
  not agreement with predictions. User adjudicates proposed materiality changes.
- Save proposals/decisions externally in a fresh Task15 namespace and link a
  compact result pointer. Preserve frozen releases and exposure disclosures.
- Inspect documentation diffs and run `git diff --check`; any later implementation
  or publication work gets appropriate additional checks.

## Non-goals

No cleanup execution, label edits, synthetic generation, model calls or downstream
rescoring in the task-writing turn. No assumption that most citations must become
context. No target evidence removal, source research expansion, MiniMax, reserved
challenges, commits or pushes. Task16 requires separate activation.
