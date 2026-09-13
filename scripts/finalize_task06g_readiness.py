"""Validate terminal Task 06G evidence and publish readiness completion last."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.task06g.finalization import finalize_readiness


def main() -> None:
    """Use only explicit execution and finalization attempt roots."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution-spec", type=Path, required=True)
    parser.add_argument("--execution-attempt-root", type=Path, required=True)
    parser.add_argument("--finalization-attempt-root", type=Path, required=True)
    parser.add_argument("--replay-root", type=Path, required=True)
    parser.add_argument("--finalization-amendment", type=Path)
    args = parser.parse_args()
    finalize_readiness(
        args.execution_spec,
        args.execution_attempt_root,
        args.finalization_attempt_root,
        args.replay_root,
        finalization_amendment=args.finalization_amendment,
    )


if __name__ == "__main__":
    main()
