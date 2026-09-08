# Task 05E: Build the Response Relationship Graph

Status: **provisional; inactive until Task 05D is accepted**.

## Abstract

Resolve explicit relationships among Volume 4 comments, individual responses,
and general responses from the complete source-unit candidate while preserving
every unresolved or ambiguous mention.

## Goal

Produce a bidirectionally valid intra-Volume graph and provenance-preserving
linked review views without changing source transcription.

## Inputs

- Accepted Task 05D source-unit candidate.
- Accepted Task 05B relationship and review-view schemas.

## Outputs

- normalized comment-to-response, response-to-response, and
  response-to-general-response edge records;
- raw-mention-to-edge provenance;
- orphan, dangling, ambiguous, cycle, and unlinked-general-response diagnostics;
- bidirectional graph-closure report; and
- compact `comment -> direct response -> linked response/general response`
  review-view indexes retaining every unit ID, edge, relation type, and anchor,
  plus rendering recipes that retrieve text from the source-unit store.

## Research / learning checkpoint

Explain why normalized edges and derived views coexist: a general response may
serve many cases, and copying its text into each source unit would erase
provenance and create inconsistent duplicates.

## Plan

Revise this contract from Task 05D's actual records. Census explicit reference
forms before promoting resolution rules. Review ambiguous identity only; do not
decide whether linked content substantively answers a comment.

## Validation

- Every edge targets an existing source unit or remains an unresolved mention
  with a terminal reason.
- Validate forward and reverse adjacency, one-to-many and many-to-one cases,
  cycles, orphans, and shuffled-input determinism.
- Verify every authoritative review-view record retains ordered source-unit IDs,
  edge IDs and types, and anchors. Render joined text from the single source-unit
  store only as regenerable cache.
- Confirm no source transcription record changes and no large upstream payload
  is copied or rehashed.
- Run focused tests, `make check`, and `git diff --check`.

## Review pass

- **Graph integrity:** Are forward/reverse edges, cardinalities, cycles, and
  diagnostics internally consistent?
- **Provenance:** Can every edge be traced to one raw mention and exact source
  units without copied text?
- **Ambiguity:** Are uncertain identities preserved for review instead of forced
  into graph closure?

## Acceptance criteria

- The complete explicit intra-Volume relationship population is accounted for.
- No edge is inferred from semantic similarity or forced through ambiguity.
- Review views are deterministic derivatives, not new canonical source units.
- Task 05F can add a separate cross-system link layer without changing this graph.

## Non-goals

- Draft EIR target resolution, response-outcome classification, substantive-link
  review for clustering, or benchmark eligibility.
