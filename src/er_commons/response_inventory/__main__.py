"""Source-free command entrypoint for the response-inventory contract gate."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from er_commons.response_inventory import validate_contract_fixtures


def main(argv: Sequence[str] | None = None) -> int:
    """Validate one schema and fixture directory without loading project settings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--fixtures", required=True, type=Path)
    arguments = parser.parse_args(argv)
    count = validate_contract_fixtures(arguments.schema.resolve(), arguments.fixtures.resolve())
    print("response_inventory_contract=valid")
    print(f"fixtures={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
