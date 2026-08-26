# Docs Index

This page routes humans and agents to the smallest useful set of project docs.
Start with `AGENTS.md`, then return here to decide what to read or skip.

## Current status

This section is the source of record for the current sprint and active task.
`docs/todo.md` owns the detailed queue and next action.

[Task 03H](../tasks/sprint2/03h_run_full_canonical_extraction.md) is complete as
the first full-corpus end-to-end attempt. It exercised and repaired the production
path but intentionally did not claim the final corpus after its closing identity
and maintainability corrections made a fresh run necessary. Completed [Task
04](../tasks/sprint2/04_review_extraction_and_freeze_release.md) completed its
first-pass user review and independent human-maintainability gate. It used the
mostly but not fully extracted Task 03H evidence to qualify a read-only local HTML review workspace and
produce anchored extraction findings. Those findings feed active [Task
03I](../tasks/sprint2/03i_remediate_task04_review_findings.md), whose first repair
and independent maintainability gate are complete. Its committed task outcome is
the durable disposition of the approved Task 04 finding.
Provisional [Task
03J](../tasks/sprint2/03j_run_final_canonical_extraction.md) then owns the fresh
35-source attempt and machine handoff. Provisional [Task
04A](../tasks/sprint2/04a_regenerate_review_and_freeze_release.md) owns the new
Task 03J-bound review dataset, rechecks, usability registry, and final release
decision. Its exact identities, paths, checksums, and handoff fields must be filled
from the completed Task 03J outcome rather than guessed in Task 04.
Retained Task 03H production artifacts are diagnostic evidence and are ineligible
for 03J reuse.

The current retained Task 03H evidence root is
`pipelines/brisbane_baylands/task_03h_clean_full_v3/` under
`ER_COMMONS_DATA_ROOT`. Its managed attempt and retry streams are available for
Task 04's diagnostic inventory; its `.trash/` subtree is retained evidence but is
excluded from normative queue populations unless Gate A explicitly promotes a
subtree with a separate identity. The v1 and v2 roots are historical and must not
be used as current inputs. Each Task 04 pass writes durable records under
`pipelines/brisbane_baylands/task_04_review/<reviewv1-id>/`; Task 04 owns the
first-pass record contract and Task 04A owns the post-03J record contract.

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
through Task 03J in the
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
the declared Task 03G--04 capabilities. Human-review code uses one validated
`ReviewSelection` for both grouped `RenderPlan` requests and
`GeneratedReviewManifest` outputs, while retaining the accepted v2 request and
v1 generated-manifest artifact schemas. Fail-fast lineage validation now
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
to Appendix D and 10 to Appendix P. Completed [Task
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
the replay. Completed [Task
03G.3](../tasks/sprint2/03g3_align_pipeline_responsibilities_and_names.md)
aligned the maintained code with the accepted responsibility DAG. Maintained code follows
the accepted document/collection responsibility DAG; public commands use
`documents` and `collections`; strict v2 workflow contracts cannot accept v1 keys;
and machine reporting is separate from human review support. All 270 frozen Task
03G.2 control files reverified exactly. No PDF/model ran and no accepted artifact
changed. The distinct human-maintainability pass is now implemented and offline-
validated: current execution uses native v2 records/identities, application shells and
runtime seams are responsibility-owned and typed, recovery diagnostics name corrupt
evidence, and behavior-focused gates pass all 595 tests plus strict mypy across 287
source files. The user accepted the human-maintainability result and closed Task
03G.3 on 2026-08-18.

## Historical Task 03H execution record

The following timeline preserves prior Task 03H execution evidence. Its v2
namespace and identities are historical; the current retained diagnostic root and
Task 04 handoff are defined in the current-status section above.

[Task
03H](../tasks/sprint2/03h_run_full_canonical_extraction.md) was reactivated on
2026-08-19. Clean source-free preparation completed, and the user approved a fresh
`deir_main` run. The historical first five-source wave is complete, and K2
part 5 sealed both memory-safe Docling conversions and derived table producers. Later K2
work exposed a 24 GB raw view, physical duplication, a 31.3-minute mapping stage, a
94.7-minute hierarchy failure, a separate 93.8-minute producer rebuild after
unrelated identity churn, and a quadratic-like heading-alignment scan. At that checkpoint, [Task
03H.1](../tasks/sprint2/03h1_profile_and_repair_full_document_scaling.md) has completed
Gate B implementation and K2 validation plus the Gate C human-ownership refactor,
deterministic identity refresh, full repository validation, and independent
cross-owner recovery review. The user approved the reviewed scope and closed Task
03H.1 on 2026-08-19. The
JSON-first MVP replaces the 22.51 GB replay record with a 26.31 MB page-alignment
stream, uses one base document plus a 470 KB heading overlay, and uses closed
references instead of raw-payload copies. Final K2 mapping completed in 8.29 minutes.
The full K2 hierarchy sealed in 17.03 minutes at 14.73 GB peak RSS and occupies 3.6
GiB instead of the former approximately 24 GB view. Ordinary completion-seal reuse is
subsecond without opening semantic payloads; an audit-only command retains exact
full-byte verification. Ruff, strict mypy across 316 source files, all 732 tests,
deterministic generation, and `git diff --check` pass. No additional source processing,
collection assembly, deletion, or Docling rerun is required to close Task 03H.1.
Task 03H then prepared a clean run from the first ordered source under the reviewed run
plan; it does not continue a historical remaining-source queue or reuse historical
Docling runs. The isolated namespace will create fresh conversion seals for all 35
sources, and restart reuse begins only within that new run.
The clean main-report conversion, shared producer, mapping, and hierarchy stages
sealed within the reviewed budgets, but document structure initially treated the
shared producer's legacy base-view annotation as the hierarchy consumer role. The
automatic retry reused all sealed work and reproduced the failure without a model
call. The approved repair makes base and heading explicit consumer selections while
preserving the one sealed conversion and shared routing/table bundle. Its focused
regressions and full 733-test repository gate pass, and Task 03H has resumed from the
retained `deir_main` transaction under production identity `exv1-66de7f37...df405`.
That transaction published `docv1-aea7f7e...69543`. Appendix A then sealed its fresh
514-page conversion, shared producer, and record mapping but failed twice at hierarchy
cross-record validation. Visual inspection proved A-3 is a heading and peer of A-2;
intervening numbered standards rows had polluted the generic predecessor check. The
approved repair prefers a same-depth, same-parent-prefix decimal peer and retains the
documented fail-closed branch for genuine jumps. A live Appendix A semantic build now
classifies A-3 as an applied level-5 heading. All 735 tests and the full gate pass under
identity `exv1-f0c129ad...df66d7`, and Task 03H is resuming from Appendix A's sealed
upstream artifacts without rerunning Docling.
That resume exposed seven genuine fifth-depth `6.5.2.2.x` headings whose calibrated
level 7 exceeded the semantic contract's level-6 maximum. The approved repair clips
all inferred heading levels to 6 and enforces the same maximum in the hierarchy
decision schema. Its Appendix A-shaped regression retains the deepest items as
headings under production identity `exv1-1027d4c6...ccd3d84`; Appendix A resumes from
its sealed upstream artifacts.
Appendix A then published all 514 pages as `docv1-7c030772...e64bc`. Appendix B sealed
its fresh 258-page conversion, shared producer, and record mapping, but both hierarchy
attempts fail closed on the source PDF's destinationless `TRT.pdf` grouping bookmark.
It owns valid child bookmarks but has no visible adjacent-page title, so the existing
strict container recovery correctly refuses to synthesize it. Task 03H was paused
before Appendix C. The user approved a transparent filename-container rule that
excludes appendix-labeled and distinctively numbered recovery candidates and requires
a nonempty, valid, internally ordered child list. Actual Appendix B inspection retains
63 outline observations and records exactly nine omissions. All 740 tests and the full
gate pass under identity `exv1-fb4f9bb9...8c6b68`; Appendix B is resuming from sealed
upstream work.
Appendix B subsequently published as `docv1-46bf7426...1624`, followed serially by
Appendices C, D, E, F1, and F2. Appendix G1 completed fresh content parsing for all
2,488 pages and sealed shared producer `prv1-159379eb...1b74`; all 2,076 routed table
pages completed and record mapping sealed below the 16 GiB resource ceiling. Both
hierarchy attempts then failed before traversal because pypdf cannot construct a raw
`Appendix_071024.pdf` outline node whose destination array is
`[null, 0.0, 0.0, 1]`. Its ten children include two invalid destinations, so the
approved Appendix B transparent-container rule does not apply. Task 03H was paused
before Appendix G2 pending review of a distinct tolerant-outline rule.
The approved two-child G1 omission passes focused regressions, but live traversal then
revealed an earlier destinationless `Binder4.pdf` subtree hidden by pypdf's original
failure. Its nested Building group has one invalid and 29 valid children, while its
Sustainability group and all nine children are invalid. Because resolving or omitting
that nested tree exceeds the approved two-leaf change, G1 remains paused with its
sealed upstream work reusable.
The user approved the expanded evidence-backed cleanup and deduplication on 2026-08-20.
The in-memory-only adapter now exhausts all five invalid G1 parents, retains 162 outline
observations and all ordered valid descendants, removes only broken duplicate or
missing-target navigation evidence, and preserves same-titled valid bookmarks on
different pages. All 743 tests and the full gate pass under identity
`exv1-cf068567...442d3`; G1 is resuming from sealed upstream work.
G1 then published all 2,488 pages as `docv1-54e6036f...c9fdef`. Appendix G2's
3,736-page Docling conversion ran for 14,940.61 seconds, reached 13.91 GB peak RSS,
and received `SIGKILL` during a system-wide macOS memory-pressure event before it
could publish a conversion seal. The table stage never began, and the automatic
monolithic retry was stopped near the start. [Task
03H.2](../tasks/sprint2/03h2_build_restartable_chunked_docling_conversion.md) is now
complete and its source-neutral production path has landed. The accepted [chunk-conversion
specification](specs/chunked_docling_conversion_v1.md) retains independently sealed
page evidence, then runs reading order, cross-page text merging, and heading inference
once over canonical whole-document order; finalized range JSON is never concatenated.
The complete G1 proof sealed 12 document-driven ranges, resumed without recomputing a
retained child, reproduced the four stable monolithic outputs byte for byte, and passed
the isolated downstream pipeline. Measured 7.17 GB range and 8.89 GB aggregate peaks
select one worker because projected two-worker memory exceeds the 10 GiB concurrent
ceiling. The final human-ownership review established named package owners, strict
lineage/recovery checks, and a full-byte audit of immutable evidence.
No Gate D or G2 rehearsal will run. Task 03H was then active with its source-free plan
prepared to restart all 35 sources from scratch under the isolated
`pipelines/brisbane_baylands/task_03h_clean_full_v2/` namespace. Earlier v1 and
historical artifacts remain preserved evidence but are ineligible for reuse. The new
production identity is
`exv1-035d99c459c7cc6d2eb7ac3977ead85ca799e425318de282953bbf49963a95e3`.
The new chat completed source-free verification and repaired the readiness owner's
stale v1 completion scan before staging only the v2 catalog and readiness record. The
exact source order, chunk selections, resource forecast, and restart behavior are now
prepared; separate user authorization is still required before the fresh `deir_main`
PDF/model run. The user subsequently authorized that checkpoint. All ten main-report
ranges sealed within resource bounds, but aggregate publication failed because the
fresh v2 `docling_conversions` parent did not exist. The automatic retry reused every
range and failed identically without new Docling/model calls. Task 03H was paused at
this main-report hard stop; Appendix A has not started.
The user authorized the aggregate fresh-root repair. The parent-safe staging fix passed
the full gate; the resumed run reused all ten ranges without Docling calls, sealed the
aggregate, and published the derived producer. Record mapping then stopped because the
aggregate's 274 valid figure files are recorded relative to the document root while
the downstream contract resolves them from the conversion root. Task 03H was paused at
this second main-report hard stop; Appendix A has not started.
The user authorized the aggregate asset-path repair. The producer now emits the
conversion-root-relative path required by record mapping, with a shared integration
regression. Full offline validation passed; main then reused all ten ranges with zero
Docling calls, published end to end, and returned the exact same completion on its
mandatory 0.88-second reuse invocation. Appendices A through F2 also published
serially, producing eight ordered v2 terminal documents. Appendix G1 sealed all twelve
fresh ranges, but aggregate publication exceeded the fixed 10 GiB RSS limit twice at
10,778,853,376 and 10,768,334,848 bytes. The second attempt ran only the aggregate
worker and reused every range seal. The user then authorized a corpus-wide increase
of the generated aggregate RSS limit from 10 GiB to 16 GiB; configs and production
identity were regenerated, and the sealed range evidence remains eligible for reuse.
G1 then completed as the ninth ordered v2 document under the regenerated identity,
with all downstream stages passing. G2 began fresh conversion, but its first range
exceeded the former 8 GiB range RSS limit twice at 8,596,865,024 and 8,590,131,200
bytes. No G2 range seal or later stage exists. The user then authorized a corpus-wide
increase of the range RSS limit to 16 GiB, matching the aggregate limit; regenerated
configs and identity now carry both 16 GiB guards, and collection work has not started.
G2 was then retried twice under that policy; both attempts stayed below the RSS cap but
the second reached 541,917,184 bytes of swap growth against the unchanged 512 MiB
safety guard. No G2 range seal exists. The host then reported only 514.44 MiB of free
swap. The user then authorized a corpus-wide increase of the swap-growth guard to
1 GiB; configs and identity were regenerated before retrying G2. Neither retry hit
that swap guard, but both exceeded the unchanged 16 GiB range RSS cap at 17,213,833,216
and 17,204,510,720 bytes. No G2 range seal exists; a separate range-RSS increase is
now required.
On 2026-08-21, Task 03H.2 was confirmed closed and a distinct v3 clean-run namespace
was prepared source-free. Its 35 documents are ordered shortest-to-longest by
physical page count, with source ID as the tie-breaker. The v3 root was verified
absent, the v3 catalog/specifications/identity were generated, and explicit approval
is still required before the first PDF/model command.
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
- `docs/task04_maintainer_runbook.md`: Task 04 build, local serving, finding
  edits, source-free validation, retry, and transaction-recovery procedures.
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
