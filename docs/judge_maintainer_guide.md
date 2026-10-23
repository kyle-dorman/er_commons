# Production judge guide

## Task15Y diagnostic coverage judge

Task15Y is complete and accepted. Start with the
[accepted handoff](specs/task15y_judge_handoff_v1.md) and its
[machine-readable bindings](specs/task15y_judge_handoff_v1.json) for downstream use.

`required_support_coverage` owns the one-required-point input, approved prompt and
strict binary parser. `required_support_coverage_inspect` shares native provider
configuration without changing frozen A/G/S/C selection. Its wire schema omits
provider-unsupported `uniqueItems`; local validation still enforces unique IDs.
Only successful complete responses can receive a semantic label.

`required_support_coverage_run` executes a frozen, independently reviewed
six-question pilot or the explicitly pinned all19 suite. It reserves the full round,
including all allowed attempts,
binds the execution directory and verifies actual native request bytes. It retains
the full reserve rather than claiming unknown retry charges are free. Use
`make prepare-support-coverage-pilot COVERAGE_ROOT=...` offline, then explicitly
select `COVERAGE_PHASE=checkpoint` or `remainder` with
`make run-support-coverage-pilot COVERAGE_ROOT=...`. Remainder requires a saved
checkpoint review; phases are create-only and cannot be automatically replayed.
The [pilot specification](specs/task15y_pilot_v1.md) owns settings and limits.
Coverage remains diagnostic, independent of grounding and overall pass policy.
The [initial checkpoint](specs/task15y_round1_result.json) stopped because Luna
requires24h caching. The [authorized continuation](specs/task15y_round1_continuation_result.json)
completedRound1 using24h, with prior sent liabilities and attempt counts carried
forward. The runner verifies the ancestor's full seal and unchanged semantic inputs;
its create-only successor claim prevents budget forks. Continuation checkpoint
retries are reduced to one to respect each previously attempted slot's ceiling.
Both attempts are sealed; do not replay them.

The [all19 contract](specs/task15y_all19_preparation_v1.md) binds585 reviewed variants,
42 points, a new$30 cap and84 checkpoint variants. Use the explicit
`prepare-support-coverage-all19` / `run-support-coverage-all19` Make targets with
`COVERAGE_ROOT` and, for dispatch, `COVERAGE_PHASE`. The manifest must select
`execution_mode=all19` and exactly match the sealed prepared inputs. The fixed sibling
execution root and shared create-only claim prevent additional budget namespaces.
Remainder requires matching result/status hashes, fewer than two invalid checkpoint
slots, no fatal stop and an explicit review finding no systematic rule failure.
One approved round only; review before further calls. All19 remains development
calibration, with original-six/additional13 reporting kept separate.

### Editing and offline verification

Keep semantic changes in `required_support_coverage` and transport integration in
`required_support_coverage_inspect`. Within `required_support_coverage_run`:

| Concern | Owner |
| --- | --- |
| Exact source/file identities | `sealed_inventory`, `all19_binding`, `continuation_accounting` |
| Allowed cases, points and checkpoint | `validate_population` |
| Conservative budget and request-size allowance | `budget_bound`, `input_byte_bound` |
| Paid claims and checkpoint permission | `authorize_phase` |
| Actual request/response guards | `WireGate` |
| Planned-slot records, including failures | `judgment_rows` |
| Native execution and CLI | `execute`, `main` |

Limits and approved release identities are deliberate constraints, not general run
configuration. Keep them explicit. Failed/missing native results have no coverage
label; a failed sample cannot retain an evaluated status from stale score metadata.

Completed runs include their original code snapshots. Current code must reject an
old manifest when its code hashes differ; do not update historical manifests or
weaken that check to make them run. Verify behavior offline using saved inputs,
outputs and native logs. The code-quality audit records equivalence to all19 results;
it does not authorize new inference. Artifact-specific authoring/report scripts stay
with their run provenance; they are not additional maintained runtime entrypoints.

## Frozen production components

The maintained judges are four independent native Inspect calls. The selected
models and exact semantic identities live in
[`configs/judges_selected_v1.json`](../configs/judges_selected_v1.json); native
provider profiles live in [`configs/judge_models_v1.json`](../configs/judge_models_v1.json).

| Component | Selected model / prompt | Model-visible input | Core / Inspect adapter |
| --- | --- | --- | --- |
| A: no-answer | Luna / v2 | Original candidate conclusion only | `no_answer` / `no_answer_inspect` |
| G: grounding | Luna / v3 | Question, one point or factual qualification, its complete owned evidence | `point_grounding` / `point_grounding_inspect` |
| S: support | Haiku / v6 | Original candidate reasoning and qualifications under the selected S contract | `adequacy_binary` / `adequacy_inspect` |
| C: conclusion | Luna / v8 | Question, candidate conclusion, reference conclusion | `adequacy_binary` / `adequacy_inspect` |

`judge_inspect` owns provider configuration, schema adaptation, model construction,
cost registration, sample identity checks and selection verification. The component
cores own input validation, exact prompts and strict parsing; component adapters
own scoring. Dataset loaders verify frozen development artifacts and keep labels
and provenance outside model messages. Task 11C owns initial whole-answer routing and joins; Task 12 audits and finalizes aggregate reporting.

## Current structured C candidate (Task15P)

[Task15P](../tasks/sprint2/15p_paragraph_internal_contradictions.md) uses explicit
`CONCLUSION_STRUCTURED_V6_PROMPT_VERSION`: original paragraph input via
`ConclusionInput`, with only reference R/O IDs. Output includes `judgments`,
`internal_contradictions` (objects with a nonempty `reason`), `conclusion_adequate`
and `reason`. No candidate statement IDs, segmentation or contradiction pairs
enter this path. The [v6 contract](specs/task15p_structured_conclusion_judge_v6.json) binds prompt and
schemas; [v4 transformations](specs/task15p_conclusion_transformations_v4.md) own
new-case authoring. Earlier versions below are retained for historical replay.

The contradiction list is model reasoning support, not a separately scored label.
No expected list, pair matching or semantic review of explanation quality is
performed. Structural validation checks its shape. Logical diagnostics flag a
nonempty list with a pass and any disagreement with the independently computed
verdict: all R satisfied, no R/O contradicted and list empty. Preserve both verdicts;
no silent correction or semantic retry. The shared Baylands overview and native
real/synthetic context composition remain unchanged. Production defaults stay frozen.

The [Task15Q full-suite result](specs/task15q_structured_judging_result.json) records
382 fresh reviewed paragraph cases across all19 development questions and three
rounds per model. Expected labels are frozen overall Booleans; contradiction
reasons and point vectors have no separate accuracy target. The user accepted Luna with v6 for subsequent evaluation, retaining one judgment
per answer. Use the explicit v6 version; frozen historical defaults remain unchanged.
The evidence remains a synthetic development diagnostic.

The aligned generation prompt is selected by [Task15R](specs/task15r_generation_prompt_v1.json).
Its approved changes were used in15S/T; the final rerun is planned in15AD.

Current references are selected by [15AC](specs/task15ac_reference_result.json).
Canonical point IDs remain stable when a required point is removed. The existing
C schema still requires sequential IDs: use each release
`curator/judge_references/<case_id>.json` `input_reference`, supply the candidate
conclusion separately, and map results back with `wire_to_reference_point_id`.
Never pass the mapping or curator provenance to the judge, or curator references
to target generation. Pin the release/version; historical loaders do not select
this publication automatically.15Y joins must use canonical point IDs.

## Historical candidate-ID-only ablation (Task15O)

[Task15O](../tasks/sprint2/15o_candidate_ids_without_pair_output.md) tests the explicit
`CONCLUSION_STRUCTURED_V5_PROMPT_VERSION`. Input is identical to v4, including
lossless candidate A IDs. Output has only judgments, conclusion_adequate and reason;
no pair field or pair-reporting instructions. `aggregate_diagnostics` accepts an
explicit v5 version and computes reference-point-only adequacy. The native adapter
preserves both model and computed verdicts. V1–v4 and all defaults remain unchanged.
This experiment uses only65 known contradiction candidates, so it cannot measure
false rejection of compatible answers. The [contract](specs/task15o_structured_conclusion_judge_v5.json)
binds the exact prompt and schemas.

## Historical candidate pairs (Task15N experiment)

[Task15N](../tasks/sprint2/15n_explicit_contradictions_and_aggregation.md) adds
`CONCLUSION_STRUCTURED_V4_PROMPT_VERSION` as an explicit opt-in. The
[v4 contract](specs/task15n_structured_conclusion_judge_v4.json) binds prompt/schema
hashes and the same Baylands overview. `ConclusionInputV4` adds
`candidate_statements`, sequential A IDs and exact text spans whose single-space
join must reproduce `candidate_conclusion`. The experimental synthetic publication
supplies these spans; callers must not paraphrase candidate text to produce them.

`ConclusionOutputV4` adds `contradicting_points`, pairs of distinct supplied A IDs.
R/O statuses still report conflicts with reference meanings. Pair order is
irrelevant; duplicate/reversed duplicate pairs, unknown IDs and self-pairs are
invalid. Exact reference coverage remains required. Unlike v1–v3, v4 preserves a
model-final Boolean that disagrees with the point/pair aggregate.
`aggregate_diagnostics` computes the independent verdict and reports consistency;
the native scorer retains both decisions. The aggregate passes only when every R
is satisfied, no R/O is contradicted, and the pair list is empty. Incomplete output
has no computed verdict. Frozen defaults and historical validators are unchanged.

This is a paired development experiment, not a production promotion. See its task
for independently reviewed pair expectations, exclusions, carried-forward budget,
and model-final versus computed-result reporting.

## Structured C candidate (Task 15K)

The Task15K required/optional C policy
is preserved as `task15.binary_adequacy.conclusion_structured.v3`. Its contract
lives in `conclusion_structured.py`, exposed through `adequacy_binary` with
`CONCLUSION_STRUCTURED_V3_PROMPT_VERSION`. V3 adds contradiction-first
ordering and reuses the v2 schema/validator. The explicit v2 constant preserves
that earlier prompt. The original
`CONCLUSION_STRUCTURED_PROMPT_VERSION` still selects v1 with its original strict
quote policy. No structured version is promoted to frozen defaults. V2 clarifies
numerical and qualification addressedness and requests status/reason consistency.

Pass the explicit version to `system_prompt`, `output_json_schema`,
`validate_input`, and the native adapter. New input fields are `question`,
`candidate_conclusion`, `reference_required_points`, and
`reference_optional_points`. Each point contains `point_id` and `text`;
required IDs are sequential R1... and optional IDs sequential O1... . Reference
supporting points and sources remain excluded. The input model is
`conclusion_structured.ConclusionInput`.

Output fields are `judgments`, `conclusion_adequate`, and `reason`. Each judgment
contains `point_id`, `status`, `candidate_quotes`, and `reason`. Required statuses
are `satisfied`, `missing`, `contradicted`; optional statuses are `not_addressed`,
`addressed_without_contradiction`, `contradicted`. No legacy reason codes or
catch-all additions entries are accepted. `parse_output` requires `payload=packet`
for this version and validates exact ID coverage, status roles, quote presence
and Boolean aggregation. V2 permits quotes for missing/not-addressed judgments
when they illustrate incomplete or related content; v1 requires empty quotes for
those statuses. Other statuses require excerpts in both versions. ID order is a presentation preference, not a semantic
failure. Literal quote fidelity remains a diagnostic, not a semantic verdict.

`system_prompt` returns the complete new prompt including the exact frozen
Task11D14 Baylands document overview. `judge_context` verifies its checksum and
shares composition with real context projections. For structured real projections,
pass the explicit version to `context_projection.project_judge`; mismatched
prompts/overviews and legacy prose derivatives are rejected. Native synthetic
messages and real projected messages are tested byte-for-byte, including offline
Luna/Haiku provider schema handling. Do not prefix the overview manually.

Frozen production defaults and old synthetic publications remain unchanged.
The Task15B loader still accepts only its original prose-reference contract; a
revised [C001 structured pilot](specs/task15j_c001_structured_synthetic_result.json)
provides native-compatible `samples.jsonl`, separate `expected_labels.json` and
full `expected_judgments.jsonl`. Verify its completion and prompt/schema identities
before passing samples and labels to the explicit structured `build_task` version.
[Task15I](../tasks/sprint2/15i_run_c001_structured_judges.md) records the first
three-round Luna/Haiku execution. [Task15J](../tasks/sprint2/15j_refine_c001_structured_judge.md)
owns the v2 rerun and remaining point-level diagnostics. The legacy
whole-answer generation/evaluation/reporting pipeline is not yet migrated to a
new approved reference release. Native structured judging and real context
projection are available; end-to-end release migration remains downstream.

## Historical Task 15 prose C candidate

The earlier 2026-10-21 C policy
is preserved as `task15.binary_adequacy.conclusion_direct_answer.v1` in
`adequacy_binary.py`. It is an unqualified candidate, not the frozen selection.
Obtain its prompt with
`system_prompt("C", prompt_version=CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION)`;
pass that same explicit version to `output_json_schema` and `parse_output`.
The three-field input and strict output schema are unchanged; the new version
distinguishes changed semantics, including the narrower `extra_list_item` rule.

Omitting the version still selects v8. The native adapter accepts the candidate
through an explicit `prompt_version` argument to `build_task`, `native_model`,
`generation_config` and `adequacy_score`; it binds the same identity throughout
the request and scoring path. The selected configuration, default adapter path
and Make targets remain frozen. [Task 15C](../tasks/sprint2/15c_run_conclusion_development.md)
owns the newly requested staged execution and its population/run preflight.
Do not run the historical synthetic loader as a Task 15
evaluation. [Task 15A](../tasks/sprint2/15a_update_conclusion_prompt.md) records
the prompt-only scope and checks. Offline checks establish preservation and
strict parsing, not improved semantic judging.

The separate [Task 15B synthetic publication](specs/task15b_conclusion_synthesis_result.json)
contains newly authored, independently agent-reviewed C proposals. Load it with
`conclusion_synthetic.load_publication(result_path, data_root=..., partition=...)`,
explicitly selecting `tuning`, `audit` or `all`. It returns native-compatible
samples plus separate labels and provenance metadata; it does not dispatch a
judge. The loader verifies the seal, policy/prompt identity, development grouping,
reference bindings and reviews. The old C246 loader and Make targets are unchanged.
Audit variants use familiar development questions and are not unseen-question
qualification. Do not use audit outcomes for tuning.

## Execution

Inspect owns generation, retries, concurrency, epochs, logs and resumption. There
is no project HTTP executor, replacement-judgment loop or custom budget scheduler.
All four components support explicit `openai_generation`, `anthropic_generation`,
`fireworks_glm`, `ollama_small` and `ollama_9b` profiles. Omitting the condition uses
the verified selected model. The local models remain diagnostic alternatives.

Run from the repository with `.env` configured. Each command uses the full frozen
**development** dataset and defaults to one repetition. Set an external log location
and bounded sample options appropriate to the authorized run, for example:

```bash
make evaluate-no-answer JUDGE_LOG_DIR=/external/fresh-a-run JUDGE_OPTIONS='--limit 3'
make evaluate-point-grounding JUDGE_LOG_DIR=/external/fresh-g-run JUDGE_OPTIONS='--limit 3'
make evaluate-adequacy JUDGE_COMPONENT=C JUDGE_LOG_DIR=/external/fresh-c-run JUDGE_OPTIONS='--limit 3'
make evaluate-adequacy JUDGE_COMPONENT=S JUDGE_LOG_DIR=/external/fresh-s-run JUDGE_OPTIONS='--limit 3'
```

Use `JUDGE_CONDITION=fireworks_glm` or `JUDGE_CONDITION=ollama_small` to choose an
alternative explicitly, and `JUDGE_EPOCHS=3` for three repetitions. `JUDGE_OPTIONS`
passes through native Inspect options. These commands perform inference; cleanup
validation uses mocks and does not run them against live providers.

For saved or newly prepared inputs, use the adapters' `build_task` functions with
validated sample packets and separately bound labels. Calibration factories remain
available but use the selected prompts. Historical prompt experiments are archived.
Native logs preserve raw responses, errors, model usage and task identities.

Cloud defaults: 4,096 output tokens, medium reasoning, four static connections,
120-second request timeout, 45-second attempt timeout, two Inspect transport retries,
and 150-second sample limit. OpenAI/Anthropic SDK retries are disabled; Fireworks
retains its native SDK behavior. Native result caching is off; provider prompt
caching remains distinct. Inspect cost limits are soft per-sample limits, not a
project-wide hard spending cap. Token prices are dated estimates from the retained
comparison profiles, not live billing guarantees.

## Failure and visibility contracts

- G rejects missing or unresolved citations before inference. A failure to load
  known evidence is an evaluator error. Supporting points and factual qualifications
  use the same isolated check; no conclusion or neighboring prose enters G.
- A's `empty_other_prose_guard` is separate and required before accepting an
  abstention route. A classification alone never exempts a whole answer.
- Invalid, truncated or malformed output is a failure with no semantic decision;
  it never becomes false or clean abstention and never triggers a semantic reroll.
- C quotation fidelity remains diagnostic. It does not alter the selected binary
  decision. S receives original premises, without G predictions or filtering.
- Expected labels, IDs, mechanisms and provenance are evaluator metadata only.
  The strict combined A/G/S/C reporting policy is Task 12 work.

## Ollama and exact context checks

The native Ollama profiles use the existing `er09b-qwen-small-48k:v2` and
`er09b-qwen-f16-48k:v1` tags through Inspect. A tag is not a verified model digest;
verify the intended local service/model before a live diagnostic. Local concurrency defaults to one connection. Local cost is
unknown, not zero. These alternatives are not selected or benchmark-qualified.

`ollama_request` and `ollama_token_counter` retain the historical exact-rendering
preflight utilities used by deterministic packet preparation. Their render-only
request cannot generate text. They are not an exact counter for the new Inspect
OpenAI-compatible request. A future live qualification must bind that actual request
and context behavior; the old context receipt cannot qualify the new adapter.

## Evidence and historical replay

Model selections and completed reports remain immutable development evidence:
[C/S](specs/task09f_final_result.json), [A](specs/task09f1_a_full_development_v2_result.json),
[G](specs/task09f1_g_full_development_v3_result.json). The older per-component selected
configs and model profiles are historical bindings; production reads only the two
shared config files above. No labels or historical scores were changed by cleanup.

The recoverable pre-cleanup source snapshot lives under `ER_COMMONS_DATA_ROOT` at
`pipelines/brisbane_baylands/task_09/09f2_cleanup_20261016/`:
`pre_cleanup_source.tar.gz` plus `manifest.json` bind every archived file and archive
bytes. It includes the old uncommitted runtimes, tests, configs and both G analyzers.
Restore it into a separate directory, verify its hashes, and use its pinned `uv.lock`
for **offline** historical replay. G's archived analyzer intentionally verifies
historical runtime hashes; running it against the cleaned source is not supported.
Never extract over this checkout or modify sealed run directories. Snapshot recovery
does not authorize rerunning historical inference.

## Validation and ownership

Run `make fix`, `make check`, and `git diff --check`. Tests cover selected semantic
identities, strict failure behavior, label isolation, native provider serialization,
and sealed data loading. [09F.2](../tasks/sprint2/09f2_cleanup_production_judges.md)
records cleanup scope and verification. The [09G freeze](specs/task09g_judge_freeze_v1.json) binds the committed production
configuration and existing evidence without new inference. Task 11C owns initial
integration and Task 12 final reporting; held-out qualification remains separate.
