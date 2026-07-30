# Docs Index

This page routes humans and agents to the smallest useful set of project docs.
Start with `AGENTS.md`, then return here to decide what to read or skip.

## Current status

This section is the source of record for the current sprint and active task.
`docs/todo.md` owns the detailed queue and next action.

Sprint 1 accepted the first benchmark contract: a Brisbane Draft-EIR defense
task. Sprint 2 is current. [Task
02](../tasks/sprint2/02_freeze_sources_and_provenance.md) completed the
versioned source freeze. [Task
03A](../tasks/sprint2/03a_validate_document_parser.md) completed the
native-only structural pilot and accepted the revised
Docling-plus-PyPdfium2 candidate with one bounded dense-table failure. [Task
03A.1](../tasks/sprint2/03a1_validate_table_extraction.md) completed the
fast-table comparison. It found a promising Lattice/Stream split and rejected
MPS, but formally rejected the split as the production contract because the
all-table stress projection exceeded 72 hours. [Task
03A.2](../tasks/sprint2/03a2_classify_table_dominant_pages.md) completed a cheap
native-PDF table-dominance scan across Appendix G3. It classified 4,408 of
6,104 pages in 129 seconds and was accepted as a conservative routing signal,
not table validation. [Task
03A.3](../tasks/sprint2/03a3_classify_numeric_table_pages.md) completed the
expanded G3 numeric-table routing signal. It classified 6,067 of 6,104 pages
as fast-route candidates, added 1,659 partial or non-dominant table pages
without removing a Task 03A.2 positive, and preserved pages 525-526 as one
reviewed run distinct from page 527.
[Task
03A.4](../tasks/sprint2/03a4_pilot_contiguous_table_families.md) completed the
first G3 contiguous-family pilot. Its over-segmented 192-family proposal is
closed as exploratory evidence and was superseded by the footer-aware clean
pipeline.
[Task
03A.5](../tasks/sprint2/03a5_test_tableformer_boundary_merge.md) completed one
bounded bare-TableFormer boundary test. Four header-plus-data crops ran in
1.74 total inference seconds and all produced the same 4-row, 7-column coarse
shape, but grouped-header span predictions differed at both boundaries. The
exact merge rule is therefore inconclusive and the Task 03A.4 list remains
unchanged.
[Task
03A.6](../tasks/sprint2/03a6_compare_nested_header_labels.md) completed the
simple reanalysis. All four preserved predictions have an identical nested
tuple of normalized header labels, so the rule recommends merging families
0014-0016 into pages 22-46. It did not identify leaf headers, use spans, rerun
a model, or rewrite the Task 03A.4 list.
[Task
03A.7](../tasks/sprint2/03a7_merge_table_families_with_tableformer.md)
completed the first-600-page boundary pass. All 241 deduplicated edge crops
and predictions succeeded; 70 of 161 boundaries passed the exact non-empty
nested-header rule, reducing the review-only proposal from 192 to 122
families. The revised list remains historical exploratory evidence.
[Task
03A.8](../tasks/sprint2/03a8_cascade_cached_header_evidence.md) completed the
cached evidence cascade. Exact native header matrices passed 130 of 161
boundaries and reduced the review-only proposal to 62 families; TableFormer
uniquely added no passing boundary. Pages 71/72 merge, pages 526/527 remain
split, and no parser, renderer, or learned model reran.
[Task
03A.9](../tasks/sprint2/03a9_build_footer_aware_table_families.md) completed
the footer-aware native pass. It found four exact worksheet runs on 582 pages,
assigned each footer only to the last Camelot table on its page, cleaned
footer-only columns, and reduced the review-only proposal to 37 families.
Page 527 table 2 through page 591 is one 65-page run; TableFormer did not run.
[Task
03A.10](../tasks/sprint2/03a10_detect_complex_page_tables.md) completed the
one-page experiment: automatic ruling geometry plus an unexplained Network
region proposed 35 logical page-527 tables and parsed all 34 ruled regions.
[Task
03A.11](../tasks/sprint2/03a11_test_complex_page_segmentation.md) completed the
fixed-parameter test on physical pages 19, 273, and 592. It proposed 4, 4, and
35 logical tables respectively, parsed all 42 ruling-derived regions, and
retained one unexplained borderless Network region on page 592.
[Task
03A.12](../tasks/sprint2/03a12_rewrite_table_pipeline.md) completed the clean
table-stage draft and ten-page mixed-route test. It produced 89 logical tables
across four simple and six complex pages, passed the full project check, and
was accepted through the exact Task 03A.13 reproduction and subsequent
first-600 and cross-document integration validations.
[Task
03A.13](../tasks/sprint2/03a13_unify_table_environment.md) put Docling and
Camelot in one locked headless-OpenCV environment and removed the clean
parser's subprocess boundary. Its sequential ten-page run exactly matched all
stable Task 03A.12 page, table, and family outputs. [Task
03A.14](../tasks/sprint2/03a14_run_first_600_table_pipeline.md) completed the
user-approved validation on exactly physical pages 1-600. It produced 681
logical tables in 19.66 minutes, formed four footer runs plus 99 singleton
families, and exactly matched the ten reviewed page/table regressions.
[Task
03A.15](../tasks/sprint2/03a15_rewrite_document_parser_pipeline.md) completed
the maintainable document-pipeline rewrite and closed Task 03A. Its final v4
run disabled TableFormer, reproduced all non-table invariants, routed exactly
main page 1500 and G3 page 1000, and invoked the complete clean table pipeline
without bypassing cleanup, footer ownership, family assignment, or sealing.
The completed [Task
03B](../tasks/sprint2/03b_define_canonical_extraction_contract.md) defines the
MVP canonical contract, executable schemas, fixtures, and offline invariant
tests. Its separate cleanup pass reorganized executable enforcement around
human-owned bundle, content, and lineage policies. [Task
03C](../tasks/sprint2/03c_build_single_document_conversion.md) completed the
first task-scoped complete-document producer run. Appendix P covered all 222
pages, routed 33 pages into the clean table stage, produced 19 tables and 19
complete-document families, and atomically published a checksum-verified run.
[Task
03C.1](../tasks/sprint2/03c1_rewrite_complete_document_producer.md) replaced
the Task 03C reference orchestrator with the human-owned implementation. Its
new code-bound run reproduced all semantic producer artifacts, passed 112
offline tests, and is now the default `documents run-complete` implementation.

The accepted benchmark contract is `benchmarks/er_bench/sprint1.md`; the
durable rationale is
[Decision 001](decisions/001_brisbane_draft_eir_defense_benchmark.md).
Sprint 2 is the smallest source-to-evaluation vertical slice. At the user's
request, the large canonical-extraction stage is decomposed into Task 03A
through Task 03H in the
[Sprint 2 plan](sprints/sprint2_brisbane_draft_eir_defense.md). Tasks 03B
through 03D, including the 03C.1 maintainability rewrite, are complete. The
completed Task 03D MVP remains reference evidence. [Task
03D.1](../tasks/sprint2/03d1_rewrite_canonical_materializer.md) replaced its
monolithic materializer with a human-owned implementation and passed an
independent record-level equivalence gate. [Task
03E](../tasks/sprint2/03e_evaluate_docling_heading_hierarchy.md) now evaluates
Docling's maintained heading hierarchy against that accepted candidate and is
planned but inactive pending user review. Tasks 03E.1 through 03H are
provisional contracts that assume the Task 03E acceptance gate passes and must
still be revised from each preceding outcome before activation.

## Document roles

- `docs/product.md`: project purpose, current scope, claim boundaries, and
  success criteria. Read when the task changes what the project is for.
- `docs/architecture.md`: package, CLI, pipeline, benchmark, and configuration
  boundaries. Read for technical design or implementation shape.
- `docs/data_artifacts.md`: external data root, artifact layout, Git policy,
  and provenance expectations. Read for any data or generated output work.
- `docs/documentation.md`: documentation ownership and change checklist. Read
  before editing or creating durable docs.
- `docs/todo.md`: active queue and next action. Read to select work; it does
  not replace a task contract.
- `docs/backlog.md`: unselected future ideas only. It does not define current
  scope or record decisions.
- `docs/sprints/`: sprint-level scope, research questions, and ordering.
- `docs/decisions/`: durable accepted choices and non-promoted results.
- `tasks/`: narrow agent-sized contracts with validation and outcomes.

Do not read every document to begin narrow work. When a task is active, use its
input list and the roles above. When no task is active, use `docs/todo.md` and
the current sprint plan only to write the next bounded task contract.
