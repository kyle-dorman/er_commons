# Task 03E.1: Define the Deterministic Hierarchy-Correction Contract

Status: **provisional and inactive**. Task 03E rejected Docling's maintained
defaults as the sole project hierarchy policy. Activate this contract only
after the user separately authorizes correction-layer work and the Task 03E
evaluation implementation has received its requested maintainability cleanup.
This task defines contracts and fixtures only; it does not implement or run the
correction layer.

## Abstract

Define a deterministic, provenance-preserving hierarchy-correction layer
between the immutable Docling producer and canonical semantic-section
materialization. Retain every raw Docling label, level, pointer, text value,
reading-order position, and provenance region. Emit separate project-owned
feature, decision, visible-TOC reconciliation, corrected-hierarchy, ambiguity,
and warning artifacts rather than rewriting the producer document.

The runtime pipeline must contain no LLM, VLM, embedding, semantic retrieval,
or manual per-document exception. Development may use human and model
assistance to inspect evidence and write ordinary code, but every production
decision must reduce to versioned data, named deterministic rules, and
executable validation.

## Goal

Freeze a correction contract that can repair the measured Task 03E failure
mechanisms while preserving the strong embedded-outline and conventional
numbering results. Make Task 03E.2 implementable without inventing feature
definitions, rule precedence, thresholds, ambiguity behavior, identity,
artifact ownership, or acceptance policy.

## Inputs

- rejected Task 03E maintained-default candidate, producer comparison,
  bounded review report, and requested review-cache renders
- accepted Task 03C.1 producer and immutable Task 03D.1 canonical reference
- checksum-pinned Appendix P and main-report control sources
- Docling document JSON, conversion-page observations, PDF outline, content
  layers, reading order, text, geometry, and hierarchy observations
- the visible Appendix P tables of contents and fixed main-report pages 44-46
  and 2000
- current canonical schemas, identity helpers, artifact inventory, completion,
  and publication conventions
- maintained primary documentation for Docling's document model and hierarchy
  implementation, PDF outlines and page labels, JSON Schema Draft 2020-12,
  and RFC 8785

## Outputs

- a versioned hierarchy-correction specification
- executable schemas or typed contracts for:
  - stable item features derived only from checksum-verified producer evidence;
  - visible-TOC entries, depth, printed-page evidence, and source anchors;
  - TOC-to-body reconciliation with exact, missing, ambiguous, page-conflict,
    level-conflict, and order-conflict states;
  - raw versus corrected semantic role and level;
  - named rule decisions, evidence values, precedence, and policy version;
  - unresolved ambiguity, warnings, and fatal invariant failures; and
  - corrected hierarchy roots, ordered parent/child edges, and exact direct
    membership
- a frozen rule vocabulary and precedence specification covering:
  - body/furniture and TOC exclusions;
  - false-heading demotion;
  - embedded-outline anchors;
  - visible-TOC reconciliation;
  - local numbering regimes and embedded-document resets;
  - conservative local sibling/style promotion and level transfer; and
  - fail-closed ambiguity rather than guessed structure
- a frozen development fixture set containing the already reviewed failures
- a separately frozen held-out review set selected before rule implementation
- exact preservation, repeatability, timing, and acceptance gates for Task
  03E.2
- a compact learning note explaining why a correction overlay is distinct from
  mutating raw producer output or using an LLM at runtime

## Research / learning checkpoint

Inspect the pinned producer artifacts and maintained implementations before
freezing features. Confirm which font, cell, geometry, outline, page-label, and
content-layer signals actually persist. Do not specify a feature that would
require an unrecorded visual judgment or silently rerunning a different parser.

Evaluate maintained deterministic parsing utilities before adding custom glue,
but prefer narrow pure functions when a package would add a broad dependency
without owning the required policy.

The outcome must explain:

- **Raw and corrected hierarchy have different owners.** Docling observations
  remain immutable; project code owns the explicit correction policy.
- **An overlay is not an in-place repair.** Every corrected decision points
  back to unchanged raw evidence and records its rule and inputs.
- **Embedded outlines and visible TOCs are distinct evidence.** Outline matches
  may anchor levels. Visible TOC rows remain source content and never start
  body sections; they reconcile to body targets and expose missing, ambiguous,
  page, level, and order conflicts.
- **TOC absence is not negative proof.** Deep headings may be omitted from a
  TOC, so absence alone cannot demote a body candidate.
- **Local context matters.** Numbering and style regimes reset across embedded
  appendices, agreements, schedules, and letters; global font-rank or marker
  rank is insufficient.
- **Conservative ambiguity is reproducible.** Unsupported or conflicting
  evidence remains explicit rather than being guessed.
- **Pipeline development and pipeline execution differ.** Human or LLM help
  may propose code during development, but accepted runtime artifacts are
  produced only by frozen deterministic code and inputs.

## Plan / spec requirement

Freeze before implementation:

1. exact input completion and inventory requirements;
2. stable item key and every persisted feature, unit, quantization, and missing
   state;
3. visible-TOC row detection, depth evidence, printed-page evidence, body-target
   matching, collision behavior, and reconciliation states;
4. corrected semantic-role and level meanings without changing raw labels;
5. ordered rule IDs, eligibility predicates, precedence, evidence fields, and
   interaction behavior;
6. local numbering-regime start/reset/stack rules;
7. exact conditions for false-heading demotion and plain-text/list-item
   promotion;
8. conservative style/sibling transfer and the conditions that produce
   ambiguity instead of a correction;
9. hierarchy construction, no-cycle, no-skipped-level, body/furniture,
   reading-order, inverse-membership, and root-continuity invariants;
10. development and held-out samples, with a prohibition on adding
    document-title, page-number, or literal-heading exceptions after review;
11. candidate identity, code/config/schema digests, artifact paths, atomic
    publication, failure preservation, and checksum reuse;
12. exact old/new comparison surfaces and permitted hierarchy-only changes;
13. runtime and storage measurements confirming that the overlay remains cheap
    relative to document production; and
14. acceptance, rejection, and inconclusive stop conditions for Task 03E.2.

## Review pass

- **Determinism:** every output follows from persisted inputs and named rules.
- **No hidden exceptions:** production configuration contains no source title,
  page number, literal heading text, or reviewed-case lookup.
- **TOC boundary:** visible rows support reconciliation and review but never
  become section starts.
- **Traceability:** every correction and non-correction is explainable from
  stable low-level evidence.
- **Leakage:** development fixtures do not double as held-out proof.
- **Architecture:** the layer is a replaceable enrichment between immutable
  production and canonical semantic materialization.
- **Maintainability:** feature extraction, reconciliation, decision rules,
  hierarchy construction, validation, comparison, and publication have
  separate responsibility owners.

## Validation

- Validate positive and negative fixtures for every persisted shape and rule
  state.
- Cover the known bullet false headings, omitted visible subheading, visible
  TOC rows, exact outline matches, conventional numbering, skipped levels,
  embedded resets, repeated titles, captions, tables, and furniture.
- Prove TOC entries reconcile only to unique body targets and that ambiguous,
  missing, page-conflicting, level-conflicting, and order-conflicting cases
  remain explicit.
- Test ordering, cycles, skipped levels, roots, direct membership, and exact
  forward/inverse relationships.
- Test that configuration cannot contain page-specific or literal-text
  exceptions.
- Test identity changes for code, config, schema, source, producer completion,
  and feature-policy changes.
- Confirm no network, model, embedding, or LLM dependency appears in the
  runtime contract.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- Task 03E.2 can implement every feature, artifact, rule, invariant, identity,
  comparison, and stop condition without inventing policy.
- Raw producer artifacts remain immutable and independently verifiable.
- Every automatic correction has explicit high-precision evidence; uncertain
  cases remain reviewable ambiguity.
- Visible TOC reconciliation is complete, deterministic, and cannot turn a TOC
  row into a body boundary.
- Development and held-out evidence are separated before implementation.
- No LLM or other learned/generative component is required by the production
  pipeline.
- The outcome requests user review before Task 03E.2 activates.

## Non-goals

- implementing or running hierarchy correction
- rewriting or republishing the Docling producer
- semantic-section schema/materialization work owned by Tasks 03E.3-03E.4
- cross-reference mentions or resolution
- corpus batching or processing another complete document
- retrieval units, embeddings, LLM inference, or human review fields
- accepting page-specific or literal-text production exceptions
