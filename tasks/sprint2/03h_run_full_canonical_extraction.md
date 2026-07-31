# Task 03H: Run and Validate the Full Canonical Extraction

Status: **provisional**. Revise this contract from the accepted Task 03G
outcome before activating it.

## Abstract

Run the frozen two-stage workflow across all 35 checksum-pinned model-corpus
PDFs. Publish immutable per-document stage-one candidates, seal the corpus
target/alias index, publish cross-document resolution records, and account
explicitly for every source and terminal state. Produce a candidate handoff and
producer-side integrity evidence for Task 04. Task 04 independently decides
usability and freezes the accepted extraction release; Task 03H does not
silently represent a failed source as a successful extraction.

## Goal

Produce a reproducible, internally consistent candidate corpus whose successes,
failures, lineage, hierarchy, labels, aliases, and cross-references can be
independently validated before benchmark use.

## Inputs

- user-approved Task 03G configuration, corpus identity, and capacity settings
- the sealed Task 02 manifest filtered to its 35 ordered, checksum-pinned
  `model_corpus` records
- production commands and contracts accepted in Tasks 03C.1 and 03D.1, the
  Task 03E.2d correction acceptance, and Tasks 03E.3–03F
- accepted pilot evidence and `/Volumes/x10pro/er_commons` capacity

## Outputs

- immutable raw producer output, canonical records, semantic hierarchy,
  printed-label evidence and resolutions, aliases, reference mentions,
  within-document resolutions, content assets, and mappings for every
  successful stage-one document
- one explicit terminal success or failure record for every required source
- a sealed target/alias index over terminal stage-one results
- immutable cross-document-resolution records, including explicit unresolved
  reasons for unavailable or ambiguous targets
- separate target-index, resolution, all-source-accounting, and candidate-
  handoff completion records
- corpus manifest, producer summary, checksums, warnings, configuration, and
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
- **Producer handoff is not Task 04 freeze.** Task 03H reports exactly what was
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

## Plan / spec requirement

Write a short run plan immediately before execution. Confirm:

1. all source, corpus, parser, model, configuration, schema, hierarchy, and
   resolution identities;
2. exact commands and resource/retry settings;
3. stage-one monitoring, interruption, and atomic publication;
4. terminal-state and all-source-accounting requirements;
5. target-index sealing and second-pass no-mutation checks;
6. candidate-handoff policy for failures, including the hard stop for a
   material main-report failure;
7. fixed-subset rerun checks;
8. Task 04 machine-record and review-cache handoff; and
9. retention and isolation of failed or rejected versions.

Do not change accepted parser, Task 03E.2d hierarchy, schema, or resolution
policy during the run. A material new failure mode stops the candidate for an
explicit Task 03G or owning earlier-task revision.

## Review pass

- **Source accounting:** all and only the 35 model-corpus sources have terminal
  records.
- **Candidate integrity:** every published artifact is checksummed, contained,
  referenced, and covered by the appropriate completion record.
- **Stage isolation:** target-index and cross-document passes preserve
  stage-one bytes.
- **Structural consistency:** IDs, hierarchy, labels, aliases, references,
  coordinates, assets, and mappings satisfy the frozen contracts.
- **Warning visibility:** no failure, warning, anomaly, or source exception is
  erased by aggregation.
- **Independent freeze:** the candidate does not claim Task 04 acceptance.

## Validation

- Reconcile inputs against all 35 ordered manifest records and checksums.
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
- Rerun the Task 03G fixed subset and compare frozen invariants.
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
  warnings, unresolved references, validation commands, and Task 04 input.
- The candidate is not called accepted or frozen until Task 04 independently
  validates it.

## Non-goals

- assigning final usability or document dispositions
- reviewing every page or table semantically
- OCR, LLM repair, or visual-question answering
- extracting Final EIR Volume 4 comments and responses
- case screening, evidence authoring, retrieval, generation, or scoring
- changing parser, hierarchy, schema, or resolution policy during the run
