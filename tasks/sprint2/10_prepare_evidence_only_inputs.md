# Task 10 — Prepare evidence-only baseline inputs

Status: complete. One bounded task, no subtasks or model runs.

## Abstract

Prepare each frozen question with its already approved cited source passages so
a target model can produce supporting points and a conclusion. Build all 49
inputs now, retaining the 19-development/30-test split. Initial generation and
evaluation use only the 19 development cases. Retrieval is deferred under
[Decision 007](../../docs/decisions/007_evidence_only_first_baseline.md).

## Goal

Publish a small, deterministic, source-faithful input dataset and citation map
for the first evidence-only baseline. Reuse existing source assembly and release
verification; no search index, new evidence selection or model call is needed.

## Inputs

- [Current 09F v2 publication](../../docs/specs/task09f_question_publication_v2_result.json):
  exact questions, approved citation inventories, split and corpus bindings.
- [08H release outcome](08h_serialize_and_freeze_benchmark.md) and the current
  publication's verified dependency chain for source content and usability.
- Existing canonical citation/source assemblers and
  [09D metric interface](../../docs/specs/task09d_automatic_metrics_v1.md).
- [Architecture](../../docs/architecture.md), [artifact contract](../../docs/data_artifacts.md)
  and [current judge guide](../../docs/judge_maintainer_guide.md).

## Outputs

In a fresh versioned directory under `ER_COMMONS_DATA_ROOT`:

- Separate `target/dev.jsonl` (19 cases) and `target/test.jsonl` (30 cases), with
  case IDs outside model-visible payloads.
- Per-case payload: exact frozen question plus ordered passages. Each passage
  has a neutral local citation ID, source title, heading path and available
  page locations, and complete canonical source text/table content.
- A separate evaluator-only map from local IDs to canonical source/extraction/
  section-or-table identities and anchors. Preserve reference support/context
  roles here, never in target payloads.
- A compact manifest, validation report and completion seal binding input release,
  split, source dependencies, assembly policy/code and exact output hashes.
- A tracked outcome/result pointer and a short command for preparation/validation.
  Generated source text and datasets remain outside Git.

## Plan / spec requirement

Use this contract as the brief plan; record the concrete schema and assembly
policy alongside implementation rather than creating another planning task.

1. Verify the designated release and dependencies. Select all 49 cases by the
   frozen split, not filename inference. Mechanically read citation inventories
   for both splits; do not use test content to tune prompts or preparation policy.
2. For each question, include all approved cited source units, including optional
   context citations, deduplicating exact repeated views within canonical identity. Use complete sections
   and tables from existing canonical assembly, not curator-written excerpts or
   summaries. Preserve table headers, units, footnotes and continuations.
3. Order passages by canonical identity then anchor-scope digest, assign local
   `P1`, `P2`, ... IDs, and
   retain that mapping. Do not order by reference reasoning or expose roles.
   There is no five-passage cap, ranking, generated summary or new source search.
4. Build payloads from an explicit allowlist. Exclude reference conclusions,
   supporting points, qualifications, official responses, authoring notes,
   support/context labels and QA/provenance diagnostics. Citation selection is
   intentionally privileged in this condition; answer text is not supplied.
5. Validate every packet mechanically, including all 30 test packets. Inspect
   readable examples only from development or invented fixtures. Record source
   failures by case ID and diagnostic, without copying test answers into reports.
   Missing or inconsistent source content blocks a complete publication; do not
   silently drop cases, citations or text.
6. Record passage counts and text lengths as preparation diagnostics. Do not
   truncate or summarize to fit a guessed model budget. Task 11 must verify the
   actual rendered request and output reserve against its selected model before
   dispatch; an oversized packet remains an explicit blocker, not silent omission.
7. Publish the split datasets and verified mapping with a completion-last seal.
   Identical inputs reproduce identical payloads/maps; changed inputs use a fresh
   namespace. Preserve upstream publications unchanged.

Prepared passages are not proof of model delivery. Task 11 records actual request
payloads; Task 12 verifies their correspondence to these packets. Reuse canonical
identity conventions from 09D, but do not manufacture ranked retrieval receipts
or a retrieval score. Retrieval recall is not applicable for this condition.

## Research / learning checkpoint

The [Inspect dataset documentation](https://inspect.aisi.org.uk/datasets.html)
(reviewed 2026-10-16) separates model `input` from reference `target`, sample IDs
and metadata, and supports JSONL. Follow that boundary with explicit payload
projection; metadata placement alone does not prevent accidental prompt leakage.
Reuse the project's source assemblers and standard JSONL rather than adding a
retrieval dependency or dataset framework. Explain in the outcome that supplied
approved evidence tests answer construction, not evidence discovery, and does not
establish that the supplied evidence is exhaustive or that an answer is correct.

## Validation and acceptance criteria

- Exactly 49 unique cases, with exact frozen questions and unchanged 19/30 split.
- Every approved citation resolves to its verified complete canonical content;
  local IDs and evaluator mappings agree, including tables and repeated citations.
- Payload allowlist tests exclude reference prose and restricted metadata; use
  invented sentinel fixtures to test leakage without relying on text coincidence.
- Deterministic reruns, changed-input rejection and source/mapping failures are
  covered by focused tests. No silent dropping or truncation.
- Development input selection cannot include test records by default; the sealed
  test file is prepared for later explicit locked-test use.
- No inference, answer scoring, prompt tuning or retrieval experiment occurs.
- Run `make fix`, `make check` and `git diff --check` during implementation;
  distinguish pre-existing failures from regressions.

## Review pass

One bounded independent review of source completeness, payload isolation, split
handling and reproducibility. Reconcile findings before sealing; no new human
labeling pass or subtask series is required.

## Non-goals and handoff

No BM25, embeddings, agentic search, query expansion, source re-curation, reference
answer revisions, judge changes or test inference. Task 11 owns zero-shot answer
generation and context/output checks on development cases. Task 12 owns final
citation metrics, A/G/S/C integration and reporting, with retrieval explicitly
not applicable. Task 13 later runs the locked evidence-only test condition.

## Implementation decision — approved source scopes

Real-release qualification found two approved C014 views sharing one canonical
table identity: one includes table footnotes, the other surrounding section text.
Retain both as separate local passage IDs mapped to the same canonical unit;
deduplicate only exact repeated scopes. This preserves all approved text without
inventing a merged passage or silently dropping context. Canonical citation
matching remains unchanged. Sort equal canonical identities by anchor-scope digest.

The sealed citation index owns final roles. Nineteen optional-context occurrences
are absent from that index but remain explicitly optional context in the approved
case records; retain them and record their different role basis. A required
occurrence missing from the index fails. Original role lists remain unchanged.

## Outcome

Prepared all 49 source-only question packets from the current 09F v2 release,
with 19 development and 30 test records. The [result pointer](../../docs/specs/task10_final_result.json)
designates the sealed external publication. All 232 approved citation occurrences
are represented by 208 passage views over 207 case-level canonical units.
The [format and replay guide](../../docs/specs/task10_evidence_only_v1.md) owns
commands, schema, role isolation and downstream loading.

Source verification replays exact recorded text and full table cells against bound
canonical files. It supports compact, expanded and linked-source anchors and
recovers headings/titles through verified source metadata. Approved scope boundaries
remain inherited from the frozen release; no source re-curation occurred.

Learning: explicit JSONL payload projection keeps references and role metadata out
of model inputs. Canonical citation identity and source presentation scope are
related but not interchangeable: the C014 views illustrate why collapsing IDs
must not discard distinct approved content. Source length is not proof of context
fit, and prepared packets are not delivery receipts.

No model calls, scoring, retrieval or test tuning occurred. Task 11 is next: use
only the 19 development packets initially, verify the fully rendered request plus
output reserve, generate structured answers and retain actual delivery receipts.
The 30 test packets are prepared for later locked execution.

The final cleanup requires normalized roles from the verified loader and rejects
duplicate inventory paths in the development loader. Updated fixtures exercise
that same contract. The fresh v4 publication preserves byte-identical payloads,
evaluator maps, split, schema and diagnostics from v3; only implementation
provenance and the completion seal change. Earlier publications remain preserved.
A scoped independent cleanup review found no issues.

### Validation and limits

- `make fix`, format/lint/type checks and `git diff --check` passed.
- Focused Task 10 tests: 31 passed, covering linked/expanded anchors, table fidelity,
  role-index reconciliation, distinct approved scopes, isolation and publication.
- Full `make check`: 4,006 passed, one skipped. The earlier missing-drive failures
  disappeared after mounting the volume; no unrelated test repair was needed.
- Real reconstruction and independent audit passed. The result pointer binds the
  final completion, replay log, tests and review receipt.
- Development has 82 passage views; test has 126. The largest source text is
  32,889 characters; this is not a token/context guarantee. Tables also contribute
  structured payload content. Task 11 must count its actual rendered request.
- Prepared content is text-only; figure pixels and inherited upstream source
  limitations remain outside this qualification. Reference source boundaries are
  inherited, not newly adjudicated. No inference or semantic scoring occurred.
