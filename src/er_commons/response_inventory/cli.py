"""Isolated command-line interface for the curator-only response inventory."""

from __future__ import annotations

import argparse
import json
import logging
import os
from collections.abc import Sequence
from pathlib import Path

from er_commons.response_inventory.run_spec import (
    load_response_inventory_run_spec,
    verify_repository_bindings,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Validate a portable specification or build its explicitly bounded pilot."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate-spec")
    validate_parser.add_argument("--run-spec", required=True, type=Path)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--run-spec", required=True, type=Path)
    build_parser.add_argument(
        "--review-dispositions",
        type=Path,
        help="JSON object mapping required physical-page numbers to accepted/requires_followup",
    )
    arguments = parser.parse_args(argv)
    repository_root = Path(__file__).resolve().parents[3]

    if arguments.command == "validate-spec":
        spec, digest = load_response_inventory_run_spec(arguments.run_spec.resolve())
        verify_repository_bindings(spec, repository_root)
        print("response_inventory_run_spec=valid")
        print(f"run_spec_sha256={digest}")
        print(f"declared_pages={spec.declared_page_count}")
        return 0

    artifact_root_value = os.environ.get("ER_COMMONS_DATA_ROOT")
    if not artifact_root_value:
        parser.error("ER_COMMONS_DATA_ROOT must be set for build")
    from er_commons.response_inventory.workflow import build_pilot

    dispositions = None
    if arguments.review_dispositions is not None:
        payload = json.loads(arguments.review_dispositions.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            parser.error("--review-dispositions must contain one JSON object")
        dispositions = {int(page): str(value) for page, value in payload.items()}
    result = build_pilot(
        arguments.run_spec.resolve(),
        repository_root,
        Path(artifact_root_value).resolve(),
        visual_dispositions=dispositions,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
