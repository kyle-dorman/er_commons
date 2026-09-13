"""Generate or check current document configs from an explicit request."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from er_commons.document_publication.config_generation.task06g_generation import (
    check_task06g_generation,
)
from er_commons.document_publication.config_generation.workflow import generate_document_configs


def main() -> None:
    """Require a generation spec; never select corpus or version from environment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation-spec", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = json.loads(args.generation_spec.read_bytes())
    if value.get("schema_version") == "er_commons.task06g_generation.v1":
        if not args.check:
            raise ValueError("Task 06G generation recipes are frozen check-only inputs")
        check_task06g_generation(args.generation_spec)
    else:
        generate_document_configs(args.generation_spec, check=args.check)


if __name__ == "__main__":
    main()
