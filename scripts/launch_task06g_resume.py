"""Launch one Task 06G resume from an exact sealed receipt."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.task06g.launch import launch_resume


def main() -> None:
    """Verify the accepted receipt and dispatch its fresh attempt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume-receipt", type=Path, required=True)
    args = parser.parse_args()
    launch_resume(args.resume_receipt)


if __name__ == "__main__":
    main()
