.DEFAULT_GOAL := help

ENV_FILE := .env
-include $(ENV_FILE)
export ER_COMMONS_DATA_ROOT

.PHONY: help bootstrap sync check-env data-dirs about paths freeze-brisbane-sources \
	verify-brisbane-sources validate-collection-contract publish-document \
	assemble-collection-handoff validate-collection-handoff \
	validate-response-inventory-contract validate-response-inventory-pilot-spec \
	validate-response-inventory-complete-spec validate-response-relationship-review-spec \
	export-pilot-case-citations \
	build-response-relationship-review-pass build-response-relationship-review \
	finalize-response-relationship-candidate \
	format format-check lint lint-fix type test check fix

help:
	@echo "ER Commons commands:"
	@echo "  make bootstrap   Install dependencies and create external data directories"
	@echo "  make about       Describe the current project scope"
	@echo "  make paths       Show the configured external data/artifact paths"
	@echo "  make report-development REPORT_OUTPUT=PATH  Replay sealed Task 11E tables/charts offline"
	@echo "  make freeze-brisbane-sources  Freeze the reviewed Brisbane source release"
	@echo "  make verify-brisbane-sources  Verify the frozen release without network access"
	@echo "  make validate-collection-contract  Validate the current v2 contract fixtures"
	@echo "  make validate-response-inventory-contract  Validate source-free Task 05 records"
	@echo "  make validate-response-inventory-pilot-spec  Validate the source-free Task 05C run spec"
	@echo "  make validate-response-inventory-complete-spec  Validate the source-free Task 05D run spec"
	@echo "  make build-response-relationship-review  Build the lazy read-only Task 05E review page"
	@echo "  make build-response-relationship-review-pass  Replay accepted bounded Task 05E rules"
	@echo "  make finalize-response-relationship-candidate  Close the reviewed Task 05E candidate"
	@echo "  make publish-document DOCUMENT_SPEC=PATH SOURCE_ID=ID  Publish one document"
	@echo "  make assemble-collection-handoff COLLECTION_SPEC=PATH  Assemble one collection handoff"
	@echo "  make validate-collection-handoff COLLECTION_ROOT=DIR SCOPE_ID=ID SCHEMA=FILE"
	@echo "  make export-pilot-case-citations CASE_EXPORT_DIR=PATH  Replay sealed reviews into a fresh case export"
	@echo "  make fix         Apply lint and formatting fixes"
	@echo "  make check       Run formatting, linting, types, and tests"

sync:
	uv sync

check-env:
	@test -f "$(ENV_FILE)" || (echo "Missing .env. Copy .env.example and set ER_COMMONS_DATA_ROOT."; exit 1)
	@test -n "$(ER_COMMONS_DATA_ROOT)" || (echo "ER_COMMONS_DATA_ROOT must be set in .env."; exit 1)

data-dirs: check-env
	@mkdir -p "$(ER_COMMONS_DATA_ROOT)/datasets/ceqa" \
		"$(ER_COMMONS_DATA_ROOT)/pipelines" \
		"$(ER_COMMONS_DATA_ROOT)/benchmarks/er_bench"

bootstrap: sync data-dirs

about: check-env
	uv run er-commons about

paths: check-env
	uv run er-commons paths

.PHONY: report-development
report-development: check-env
	@test -n "$(REPORT_OUTPUT)" || (echo "REPORT_OUTPUT=PATH is required"; exit 1)
	uv run --offline --env-file "$(ENV_FILE)" python -m er_commons.reporting_run --output "$(REPORT_OUTPUT)"

freeze-brisbane-sources: check-env
	uv run er-commons sources freeze \
		--spec configs/brisbane_baylands_2025_deir_sources_v1.json

verify-brisbane-sources: check-env
	uv run er-commons sources verify \
		--spec configs/brisbane_baylands_2025_deir_sources_v1.json

validate-collection-contract:
	uv run er-commons collections validate-contract \
		--schema benchmarks/er_bench/schemas/collection_processing/v2/collection_run_spec.schema.json \
		--fixtures benchmarks/er_bench/fixtures/collection_processing/v2

validate-response-inventory-contract:
	uv run python -m er_commons.response_inventory \
		--schema benchmarks/er_bench/schemas/response_inventory/v1/records.schema.json \
		--fixtures benchmarks/er_bench/fixtures/response_inventory/v1

validate-response-inventory-pilot-spec:
	uv run er-responses validate-spec \
		--run-spec configs/brisbane_baylands_2025_feir_task05c_pilot_v1.json

validate-response-inventory-complete-spec:
	uv run er-responses validate-spec \
		--run-spec configs/brisbane_baylands_2025_feir_task05d_complete_v2.json

validate-response-relationship-exact-spec:
	uv run er-responses validate-spec \
		--run-spec configs/brisbane_baylands_2025_feir_task05e_exact_v3.json

validate-response-relationship-review-spec:
	uv run er-responses validate-spec \
		--run-spec configs/brisbane_baylands_2025_feir_task05e_review_v4.json

build-response-relationship-review-pass: check-env
	uv run er-responses build \
		--run-spec configs/brisbane_baylands_2025_feir_task05e_review_v4.json

finalize-response-relationship-candidate: check-env
	@test -n "$(RELATIONSHIP_REVIEW_ROOT)" || (echo "RELATIONSHIP_REVIEW_ROOT=PATH is required"; exit 1)
	@test -n "$(QUALITY_REPORT)" || (echo "QUALITY_REPORT=PATH is required"; exit 1)
	uv run er-responses finalize-05e \
		--review-root "$(RELATIONSHIP_REVIEW_ROOT)" \
		--quality-report "$(QUALITY_REPORT)"

build-response-relationship-review: check-env
	@test -n "$(RELATIONSHIP_ROOT)" || (echo "RELATIONSHIP_ROOT=PATH is required"; exit 1)
	@test -n "$(SOURCE_RECORDS)" || (echo "SOURCE_RECORDS=PATH is required"; exit 1)
	@test -n "$(QUALIFICATION)" || (echo "QUALIFICATION=PATH is required"; exit 1)
	@test -n "$(RENDER_ROOT)" || (echo "RENDER_ROOT=PATH is required"; exit 1)
	@test -n "$(REVIEW_TOOL_ROOT)" || (echo "REVIEW_TOOL_ROOT=PATH is required"; exit 1)
	@test -n "$(SERVED_ROOT)" || (echo "SERVED_ROOT=PATH is required"; exit 1)
	uv run er-responses build-review \
		--relationship-root "$(RELATIONSHIP_ROOT)" \
		--source-records "$(SOURCE_RECORDS)" \
		--qualification "$(QUALIFICATION)" \
		--render-root "$(RENDER_ROOT)" \
		--output-root "$(REVIEW_TOOL_ROOT)" \
		--served-root "$(SERVED_ROOT)"

publish-document: check-env
	@test -n "$(DOCUMENT_SPEC)" || (echo "DOCUMENT_SPEC=PATH is required"; exit 1)
	@test -n "$(SOURCE_ID)" || (echo "SOURCE_ID=ID is required"; exit 1)
	uv run er-commons documents publish --document-spec "$(DOCUMENT_SPEC)" --source-id "$(SOURCE_ID)"

assemble-collection-handoff: check-env
	@test -n "$(COLLECTION_SPEC)" || (echo "COLLECTION_SPEC=PATH is required"; exit 1)
	uv run er-commons collections assemble-handoff --collection-spec "$(COLLECTION_SPEC)"

validate-collection-handoff: check-env
	@test -n "$(COLLECTION_ROOT)" || (echo "COLLECTION_ROOT=DIR is required"; exit 1)
	@test -n "$(SCOPE_ID)" || (echo "SCOPE_ID=ID is required"; exit 1)
	@test -n "$(SCHEMA)" || (echo "SCHEMA=FILE is required"; exit 1)
	uv run er-commons collections validate-handoff \
		--collection-root "$(COLLECTION_ROOT)" \
		--scope-id "$(SCOPE_ID)" \
		--schema "$(SCHEMA)"

# Use a fresh output directory; the exporter never overwrites a release.
export-pilot-case-citations: check-env
	@test -n "$(CASE_EXPORT_DIR)" || (echo "Set CASE_EXPORT_DIR to a fresh output directory"; exit 1)
	uv run python -m er_commons.pilot_case_export \
		--data-root "$(ER_COMMONS_DATA_ROOT)" \
		--review-status docs/specs/task07d_review_export_status.json \
		--claim-handoff docs/specs/task07c1_final_result.json \
		--output "$(CASE_EXPORT_DIR)"

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

type:
	uv run mypy src scripts/qualify_figure_caption_aliases.py

test: check-env
	uv run pytest

check: format-check lint type test

fix: lint-fix format

# Task 08A consumes exactly one accepted group; output paths must be fresh.
.PHONY: prepare-group-ranking publish-group-ranking validate-group-ranking
prepare-group-ranking: check-env
	@test -n "$(GROUPING_DIR)" -a -n "$(GROUPING_SHA256)" -a -n "$(GROUP)" -a -n "$(RANKING_INPUT)" || (echo "Set GROUPING_DIR, GROUPING_SHA256, GROUP, RANKING_INPUT"; exit 1)
	uv run python -m er_commons.group_ranking prepare \
		--data-root "$(ER_COMMONS_DATA_ROOT)" \
		--inventory-result docs/specs/task07a1_final_result.json \
		--grouping-directory "$(GROUPING_DIR)" --grouping-sha256 "$(GROUPING_SHA256)" \
		--group "$(GROUP)" --output "$(RANKING_INPUT)" $(if $(SOURCE_SUPPLEMENTS),--source-supplements "$(SOURCE_SUPPLEMENTS)",)

publish-group-ranking: check-env
	@test -n "$(RANKING_INPUT)" -a -n "$(RANKING_PROPOSAL)" -a -n "$(RANKING_OUTPUT)" || (echo "Set RANKING_INPUT, RANKING_PROPOSAL, RANKING_OUTPUT"; exit 1)
	uv run python -m er_commons.group_ranking publish \
		--input "$(RANKING_INPUT)" --proposal "$(RANKING_PROPOSAL)" \
		--prompt docs/prompts/task08a_ranking_v1.md --spec docs/specs/task08a_ranking_v1.md \
		--output "$(RANKING_OUTPUT)"

validate-group-ranking: check-env
	@test -n "$(RANKING_OUTPUT)" || (echo "Set RANKING_OUTPUT"; exit 1)
	uv run python -m er_commons.group_ranking validate --output "$(RANKING_OUTPUT)"

# Task 08B creates blank queues; accepted decisions require a saved human export.
.PHONY: prepare-group-selection export-group-selection
prepare-group-selection: check-env
	@test -n "$(RANKING_OUTPUT)" -a -n "$(RANKING_RESULT)" -a -n "$(SELECTION_OUTPUT)" || (echo "Set RANKING_OUTPUT, RANKING_RESULT, SELECTION_OUTPUT"; exit 1)
	uv run python -m er_commons.group_selection prepare \
		--ranking-root "$(RANKING_OUTPUT)" --result "$(RANKING_RESULT)" \
		--data-root "$(ER_COMMONS_DATA_ROOT)" --output "$(SELECTION_OUTPUT)"

export-group-selection: check-env
	@test -n "$(SELECTION_OUTPUT)" -a -n "$(NATIVE_EXPORT)" -a -n "$(PROJECT_ID)" -a -n "$(DECISIONS_OUTPUT)" || (echo "Set SELECTION_OUTPUT, NATIVE_EXPORT, PROJECT_ID, DECISIONS_OUTPUT"; exit 1)
	uv run python -m er_commons.group_selection export \
		--prepared "$(SELECTION_OUTPUT)" --native-export "$(NATIVE_EXPORT)" \
		--project-id "$(PROJECT_ID)" --output "$(DECISIONS_OUTPUT)" \
		$(if $(FINISH_CONFIRMATION),--finish-confirmation "$(FINISH_CONFIRMATION)",)

# Task 08C separates restricted extraction, comment-only review and saved decisions.
.PHONY: prepare-wording-input prepare-group-wording export-group-wording
prepare-wording-input: check-env
	@test -n "$(SELECTION_HANDOFF)" -a -n "$(HANDOFF_SHA256)" -a -n "$(WORDING_INPUT)" -a -n "$(COMMENT_IDS)" || (echo "Set SELECTION_HANDOFF, HANDOFF_SHA256, WORDING_INPUT, COMMENT_IDS"; exit 1)
	uv run python -m er_commons.group_wording_input \
		--handoff "$(SELECTION_HANDOFF)" --expected-handoff-sha256 "$(HANDOFF_SHA256)" \
		--data-root "$(ER_COMMONS_DATA_ROOT)" --output "$(WORDING_INPUT)" \
		$(foreach id,$(COMMENT_IDS),--comment-id "$(id)")

prepare-group-wording: check-env
	@test -n "$(WORDING_PACKET)" -a -n "$(WORDING_PROPOSAL)" -a -n "$(WORDING_OUTPUT)" || (echo "Set WORDING_PACKET, WORDING_PROPOSAL, WORDING_OUTPUT"; exit 1)
	uv run python -m er_commons.group_wording prepare \
		--packet "$(WORDING_PACKET)" --proposal "$(WORDING_PROPOSAL)" \
		--output "$(WORDING_OUTPUT)" --namespace dataset

export-group-wording: check-env
	@test -n "$(WORDING_OUTPUT)" -a -n "$(NATIVE_EXPORT)" -a -n "$(PROJECT_ID)" -a -n "$(REVIEWER_ID)" -a -n "$(DECISIONS_OUTPUT)" || (echo "Set WORDING_OUTPUT, NATIVE_EXPORT, PROJECT_ID, REVIEWER_ID, DECISIONS_OUTPUT"; exit 1)
	uv run python -m er_commons.group_wording export \
		--prepared "$(WORDING_OUTPUT)" --native-export "$(NATIVE_EXPORT)" \
		--project-id "$(PROJECT_ID)" --reviewer-id "$(REVIEWER_ID)" --output "$(DECISIONS_OUTPUT)"

# Current Task 08C uses explicit version-bound chat decisions.
.PHONY: validate-wording-chat export-wording-chat
validate-wording-chat: check-env
	@test -n "$(CHAT_JOURNAL)" -a -n "$(WORDING_PACKET)" -a -n "$(WORDING_PROPOSAL)" || (echo "Set CHAT_JOURNAL, WORDING_PACKET, WORDING_PROPOSAL"; exit 1)
	uv run python -m er_commons.group_wording_chat validate \
		--journal "$(CHAT_JOURNAL)" --packet "$(WORDING_PACKET)" --proposal "$(WORDING_PROPOSAL)" \
		--prompt docs/prompts/task08c_chat_review_v1.md $(if $(CHAT_PREVIOUS),--previous "$(CHAT_PREVIOUS)",)

export-wording-chat: check-env
	@test -n "$(CHAT_JOURNAL)" -a -n "$(WORDING_PACKET)" -a -n "$(WORDING_PROPOSAL)" -a -n "$(DECISIONS_OUTPUT)" || (echo "Set CHAT_JOURNAL, WORDING_PACKET, WORDING_PROPOSAL, DECISIONS_OUTPUT"; exit 1)
	uv run python -m er_commons.group_wording_chat export \
		--journal "$(CHAT_JOURNAL)" --packet "$(WORDING_PACKET)" --proposal "$(WORDING_PROPOSAL)" \
		--prompt docs/prompts/task08c_chat_review_v1.md --output "$(DECISIONS_OUTPUT)" \
		$(if $(CHAT_PREVIOUS),--previous "$(CHAT_PREVIOUS)",)

# Task 08D separates response proposals from exact saved human approvals.
.PHONY: prepare-group-claims export-group-claims
prepare-group-claims:
	uv run python -m er_commons.group_claims_workflow prepare \
		--packet "$(CLAIM_PACKET)" --proposal "$(CLAIM_PROPOSAL)" --output "$(CLAIM_PREPARED)"

export-group-claims:
	uv run python -m er_commons.group_claims_workflow export \
		--prepared "$(CLAIM_PREPARED)" --native "$(NATIVE_EXPORT)" \
		--identity "$(PROJECT_IDENTITY)" --current-project "$(CURRENT_PROJECT)" \
		--reviewer-id "$(REVIEWER_ID)" --output "$(CLAIM_EXPORT)" \
		$(if $(CLAIM_AUTHORIZATION),--authorization "$(CLAIM_AUTHORIZATION)",)

# Task 08A v2: shared order-only ranking and deterministic small-group bypass.
.PHONY: prepare-group-ranking-v2 prepare-small-group-order-v2 publish-group-ranking-v2 validate-group-ranking-v2
prepare-group-ranking-v2: check-env
	uv run python -m er_commons.group_ranking_v2 prepare \
		--data-root "$(ER_COMMONS_DATA_ROOT)" --inventory-result docs/specs/task07a1_final_result.json \
		--grouping-directory "$(GROUPING_DIR)" --grouping-sha256 "$(GROUPING_SHA256)" \
		--group "$(GROUP)" --output "$(RANKING_INPUT)"

prepare-small-group-order-v2: check-env
	uv run python -m er_commons.group_ranking_v2 prepare-small-order \
		--input "$(RANKING_INPUT)" --prompt docs/prompts/task08a_ranking_v2.md \
		--output "$(RANKING_PROPOSAL)"

publish-group-ranking-v2: check-env
	uv run python -m er_commons.group_ranking_v2 publish \
		--input "$(RANKING_INPUT)" --proposal "$(RANKING_PROPOSAL)" \
		--prompt docs/prompts/task08a_ranking_v2.md --spec docs/specs/task08a_ranking_v2.md \
		--output "$(RANKING_OUTPUT)"

validate-group-ranking-v2: check-env
	uv run python -m er_commons.group_ranking_v2 validate --output "$(RANKING_OUTPUT)"

# Task 08B setup only: no human selections or downstream authoring.
.PHONY: prepare-group-selection-batch
prepare-group-selection-batch: check-env
	@test -n "$(HANDOFF_INDEX)" -a -n "$(RANKING_RESULT)" -a -n "$(SETUP_OUTPUT)" -a -n "$(BATCH_REGISTER)" -a -n "$(LABEL_STUDIO_URL)" -a -n "$(LABEL_STUDIO_CREDENTIALS)"
	uv run python -m er_commons.group_selection_batch \
		--index "$(HANDOFF_INDEX)" --completion "$(RANKING_RESULT)" \
		--data-root "$(ER_COMMONS_DATA_ROOT)" --output "$(SETUP_OUTPUT)" \
		--register "$(BATCH_REGISTER)" --url "$(LABEL_STUDIO_URL)" \
		--credentials "$(LABEL_STUDIO_CREDENTIALS)"

# Combined Task 08C keeps full immutable predecessor chains and lazy proposals.
.PHONY: validate-combined-wording-chat export-combined-wording-chat
validate-combined-wording-chat: check-env
	uv run python -m er_commons.group_wording_combined_chat validate \
		--journal "$(CHAT_JOURNAL)" --packet "$(WORDING_PACKET)" --prompt "$(CHAT_PROMPT)" \
		$(foreach snapshot,$(CHAT_PREDECESSORS),--previous "$(snapshot)")

export-combined-wording-chat: check-env
	uv run python -m er_commons.group_wording_combined_chat export \
		--journal "$(CHAT_JOURNAL)" --packet "$(WORDING_PACKET)" --prompt "$(CHAT_PROMPT)" \
		$(foreach snapshot,$(CHAT_PREDECESSORS),--previous "$(snapshot)") \
		--output "$(DECISIONS_OUTPUT)"

# Combined Task 08D: source preparation and saved chat events have separate gates.
.PHONY: prepare-combined-claim-input assemble-combined-claims claim-chat
prepare-combined-claim-input: check-env
	@test -n "$(CLAIM_INPUT)"
	uv run python -m er_commons.group_claims_combined_input \
		--result docs/specs/task08c_combined_review_result.json \
		--data-root "$(ER_COMMONS_DATA_ROOT)" --output "$(CLAIM_INPUT)"

assemble-combined-claims:
	@test -n "$(CLAIM_BATCH)" -a -n "$(CLAIM_PREPARED)"
	uv run python -m er_commons.group_claims_batch \
		--root "$(CLAIM_BATCH)" --output "$(CLAIM_PREPARED)"

claim-chat:
	@test -n "$(CLAIM_QUEUE_REFERENCE)" -a -n "$(CLAIM_JOURNAL)" -a -n "$(CLAIM_ACTION)"
	uv run python -m er_commons.group_claims_chat_cli "$(CLAIM_ACTION)" \
		--queue-reference "$(CLAIM_QUEUE_REFERENCE)" --journal "$(CLAIM_JOURNAL)" \
		$(if $(CLAIM_EVENT),--event "$(CLAIM_EVENT)",) \
		$(if $(CLAIM_EXPORT),--output "$(CLAIM_EXPORT)",)

# Task 08F preparation only; a sealed batch is never mutated by these commands.
.PHONY: run-answer-preparation seal-answer-preparation verify-answer-preparation
run-answer-preparation: check-env
	@test -n "$(ANSWER_BATCH)"
	uv run python -m er_commons.group_answer_batch run "$(ANSWER_BATCH)"

seal-answer-preparation: check-env
	@test -n "$(ANSWER_BATCH)"
	uv run python -m er_commons.group_answer_batch seal "$(ANSWER_BATCH)"

verify-answer-preparation: check-env
	@test -n "$(ANSWER_BATCH)"
	uv run python -m er_commons.group_answer_batch verify "$(ANSWER_BATCH)"

# Task 09A source-only synthetic authoring; no judge or target execution.
.PHONY: run-synthetic-answers publish-synthetic-answers verify-synthetic-answers
run-synthetic-answers: check-env
	@test -n "$(SYNTHETIC_BATCH)"
	uv run python -m er_commons.synthetic_batch run "$(SYNTHETIC_BATCH)" \
		--workers $(or $(SYNTHETIC_WORKERS),1)

publish-synthetic-answers: check-env
	@test -n "$(SYNTHETIC_BATCH)" -a -n "$(SYNTHETIC_REVIEW)"
	uv run python -m er_commons.synthetic_publication publish "$(SYNTHETIC_BATCH)" \
		--review "$(SYNTHETIC_REVIEW)"

verify-synthetic-answers: check-env
	@test -n "$(SYNTHETIC_BATCH)"
	uv run python -m er_commons.synthetic_publication verify "$(SYNTHETIC_BATCH)"

# Task 09B infrastructure qualification only, not the later semantic judges.
.PHONY: prepare-judge-qualification
prepare-judge-qualification: check-env
	@test -n "$(QUALIFICATION_PACKETS)" || { \
		echo 'Set QUALIFICATION_PACKETS to the output directory for prepared packets.' >&2; exit 2; }
	uv run python -m er_commons.judge_qualification_packets prepare \
		--result docs/specs/task09a_final_result.json --output "$(QUALIFICATION_PACKETS)"

# Task 09C deterministic packet construction; explicit selections, no model calls.
.PHONY: prepare-judge-packets
prepare-judge-packets: check-env
	@test -n "$(JUDGE_PACKETS)" -a -n "$(JUDGE_SELECTIONS)" || { \
		echo 'Set JUDGE_PACKETS and JUDGE_SELECTIONS (--variant-id ID / --control-case ID).' >&2; exit 2; }
	uv run python -m er_commons.judge_packet_publication \
		--result docs/specs/task09a_final_result.json \
		--release docs/specs/task08h_final_result.json \
		--output "$(JUDGE_PACKETS)" $(JUDGE_SELECTIONS)

# Task 09D saved-answer metrics; Inspect owns execution and logs, no inference.
.PHONY: evaluate-automatic-metrics
evaluate-automatic-metrics: check-env
	@test -n "$(METRIC_SAMPLES)" -a -n "$(METRIC_LOG_DIR)" || { \
		echo 'Set METRIC_SAMPLES (prepared JSON array) and METRIC_LOG_DIR (external directory).' >&2; exit 2; }
	uv run python -m er_commons.automatic_metric_inspect \
		"$(METRIC_SAMPLES)" --log-dir "$(METRIC_LOG_DIR)"

# Native Inspect judges: selected configurations, explicit external log location.
# Inspect CLI options control sample limits, epochs, concurrency and soft budgets.
JUDGE_EPOCHS ?= 1
.PHONY: evaluate-no-answer evaluate-point-grounding evaluate-adequacy
evaluate-no-answer: check-env
	@test -n "$(JUDGE_LOG_DIR)" || (echo "Set JUDGE_LOG_DIR to an external run directory"; exit 1)
	uv run --env-file "$(ENV_FILE)" inspect eval src/er_commons/no_answer_inspect.py@no_answer_full \
		$(if $(JUDGE_CONDITION),-T condition_id=$(JUDGE_CONDITION)) \
		--epochs $(JUDGE_EPOCHS) --log-dir "$(JUDGE_LOG_DIR)" $(JUDGE_OPTIONS)

evaluate-point-grounding: check-env
	@test -n "$(JUDGE_LOG_DIR)" || (echo "Set JUDGE_LOG_DIR to an external run directory"; exit 1)
	uv run --env-file "$(ENV_FILE)" inspect eval src/er_commons/point_grounding_inspect.py@point_grounding_full \
		$(if $(JUDGE_CONDITION),-T condition_id=$(JUDGE_CONDITION)) \
		--epochs $(JUDGE_EPOCHS) --log-dir "$(JUDGE_LOG_DIR)" $(JUDGE_OPTIONS)

evaluate-adequacy: check-env
	@test -n "$(JUDGE_LOG_DIR)" || (echo "Set JUDGE_LOG_DIR to an external run directory"; exit 1)
	@test "$(JUDGE_COMPONENT)" = C -o "$(JUDGE_COMPONENT)" = S || (echo "Set JUDGE_COMPONENT=C or S"; exit 1)
	uv run --env-file "$(ENV_FILE)" inspect eval src/er_commons/adequacy_inspect.py@adequacy \
		-T component=$(JUDGE_COMPONENT) -T panel=full_development \
		$(if $(JUDGE_CONDITION),-T condition_id=$(JUDGE_CONDITION)) \
		--epochs $(JUDGE_EPOCHS) --log-dir "$(JUDGE_LOG_DIR)" $(JUDGE_OPTIONS)

# Task 10 is offline preparation only; the release is explicit and output is external.
.PHONY: prepare-evidence-only validate-evidence-only
prepare-evidence-only: check-env
	@test -n "$(EVIDENCE_RELEASE)" -a -n "$(EVIDENCE_OUTPUT)" || (echo "Set EVIDENCE_RELEASE and EVIDENCE_OUTPUT"; exit 1)
	uv run python -m er_commons.evidence_only prepare --release "$(EVIDENCE_RELEASE)" --output "$(EVIDENCE_OUTPUT)"

validate-evidence-only: check-env
	@test -n "$(EVIDENCE_OUTPUT)" || (echo "Set EVIDENCE_OUTPUT"; exit 1)
	uv run python -m er_commons.evidence_only validate --output "$(EVIDENCE_OUTPUT)"

# Task 11B: one fixed initial-three smoke, no judges or prompt iteration.
.PHONY: generate-luna-smoke
generate-luna-smoke: check-env
	@test -n "$(GENERATION_OUTPUT)" || (echo "Set GENERATION_OUTPUT to a fresh external run directory"; exit 1)
	uv run --env-file "$(ENV_FILE)" python -m er_commons.target_generation --output "$(GENERATION_OUTPUT)" $(GENERATION_OPTIONS)

.PHONY: evaluate-development-smoke
evaluate-development-smoke: check-env
	@test -n "$(EVALUATION_OUTPUT)" || (echo "Set EVALUATION_OUTPUT to a fresh external run directory"; exit 1)
	uv run --env-file "$(ENV_FILE)" python -m er_commons.development_evaluation_run --output "$(EVALUATION_OUTPUT)" $(EVALUATION_OPTIONS)

# Task15Y guarded phases; prepare validates inputs offline, run dispatches one phase.
.PHONY: prepare-support-coverage-pilot prepare-support-coverage-all19
.PHONY: run-support-coverage-pilot run-support-coverage-all19
prepare-support-coverage-pilot prepare-support-coverage-all19: check-env
	@test -n "$(COVERAGE_ROOT)" || (echo "Set COVERAGE_ROOT to the frozen external coverage run directory"; exit 1)
	uv run python -m er_commons.required_support_coverage_run --root "$(COVERAGE_ROOT)" --phase prepare

run-support-coverage-pilot run-support-coverage-all19: check-env
	@test -n "$(COVERAGE_ROOT)" || (echo "Set COVERAGE_ROOT to the frozen external coverage run directory"; exit 1)
	@test "$(COVERAGE_PHASE)" = checkpoint -o "$(COVERAGE_PHASE)" = remainder || (echo "Set COVERAGE_PHASE=checkpoint or remainder"; exit 1)
	uv run --env-file "$(ENV_FILE)" python -m er_commons.required_support_coverage_run --root "$(COVERAGE_ROOT)" --phase "$(COVERAGE_PHASE)"
