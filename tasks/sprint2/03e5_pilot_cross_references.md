# Task 03E.5: Pilot Canonical Cross-References

Status: **provisional**. Revise this contract from the accepted Task 03E.4
outcome before activation.

## Abstract

Pilot deterministic cross-reference mention extraction and within-document
candidate resolution on the accepted Appendix P semantic candidate. Preserve
exact source text spans and provenance, generate zero-or-more targets from the
accepted alias inventory, and retain resolved, ambiguous, and unresolved
states.

This document-scoped task cannot resolve references to canonical targets in
other Draft EIR PDFs that have not yet been extracted. Preserve those mentions
as explicit unresolved or alias-based candidates for Task 03F's corpus second
pass.

## Goal

Validate a provenance-preserving canonical mention and candidate contract
without using LLM linking, embeddings, fuzzy semantic search, curator-only
response content, or retrieval-specific graph construction.

## Inputs

- accepted Task 03E.4 semantic candidate and completion artifacts
- semantic section, printed-page, document, appendix, table, and figure aliases
- canonical block, table, figure, page, and section anchors
- checksum-pinned source and raw producer lineage
- current cross-reference schema and invariant tests
- maintained open-source options for deterministic citation and reference
  parsing, evaluated before adding custom parsing glue

## Outputs

- a supported mention-pattern and candidate-resolution specification
- schema changes required for raw mentions, exact spans, candidates, evidence,
  unresolved reasons, and deferred cross-document resolution
- package-backed extraction/resolution code with tiny fixtures
- a new immutable Appendix P candidate or accepted separate enrichment artifact,
  as decided by the revised contract
- deterministic mention, within-document resolution, and unresolved-reference
  summaries
- independent preservation evidence against Task 03E.4
- exact target/alias/index handoff to Task 03F

## Research / learning checkpoint

Compare maintained deterministic parsers and citation utilities with thin
project-owned patterns for the exact source forms observed in Appendix P.
Adopt a package only when it materially handles the required reference grammar;
do not add a broad NLP dependency merely to replace a few explicit patterns.

The outcome must explain:

- **Aliases and mentions are separate data.** Task 03E.4 defines potential
  targets; this task locates source spans that may refer to them.
- **Candidate generation is not confident resolution.** Zero, one, or several
  candidates remain visible with deterministic evidence.
- **Cross-document resolution is two-pass.** Other-document targets do not
  exist until Task 03F completes per-document semantic stage one and seals a
  corpus target index.
- **The canonical source graph differs from later graphs.** Task 05 owns
  comment/response relationships, Task 06 owns a curator traversal view, and
  Task 07 owns reviewed case-clustering edges.

## Plan / spec requirement

Freeze before implementation:

1. supported mention classes and exact source-span rules;
2. target types and alias lookup behavior;
3. deterministic normalization and collision handling;
4. resolved, ambiguous, unresolved, and deferred-cross-document semantics;
5. source record, character span, region, raw-lineage, and evidence fields;
6. ordering and ID rules;
7. schema/identity/publication consequences;
8. exact permitted differences from Task 03E.4;
9. corpus target-index and second-pass handoff; and
10. unsupported forms and warning/failure policy.

## Review pass

- **Package leverage:** maintained parsing is used where it clearly fits.
- **Traceability:** every mention resolves to literal canonical text and exact
  low-level anchors.
- **Uncertainty:** no candidate is silently forced to one target.
- **Scope:** within-document resolution is distinguished from deferred
  cross-document work.
- **Leakage:** no Final EIR response, curator label, usability field, or
  benchmark evidence enters the canonical graph.

## Validation

- Test section, appendix, page, table, figure, document, malformed, repeated,
  ambiguous, unresolved, and deferred cross-document fixtures.
- Verify exact source spans, regions, aliases, candidates, status, evidence, and
  deterministic ordering.
- Verify candidates target only accepted canonical target types.
- Require exact preservation of Task 03E.4 records and assets outside declared
  identity and cross-reference outputs.
- Confirm repeat execution and fresh staging are byte-identical.
- Confirm no LLM, embedding, fuzzy semantic retrieval, response inventory, or
  curator decision enters the stage.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- Supported mentions have exact text, spans, provenance, candidates, and
  deterministic evidence.
- Resolution state agrees mechanically with the candidate set.
- Other-document references remain explicit for Task 03F rather than being
  dropped or guessed.
- The canonical cross-reference output is sufficient to build a sealed corpus
  second pass without mutating completed per-document stage-one artifacts.
- Task 06 can later consume canonical edges without owning extraction or
  resolution semantics.
- The outcome requests user review before Task 03F activates.

## Non-goals

- full-corpus or cross-document resolution
- response/general-response links in Final EIR Volume 4
- case clustering or split-leakage edges
- semantic evidence selection or citation approval
- graph retrieval, BM25, embeddings, or LLM entity linking
