# Maintained pipeline commands

These entrypoints describe maintained interfaces; completed-task commands are
historical evidence unless an active contract selects them.
Run commands from the repository with `uv run python scripts/<name>.py` (or the
package CLI shown below). Paths in a request are resolved by its typed loader;
read that loader's schema before preparing a new request. `--help` performs no
source or model work. Commands that execute or render require the active task's
applicable authorization; their presence here is not production authorization.

| Operation | Interface and required selection | Owner / contract |
| --- | --- | --- |
| Qualify a selected source | `er-commons sources validate-qualification-spec`, `sources acquire-qualified`, `sources reuse-qualified`, each with `--spec PATH` | [Task 06C qualification contract](specs/task06c_source_qualification_v1.md); validation/reuse are source-free, acquisition requires separate authorization and never starts conversion |
| Supervise a background command | `python -m er_commons.document_publication.background_execution --help` | Explicit command/attempt/output paths and finite limits; use within tmux for persistent execution; [06C preparation](specs/task06c_gate3_preparation.md) |
| Propose or check current configs | `generate_document_configs.py --generation-spec PATH [--check]` | `document_publication/config_generation`; [request schema](../benchmarks/er_bench/schemas/document_config_generation/v1/request.schema.json) |
| Qualify selected run inputs | `prepare_document_inputs.py --document-spec PATH --collection-spec PATH --output-root PATH` | `document_publication/input_preparation.py`; compact bounded manifest/recipe checks |
| Execute declared documents | `run_document_collection.py --document-spec PATH --source-id ID --progress-root PATH` (repeat IDs, or select `--all-sources`) | `document_publication/collection_runner.py`; serial, spec-bound progress; actual execution may open sources |
| Prepare relink contracts | `prepare_document_relink_specs.py --preparation-spec PATH` | `document_records/document_references/preparation_spec.py`; explicit accepted roots, old recipe, new paths, policies and v2/v3 schemas |
| Qualify caption-backed figures | `uv run python scripts/qualify_figure_caption_aliases.py --structured-root DIR --source-id ID --source-document-id ID --output-root DIR [--reuse-existing]` | [Figure-caption policy](specs/figure_caption_alias_v1.md); source-free selected-record qualification with a fresh no-clobber output, or exact current-identity verification when reuse is explicit. [Task 06F](../tasks/sprint2/06f_publish_caption_backed_figure_targets.md) retains the accepted example. |
| Prepare/materialize/reconcile reviewed navigation | `prepare_reviewed_navigation.py`, `materialize_reviewed_navigation.py`, `reconcile_reviewed_navigation.py`, each with `--input-spec PATH --output-root PATH` | `navigation_overlay/input_specs.py`; explicit extraction/review/scope/schema bindings |
| Publish one document / relink / assemble | `er-commons documents publish`, `documents relink`, `collections assemble-handoff` | Existing commands retain their explicit document/link/collection specs; use `--help` for selectors |
| Inspect Task 05G replay | `er-responses validate-spec --run-spec PATH`; `python -m er_commons.response_inventory.reference_replay_launch --run-spec PATH --attempt N --print-packet` | New v6 consumer; read-only request/packet validation; [05G contract](../tasks/sprint2/05g_replay_and_extend_official_reference_links.md) |
| Supervise Task 05G replay | `python -m er_commons.response_inventory.reference_replay_launch --run-spec PATH --attempt N --operation all [--resume-from N]` | Separate execution authorization; primary prepare/build/compare route. Public v6 stage verbs also supervise, each in a fresh explicit attempt; never invoke the private worker directly |
| Compact historical reuse | `read_accepted_conversion`, `read_accepted_producer`, `read_accepted_range`, prepared publication inputs | [Verification contract](specs/task06b_verification_boundaries_v1.md); recorded identities, seals, metadata and closure; no fresh payload equality claim |
| Inspect conversion metadata | `inspect_conversion_scaling.py --data-root PATH --run-relative-root PATH --source-id ID --output-root PATH --ledger` | `document_performance/conversion_scaling.py`; source/model-free ledger |
| Profile or deep audit conversion evidence | Same diagnostic command, explicitly select its profile, benchmark, or `--deep-audit-legacy-conversions` operation | `conversion_scaling.py`, `conversion_compatibility_audit.py`; these operations can read/hash large selected payloads and are separate from compact reuse |
| Audit no-page section rules | `audit_document_linking.py --entries PATH --document-publications-root PATH --linking-policy PATH --policy-schema PATH --operation no-page-sections` | `navigation_overlay/linking_reconciliation.py`; selected implemented rule scope only |
| Deep regression audit | `validate_document_relink_run.py --operation deep-regression-audit --validation-spec PATH --data-root PATH --link-spec PATH --navigation-root PATH --output PATH` | `navigation_overlay/relink_run_validation.py`; explicit populations/context, byte audit, in-memory relinking; no candidate publication |
| Prepare/build/publish review | `prepare_extraction_review.py`, `build_extraction_review_bundle.py`, `build_final_extraction_review.py`, `publish_extraction_review.py`, each with `--review-spec PATH --output-root PATH` | [Review runbook](task04_maintainer_runbook.md); historical profiles plus the Task 06H source-free preparation and separately bounded rendering profile; publishing remains a separate authorization gate |
| Update reviewed findings | `record_review_finding.py`, `set_review_register_status.py` with explicit `--review-root` and finding/status arguments | Existing finding/register semantics retained |

`make finalize-response-relationship-candidate` requires
`RELATIONSHIP_REVIEW_ROOT` and `QUALITY_REPORT`. The review builder requires
`RELATIONSHIP_ROOT`, `SOURCE_RECORDS`, `QUALIFICATION`, `RENDER_ROOT`,
`REVIEW_TOOL_ROOT`, and `SERVED_ROOT`. No mutation target silently selects an
accepted review root.

Current run specs retain original per-source manifests. A replacement collection
uses explicit logical-to-physical membership; an F1 replacement or wrapper rename
does not make the other documents fresh conversion outputs. Original task-named
configs, schema literals, seals, identities, and human decisions remain historical
contracts. A historical reader does not require old implementation files to exist.

## Task 08A saved preparation

New groups use `make prepare-group-ranking-v2`, then either
`make prepare-small-group-order-v2` for at most three candidates or a separately
recorded Astra order for larger groups, followed by
`make publish-group-ranking-v2` and `make validate-group-ranking-v2`.
Set `GROUPING_DIR`, `GROUPING_SHA256`, `GROUP`, `RANKING_INPUT`,
`RANKING_PROPOSAL` and a fresh `RANKING_OUTPUT` as applicable.
The [shared v2 specification](specs/task08a_ranking_v2.md) owns exact formats.
Historical `validate-group-ranking` remains the v1 validation route.
Preparation does not start human selection or later authoring stages.

## Task 08B batch setup

`make prepare-group-selection-batch` prepares separate blank review projects from
the verified 08A index. Required variables and restart behavior are in the
[shared intake revision](specs/task08b_intake_v2.md). It preserves completed and
compatible projects, reports blocked groups independently, and saves a compact
link/status index. This command does not select candidates or advance 08C.

## Combined Task 08C review

Use `make validate-combined-wording-chat` and `make export-combined-wording-chat`
with the pinned packet/prompt and full predecessor chain specified in the
[combined review process](specs/task08c_combined_chat_review_v1.md). The
[current checkpoint](specs/task08c_combined_review_result.json) identifies exact
files. Historical per-group commands retain their original semantics.

## Combined Task 08D preparation and chat

`make prepare-combined-claim-input CLAIM_INPUT=...` verifies the final combined
08C result into a fresh input directory. After separately recorded Astra proposals,
`make assemble-combined-claims CLAIM_BATCH=... CLAIM_PREPARED=...` prepares the
combined queue; independent review and publication remain separate gates.

Use `make claim-chat` with `CLAIM_ACTION=validate|next|record|export`,
`CLAIM_QUEUE_REFERENCE` and `CLAIM_JOURNAL`. Recording additionally requires
`CLAIM_EVENT`; export requires a fresh `CLAIM_EXPORT`. The
[production chat specification](specs/task08d_combined_chat_review_v1.md) owns
exact events and resumption. A preparation request does not authorize human review.


## Native judge evaluation

The [production judge guide](judge_maintainer_guide.md) owns current native Inspect
commands: `make evaluate-no-answer`, `make evaluate-point-grounding`, and
`make evaluate-adequacy JUDGE_COMPONENT=C|S`. Each requires an explicit external
`JUDGE_LOG_DIR`; native Inspect options control repetitions and limits. Retired
09E/09F experiment commands exist only in the historical source snapshot.

## Evidence-only baseline preparation

Task 10 provides `make prepare-evidence-only EVIDENCE_RELEASE=PATH EVIDENCE_OUTPUT=DIR`
and `make validate-evidence-only EVIDENCE_OUTPUT=DIR`. Both are offline; preparation
requires the configured artifact root to exist. The completed Task 10 publication
is selected by its result pointer. The [format/replay guide](specs/task10_evidence_only_v1.md)
owns exact arguments, outputs and split-loading behavior.

## Offline development reports

`make report-development REPORT_OUTPUT=/absolute/external/task_12/output` verifies
and replays the sealed Task 11E development results, then publishes tables/charts.
The output must lie under `$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_12/`;
`.env` supplies the root. This command runs the package manager offline and has
no model/counting mode. An identical rerun verifies all output bytes; use a fresh
namespace after code/configuration changes. See the [frozen definitions](specs/task12_reporting_v1.md)
and [accepted result](specs/task12_result.json).

Saved-report figure/table export and explicit legacy-judge enrichment are documented
in the [reporting maintainer guide](reporting_maintainer_guide.md). The exporter
accepts `--primary-model`; model comparison rosters come from saved tables.

## Locked evaluation and selective review

Task 13 is closed. Its [task outcome](../tasks/sprint2/13_run_locked_test.md)
retains historical preparation/dispatch commands and the approved execution gates;
these do not authorize restarting the run. Use the
[sealed result pointer](specs/task13_result.json) for the completed Luna/Haiku report.
The final gallery is `task_13/test_30_review/START_HERE.html` beneath the project's
external pipeline root. Offline re-export uses the
[reporting maintainer guide](reporting_maintainer_guide.md) and a fresh destination.

[Task 14](../tasks/sprint2/14_selective_failure_review.md) is active for structured,
iterative review with Kyle in the next chat. Read saved score tables to select
examples, then review their saved answers and evidence within the task's bounds.
It authorizes no remote generation, judging or token-counting requests and no
changes to sealed scores. The task contract owns the review record and handoff.
