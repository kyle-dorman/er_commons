"""Named stages for the Task 05H curator workflow.

``execute`` is the supervised dispatch boundary. Preparation assembles references;
review builds disposable views; finalization seals reviewed records; publication
and acceptance check the exact preceding supervised result. Payload construction
and validation helpers are pure except for explicitly named evidence reads.
Upstream producers and resolvers are never invoked.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import canonical_json_sha256
from er_commons.response_inventory.release_inputs import ReleaseInputs, load_release_inputs
from er_commons.response_inventory.release_publication import (
    accept_inventory,
    publish_inventory,
    require_authorization,
    validate_quality,
)
from er_commons.response_inventory.release_review import (
    build_selection,
    build_view_index,
    validate_decision_evidence,
    validate_decisions,
)
from er_commons.response_inventory.release_spec import (
    contained_path,
    load_release_spec,
    verify_file_binding,
)
from er_commons.response_inventory.release_storage import (
    digest,
    encode,
    encode_rows,
    inventory_identity,
    no_symlinks,
    publish_container,
    read_container,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReleaseRun:
    """One explicitly identified attempt; later authorization never changes upstream identities."""

    spec: dict[str, Any]
    plan_id: str
    repository_root: Path
    artifact_root: Path
    root: Path
    attempt: int
    resume_from: int | None = None

    @property
    def attempt_root(self) -> Path:
        """Return the exact attempt path without creating it."""
        return self.root / self.plan_id / f"attempt-{self.attempt:03d}"

    @property
    def prepared_root(self) -> Path:
        """Resolve only an explicitly named same-plan preparation checkpoint."""
        attempt = self.resume_from if self.resume_from is not None else self.attempt
        return self.root / self.plan_id / f"attempt-{attempt:03d}" / "prepared"

    @property
    def cache_root(self) -> Path:
        """Keep regenerable text views outside authoritative closure."""
        return self.root.parent / "cache" / "05h" / self.plan_id / f"attempt-{self.attempt:03d}"


def open_run(
    request: Path,
    repository_root: Path,
    artifact_root: Path,
    attempt: int = 1,
    resume_from: int | None = None,
) -> ReleaseRun:
    """Read only the request and its exact repository bindings."""
    if isinstance(attempt, bool) or attempt < 1:
        raise ValueError("05H attempt must be a positive integer")
    if resume_from is not None and (type(resume_from) is not int or not 0 < resume_from < attempt):
        raise ValueError("resume-from must name an earlier positive attempt")
    spec, identity = load_release_spec(request, repository_root)
    return ReleaseRun(
        spec,
        "plan05hv1-" + identity,
        repository_root,
        artifact_root,
        contained_path(artifact_root, spec["output_relative_root"]),
        attempt,
        resume_from,
    )


def load_inputs(run: ReleaseRun) -> ReleaseInputs:
    """Load only the accepted JSON records under the frozen metadata authority."""
    binding = json.loads(
        verify_file_binding(run.spec["binding_freeze"], run.repository_root).read_bytes()
    )
    return load_release_inputs(binding, run.artifact_root)


def selected_review(run: ReleaseRun, inputs: ReleaseInputs) -> dict[str, Any]:
    """Reproduce exact frozen membership; a matching count alone is not sufficient."""
    selection = build_selection(inputs)
    frozen = json.loads(
        verify_file_binding(run.spec["selection_freeze"], run.repository_root).read_bytes()
    )
    if selection != frozen:
        raise ValueError("05H selection differs from approved membership; stop before output")
    return selection


def _base_payloads(
    run: ReleaseRun, inputs: ReleaseInputs, selection: dict[str, Any]
) -> dict[str, bytes]:
    """Compose compact references and indexes while source text stays in accepted 05D."""
    return {
        "records/dependencies.json": encode(inputs.dependencies),
        "records/activity.json": encode(
            {
                "schema_version": "er_commons.response_inventory_release.v1",
                "stage": "05h",
                "plan_id": run.plan_id,
                "repository_bindings": run.spec["repository_bindings"],
                "tool_versions": run.spec["runtime_versions"],
                "selection_sha256": digest(encode(selection)),
                "input_semantic_digest": inputs.semantic_digest,
                "source_model_execution": False,
                "request_policy": {
                    k: run.spec[k] for k in ("selection_policy", "question_version", "view_policy")
                },
            }
        ),
        "inventory/components.json": encode(inputs.components),
        "review_views/index.jsonl": encode_rows(build_view_index(inputs)),
        "review_views/recipe.json": encode(
            {
                "policy": run.spec["view_policy"],
                "source_text_owner": "05d",
                "flatten_linked_units": False,
                "automatic_cycle_traversal": False,
            }
        ),
        "records/review_selection.json": encode(selection),
        "diagnostics/accounting.json": encode(inputs.accounting),
        "diagnostics/limitations.json": encode(
            {
                "coverage": inputs.limitations["coverage"],
                "final_f1_warning_binding": inputs.limitations["final_f1_warning_binding"],
                "inherited_refs": [
                    r for r in inputs.dependencies if r.get("role", "").startswith("task06h")
                ],
                "caption_backed_figures_unavailable_as_text_only_evidence": 178,
                "review_scope": "composition only; inherited sampled coverage is unchanged",
            }
        ),
    }


def prepare(run: ReleaseRun) -> dict[str, Any]:
    """Prepare references and selection only after production composition is authorized."""
    require_authorization(run.spec, "prepare")
    inputs = load_inputs(run)
    selection = selected_review(run, inputs)
    payloads = _base_payloads(run, inputs, selection)
    if run.resume_from is not None:
        validate_candidate(run, run.prepared_root)
        completion, _ = read_container(run.prepared_root, plan_id=run.plan_id)
        return {"status": "prepared_reused", "completion": completion}
    completion = publish_container(
        run.prepared_root,
        payloads,
        plan_id=run.plan_id,
        semantic_digest=inputs.semantic_digest,
        status="prepared",
    )
    return {"status": "prepared", "completion": completion}


def validate_candidate(run: ReleaseRun, candidate: Path) -> dict[str, Any]:
    """Validate closure and live accepted semantics without rewriting any file."""
    completion, payloads = read_container(candidate, plan_id=run.plan_id)
    inputs = load_inputs(run)
    selection = selected_review(run, inputs)
    expected = _base_payloads(run, inputs, selection)
    for name, value in expected.items():
        if (
            name == "inventory/components.json"
            and completion["status"] == "complete_with_limitations"
        ):
            _validate_sealed_components(
                json.loads(payloads[name]), inputs.components, run.artifact_root
            )
        elif payloads.get(name) != value:
            raise ValueError(f"05H composed payload differs from accepted inputs: {name}")
    if completion["status"] == "complete_with_limitations":
        from er_commons.response_inventory.release_execution import verify_finalized_result

        verify_finalized_result(run, completion)
        _validate_final_payloads(run, inputs, selection, payloads, completion)
    elif set(payloads) != set(expected) or completion["semantic_digest"] != inputs.semantic_digest:
        raise ValueError("05H prepared payload closure mismatch")
    return {
        "status": "valid",
        "completion": completion,
        "input_semantic_digest": inputs.semantic_digest,
    }


def _evidence(run: ReleaseRun, key: str) -> Any:
    """Require exact selected JSON evidence under its declared authority."""
    binding = run.spec.get(key)
    if binding is None:
        raise ValueError(f"05H requires an explicit {key} binding")
    allowed = {".json", ".jsonl"} if key == "review_decisions" else {".json"}
    if Path(binding["path"]).suffix not in allowed:
        raise ValueError(f"05H {key} must be source-free JSON evidence")
    root = run.repository_root if binding["authority"] == "repository" else run.artifact_root
    path = verify_file_binding(binding, root)
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return json.loads(path.read_bytes())


def _seal_components(components: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    """Hash a Task-05-owned component once only where its accepted inventory lacks a digest."""
    result = []
    for original in components:
        row = dict(original)
        if row.get("sha256") is None:
            if "/working/05d/" not in row["path"] or Path(row["path"]).suffix not in {
                ".json",
                ".jsonl",
            }:
                raise ValueError(
                    "first publication digest may only seal declared 05D JSON payloads"
                )
            path = contained_path(root, row["path"])
            data = path.read_bytes()
            rows = (
                [json.loads(line) for line in data.splitlines() if line.strip()]
                if path.suffix == ".jsonl"
                else [json.loads(data)]
            )
            if canonical_json_sha256(rows) != row["record_semantic_digest"]:
                raise ValueError("05D component changed between semantic validation and first seal")
            row["sha256"] = digest(data)
            row["check_mode"] = "first_publication_byte_seal"
        result.append(row)
    return result


def _validate_sealed_components(
    sealed: list[dict[str, Any]], accepted: list[dict[str, Any]], root: Path
) -> None:
    """Check first-time seals without silently changing any inherited component field."""
    if len(sealed) != len(accepted):
        raise ValueError("release component count changed")
    for row, original in zip(sealed, accepted, strict=True):
        expected = dict(original)
        if original.get("sha256") is None:
            sha = row.get("sha256")
            if (
                not isinstance(sha, str)
                or len(sha) != 64
                or any(c not in "0123456789abcdef" for c in sha)
            ):
                raise ValueError("missing first-publication component digest")
            expected.update(sha256=sha, check_mode="first_publication_byte_seal")
        if row != expected or contained_path(root, row["path"]).stat().st_size != row["size_bytes"]:
            raise ValueError(f"release component drift: {row.get('path')}")


def review_payload_digest(
    run: ReleaseRun,
    inputs: ReleaseInputs,
    selection: dict[str, Any],
    decisions: list[dict[str, Any]],
    review: dict[str, Any],
) -> str:
    """Name exactly the pre-completion composition and curator decisions reviewed for quality."""
    payloads = _base_payloads(run, inputs, selection)
    payloads["inventory/decisions.jsonl"] = encode_rows(canonical_decisions(decisions))
    payloads["records/review_completion.json"] = encode(review)
    return canonical_json_sha256({name: digest(value) for name, value in sorted(payloads.items())})


def canonical_decisions(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort unique reviewed records while preserving their explicit supersession links."""
    by_id: dict[str, dict[str, Any]] = {}
    for row in decisions:
        key = row["decision_id"]
        if key in by_id and by_id[key] != row:
            raise ValueError(f"05H conflicting repeated decision ID: {key}")
        by_id[key] = row
    return [by_id[key] for key in sorted(by_id)]


def _validate_execution_evidence(run: ReleaseRun, evidence: list[dict[str, Any]]) -> None:
    """Retain exact terminal preparation and view-build receipts in final provenance."""
    from er_commons.response_inventory.release_execution import verify_terminal_execution

    if [item.get("operation") for item in evidence] != ["prepare", "review"]:
        raise ValueError("05H final execution provenance is incomplete")
    for item in evidence:
        if item != verify_terminal_execution(run, item["operation"], item["attempt"]):
            raise ValueError("05H final execution evidence differs from terminal receipt")


def _final_extras(
    run: ReleaseRun,
    inputs: ReleaseInputs,
    selection: dict[str, Any],
    decisions: list[dict[str, Any]],
    quality: dict[str, Any],
    execution_evidence: list[dict[str, Any]],
) -> dict[str, bytes]:
    """Bind review and quality below final completion, avoiding cyclic identities."""
    validate_decision_evidence(inputs, selection, decisions)
    review = validate_decisions(selection, decisions, run.plan_id)
    validate_quality(
        quality,
        plan_id=run.plan_id,
        semantic_digest=inputs.semantic_digest,
        repository_bindings=run.spec["repository_bindings"],
    )
    target = review_payload_digest(run, inputs, selection, decisions, review)
    if quality.get("review_payload_digest") != target:
        raise ValueError("05H quality report does not bind the exact assembled review payloads")
    return {
        "records/execution_evidence.json": encode(execution_evidence),
        "inventory/decisions.jsonl": encode_rows(canonical_decisions(decisions)),
        "records/review_completion.json": encode(review),
        "records/quality_review.json": encode(quality),
        "records/validation.json": encode(
            {
                "status": "passed",
                "plan_id": run.plan_id,
                "input_semantic_digest": inputs.semantic_digest,
                "selection_sha256": digest(encode(selection)),
                "repeat_semantics_verified": True,
            }
        ),
        "records/task07_task08_handoff.json": encode(
            {
                "schema_version": "er_commons.task05h.downstream_handoff.v1",
                "plan_id": run.plan_id,
                "input_semantic_digest": inputs.semantic_digest,
                "curator_only": True,
                "review_completion_sha256": digest(encode(review)),
                "execution_evidence_sha256": digest(encode(execution_evidence)),
                "dependencies": inputs.dependencies,
                "required_limitations": "diagnostics/limitations.json",
                "components": "inventory/components.json",
                "downstream_execution_authorized": False,
                "link_is_evidence_eligibility": False,
            }
        ),
    }


def _validate_final_payloads(
    run: ReleaseRun,
    inputs: ReleaseInputs,
    selection: dict[str, Any],
    payloads: dict[str, bytes],
    completion: dict[str, Any],
) -> None:
    """Recompute reviewed final fields rather than trust a self-consistent file manifest."""
    decisions = [json.loads(line) for line in payloads["inventory/decisions.jsonl"].splitlines()]
    quality = json.loads(payloads["records/quality_review.json"])
    execution_evidence = json.loads(payloads["records/execution_evidence.json"])
    _validate_execution_evidence(run, execution_evidence)
    extras = _final_extras(run, inputs, selection, decisions, quality, execution_evidence)
    if any(payloads.get(k) != value for k, value in extras.items()):
        raise ValueError("05H final review, validation or handoff payload mismatch")
    if set(payloads) != set(_base_payloads(run, inputs, selection)) | set(extras):
        raise ValueError("05H final payload set mismatch")
    semantic = canonical_json_sha256(
        {name: digest(data) for name, data in sorted(payloads.items())}
    )
    if completion["semantic_digest"] != semantic:
        raise ValueError("05H final semantic digest mismatch")


def _reuse_finalized_candidate(run: ReleaseRun, final_root: Path) -> dict[str, Any]:
    """Reuse only the same closed decisions and quality report, without resealing inputs."""
    result = validate_candidate(run, final_root)
    completion, payloads = read_container(final_root, plan_id=run.plan_id)
    if payloads["inventory/decisions.jsonl"] != encode_rows(
        canonical_decisions(_evidence(run, "review_decisions"))
    ):
        raise ValueError("changed decisions require a fresh finalization attempt")
    if payloads["records/quality_review.json"] != encode(_evidence(run, "quality_report")):
        raise ValueError("changed quality report requires a fresh finalization attempt")
    return {**result, "inventory_id": inventory_identity(completion)}


def finalize(run: ReleaseRun) -> dict[str, Any]:
    """Close only an explicitly reviewed and repeat-validated prepared candidate."""
    require_authorization(run.spec, "finalize")
    from er_commons.response_inventory.release_execution import verify_terminal_execution

    prior_attempt = run.resume_from if run.resume_from is not None else run.attempt
    execution_evidence = [
        verify_terminal_execution(run, "prepare", prior_attempt),
        verify_terminal_execution(run, "review", run.attempt),
    ]
    prepared = run.prepared_root
    validation = validate_candidate(run, prepared)
    inputs = load_inputs(run)
    selection = selected_review(run, inputs)
    # The repeated source-free load must reproduce the prepared semantic state.
    if validation["input_semantic_digest"] != inputs.semantic_digest:
        raise ValueError("05H repeat semantic mismatch")
    final_root = run.attempt_root / "finalized"
    if final_root.exists():
        return _reuse_finalized_candidate(run, final_root)
    decisions = _evidence(run, "review_decisions")
    quality = _evidence(run, "quality_report")
    extras = _final_extras(run, inputs, selection, decisions, quality, execution_evidence)
    payloads = _base_payloads(run, inputs, selection)
    payloads["inventory/components.json"] = encode(
        _seal_components(inputs.components, run.artifact_root)
    )
    payloads.update(extras)
    semantic = canonical_json_sha256(
        {name: digest(data) for name, data in sorted(payloads.items())}
    )
    completion = publish_container(
        final_root,
        payloads,
        plan_id=run.plan_id,
        semantic_digest=semantic,
        status="complete_with_limitations",
    )
    return {
        "status": "finalized_pending_publication",
        "inventory_id": inventory_identity(completion),
        "candidate_root": str(final_root),
        "completion": completion,
    }


def review(run: ReleaseRun) -> dict[str, Any]:
    """Validate preparation, then build or reuse this attempt's disposable text cache."""
    require_authorization(run.spec, "review")
    from er_commons.response_inventory.release_views import build_review_cache

    validate_candidate(run, run.prepared_root)
    inputs = load_inputs(run)
    selection = selected_review(run, inputs)
    cache = build_review_cache(
        inputs,
        build_view_index(inputs),
        subject_ids=[row["subject_ref"] for row in selection["obligations"]],
    )
    no_symlinks(run.cache_root)
    if run.cache_root.exists():
        existing = {}
        for path in run.cache_root.rglob("*"):
            no_symlinks(path)
            if path.is_file():
                existing[path.relative_to(run.cache_root).as_posix()] = path.read_bytes()
        if existing != cache:
            raise ValueError("review cache differs; use a fresh attempt")
    else:
        from er_commons.response_inventory.release_storage import relative_name, write_file

        run.cache_root.mkdir(parents=True)
        for name, data in cache.items():
            path = run.cache_root / relative_name(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            write_file(path, data)
    return {
        "status": "review_required",
        "cache_root": str(run.cache_root),
        "selection_sha256": digest(encode(selection)),
    }


def publish(run: ReleaseRun, candidate: Path) -> dict[str, Any]:
    """Publish only the candidate produced by this attempt's successful finalization."""
    require_authorization(run.spec, "publish")
    from er_commons.response_inventory.release_execution import verify_terminal_execution

    validate_candidate(run, candidate)
    if candidate.resolve() != (run.attempt_root / "finalized").resolve():
        raise ValueError("publication must use the exact supervised finalization attempt")
    verify_terminal_execution(run, "finalize", run.attempt)
    return publish_inventory(candidate, run.root.parent.parent, run.spec, plan_id=run.plan_id)


def accept(
    run: ReleaseRun, candidate: Path, *, accepted_by: str, accepted_at: str
) -> dict[str, Any]:
    """Prepare acceptance evidence; the launcher owns designation after terminal success."""
    require_authorization(run.spec, "accept")
    from er_commons.response_inventory.release_execution import (
        verify_published_candidate,
        verify_terminal_execution,
    )

    validate_candidate(run, candidate)
    verify_terminal_execution(run, "publish", run.attempt)
    verify_published_candidate(run, candidate)
    return accept_inventory(
        candidate,
        run.root,
        run.spec,
        plan_id=run.plan_id,
        accepted_by=accepted_by,
        accepted_at=accepted_at,
    )


def execute(
    run: ReleaseRun,
    operation: str,
    *,
    candidate: Path | None = None,
    accepted_by: str = "",
    accepted_at: str = "",
) -> dict[str, Any]:
    """Authorize and dispatch one stage; each named stage owns its local sequence."""
    require_authorization(run.spec, operation)
    LOGGER.info("05H %s started plan=%s attempt=%s", operation, run.plan_id, run.attempt)
    if operation == "prepare":
        result = prepare(run)
    elif operation == "review":
        result = review(run)
    elif operation == "finalize":
        result = finalize(run)
    else:
        if candidate is None:
            raise ValueError("publication/acceptance requires an exact candidate root")
        if operation == "publish":
            result = publish(run, candidate)
        elif operation == "accept":
            result = accept(run, candidate, accepted_by=accepted_by, accepted_at=accepted_at)
        else:
            raise ValueError(f"unknown 05H operation: {operation}")
    LOGGER.info("05H %s completed status=%s", operation, result["status"])
    return result


def main() -> None:
    """Worker entry; the maintained launch adapter provides process supervision."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-spec", required=True, type=Path)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--resume-from", type=int)
    parser.add_argument(
        "--operation", required=True, choices=("prepare", "review", "finalize", "publish", "accept")
    )
    parser.add_argument("--candidate-root", type=Path)
    parser.add_argument("--accepted-by", default="")
    parser.add_argument("--accepted-at", default="")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    data_root = os.environ.get("ER_COMMONS_DATA_ROOT")
    if not data_root:
        parser.error("ER_COMMONS_DATA_ROOT must be set explicitly")
    run = open_run(
        args.run_spec,
        Path(__file__).resolve().parents[3],
        Path(data_root),
        args.attempt,
        args.resume_from,
    )
    from er_commons.response_inventory.release_execution import verify_worker_launch

    verify_worker_launch(
        run, args.run_spec, args.operation, args.candidate_root, args.accepted_by, args.accepted_at
    )
    result = execute(
        run,
        args.operation,
        candidate=args.candidate_root,
        accepted_by=args.accepted_by,
        accepted_at=args.accepted_at,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
