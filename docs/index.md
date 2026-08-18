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
03E](../tasks/sprint2/03e_evaluate_docling_heading_hierarchy.md) completed its
deterministic producer gate but rejected Docling's maintained defaults as the
sole project hierarchy policy. The Task 03D.1 candidate remains downstream
reference evidence. [Task
03E.0](../tasks/sprint2/03e0_rewrite_hierarchy_evaluation.md) replaced the
Task 03E MVP evaluator with an exactly equivalent human-owned implementation.
[Task
03E.1](../tasks/sprint2/03e1_define_deterministic_hierarchy_correction.md)
completed its deterministic contract, fixtures, and human-oriented
cross-record validator after a reference-equivalence and maintainability gate.
The unanchored page-2000 heading remains a non-blocking ambiguity by user
decision. [Task
03E.2](../tasks/sprint2/03e2_implement_deterministic_hierarchy_correction.md)
completed implementation and evaluation, but its frozen quality gate rejected
publication: four development fixtures failed and held-out review found two
false table boundaries plus four wrong level/parent results. Outline,
numbering, controls, preservation, repeatability, and resource gates passed.
That candidate remains historically rejected; the task is closed as MVP
reference evidence and was superseded for production ownership by Task 03E.2b.
Task 03E.3 is complete after its human-ownership rewrite. Canonical-extraction
schema major v2, exact bridge and preservation contracts, 222-page label
outcomes, target-only aliases, and bounded-control propagation now have a
responsibility-owned validator that passed independent maintainability and
refactor-safety review. [Task
03E.4](../tasks/sprint2/03e4_materialize_semantic_structure.md) is complete. Its
visually approved behavioral MVP candidate
`exv1-c500c1731aa02a97d3cebe1b582eb8b03671a75b29eb3f1df349edd2f34fe5bf`
remains immutable reference evidence. The human-owned replacement
`exv1-2cba27c14e4a1aba72080c9803ce72f8dd728595bcd8176b60ffad777af4cf9b`
has zero candidate and review mismatches under its independent equivalence gate,
retains the exact ten-page review pixels, and is accepted as the immutable
handoff to completed [Task
03E.5](../tasks/sprint2/03e5_pilot_cross_references.md). Its read-only Gate A
inventory and checked-in Gate B contract were explicitly approved before
production. Behavioral MVP candidate
`exv1-e3e81078dfb21b3d0718cd935004077e163dffc180bbc3d80f4a54391caa67f6`
remains immutable reference evidence. The first human-owned candidate
`exv1-4a65944e4ce99a445953ea2904ca0e0c4b20fdd5412e9b89e7b6dac0254cc464`
matched it across all 19 semantic paths but is now immutable
correction-baseline evidence after a user audit found five false resolved
section links. Accepted pattern-policy-v2 candidate
`exv1-34f91f3117d7bbd2284b4b18b7b75df956eec7ca1cb493e6a4bbe51c7563f263`
uses this
precision-first policy:
target-side table labels may support a table alias only under a strict
same-page/single-table rule. Table mentions consider exact verified targets
only within five physical pages, with multiple targets left ambiguous and
qualified external-reference forms unresolved. Distance never creates target
evidence. Figure
mentions remain unresolved because current v3 authorizes zero derived figure
aliases. The user selected an OCR-free first pass that skips figure linking and
retains unresolved counts for impact evaluation. It contains 292 mentions, 256
resolved records, 35 unresolved records, one ambiguous `Section 4`, 11 verified
table aliases, and zero figure aliases. Any future OCR or figure-link support
requires a separately reviewed contract revision. The accepted implementation
uses explicit policy/domain types and a generic named-EIR grammar backed by the
sealed corpus catalog rather than fixture-specific document text. Reference
sections are structurally excluded, and explicit external/statutory section
qualifiers cannot fall through to local numeric lookup. The user accepted two
visually confirmed source-authored appendix-link inconsistencies as bounded
first-pass noise; no document-specific correction is applied. Task 03E.5 is
accepted. [Task
03F](../tasks/sprint2/03f_make_extraction_restartable.md) is now a four-part
umbrella. [Task
03F.1](../tasks/sprint2/03f1_define_restartable_extraction_contract.md) is
complete with its read-only inventory and Gate B two-stage corpus contract
explicitly accepted. [Task
03F.2](../tasks/sprint2/03f2_generalize_restartable_document_stage.md) is
complete. Its human-owned replacement preserved the behavioral MVP and exact
offline Appendix P evidence, then passed the separate maintainability gate.
[Task 03F.3](../tasks/sprint2/03f3_implement_corpus_resolution_workflow.md)
completed Gate A with the validated v1.1 executable-contract corrigendum and
non-executed production identity. Its synthetic Gate B implementation served as
a transient rewrite oracle. The task is complete after its human-owned
replacement passed exact fixed-evidence artifact equivalence and substantive
maintainability gates; the unused MVP package, equivalence test, and retained
identity copy were then removed. Its final non-executed production identity is
`exv1-3cbbe57424f72ca8800456b23c887e1b2b65693917a8b33ac40791f3630852ea`.
[Task 03F.4](../tasks/sprint2/03f4_prune_extraction_proof_scaffolding.md) is
complete and accepted after its read-only Gate A, integrated Gate B cleanup,
and pre-close maintainability pass.
The maintained stages build once, validate active invariants, and publish or
verify reuse; hierarchy records one honest build while Appendix P's bounded
authorization remains source-specific. Corpus v1, reference/rewrite/repeat/
quality/review proof paths, completed-task commands, and their proof-only
schemas/configs/tests were removed after invariant transfer. Candidate-neutral
comparison/requested-render utilities and read-only handoff validation preserve
the declared Task 03G--04 capabilities. Fail-fast lineage validation now
rejects stale inter-stage pins before attempt allocation or PDF work. After
candidate-neutral review, the user approved the exact Appendix P hierarchy
rebind. The pre-close maintainability pass refreshed hierarchy candidate
`hcorv1-30385014...1ad42`, semantic candidate `exv1-89a57777...8f6c4`, and
cross-reference candidate `exv1-1da64e08...21509`. Production identity
`exv1-1bd71e02...c1fcc4` completed all 222 Appendix P pages through sealed
stage reuse as `docv1-532b14da...8df40`; checksum reuse was verified. [Task
03G](../tasks/sprint2/03g_run_representative_extraction_pilot.md) is now an open
umbrella. [Task
03G.1](../tasks/sprint2/03g1_smoke_all_model_corpus_sources.md) is complete and
accepted as an MVP diagnostic after all 342 requested pages completed, all 35
sources were inspected, and its separate human-maintainability rewrite passed
preservation and project validation. Completed and accepted [Task
03G.1a](../tasks/sprint2/03g1a_remediate_smoke_extraction_failures.md) owns the
four selected warning, rotated-geometry, learned-fallback, and continuation
improvements as one end-to-end remediation. Its implementation and bounded
behavioral regression and separate human-maintainability rewrite passed user
acceptance on 2026-08-05: after correcting both the
compressed-column interpretation and missing-header acceptance gap, the
learned path recovered 14 of 17 fixed pages with 26 accepted regions and nine
explicit abstentions after excluding only clipped top-edge text wholly outside
the structural grid. The responsibility-owned implementation exactly preserves
all 35 fallback decisions and all persisted continuation decisions in a fresh
v7 bounded run. The new non-executed production recipe is
`exv1-a0908c8f...5adee`. [Task
03G.2](../tasks/sprint2/03g2_run_three_document_full_pilot.md) execution was
separately approved after fresh-lineage preparation. Completed [Task
03G.2a](../tasks/sprint2/03g2a_remediate_main_table_boundaries.md) fixed the
first continuation/family invariant. Completed [Task
03G.2b](../tasks/sprint2/03g2b_preserve_document_index_text.md) then filtered
Docling `document_index` mappings only in the canonical logical-table view,
checksum-reused the sealed main producers, and completed the main document
through all six owners. The resumed scope exposed off-canvas Appendix D native
text geometry and 18 uniquely corresponding Appendix P producer text items
with subpoint bbox drift. Task
[03G.2c](../tasks/sprint2/03g2c_remediate_cross_source_geometry_and_alignment.md)
completed both source-general corrections and the three full document
candidates. Completed [Task
03G.2d](../tasks/sprint2/03g2d_seal_complete_target_streams.md) repaired the
sealed target-stream handoff, published a ready handoff, and proved exact
reuse. Completed [Task
03G.2e](../tasks/sprint2/03g2e_repair_pilot_report_page_labels.md) repaired the
review-only page-label observation path and completed final aggregate
reporting. Review then found that the sealed corpus resolver received zero
eligible mentions even though the main report contains at least 8 references
to Appendix D and 10 to Appendix P. Active [Task
03G.2f](../tasks/sprint2/03g2f_repair_cross_document_resolution.md) completed
the
shared source-family boundary and ran the approved ten-page exact-table policy
without PDF, model, parser, producer, semantic, or document attempts. All 18
eligible mentions resolved, every exact table/local-ownership control passed,
the handoff and aggregate report validate, and identical invocation reused
exact bytes. The offline human-ownership refactor then replaced the monolithic
runner with a 45-line CLI and typed responsibility-owned replay, audit,
inventory, and validation modules. The 520-test project gate, stable
diagnostics, and objective module/function size gates pass without rerunning
any upstream content-owner stage. Its maintained bounded replay then published
scope `scopev1-c52b...beb6a8`, resolved 18/18 eligible mentions, validated the
ready handoff and report independently, proved exact reuse, and preserved all
forbidden attempt inventories. Task 03G.2 and Task 03G.2f are closed. No
historical Appendix P producer, candidate, or bounded authorization entered
the replay. Task 03H remains provisional.
[Task 03E.2a](../tasks/sprint2/03e2a_fix_nested_regime_exit.md) completed the
user-authorized follow-up for the single material Appendix E defect. Its
general nested-regime exit reset passed synthetic and real-source regressions
without rewriting the rejected evaluation or activating Task 03E.3.
[Task 03E.2b](../tasks/sprint2/03e2b_rewrite_hierarchy_correction.md) completed
the human-ownership rewrite of the 03E.2/03E.2a MVP. Its responsibility-owned
semantic, review, quality, and application modules reproduce the complete
post-03E.2a semantic payload byte-for-byte and passed the explicit
human-maintainability review. The MVP remains reference evidence, not the
production implementation. [Task
03E.2d](../tasks/sprint2/03e2d_accept_and_publish_hierarchy_correction.md) is
complete. It published the full human-owned Appendix P correction candidate
`hcorv1-aab01b14c3122dbc0f5cec57147b5be2eadaf1cd895311ef7dafa46b469348b1`
under a separate, candidate-bound `accepted_with_known_limitations`
authorization while preserving the historical rejection. Task 03E.3's
behavioral MVP satisfies the exact handoff, including both semantic digest
roles, the cross-producer bridge, mixed-content coverage, page-label provenance,
and bounded-acceptance requirements. Its human-owned validator is the accepted
validation authority used by completed Task 03E.4.

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
