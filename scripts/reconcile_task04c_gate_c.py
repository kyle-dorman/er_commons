#!/usr/bin/env python3
"""Publish the source-free Task 04C TOC text and navigation-link view."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from er_commons.navigation_overlay.reconciliation import (
    GateCReconciliationRequest,
    prepare_and_publish_gate_c,
)
from er_commons.settings import load_settings


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the checkout root and publish or verify Gate C."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    if not repo_root.is_dir():
        parser.error(f"repository root is not a directory: {repo_root}")
    publication = prepare_and_publish_gate_c(
        GateCReconciliationRequest(data_root=load_settings().data_root, repo_root=repo_root)
    )
    print(f"navigation_gate_c={publication}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
