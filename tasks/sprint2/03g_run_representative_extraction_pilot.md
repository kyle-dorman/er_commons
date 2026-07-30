# Task 03G: Run the Representative Two-Stage Extraction Pilot

Status: **provisional**. Revise this contract from the accepted Task 03F
outcome before activating it.

## Abstract

Run the complete two-stage extraction workflow on a predeclared,
heterogeneous subset of full Brisbane Draft EIR documents. Measure structural
failure modes, runtime, memory, storage, restart behavior, and semantic
reproducibility. Inspect hierarchy, printed labels, aliases, reference
mentions, within- and cross-document resolutions, tables, assets, and requested
review cache. Rehearse Task 04's human-usability review in a provisional
namespace. This is the final configuration and workload gate before Task 03H.

## Goal

Demonstrate that the accepted Docling-backed hierarchy and complete corpus
workflow remain task-sufficient across representative document regimes, and
that systematic failures return to their owning task rather than accumulating
document-specific patches.

## Inputs

- accepted Tasks 03A–03F
- the frozen corpus extraction identity and two-stage batch command
- the sealed model-corpus source manifest
- a reviewed pilot selection spanning structurally distinct reports and
  appendices, including a very large document and known source warnings
- Task 03A parser observations, including known heading false-positive and
  false-negative controls
- the accepted Task 03E hierarchy rubric and Task 03E.1 semantic-structure
  contract

## Outputs

- a frozen full-document pilot specification selected before execution
- completed external stage-one artifacts for every pilot source or explicit
  terminal failure records
- a sealed pilot target/alias index and immutable cross-document resolutions
- per-stage runtime, peak-resource, and artifact-size observations
- structural distributions and a failure taxonomy with preserved examples
- a mini Task 04 review protocol and predeclared sample combining ordinary,
  structural-stress, and anomaly-triggered pages
- provisional pilot-only page, table, document, hierarchy, label, alias, and
  cross-reference observations
- repeated-run semantic and identity results from a fixed subset
- tested interruption, resume, failure-accounting, and unresolved-reference
  behavior
- a reviewed production configuration and Task 04 review method, or a
  documented stop requiring revision of the owning earlier task
- a capacity estimate and safe Task 03H settings

## Research / learning checkpoint

Design the pilot as an experiment with predeclared observables and stop rules.
The sample must cover, where available:

- the main Draft EIR report;
- a typical narrative appendix;
- a table- or figure-heavy appendix;
- a very large appendix and a document with Task 02 warnings;
- Appendix K2 part 2 with `source_edition_override`;
- documents with and without PDF outlines and visible tables of contents;
- numbered and unnumbered headings;
- embedded numbering or printed-page-label resets;
- explicit PDF page-label metadata, if any, and absent-metadata or
  visible-label-only regimes; and
- a regime Task 03A identified as materially different.

The outcome must explain:

- **Appendix P acceptance is necessary, not corpus-wide proof.** The accepted
  Task 03E result is a hypothesis to test against heterogeneous structure.
- **Hierarchy and label failures have mechanisms.** Measure heading
  promotions/misses, incorrect nesting, table-of-contents rows promoted as
  starts, furniture promoted as body sections, label conflicts, and alias
  collisions separately.
- **Cross-reference quality has two stages.** Report mention detection,
  within-document resolution, cross-document resolution, ambiguity, and
  unresolved reason codes independently.
- **Parser-intrinsic correctness, task-conditioned sufficiency, and corpus
  coverage are distinct.**
- **Silent structural failure matters more than loud failure.** Plausible
  hierarchy or labels can still misroute retrieval and citations.
- **Reproducibility is empirical.** Repeat a fixed subset and compare semantic
  records, IDs, geometry, assets, indexes, and resolution outputs.
- **Review cache is not candidate completeness.** Page renders exist only for
  selected human review and are regenerable.
- **Pilot labels and Task 04 decisions have different authority.** Pilot review
  tests the workflow but cannot prefill the accepted usability registry.

## Plan / spec requirement

Before running the pilot, freeze:

1. selected documents and structural-regime rationale;
2. stage-one, target-index, and second-pass observables;
3. repeated-run subset and equality criteria;
4. hierarchy, label, alias, and cross-reference anomaly rules;
5. the mini Task 04 sample and requested render-cache recipe;
6. review dimensions, reason codes, escalation rules, and timing measures;
7. a simulated source failure and expected accounting/resolution behavior;
8. runtime, memory, storage, review-burden, and failure stop thresholds;
9. permitted configuration changes and required reruns;
10. the evidence needed to freeze Task 03H settings; and
11. retention rules for rejected extraction versions and disposable cache.

Systematic hierarchy failure returns to Task 03E, contract failure to Task
03E.1, materialization failure to Task 03E.2, reference-policy failure to Task
03E.3, and batch-state failure to Task 03F. Do not add pilot-local heuristics
that bypass the owning contract.

## Review pass

- **Sample adequacy:** the pilot spans structural mechanisms, not only convenient
  file sizes.
- **Identity:** all accepted artifacts share the corpus identity and only the
  permitted subordinate transaction identities.
- **Structural quality:** body/furniture roots, hierarchy, labels, aliases, and
  reference outcomes are reviewed by type and downstream consequence.
- **Two-stage integrity:** the target index is sealed from terminal stage-one
  inputs and the second pass leaves them unchanged.
- **Operational credibility:** resource tails and restart evidence support the
  full run.
- **Human-review boundary:** provisional records remain outside Task 04.

## Validation

- Verify every pilot input against the source manifest.
- Run the same two-stage entrypoint intended for Task 03H.
- Validate schemas, references, coordinates, counts, assets, completion
  records, identity, and warning propagation.
- Repeat the fixed subset and compare declared semantic invariants.
- Exercise stop/resume and one simulated document failure.
- Confirm the simulated failure is accounted for and references to its missing
  targets remain explicit and unresolved.
- Review all predeclared hierarchy, label, alias, and cross-reference
  observables plus every algorithmically flagged pilot outlier.
- Generate renders only for the frozen review sample; verify their absence does
  not invalidate the candidate.
- Record review time by ordinary and risk-triggered strata.
- Confirm rejected configurations cannot mix with the accepted identity.
- Run:

```bash
make check
git diff --check
```

## Acceptance criteria

- The pilot exercises the main report, representative appendices,
  long-document behavior, known warnings, and the K2 provenance exception.
- The accepted Docling hierarchy is good enough across the declared document
  regimes under the frozen rubric; otherwise Task 03H does not proceed.
- Visible tables of contents inform aliases/evidence without becoming false
  body-section starts.
- Printed-label regimes and conflicts remain explicit rather than collapsing
  into physical page numbers.
- Cross-document resolution uses the sealed target/alias index, and unresolved
  outcomes carry deterministic reasons.
- Semantic reruns preserve the declared identities and invariants.
- Resource evidence supports explicit Task 03H settings.
- The mini review demonstrates a credible Task 04 process without making
  authoritative dispositions.
- No unbounded or systemic failure remains; any such failure returns to its
  owning task.
- The outcome asks for explicit user approval before Task 03H.

## Non-goals

- converting all 35 model-corpus PDFs
- corpus acceptance or final page usability decisions
- OCR fallback, generative repair, or a custom hierarchy algorithm
- benchmark case selection
- retrieval, target generation, judging, or evaluation
- claiming corpus-wide accuracy from the pilot
