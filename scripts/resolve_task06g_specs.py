"""Resolve one allowlisted Task 06G concrete-spec phase."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.task06g.phases import resolve_phase


def main() -> None:
    """Parse an explicit phase request and publish or exactly reuse it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation-spec", type=Path, required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--resume-existing", action="store_true")
    parser.add_argument("--prelaunch-recovery-receipt", type=Path)
    args = parser.parse_args()
    resolve_phase(
        args.generation_spec,
        args.phase,
        args.output_root,
        resume_existing=args.resume_existing,
        prelaunch_recovery_receipt=args.prelaunch_recovery_receipt,
    )


if __name__ == "__main__":
    main()
