# Task 03E.3: Define the Semantic-Structure Contract

Status: **complete as of 2026-07-31 after human-ownership rewrite**. The schema
and behavioral MVP remain reference evidence; the repository implementation is
the responsibility-owned validator described in the outcome. This task did not
publish a live canonical candidate.

## Abstract

Translate the Task 03E.2d-accepted corrected hierarchy into a project-owned
contract for semantic sections, ordered membership, printed-page-label
evidence, resolved page labels, and deterministic target aliases. Decide which
evidence belongs in canonical records and which belongs in checksummed
supporting observations before implementation.

This task is a specification gate, not a fourth persisted data layer. Extend
the existing canonical section and page concepts where sufficient; do not copy
the complete correction evidence into parallel canonical record families.

Keep the accepted Task 03D.1 candidate as immutable core-content reference
evidence. Define a new candidate identity and an exact allowed-difference gate
for Task 03E.4 rather than modifying the completed candidate in place.

## Goal

Make the hierarchy, page-label, alias, identity, provenance, and publication
rules executable and independently reviewable so Task 03E.4 can remain thin
mapping and validation glue around accepted corrected-hierarchy output.

## Inputs

Exact Task 03E.2d semantic input:

- completed
  [`03e2d_accept_and_publish_hierarchy_correction.md`](03e2d_accept_and_publish_hierarchy_correction.md),
  [`hierarchy_correction_v1.md`](../../docs/specs/hierarchy_correction_v1.md),
  correction-v1 schemas, and human-owned validator
- hierarchy-correction candidate
  `hcorv1-aab01b14c3122dbc0f5cec57147b5be2eadaf1cd895311ef7dafa46b469348b1`
  under
  `pipelines/brisbane_baylands/task_03e2_hierarchy_correction/<candidate_id>/`
- its 15 managed candidate files, including
  `records/completion_record.json`, `records/identity.json`,
  `records/input_inventory.json`, `records/artifact_inventory.json`, and the
  eight semantic artifacts under `artifacts/`
- candidate completion status `complete_with_ambiguities` and artifact-
  inventory SHA-256
  `8242a22aab347b17964562081e3a4f1f38b2efec23480aed07b770c2ada35c3a`
- candidate semantic-file-set SHA-256
  `75a0e36c7e5814d5135763a09c7374643fdd5e0edafd30de360bb954345dd3d2`,
  which hashes the ordered semantic artifact paths and their byte checksums
- frozen aggregate semantic-payload SHA-256
  `c3036210f5698a295ca799ee25d1850a080f0a5d211bef303b94900882cb4db8`,
  which hashes the reconstructed canonical JSON aggregate used for Task
  03E.2a/03E.2b semantic equivalence
- frozen counts: 6,931 features and decisions, 140 visible-TOC entries and
  reconciliations, two regimes, 12 roots, 234 edges, 4,571 direct memberships,
  two unassigned content items, 17 ambiguities, and 148 warnings

Exact Task 03E.2d control input, which is not semantic content and must not be
copied into a canonical record family:

- `pipelines/brisbane_baylands/task_03e2_hierarchy_review/<candidate_id>/`
  `bounded_acceptance.json`, SHA-256
  `5335737128fcbac2b1f2d41c42712af0534e2d15141ccf1150c37ffbf70f328c`
- status `accepted_with_known_limitations`, authorization ID
  `brisbane_baylands_2025_deir_task03e2d_bounded_acceptance_v1`, Appendix P
  222-page scope, and authorized Task 03E.3/03E.4/03G uses
- all seven limitation categories and the historical Task 03E.2 rejection,
  Task 03E.2a reference, and Task 03E.2b equivalence evidence checksum-pinned by
  that authorization
- [Decision 004](../../docs/decisions/004_accept_appendix_p_hierarchy_with_known_limitations.md),
  which owns the bounded human disposition

Canonical and bridge inputs:

- [`architecture.md`](../../docs/architecture.md),
  [`data_artifacts.md`](../../docs/data_artifacts.md), and
  [`documentation.md`](../../docs/documentation.md) for current layer,
  provenance, and documentation ownership boundaries
- completed Task 03B canonical contract, executable schemas, fixtures, and
  human-owned cross-record validators
- immutable Task 03D.1 canonical candidate
  `exv1-2ea82d10c3459d4a4249b875c0ec1cbe594bc81a1c1b541f2fe85554b6854b28`,
  its 57-path equivalence evidence, and
  [`task03d_appendix_p_mapping_v1.md`](../../docs/specs/task03d_appendix_p_mapping_v1.md)
- the Task 03D.1 baseline producer
  `prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0`
  and the separate Task 03E hierarchy producer
  `prv1-92170ee8b5f5d51ffa738749ee872d7c7e9e5e7dbcb16cf6150bcf33d10d68e1`
- Task 03E producer comparison
  `pipelines/brisbane_baylands/task_03e_hierarchy_review/`
  `cmpv2-9106e5d03fa4f1e8f57eadd2b1aa8cc0a02030131f9684964caf6bea86f3aff0/`
  `producer_comparison_report.json`, SHA-256
  `33574f6b15dc128a7bf58d6e2ab1a35c867ce1df493fe317a46bed1b8e8bf364`,
  whose machine-pass comparison binds those producer IDs, matches all 159
  artifact paths, and records hierarchy-aware equality for `document.json`
- both producers' checksum-pinned Docling item pointers and the Task 03D.1 raw-
  to-canonical mappings needed to define an exact cross-producer bridge
- current page, section, manifest, identity, completion, observation, bundle,
  ordering, and publication contracts in
  `benchmarks/er_bench/schemas/canonical_extraction/v1/` and
  `src/er_commons/canonical_extraction/`

Source-only observations used to define new canonical policy, not to change
the accepted hierarchy:

- checksum-pinned Appendix P PDF outline, visible TOC blocks, body/furniture
  layers, canonical order, page geometry, and raw lineage
- verified Appendix P fact that the 222-page PDF has no explicit
  `/PageLabels`; pypdf's `1` through `222` values are synthesized defaults and
  are not source evidence
- Task 03E.2d `item_features.jsonl`, whose `printed_page_label` is visible-
  footer evidence: it represents 221 physical pages, has a non-null label on
  167 pages, has 54 represented pages with no label, and contains no item for
  physical page 2
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12),
  [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html), and
  [ISO 32000-2:2020 section 12.4.2 page-label semantics](https://pdf-issues.pdfa.org/32000-2-2020/clause12.html)
  needed to distinguish explicit metadata from library defaults

## Outputs

- a revised semantic-structure specification
- executable schema changes or new schemas for:
  - semantic section level, path, ordered containment, and inference provenance;
  - printed-label observations, evidence methods, conflicts, unknown states, and
    the resolved nullable page value;
  - deterministic document, appendix, section, table, figure, and printed-page
    target aliases; and
  - old-candidate to new-candidate semantic correspondence, defaulting to a
    checksummed comparison/report artifact rather than a canonical record family
    unless a demonstrated runtime consumer requires it
- explicit decisions identifying canonical fields, canonical observations, and
  checksummed support artifacts
- revised ID, ordering, serialization, status, manifest, and completion rules
- an order-sensitive section hierarchy validator
- fixtures covering bookmarks, numbering, missing/skipped levels, repeated
  headings, heading-block ownership, pre-root content, TOC rows, furniture,
  tables, figures, embedded numbering resets, explicit and absent `/PageLabels`,
  visible-only labels, fully unlabeled pages, conflicts, aliases, and ambiguity
- a compact limitation-propagation specification referencing, without copying,
  the checksum-pinned evidence for the two observed false table boundaries,
  frozen R04/R05 attribution disagreements, `Existing SSF District` level
  disagreement, page-2000 R06 ambiguity, and complete inherited ambiguity and
  warning artifacts
- an exact Task 03D.1-to-03E.4 preservation/equivalence specification
- an exact cross-producer bridge specification mapping accepted Task 03E.2d
  stable item keys and Task 03E raw pointers to Task 03D.1 canonical records,
  including one-to-one coverage, collisions, missing mappings, and permitted
  unmapped categories
- a 222-page label-coverage rule independent of whether a page has a Docling
  text item or visible footer
- a compact, checksummed control-provenance reference that lets a downstream
  candidate distinguish strict acceptance from `accepted_with_known_limitations`
  without copying the external authorization or its historical review evidence
  into canonical semantic content
- an explicit no-duplication decision keeping detailed features, TOC rows,
  reconciliations, regimes, rule decisions, ambiguities, and warnings in the
  checksum-pinned Task 03E.2d evidence unless a demonstrated canonical consumer
  requires a compact field or observation

## Research / learning checkpoint

Compare strict-schema evolution against a separate observation/support-artifact
design. Prefer the smallest representation that preserves evidence and supports
later review, citation rendering, and cross-reference matching without
duplicating the accepted producer document.

Read the named JSON Schema, JSON canonicalization, and PDF page-label sources
before freezing shapes. Record why the selected representation fits the
existing strict canonical bundle and which facts remain referenced supporting
evidence rather than copied canonical content.

The outcome must explain:

- **Raw, corrected, and canonical hierarchy have different owners.** Docling
  supplies immutable observations, Task 03E.2b implements corrected roles and
  levels, Task 03E.2d accepts and publishes them with known limitations, and
  this contract owns stable canonical records, provenance, invariants, and
  downstream isolation.
- **Physical pages and printed labels are separate identities.** Distinguish
  internal indices, one-based PDF pages, explicit PDF `/PageLabels`, synthesized
  library defaults, and visible printed labels. The current Appendix P has no
  explicit `/PageLabels`; its accepted correction feature is visible-footer
  evidence and is not by itself a canonical resolved label.
- **The join crosses two preserved producer identities.** Task 03D.1 and Task
  03E.2d derive from distinct complete-document producer candidates. Shared raw
  pointers and verified producer comparison evidence may support a bridge, but
  canonical membership cannot assume their internal IDs are interchangeable.
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
   or checksummed support artifact, defaulting to referenced Task 03E.2d
   evidence rather than duplication;
3. schema compatibility and versioning decision;
4. semantic-section start, end, parent, path, level, and direct-membership rules;
5. exact mixed-content projection for heading blocks, ordinary body blocks,
   the two unassigned content items, visible TOC rows, tables, figures, and
   retained furniture, with body-only semantic induction by default;
6. physical-page, explicit-page-label, visible-label, resolved-label, unknown,
   and conflict semantics across all 222 pages, independent of item presence;
7. alias normalization, collision behavior, evidence, order, and target types,
   requiring every TOC-derived alias to resolve to a non-TOC canonical target;
8. the exact cross-producer bridge, coverage and collision rules, and raw-to-
   canonical correspondence used by Task 03E.4;
9. candidate identity, old/new correspondence, atomic publication, verified
   reuse, and failure preservation;
10. exact verification and compact downstream reference of the bounded-
    acceptance control, including its seven limitations and authorized scope;
11. inherited versus new warnings and fatal/ambiguous states, without treating
    the main-report page-2000 control as an Appendix P canonical warning;
12. exact permitted differences from Task 03D.1; and
13. the Task 03E.4 implementation and review handoff.

## Review pass

- **Schema sufficiency:** every promised output is representable without hidden
  side files or unvalidated extra properties.
- **Correction boundary:** the contract maps the Task 03E.2d-accepted corrected
  hierarchy without changing its rules, hiding its raw Docling evidence, or
  erasing its bounded-acceptance limitations.
- **Bridge:** every hierarchy node and direct-membership item either maps
  uniquely through verified raw evidence to a compatible Task 03D.1 canonical
  record or has one explicitly permitted unmapped disposition.
- **Order:** ordered children exactly invert parent/section links in canonical
  mixed-content order.
- **Identity:** no completed candidate is rewritten and cross-version
  correspondence is explicit.
- **Review isolation:** Task 04 reviewer, usability, and disposition fields
  remain forbidden from Task 03 records.

## Validation

- Validate positive and negative fixtures against every revised schema.
- Test order-sensitive hierarchy, cycles, skipped levels, repeated headings,
  root continuity, heading-block ownership, pre-root content, tables, figures,
  TOC content, body/furniture isolation, and exact inverse membership.
- Test exact cross-producer pointer/key correspondence, full coverage, type
  compatibility, duplicate targets, missing mappings, and changed producer
  evidence.
- Test explicit `/PageLabels`, absent metadata, synthesized-default rejection,
  visible-footer source anchors, conflicting evidence, repeated regimes,
  pages with no text item, all 222 page outcomes, and unknown states.
- Test deterministic alias order, normalization, collisions, provenance, and
  target-type restrictions.
- Test identity change, cross-version correspondence, manifest agreement, and
  declared allowed differences.
- Verify the exact completion, inventory, both semantic digest forms, bounded-
  acceptance SHA, status, candidate binding, authorized scope, and seven-
  limitation inventory; fail closed for any change.
- Verify digest-backed limitation expectations preserve rather than silently
  repair, accept as correct, or hide every tolerated limitation and inherited
  ambiguity/warning; do not copy historical evidence into tracked fixtures.
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
  ordering, bridge, membership, evidence, or publication policy.
- The contract retains the synthetic roots while replacing flat body
  membership with semantic sections derived from the accepted-with-known-
  limitations hierarchy and defines exact placement for every retained block,
  table, figure, TOC item, furniture item, and pre-root content item.
- The contract creates no persisted intermediate semantic dataset and does not
  duplicate detailed Task 03E.2d correction evidence in canonical records.
- Printed labels never replace physical PDF identity.
- Every physical page has one explicit resolved-label outcome, including
  `unknown`; synthesized library defaults never count as source evidence.
- Downstream provenance distinguishes `accepted_with_known_limitations` from a
  strict quality pass and retains the exact authorization binding without
  turning external control/review evidence into canonical content.
- Aliases identify canonical potential targets but contain no extracted
  mentions or mention-derived candidates, and no TOC row is itself an alias
  target.
- Exact preservation requirements protect all undeclared Task 03D.1 semantics.
- The outcome requests user review before Task 03E.4 activates.

## Non-goals

- running Docling or publishing a live canonical candidate
- changing Task 03E.2d-accepted correction behavior or its limitation record
- cross-reference mention extraction or target resolution
- corpus identity, batching, or cross-document resolution
- Task 04 usability judgments
- retrieval units, indexing, or graph traversal

## Outcome

The Task 03E.3 behavioral MVP is complete. It defines canonical-extraction
schema major v2 while
preserving strict v1 and the immutable Task 03D.1 candidate. The contract
extends sections rather than creating another semantic layer, emits one page-
label outcome per physical page, introduces target-only aliases, and keeps
bridge, correspondence, preservation, and bounded-acceptance verification as
checksummed support artifacts.

The executable schema, positive/negative fixtures, and human-owned validator
cover exact ordered hierarchy inversion, sparse accepted levels, repeated
headings, heading ownership, pre-root and TOC content, furniture, tables,
figures, page-label provenance and conflicts, alias collisions and target
restrictions, cross-producer bridge coverage, the two permitted replacement
dispositions, old/new allowed differences, and exact Task 03E.2d control
binding. Fixtures contain no mention-derived cross-reference candidates.

The read-only handoff audit verified all 15 Task 03E.2d managed files and the
candidate-bound authorization. It distinguished the inventory digest,
semantic-file-set digest, and reconstructed aggregate digest; confirmed all
6,931 stable keys in the producer comparison; and established that all 246
headings map uniquely to canonical blocks. Of 4,571 direct members, 2,255 map
to blocks and exactly 2,316 use the evidence-backed table-replacement or
picture-suppression dispositions. Appendix P has no explicit `/PageLabels`;
the contract rejects pypdf's synthesized defaults and requires 222 page
outcomes independently of text-item presence.

Research retained JSON Schema Draft 2020-12 for strict shapes, RFC 8785 for
identity serialization, and ISO 32000-2 page-label semantics. The closed v1
shapes and meaning changes require a schema major; the unchanged identity hash
algorithm retains the `exv1-` prefix while the expanded payload creates a new
candidate.

The accepted behavioral MVP was then rewritten for human ownership. The public
facade now only sequences named policy modules for sections, page labels,
aliases, bridge evidence, control provenance, and candidate correspondence;
shared indexing, normalization, and sealed-input handoff each have one explicit
home. Bridge validation requires independently supplied producer evidence, so
the persisted payload cannot authenticate its own pointers or unmapped
dispositions. Tests use named fixture selectors and describe the invariant each
mutation protects.

Two independent final reviews passed: the maintainability review found the code
readable, understandable, debuggable, and editable, and the refactor-safety
review rejected all adversarial counterexamples. Focused validation passed 40
tests. Full `make fix`, `make check`, and `git diff --check` passed with 372
tests, Ruff, and mypy. A final read-only audit reverified the real 222-page
sealed handoff and its `accepted_with_known_limitations` control. No producer
ran and no external candidate was published. Task 03E.4 remains inactive
pending revision and explicit activation.
