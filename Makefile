.DEFAULT_GOAL := help

ENV_FILE := .env
-include $(ENV_FILE)
export ER_COMMONS_DATA_ROOT

.PHONY: help bootstrap sync check-env data-dirs about paths freeze-brisbane-sources \
	verify-brisbane-sources format format-check lint lint-fix type test check fix

help:
	@echo "ER Commons commands:"
	@echo "  make bootstrap   Install dependencies and create external data directories"
	@echo "  make about       Describe the current project scope"
	@echo "  make paths       Show the configured external data/artifact paths"
	@echo "  make freeze-brisbane-sources  Freeze the reviewed Brisbane source release"
	@echo "  make verify-brisbane-sources  Verify the frozen release without network access"
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
