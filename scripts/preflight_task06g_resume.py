"""Validate a preserved Task 06G attempt and seal fresh resume accounting."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.task06g.packets import preflight_resume


def main() -> None:
    """Write one explicit no-clobber resume receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution-spec", type=Path, required=True)
    parser.add_argument("--replay-root", type=Path, required=True)
    parser.add_argument("--prior-attempt-root", type=Path, required=True)
    parser.add_argument("--next-attempt-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    preflight_resume(
        args.execution_spec,
        args.replay_root,
        args.prior_attempt_root,
        args.next_attempt_root,
        args.output_root,
    )


if __name__ == "__main__":
    main()
