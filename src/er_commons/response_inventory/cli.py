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
    ResponseRelationshipReviewRunSpecV4,
    load_response_inventory_run_spec,
    verify_repository_bindings,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Validate or run an explicitly bounded Task 05 response specification."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    repository_root = Path(__file__).resolve().parents[3]

    if arguments.command.endswith("-05g") or (
        arguments.command in {"validate-spec", "build"} and _is_reference_replay(arguments.run_spec)
    ):
        return _dispatch_05g(arguments, parser, repository_root)

    if arguments.command == "validate-spec":
        return _validate_spec(arguments.run_spec, repository_root)
    artifact_root = _artifact_root(parser)
    if arguments.command == "accept":
        return _accept_candidate(arguments, artifact_root)
    if arguments.command == "accept-05e":
        return _accept_05e_candidate(arguments, repository_root, artifact_root)
    if arguments.command == "finalize-05e":
        return _finalize_05e(arguments, repository_root, artifact_root)
    if arguments.command == "build-review":
        return _build_review(arguments, artifact_root)
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
    accept_05e_parser = subparsers.add_parser(
        "accept-05e", help="accept one unchanged terminal Task 05E candidate"
    )
    accept_05e_parser.add_argument("--candidate-root", required=True, type=Path)
    accept_05e_parser.add_argument("--accepted-by", required=True)
    accept_05e_parser.add_argument("--accepted-at", required=True)
    finalize_parser = subparsers.add_parser(
        "finalize-05e", help="close one reviewed source-free Task 05E candidate"
    )
    finalize_parser.add_argument("--review-root", required=True, type=Path)
    finalize_parser.add_argument("--quality-report", required=True, type=Path)
    review_parser = subparsers.add_parser(
        "build-review", help="build a read-only lazy Task 05E relationship-review page"
    )
    review_parser.add_argument("--relationship-root", required=True, type=Path)
    review_parser.add_argument("--source-records", required=True, type=Path)
    review_parser.add_argument("--qualification", required=True, type=Path)
    review_parser.add_argument("--render-root", required=True, type=Path)
    review_parser.add_argument("--output-root", required=True, type=Path)
    review_parser.add_argument("--served-root", required=True, type=Path)
    _add_05g_parsers(subparsers)
    build_parser.add_argument("--attempt", type=int, default=1)
    build_parser.add_argument("--resume-from", type=int)
    return parser


def _validate_spec(run_spec: Path, repository_root: Path) -> int:
    """Validate one source-free run specification and report its exact identity."""
    spec, digest = load_response_inventory_run_spec(run_spec.resolve())
    verify_repository_bindings(spec, repository_root)
    print("response_inventory_run_spec=valid")
    print(f"run_spec_sha256={digest}")
    print(f"task_stage={spec.task_stage}")
    if hasattr(spec, "declared_page_count"):
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


def _build_review(arguments: argparse.Namespace, artifact_root: Path) -> int:
    """Build a read-only Task 05E review cache from accepted source-free artifacts."""
    from er_commons.response_inventory.review_tool import build_relationship_review_tool

    for name in (
        "relationship_root",
        "source_records",
        "qualification",
        "render_root",
        "output_root",
        "served_root",
    ):
        path = getattr(arguments, name).resolve()
        if not path.is_relative_to(artifact_root):
            raise ValueError(f"--{name.replace('_', '-')} escapes ER_COMMONS_DATA_ROOT")
    result = build_relationship_review_tool(
        relationship_root=arguments.relationship_root,
        source_records_path=arguments.source_records,
        qualification_path=arguments.qualification,
        render_root=arguments.render_root,
        output_root=arguments.output_root,
        served_root=arguments.served_root,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def _accept_05e_candidate(
    arguments: argparse.Namespace,
    repository_root: Path,
    artifact_root: Path,
) -> int:
    """Run the explicit adjacent-pointer acceptance transition for Task 05E."""
    from er_commons.response_inventory.relationship_candidate import (
        publish_task05e_acceptance,
    )

    result = publish_task05e_acceptance(
        arguments.candidate_root,
        artifact_root,
        repository_root,
        accepted_by=arguments.accepted_by,
        accepted_at=arguments.accepted_at,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def _finalize_05e(
    arguments: argparse.Namespace,
    repository_root: Path,
    artifact_root: Path,
) -> int:
    """Publish the separately authorized terminal wrapper around a closed review pass."""
    from er_commons.response_inventory.relationship_candidate import (
        publish_task05e_candidate,
    )

    result = publish_task05e_candidate(
        arguments.review_root,
        arguments.quality_report,
        repository_root,
        artifact_root,
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
    if spec.task_stage == "05f":
        if arguments.review_dispositions is not None:
            parser.error("Task 05F does not accept --review-dispositions")
        from er_commons.response_inventory.reference_baseline import (
            build_qualified_reference_rules,
        )

        result = build_qualified_reference_rules(
            arguments.run_spec.resolve(), repository_root, artifact_root
        )
    elif spec.task_stage == "05e":
        if arguments.review_dispositions is not None:
            parser.error("Task 05E does not accept --review-dispositions")
        if isinstance(spec, ResponseRelationshipReviewRunSpecV4):
            from er_commons.response_inventory.relationship_baseline import (
                build_bounded_relationship_review,
            )

            result = build_bounded_relationship_review(
                arguments.run_spec.resolve(), repository_root, artifact_root
            )
        else:
            from er_commons.response_inventory.relationship_baseline import (
                build_exact_relationship_baseline,
            )

            result = build_exact_relationship_baseline(
                arguments.run_spec.resolve(), repository_root, artifact_root
            )
    elif spec.task_stage == "05d":
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


def _is_reference_replay(path: Path) -> bool:
    """Select v6 without changing the accepted historical run-spec reader."""
    from er_commons.response_inventory.reference_replay_spec import is_replay_spec

    return is_replay_spec(path)


def _add_05g_parsers(subparsers: Any) -> None:
    """Expose separate source-free preparation, comparison and publication gates."""
    for name in ("prepare", "compare", "validate", "finalize", "accept"):
        command = subparsers.add_parser(f"{name}-05g")
        command.add_argument("--run-spec", type=Path, required=True)
        command.add_argument("--attempt", type=int, default=1)
        command.add_argument("--resume-from", type=int)
        if name in {"finalize", "accept"}:
            command.add_argument("--review-record", type=Path, required=True)
        if name == "finalize":
            command.add_argument("--quality-report", type=Path, required=True)
        if name == "accept":
            command.add_argument("--candidate-root", type=Path, required=True)
            command.add_argument("--accepted-by", required=True)
            command.add_argument("--accepted-at", required=True)


def _dispatch_05g(
    args: argparse.Namespace, parser: argparse.ArgumentParser, repository_root: Path
) -> int:
    """Keep new consumer roles out of all historical parser and writer recipes."""
    from er_commons.response_inventory.reference_replay_spec import load_replay_spec
    from er_commons.response_inventory.reference_replay_workflow import (
        open_run,
    )

    if args.command == "validate-spec":
        _, digest = load_replay_spec(args.run_spec, repository_root)
        print(json.dumps({"status": "valid", "task_stage": "05g", "behavior_sha256": digest}))
        return 0
    if getattr(args, "review_dispositions", None) is not None:
        parser.error("Task 05G does not accept --review-dispositions")
    run = open_run(
        args.run_spec,
        repository_root,
        _artifact_root(parser),
        attempt=args.attempt,
        resume_from=args.resume_from,
    )
    if args.command == "finalize-05g":
        from er_commons.response_inventory.reference_replay_acceptance import finalize_replay

        result = finalize_replay(run, args.quality_report, args.review_record)
    elif args.command == "accept-05g":
        from er_commons.response_inventory.reference_replay_acceptance import accept_replay

        result = accept_replay(
            run,
            args.candidate_root,
            args.review_record,
            accepted_by=args.accepted_by,
            accepted_at=args.accepted_at,
        )
    else:
        from er_commons.response_inventory.reference_replay_launch import launch_replay

        operation = {
            "prepare-05g": "prepare",
            "build": "build",
            "compare-05g": "compare",
            "validate-05g": "validate",
        }[args.command]
        result = launch_replay(
            args.run_spec,
            repository_root,
            run.artifact_root,
            attempt=run.attempt,
            resume_from=run.resume_from,
            operation=operation,
        )
    print(json.dumps(result, sort_keys=True))
    return 1 if result.get("status") == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
