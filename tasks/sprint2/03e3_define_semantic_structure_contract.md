# Task 03E.3: Define the Semantic-Structure Contract

Status: **provisional**. Revise this contract from the accepted Task 03E.2
outcome and activate it only after explicit user approval. It changes tracked
contracts, schemas, fixtures, and validators but does not publish a live
canonical candidate.

## Abstract

Translate the accepted Task 03E.2 corrected hierarchy into a project-owned
contract for semantic sections, ordered membership, printed-page-label
evidence, resolved page labels, and deterministic target aliases. Decide which
evidence belongs in canonical records and which belongs in checksummed
supporting observations before implementation.

Keep the accepted Task 03D.1 candidate as immutable core-content reference
evidence. Define a new candidate identity and an exact allowed-difference gate
for Task 03E.4 rather than modifying the completed candidate in place.

## Goal

Make the hierarchy, page-label, alias, identity, provenance, and publication
rules executable and independently reviewable so Task 03E.4 can remain thin
mapping and validation glue around accepted corrected-hierarchy output.

## Inputs

- accepted Task 03E.2 corrected-hierarchy candidate, completion, comparison,
  reconciliation, decision, ambiguity, and review artifacts
- immutable raw Task 03E producer hierarchy and correction correspondence
- completed Task 03B canonical contract and executable schemas
- accepted Task 03D.1 canonical candidate and its 57-path equivalence evidence
- Appendix P PDF outline, visible TOC/index blocks, body/furniture layers,
  canonical order, page geometry, and raw lineage
- current page, section, manifest, identity, completion, and observation schemas
- current canonical bundle and order-sensitive validation requirements
- JSON Schema Draft 2020-12 and RFC 8785

## Outputs

- a revised semantic-structure specification
- executable schema changes or new schemas for:
  - semantic section level, path, ordered containment, and inference provenance;
  - printed-label observations, evidence methods, conflicts, unknown states, and
    the resolved nullable page value;
  - deterministic document, appendix, section, table, figure, and printed-page
    target aliases; and
  - old-candidate to new-candidate semantic correspondence
- explicit decisions identifying canonical fields, canonical observations, and
  checksummed support artifacts
- revised ID, ordering, serialization, status, manifest, and completion rules
- an order-sensitive section hierarchy validator
- fixtures covering bookmarks, numbering, missing/skipped levels, repeated
  headings, TOC rows, furniture, embedded numbering resets, explicit and absent
  `/PageLabels`, visible-only labels, conflicts, aliases, and ambiguity
- an exact Task 03D.1-to-03E.4 preservation/equivalence specification

## Research / learning checkpoint

Compare strict-schema evolution against a separate observation/support-artifact
design. Prefer the smallest representation that preserves evidence and supports
later review, citation rendering, and cross-reference matching without
duplicating the accepted producer document.

The outcome must explain:

- **Raw, corrected, and canonical hierarchy have different owners.** Docling
  supplies immutable observations, Task 03E.2 supplies accepted corrected roles
  and levels, and this contract owns stable canonical records, provenance,
  invariants, and downstream isolation.
- **Physical pages and printed labels are separate identities.** Distinguish
  internal indices, one-based PDF pages, explicit PDF `/PageLabels`, synthesized
  library defaults, and visible printed labels.
- **TOC rows name targets without starting body sections.** Visible contents
  support reconciliation and aliases but remain ordinary anchored content.
  A TOC-derived alias may attach only to a reconciled body target, never to the
  TOC row itself.
- **Ambiguity should be represented, not silently resolved.**
- **Schema meaning controls identity.** Required-field, ordering, ownership, or
  status changes create a new candidate identity and may require a schema-major
  revision.

## Plan / spec requirement

Freeze before implementation:

1. exact persisted shapes for hierarchy, label, alias, and evidence data;
2. whether each shape is a canonical record family, record field, observation,
   or checksummed support artifact;
3. schema compatibility and versioning decision;
4. semantic-section start, end, parent, path, level, and direct-membership rules;
5. retained synthetic body/furniture roots and body-only semantic induction by
   default;
6. physical-page, explicit-page-label, visible-label, resolved-label, unknown,
   and conflict semantics;
7. alias normalization, collision behavior, evidence, order, and target types,
   requiring every TOC-derived alias to resolve to a non-TOC canonical target;
8. candidate identity, old/new correspondence, atomic publication, verified
   reuse, and failure preservation;
9. inherited versus new warnings and fatal/ambiguous states;
10. exact permitted differences from Task 03D.1; and
11. the Task 03E.4 implementation and review handoff.

## Review pass

- **Schema sufficiency:** every promised output is representable without hidden
  side files or unvalidated extra properties.
- **Correction boundary:** the contract maps the accepted Task 03E.2 corrected
  hierarchy without changing its rules or hiding its raw Docling evidence.
- **Order:** ordered children exactly invert parent/section links in canonical
  mixed-content order.
- **Identity:** no completed candidate is rewritten and cross-version
  correspondence is explicit.
- **Review isolation:** Task 04 reviewer, usability, and disposition fields
  remain forbidden from Task 03 records.

## Validation

- Validate positive and negative fixtures against every revised schema.
- Test order-sensitive hierarchy, cycles, skipped levels, repeated headings,
  root continuity, body/furniture isolation, and exact inverse membership.
- Test explicit `/PageLabels`, absent metadata, synthesized-default rejection,
  visible labels, conflicting evidence, repeated regimes, and unknown states.
- Test deterministic alias order, normalization, collisions, provenance, and
  target-type restrictions.
- Test identity change, cross-version correspondence, manifest agreement, and
  declared allowed differences.
- Confirm fixtures contain no cross-reference mentions or mention-derived
  candidates.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- Task 03E.4 can implement every output without inventing schema, identity,
  ordering, evidence, or publication policy.
- The contract retains the synthetic roots while replacing flat body
  membership with accepted semantic sections.
- Printed labels never replace physical PDF identity.
- Aliases identify canonical potential targets but contain no extracted
  mentions or mention-derived candidates, and no TOC row is itself an alias
  target.
- Exact preservation requirements protect all undeclared Task 03D.1 semantics.
- The outcome requests user review before Task 03E.4 activates.

## Non-goals

- running Docling or publishing a live canonical candidate
- changing accepted Task 03E.2 correction behavior
- cross-reference mention extraction or target resolution
- corpus identity, batching, or cross-document resolution
- Task 04 usability judgments
- retrieval units, indexing, or graph traversal
