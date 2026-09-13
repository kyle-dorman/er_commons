"""Seal source-free Task 06G recovery observations before supervisor launch."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.task06g.packets import preflight_prelaunch


def main() -> None:
    """Write one fresh no-clobber prelaunch recovery receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation-spec", type=Path, required=True)
    parser.add_argument("--replay-root", type=Path, required=True)
    parser.add_argument("--execution-attempt-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    preflight_prelaunch(
        args.generation_spec,
        args.replay_root,
        args.execution_attempt_root,
        args.output_root,
    )


if __name__ == "__main__":
    main()
