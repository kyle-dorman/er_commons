.DEFAULT_GOAL := help

ENV_FILE := .env
-include $(ENV_FILE)
export ER_COMMONS_DATA_ROOT

.PHONY: help bootstrap sync check-env data-dirs about paths freeze-brisbane-sources \
	verify-brisbane-sources validate-collection-contract publish-document \
	assemble-collection-handoff validate-collection-handoff \
	format format-check lint lint-fix type test check fix

help:
	@echo "ER Commons commands:"
	@echo "  make bootstrap   Install dependencies and create external data directories"
	@echo "  make about       Describe the current project scope"
	@echo "  make paths       Show the configured external data/artifact paths"
	@echo "  make freeze-brisbane-sources  Freeze the reviewed Brisbane source release"
	@echo "  make verify-brisbane-sources  Verify the frozen release without network access"
	@echo "  make validate-collection-contract  Validate the current v2 contract fixtures"
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
