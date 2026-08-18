# Project TODO

## Sprint status

Status: Sprint 2, Brisbane Draft-EIR defense vertical slice.

Previously completed: [Task
03E.4](../tasks/sprint2/03e4_materialize_semantic_structure.md). Its
checksum-verified semantic v2 MVP candidate
`exv1-c500c1731aa02a97d3cebe1b582eb8b03671a75b29eb3f1df349edd2f34fe5bf`
has zero undeclared Task 03D.1 differences, all four support roles, 222
page-label outcomes, 323 target aliases, byte-identical fresh builds, valid
reuse, and a user-approved exact ten-page visual review. By explicit user
direction it remains immutable reference evidence. Its human-owned replacement
`exv1-2cba27c14e4a1aba72080c9803ce72f8dd728595bcd8176b60ffad777af4cf9b`
passed the independent candidate/review equivalence gate with zero mismatches,
dual-build reproducibility, checksum reuse, failure retention, and a 400-test
project check. The final user-authorized maintainability pass corrected
support-preimage reproducibility and tightened the equivalence, source-
verification, reporting, lifecycle, ownership, and test boundaries.

Most recently completed: [Task
03E.5](../tasks/sprint2/03e5_pilot_cross_references.md). Gate A and Gate B were
explicitly approved before the behavioral MVP. Reference candidate
`exv1-e3e81078dfb21b3d0718cd935004077e163dffc180bbc3d80f4a54391caa67f6`
preserves all 323 upstream aliases, adds 11 verified table aliases, and
materializes 300 exact-span mentions.
Exact target-side table labels may support a table alias under a
same-page/single-table rule. Table mentions then consider exact verified targets
only within five physical pages; multiple targets remain ambiguous and
qualified external-reference forms remain unresolved. Proximity alone cannot
create a target. Current v3
authorizes zero derived figure aliases. By user decision, the OCR-free first
pass detects but does not link figure mentions and reports seven unresolved
figure mentions for later impact evaluation. The original human rewrite had
261 resolved, 38 unresolved, and one ambiguous record, but a user audit found
five incorrect resolved section links. Pattern-policy v2 now excludes complete
reference sections structurally, rejects author-year bibliography entries,
retains `of this Agreement`, and routes named external-section and low-numbered
statutory qualifiers to diagnostics. Its corrected candidate has 256 resolved,
35 unresolved, and one ambiguous record. Any future OCR or figure-linking
support requires a separately reviewed contract revision. No external parsing
dependency or full-corpus scan was added. Accepted corrected candidate
`exv1-34f91f3117d7bbd2284b4b18b7b75df956eec7ca1cb493e6a4bbe51c7563f263`
has eight policy-explained removals, zero additions, zero changed shared
mentions, and 17 exactly preserved paths relative to the prior human rewrite.
Its generic named-EIR rule,
typed policy/domain model, checksum-bound corpus catalog, responsibility-owned
modules, dual-build reproducibility, and checksum reuse passed the separate
human-maintainability gate. The user accepted two source-authored appendix-link
inconsistencies as bounded first-pass noise to handle at query time rather than
through document-specific extraction exceptions. Task 03E.5 is closed.

Previously completed: [Task
03E](../tasks/sprint2/03e_evaluate_docling_heading_hierarchy.md). Its producer
and repeatability gates passed, but the user rejected Docling's maintained
defaults as the sole hierarchy policy because known false headings remained, a
visible subheading remained plain text, and unsupported style fallback produced
poor depths. The immutable candidate remains evaluation evidence.

Previously completed: [Task
03D.1](../tasks/sprint2/03d1_rewrite_canonical_materializer.md). It replaced
the Task 03D MVP's monolithic record builder with typed,
responsibility-specific modules and passed an independent 57-path
semantic-equivalence gate with zero mismatches. [Task
03C](../tasks/sprint2/03c_build_single_document_conversion.md). It converted
all 222 physical pages of Appendix P, saved 27 figure assets, routed 33 pages
through the complete clean table stage, produced 19 logical tables and 19
complete-document families, and atomically published a checksum-verified
task-scoped producer run. Fourteen routed pages have explicit zero-table
mappings, and the run is `complete_with_warnings`.

Earlier completed: [Task
03A.15](../tasks/sprint2/03a15_rewrite_document_parser_pipeline.md) replaced
the document-parser proof of concept, disabled TableFormer, and integrated the
content router with the complete clean table pipeline. The final ten-page v4
run had zero errors, matched every non-table range, produced the two expected
table routes, preserved cleanup/footer/family behavior, and reduced measured
Docling range time from 112.03 to 9.30 seconds. [Task
03A.14](../tasks/sprint2/03a14_run_first_600_table_pipeline.md) completed the
user-approved first-600-page validation of the clean unified table parser in
19.66 minutes. It produced 681 logical tables and exactly matched the ten
reviewed page/table regressions.
[Task 03A.13](../tasks/sprint2/03a13_unify_table_environment.md) moved the clean
table parser into one main uv environment and reproduced all stable Task
03A.12 outputs exactly on the ten-page sample. Tasks 03A.14-03A.15 subsequently
accepted that implementation.
[Task
03A.12](../tasks/sprint2/03a12_rewrite_table_pipeline.md) completed a clean
table-stage draft and ten-page mixed-route test. It produced 89 logical tables,
passed the full 72-test project check, and was accepted through the later
reproduction and integration tasks. [Task
03A.11](../tasks/sprint2/03a11_test_complex_page_segmentation.md) completed the
fixed-parameter test on physical Appendix G3 pages 19, 273, and 592. It found
4, 4, and 35 logical tables respectively, parsed every ruling-derived region,
and was accepted through Task 03A.12. [Task
03A.10](../tasks/sprint2/03a10_detect_complex_page_tables.md) automatically
detected and parsed 34 ruled regions plus one unexplained borderless region on
physical page 527.
[Task
03A.9](../tasks/sprint2/03a9_build_footer_aware_table_families.md) completed
the footer-aware native pass. Four exact worksheet runs cover 582 pages, each
footer belongs only to the last parser table on its page, and footer cleanup
reduces the review-only proposal to 37 families. Page 527 table 2 through page
591 is one 65-page run.
[Task
03A.8](../tasks/sprint2/03a8_cascade_cached_header_evidence.md) completed the
cached cascade. Exact native header matrices passed 130 of 161 boundaries,
recovering 60 beyond Task 03A.7 and reducing the review-only proposal to 62
families. TableFormer uniquely added no passing boundary; no parser, renderer,
or learned model reran.
[Task
03A.7](../tasks/sprint2/03a7_merge_table_families_with_tableformer.md)
completed the first-600-page TableFormer edge pass. All 241 deduplicated crops
and predictions succeeded. Exact non-empty nested headers merged 70 of 161
eligible boundaries, reducing the review-only proposal from 192 to 122
families without rerunning the fast parser.
[Task
03A.6](../tasks/sprint2/03a6_compare_nested_header_labels.md) completed the
exact nested-label comparison. All four pages match, supporting a proposed
merge of families 0014-0016 into pages 22-46 without leaf detection, spans,
geometry, or a model rerun. The Task 03A.4 list remains historical exploratory
evidence. [Task
03A.5](../tasks/sprint2/03a5_test_tableformer_boundary_merge.md) completed the
four-crop TableFormer test at the page 29/30 and 31/32 boundaries. Inference
was fast and coarse shapes matched, but exact grouped-header spans differed at
both boundaries, so the merge result is inconclusive and the Task 03A.4 list
remains unchanged. [Task
03A.4](../tasks/sprint2/03a4_pilot_contiguous_table_families.md) completed the
fast-parser family pilot for G3 pages 1-600. Its unaccepted 192-family proposal
is retained as exploratory evidence and was superseded by the footer-aware
clean pipeline. [Task
03A.3](../tasks/sprint2/03a3_classify_numeric_table_pages.md) completed the
partial numeric-table classification without overwriting Task 03A.2. It
classified 6,067 of 6,104 G3 pages as fast-route candidates, left 37
general-path candidates, and preserved pages 525-526 as a reviewed run
distinct from page 527. [Task
03A.2](../tasks/sprint2/03a2_classify_table_dominant_pages.md) classified all
6,104 Appendix G3 pages in 129 seconds and identified 4,408 table-dominant
pages as conservative fast-route candidates. [Task
03A.1](../tasks/sprint2/03a1_validate_table_extraction.md) completed the
fast-table and accelerator comparison, found a provisional Lattice/Stream
split, and rejected MPS.
[Task 03A](../tasks/sprint2/03a_validate_document_parser.md) completed the
native-only parser pilot and accepted the revised PyPdfium2-backed Docling
candidate. [Task
02](../tasks/sprint2/02_freeze_sources_and_provenance.md) froze and verified
`brisbane_baylands_2025_deir_sources_v1` under the external artifact root.

Tasks 03E.2d through 03E.5 are complete. Task 03F is a four-part umbrella.
[Task
03F.1](../tasks/sprint2/03f1_define_restartable_extraction_contract.md) is
complete with its Gate A inventory and Gate B contract explicitly accepted.
[Task 03F.2](../tasks/sprint2/03f2_generalize_restartable_document_stage.md) is
complete. Its human-owned replacement preserves the accepted restartable
behavior and exact offline Appendix P evidence and passes the separate
maintainability gate. Task 03F.3 Gate A is complete with a validated v1.1
executable-contract corrigendum. Its Gate B synthetic runtime served as a
transient rewrite oracle. Task 03F.3 is complete after the human-owned
replacement passed exact fixed-evidence artifact equivalence and substantive
maintainability checks; the unused MVP package, equivalence test, and retained
identity copy were then removed. A later user-authorized Appendix P Task 03F.4
attempt found stale inter-stage IDs and candidate-bound authorization evidence.
After fail-fast lineage validation and candidate-neutral review, the user
approved the exact candidate rebind. The refreshed hierarchy, semantic, and
cross-reference chain now verifies, and the 222-page document transaction
completed as `docv1-c7160cd...188fb0` with checksum reuse verified.
[Task
03E.0](../tasks/sprint2/03e0_rewrite_hierarchy_evaluation.md) completed the
behavior-preserving rewrite of the Task 03E evaluator and matched both frozen
159-artifact comparisons exactly.

## Open queue

1. Task 03F.4 is complete and accepted. Fail-fast lineage validation now runs
   before attempt allocation; refreshed production identity
   `exv1-1bd71e02...c1fcc4` completed Appendix P as
   `docv1-532b14da...8df40`. The hierarchy authorization remains bounded to
   Appendix P.
2. [Task 03G](../tasks/sprint2/03g_run_representative_extraction_pilot.md) is an
   open umbrella. [Task
   03G.1](../tasks/sprint2/03g1_smoke_all_model_corpus_sources.md) is complete
   and accepted as an MVP diagnostic: all 342 requested pages across 35 sources
   have terminal outcomes, all sources were inspected, and the separate
   human-maintainability rewrite passed preservation and project validation. It
   published no complete-document or corpus candidate.
3. Completed and accepted [Task
   03G.1a](../tasks/sprint2/03g1a_remediate_smoke_extraction_failures.md) owns
   the four user-selected improvements: warning scope/accounting, rotated-page
   routing geometry, bounded learned fallback for credible zero-output table
   regions, and cross-page continuation recovery. The user activated it as one
   end-to-end remediation on 2026-08-04, including bounded affected-page
   PDF/TableFormer validation. Behavioral implementation, the checksum-closed
   bounded regression, the user-requested OTSL reevaluation, and the separate
   human-maintainability rewrite are complete: warning scope
   and routing controls pass, learned fallback recovered 14 of 17 positive
   pages with 26 accepted regions, and the three original positive/one negative
   continuation boundaries still match expectations. One newly evaluable K1
   part 3 continuation also accepts; four K1 boundaries remain ambiguous and
   one is not evaluable because its edge page has no accepted table. The fresh
   v7 run exactly preserves all 35 fallback attempts and every persisted
   continuation decision after the responsibility split.
   The refreshed non-executed production recipe is
   `exv1-a0908c8f...5adee`. The user accepted the behavioral and
   human-maintainability outcome on 2026-08-05. No full smoke rerun or
   complete-document/corpus candidate was produced.
4. Completed remediation [Task
   03G.2a](../tasks/sprint2/03g2a_remediate_main_table_boundaries.md) fixed and
   validated the hard split, genuine continuation, and repeated header-only
   fragment regimes. The refreshed 2,092-page main baseline and hierarchy
   producers sealed, but canonical materialization failed twice because 24
   Docling `document_index` regions became logical tables and suppressed 7,092
   required descendant text blocks. Completed [Task
   03G.2b](../tasks/sprint2/03g2b_preserve_document_index_text.md) derived the
   filtered canonical table view, checksum-reused both main producers, and
   completed the main document through all six owners. The resumed scope then
   exposed two source-general failures. Completed [Task
   03G.2c](../tasks/sprint2/03g2c_remediate_cross_source_geometry_and_alignment.md)
   completed the source-general geometry and alignment repair, all six fresh
   producers, all downstream content owners, the three document candidates,
   and exact scope accounting. Completed [Task
   03G.2d](../tasks/sprint2/03g2d_seal_complete_target_streams.md) exposed all
   five sealed semantic target streams, published the ready handoff, and proved
   exact reuse. Completed [Task
   03G.2e](../tasks/sprint2/03g2e_repair_pilot_report_page_labels.md) repaired
   the review-only page-label observation path and published the aggregate
   report plus a checksummed request-only render recipe with no renders.
   Review then found that the valid sealed corpus-resolution candidate had
   zero eligible mentions and zero rows: at least 8 main-report references to
   Appendix D and 10 to Appendix P never crossed the local/corpus boundary.
   Completed [Task
   03G.2f](../tasks/sprint2/03g2f_repair_cross_document_resolution.md) delivered
   the downstream-only shared source-family catalog and resolver repair,
   together with the approved five- to ten-physical-page exact-table window.
   It reused every checksum-valid completion through semantic materialization
   without rerunning PDF, model, parser, producer, canonical, hierarchy, or
   semantic work. The subsequent offline human-ownership refactor replaced
   the monolithic runner with a 45-line CLI and typed responsibility-owned
   replay, audit, inventory, and validation modules. Stable diagnostic codes,
   module/function size gates, and direct pure-behavior tests now pass in the
   520-test project gate. The maintained bounded replay then published scope
   `scopev1-c52b...beb6a8`, resolved all 18 eligible mentions, passed
   independent handoff/report/request validation and exact reuse, and changed
   no forbidden attempt inventory. No upstream content owner or document
   attempt ran. [Task
   03G.2](../tasks/sprint2/03g2_run_three_document_full_pilot.md)
   is complete and accepted: all 18 eligible mentions resolved, the ten-page table replay
   matched every exact expectation, the handoff/report validate, and identical
   invocation reused exact bytes without upstream or document attempts.
   The maintained execution reproduced the accepted report metrics and closed
   both Task 03G.2 and Task 03G.2f.
   Historical Appendix P lineage remains forbidden.
5. Review and explicitly activate drafted [Task
   03G.3](../tasks/sprint2/03g3_align_pipeline_responsibilities_and_names.md).
   It must inventory and freeze the exact semantic responsibility graph,
   operation-oriented vocabulary, caller/artifact migration, and identity
   consequences before implementation. It then owns the behavior-preserving
   refactor and revision of provisional [Task
   03H](../tasks/sprint2/03h_run_full_canonical_extraction.md). No PDF/model run,
   implementation, commit, or Task 03H activation is authorized by the drafted
   contract. Close Task 03G only after Task 03G.3 is accepted.
6. Independently review usability and freeze the accepted extraction release
   in Task 04.
7. Continue through the separately identified curator-only response inventory,
   reference-case authoring, clustering, and benchmark freeze.
8. Freeze human evaluation before BM25 retrieval, target generation, and judge
   calibration; finish with the primary test and oracle diagnostics.

Sprint 2 scope, decisions, and provisional sequencing live in
`docs/sprints/sprint2_brisbane_draft_eir_defense.md`. The completed Task 02
owns source-freeze implementation detail and the precise extraction handoff.
