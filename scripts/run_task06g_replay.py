"""Run the exact reviewed Task 06G command sequence."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.task06g.driver import run_replay


def main() -> None:
    """Require and verify the immutable launch or resume binding."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution-spec", type=Path, required=True)
    parser.add_argument("--binding-path", type=Path, required=True)
    parser.add_argument("--binding-sha256", required=True)
    args = parser.parse_args()
    run_replay(args.execution_spec, args.binding_path, args.binding_sha256)


if __name__ == "__main__":
    main()
