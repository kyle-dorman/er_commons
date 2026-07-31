# Task 03E.2: Implement and Evaluate Deterministic Hierarchy Correction

Status: **closed on 2026-07-31 as the completed, rejected MVP/reference
implementation; superseded for production ownership by Task 03E.2b**. The
contract was activated 2026-07-30 after review of the completed Task 03E.1
contract and validator.

## Abstract

Implement the accepted deterministic correction contract as a fast,
artifact-producing overlay on the checksum-verified Task 03E Docling candidate.
Extract frozen features, reconcile visible TOC entries with body targets, apply
named correction rules, construct and validate the corrected hierarchy, and
publish a new immutable hierarchy-evidence candidate only after independent
rebuild and preservation gates pass.

Treat the Task 03E.1 specification, schemas, fixtures, rule vocabulary,
cross-record validator, and held-out protocol as frozen implementation inputs.
Extend the existing human-oriented `hierarchy_correction` package with the
producer and application shell; do not replace the accepted validator or
invent a parallel contract.

Do not rerun or mutate Docling, materialize canonical semantic sections, or use
an LLM, embedding model, VLM, semantic search, or manual document exception in
the runtime path.

## Goal

Determine whether a narrow deterministic overlay repairs the measured Task 03E
failure mechanisms without sacrificing the accepted outline and numbering
behavior, introducing false section boundaries, or changing any unrelated
producer or Task 03D.1 evidence.

## Inputs

Frozen tracked contract inputs:

- accepted Task 03E.1 contract,
  [`hierarchy_correction_v1.md`](../../docs/specs/hierarchy_correction_v1.md),
  and [Decision 003](../../docs/decisions/003_deterministic_hierarchy_correction.md)
- accepted
  [`records.schema.json`](../../benchmarks/er_bench/schemas/hierarchy_correction/v1/records.schema.json),
  [`review.schema.json`](../../benchmarks/er_bench/schemas/hierarchy_correction/v1/review.schema.json),
  development cases, fixture manifest, held-out manifest, valid bundle, and
  invalid mutations under the tracked
  [`hierarchy_correction/v1`](../../benchmarks/er_bench/fixtures/hierarchy_correction/v1/)
- accepted human-oriented cross-record validator and held-out comparator in
  [`src/er_commons/hierarchy_correction`](../../src/er_commons/hierarchy_correction)

Candidate-producing external inputs:

- checksum-verified Task 03E candidate
  `prv1-92170ee8b5f5d51ffa738749ee872d7c7e9e5e7dbcb16cf6150bcf33d10d68e1`
- its producer completion and inventory plus the checksum-pinned source PDF
- PDF outline and page-label observations plus the candidate's visible TOCs,
  conversion-page evidence, reading order, content layers, text, geometry, and
  raw hierarchy observations

Evaluation and comparison inputs, which never enter the candidate input
inventory:

- Task 03E producer comparison and bounded review evidence
- accepted Task 03C.1 producer and Task 03D.1 canonical reference candidate
- bounded main-report control sources
- tracked development cases and held-out manifest
- requested disposable review-cache renders

## Outputs

Tracked:

- responsibility-specific producer modules for verified inputs, feature
  extraction, outline and page-label observations, visible-TOC parsing and
  reconciliation, numbering regimes, rule application, hierarchy construction,
  comparison, measurement, and publication
- a thin application shell and public package facade that reuse the accepted
  Task 03E.1 schema and cross-record validation owners
- package-backed `hierarchy correct-document` command and checked-in
  `configs/brisbane_baylands_2025_deir_task03e2_hierarchy_correction_v1.json`
- unchanged reuse of the executable schemas, fixture manifests, and rule policy
  accepted in Task 03E.1; a discovered contradiction stops the task for a
  contract decision rather than being repaired inside implementation
- focused unit, invariant, identity, publication, and regression tests
- a compact learning note reporting which deterministic evidence generalized
  and which cases remained ambiguous
- explicit user acceptance or rejection status

External:

- an immutable candidate with the exact v1 layout:

```text
pipelines/brisbane_baylands/task_03e2_hierarchy_correction/<candidate_id>/
  records/identity.json
  records/input_inventory.json
  records/environment.json
  records/completion_record.json
  artifacts/item_features.jsonl
  artifacts/visible_toc_entries.jsonl
  artifacts/toc_reconciliation.jsonl
  artifacts/regimes.jsonl
  artifacts/decisions.jsonl
  artifacts/hierarchy.json
  artifacts/ambiguities.jsonl
  artifacts/warnings.jsonl
  records/summary.json
  records/metrics.json
  records/artifact_inventory.json
```

- complete rule-application and non-application counts
- exact correspondence from every corrected item to raw producer evidence
- independent comparison against the rejected maintained-default hierarchy and
  the accepted non-hierarchy producer surfaces
- two fresh independent build artifacts or checksummed scratch evidence
- bounded development and held-out review reports and requested review-cache
  renders under the separate Task 03E.2 review root
- input inventory (the authoritative manifest for verified external correction
  inputs), identity, environment, summary, metrics, completion-last, and
  failed-attempt evidence

## Research / learning checkpoint

Before implementation, trace the accepted contract through the actual pinned
producer payloads. Reconfirm that every frozen feature exists with the
specified unit and missing-state behavior. Use the already installed PDF and
Docling stack only where the contract assigns it a deterministic parsing role.
Do not add or reinterpret a feature, threshold, rule, package-policy choice, or
missing-state behavior.

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

## Activated implementation plan

The requested user check-in is complete. Proceed in this order:

1. Add the typed correction configuration, verified-input loader, identity
   builder, and `hierarchy correct-document` facade. Resolve the Task 03E
   producer and source through their sealed records; do not accept arbitrary
   unmanifested semantic inputs.
2. Implement pure feature, outline/page-label, visible-TOC, reconciliation,
   regime, rule-decision, and hierarchy builders against the frozen v1
   contracts. Validate each stage with the accepted schemas and human-oriented
   cross-record validator.
3. Run the eight tracked development cases and complete development review.
   Freeze code, configuration, policy, and schema digests before exposing any
   corrected held-out output.
4. Generate only the predeclared source-only held-out renders in the disposable
   review cache with `hierarchy prepare-heldout`: pinned pypdfium2 scale 2.0
   (144 DPI), RGB PNG without alpha, exact manifest page order, and names
   `source-p{physical_page:05d}.png`. Keep the adjacent render manifest and
   complete the generated key-complete annotation template. Run `hierarchy
   seal-heldout` to schema- and cross-validate source, identity, page order,
   recomputed producer keys, and render hashes, then write the no-clobber
   annotation bundle and compact checksum seal. Stop before showing or
   generating any corrected held-out output.
5. After sealing the annotations, run the overlay once for complete Appendix P
   plus the fixed main-report controls, then evaluate the held-out pages from
   that complete candidate without tuning. Persist every applied demotion,
   transfer, TOC promotion, and numbering change in the review inventory;
   preserve the page-2000 R06 ambiguity as accepted non-blocking evidence.
6. Reverify all producer bytes, compare every undeclared producer and Task
   03D.1 surface, build twice in independent fresh processes, run the completed
   candidate again to prove checksum reuse, and collect three fresh timing
   measurements.
7. Publish atomically only after schema, cross-record, preservation,
   repeatability, held-out, and resource gates pass. Preserve failed attempts
   without a completion record; do not overwrite or roll back an immutable
   candidate.

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

- Verify the source and producer completion/inventory checksums, including the
  producer-sealed model evidence, and verify every correction identity digest
  before reading semantic inputs.
- Require exact source coverage and stable item correspondence.
- Run the frozen development fixtures first, freeze the selected implementation
  and configuration, seal source-only held-out annotations, then run the
  complete overlay once and evaluate its held-out pages under the Task 03E.1
  stop rules.
- Require all eight development cases to match their expected corrected role,
  level, rule, and outcome; preserve all 29 exact outline anchors and 21
  reviewed numbering relations.
- Create and checksum-seal complete source-only held-out annotations before
  corrected held-out output is shown; bind the evaluation to that checksum and
  prohibit post-review tuning.
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
- Record total and per-stage wall time, peak memory, and exact artifact bytes
  across all 15 persisted final candidate files.
- Inspect all predeclared development and held-out review pages against
  requested renders.
- Require zero held-out false boundaries, false demotions, missed boundaries,
  wrong levels or parents, and regime errors. A source-ambiguous annotation is
  inconclusive rather than a pass.
- Require the review inventory to include every applied demotion, level
  transfer, TOC promotion, and numbering change across Appendix P and the fixed
  main-report controls.
- Require median fresh overlay wall time across three runs to be less than the
  frozen producer build wall time and persisted overlay bytes to be less than
  inventoried producer bytes. Report peak RSS without inventing a gate.
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

- All eight development cases, all 29 exact outline anchors, and all 21 reviewed
  numbering relations pass exactly.
- The known failure mechanisms are repaired or represented exactly as the
  frozen ambiguity policy allows.
- No visible TOC row, list item, table title, caption, footnote, or furniture
  item becomes a false body section.
- Every frozen held-out error count is zero without post-review rule or
  threshold changes; source ambiguity makes the result inconclusive.
- Every correction and ambiguity is reproducible, provenance-backed, and
  attributable to one versioned rule.
- All undeclared producer and canonical-reference semantics remain unchanged.
- Independent builds and checksum reuse pass.
- Runtime uses only deterministic local code over verified inputs and remains
  small relative to document production under both frozen comparable gates.
- The outcome requests explicit user acceptance before Task 03E.3 activates.

## Non-goals

- rerunning, tuning, or mutating Docling
- canonical semantic-section, page-label, or alias materialization
- cross-reference mention extraction or resolution
- processing a second complete document or starting corpus batching
- retrieval chunks, embeddings, LLMs, VLMs, semantic search, or human review
  state in runtime outputs
- page-specific, title-specific, or literal-heading production exceptions

## Activation note

The user authorized contract revision and activation on 2026-07-30 after Task
03E.1 completed its specification, executable schemas, fixtures, held-out
protocol, reference-equivalence gate, and maintainability review. The accepted
page-2000 R06 `content` ambiguity remains non-blocking and is not a reason to
add font extraction or a document-specific rule. No implementation, external
candidate generation, held-out annotation, or correction run occurred during
activation.

## Outcome

The deterministic overlay, CLI, source-only held-out workflow, candidate
identity, atomic publication, comparison reports, and focused tests were
implemented. The final evaluated identity was
`hcorv1-97ffded53a26803052be6a6b6451d2f38587a604923c41b6f2402185105c2c1a`.
Its 281 source-only annotations cover the eight frozen pages, contain six
expected boundaries and zero source ambiguities, and are sealed by annotation
bundle SHA-256
`9f355e356764665f7a6b7beda66f4794ef9a8fb917d2b0bbc8efea07467fdf13`.

The candidate did not publish and has no completion record because two required
quality reports rejected it:

- development fixtures passed 4 of 8. The local-transfer case produced level 4
  instead of expected level 3. The Article reset and two decimal cases produced
  the expected levels but selected exact-TOC rule R04 instead of expected
  numbering rule R05;
- held-out evaluation found two false table boundaries and four wrong
  level/parent results. It found zero false demotions, missed boundaries,
  regime errors, or source ambiguities;
- all 29 exact outline anchors, all 21 reviewed numbering relations, all three
  main controls, producer and Task 03D.1 preservation, three-build semantic
  repeatability, and both resource comparisons passed. Median overlay time was
  4.27 seconds, exact candidate size was 13,556,053 bytes, wall-time ratio was
  0.0686, and artifact-size ratio was 0.035995;
- the visible-TOC parser produced and exactly reconciled 140 rows. The failed
  candidate retained 6,931 item decisions, 17 explicit ambiguities, and 147
  warnings for review.

The complete report manifest is external under
`pipelines/brisbane_baylands/task_03e2_hierarchy_review/<candidate_id>/reports/`
and has terminal status `reject`. The failed candidate workspace is preserved
under `pipelines/brisbane_baylands/task_03e2_hierarchy_correction/attempts/`.
No post-review hierarchy tuning or rerun was performed after reading the
held-out result, and Task 03E.3 remains inactive.

Implementation exposed three pre-evaluation integration defects that were
repaired without changing source judgments: a one-byte self-referential metric
serialization cycle, a validator that excluded raw-text split TOC headings
accepted by its builder, and a validator missing R07's explicit ambiguity
branch. The MVP quality-pass assembler surfaced rejecting reports as a Pydantic
error after persisting the correct terminal `reject` manifest. Task 03E.2b
replaced that path with an explicit typed quality rejection before this lineage
closed.

The learning result is that exact outline, numbering-depth, preservation, and
repeatability evidence generalized, but precedence and parent assignment did
not. Exact TOC evidence currently outranks the expected numbering-rule
attribution in three development cases, local level transfer disagrees with its
fixture, and raw Docling `section_header` false positives survive on held-out
table pages. Under the frozen protocol these are a rejected policy outcome,
not permission for document-specific exceptions.

The subsequently authorized [Task 03E.2a](03e2a_fix_nested_regime_exit.md)
fixed the one material Appendix E defect with a general nested-regime exit
reset. That follow-up does not rewrite this task's sealed annotations or
historical rejection.
