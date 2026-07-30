# Task 03E: Evaluate Docling Heading Hierarchy

Status: **completed and rejected 2026-07-30**. The user accepted the
recommendation to reject Docling's maintained defaults as the sole project
hierarchy policy and authorized planning for a deterministic correction layer.
Task 03E.1 subsequently completed the correction contract. Tasks 03E.2 through
03E.5 remain provisional and inactive.

## Abstract

Enable the heading-hierarchy stage already provided by the pinned Docling
2.115.0 runtime and evaluate it on the accepted Appendix P producer path before
writing project-owned hierarchy logic. Use Docling's maintained defaults:
PDF bookmarks, numbering, then font style. Publish a new immutable producer
candidate, compare it independently with the accepted Task 03C.1 producer, and
stop for explicit user acceptance or rejection.

This is an open-source-tool acceptance gate. It does not assume that Docling
will work well enough, but downstream tasks are provisionally written for the
accepted case. A rejection does not authorize a custom hierarchy algorithm; it
requires a new bounded fallback task.

## Goal

Determine whether Docling can supply a sufficiently accurate, deterministic
heading hierarchy while preserving every unrelated accepted producer output.
Keep later project code focused on canonical mapping, validation, provenance,
and review rather than rebuilding document-tree inference.

## Inputs

- accepted Task 03C.1 producer implementation and completion artifacts
- accepted Appendix P producer run
  `prv1-93dfb03242a3651b90ee5424f36b7f6c58b5ac814dd48e1495b6359cdc6e92e0`
- checksum-pinned `deir_appendix_p.pdf`
- pinned Docling 2.115.0, PyPdfium2 backend, Heron layout model, and existing
  `generate_parsed_pages=True` runtime behavior
- Appendix P's PDF outline, visible tables of contents, numbered body headings,
  embedded appendices and agreements, and repeated furniture
- the Task 03A false-positive section header on main-report pages 44-45 and
  false-negative visible subheading on main-report page 2000
- the accepted Task 03A bounded-review harness, configuration, and comparison
  artifacts for those fixed main-report controls
- on-demand review-cache renders for only the predeclared review pages
- Docling's maintained
  [heading-hierarchy options](https://docling-project.github.io/docling/reference/pipeline_options/#docling.datamodel.pipeline_options.HeadingHierarchyOptions)

## Outputs

Tracked:

- a versioned Appendix P producer configuration with
  `heading_hierarchy_options.enabled=true`
- the narrow configuration/runtime plumbing and focused tests needed to pass
  Docling's maintained hierarchy options
- a frozen evaluation specification with review pages, comparison rules,
  severity categories, good-enough thresholds, and stop conditions
- a compact learning note explaining Docling's bookmark, numbering, and style
  precedence and how that differs from project-owned canonical hierarchy
- Task 03E outcome evidence and explicit user accept/reject status

External:

- a new immutable Appendix P producer candidate under the existing
  `task_03c_single_document/<producer_run_id>/` lifecycle
- an independent comparison report against the accepted Task 03C.1 producer,
  which is the sole direct comparison baseline
- an inventory of every changed heading level, promoted item, label, parent,
  child relationship, and hierarchy-dependent serialized value
- bounded hierarchy-enabled diagnostic runs for only the predeclared Task 03A
  main-report control ranges; these are comparison evidence, not a second
  complete-document producer candidate
- requested disposable review-cache renders and a bounded review report

## Research / learning checkpoint

Inspect the pinned implementation and maintainers' documentation before
configuring it. Confirm which signals are actually available in the accepted
runtime and whether the stage changes only heading levels and confident
bookmark-matched promotions as documented.

The outcome must explain:

- **Open-source first is an engineering constraint.** Maintained hierarchy
  inference is preferred over a project-owned parser unless measured evidence
  shows it is inadequate.
- **Bookmarks and visible TOCs are different evidence.** Docling consumes the
  embedded PDF outline. Visible TOC rows remain document content used for
  review and later alias reconciliation; they must not become body section
  starts merely because they name sections.
- **All existing headings at level one is expected baseline behavior.** With
  hierarchy inference disabled, the PDF path emits detected section headers at
  level one.
- **Tool success and task sufficiency differ.** A completed conversion is not
  evidence that heading levels, promotions, or boundaries are good enough.
- **A configuration change creates a new producer identity.** The accepted
  Task 03C.1 run remains immutable evidence even when the new candidate is
  accepted.

## Plan / spec requirement

Before any live conversion, freeze:

1. exact hierarchy options, beginning with the maintained defaults
   `use_bookmarks=true`, `use_numbering=true`, and `use_style=true`;
2. exact package, model, backend, source, and configuration identities;
3. old/new producer comparison normalization and permitted hierarchy-only
   differences;
4. the Appendix P hierarchy review set, covering visible TOCs, ordinary and
   deep numbering, embedded appendix/agreement resets, repeated titles, table
   titles, footnotes, and furniture-like content;
5. the fixed Task 03A false-positive and false-negative control ranges;
6. the exact bounded-review command and interpretation limits for those
   controls, including that page-range behavior is diagnostic rather than
   corpus-wide hierarchy proof;
7. severity categories and the quantitative or exact good-enough thresholds;
8. repeat-run equality requirements;
9. how review-cache pages are generated and excluded from producer completion;
10. acceptance, rejection, and inconclusive stop conditions; and
11. whether one diagnostic option variant is allowed after the default run.

Do not tune several variants against an expanding review set. Any permitted
second configuration and the decision rule for selecting it must be declared
before reviewing its output.

## Review pass

- **Tool leverage:** project code passes and validates maintained options rather
  than reproducing Docling hierarchy logic.
- **Hierarchy quality:** bookmark-covered, numbered, unnumbered, deeply nested,
  repeated, and embedded-document headings behave under the frozen rubric.
- **False promotions and omissions:** list items, table titles, TOC rows,
  furniture, and visible headings mislabeled as text receive explicit review.
- **Semantic preservation:** text, reading order, tables, figures, geometry,
  images, warnings, and durable artifacts do not change outside the declared
  hierarchy surface.
- **Reproducibility:** identity, output, and comparison rules are deterministic.

## Validation

- Verify the accepted Task 03C.1 completion record and every inventoried input
  checksum before running.
- Require exact source and 222-page coverage.
- Compare every producer artifact and normalized record, not only aggregate
  counts.
- Require exact equality for producer-owned Docling `text` and `orig` values,
  non-hierarchy reading order, tables, table families, figures, images, valid
  geometry, saved content assets, routing/table observations, and warnings
  after declared identity normalization. The accepted Task 03D.1 canonical
  candidate is downstream reference evidence; do not rerun or directly compare
  canonical materialization in this task.
- Enumerate every allowed heading-level, promotion, label, parent, child, and
  hierarchy serialization change.
- Reconcile bookmark-covered headings with the embedded outline and inspect
  visible TOC/body agreement without treating TOC rows as section starts.
- Inspect the complete frozen Appendix P sample and both Task 03A controls
  against requested review-cache renders. Run the controls only through the
  accepted bounded-review harness; do not publish them as complete-document
  producer candidates or generalize their page-range result to the corpus.
- Build the selected candidate independently in fresh scratch publication
  roots and require semantic equality before one immutable publication. Then
  invoke the normal command again and require checksum-verified reuse without
  conversion or table rebuilding.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- Docling hierarchy inference meets every predeclared good-enough threshold and
  has no unreviewed material failure pattern.
- Every undeclared producer semantic and durable artifact is preserved.
- Every hierarchy-related change is enumerated and traceable to the new
  configuration and source evidence.
- The selected configuration is deterministic and versioned.
- The accepted Task 03C.1 producer remains checksum-valid and unchanged.
- No competing project-owned hierarchy algorithm is introduced.
- The task stops for explicit user disposition before any correction or
  semantic-structure task activates.

If Docling is rejected or inconclusive, downstream tasks remain inactive until
the outcome describes the failure evidence and the user authorizes a bounded
fallback evaluation sequence.

## Non-goals

- changing canonical schemas or materializing canonical semantic sections
- printed-page-label inference or target aliases
- cross-reference mention extraction or resolution
- corpus batching or a second document's complete producer run; only the two
  frozen bounded main-report control ranges are permitted
- OCR, VLM, LLM, embedding, or fuzzy semantic hierarchy repair
- a project-owned document-tree inference algorithm
- committing, pushing, or activating a later task without separate approval

## Evaluation evidence (2026-07-30)

The maintained-default candidate is
`prv1-92170ee8b5f5d51ffa738749ee872d7c7e9e5e7dbcb16cf6150bcf33d10d68e1`.
It was built in two fresh, independent Python processes. Both 159-file
inventories compare equal after only the frozen identity and measurement
normalizations, and the normal producer command checksum-verified reuse in
4.18 seconds. The accepted Task 03C.1 producer remains checksum-valid and
unchanged.

The full producer comparison aligned all 6,931 Docling text items, preserved
semantic reading order and every non-hierarchy comparison surface, and
enumerated 256 hierarchy-only level changes, zero promotions, zero reference
rewrites, and zero undeclared baseline changes. On the frozen Appendix P review
set, 29 of 29 uniquely exact bookmark-covered headings received their expected
clamped outline level, 21 of 21 reviewed numbered headings received the
correct relative level, and no visible TOC row was promoted.

The bounded controls fail task sufficiency even though their conversions and
preservation comparisons pass:

- Main-report pages 44-45 retain the known false-positive bullet headings
  `General Plan Amendment` and `Specific Plan`, now at levels 3 and 2.
- Main-report page 2000 retains the visible subheading `Exacerbate Land Use /
  Noise Incompatibilities by Placing People in High Noise Areas` as plain
  `text` with no hierarchy level.
- The Appendix P review also found poor style-fallback depths outside bookmark
  coverage, including `Existing SSF District` at level 6 on page 8, a skipped
  level between `Article 2` and sections `2.01`/`2.02` on page 120, and
  `B. Balancing Account Under This Agreement` at level 6 on page 180.

Decision: **rejected** as the sole project hierarchy policy. This is a quality
rejection, not a producer-integrity failure. The
immutable candidate remains valid evaluation evidence but is not accepted for
downstream canonical work.

Learning note: Docling applies the embedded PDF outline first, then recognized
numbering, then font style. That precedence explains the perfect exact match
for eligible bookmarks and numbered headings, but it cannot be treated as
project-owned canonical hierarchy. The embedded outline is distinct from
visible TOC content, style fallback can assign implausible deep levels, and the
stage does not generally demote existing false section headers or promote
unbookmarked text headings. Tool completion therefore establishes neither
section-boundary accuracy nor retrieval suitability.

Evidence:

- external producer comparison:
  `pipelines/brisbane_baylands/task_03e_hierarchy_review/cmpv2-9106e5d03fa4f1e8f57eadd2b1aa8cc0a02030131f9684964caf6bea86f3aff0/producer_comparison_report.json`
- external bounded review:
  `pipelines/brisbane_baylands/task_03e_hierarchy_review/cmpv2-9106e5d03fa4f1e8f57eadd2b1aa8cc0a02030131f9684964caf6bea86f3aff0/bounded_review_report.json`
- disposable renders:
  `pipelines/brisbane_baylands/review_cache/cmpv2-9106e5d03fa4f1e8f57eadd2b1aa8cc0a02030131f9684964caf6bea86f3aff0/`

Explicit user disposition: **rejected**. The user authorized a two-stage
fallback: Task 03E.1 defined the deterministic correction contract, and Task
03E.2 will implement and evaluate it after separate activation. The former
semantic-structure and cross-reference tasks are renumbered 03E.3 through
03E.5. No fallback implementation is active. The immutable comparison and
bounded-review reports retain their pre-disposition `pending` fields; this
completed task record and [Decision
003](../../docs/decisions/003_deterministic_hierarchy_correction.md) own the
later explicit rejection.

## Outcome

Docling's maintained hierarchy stage is deterministic, preserves the accepted
producer, and performs well for exact embedded-outline matches and conventional
numbering. It is not sufficient as the sole project hierarchy policy because
it retains known false heading labels, misses a visible plain-text subheading,
and assigns poor global fallback depths outside outline coverage.

The accepted next direction is a fast deterministic overlay that preserves raw
Docling evidence, reconciles visible TOC entries to body targets, applies named
project-owned correction rules, records ambiguity, and contains no LLM or
learned component at runtime. Task 03E.1 completed the correction contract;
Task 03E.2 owns implementation and evaluation and remains inactive pending
later explicit activation. The separate Task 03E MVP maintainability cleanup is
complete.
