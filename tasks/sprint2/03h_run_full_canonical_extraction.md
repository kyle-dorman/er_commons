# Task 03H: Publish and Validate the Full Document Collection

Status: **provisional; execution shape revised by user direction on
2026-08-05**. Tasks 03G.1, 03G.2, all observed-failure remediation, and the
[Task 03G.3](03g3_align_pipeline_responsibilities_and_names.md) architecture
and naming refactor are accepted and closed. This contract uses the accepted
Task 03G.3 responsibility graph and vocabulary but remains inactive. The Task
03G umbrella must receive separate closure and Task 03H must receive separate
user activation; before activation, also confirm that the independently sealed
content-parsing restart boundary below is implemented and validated.

## Abstract

Run the frozen document and collection workflow across all 35 checksum-pinned
model-collection PDFs without treating document parsing as one restart boundary. For
each required source/configuration pair, publish the expensive Docling
conversion as independently sealed immutable evidence before routing, table
reconstruction, record mapping, or later processes consume it. Prove that boundary
on a small, diverse full-document wave before scheduling the remaining corpus;
afterward, pipeline work as capacity allows while retaining the stage seals.

Publish immutable per-document candidates, seal the collection
target/alias index, publish cross-document resolution records, and account
explicitly for every source and terminal state. Produce a candidate handoff and
machine integrity evidence for Task 04. Task 04 independently decides
usability and freezes the accepted extraction release; Task 03H does not
silently represent a failed source as a successful extraction.

## Goal

Produce a reproducible, internally consistent candidate corpus whose successes,
failures, lineage, hierarchy, labels, aliases, and cross-references can be
independently validated before benchmark use.

## Inputs

- user-approved Task 03G umbrella outcome and strict Task 03G.3 v2 configuration,
  identity, and capacity settings
- the sealed Task 02 manifest filtered to its 35 ordered, checksum-pinned
  `model_corpus` records
- responsibility-oriented packages and commands accepted in Task 03G.3, plus the
  behavioral contracts accepted in Tasks 03C.1 and 03D.1, the
  Task 03E.2d correction acceptance, and Tasks 03E.3–03F
- accepted pilot evidence and `/Volumes/x10pro/er_commons` capacity
- measured Task 03G conversion and downstream timings sufficient to forecast
  the first full-corpus execution window

## Outputs

- one immutable, completion-last Docling conversion bundle for every required
  successful source/configuration pair, including source checksum, conversion
  configuration, model/package/runtime identity, managed-file inventory,
  checksums, warnings, and an explicit success seal
- derived routing and table evidence that names its exact sealed Docling input
  and can be rebuilt without rerunning conversion when that input remains valid
- immutable parser evidence, canonical records, inferred hierarchy,
  printed-label evidence and resolutions, aliases, reference mentions,
  within-document resolutions, content assets, and mappings for every
  successful stage-one document
- one explicit terminal success or failure record for every required source
- a sealed target/alias index over terminal stage-one results
- immutable cross-document-resolution records, including explicit unresolved
  reasons for unavailable or ambiguous targets
- separate target-index, resolution, all-source-accounting, and candidate-
  handoff completion records
- collection manifest, machine report, checksums, warnings, configuration, and
  software/model/runtime identities
- producer-side completeness, schema, referential-integrity, coordinate,
  asset, stage-immutability, and rerun reports
- page-, table-, table-family-, hierarchy-, label-, alias-, mention-, and
  resolution-level machine observations for Task 04, with no human-review
  fields
- an exact Task 04 input path and review-cache recipe

Page renders are not canonical outputs. Generate only the predeclared Task 04
review sample as regenerable cache, outside extraction identity and
completeness.

## Research / learning checkpoint

The outcome must explain:

- **A zero exit code is not a release proof.** Source accounting, artifact
  integrity, schema validity, referential integrity, stage immutability,
  rerun checks, and warning visibility are separate layers.
- **Accounting is not success.** Every source can have a terminal record even
  when policy blocks candidate handoff or later acceptance.
- **Machine handoff is not Task 04 freeze.** Task 03H reports exactly what was
  produced; Task 04 determines what is usable for the benchmark.
- **The corpus pass cannot rewrite documents.** Cross-document resolutions are
  new records over a sealed target index.
- **Extraction recall bounds retrieval recall.** Later analysis must distinguish
  absent/unusable evidence from ranking and synthesis failures.
- **Extraction changes invalidate anchors.** A new parser, hierarchy,
  configuration, schema, or resolution policy creates a new identity and
  requires explicit benchmark migration.
- **Warnings and failures are release data.** Parser anomalies, source
  exceptions, partial outcomes, and unresolved references must remain
  queryable.
- **Expensive inference and deterministic interpretation have different
  restart boundaries.** A routing, table, canonical, hierarchy, resolution, or
  reporting correction must not rerun valid Docling conversion merely because
  the old parsing lifecycle sealed them together. Only a source-byte,
  Docling/model/configuration, conversion-adapter, or conversion-contract
  change can invalidate the corresponding conversion bundle.
- **An overnight target requires an honest forecast.** Pilot timings, source
  pages, model multiplicity, concurrency, memory, free space, and downstream
  throughput must support the intended window before launch. Missing the
  forecast is reported as operational variance; it is never hidden by calling
  incomplete work successful.

## Plan / spec requirement

Write a short run plan immediately before execution. Confirm:

1. all source, corpus, parser, model, configuration, schema, hierarchy, and
   resolution identities;
2. a preparation phase that implements and offline-validates the split
   conversion identity, raw seal, derived-stage consumer, and no-converter
   reuse path before any Task 03H PDF allocation;
3. that Docling conversion has its own content-bound identity, managed-file
   inventory, completion-last publication, checksum-verifiable reuse path, and
   consumer validation independent of routing/table policy identity;
4. exact commands, bounded concurrency, memory/disk limits, interruption
   behavior, and retry settings;
5. a conservative wall-clock and capacity forecast from Task 03G evidence for
   the intended first execution window: launch during the evening of
   2026-08-05 and target terminal all-source accounting by the morning of
   2026-08-06. If that target is not credible, report the estimate and revised
   schedule before allocating the corpus run;
6. a first wave of four to six diverse small or medium documents that runs
   through the complete document pipeline. Select the exact sources in the run
   plan from page count, layout/table regime, rotation, and learned-fallback
   evidence; do not select only easy controls;
7. that the first wave passes conversion sealing, derived producer stages, all
   document processes, and reuse verification before the remaining conversions
   are scheduled;
8. after the first wave passes, a work queue that may convert the remaining
   documents and start later stages as each conversion seal becomes available,
   without waiting for all 35 conversions or weakening resource limits;
9. stage-specific invalidation and restart behavior:
   - record-mapping or later-process changes reuse sealed Docling and derived parsing
     evidence when their identities still verify;
   - routing or table changes reuse sealed Docling evidence and rebuild the
     affected derived parsing and downstream stages;
   - source bytes, Docling/model/configuration, conversion-adapter, or
     conversion-contract changes invalidate only the affected conversion
     identity and require an explicit scope decision before rerun;
   - an operational retry or resource-setting change that leaves all
     output-affecting inputs unchanged resumes or checksum-reuses the existing
     identity rather than inventing a new semantic version;
   - a source-specific failure retries only that source, while a shared-stage
     change invalidates only that stage and its descendants;
10. stage-one monitoring, interruption, atomic publication, terminal-state,
   and all-source-accounting requirements;
11. target-index sealing and second-pass no-mutation checks;
12. candidate-handoff policy for failures, including the hard stop for a
   material main-report failure;
13. fixed-subset rerun checks;
14. Task 04 machine-record and review-cache handoff; and
15. retention and isolation of failed or rejected versions.

If the maintained runtime cannot seal and reuse Docling conversion separately
from routing and tables, that is a pre-execution implementation blocker. Do
not compensate by launching a monolithic 35-document parsing run.

Do not change accepted parser, Task 03E.2d hierarchy, schema, or resolution
policy during the run. A material new failure mode stops the candidate for an
explicit Task 03G or owning earlier-task revision.

## Review pass

- **Source accounting:** all and only the 35 model-corpus sources have terminal
  records.
- **Candidate integrity:** every published artifact is checksummed, contained,
  referenced, and covered by the appropriate completion record.
- **Restart isolation:** downstream identities reference exact Docling seals,
  and invalidation tests prove which stage must rebuild for each change class.
- **Stage isolation:** target-index and cross-document passes preserve
  stage-one bytes.
- **Structural consistency:** IDs, hierarchy, labels, aliases, references,
  coordinates, assets, and mappings satisfy the frozen contracts.
- **Warning visibility:** no failure, warning, anomaly, or source exception is
  erased by aggregation.
- **Independent freeze:** the candidate does not claim Task 04 acceptance.

## Validation

- Reconcile inputs against all 35 ordered manifest records and checksums.
- Validate every Docling conversion bundle independently before a derived
  producer consumes it; reject missing, partial, stale, or checksum-mismatched
  conversion evidence.
- Reconcile expected pages for every successful extraction; preserve explicit
  failure coverage rather than fabricating page success for failed sources.
- Validate every artifact role, schema, checksum, contained path, and identity.
- Validate global ID uniqueness and all document, page, block, section, table,
  table-family, figure, image, asset, mapping, alias, mention, and resolution
  relationships.
- Validate bounding boxes against page dimensions and coordinate frames.
- Validate every referenced content asset.
- Verify the target index contains exactly the eligible terminal stage-one
  outputs.
- Verify cross-document resolution leaves stage-one checksums unchanged.
- Recompute aggregate counts instead of trusting separately maintained totals.
- Reinvoke the accepted Task 03G.2 pilot subset under the Task 03H contract and
  verify the exact reuse or rebuild behavior frozen after Task 03G.
- Exercise the invalidation matrix without rerunning PDFs: a downstream-only
  identity change must reuse sealed Docling evidence, a routing/table identity
  change must rebuild from it, and a conversion-owned change must refuse reuse.
- Interrupt a bounded fixture workflow and verify it resumes from the first
  missing or incomplete source while preserving earlier valid seals.
- Require the checksum-reuse invocation to make zero Docling calls for every
  verified raw conversion candidate and zero model calls for every other
  verified reusable model-owned artifact.
- Compare observed wave and full-run timings against the preflight forecast and
  report the critical path, idle time, retries, and completion variance.
- Verify human-review fields are absent and all Task 02 warnings propagate,
  including K2's `source_edition_override`.
- Verify requested review renders are reproducible cache and excluded from
  completeness.
- Verify Git contains no bulk source or generated extraction artifacts.
- Run:

```bash
make check
git diff --check
```

## Acceptance criteria

- All 35 sources have explicit terminal records under one corpus identity.
- Every successful document has a verified immutable stage-one candidate;
  failures remain failures with deterministic reasons.
- Every successful required Docling conversion has its own verified immutable
  completion, and routing/table or downstream remediation can reuse it without
  model execution when conversion-owned inputs are unchanged.
- The diverse first wave completes end to end before remaining corpus
  conversion is scheduled.
- No completed main-document raw conversion runs twice under the same frozen
  raw-conversion identity.
- A material native-extraction failure in the main report blocks candidate
  handoff and requires a new decision.
- The target index and cross-document resolution are complete under the frozen
  policy and do not mutate document candidates.
- All-source accounting, candidate handoff, and the later Task 04 freeze are
  represented by distinct records.
- Schemas, IDs, coordinates, checksums, assets, references, and fixed-subset
  rerun checks pass for published candidates.
- Task 04 receives complete machine observations and source-failure records
  without prefilled human dispositions.
- Page renders are absent from canonical completeness claims.
- Generated bulk artifacts remain outside Git.
- The outcome reports exact success/failure counts, pages, bytes, timings,
  warnings, unresolved references, validation commands, forecast variance,
  and Task 04 input.
- For the first execution window, “done by morning” means a complete validated
  candidate and handoff, not merely finished Docling conversions. Elapsed time
  is an operational target rather than a corpus-validity acceptance criterion;
  if only an earlier phase fits the window, the run plan must say so before
  launch.
- The candidate is not called accepted or frozen until Task 04 independently
  validates it.

## Non-goals

- assigning final usability or document dispositions
- reviewing every page or table semantically
- OCR, LLM repair, or visual-question answering
- extracting Final EIR Volume 4 comments and responses
- case screening, evidence authoring, retrieval, generation, or scoring
- changing parser, hierarchy, schema, or resolution policy during the run
