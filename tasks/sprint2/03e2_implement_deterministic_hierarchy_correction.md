# Task 03E.2: Implement and Evaluate Deterministic Hierarchy Correction

Status: **provisional and inactive**. Revise this contract from the accepted
Task 03E.1 outcome and activate it only with explicit user approval.

## Abstract

Implement the accepted deterministic correction contract as a fast,
artifact-producing overlay on the checksum-verified Task 03E Docling candidate.
Extract frozen features, reconcile visible TOC entries with body targets, apply
named correction rules, construct and validate the corrected hierarchy, and
publish a new immutable hierarchy-evidence candidate only after independent
rebuild and preservation gates pass.

Do not rerun or mutate Docling, materialize canonical semantic sections, or use
an LLM, embedding model, VLM, semantic search, or manual document exception in
the runtime path.

## Goal

Determine whether a narrow deterministic overlay repairs the measured Task 03E
failure mechanisms without sacrificing the accepted outline and numbering
behavior, introducing false section boundaries, or changing any unrelated
producer or Task 03D.1 evidence.

## Inputs

- accepted Task 03E.1 contract, schemas, fixtures, rule policy, held-out sample,
  and stop conditions
- checksum-verified Task 03E candidate
  `prv1-92170ee8b5f5d51ffa738749ee872d7c7e9e5e7dbcb16cf6150bcf33d10d68e1`
- Task 03E producer comparison and bounded review evidence
- accepted Task 03C.1 producer and Task 03D.1 canonical reference candidate
- checksum-pinned Appendix P source and bounded main-report control sources
- PDF outline, visible TOCs, conversion-page evidence, reading order, content
  layers, text, geometry, and raw hierarchy observations
- requested disposable review-cache renders

## Outputs

Tracked:

- responsibility-specific modules for feature extraction, TOC parsing and
  reconciliation, correction rules, hierarchy construction, validation,
  comparison, and publication
- a package-backed command and versioned correction-policy configuration
- executable schemas and fixtures accepted in Task 03E.1
- focused unit, invariant, identity, publication, and regression tests
- a compact learning note reporting which deterministic evidence generalized
  and which cases remained ambiguous
- explicit user acceptance or rejection status

External:

- immutable feature, visible-TOC, reconciliation, decision, corrected
  hierarchy, ambiguity, and warning artifacts
- complete rule-application and non-application counts
- exact correspondence from every corrected item to raw producer evidence
- independent comparison against the rejected maintained-default hierarchy and
  the accepted non-hierarchy producer surfaces
- two fresh independent build artifacts or checksummed scratch evidence
- bounded development and held-out review reports and requested review-cache
  renders
- input inventory (the authoritative input manifest), environment, summary,
  metrics, completion-last, and failed-attempt evidence

## Research / learning checkpoint

Before implementation, trace the accepted contract through the actual pinned
producer payloads. Reconfirm that every feature exists with the specified unit
and missing-state behavior. Inspect maintained deterministic utilities for PDF
outline, page-label, and text/layout parsing only where the contract permits
them.

The outcome must explain:

- **Correction is evidence transformation, not generative repair.** Runtime
  outputs come from frozen pure rules over verified artifacts.
- **Visible TOC reconciliation is both evidence and a gate.** It can support a
  unique body target and expose conflicts, but the TOC row itself never becomes
  a body boundary.
- **Raw observations remain queryable.** A consumer can always recover the
  original Docling label, level, position, and provenance.
- **High precision is more important than forced coverage.** Ambiguous
  headings remain explicit rather than being silently promoted or assigned a
  guessed depth.
- **Reproducibility includes non-decisions.** Rule eligibility, rejected
  candidates, warnings, and ambiguity are stable artifacts, not only the final
  section tree.
- **Fast does not mean unmeasured.** Report runtime, memory, and artifact size
  separately from the expensive producer.

## Plan / spec requirement

Before implementation, write a short stage plan naming:

1. module and public command boundaries;
2. verified producer, source, outline, and configuration inputs;
3. candidate identity and artifact paths;
4. feature, TOC, reconciliation, rule, hierarchy, validation, comparison, and
   publication stages;
5. development and held-out execution order that prevents post-review tuning;
6. exact permitted differences and preservation normalization;
7. independent scratch rebuild, atomic publication, checksum reuse, and
   failed-attempt behavior;
8. timing, memory, storage, and logging measurements;
9. requested render-cache generation; and
10. acceptance, rejection, rollback, and stop behavior.

## Review pass

- **Contract fidelity:** implementation adds no feature, threshold, rule, or
  exception absent from Task 03E.1.
- **TOC correctness:** row parsing, depth, page evidence, target matching, and
  conflicts are independently inspectable.
- **Correction quality:** known failures are fixed by general rules and the
  held-out sample introduces no material false boundary or omission.
- **Preservation:** text, reading order, geometry, tables, figures, assets,
  warnings, lineage, and raw hierarchy remain unchanged.
- **Uncertainty:** unsupported cases stay ambiguous without document-specific
  patches.
- **Runtime isolation:** no network, model, LLM, embedding, or human-in-the-loop
  dependency exists in execution.
- **Maintainability:** pure decision logic is independently testable from I/O
  and publication.

## Validation

- Verify all source, producer, model, configuration, inventory, and completion
  checksums before reading inputs.
- Require exact source coverage and stable item correspondence.
- Run the frozen development fixtures first, freeze the selected implementation
  and configuration, then run the held-out review once under the Task 03E.1
  stop rules.
- Require the known main-report bullet false headings not to start semantic
  sections. Preserve the page-2000 unanchored plain-text heading as the frozen,
  non-blocking R06 `content` ambiguity unless it gains an exact outline or TOC
  anchor under the accepted policy.
- Verify exact outline-anchor and numbered-heading results inherited from Task
  03E unless a predeclared correction explains the difference.
- Verify every visible TOC row remains non-boundary content and every parsed
  entry is exact, missing, ambiguous, or conflicting under the frozen
  reconciliation vocabulary.
- Validate roots, levels, cycles, order, parent/children, direct membership,
  body/furniture isolation, rule evidence, and ambiguity.
- Compare every producer and Task 03D.1 artifact surface outside declared
  hierarchy-enrichment outputs.
- Build twice in independent fresh processes and require byte-identical
  candidate-owned artifacts after only frozen measurement normalization.
- Invoke the normal command again and require checksum-verified reuse without
  feature extraction or correction rebuilding.
- Record total and per-stage wall time, peak memory, and artifact bytes.
- Inspect all predeclared development and held-out review pages against
  requested renders.
- Confirm configuration and generated artifacts contain no page-specific,
  literal-heading, LLM, embedding, semantic-retrieval, or manual-exception
  production behavior.
- Run:

```bash
make fix
make check
git diff --check
```

## Acceptance criteria

- Every Task 03E.1 invariant and good-enough threshold passes.
- The known failure mechanisms are repaired or represented exactly as the
  frozen ambiguity policy allows.
- No visible TOC row, list item, table title, caption, footnote, or furniture
  item becomes a false body section.
- Held-out quality passes without post-review rule or threshold changes.
- Every correction and ambiguity is reproducible, provenance-backed, and
  attributable to one versioned rule.
- All undeclared producer and canonical-reference semantics remain unchanged.
- Independent builds and checksum reuse pass.
- Runtime uses only deterministic local code over verified inputs and remains
  small relative to document production.
- The outcome requests explicit user acceptance before Task 03E.3 activates.

## Non-goals

- rerunning, tuning, or mutating Docling
- canonical semantic-section, page-label, or alias materialization
- cross-reference mention extraction or resolution
- processing a second complete document or starting corpus batching
- retrieval chunks, embeddings, LLMs, VLMs, semantic search, or human review
  state in runtime outputs
- page-specific, title-specific, or literal-heading production exceptions
