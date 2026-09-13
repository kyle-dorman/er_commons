"""Generate or verify tracked source-free collection-only Task 06G controls."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.task06g.collection_generation import generate_collection_configs


def main() -> None:
    """Require an explicit repository root; never create external replay artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate_collection_configs(args.repository_root, check=args.check)


if __name__ == "__main__":
    main()
