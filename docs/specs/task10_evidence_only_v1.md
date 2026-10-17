# Task 10 evidence-only inputs v1

Status: real-release preparation complete; see the [Task 10 result](task10_final_result.json)
for the designated publication and validation evidence.

`evidence_only_sources.load_evidence_sources` verifies the designated release,
all 49 memberships, exact question/reference agreement, approval and corpus
membership. It requires canonical files to have frozen dependency hashes, then
replays the complete recorded block/cell spans and compares text/table content.
Complete section/table boundary selection remains inherited from the approved
release; this does not re-curate evidence or re-extract documents.

`evidence_only` projects and publishes deterministic JSONL. Its strict `Payload`
model generates `payload.schema.json`. Each target record contains only
`schema_version`, `case_id` and `payload`; only `payload` enters model messages.
The payload contains `question` and `passages`. Passages contain local citation
IDs, source-document IDs, title, edition when supplied, heading path, complete text, structured tables
and page labels.
Nested source diagnostics and review metadata are explicitly projected away.

Canonical source/extraction/kind/unit tuples followed by anchor-scope digests
determine ordering. Exact repeated views are deduplicated. Distinct approved
scopes sharing a canonical unit remain separate passages; no text is merged or
dropped. A repeated scope with conflicting content still fails validation. Evaluator mappings
retain original occurrences, canonical anchors and original role lists. The sealed
release citation index supplies final support/context roles, with support
precedence over optional context. Empty or historical role-list spellings do not
replace that approved index. Optional-context occurrences omitted from that index
remain included when their frozen occurrence explicitly has `role=optional_context`;
required occurrences must be indexed. Mappings distinguish those two role bases. They remain separate from target files. Downstream citation scoring should consume
`reference_role` and `canonical_unit`; the preserved `approved_roles` list is
historical provenance and is not a normalized metric input.

## Publication and replay

The output contains `target/dev.jsonl`, `target/test.jsonl`, corresponding
`evaluator/*_mappings.jsonl`, `split.json`, `payload.schema.json`,
`validation.json`, `manifest.json` and completion-last `completion.json`.
The manifest binds the release, source files, implementation and dependency lock.
No-clobber publication allows exact partial resumes. Validation reconstructs
outputs from verified sources and compares every byte, including mappings.

Use an explicit release pointer and a fresh output directory under the configured
`ER_COMMONS_DATA_ROOT`:

```bash
make prepare-evidence-only \
  EVIDENCE_RELEASE=docs/specs/task09f_question_publication_v2_result.json \
  EVIDENCE_OUTPUT="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_10/evidence_only_v4"
make validate-evidence-only \
  EVIDENCE_OUTPUT="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_10/evidence_only_v4"
```

The shell variable in this example must be exported; Make also reads `.env`.
Do not create a missing external mount point as a substitute for mounting the
source drive. Preparation refuses an absent data root.

`load_records(output)` reads only the development payload file by default.
Explicit `split="test"` selects the sealed test file for later authorized use.
Consumers must bind the completion identity in their run manifest and send only
`record["payload"]`; target generation still owns prompt/schema formatting.

## Limits

These are prepared inputs, not model-delivery receipts. Task 11 must check actual
rendered token counts with output reserve and record exactly what was sent. Text
lengths in validation are diagnostics, not proof of context fit. No truncation,
summary, inference, scoring or retrieval occurs. Retrieval recall is inapplicable.

The actual 49-case publication includes 232 citation occurrences represented by
208 passage views over 207 case-level canonical units. C014 retains both approved
views of one table: surrounding-section context and table footnotes. Exact source
text and complete tables are preserved separately. Linked/expanded anchors and
missing display metadata are recovered only through checksum-bound source records.
Figure pixels remain outside this inherited text-only evidence representation.

Earlier publications through `evidence_only_v3` remain preserved;
`evidence_only_v4` binds the final cleaned implementation. Use the result pointer,
not directory recency, to select the accepted handoff.
