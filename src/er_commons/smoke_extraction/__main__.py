"""Command-line entrypoint for the diagnostic-only Task 03G.1 smoke."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.settings import load_settings
from er_commons.smoke_extraction import run_smoke


def main() -> None:
    """Run one explicit smoke specification and print its summary path."""
    parser = argparse.ArgumentParser(
        description="Run a bounded-page diagnostic without complete-document semantics."
    )
    parser.add_argument(
        "--spec",
        type=Path,
        required=True,
        help="Checked-in Task 03G.1 smoke specification.",
    )
    arguments = parser.parse_args()
    if not arguments.spec.is_file():
        parser.error(f"smoke specification is not a readable file: {arguments.spec}")
    summary = run_smoke(load_settings().data_root, arguments.spec)
    print(f"smoke_summary={summary}")


if __name__ == "__main__":
    main()
