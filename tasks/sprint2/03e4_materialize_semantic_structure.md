# Task 03E.4: Materialize Semantic Structure for Appendix P

Status: **active as of 2026-07-31 by explicit user approval**. This contract
incorporates the accepted Task 03E.3 outcome and is ready for implementation in
a new chat.

## Abstract

Implement the accepted canonical-extraction schema-major v2 semantic-structure
contract as thin project-owned glue over the Task 03E.2d-accepted corrected
hierarchy. Combine the changed v2 definitions with the otherwise unchanged v1
record families and publish a new immutable Appendix P canonical candidate.
The candidate extends existing section and content records, emits one printed-
page-label observation per physical page, adds deterministic target aliases,
and records exact correspondence to the Task 03D.1 core records.

The RFC 8785 plus SHA-256 extraction-ID algorithm and `exv1-` prefix remain
unchanged, but the expanded identity payload must produce a candidate ID
different from the Task 03D.1 candidate. Task 03E.3 defined the identity and
bridge policies and verified their real handoff facts; it did not publish a
candidate identity or candidate-owned bridge artifact.

Visible TOCs and the PDF outline carry Task 03E.2d-accepted reconciliation
evidence and support validation and aliases. The accompanying bounded-
acceptance record remains visible provenance. These inputs do not authorize new
materialization-local hierarchy inference.

## Goal

Produce the first complete semantic canonical document while proving that all
undeclared Task 03D.1 content, table, figure, asset, observation, geometry,
ordering, warning, and lineage semantics remain unchanged.

## Inputs

- accepted [`semantic_structure_v2.md`](../../docs/specs/semantic_structure_v2.md),
  executable schema under
  `benchmarks/er_bench/schemas/canonical_extraction/v2/`, fixtures, identity
  and equivalence policies, and the responsibility-owned
  `er_commons.semantic_structure` validator and sealed-input handoff
- exact Task 03E.2d hierarchy-correction candidate
  `hcorv1-aab01b14c3122dbc0f5cec57147b5be2eadaf1cd895311ef7dafa46b469348b1`,
  status `complete_with_ambiguities`, its 15 managed files, artifact-inventory
  canonical digest
  `8242a22aab347b17964562081e3a4f1f38b2efec23480aed07b770c2ada35c3a`,
  semantic-file-set digest
  `75a0e36c7e5814d5135763a09c7374643fdd5e0edafd30de360bb954345dd3d2`,
  and aggregate semantic-payload digest
  `c3036210f5698a295ca799ee25d1850a080f0a5d211bef303b94900882cb4db8`
- external bounded-acceptance authorization SHA-256
  `5335737128fcbac2b1f2d41c42712af0534e2d15141ccf1150c37ffbf70f328c`,
  status `accepted_with_known_limitations`, exact seven ordered limitations,
  and authorized Appendix P/222-page Task 03E.4 scope
- immutable Task 03D.1 candidate
  `exv1-2ea82d10c3459d4a4249b875c0ec1cbe594bc81a1c1b541f2fe85554b6854b28`
- Task 03D.1 baseline producer
  `prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0`,
  Task 03E hierarchy producer
  `prv1-92170ee8b5f5d51ffa738749ee872d7c7e9e5e7dbcb16cf6150bcf33d10d68e1`,
  and producer-comparison report SHA-256
  `33574f6b15dc128a7bf58d6e2ab1a35c867ce1df493fe317a46bed1b8e8bf364`
- checksum-pinned source PDF, producer completions and inventories, preserved
  producer artifacts, and Task 03D.1 raw-to-canonical mappings needed to build
  an independently evidenced real bridge
- PDF outline and verified absence of explicit Appendix P `/PageLabels` metadata
- visible TOC blocks, furniture labels, and exact canonical anchors

## Outputs

- responsibility-specific construction, application, comparison, identity,
  and publication code that invokes the accepted v2 schema and
  `er_commons.semantic_structure` policies rather than creating a parallel
  semantic validator
- a package-backed command and checked-in Appendix P configuration
- a new immutable, closed canonical-extraction v2 non-release candidate under
  the existing canonical candidate lifecycle
- extended existing section records and block/table/figure semantic-placement
  fields, exactly 222 page-label observations, and one target-alias record
  family as accepted in Task 03E.3; no other semantic or observation family
  may be invented
- compact canonical hierarchy-provenance references; detailed correction
  features, TOC reconciliation, regimes, decisions, ambiguities, and warnings
  remain in Task 03E.2d evidence
- exactly four checksummed support artifacts with schema role
  `cross_producer_bridge`, `candidate_correspondence`,
  `baseline_preservation`, and `bounded_control_verification`; none is a
  canonical record family
- manifest, inventory, summary, warnings/errors, and completion-last record
- fixtures and tests for hierarchy mapping, labels, aliases, ordering,
  ambiguity, publication, reuse, and failure retention
- disposable review-cache source renders and semantic overlays for the exact
  predeclared sample below

## Research / learning checkpoint

Trace representative accepted corrected headings back through raw Docling
evidence and forward through canonical section construction and exact low-level
anchors. Trace one visible TOC entry into alias and reconciliation evidence
without treating it as a body boundary. Trace one resolved visible printed
label while retaining its physical page number and source block.

The outcome must explain:

- **Thin glue still owns invariants.** Package output does not remove the need
  for schema validation, exact ordering, provenance, identity, or atomic
  publication.
- **Cross-version preservation is semantic correspondence.** Every canonical ID
  contains the new extraction ID, so literal Task 03D.1 IDs cannot be reused.
- **Furniture is not semantic body structure.** Repeated page furniture stays
  under the furniture root unless the accepted contract names a narrow
  exception.
- **Aliases are targets, not mentions.** Mention extraction remains Task 03E.5.

## Plan / spec requirement

Before implementation, write the short stage plan naming:

1. module and public command boundaries;
2. verified Task 03E.2d correction candidate/evidence and Task 03D.1 canonical
   inputs;
3. construction of the candidate-owned cross-producer bridge from the
   independently verified producer pointer/disposition index and its exact
   coverage rules;
4. every candidate identity input named by the accepted v2 specification,
   including upstream completions and inventories, both semantic digest roles,
   bounded control, specification, schema, configuration, bridge, and owned
   code;
5. hierarchy, mixed-content membership, label, alias, correspondence, and
   warning construction stages;
6. exact allowed-difference normalization;
7. atomic publication, no-clobber reuse, and failed-attempt behavior;
8. the exact review sample and source-render/semantic-overlay recipe; and
9. acceptance and rollback/stop behavior.

## Predeclared visual review sample

Generate review-cache source renders and semantic overlays for exactly these
Appendix P physical pages after the candidate passes machine validation:

| Physical page | Review purpose |
| ---: | --- |
| 2 | Page with no Task 03E.2d item-feature row; verify an explicit page-label outcome independent of item presence. |
| 4 | Primary visible TOC; verify TOC rows stay body content and aliases target reconciled body sections, not TOC blocks. |
| 8 | Accepted `Existing SSF District` level disagreement and a visible printed label; verify the limitation remains visible without local repair. |
| 73 | First accepted false table boundary plus canonical table/figure mixed-content placement. |
| 82 | Second accepted false table boundary plus canonical table placement on a landscape page. |
| 96 | Held-out `9 CONCLUSIONS` level/parent disagreement and resolved printed label. |
| 105 | Held-out `Appendix B` root/parent case and an unlabeled appendix separator page. |
| 112 | Embedded visible TOC page; verify TOC isolation and reconciled target aliases. |
| 166 | Held-out nested heading level/parent disagreement with visible printed-label evidence. |
| 220 | `Appendix E` root and the post-03E.2a nested-regime exit boundary. |

Each overlay must show physical page identity, source and resolved printed-label
state, retained content in canonical mixed order, direct section membership and
section path, heading ownership, table/figure replacement positions, and alias
targets present on the page. Compare it with the source render and a compact
record diagnostic. This review verifies comprehensibility and catches mapping
or rendering mistakes; it must not change the accepted hierarchy, page-label,
alias, bridge, or preservation policies. Renders and overlays remain disposable
review-cache derivatives outside candidate identity and completeness.

## Review pass

- **Correction boundary:** hierarchy roles and levels come from the accepted
  Task 03E.2d artifact; this task does not rerun or reinterpret correction
  rules or hide its accepted limitations.
- **Preservation:** every undeclared Task 03D.1 value remains equivalent.
- **Order and containment:** roots, semantic sections, pages, and mixed content
  have exact forward/inverse relationships.
- **Labels and aliases:** evidence, conflicts, unknowns, collisions, and
  provenance follow the accepted contract.
- **Maintainability:** construction, validation, comparison, and publication
  have clear responsibility owners, while the accepted semantic-policy modules
  remain the single validator authority.

## Validation

- Verify all input completion records, inventories, managed file sets, and
  candidate-owned bytes before construction.
- Verify the exact Task 03E.2d candidate ID, `complete_with_ambiguities` status,
  15 managed files, artifact-inventory digest, semantic-file-set digest,
  aggregate-payload digest, bounded-acceptance checksum and status, seven
  ordered limitations, authorized scope, both producer IDs, and producer-
  comparison checksum.
- Require the accepted 222 pages, 3,706 blocks, 19 tables, 3,669 clean cells,
  19 families, 27 figures, 27 images, 146 assets, 34 table observations, and
  3,798 raw mappings. Permit only the v2 section/content extensions, exactly
  222 page-label observations, and the target-alias family; require exactly the
  four declared support artifacts.
- Apply only the five accepted difference categories: identity/schema,
  semantic sections/membership, page-label resolution/observations, target
  aliases, and semantic support/completion. After extraction-ID normalization,
  require byte-equivalence for every other Task 03D.1 semantic, including page
  and global mixed-content order, text, tables/cells/CSVs/families,
  figures/images/assets, observations, valid geometry, rejected raw geometry,
  raw mappings, baseline warnings, and errors.
- Validate exact ordered inverse section membership and retained roots.
- Build and validate the real candidate-owned bridge against independently
  supplied producer evidence. Require all 6,931 producer stable keys to remain
  aligned, 246 accepted headings to map uniquely, and all 4,571 direct members
  to resolve as exactly 2,255 mapped blocks, 2,314 table-replacement
  descendants, and two figure-suppression descendants. Permit only
  `canonical_table_replacement_descendant` and
  `canonical_figure_suppressed_descendant` as unmapped dispositions.
- Validate exact placement of heading blocks, ordinary blocks, two pre-root
  content items, visible TOC rows, tables, figures, and furniture without
  materialization-local inference.
- Validate physical pages, explicit PDF labels, visible-label observations,
  resolved labels, ambiguity, and aliases. Require exactly 222 ordered page
  outcomes even though Task 03E.2d features represent 221 pages: 167 represented
  pages have non-null visible labels, 54 represented pages have no visible
  label, and physical page 2 has no item-feature row. Verify page-wide consensus
  before resolving visible evidence, and reject synthesized pypdf `1` through
  `222` defaults as source evidence.
- Verify every TOC-derived alias points to its reconciled body target and no
  visible TOC row becomes a semantic section start or alias target.
- Independently rebuild fresh staging and require byte-identical
  candidate-owned files.
- Verify checksum-valid reuse and one preserved simulated failure.
- Inspect only the ten predeclared review-cache pages after machine validation;
  any visual discrepancy stops publication or acceptance for diagnosis but
  does not authorize policy tuning inside this task.
- Confirm no mention or resolution-candidate records were introduced.
- Require successful materialization with inherited warnings to publish status
  `complete_with_warnings`, while preserving the distinct source semantic
  disposition `accepted_with_known_limitations`. Treat unknown labels and
  represented alias collisions as non-fatal; treat bridge/control/schema/
  preservation failures as fatal.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- The candidate is reproducible, schema-valid, checksum-verified, and
  completion-last published without changing completed inputs.
- The candidate is a closed canonical-extraction v2 bundle with a new `exv1-`
  ID, exactly the accepted v2 record extensions, and exactly four inventoried
  support artifacts.
- The Task 03E.2d-accepted hierarchy is mapped without changing its correction
  policy or bounded-acceptance provenance.
- Every undeclared Task 03D.1 semantic has exact verified correspondence.
- Roots, sections, content membership, page labels, aliases, evidence, and
  ambiguity satisfy the Task 03E.3 contract.
- The bridge and preservation gates match the frozen counts and permit no
  undeclared difference or unmapped disposition.
- Machine status is `complete_with_warnings`; source semantic disposition stays
  `accepted_with_known_limitations` and cannot impersonate a strict pass.
- Review-cache renders are disposable and absent from candidate identity and
  completeness.
- The outcome requests user review before Task 03E.5 activates.

## Non-goals

- rerunning or retuning Docling
- changing or bypassing Task 03E.2d-accepted hierarchy correction
- cross-reference mentions, resolution candidates, or corpus graph edges
- processing another complete document
- corpus batching, retrieval, usability review, or LLM work
