.DEFAULT_GOAL := help

ENV_FILE := .env
-include $(ENV_FILE)
export ER_COMMONS_DATA_ROOT

.PHONY: help bootstrap sync check-env data-dirs about paths freeze-brisbane-sources \
	verify-brisbane-sources run-document-review run-table-review run-table-first-600 \
	run-complete-document run-hierarchy-evaluation run-canonical-document \
	run-semantic-document run-cross-references \
	validate-extraction-contract \
	format format-check lint lint-fix type test check fix

help:
	@echo "ER Commons commands:"
	@echo "  make bootstrap   Install dependencies and create external data directories"
	@echo "  make about       Describe the current project scope"
	@echo "  make paths       Show the configured external data/artifact paths"
	@echo "  make freeze-brisbane-sources  Freeze the reviewed Brisbane source release"
	@echo "  make verify-brisbane-sources  Verify the frozen release without network access"
	@echo "  make run-document-review      Run the clean ten-page document parser"
	@echo "  make run-complete-document    Run or verify the Task 03C Appendix P producer"
	@echo "  make run-hierarchy-evaluation Run the Task 03E repeated producer gate"
	@echo "  make run-canonical-document   Materialize or verify the Task 03D candidate"
	@echo "  make run-semantic-document    Materialize Appendix P semantic structure"
	@echo "  make run-cross-references     Materialize Appendix P cross-references"
	@echo "  make validate-extraction-contract  Validate Task 03F.1 offline fixtures"
	@echo "  make run-table-review         Run or resume the ten-page table review"
	@echo "  make run-table-first-600      Run or resume the first-600-page table validation"
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

run-document-review: check-env
	uv run er-commons documents run-review

run-complete-document: check-env
	uv run er-commons documents run-complete

run-hierarchy-evaluation: check-env
	uv run er-commons documents evaluate-hierarchy

run-canonical-document: check-env
	uv run er-commons canonicalize run-document

run-semantic-document: check-env
	uv run er-commons canonicalize run-semantic-document

run-cross-references: check-env
	uv run er-commons canonicalize run-cross-references

validate-extraction-contract:
	uv run er-commons extraction validate-contract \
		--schema benchmarks/er_bench/schemas/corpus_extraction/v1/records.schema.json \
		--fixtures benchmarks/er_bench/fixtures/corpus_extraction/v1

run-table-review: check-env
	uv run er-commons tables run-review

run-table-first-600: check-env
	uv run er-commons tables run-first-600

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
