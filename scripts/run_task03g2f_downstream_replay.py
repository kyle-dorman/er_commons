"""CLI for the bounded Task 03G.2f downstream replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from er_commons.settings import load_settings
from er_commons.task03g2f_replay.config import DEFAULT_RETAINED_SCOPE_ID, ReplayPaths
from er_commons.task03g2f_replay.workflow import Task03G2FReplay


def main() -> None:
    """Parse explicit roots and run the reviewable application service."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="checkout containing the reviewed Task 03G.2 configurations",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="artifact root; defaults to ER_COMMONS_DATA_ROOT from project settings",
    )
    parser.add_argument(
        "--retained-scope-id",
        default=DEFAULT_RETAINED_SCOPE_ID,
        help="immutable pre-repair scope used as the replay source",
    )
    args = parser.parse_args()
    paths = ReplayPaths(
        project_root=args.project_root.resolve(),
        data_root=(args.data_root or load_settings().data_root).resolve(),
        retained_scope_id=args.retained_scope_id,
    )
    outcome = Task03G2FReplay(paths).execute()
    print(json.dumps(outcome.report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
