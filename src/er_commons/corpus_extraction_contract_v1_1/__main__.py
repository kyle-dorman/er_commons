"""Command-line entry point for the Gate A offline contract gate."""

from pathlib import Path

from er_commons.corpus_extraction_contract_v1_1.fixture_validation import (
    validate_fixture_directory,
)


def main() -> None:
    """Run the checked v1.1 schema, fixture, and identity validations."""
    root = Path.cwd()
    validate_fixture_directory(
        root / "benchmarks/er_bench/schemas/corpus_extraction/v1_1/records.schema.json",
        root / "benchmarks/er_bench/fixtures/corpus_extraction/v1_1",
    )
    print("restartable_extraction_contract_v1_1=valid")


if __name__ == "__main__":
    main()
