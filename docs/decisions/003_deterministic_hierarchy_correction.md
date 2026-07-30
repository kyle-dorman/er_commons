# Decision 003: Correct Docling Hierarchy with a Deterministic Overlay

Status: accepted 2026-07-30.

## Decision

Reject Docling 2.115.0's maintained heading-hierarchy defaults as the sole
project hierarchy policy. Retain the immutable Task 03E candidate as valid
producer and evaluation evidence because it passed complete preservation,
independent repeatability, and checksum-reuse gates.

Before canonical semantic-section materialization, add a separately identified
project-owned correction overlay. The overlay preserves raw Docling labels,
levels, text, order, geometry, pointers, and provenance; emits corrected roles
and levels as new evidence; reconciles visible TOC entries only to body targets;
and records every decision, non-decision, ambiguity, warning, and rule version.

The production correction path is deterministic local code. It contains no
LLM, VLM, embedding, semantic retrieval, or manual per-document exception.
Human and model assistance may support development, but accepted runtime
behavior must be frozen as reviewed code, configuration, schemas, fixtures,
and checksummed inputs.

## Why

Task 03E found that maintained hierarchy inference is deterministic and strong
for embedded-outline matches and conventional numbering: 29 of 29 eligible
bookmark-covered headings and 21 of 21 reviewed numbered headings received the
expected relative level. It also preserved all unrelated accepted producer
surfaces.

The same run retained known false bullet headings on main-report pages 44-45,
left a visibly styled page-2000 subheading as plain text, and assigned poor
global fallback depths to unbookmarked or embedded-document headings. The
maintained stage changes levels, can promote a bookmark-matched list item, and
does not provide the demotion, plain-text promotion, local regime reset, or
parent-aware fallback behavior the project needs.

Visible TOCs provide useful independent evidence, but they differ from embedded
PDF outlines. Their rows remain source content and never become body-section
starts. Deterministic reconciliation may support a unique body target and expose
missing, ambiguous, page, level, or order conflicts.

## Consequences

- Task 03E is complete and rejected as the sole hierarchy policy.
- Task 03E.1 defines correction features, rules, reconciliation, identity,
  development/held-out evidence, and stop conditions.
- Task 03E.2 implements and evaluates the correction overlay.
- The former semantic-structure and cross-reference tasks are renumbered
  03E.3 through 03E.5.
- No correction task is active. The Task 03E MVP implementation receives a
  separately triggered maintainability cleanup first.
- The correction layer must remain fast, artifact-producing, independently
  reproducible, and replaceable without changing immutable producer evidence.
- Production rules may not contain document titles, page numbers, literal
  reviewed headings, or other hidden case lookups.

## Excludes

- accepting the maintained-default hierarchy unchanged
- rewriting or republishing the raw Docling producer document
- LLM or learned-model hierarchy repair in the production pipeline
- allowing visible TOC rows to become body-section starts
- silently forcing ambiguous hierarchy decisions
