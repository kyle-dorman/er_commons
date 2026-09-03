# Task 04B: Remediate TOC Navigation and Reprocess the Candidate

Status: **closed as a no-op by the 2026-09-03 Task 04A disposition**. Task 03J
will be frozen without machine regeneration; the separate human-overlay and
linking work belongs to [Task 04C](04c_materialize_human_review_navigation_overlay.md).

## Abstract

Consume only the human-approved TOC/navigation extraction findings from [Task
04A](04a_regenerate_review_and_freeze_release.md), implement the smallest
source-general correction, and publish a fresh candidate from immutable producer
evidence. Prefer canonical and downstream replay over PDF/model reruns. Rebuild
document linking and corpus resolution whenever canonical content or identity
changes, then generate a new identity-bound TOC recheck and freeze only after
human confirmation.

Task 04B is the second human-review-driven remediation cycle after the Task
04-to-03I-to-03J sequence. It does not mutate Task 03J artifacts, inherit Task
04A approvals, or treat one reviewed Brisbane page as a document-specific
exception.

## Goal

1. Disposition every approved Task 04A TOC/navigation finding against its exact
   source, machine evidence, expected behavior, and owning pipeline stage.
2. Preserve verified TOCs as navigable canonical content without converting
   substantive data tables into TOCs or allowing TOC copies to become body
   targets.
3. Reuse sealed baseline, table, and hierarchy producers when their owning
   checksums and contracts permit; allocate no PDF/model work unless a separate
   evidence-based decision proves it necessary.
4. Publish a fresh, internally consistent canonical and linked corpus candidate,
   followed by a fresh human recheck and either an exact release-freeze record
   or another stop decision.

## Inputs and activation boundary

Activation requires:

- Task 04A's completed review record, stop record, TOC candidate inventory,
  complete human TOC review register, usability registry, unresolved-risk
  report, and `task04b_handoff.json`;
- the handoff digest and exact Task 03J corpus, document, producer, canonical,
  linking, and publication identities referenced by those records;
- the accepted semantic-structure, document-index preservation, reference-
  linking, restartability, and artifact contracts; and
- explicit user authorization to activate Task 04B after the expected repair,
  replay scope, disk use, runtime, and any source/model need are presented.

The handoff must contain only human-approved TOC/navigation extraction findings
and must identify, for each finding:

- stable finding ID, human disposition, reviewer, and review timestamp;
- source ID, physical pages, canonical entities, parser observations, and exact
  evidence checksums;
- observed and expected representation, navigation consequence, and materiality;
- relevant TOC signals, section ancestry, raw-provenance availability, heading
  preservation, and target reconciliation; and
- the Task 04A register digest and Task 03J identity against which the finding
  was approved.

Reject a missing, ambiguous, stale, nonterminal, or checksum-inconsistent
handoff. Do not reconstruct approval from conversation history or Task 03H
artifacts.

The observed Task 03J main-report page 11 behavior is planning evidence only:
a visually apparent contents page was emitted as a generic TableFormer table,
its table-stage observation had no raw Docling provenance link, and one visible
continuation heading disappeared. Task 04A must independently re-resolve and
approve this or any analogous finding before it can authorize Task 04B behavior.

## Expected behavior and repair invariant

Visible document-level and embedded TOCs, document indexes, lists of tables, and
lists of figures remain canonical navigation content. Their visible headings,
ordered row text, destination labels, geometry, and raw provenance remain
inspectable. TOC rows use semantic placement `toc_content`; they do not start
body sections, become ordinary data tables, or serve as retrieval/link targets.
TOC-derived aliases may target only exactly reconciled semantic body sections,
as required by the maintained semantic contract.

A clean parser grid is evidence about layout, not sufficient evidence that a
region is a substantive table. Conversely, dotted leaders, words such as
`Contents`, section ancestry, or a human label alone are not sufficient runtime
rules for deleting a canonical table. The repair must use an explicit,
source-general, fail-closed ownership decision backed by available producer or
verified hierarchy/TOC evidence. Ambiguous and mixed regions remain visible and
diagnostic rather than being silently rewritten.

Preserve all sealed producer tables and parser attempts as immutable evidence.
When an accepted navigation region has a parsed grid, exclude it only from the
canonical logical-table view, emit its native navigation text exactly once, and
record the exclusion and replacement evidence in a checksummed observation.

## Outputs

- a closed disposition for every Task 04A handoff finding: repair, accepted
  limitation, duplicate, not reproducible, review-only issue, or no-op;
- a source-general repair contract, maintained implementation, focused tests,
  and any required schema or specification revision;
- an identity-impact and replay manifest naming reusable sealed producers,
  invalidated stages, affected documents, fresh namespaces, expected disk use,
  and explicit source/model allocation of zero unless separately approved;
- checksummed TOC ownership/projection observations connecting each excluded
  canonical table or preserved block to producer and hierarchy evidence;
- fresh canonical, semantic, alias, per-document linking, publication,
  collection-index, corpus-resolution, and handoff records for every stage that
  the identity-impact inventory invalidates;
- exact before/after accounting for blocks, TOC placements, tables, families,
  headings, aliases, cross-references, warnings, and content hashes;
- a new review identity and targeted recheck bundle covering every repaired
  finding, every affected TOC run, neighboring pages, and substantive-table
  controls; and
- a post-repair usability registry and release-freeze record, or a stop record
  that preserves the unresolved evidence without promoting the candidate.

Large artifacts remain under `ER_COMMONS_DATA_ROOT`. Compact contracts, schemas,
tests, task outcomes, and summary documentation belong in Git. Task 03J and
Task 04A artifacts remain immutable inputs.

## Research / learning checkpoint

Before implementation:

1. Read the accepted Task 04A findings and trace every affected page from sealed
   producer observations through canonical projection, semantic placement,
   aliases, document linking, corpus resolution, and publication.
2. Inspect the existing `document_index` projection and visible-TOC
   reconciliation owners. Explain why the approved failure escaped them and
   whether missing raw-region provenance, routing, ownership, or another stage
   is the narrow cause.
3. Review Docling's maintained document-index and layout-label behavior and the
   project's accepted semantic contracts. Record why the selected evidence is
   source-general and fail-closed.
4. Compare canonical-only replay with baseline, hierarchy, or table-producer
   reruns. Explain in plain language why immutable parser evidence may remain
   truthful while the consumer chooses a different canonical representation.
5. Trace one TOC-derived target alias and one cross-reference through the
   proposed replay so the required linking boundary is explicit.

## Plan / gates

### Gate A: freeze findings, ownership, and replay scope

1. Validate every Task 04A input with its owning schema and checksum.
2. Map each accepted finding to the narrow owning policy, expected invariant,
   regression, affected identity inputs, and required downstream stages.
3. Inventory available sealed producer evidence for every affected source.
4. Decide whether canonical-only replay is sufficient. If any required evidence
   would need PDF, Docling, Camelot, TableFormer, OCR, VLM, or LLM execution,
   stop and obtain separate user approval before allocating it.
5. Present the exact implementation and replay plan before modifying code or
   creating a new artifact namespace.

### Gate B: implement and qualify the source-general repair

1. Add the smallest explicit TOC ownership/projection policy in the existing
   responsible module; do not create a parallel extraction framework.
2. Preserve native TOC blocks and headings as canonical content with
   `toc_content`, exclude only verified navigation grids from the canonical
   logical-table view, and publish exact decision evidence.
3. Preserve substantive tables, mixed/ambiguous regions, furniture, figures,
   raw producers, and unrelated document-index behavior.
4. Add source-free fixtures for explicit TOC rows, embedded TOCs, lists of
   tables/figures, absent raw-region links, neighboring routed pages, missing
   headings, mixed TOC/data layouts, and substantive-table controls.
5. Run focused semantic, alias, reference-linking, identity, restart, and
   maintainability checks before any artifact replay.

### Gate C: replay canonical and downstream stages

1. Allocate a fresh Task 04B namespace and production identity. Never overwrite
   or extend Task 03J publications.
2. Verify and checksum-reuse sealed baseline, table, and hierarchy producers
   only where their owning contracts allow reuse under the repaired identity.
3. Rebuild canonical materialization and every invalidated later document stage,
   including semantic structure, target aliases, document reference linking,
   and publication.
4. Regenerate collection indexing, cross-document resolution, terminal
   accounting, and the machine handoff from one coherent candidate. If the
   implementation identity invalidates unaffected documents, replay their
   downstream stages from sealed producers rather than mixing identities.
5. Stop on an undeclared semantic difference, stale identity, missing producer,
   unexpected model allocation, or incomplete all-source accounting.

### Gate D: compare the repaired candidate

1. Recompute the Task 04A TOC candidate census against the new identity.
2. Require every approved finding to resolve to exact new evidence and compare
   every affected navigation run with Task 03J.
3. Verify that repaired TOC text, headings, ordering, destinations, and aliases
   are present exactly once and that removed generic tables leave no dangling
   families, aliases, references, or publication links.
4. Review substantive-table controls and all undeclared changed pages before
   generating the human recheck bundle.

### Gate E: recheck and freeze

1. Allocate a new immutable review identity; do not reuse Task 04A review item
   IDs, approvals, anchors, or renders.
2. Recheck every repaired finding, affected TOC run, and substantive-table
   control against source and canonical evidence.
3. Rebind unaffected Task 04A usability dispositions only through an explicit
   checksum-verified correspondence record; unresolved correspondence returns
   the item to human review.
4. Freeze only after all repaired items have terminal human approval, all 35
   sources have coherent terminal and usability records, and no material defect
   remains. Otherwise publish a stop record.

## Review pass

- **Evidence ownership:** Does every TOC decision cite producer or verified
  hierarchy evidence rather than a document-specific text exception?
- **Fail-closed behavior:** Can a substantive or mixed table survive ambiguous
  TOC signals without data loss?
- **Navigation integrity:** Are headings, ordered entries, destination labels,
  body-target aliases, and cross-references correct and nonduplicated?
- **Replay integrity:** Are all changed records under one fresh identity with no
  Task 03H or Task 03J artifact reuse beyond explicitly verified sealed producer
  inputs?
- **Human boundary:** Are Task 04A findings inputs, machine repairs outputs, and
  post-repair human approvals separate records?
- **Maintainability:** Is the rule easy to locate, understand, test, debug, and
  replace without a hidden TOC heuristic spread across stages?

## Validation

- owning Task 04A input and Task 03J producer validators pass before work;
- one disposition and one regression for every approved handoff finding;
- deterministic source-free projection under shuffled discovery and repeated
  builds;
- all verified TOC rows emitted exactly once with `toc_content` and no TOC row
  starting a body section or becoming a target;
- every excluded navigation grid has exact replacement evidence and no dangling
  table family, alias, reference, or ordered-child ID;
- substantive-table and mixed-layout controls remain byte- or semantically
  unchanged as declared by the repair contract;
- no PDF/model attempt exists unless separately authorized and recorded;
- exact document and all-source accounting, checksums, containment, and fresh
  identity validation;
- per-document reference linking and corpus resolution rerun wherever canonical
  records or identities changed;
- deterministic post-repair TOC census and one terminal recheck outcome for every
  repaired item;
- routine repository formatting, lint, typing, tests, deterministic generation,
  maintainability review, and `git diff --check` pass.

## Acceptance criteria

- every Task 04A TOC/navigation finding has a closed, evidence-backed
  disposition;
- the repair is source-general, fail-closed, and contains no source ID, page
  number, or document-specific heading exception;
- reviewed TOCs are canonical `toc_content` with visible headings, ordered text,
  destination labels, and exact body-target reconciliation preserved;
- substantive tables remain tables and ambiguous regions remain explicit rather
  than being silently discarded;
- Task 03J machine and Task 04A review artifacts remain immutable;
- the fresh candidate has complete, coherent canonical, linking, resolution,
  publication, and all-source handoff records under accepted identities;
- the post-repair review is bound only to the new candidate and records explicit
  human approval for every repaired item; and
- the release freezes only when no material TOC/navigation or other extraction
  defect remains.

## Non-goals

- repairing findings that Task 04A did not approve or that are unrelated to
  TOC/navigation representation;
- treating all table-shaped contents pages as substantive tables or treating all
  dotted-leader pages as TOCs;
- mutating, deleting, or promoting Task 03H, Task 03J, or Task 04A artifacts;
- rerunning source PDFs or models when sealed producer evidence is sufficient;
- OCR, VLM conversion, LLM repair, or document-specific exception lists;
- changing benchmark cases, retrieval units, generation, or scoring; or
- freezing a repaired release without a fresh identity-bound human recheck.
