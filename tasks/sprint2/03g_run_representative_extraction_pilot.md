# Task 03G: Run the Representative Production Pilot

Status: **provisional**. Revise this contract from the accepted Task 03F outcome
before activating it.

## Abstract

Run the complete extraction workflow on a predeclared, heterogeneous subset of
full Brisbane Draft EIR documents. Measure structural failure modes, runtime,
memory, output size, restart behavior, and semantic reproducibility; inspect
the resulting raw, canonical, hierarchy, cross-reference, render, and asset
artifacts; and rehearse Task 04's human-usability review on a predeclared page
sample. Use provisional pilot-only review records to freeze or reject the
production configuration and review method. This is the last configuration
gate before the 48,341-page corpus run.

## Goal

Demonstrate that the complete pipeline is operationally credible and
task-sufficient across representative document regimes, and that Task 04 can
review it efficiently under a tested rubric, not merely that conversion
commands complete on small page-range examples.

## Inputs

- completed Tasks 03A–03F
- the frozen candidate extraction contract and batch command
- the sealed model-corpus source manifest
- a reviewed pilot selection covering the main report and structurally distinct
  appendices, including a very large document and known source warnings
- Task 03A page-level observations and error dimensions
- primary evaluation guidance such as
  [READoc](https://aclanthology.org/2025.findings-acl.1128/) and
  [DocLayNet](https://arxiv.org/abs/2206.01062)

## Outputs

- a frozen full-document pilot specification selected before execution
- completed external extraction artifacts for every pilot document
- per-stage runtime, peak-resource, and artifact-size observations
- structural distributions and outlier reports
- an extraction error taxonomy with representative preserved examples
- a mini Task 04 review protocol and predeclared page sample containing
  stratified ordinary pages, structural stress pages, and every pilot anomaly
- provisional pilot-only page observations and document-level review summaries
- semantic reproducibility results from repeated conversion of a fixed subset
- a reviewed production configuration and schema freeze, or a documented stop
  requiring an earlier-task revision
- a reviewed Task 04 sampling, escalation, and disposition procedure, or a
  documented stop if the candidate cannot be reviewed reliably
- a capacity estimate and safe execution settings for Task 03H

## Research / learning checkpoint

Design the pilot as an experiment with predeclared observables and stop rules,
not as an informal demo. Include at least:

- the main Draft EIR report;
- a typical narrative appendix;
- a table- or figure-heavy appendix;
- a document with known Task 02 parser warnings;
- a very large appendix that exercises memory and long-tail runtime;
- Appendix K2 part 2 with `source_edition_override`; and
- any document regime Task 03A identified as materially different.

If that set is operationally too large for one bounded task, preserve the
selection criteria and use document/page strata that still exercise the
long-document path; record the limitation rather than substituting only easy
examples.

The outcome must explain:

- **Parser-intrinsic correctness, task-conditioned sufficiency, and corpus
  coverage are different questions.** A reconstruction can contain local errors
  yet remain sufficient for text-only retrieval, while a visually polished
  conversion can omit the exact table or section needed by a benchmark case.
- **Error taxonomies should follow failure mechanisms.** Separate omission,
  duplication, reading-order corruption, region-label confusion, heading-level
  error, table-topology error, caption/figure misassociation, geometry error,
  cross-reference error, and serialization/provenance loss.
- **Aggregate text similarity is inadequate.** Correct characters in the wrong
  order can break retrieval; correct table text with wrong row/column structure
  can reverse meaning; correct prose without anchors cannot support auditable
  citations.
- **Domain shift is structural.** Environmental reports contain appendices,
  engineering tables, maps, repeated exhibit templates, and numbering regimes
  that may differ from document-layout training corpora.
- **Silent failure matters more than loud failure.** Explicit conversion errors
  are easier to quarantine than plausible-looking but structurally wrong
  outputs.
- **Reproducibility is empirical.** Repeat a fixed subset and compare semantic
  records, IDs, geometry, and assets; do not infer determinism from fixed
  settings.
- **Capacity planning must use distributions.** Report per-document and
  per-page tails, peak memory, and storage by artifact family rather than only a
  mean pages-per-second estimate.
- **Parser QA needs both probability sampling and risk-based sampling.** A
  stratified ordinary-page sample estimates how often routine output is
  acceptable, while anomaly-triggered and structural-stress pages test known
  high-consequence failure modes. Neither sample alone supports both purposes.
- **A review rubric must be consequence-aware.** Text completeness, reading
  order, hierarchy, table topology, figure/caption linkage, and anchor geometry
  have different effects on text-only retrieval and citation verification.
  Review should record the failure mechanism and downstream consequence rather
  than one undifferentiated quality score.
- **Pilot labels and release labels have different authority.** Provisional
  review records test configuration and workflow. They do not become frozen
  page dispositions because Task 03H has not yet produced the complete candidate
  and Task 04 has not independently validated it.
- **Extraction quality bounds later evaluation.** Missing canonical evidence
  caps retrieval recall. Later analysis must distinguish evidence absent from
  the extraction from evidence present but missed by BM25.

## Plan / spec requirement

Before running the pilot, freeze:

1. selected documents and coverage rationale;
2. structural and operational observables;
3. repeated-run subset and equality criteria;
4. automated anomaly rules and their intended interpretation;
5. the mini Task 04 sample, combining a predeclared stratified ordinary-page
   sample with all anomaly-triggered and structural-stress pages;
6. the provisional page-review dimensions, reason codes, and document rollup;
7. review-time observations and escalation rules for excluded-page or
   skipped-document candidates;
8. runtime, memory, storage, review burden, and failure stop thresholds;
9. permitted configuration changes and required reruns;
10. the evidence required to freeze production settings and the Task 04 review
    method; and
11. cleanup or retention rules for rejected extraction versions.

Task 03G performs a mini human-usability review to validate the parser,
configuration, anomaly detection, sampling plan, and review workflow. Store its
decisions in a distinct pilot namespace and mark them non-authoritative. It must
not populate the Task 04 registry, freeze final page exclusions, or assign
release document dispositions.

## Review pass

- **Sample adequacy:** the pilot spans failure mechanisms rather than only
  convenient file sizes.
- **Structural quality:** anomalies are evaluated by type and downstream
  consequence.
- **Operational credibility:** long-tail runtime, memory, storage, and resume
  behavior support a safe full run.
- **Version freeze:** accepted artifacts all share one closed
  source/parser/model/configuration/schema identity.
- **Review-loop quality:** the pilot combines representative and risk-based
  pages, captures review burden, and makes systemic failures visible before the
  full run.
- **Human-review boundary:** pilot review records are explicit and useful but
  cannot masquerade as the frozen Task 04 usability registry.

## Validation

- Verify every pilot input against the source manifest before conversion.
- Run through the same batch entrypoint intended for Task 03H.
- Validate schemas, references, coordinates, counts, assets, completion records,
  and source-warning propagation.
- Repeat the fixed subset and compare version-scoped IDs and semantic outputs.
- Exercise stop/resume during at least one nontrivial conversion if Task 03F did
  not already prove the real path.
- Perform the mini Task 04 review against page renders for the complete
  predeclared ordinary-page sample, every structural stress page, and every
  algorithmically flagged pilot outlier.
- Review every provisional excluded-page or skipped-document candidate in the
  pilot and verify that the reason codes and escalation rules are usable.
- Record review time and estimate the likely Task 04 workload from ordinary and
  anomaly-triggered strata separately.
- Verify pilot decisions are stored outside the final usability registry and
  marked non-authoritative.
- Confirm rejected configurations cannot mix with the accepted version.
- Run:

```bash
make check
git diff --check
```

## Acceptance criteria

- The pilot exercises the main report, representative appendices, long-document
  behavior, known warnings, and the K2 provenance exception.
- Structural and operational results are reported by failure mode and
  distribution, not only aggregate success.
- Semantic rerun behavior is measured and compatible with deterministic
  extraction-scoped anchors.
- Resource evidence supports explicit Task 03H concurrency, timeout, and storage
  settings.
- The mini review demonstrates that ordinary pages and every flagged pilot
  anomaly can be adjudicated using the proposed Task 04 dimensions, reason
  codes, renders, and canonical links.
- No unbounded or systemic failure pattern remains that would make the full
  candidate predictably fail Task 04; otherwise the task returns to the
  responsible earlier subtask before Task 03H.
- Review effort is measured by sample stratum and supports a credible Task 04
  workload estimate.
- All accepted pilot artifacts share one frozen extraction identity.
- Any material configuration or schema change triggers the specified rerun
  rather than being applied only to later documents.
- Pilot review records are explicitly provisional and do not prefill or replace
  Task 04 decisions.
- The outcome asks for explicit user approval before Task 03H.

## Non-goals

- converting all 35 model-corpus PDFs
- final or authoritative page-level usability review
- OCR fallback or generative repair
- benchmark candidate selection
- retrieval, target generation, judging, or LLM evaluation
- claiming corpus-wide parser accuracy from the pilot
