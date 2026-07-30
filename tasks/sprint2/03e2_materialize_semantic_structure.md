# Task 03E.2: Materialize Semantic Structure for Appendix P

Status: **provisional**. Revise this contract from the accepted Task 03E.1
outcome before activation.

## Abstract

Implement the accepted semantic-structure contract as thin project-owned glue
over the accepted Docling hierarchy. Publish a new immutable Appendix P
canonical candidate containing semantic sections, printed-page-label evidence
and resolved values, deterministic target aliases, and exact correspondence to
the Task 03D.1 core records.

Visible TOCs and the PDF outline support deterministic reconciliation,
validation, and aliases. They do not authorize a competing project-owned
hierarchy inference algorithm.

## Goal

Produce the first complete semantic canonical document while proving that all
undeclared Task 03D.1 content, table, figure, asset, observation, geometry,
ordering, warning, and lineage semantics remain unchanged.

## Inputs

- accepted Task 03E producer completion and hierarchy output
- accepted Task 03E.1 specification, schemas, fixtures, identity, and
  equivalence policy
- immutable Task 03D.1 candidate
  `exv1-2ea82d10c3459d4a4249b875c0ec1cbe594bc81a1c1b541f2fe85554b6854b28`
- checksum-pinned source PDF and preserved producer artifacts
- PDF outline and explicit `/PageLabels` metadata when actually present
- visible TOC/index blocks, furniture labels, and exact canonical anchors
- requested on-demand review-cache renders

## Outputs

- responsibility-specific semantic-structure mapping and validation code
- a package-backed command and checked-in Appendix P configuration
- a new immutable non-release canonical candidate under the existing canonical
  candidate lifecycle
- semantic section, membership, hierarchy-evidence, page-label, and alias
  outputs exactly as accepted in Task 03E.1
- old-to-new canonical correspondence and independent Task 03D.1 preservation
  report
- manifest, inventory, summary, warnings/errors, and completion-last record
- fixtures and tests for hierarchy mapping, labels, aliases, ordering,
  ambiguity, publication, reuse, and failure retention

## Research / learning checkpoint

Trace representative accepted Docling headings through canonical section
construction and exact low-level anchors. Trace one visible TOC entry into alias
and reconciliation evidence without treating it as a body boundary. Trace one
resolved visible printed label while retaining its physical page number and
source block.

The outcome must explain:

- **Thin glue still owns invariants.** Package output does not remove the need
  for schema validation, exact ordering, provenance, identity, or atomic
  publication.
- **Cross-version preservation is semantic correspondence.** Every canonical ID
  contains the new extraction ID, so literal Task 03D.1 IDs cannot be reused.
- **Furniture is not semantic body structure.** Repeated page furniture stays
  under the furniture root unless the accepted contract names a narrow
  exception.
- **Aliases are targets, not mentions.** Mention extraction remains Task 03E.3.

## Plan / spec requirement

Before implementation, write the short stage plan naming:

1. module and public command boundaries;
2. verified Task 03E and Task 03D.1 inputs;
3. candidate identity inputs and artifact paths;
4. hierarchy, label, alias, correspondence, and warning construction stages;
5. exact allowed-difference normalization;
6. atomic publication, no-clobber reuse, and failed-attempt behavior;
7. on-demand review pages and review-cache recipes; and
8. acceptance and rollback/stop behavior.

## Review pass

- **Tool boundary:** hierarchy levels come from accepted Docling output.
- **Preservation:** every undeclared Task 03D.1 value remains equivalent.
- **Order and containment:** roots, semantic sections, pages, and mixed content
  have exact forward/inverse relationships.
- **Labels and aliases:** evidence, conflicts, unknowns, collisions, and
  provenance follow the accepted contract.
- **Maintainability:** construction, validation, comparison, and publication
  have clear responsibility owners.

## Validation

- Verify all input completion records and inventories before construction.
- Require the accepted 222 pages, 3,706 blocks, 19 tables, 3,669 clean cells,
  19 families, 27 figures, 27 images, 146 assets, 34 table observations, and
  3,798 raw mappings unless Task 03E's explicitly accepted item promotion
  changes a declared record-family count.
- Compare ordered text, mixed content, tables/cells/CSVs/families,
  figures/images/assets, observations, valid geometry, rejected raw geometry,
  raw mappings, warnings, and errors under only the declared normalization.
- Validate exact ordered inverse section membership and retained roots.
- Validate physical pages, explicit PDF labels, visible-label observations,
  resolved labels, ambiguity, and aliases.
- Verify every TOC-derived alias points to its reconciled body target and no
  visible TOC row becomes a semantic section start or alias target.
- Independently rebuild fresh staging and require byte-identical
  candidate-owned files.
- Verify checksum-valid reuse and one preserved simulated failure.
- Inspect only the predeclared requested review-cache sample.
- Confirm no mention or resolution-candidate records were introduced.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- The candidate is reproducible, schema-valid, checksum-verified, and
  completion-last published without changing completed inputs.
- Accepted Docling hierarchy is mapped without a competing inference algorithm.
- Every undeclared Task 03D.1 semantic has exact verified correspondence.
- Roots, sections, content membership, page labels, aliases, evidence, and
  ambiguity satisfy the Task 03E.1 contract.
- Review-cache renders are disposable and absent from candidate identity and
  completeness.
- The outcome requests user review before Task 03E.3 activates.

## Non-goals

- rerunning or retuning Docling
- custom hierarchy repair
- cross-reference mentions, resolution candidates, or corpus graph edges
- processing another complete document
- corpus batching, retrieval, usability review, or LLM work
