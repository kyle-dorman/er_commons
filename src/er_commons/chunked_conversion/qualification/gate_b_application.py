"""Human-sized application workflow for Gate B qualification."""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from er_commons.artifact_io import (
    artifact_inventory,
    canonical_json_sha256,
    read_json_object,
    sha256_file,
    write_json_atomic,
)
from er_commons.chunked_conversion.gate_b import GateBStandardPdfPipeline
from er_commons.chunked_conversion.qualification.gate_b_contracts import (
    CONVERSION_ID,
    SEAMS,
    GateBContractError,
    GateBRunCompletion,
    GateBRunRequest,
    GateBSeamCompletion,
    GateBWorkerSpec,
    seam_payload,
)
from er_commons.chunked_conversion.qualification.gate_b_inputs import (
    identity_payload,
    verified_inputs,
)
from er_commons.chunked_conversion.qualification.gate_b_process import run_isolated_worker
from er_commons.chunked_conversion.qualification.gate_b_trace import sealed_page_trace
from er_commons.chunked_conversion.qualification.gate_b_worker import (
    run_worker_spec,
    write_failure,
)
from er_commons.document_parsing.content_parsing.evidence import verify_inventory

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_WORKER_ENTRYPOINT = PROJECT_ROOT / "scripts/run_task03h2_gate_b.py"

WorkerRunner = Callable[[Path, Path], dict[str, Any]]


def run_gate_b(
    request: GateBRunRequest,
    *,
    worker_runner: WorkerRunner | None = None,
) -> Path:
    """Verify inputs, execute missing seams, and completion-seal one Gate B run."""
    identity, prepared = verified_inputs(
        request.source_root, request.config_path, request.data_root
    )
    payload = identity_payload(
        project_root=PROJECT_ROOT,
        source_root=request.source_root,
        config_path=request.config_path,
        prepared=prepared,
        max_rss_bytes=request.max_rss_bytes,
        max_wall_seconds=request.max_wall_seconds,
    )
    run_id = "gateb1-" + canonical_json_sha256(payload)
    final = request.output_root / "runs" / run_id
    if final.exists():
        return verify_completed_run(final, expected_run_id=run_id)
    staging = _new_attempt(request.output_root, run_id)
    try:
        trace_path = _write_run_contract(staging, request, run_id, payload, identity, prepared)
        seam_reports = _run_seams(
            staging,
            request,
            trace_path,
            worker_runner or _default_worker_runner(request),
        )
        _write_run_report(staging, run_id, seam_reports)
        completion = _publish_run(staging, run_id)
        final.parent.mkdir(parents=True, exist_ok=True)
        staging.rename(final)
        return final / completion.relative_to(staging)
    except BaseException as error:
        write_failure(staging, error, stage="coordinator")
        raise


def _new_attempt(output_root: Path, run_id: str) -> Path:
    attempts = output_root / "attempts"
    attempts.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f"{run_id}.", dir=attempts))


def _write_run_contract(
    staging: Path,
    request: GateBRunRequest,
    run_id: str,
    payload: dict[str, Any],
    sealed_identity: dict[str, Any],
    prepared: Any,
) -> Path:
    trace_path = staging / "records/sealed_g1_page_trace.json"
    trace = sealed_page_trace(
        request.source_root, {page for seam in SEAMS for page in seam.comparison_pages}
    )
    write_json_atomic(trace_path, trace)
    write_json_atomic(
        staging / "records/run_contract.json",
        {
            "schema_version": "er_commons.task03h2_gate_b_contract.v1",
            "run_id": run_id,
            "identity": payload,
            "source_conversion_id": CONVERSION_ID,
            "source_identity": sealed_identity["identity"]["source"],
            "model_inventory_sha256": prepared.model_inventory_sha256,
            "prepared_conversion_identity": {
                "conversion_id": prepared.conversion_identity.run_id,
                "payload": prepared.conversion_identity.payload,
            },
            "sealed_runtime_configuration": prepared.runtime,
            "gate_b_pipeline_class": (
                f"{GateBStandardPdfPipeline.__module__}.{GateBStandardPdfPipeline.__name__}"
            ),
            "seams": [seam_payload(seam) for seam in SEAMS],
            "execution_order": [seam.seam_id for seam in SEAMS],
            "child_process_isolation": "one_fresh_sequential_process_per_seam",
            "limits": {
                "max_rss_bytes": request.max_rss_bytes,
                "max_wall_seconds_per_seam": request.max_wall_seconds,
            },
            "scope_boundary": "G1 Gate B only; no G2 and no Gate C",
        },
    )
    return trace_path


def _run_seams(
    staging: Path,
    request: GateBRunRequest,
    trace_path: Path,
    worker_runner: WorkerRunner,
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for seam in SEAMS:
        seam_root = staging / "seams" / seam.seam_id
        seam_root.mkdir(parents=True)
        spec_path = seam_root / "worker_spec.json"
        spec = GateBWorkerSpec(
            source_root=request.source_root,
            config_path=request.config_path,
            data_root=request.data_root,
            seam_root=seam_root,
            sealed_trace_path=trace_path,
            seam=seam,
            max_rss_bytes=request.max_rss_bytes,
        )
        write_json_atomic(spec_path, spec.model_dump(mode="json"))
        observation = worker_runner(spec_path, seam_root)
        completion = verify_seam_completion(seam_root, expected_seam_id=seam.seam_id)
        reports.append(
            {
                **read_json_object(seam_root / "records/seam_report.json"),
                "completion": completion.model_dump(mode="json"),
                "coordinator_observation": observation,
            }
        )
    return reports


def _default_worker_runner(request: GateBRunRequest) -> WorkerRunner:
    def execute(spec_path: Path, seam_root: Path) -> dict[str, Any]:
        return run_isolated_worker(
            spec_path,
            seam_root,
            worker_entrypoint=DEFAULT_WORKER_ENTRYPOINT,
            max_rss_bytes=request.max_rss_bytes,
            timeout_seconds=request.max_wall_seconds,
        )

    return execute


def verify_seam_completion(root: Path, *, expected_seam_id: str) -> GateBSeamCompletion:
    """Verify terminal identity and every inventoried byte before seam reuse."""
    path = root / "records/completion_record.json"
    try:
        completion = GateBSeamCompletion.model_validate_json(path.read_bytes())
    except (OSError, ValueError) as error:
        raise GateBContractError("invalid_seam_completion", path.as_posix(), str(error)) from error
    if completion.seam_id != expected_seam_id or root.name != expected_seam_id:
        raise GateBContractError(
            "foreign_seam_completion",
            path.as_posix(),
            f"expected={expected_seam_id} actual={completion.seam_id} root={root.name}",
        )
    inventory_path = root / completion.artifact_inventory
    if sha256_file(inventory_path) != completion.artifact_inventory_sha256:
        raise GateBContractError("seam_inventory_seal", inventory_path.as_posix(), "digest differs")
    verify_inventory(root, read_json_object(inventory_path))
    return completion


def _write_run_report(staging: Path, run_id: str, reports: list[dict[str, Any]]) -> None:
    write_json_atomic(
        staging / "records/gate_b_report.json",
        {
            "schema_version": "er_commons.task03h2_gate_b_report.v1",
            "status": "passed",
            "run_id": run_id,
            "source_conversion_id": CONVERSION_ID,
            "seam_reports": reports,
            "calibration_ran_first": SEAMS[0].seam_class == "ordinary_prose_calibration",
            "sequential_child_processes": True,
            "gate_c_started": False,
            "g2_started": False,
        },
    )


def _publish_run(staging: Path, run_id: str) -> Path:
    inventory_path = staging / "records/artifact_inventory.json"
    inventory = artifact_inventory(
        staging,
        excluded={"records/artifact_inventory.json", "records/completion_record.json"},
    )
    write_json_atomic(inventory_path, inventory)
    verify_inventory(staging, inventory)
    completion_path = staging / "records/completion_record.json"
    write_json_atomic(
        completion_path,
        {
            "schema_version": "er_commons.task03h2_gate_b_completion.v1",
            "status": "complete",
            "run_id": run_id,
            "source_conversion_id": CONVERSION_ID,
            "artifact_inventory": "records/artifact_inventory.json",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "completion_last": True,
            "gate_c_started": False,
            "g2_started": False,
        },
    )
    return completion_path


def verify_completed_run(root: Path, *, expected_run_id: str) -> Path:
    """Reject transplanted or corrupted completed runs before reuse."""
    completion_path = root / "records/completion_record.json"
    try:
        completion = GateBRunCompletion.model_validate_json(completion_path.read_bytes())
    except (OSError, ValueError) as error:
        raise GateBContractError(
            "invalid_run_completion", completion_path.as_posix(), str(error)
        ) from error
    if root.name != expected_run_id or completion.run_id != expected_run_id:
        raise GateBContractError(
            "foreign_run_completion",
            completion_path.as_posix(),
            f"expected={expected_run_id} actual={completion.run_id} root={root.name}",
        )
    inventory_path = root / completion.artifact_inventory
    if completion.artifact_inventory_sha256 != sha256_file(inventory_path):
        raise GateBContractError("run_inventory_seal", inventory_path.as_posix(), "digest differs")
    verify_inventory(root, read_json_object(inventory_path))
    return completion_path


__all__ = [
    "GateBRunRequest",
    "run_gate_b",
    "run_worker_spec",
    "verify_completed_run",
    "verify_seam_completion",
]
