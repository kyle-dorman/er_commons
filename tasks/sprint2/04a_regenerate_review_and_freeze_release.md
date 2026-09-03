# Task 04A: Regenerate the Final Review Dataset and Freeze the Release

Status: **complete; Gate D release frozen on 2026-09-03**.

## Abstract

With Task 03J's fresh 35-source extraction now complete, generate a new document
review dataset bound only to the Task 03J corpus and evidence identities. Recheck
the accepted Task 04 extraction findings against their Task 03I dispositions,
review fresh stratified and risk-triggered evidence, and conduct a complete
candidate review of document-level and embedded table-of-contents structures.
Record human usability separately from immutable machine artifacts and either
freeze the accepted release or stop with an exact handoff to provisional [Task
04B](04b_remediate_toc_navigation_and_reprocess.md) or another bounded
remediation task.

This is a new review run, not a continuation of the Task 03H-backed Task 04
bundle. Task 04 items may identify what needs rechecking, but their canonical
IDs, checksums, page anchors, renders, and approval state cannot transfer.

## Goal

1. Produce a deterministic, reviewable dataset derived from the completed Task
   03J handoff without relying on conversation history or stale Task 03H anchors.
2. Verify every applicable Task 04 extraction finding after Task 03I remediation
   and inspect fresh all-source risk samples.
3. Inventory and review every machine-detectable potential TOC, document index,
   list of tables, list of figures, and embedded section TOC so navigation
   evidence is not silently represented as an ordinary table or body hierarchy.
4. Human-review every ambiguous TOC-derived reference link, including links
   made ambiguous because multiple navigation rows compete for one body target.
5. Publish a separate human-usability registry and an exact release-freeze
   record, or stop with an evidence-anchored remediation decision and a
   checksummed Task 04B handoff.

## Prerequisites and inputs

Activation requires the completed outcomes, validators, and immutable handoffs
from:

- [Task 04](04_review_extraction_and_freeze_release.md): the approved first-pass
  finding register, exact Task 03I handoff, review selection policy, and qualified
  review-workspace implementation;
- [Task 03I](03i_remediate_task04_review_findings.md): the closed disposition of
  every accepted extraction finding and its disposition digest; and
- [Task 03J](03j_run_final_canonical_extraction.md): the fresh corpus identity,
  all 35 terminal source records, machine-candidate handoff, canonical manifests,
  checksums, validator results, and reproducible render inputs.

The primary Task 03J anchors are now frozen:

- production identity
  `exv1-6913f56bed93302d7cf5ef424ee63c0b7427e90e2b2cd5c4ec483d275009a773`;
- scope `scopev1-bd4b7ca85b299ae528376b1a6e88b9d0fdba02e4f7e8862c5fa91a28b719e893`;
- ready handoff
  `handoffv1-44d510d545026a427ccdb47497d30f1d46c66130291af66fc0d5883a35102325`;
- handoff completion at
  `pipelines/brisbane_baylands/task_03h_clean_full_v4/document_publications/scopes/scopev1-bd4b7ca85b299ae528376b1a6e88b9d0fdba02e4f7e8862c5fa91a28b719e893/handoffs/handoffv1-44d510d545026a427ccdb47497d30f1d46c66130291af66fc0d5883a35102325/records/completion_record.json`,
  SHA-256
  `8bd72f2712a20de5aa865575566e4d5b187d7fccc02ba02dd0f92d87bf04117a`;
  and
- validator result: 35 verified documents, ready status, and
  `task04_status: not_evaluated`.

The following candidate-level dependencies must still be recorded during Task
04A activation from that validated handoff:

- the exact Task 03J corpus, candidate, source, attempt, and implementation
  identities;
- artifact-relative paths and checksums for canonical pages, text, tables,
  table families, warnings, provenance, parser-attempt evidence, and render
  inputs;
- the final Task 03J handoff schema and validator interface;
- which Task 04 findings remain applicable and the exact Task 03J evidence that
  can recheck each one;
- the available Task 03J hierarchy, visible-TOC, document-index, canonical
  placement, target-alias, parser-route, and table-provenance evidence needed to
  build the TOC candidate census; and
- any new warning, failure, table, geometry, or provenance populations that
  require a revised risk stratum.

If any prerequisite is absent or ambiguous, stop and repair the owning upstream
handoff. Do not reconstruct it from Task 03H artifacts or conversation history.

## Source-free MVP preparation outcome

On 2026-09-02, the source-free preparation published:

```text
pipelines/brisbane_baylands/task_04_review/
  reviewv1-task03j-final-b19a7a36b04bda89/records/gate_a_preparation.json
```

The record is bound to the frozen `task03j_final` production identity,
scope, and handoff above. It accounts for all 35 Task 03J terminal sources and
the one approved Task 03I finding recheck. It freezes the selection, recheck,
TOC signal, adjacency, and approval policies. The production machine-artifact
census is now complete and marked `completed`. It reports 5,624 candidate
pages, 3,433 seed pages, 2,191 adjacent pages, 9,421 ambiguous aliases, 725
ambiguous links, 206 raw document-index objects, and 60 substantive-table
controls. Three sources have zero machine-detectable candidates and remain
explicit source census entries.

The preparation record reports `source_pdf_bytes_read: false`,
`source_pdf_checksum_verified: false`, `renders_generated: false`,
`model_files_read: false`, and `human_review_started: false`. It used the prior
read-only Task 03J validator evidence rather than rerunning an expensive
validator/checksum pass. This is a preparation boundary, not a usability
registry or release freeze, and it does not satisfy the full acceptance
criteria below. This completes Gate B's source-free qualification.

## Gate C machine execution outcome

The original Gate C package incorrectly presented every census page as a valid
page and is superseded. The corrected six-tab reviewer is:

```text
pipelines/brisbane_baylands/task_04_review/
  reviewv1-task03j-final-c17/
```

It contains 0 failure cards, 9 warning cards, 129 valid-page cards including
the Task 03I recheck, 44 table-family cards, 117 stable TOC-review run cards,
and 224 stable machine-positive TOC page cards. Labels no longer change card
membership; Hide reviewed is the pending-only filter. All 341 TOC cards are
currently labeled by the merged export. Both tabs provide explicit TOC and Not
TOC controls, with click-again-to-clear behavior; positive rejection applies
through the contiguous run end. The TOC sample
excludes prior `not_toc` decisions, recognized TOC pages, substantive controls,
numeric two-column tables, and repeated-left-column tables. The Positive TOCs
tab is a false-positive review and exposes only `Not TOC`, with `F` as its
hotkey. Hide reviewed filters completed labels. The 757 persisted decisions
include deterministic run suffixes and carry into later `c*` regenerations.
Separate progress text distinguishes the two TOC queues, and exports use the
review ID in their filename. The merged human decisions are the accepted MVP
TOC layer. Detailed per-entity role and representation fields were not collected
and are recorded as an accepted limitation rather than silently inferred.

## Approved Gate D disposition

On 2026-09-03, the user confirmed that the Task 03I finding is fixed, all 35
sources are eligible when paired with the exported human TOC review layer, and
the 725 ambiguous TOC-derived links were not reviewed and must remain explicitly
unresolved. The accepted MVP path freezes Task 03J plus the separate human
registry without machine regeneration. Task 04B is therefore a no-op.

Gate D publication must reuse the existing sealed Task 03J checksums and hash
only new compact review records; it must not recompute checksums for large
source or extraction files. The current implementation does not consume the
human TOC decisions in semantic placement, aliases, or reference linking.
That significant downstream concern is assigned to provisional [Task
04C](04c_materialize_human_review_navigation_overlay.md), not added to Task
04A and not treated as Task 04B regeneration.

## Maintainability gate

Before Gate D publication, the Task 04A implementation received a dedicated
human-maintainability pass. The pass introduced typed TOC census page/source
objects at the JSON boundary, direct contiguous-run objects, named selection
accounting, separate table-shape filter ownership, smaller review planning and
record-writing stages, path-rich input validation, and recoverable browser-state
parsing. Focused tests cover malformed census diagnostics and deterministic run
grouping. Repository formatting, lint, strict typing, all tests, JavaScript
syntax validation, and `git diff --check` must pass before the code is presented
for user review.

The user accepted this maintainability pass before Gate D publication.

## Outcome

Gate D completed on 2026-09-03 under:

```text
pipelines/brisbane_baylands/task_04_review/
  reviewv1-task03j-final-c17/gate_d/
```

The additive, no-clobber package contains the usability registry, ambiguous-link
dispositions, Task 03I recheck disposition, unresolved-risk report,
release-freeze record, and completion record. It records:

- all 35 sources as eligible with the accepted Task 04A human TOC layer;
- 757 accepted TOC decisions: 60 `toc` and 697 `not_toc`;
- all 725 unreviewed ambiguous links as unresolved and excluded from trusted
  resolved-link use;
- the Task 03I finding as fixed on physical pages 974-983 of
  `deir_appendix_k2_part_5_of_5`;
- zero material release blockers and three accepted MVP limitations; and
- Task 04B as `closed_no_op`, with provisional Task 04C as the next task.

The freeze pins Task 03J production extraction
`exv1-6913f56bed93302d7cf5ef424ee63c0b7427e90e2b2cd5c4ec483d275009a773`,
scope `scopev1-bd4b7ca85b299ae528376b1a6e88b9d0fdba02e4f7e8862c5fa91a28b719e893`,
and handoff
`handoffv1-44d510d545026a427ccdb47497d30f1d46c66130291af66fc0d5883a35102325`.
No source PDF, render, or model file was read. Existing large Task 03J inputs
were not rehashed; the largest hashed input was the 55,949-byte TOC decision
record. The newly published compact records were checksummed into the completion
record.

Task 04A does not apply page-level labels to semantic placement, aliases, or
links. That work remains isolated in provisional [Task
04C](04c_materialize_human_review_navigation_overlay.md), which must be reviewed
and activated separately.

## TOC and navigation review contract

TOCs are navigation evidence, not ordinary data tables. This review covers both
front matter and embedded document or section indexes. It does not assume that
every TOC uses the words `Contents` or that every dotted-leader layout is a TOC.

Build a deterministic candidate census from the union of independently
inspectable signals, including:

- canonical blocks with `is_toc_row == true` or semantic placement
  `toc_content`;
- hierarchy-producer visible-TOC regions, rows, reconciliations, or warnings;
- every non-exact visible-TOC reconciliation, with all `ambiguous` reference
  links included regardless of whether ambiguity comes from multiple candidate
  targets or multiple TOC anchors competing for one candidate target;
- raw Docling `document_index` objects and their descendants;
- canonical tables whose section ancestry includes a contents, document-index,
  list-of-tables, list-of-figures, or equivalent navigation heading;
- page furniture or headings that identify contents or index context;
- table or block layouts containing a plausible ordered combination of section
  labels, titles, dot leaders, and destination page labels; and
- pages adjacent to a detected candidate when they form one continuous
  navigation run, so a single differently routed page cannot escape review.

Heuristic signals select review candidates only. They never automatically
change extraction records or declare a page to be a TOC. Freeze the normalized
signal vocabulary, precedence, adjacency rule, and deterministic ordering before
reading source PDFs.

For every candidate page, show the source render beside canonical blocks,
tables, section ancestry, semantic placements, TOC flags, parser route and raw
provenance availability, visible-TOC reconciliation, target aliases, and
neighboring candidate context. The reviewer must record:

- page role: `toc_or_document_index`, `list_of_tables_or_figures`,
  `substantive_table`, `mixed`, or `neither`;
- representation: `correct_toc_blocks`, `incorrect_generic_table`,
  `missing_or_suppressed_text`, `duplicate_representation`,
  `incorrect_heading_or_ownership`, `incorrect_order`, or `other`;
- navigation outcome: usable, usable with a recorded limitation, or repair
  required;
- whether visible headings, row text, ordering, destination labels, and
  provenance are preserved; and
- whether each reviewed TOC-derived alias resolves to the intended body target
  rather than to a TOC block or false table.

For every ambiguous TOC-derived reference link, preserve the source TOC row,
candidate body target or targets, match basis, printed-page evidence, conflict
reason, and neighboring navigation context. Human review must select the
intended body target when the evidence supports one, or record the link as
unresolved. These review decisions belong only to the Task 04A usability
registry and must not rewrite Task 03J machine artifacts.

The census is complete only for the frozen machine-detectable candidate
population. Do not describe it as proof that no visually novel, signal-free TOC
exists.

## Outputs

- a new immutable `reviewv1-` run whose identity declares the `task03j_final`
  pass and binds the exact Task 03J inputs, policy digest, schemas, and review
  implementation;
- checksummed input inventory, deterministic selection manifest, generated
  review-bundle manifest, HTML workspace, and selected render cache;
- an explicit recheck record for every applicable first-pass extraction finding;
- a checksummed TOC candidate inventory, deterministic signal evidence, complete
  human TOC review register, and unresolved-candidate report;
- a complete human-review register for ambiguous TOC-derived reference links,
  including intended-target or unresolved dispositions;
- fresh findings and an unresolved-risk report, if any;
- a usability registry keyed by Task 03J corpus and source identity, with page,
  table, or family dispositions only for evidence actually reviewed; and
- a release-freeze record pinning the accepted candidate and all review evidence,
  or a stop record plus `task04b_handoff.json` containing only approved
  TOC/navigation extraction findings, exact evidence anchors, register digest,
  affected sources/pages/entities, expected behavior, and reviewer disposition.

Bulk HTML, renders, and review-cache derivatives remain under
`ER_COMMONS_DATA_ROOT`. Compact schemas, tests, task outcomes, and summary
documentation belong in Git. Task 03J machine artifacts remain immutable.

## Research / learning checkpoint

Before activation:

1. Read the closed Task 03I and Task 03J outcomes and inspect their owning
   schemas and validators rather than assuming the provisional field list above.
2. Compare the final Task 03J handoff with the Task 04 first-pass inventory and
   document how stale evidence is rejected and findings are re-resolved.
3. Recheck the maintained renderer and overlay coordinate contracts, including
   rotated and landscape pages, before trusting visual review geometry.
4. Re-read the visible-TOC and document-index preservation contracts and trace
   one ordinary TOC block, one embedded TOC, one correctly excluded
   document-index table, and one generic table candidate through canonical
   placement and target aliases.
5. Explain in plain language why TOCs support model navigation but must not
   become body-section starts or ordinary data-table targets.
6. Explain why a new corpus identity requires a new review
   dataset and why reviewing a sample supports only the recorded usability
   decisions, while the complete TOC candidate census supports only its frozen
   detectable population and not a corpus-wide error-rate estimate.

## Plan / gates

### Gate A: activate from closed upstream handoffs

1. Validate the Task 03I disposition and Task 03J handoff with their owning
   validators. The MVP record uses the prior successful read-only Task 03J
   validator result plus record-shape validation; a full validator rerun remains
   available before Gate B if needed.
2. Record every exact dependency listed above and reject stale Task 03H-derived
   identities, checksums, pages, or render inputs.
3. Revise this provisional contract to the actual handoff shape and freeze the
   final selection, recheck, artifact, and stop policies.
4. Present the expected review workload before reading source PDFs or producing
   renders.

### Gate B: add and qualify the final-pass generator mode (completed source-free)

1. Extend the Task 04 generator with an explicit `task03j_final` mode rather
   than cloning the review framework.
2. Validate selection and record generation on source-free fixtures, including
   stale-anchor rejection and finding re-resolution.
3. Preserve the qualified side-by-side UI, canonical/table overlays, parser
   attempt explanations, warning normalization, and shared image-overlay
   geometry frame from Task 04.
4. Run the production deterministic TOC candidate census, neighboring-run grouping,
   machine-evidence panel, human disposition fields, and Task 04B handoff
   projection without adding extraction repair behavior.
5. Cover explicit TOC blocks, embedded TOCs, raw `document_index` objects,
   generic tables under TOC ancestry, signal disagreement, substantive-table
   controls, and adjacency-only candidates with source-free fixtures.

### Gate C: generate and review the Task 03J dataset

Machine generation is complete in `reviewv1-task03j-final-c17`; the following
steps remain the human-review portion of this gate:

1. Allocate the new review identity and generate the deterministic inventory,
   selection, HTML, and selected render derivatives.
2. Recheck every applicable Task 04 extraction finding.
3. Review fresh per-source, warning, failure, page, table, and risk-triggered
   evidence under the frozen policy.
4. Review the bounded TOC false-negative sample; already recognized TOC pages
   are excluded.
5. Reconcile every positively tagged TOC page against its canonical
   representation and, where present, its body-target alias.
6. Review every ambiguous TOC-derived reference link and record either its
   intended body target or an unresolved disposition.
7. Record user-confirmed findings and usability dispositions outside the Task
   03J machine records.

### Gate D: decide and freeze

1. Reconcile all 35 sources and every reviewed item with exact checksums.
2. Publish the usability registry and unresolved-risk report.
3. Freeze only if no material defect remains and every TOC candidate has a
   terminal human disposition.
4. If one or more approved TOC/navigation extraction defects remain, publish a
   stop record and exact Task 04B handoff. Do not pre-authorize Task 04B or carry
   Task 04A approvals into its future recheck.
5. Route non-TOC material defects to their own separately approved remediation
   task rather than broadening Task 04B.

## Review pass

- **Handoff integrity:** Can every selected item be regenerated from the declared
  Task 03J records without Task 03H evidence?
- **Recheck integrity:** Does every applicable first-pass finding resolve to new
  Task 03J evidence and the exact Task 03I disposition?
- **Review utility:** Are source content, canonical text, tables, parser attempts,
  warnings, failures, and geometric overlays understandable and actionable?
- **Navigation integrity:** Are document and embedded TOCs represented as
  `toc_content`, are their headings and row order preserved, and do reconciled
  aliases target body sections rather than navigation copies?
- **Candidate integrity:** Can every included TOC candidate be justified by the
  frozen signals, and do substantive-table controls expose over-broad rules?
- **Release boundary:** Are human dispositions separate from machine artifacts,
  and does the freeze pin exactly what was reviewed and accepted?
- **Maintainability:** Is final-pass support a narrow extension of the qualified
  review generator with focused tests and no parallel framework?

## Validation

- owning Task 03I and Task 03J validators pass before selection;
- deterministic selection and byte-stable compact records under shuffled input
  discovery;
- exact all-35-source terminal accounting;
- stale Task 03H identity, checksum, anchor, and render-input rejection;
- one explicit outcome for every applicable first-pass finding;
- warning/failure population reconciliation and declared sample coverage;
- deterministic all-source TOC candidate census with complete signal provenance,
  adjacency closure, and no duplicate candidate identities;
- one terminal human disposition for every TOC candidate and every approved
  finding represented exactly once in the Task 04B handoff;
- one human intended-target or unresolved disposition for every ambiguous
  TOC-derived reference link;
- per-source page floors, main-report oversampling, and required table strata;
- source/canonical/table overlay checks on portrait, landscape, and rotated pages;
- no broken HTML resources and keyboard-accessible review navigation;
- no writes to Task 03J artifacts or authoritative browser state;
- focused tests, routine repository checks, deterministic-generation checks, and
  `git diff --check`.

## Acceptance criteria

- the review run binds only to validated Task 03J identities and checksums;
- all 35 sources have explicit terminal and human-usability dispositions;
- every applicable Task 04 extraction finding has a closed Task 03I disposition
  and an exact Task 03J recheck;
- every machine-detectable potential TOC page has a human role, representation,
  navigation, heading-preservation, and target-reconciliation disposition;
- every ambiguous TOC-derived reference link has a human intended-target or
  unresolved disposition backed by the preserved machine candidates;
- every reviewed navigation structure is either verified usable or represented
  by an exact accepted finding or unresolved limitation;
- reviewed tables are explicitly verified or rejected, while unreviewed tables
  remain unverified and ineligible until a separately versioned review extends
  the registry;
- the usability registry remains separate from Task 03J machine records;
- the release-freeze record pins the Task 03J candidate, registry, selection,
  generated-render manifest, findings, and unresolved limitations; and
- a materially unusable main report or required source produces an explicit stop
  rather than silent exclusion or a prefilled usable disposition.

## Non-goals

- rerunning or repairing extraction inside Task 04A;
- automatically classifying or rewriting TOCs from dotted leaders, heading text,
  or section ancestry without human review;
- reusing Task 03H production artifacts, review anchors, or approvals;
- reviewing every warning, page, or table;
- storing authoritative decisions in browser state;
- building a hosted review platform or general labeling system;
- OCR, VLM conversion, LLM repair, or visual-question answering; or
- case screening, evidence authoring, retrieval, generation, or scoring.
