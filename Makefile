.DEFAULT_GOAL := help

ENV_FILE := .env
-include $(ENV_FILE)
export ER_COMMONS_DATA_ROOT

.PHONY: help bootstrap sync check-env data-dirs about paths freeze-brisbane-sources \
	verify-brisbane-sources validate-collection-contract publish-document \
	assemble-collection-handoff validate-collection-handoff \
	validate-response-inventory-contract validate-response-inventory-pilot-spec \
	validate-response-inventory-complete-spec validate-response-relationship-review-spec \
	build-response-relationship-review-pass build-response-relationship-review \
	finalize-response-relationship-candidate \
	format format-check lint lint-fix type test check fix

help:
	@echo "ER Commons commands:"
	@echo "  make bootstrap   Install dependencies and create external data directories"
	@echo "  make about       Describe the current project scope"
	@echo "  make paths       Show the configured external data/artifact paths"
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

TASK05E_REVIEW_ROOT := $(ER_COMMONS_DATA_ROOT)/pipelines/brisbane_baylands/task_05_response_inventory/working/05e/reviewpassv1-df6e04a7f24a79ad15dbb12f0796edcd9c9348bdd1f1db94093dd800e4091ca1

finalize-response-relationship-candidate: check-env
	uv run er-responses finalize-05e \
		--review-root "$(TASK05E_REVIEW_ROOT)" \
		--quality-report configs/brisbane_baylands_2025_feir_task05e_code_quality_v1.json

RELATIONSHIP_ROOT ?= $(ER_COMMONS_DATA_ROOT)/pipelines/brisbane_baylands/task_05_response_inventory/working/05e/baselinev1-50ae2f7de5f28e882e62627db103e03f0059677fcdfc1e1f8be3a9bf5232b778
REVIEW_TOOL_ROOT ?= $(ER_COMMONS_DATA_ROOT)/pipelines/brisbane_baylands/task_05_response_inventory/working/05e/review_tool_gate1_v1

build-response-relationship-review: check-env
	uv run er-responses build-review \
		--relationship-root "$(RELATIONSHIP_ROOT)" \
		--source-records "$(ER_COMMONS_DATA_ROOT)/pipelines/brisbane_baylands/task_05_response_inventory/working/05d/revisionv1-857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030/inventory/source_records.jsonl" \
		--qualification "$(ER_COMMONS_DATA_ROOT)/pipelines/brisbane_baylands/task_05_response_inventory/working/05d/revisionv1-857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030/diagnostics/qualification.json" \
		--render-root "$(ER_COMMONS_DATA_ROOT)/pipelines/brisbane_baylands/task_05_response_inventory/working/05d/cache/857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030/qualification" \
		--output-root "$(REVIEW_TOOL_ROOT)" \
		--served-root "$(ER_COMMONS_DATA_ROOT)/pipelines/brisbane_baylands/task_05_response_inventory"

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

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

type:
	uv run mypy src

test: check-env
	uv run pytest

check: format-check lint type test

fix: lint-fix format
