# Task 03I: Disposition Task 04 Extraction Findings

Status: **complete; repair and independent human-maintainability gate passed**.
The first-pass
[Task 04](04_review_extraction_and_freeze_release.md) review identified one
source-general ownership defect. The repair has an explicit responsibility owner,
inspectable ownership evidence, fail-closed single-table semantics, editable
policy tests, and complete source-free correctness and maintainability validation.
The committed code, tests, task contract, production identity, and recorded Task
04 input checksums are the durable disposition; no duplicate Task 03I receipt is
required.

## Abstract

Disposition the extraction-pipeline findings produced by the user-led Task 04
review of Task 03H evidence. Implement only findings that Task 04 classifies as
source-general extraction defects that must be corrected before the next complete
run. Keep review usability decisions in Task 04 and full-corpus execution in Task
03J.

## Goal

Produce a closed, reviewable disposition for every Task 04 finding that could
affect the Task 03 extraction, with bounded repairs and regressions where needed.

## Inputs

- Task 04's user-approved first-pass `records/finding_register.json` and
  `records/task03i_handoff.json` from
  `pipelines/brisbane_baylands/task_04_review/<reviewv1-id>/`, including the
  handoff digest and exact evidence anchors
- the completed [Task 03H](03h_run_full_canonical_extraction.md) outcome
- the maintained source-free pipeline and tests at Task 03I activation
- accepted Task 03 contracts and durable decisions implicated by a finding

## Frozen finding 1: accepted full-page tables retain duplicate native text

The first approved finding is anchored to review item
`reviewitem-9e4881101e7f8c6fa60dcf8a` in review run
`reviewv1-task03h-first-7e8e89a40907adba`. It is an extraction/canonicalization
defect, not only a review-interface concern.

The reproducible evidence is source
`deir_appendix_k2_part_5_of_5`, candidate
`docv1-60d0928a0fb7af7ab1a58cb1838a0a52b5224e0ddff0bff1386d9fbe20bcad57`,
table family `.../fam000709`, physical pages 974--983. On page 974, the
validated `camelot_stream` table `.../tbl000805` has a `196 x 48` clean grid
and bbox `[40.879856, 46.04, 1167.397432, 747.000008]`. The same canonical
page contains 585 standalone Docling body-text blocks whose valid provenance
boxes fall inside that table bbox. The page has no
`table_stage_observation_ids`, so the existing observation-based suppression
path has no native table pointer to suppress. The result is one accepted table
plus a second, text-shaped representation of its contents. This is why the
review UI appeared to show a paragraph column in the middle of the table.

Expected behavior: once a regionless producer table has passed the existing
clean-grid and CSV validation for the `full_page_numeric` route, it owns body
text whose every valid provenance region is fully contained by that table's
page-local bbox. Those native text pointers must be suppressed from the
canonical traversal so the table event is the sole canonical representation.

The repair is deliberately fail-closed. It does not suppress text merely
because it intersects a table, and it does not use the route label alone. Text
with rejected or mixed provenance, partial or outside geometry, furniture
content, and document-index descendants remains visible. Raw Docling evidence
and the accepted table artifact remain unchanged; only the canonical ownership
view changes. This follows the existing contract that table text may be
suppressed only after page-local table extraction evidence is verified.

The focused source-free policy regressions in
`tests/test_record_mapping_table_text_ownership.py` cover exact owner mapping,
multiple regions contained by one table, one contained plus one outside region,
regions spanning pages, mixed or rejected provenance, split multi-table
coverage, wrong-page geometry, non-full-page tables, furniture, and
document-index text. The public context regression
`tests/test_record_mapping_context.py::test_context_preserves_exact_full_page_table_text_owner`
requires the duplicate block to disappear while preserving the exact producer
table owner and table event.

Every accepted decision is published to
`observations/table_text_ownership.jsonl` with its text pointer, producer table
ID, physical page, table bbox, complete text-region list, and stable reason.
`canonicalization_summary.json` names the sidecar, records its count and reason
counts, and separates reason-specific table ownership while preserving the
existing emitted/suppressed/unaccounted total equation.

Hierarchy-relevant suppressed text remains explainable downstream. Document
structure reuses the same classifier and persists
`canonical_table_geometry_owned_text` through its replacement-evidence bridge;
it does not duplicate the geometry rule. The maintained mapping and semantic
specifications describe the exclusions, diagnostics, and raw-evidence
preservation. These code and contract changes are bound by regenerated Task 03H
production identity `exv1-dc215a29286198af33a31c708e431b65cd5e445adb82f4543270335d2094dba9`.
The next fresh Task 03J extraction must recheck the Brisbane example under its
new identity; this change does not promote or mutate Task 03H artifacts.

The separate code-quality pass is complete. The geometry rule lives in the
focused typed `table_text_ownership` policy module; traversal preserves exact
ownership decisions; candidate publication writes a checksummed ownership
sidecar; and document structure reuses the same classifier and explicit
disposition. An independent review found no remaining maintainability blockers.
The repository-wide gate passed Ruff, mypy, all 982 tests, deterministic Task 03H
config generation, and `git diff --check`. The approved Task 04 inputs remain
`finding_register.json` SHA-256
`a8c3a763af0da402834e61e1a88fb38011c67f35edc47d3e07bfe585d7c71100` and
`task03i_handoff.json` SHA-256
`b946d77e6a2189302a23b3d2ae41a6dda3708a2ece903cffeedc62c7114772b4`.

## Outputs

- a disposition for each in-scope finding: repair, accepted limitation, duplicate,
  not reproducible, review-only usability issue, or out of scope
- source-general code, configuration, contract, and regression changes for every
  accepted repair
- an identity-impact inventory stating which Task 03J stages must be fresh
- a committed task outcome naming the input handoff and finding-register digests,
  repair identity, owning code, and validation evidence
- an outcome that either records the validated repairs or explicitly closes no-op

## Research / learning checkpoint

For each accepted defect, inspect the owning stage contract and primary package
documentation before selecting a repair. Record why the failure is an extraction
defect rather than a Task 04 usability judgment, and explain the repair invariant in
plain language.

## Plan / spec requirement

Before implementation, freeze the exact input finding IDs and map each one to its
owning stage, reproducible evidence, expected behavior, identity impact, regression,
and disposition. Ask the user before broadening beyond those findings or running
source PDFs/models.

## Review pass

- verify every change is source-general and does not encode a document-specific
  exception unless an existing accepted contract explicitly permits one
- review ownership, typing, failure diagnostics, restart behavior, and identity
  coverage separately from behavioral correctness
- confirm that findings left to Task 04 cannot alter Task 03J extraction bytes

## Validation

- run focused regressions for every accepted repair
- run the repository's source-free formatting, lint, typing, test, deterministic
  generation, and diff checks
- use only the smallest explicitly authorized source/model qualification needed to
  prove a repair; preserve its lineage separately from Task 03J

## Acceptance criteria

- every supplied extraction finding has one explicit disposition and evidence
- every repaired behavior has a source-general regression and complete identity
  ownership
- maintained code meets the repository's readability and ownership standards
- no Task 03H completion is promoted into Task 03J
- Task 03J has an exact, closed code/configuration baseline to execute
- if there are no accepted extraction defects, the task closes with a no-op outcome
  and Task 03J proceeds unchanged

## Non-goals

- defining or executing Task 04's review process
- deciding final document, page, table, or corpus usability
- rerunning all 35 documents or assembling the final corpus
- opportunistic extraction changes not anchored to a Task 04 finding
- freezing the accepted extraction release
