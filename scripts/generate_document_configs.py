"""Generate or check current document configs from an explicit request."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.document_publication.config_generation.workflow import generate_document_configs


def main() -> None:
    """Require a generation spec; never select corpus or version from environment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation-spec", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate_document_configs(args.generation_spec, check=args.check)


if __name__ == "__main__":
    main()
