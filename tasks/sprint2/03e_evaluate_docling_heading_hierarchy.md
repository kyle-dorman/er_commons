# Task 03E: Evaluate Docling Heading Hierarchy

Status: **planned and inactive pending explicit user activation**. Writing this
contract does not authorize a producer run. Tasks 03E.1 through 03E.3 are
provisional and cannot activate unless this task accepts Docling's maintained
hierarchy output as good enough.

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
- an independent comparison report against the accepted Task 03C.1 producer
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
- Require exact equality for raw/canonical text, non-hierarchy reading order,
  tables, table families, figures, images, valid geometry, saved content assets,
  routing/table observations, and warnings after declared identity
  normalization.
- Enumerate every allowed heading-level, promotion, label, parent, child, and
  hierarchy serialization change.
- Reconcile bookmark-covered headings with the embedded outline and inspect
  visible TOC/body agreement without treating TOC rows as section starts.
- Inspect the complete frozen Appendix P sample and both Task 03A controls
  against requested review-cache renders. Run the controls only through the
  accepted bounded-review harness; do not publish them as complete-document
  producer candidates or generalize their page-range result to the corpus.
- Repeat the accepted candidate and require semantic equality and verified
  checksum reuse.
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
- The task stops for explicit user acceptance before Task 03E.1 activates.

If Docling is rejected or inconclusive, Tasks 03E.1 through 03H remain inactive.
The outcome must describe the failure evidence and propose, but not implement,
the smallest new fallback evaluation task.

## Non-goals

- changing canonical schemas or materializing canonical semantic sections
- printed-page-label inference or target aliases
- cross-reference mention extraction or resolution
- corpus batching or a second document's complete producer run; only the two
  frozen bounded main-report control ranges are permitted
- OCR, VLM, LLM, embedding, or fuzzy semantic hierarchy repair
- a project-owned document-tree inference algorithm
- committing, pushing, or activating a later task without separate approval
