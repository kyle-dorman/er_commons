"""Isolated command-line interface for the curator-only response inventory."""

from __future__ import annotations

import argparse
import json
import logging
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from er_commons.response_inventory.run_spec import (
    load_response_inventory_run_spec,
    verify_repository_bindings,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Validate or run an explicitly bounded Task 05C or 05D specification."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    repository_root = Path(__file__).resolve().parents[3]

    if arguments.command == "validate-spec":
        return _validate_spec(arguments.run_spec, repository_root)
    artifact_root = _artifact_root(parser)
    if arguments.command == "accept":
        return _accept_candidate(arguments, artifact_root)
    return _build_inventory(arguments, parser, repository_root, artifact_root)


def _build_parser() -> argparse.ArgumentParser:
    """Define the small public command surface independently from dispatch."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate-spec")
    validate_parser.add_argument("--run-spec", required=True, type=Path)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--run-spec", required=True, type=Path)
    build_parser.add_argument(
        "--review-dispositions",
        type=Path,
        help="JSON object mapping required physical pages to stage-specific decisions",
    )
    accept_parser = subparsers.add_parser("accept")
    accept_parser.add_argument("--candidate-root", required=True, type=Path)
    accept_parser.add_argument("--accepted-by", required=True)
    accept_parser.add_argument("--accepted-at", required=True)
    return parser


def _validate_spec(run_spec: Path, repository_root: Path) -> int:
    """Validate one source-free run specification and report its exact identity."""
    spec, digest = load_response_inventory_run_spec(run_spec.resolve())
    verify_repository_bindings(spec, repository_root)
    print("response_inventory_run_spec=valid")
    print(f"run_spec_sha256={digest}")
    print(f"declared_pages={spec.declared_page_count}")
    return 0


def _artifact_root(parser: argparse.ArgumentParser) -> Path:
    """Resolve the required external root without inventing a default."""
    artifact_root_value = os.environ.get("ER_COMMONS_DATA_ROOT")
    if not artifact_root_value:
        parser.error("ER_COMMONS_DATA_ROOT must be set for build or acceptance")
    return Path(artifact_root_value).resolve()


def _accept_candidate(arguments: argparse.Namespace, artifact_root: Path) -> int:
    """Run the separately authorized acceptance transition."""
    from er_commons.response_inventory.acceptance import publish_task05d_acceptance

    result = publish_task05d_acceptance(
        arguments.candidate_root,
        artifact_root,
        accepted_by=arguments.accepted_by,
        accepted_at=arguments.accepted_at,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def _build_inventory(
    arguments: argparse.Namespace,
    parser: argparse.ArgumentParser,
    repository_root: Path,
    artifact_root: Path,
) -> int:
    """Dispatch one stage after validating its distinct review-decision shape."""
    spec, _digest = load_response_inventory_run_spec(arguments.run_spec.resolve())
    if spec.task_stage == "05d":
        from er_commons.response_inventory.full_workflow import build_complete_inventory

        dispositions = _load_review_dispositions(
            arguments.review_dispositions, parser, decision_objects=True
        )
        result = build_complete_inventory(
            arguments.run_spec.resolve(),
            repository_root,
            artifact_root,
            visual_dispositions=dispositions,
        )
    else:
        from er_commons.response_inventory.workflow import build_pilot

        dispositions = _load_review_dispositions(
            arguments.review_dispositions, parser, decision_objects=False
        )
        result = build_pilot(
            arguments.run_spec.resolve(),
            repository_root,
            artifact_root,
            visual_dispositions=dispositions,
        )
    print(json.dumps(result, sort_keys=True))
    return 0


def _load_review_dispositions(
    path: Path | None,
    parser: argparse.ArgumentParser,
    *,
    decision_objects: bool,
) -> dict[int, Any] | None:
    """Load page-keyed JSON and localize malformed keys or stage value shapes."""
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        parser.error(f"cannot read --review-dispositions: {error}")
    if not isinstance(payload, dict):
        parser.error("--review-dispositions must contain one JSON object")
    try:
        dispositions = {int(page): value for page, value in payload.items()}
    except (TypeError, ValueError):
        parser.error("--review-dispositions page keys must be integers")
    if decision_objects:
        if not all(
            isinstance(value, dict)
            and all(isinstance(key, str) and isinstance(item, str) for key, item in value.items())
            for value in dispositions.values()
        ):
            parser.error("05D review dispositions must contain string-valued decision objects")
    elif not all(isinstance(value, str) for value in dispositions.values()):
        parser.error("05C review dispositions must map pages to status strings")
    return dispositions


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
