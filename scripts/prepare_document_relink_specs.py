"""Prepare document relink contracts from an explicit preparation specification."""

import argparse
from pathlib import Path

from er_commons.artifact_verification import VerificationBudget
from er_commons.document_records.document_references.preparation_spec import load_preparation_spec
from er_commons.document_records.document_references.spec_preparation import prepare_specs


def main() -> None:
    """Validate the explicit invocation before generating any contract."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation-spec", required=True, type=Path)
    args = parser.parse_args()
    budget = VerificationBudget()
    prepare_specs(load_preparation_spec(args.preparation_spec, budget=budget), budget=budget)


if __name__ == "__main__":
    main()
