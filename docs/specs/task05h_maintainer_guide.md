# Task 05H maintainer guide

Task 05H combines accepted records and records new composition review. It does
not run an extractor, resolver, model, or visual review. Task 05H is
published and accepted with limitations. The [final result](task05h_final_result.json)
and [summary](task05h_final_summary.md) own current release evidence; earlier
replay and finalization results remain preserved history.

## Start and authority

Read the [task](../../tasks/sprint2/05h_review_and_freeze_response_inventory.md),
[accepted-input freeze](task05h_phase1_bindings.json),
[exact review selection](task05h_review_selection.json),
[publication/acceptance request](../../configs/brisbane_baylands_2025_feir_task05h_publish_v1.json),
and [publication packet](task05h_publication_packet.json) and [acceptance packet](task05h_acceptance_packet.json). The accepted base remains
`3d5bea8`; the uncommitted implementation has its own exact file bindings.
All five phases completed under explicit authorization. The accepted release is
immutable; those approvals do not permit changing it or starting downstream work.

The plan identity binds accepted authority, behavior, schemas, explicit code
owners, Python/library versions and resource limits. Selection has its own exact
seal and is recomputed before output. Later review inputs and authorization
switches are excluded from plan identity to avoid an identity cycle. They remain
bound by each launch packet and by finalized review payloads. Changed code,
runtime or policy requires a new plan; changed inputs cannot inherit review.

## Small ownership boundaries

| Module | Responsibility |
| --- | --- |
| `release_spec` | Strict request, portable paths, finite code/runtime inventory, plan identity |
| `release_inputs` | Read selected JSON authorities, validate closure and accepted semantics |
| `release_validation` | Exact record membership, accounting and inherited limitations |
| `release_review` | Deterministic strata/obligations, view index, decisions and evidence |
| `release_views` | Bounded static text cards; no judgments or authoritative source copies |
| `release_storage` | Closed managed files, deterministic JSON, completion-last containers |
| `release_workflow` | Explicit preparation, review cache, validation and finalization steps |
| `release_publication` | Quality gate, immutable copy, acceptance evidence and designation |
| `release_launch` / `release_execution` | Existing resource supervisor, exact packets and terminal receipts |

These modules use the existing artifact helpers and accepted record validator.
They do not import historical reference resolver loaders. There are no added
runtime dependencies or generic workflow engine. The CLI dispatch is additive;
accepted requests and historical tests retain their original behavior.

For a local change, start at the rule's owner: `_select_source_anchors`,
`_select_graph_relationships` or `_select_official_references` for review
selection; `_render_card`, `_unit_html` and `_span_html` for presentation;
`_operation_arguments` for shared command arguments. In `release_workflow`,
`execute` lists the stage routing and each named stage exposes its own sequence.
Keep policy out of serialization and rendering helpers. The dedicated
[human maintainability review](task05h_code_quality_review.md) explains these
boundaries and the independent assessment.

## Review and corrections

The frozen selection contains 116 obligations across 52 strata. An obligation
may cover a selected individual or a rule/class card; this is not a claim of
116 newly reviewed source records. Class cards name their complete membership
and require first/last representative evidence. The 2,029-unit view index keeps
all 1,011 accepted comment views plus otherwise unrepresented units. Shared
general responses and graph cycles are not recursively flattened.

Reuse accepted evidence at its recorded scope. The new task asks whether source
identity, boundaries, direct relationships, outcomes, warnings and display
eligibility remain faithful in the assembled inventory. It does not upgrade
the 51 sampled-stratum carries into individual reviews, revisit the 43 nonlinks,
remove the 66 F1 warnings, or make any of the 178 figure targets text evidence.

Maintain a JSONL decision journal outside release closure during curation. Each
record follows the closed `decision` definition in
[records.schema.json](../../benchmarks/er_bench/schemas/response_inventory/release_v1/records.schema.json):
`decision_id`, `schema_version`, `plan_id`, `subject_refs`, `question_version`,
`coverage_basis`, `disposition`, `rationale`, `evidence_refs`, `reviewer`,
`reviewed_at`, `supersedes`, `action`, `replacement_refs`, `requires_owner_replay`.
Use the exact subject and coverage basis from the selection. Record an actual
reviewer, timezone-aware time, and an explanation of the inspection performed.
Evidence references require exact identity, artifact-relative path, SHA-256 and
record ID. Null-digest 05D records use the accepted completion as authority
together with exact source-record membership and accepted semantic validation.
Disposable HTML alone cannot establish evidence authority.

Identical decision retries deduplicate; conflicting IDs or overlapping active
decisions fail. Supersession must explicitly name an earlier decision for the
same subjects. Finalized decision records are sorted by ID. Any correction,
owner finding or required upstream replay in the same plan blocks closure,
including a later attempt to supersede it away. Record the finding and obtain a
bounded amendment with renewed affected review. Never edit accepted evidence.

The independent final quality report must bind `plan_id`,
`input_semantic_digest`, exact `repository_bindings`, and `review_payload_digest`
from `release_workflow.review_payload_digest`. It requires an identified reviewer,
literal `independent_review: true`, `status: passed`, no material findings, and
passing readability, editability, debuggability, operations and testing dimensions.
The Phase 2 code review cannot substitute for this later review of actual
assembled decisions and payloads.

## Commands and restart

Repository-only checks are available now:

```sh
uv run er-responses validate-spec --run-spec configs/brisbane_baylands_2025_feir_task05h_publish_v1.json
uv run pytest tests/test_task05h_*.py
make check
git diff --check
```

The helper `scripts/prepare_task05h_execution.py --data-root <configured-root>`
is the historical Phase 2 packet generator. Do not rerun it over preserved
request/preview evidence. Changing bound code requires a separately named
request and fresh plan with reviewed bindings, as in the current replay.

The executable stages below use one supervised worker; validation is read-only.
All stages completed under their separate authorizations. Preserve the existing
receipts and immutable release; the commands below document stage responsibilities. Use the exact
request, roots and command in the reviewed packet. All stages require `--run-spec`; all take `--attempt` and optional `--resume-from`.

| Stage | Additional arguments / result |
| --- | --- |
| `prepare-05h` | Creates compact prepared composition and selection |
| `review-05h` | Creates text cache only; curator decisions remain explicit |
| `validate-05h` | `--candidate-root`; read-only semantic and closure check |
| `finalize-05h` | Requires sealed decision/quality inputs and successful prepare/review receipts |
| `publish-05h` | `--candidate-root` naming that attempt's supervised finalized candidate |
| `accept-05h` | `--candidate-root` naming its published inventory, `--accepted-by`, `--accepted-at` |

Attempt 001 is the initial request. A resume explicitly names an earlier
prepared checkpoint, creates a fresh numbered attempt, revalidates its exact
semantics and builds review views for the new attempt. Never pick the newest
directory, delete a partial attempt, or overwrite a differing cache. Successful
identical containers reuse without rewriting. Failed finalization/publication
retains its evidence and cannot satisfy the next gate.

One worker and two CPU threads are allowed. Per-command limits are 4 GiB
process-tree RSS, zero swap growth, 1,800 seconds and at least 8 GiB free space.
The 2 GiB cumulative new-output ceiling includes all 05H attempts, caches,
supervisor records, staging and publication. The launcher charges prior output,
publication copies and reserved terminal metadata. Human review time is outside
command deadlines. A limit failure requires inspection and a reviewed amendment,
not disabling the supervisor.

## Finalization, publication and debugging

Source text stays in accepted 05D. The release owns compact references, indexes,
decisions, diagnostics, provenance and handoff. During first finalization, only
declared null-digest 05D JSON files receive new byte seals in the 05H component
record. The exact bytes being sealed must match the already validated semantic
records. Original files and inventories remain unchanged. Later reuse checks
the finalized completion against the successful worker's retained result;
self-consistent replacement manifests cannot silently replace those seals.

Read the first failed invariant and the exact launch/terminal records before
changing anything. Source semantic mismatch means stop at the accepted-input
boundary. Selection mismatch means stale plan membership. Review mismatch means
unclosed subjects, evidence or conflicts. Quality mismatch means stale code or
decision attestation. File-closure mismatch means extra, missing or changed
owned files. None is repaired by weakening a check.

Publication copies only compact 05H-owned files to the predicted immutable
inventory identity. Acceptance writes evidence outside closure; designation is
last and only after successful terminal supervision. A different existing
pointer requires explicit supersession approval. Tasks 07/08 pin the pointer,
completion and external component seals and retain every inherited limitation.
Their execution remains separately authorized.
