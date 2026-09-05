#!/usr/bin/env python3
"""Publish the source-free Task 04C Gate A navigation-overlay plan."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from er_commons.navigation_overlay import GateAPreparationRequest, prepare_and_publish_gate_a
from er_commons.settings import load_settings


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the explicit checkout root and publish or verify Gate A."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="Checkout containing the versioned navigation-overlay schemas and code.",
    )
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    if not repo_root.is_dir():
        parser.error(f"repository root is not a directory: {repo_root}")
    publication = prepare_and_publish_gate_a(
        GateAPreparationRequest(
            data_root=load_settings().data_root,
            repo_root=repo_root,
        )
    )
    print(f"navigation_gate_a={publication}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
