# Task 03H: Run and Validate the Full Canonical Extraction

Status: **provisional**. Revise this contract from the accepted Task 03G outcome
before activating it.

## Abstract

Execute the frozen Task 03G workflow across all 35 checksum-pinned model-corpus
PDFs, validate the resulting raw and canonical artifact graph, and publish a
complete candidate extraction plus producer-side integrity evidence and the
precise Task 04 usability handoff. Account explicitly for every source, page,
record, asset, warning, partial result, and inherited provenance exception.
Task 04 independently validates the candidate and freezes extraction v1; do not
make human page-usability or document-disposition decisions here.

## Goal

Produce a complete, reproducible, internally consistent candidate canonical
extraction whose lineage and limitations can be independently validated before
human usability review freezes it.

## Inputs

- user-approved Task 03G production configuration and capacity settings
- the sealed Task 02 `source_manifest.json`, filtered to its 35
  checksum-pinned `model_corpus` records
- production commands and schemas completed in Tasks 03C–03F
- accepted pilot artifacts and extraction-version identity
- `/Volumes/x10pro/er_commons` with sufficient verified free space

## Outputs

- raw Docling and clean table-pipeline output, page renders, extracted images,
  canonical records including tables and table families, hierarchy records,
  mapping observations, and cross-reference candidates for all accepted
  conversions
- one per-document completion or explicit failure record for every required
  source
- corpus-level candidate manifest, producer summary, checksums, warnings,
  configuration, software/model/runtime identities, and producer completion
  record
- producer-side completeness, schema, referential-integrity, coordinate, asset,
  and rerun-validation reports for Task 04 to check independently
- page-, table-, and table-family machine records plus mapping observations for
  Task 04, with no human-review fields
- document-level machine summaries for Task 04, without usability dispositions
- propagation of every Task 02 source warning through the applicable candidate
  document/page records, including `source_edition_override` for Appendix K2
  part 2
- an exact Task 04 input path and review boundary

## Research / learning checkpoint

Before the full run, review the distinction between conversion status,
artifact integrity, and semantic correctness. Use W3C
[PROV-O](https://www.w3.org/TR/prov-o/) as a general lineage vocabulary and
Docling's conversion status/error model as the concrete parser boundary.

The outcome must explain:

- **A zero exit code is not a data-release proof.** Release validation has
  layers: source coverage, artifact completeness, schema validity, referential
  integrity, geometric consistency, semantic rerun checks, and explicit warning
  accounting.
- **Producer completeness is not correctness or release acceptance.** Automated
  checks can establish that
  48,341 expected pages and their relationships were accounted for; they cannot
  establish that every table, reading order, or heading is semantically right.
  Task 04 remains the independent validation and freeze gate.
- **Partial success requires policy, not optimism.** A raw parser document with
  warnings or missing stages must retain its evidence and cannot be silently
  promoted to an accepted corpus member.
- **Extraction recall bounds retrieval recall.** If support is absent or
  unusable in the canonical corpus, no retriever can recover it. Later
  evaluation should separate extraction absence from ranking failure and from
  target-model synthesis failure.
- **Oracle contexts do not repair corpus lineage.** Later oracle evidence
  diagnostics help localize retrieval versus synthesis limitations only when
  their evidence anchors resolve against this exact extraction version.
- **Extraction changes invalidate anchors.** Reprocessing with a new parser,
  model, or configuration creates a new corpus version and requires explicit
  benchmark migration; it must not silently refresh low-level evidence under
  old IDs.
- **Warnings are part of the release contract.** Parser repairs, partial
  results, suspicious structural distributions, and the K2 source override
  must remain queryable by later curation and attrition analysis.
- **Evaluation validity depends on a fixed preprocessing treatment.** Comparing
  target or retriever runs over different unnoticed extraction states creates a
  confounded experiment even if model settings are identical.

## Plan / spec requirement

Write a short run plan immediately before execution. It must confirm:

1. source and extraction identities plus available storage;
2. exact commands, concurrency, device, batch, timeout, and retry settings;
3. progress-monitoring and interruption behavior;
4. required per-document and corpus completion records;
5. producer-side validation layers and stop conditions;
6. how partial/failing documents remain preserved without marking the candidate
   producer-complete;
7. fixed-subset rerun checks after completion;
8. Task 04 machine-record handoff with human-review fields absent; and
9. final artifact retention and rejected-version isolation.

Do not change the accepted parser configuration or canonical schemas during the
run. A material new failure mode stops the release for an explicit Task 03G or
earlier-task revision; it is not patched only for the remaining documents.

## Review pass

- **Corpus completeness:** all and only the 35 model-corpus sources and their
  expected pages are accounted for.
- **Candidate integrity:** every required artifact is checksummed, contained,
  referenced, and marked producer-complete only after producer validation.
- **Structural consistency:** IDs, hierarchy, cross-references, coordinates,
  assets, and raw mappings satisfy the frozen contract.
- **Warning visibility:** no partial success, parser warning, anomaly, or source
  exception is erased by aggregation.
- **Evaluation handoff:** Task 04 can review page renders and machine
  observations without recomputing extraction or receiving prefilled human
  judgments.
- **Independent freeze:** the candidate does not claim the Task 04 extraction-v1
  freeze or substitute producer checks for independent validation.

## Validation

- Reconcile extraction inputs against all 35 ordered manifest records and
  recorded source checksums.
- Reconcile expected versus produced PDF page counts per document and corpus.
- Validate every raw/canonical artifact role, schema, checksum, and contained
  path.
- Validate global ID uniqueness within the extraction version and every
  document, page, block, section, table, table-family, figure, image, asset,
  mapping, and reference relationship.
- Validate bounding boxes against page dimensions and declared coordinate
  frames.
- Validate every required page render and every referenced extracted asset.
- Recompute aggregate counts from records rather than trusting separately
  maintained totals.
- Rerun the Task 03G fixed subset and compare the declared semantic invariants.
- Verify human-review fields are absent from Task 03 records and all applicable
  Task 02 source warnings are propagated, including K2's source-edition
  warning.
- Verify Git contains no raw PDFs, converted bulk content, renders, models, or
  generated extraction records.
- Run:

```bash
make check
git diff --check
```

## Acceptance criteria

- Every one of the 35 source-manifest records has a producer-verified completed
  extraction under one frozen extraction identity; otherwise no producer
  completion record is published.
- Expected source and PDF page counts reconcile exactly or stop with an
  explicit reviewed exception.
- Any material native-extraction failure in the main report stops the candidate
  and requires a new decision; it cannot be passed forward as a skipped source.
- Raw Docling and clean table-pipeline output, canonical records, renders,
  assets, logs, warnings, and manifests are complete and internally linked.
- All schemas, IDs, coordinates, checksums, and referential-integrity checks
  pass.
- Fixed-subset reruns satisfy the frozen semantic reproducibility policy.
- Every Task 02 source warning remains discoverable in the applicable candidate
  metadata, and `source_edition_override` is present on the K2 part 2 document
  and page machine metadata.
- Task 04 receives complete page, table, table-family, and mapping machine
  records with human-review fields absent.
- Generated bulk artifacts remain outside Git under the versioned external
  extraction root.
- The outcome reports exact counts, bytes, timings, warnings, validation
  commands, and the precise Task 04 input.
- The candidate is not called extraction v1 or frozen until Task 04 independently
  validates and accepts it.

## Non-goals

- assigning `usable`, `usable_with_exclusions`, or `skipped_no_ocr`
- reviewing every page render or verifying every table semantically
- OCR, LLM repair, or visual-question answering
- extracting Final EIR Volume 4 comments and responses
- case screening, evidence authoring, or benchmark splitting
- retrieval indexing, target generation, judging, or scoring
- changing the parser, schema, or configuration during the run
