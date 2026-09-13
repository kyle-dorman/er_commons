"""Source-free terminal validation and completion-last readiness publication."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from er_commons.artifact_io import sha256_bytes
from er_commons.collection_processing import validate_collection_handoff
from er_commons.task06g.core import (
    FORBIDDEN_PAYLOAD_SUFFIXES,
    JsonObject,
    canonical_bytes,
    content_reference,
    load_object,
    publish_directory_no_clobber,
    reference,
    verify_reference,
)
from er_commons.task06g.packets import (
    _payload_inventory_references,
    _tree_bytes,
    evidence_root_record,
    execution_total_cap,
    verify_evidence_root_record,
)


@dataclass(frozen=True)
class FinalizationHooks:
    """Test-only interruption points around each completion-last boundary."""

    after_inventory: Callable[[], None] = lambda: None
    after_readiness: Callable[[], None] = lambda: None
    after_completion: Callable[[], None] = lambda: None
    after_rename: Callable[[], None] = lambda: None


def _terminal_execution(attempt_root: Path) -> tuple[JsonObject, JsonObject]:
    path = attempt_root / "execution.json"
    execution = load_object(path)
    if execution.get("status") != "succeeded":
        raise ValueError("terminal execution status is not succeeded")
    if execution.get("return_code", execution.get("returncode")) != 0:
        raise ValueError("terminal execution return code is nonzero")
    if execution.get("failure_reason") or execution.get("reason"):
        raise ValueError("terminal execution records a failure reason")
    if execution.get("surviving_descendants", execution.get("surviving_pids", [])):
        raise ValueError("terminal execution records surviving descendants")
    return execution, reference(path, root=attempt_root)


def _required_evidence(spec: JsonObject, replay_root: Path) -> list[JsonObject]:
    finalization = spec.get("finalization")
    raw_files = (
        finalization.get("required_files")
        if isinstance(finalization, dict)
        else spec.get("finalization_required_files")
    )
    if not isinstance(raw_files, list):
        raise ValueError("execution spec requires finalization.required_files")
    required_suffixes = {
        "resolved_specs_v1/aggregate_v1/resolved_spec_manifest.json",
        "resolved_specs_v1/aggregate_v1/artifact_inventory.json",
        "identity_checkpoints_v1/inventory.json",
    }
    if not required_suffixes.issubset(set(raw_files)):
        raise ValueError("finalization required files omit resolved-spec or checkpoint closure")
    if not any(str(item).startswith("correspondence_v1/") for item in raw_files):
        raise ValueError("finalization required files omit correspondence closure")
    if not any(str(item).startswith("comparison_v1/") for item in raw_files):
        raise ValueError("finalization required files omit comparison closure")
    references = []
    for item in raw_files:
        if not isinstance(item, str):
            raise ValueError("finalization required paths must be explicit strings")
        references.append(reference(replay_root / item, root=replay_root))
    if spec.get("schema_version") in {
        "er_commons.task06g.execution_template.v1",
        "er_commons.task06g.collection_execution_template.v1",
    }:
        _verify_compact_completion(replay_root / "correspondence_v1", "correspondence")
        _verify_compact_completion(replay_root / "comparison_v1", "comparison")
        _verify_reference_inventory(
            replay_root / "identity_checkpoints_v1",
            "inventory.json",
            expected_paths=_checkpoint_paths(spec),
        )
        _verify_reference_inventory(
            replay_root / "resolved_specs_v1/aggregate_v1",
            "artifact_inventory.json",
            expected_paths=None,
        )
        _verify_resolved_closure(
            replay_root / "resolved_specs_v1/aggregate_v1",
            spec=spec,
            artifact_root=_artifact_root(spec),
        )
        _verify_collection_closure(spec, replay_root)
    return references


def _checkpoint_paths(spec: JsonObject) -> set[str]:
    closure = spec.get("resolver_closure")
    values = closure.get("checkpoint_files") if isinstance(closure, dict) else None
    if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
        raise ValueError("execution spec lacks exact checkpoint file enumeration")
    return set(values)


def _verify_reference_inventory(
    root: Path, inventory_name: str, *, expected_paths: set[str] | None
) -> None:
    """Verify a compact reference inventory and each declared JSON object's closure flags."""
    inventory = load_object(root / inventory_name)
    files = inventory.get("files")
    if not isinstance(files, list) or any(not isinstance(item, dict) for item in files):
        raise ValueError(f"managed inventory is malformed: {root / inventory_name}")
    paths = {str(cast(JsonObject, item).get("path")) for item in files}
    if len(paths) != len(files) or (expected_paths and paths != expected_paths):
        raise ValueError(f"managed inventory paths differ: {root / inventory_name}")
    for item in files:
        path = verify_reference(cast(JsonObject, item), root=root)
        if path.suffix == ".json" and path.name != inventory_name:
            value = load_object(path)
            if "verified" in value and value.get("verified") is not True:
                raise ValueError(f"checkpoint is not independently verified: {path}")
            if "derived_id" in value and value.get("derived_id") != value.get("recomputed_id"):
                raise ValueError(f"checkpoint identity recomputation differs: {path}")


def _artifact_root(spec: JsonObject) -> Path:
    """Resolve the sole artifact authority from the frozen generation recipe."""
    generation_path = Path(cast(str, spec["generation_spec"])).resolve()
    generation = load_object(generation_path)
    raw = generation["data_root"]
    if raw == "${ER_COMMONS_DATA_ROOT}":
        from er_commons.settings import load_settings

        return load_settings().data_root.resolve()
    return (generation_path.parent / cast(str, raw)).resolve()


def _resolver_lists(spec: JsonObject) -> tuple[list[str], list[str]]:
    """Return exact phase and process-checkpoint enumerations from execution policy."""
    closure = spec.get("resolver_closure")
    if not isinstance(closure, dict):
        raise ValueError("execution spec lacks resolver closure")
    phases = closure.get("phase_directories")
    checkpoints = closure.get("process_checkpoint_files")
    if (
        not isinstance(phases, list)
        or any(not isinstance(item, str) for item in phases)
        or not isinstance(checkpoints, list)
        or any(not isinstance(item, str) for item in checkpoints)
    ):
        raise ValueError("resolver phase/checkpoint enumeration is malformed")
    return cast(list[str], phases), cast(list[str], checkpoints)


def _verify_process_checkpoint(
    path: Path,
    *,
    expected_name: str,
    resolved_root: Path,
    artifact_root: Path,
) -> None:
    """Verify one independently sealed stage result and its resolved config phase."""
    parts = Path(expected_name).parts
    if len(parts) != 3 or parts[0] != "document_stage_checkpoints_v1":
        raise ValueError(f"process checkpoint name differs: {expected_name}")
    source_id = parts[1]
    ordinal_role = Path(parts[2]).stem
    _, role = ordinal_role.split("_", 1)
    value = load_object(path)
    if (
        value.get("schema_version") != "er_commons.task06g.process_identity_checkpoint.v1"
        or value.get("source_id") != source_id
        or value.get("stage") != role
        or value.get("verified") is not True
        or value.get("derived_id") != value.get("recomputed_id")
    ):
        raise ValueError(f"process identity checkpoint semantics differ: {path}")
    for field in ("stage_completion", "stage_inventory", "resolved_config_ref"):
        reference_value = value.get(field)
        if not isinstance(reference_value, dict) or reference_value.get("authority") != (
            "artifact_root"
        ):
            raise ValueError(f"process checkpoint lacks artifact authority: {path}")
        observed = verify_reference(cast(JsonObject, reference_value), root=artifact_root)
        if field == "resolved_config_ref":
            expected = resolved_root / "document_stages" / source_id / ordinal_role / f"{role}.json"
            if observed != expected.resolve():
                raise ValueError(f"process checkpoint resolved config differs: {path}")


def _verify_resolved_closure(root: Path, *, spec: JsonObject, artifact_root: Path) -> None:
    """Verify aggregate resolved-spec inventory, phase manifests, and checkpoint binding."""
    expected_phases, expected_process_checkpoints = _resolver_lists(spec)
    inventory = load_object(root / "artifact_inventory.json")
    external = inventory.get("external_files")
    if not isinstance(external, list) or any(not isinstance(item, dict) for item in external):
        raise ValueError("resolved-spec inventory external files are malformed")
    closure = cast(JsonObject, spec["resolver_closure"])
    pre_execution_name = cast(
        str,
        closure.get(
            "pre_execution_identity_checkpoint",
            "00_initial/pre_execution_production_identity_checkpoint.json",
        ),
    )
    pre_execution_field = cast(
        str,
        closure.get(
            "pre_execution_manifest_field",
            "pre_execution_production_identity_checkpoint",
        ),
    )
    expected_external = {pre_execution_name, *expected_process_checkpoints}
    if {str(cast(JsonObject, item).get("path")) for item in external} != expected_external:
        raise ValueError("resolved-spec aggregate external closure differs")
    for item in external:
        verify_reference(cast(JsonObject, item), root=root.parent)
    manifest = load_object(root / "resolved_spec_manifest.json")
    if manifest.get("schema_version") != "er_commons.task06g.resolved_spec_manifest.v1":
        raise ValueError("resolved-spec manifest schema differs")
    phases = manifest.get("phases")
    if not isinstance(phases, list) or any(not isinstance(item, dict) for item in phases):
        raise ValueError("resolved-spec manifest phase closure is malformed")
    expected_phase_paths = [f"{name}/phase_manifest.json" for name in expected_phases]
    if [str(cast(JsonObject, item).get("path")) for item in phases] != expected_phase_paths:
        raise ValueError("resolved-spec manifest phase enumeration differs")
    for item in phases:
        phase_path = verify_reference(cast(JsonObject, item), root=root.parent)
        phase = load_object(phase_path)
        managed = phase.get("managed_files")
        if not isinstance(managed, list) or any(not isinstance(row, dict) for row in managed):
            raise ValueError(f"resolved phase manifest is malformed: {phase_path}")
        phase_root = phase_path.parent
        external_checkpoints = phase.get("external_checkpoints", [])
        if not isinstance(external_checkpoints, list) or any(
            not isinstance(row, dict) for row in external_checkpoints
        ):
            raise ValueError(f"resolved phase external checkpoints are malformed: {phase_path}")
        for row in external_checkpoints:
            if row.get("authority") != "artifact_root":
                raise ValueError(f"resolved phase checkpoint authority differs: {phase_path}")
            verify_reference(cast(JsonObject, row), root=artifact_root)
        for row in managed:
            verify_reference(cast(JsonObject, row), root=phase_root)
        expected = {str(cast(JsonObject, row)["path"]) for row in managed} | {"phase_manifest.json"}
        observed = {
            path.relative_to(phase_root).as_posix()
            for path in phase_root.rglob("*")
            if path.is_file()
        }
        if expected != observed:
            raise ValueError(f"resolved phase managed-file closure differs: {phase_root}")
    checkpoint = manifest.get(pre_execution_field)
    if not isinstance(checkpoint, dict):
        raise ValueError("resolved-spec manifest lacks production checkpoint")
    verify_reference(checkpoint, root=root.parent)
    process_checkpoints = manifest.get("process_identity_checkpoints")
    if not isinstance(process_checkpoints, list) or any(
        not isinstance(item, dict) for item in process_checkpoints
    ):
        raise ValueError("resolved-spec manifest process checkpoints are malformed")
    if [str(cast(JsonObject, item).get("path")) for item in process_checkpoints] != (
        expected_process_checkpoints
    ):
        raise ValueError("resolved-spec process checkpoint enumeration differs")
    for name, item in zip(expected_process_checkpoints, process_checkpoints, strict=True):
        path = verify_reference(cast(JsonObject, item), root=root.parent)
        _verify_process_checkpoint(
            path,
            expected_name=name,
            resolved_root=root.parent,
            artifact_root=artifact_root,
        )


def _verify_collection_closure(spec: JsonObject, replay_root: Path) -> None:
    """Run the maintained semantic handoff validator from the sealed collection checkpoint."""
    checkpoint = load_object(replay_root / "identity_checkpoints_v1/stages/collection_handoff.json")
    outputs = checkpoint.get("outputs")
    scope_id = outputs.get("scope_id") if isinstance(outputs, dict) else None
    if checkpoint.get("verified") is not True or not isinstance(scope_id, str):
        raise ValueError("collection checkpoint lacks verified scope identity")
    if spec.get("schema_version") == "er_commons.task06g.collection_execution_template.v1":
        from er_commons.artifact_verification import VerificationBudget
        from er_commons.collection_processing.preflight import prepare_collection_run

        closure = cast(JsonObject, spec["resolver_closure"])
        collection_spec = Path(cast(str, closure["collection_spec"]))
        artifact_root = _artifact_root(spec)
        run = prepare_collection_run(artifact_root, collection_spec, budget=VerificationBudget())
        schema_path = (
            Path(cast(str, spec["repository_working_directory"]))
            / "benchmarks/er_bench/schemas/collection_processing/v3/records.schema.json"
        )
        verified = validate_collection_handoff(
            extraction_root=run.extraction_root,
            scope_id=scope_id,
            schema_path=schema_path,
            data_root=artifact_root,
            document_input_root=run.imported_document_root,
        )
    else:
        schema_path = (
            Path(cast(str, spec["repository_working_directory"]))
            / "benchmarks/er_bench/schemas/collection_processing/v2/records.schema.json"
        )
        verified = validate_collection_handoff(
            extraction_root=replay_root / "document_publications",
            scope_id=scope_id,
            schema_path=schema_path,
        )
    if (
        verified.status != "ready"
        or verified.verified_document_count != 35
        or verified.task04_status != "not_evaluated"
    ):
        raise ValueError("collection handoff semantic closure differs")


def _binding_evidence(execution: JsonObject) -> tuple[list[JsonObject], list[JsonObject]]:
    """Verify the exact launch-intent or resume-receipt chain sealed by the driver argv."""
    command = execution.get("command")
    if not isinstance(command, list) or any(not isinstance(item, str) for item in command):
        raise ValueError("terminal execution lacks exact driver command")
    try:
        path_index = command.index("--binding-path") + 1
        digest_index = command.index("--binding-sha256") + 1
        binding_path = Path(command[path_index])
        binding_digest = command[digest_index]
    except (ValueError, IndexError) as error:
        raise ValueError("terminal driver command lacks explicit binding") from error
    binding_ref = reference(binding_path)
    if binding_ref["sha256"] != binding_digest:
        raise ValueError("terminal driver binding digest mismatch")
    binding = load_object(binding_path)
    preserved = binding.get("preserved_evidence_roots")
    if not isinstance(preserved, list) or any(not isinstance(item, dict) for item in preserved):
        raise ValueError("terminal binding lacks explicit preserved evidence roots")
    preserved_records = [cast(JsonObject, item) for item in preserved]
    for item in preserved_records:
        verify_evidence_root_record(item)
    schema = binding.get("schema_version")
    if schema == "er_commons.task06g.launch_intent.v1":
        dispatch_path = binding_path.parent / "dispatch_record.json"
        manifest_path = binding_path.parent / "packet_manifest.json"
        dispatch = load_object(dispatch_path)
        if dispatch.get("driver_argv") != command:
            raise ValueError("terminal driver command differs from initial dispatch")
        intent_ref = dispatch.get("launch_intent")
        if (
            not isinstance(intent_ref, dict)
            or verify_reference(intent_ref, root=binding_path.parent) != binding_path.resolve()
        ):
            raise ValueError("dispatch does not bind the selected launch intent")
        manifest = load_object(manifest_path)
        manifest_files = manifest.get("files")
        if not isinstance(manifest_files, list) or len(manifest_files) != 2:
            raise ValueError("launch packet manifest has unexpected closure")
        for item in manifest_files:
            if not isinstance(item, dict):
                raise ValueError("launch packet manifest reference is malformed")
            verify_reference(item, root=binding_path.parent)
        recovery = binding.get("prelaunch_recovery_receipt")
        evidence = [binding_ref, reference(dispatch_path), reference(manifest_path)]
        if recovery is not None:
            if not isinstance(recovery, dict):
                raise ValueError("launch intent recovery binding is malformed")
            verify_reference(recovery)
            evidence.append(dict(recovery))
        return evidence, preserved_records
    if schema == "er_commons.task06g.resume_receipt.v1":
        launch_path = binding_path.parent / "resume_launch_record.json"
        launch = load_object(launch_path)
        if launch.get("driver_argv") != command:
            raise ValueError("terminal driver command differs from resume launch")
        receipt_ref = launch.get("resume_receipt")
        if (
            not isinstance(receipt_ref, dict)
            or verify_reference(receipt_ref) != binding_path.resolve()
        ):
            raise ValueError("resume launch does not bind the selected receipt")
        return [binding_ref, reference(launch_path)], preserved_records
    raise ValueError("terminal driver binding has an unsupported schema")


def _ledger_siblings(spec: JsonObject) -> list[Path]:
    values = spec.get("ledger_sibling_roots")
    if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
        raise ValueError("execution spec requires explicit ledger_sibling_roots")
    roots = [Path(item).resolve() for item in values]
    if len(set(roots)) != len(roots):
        raise ValueError("execution spec repeats a ledger sibling root")
    return roots


def _ordinal(path: Path, prefix: str) -> int:
    """Parse one explicitly supplied positive attempt ordinal."""
    suffix = path.name.removeprefix(prefix)
    if path.name == suffix or not suffix.isdigit() or int(suffix) < 1:
        raise ValueError(f"invalid attempt root name: {path.name}")
    return int(suffix)


def _verify_finalization_amendment(
    amendment_path: Path,
    *,
    spec: JsonObject,
    execution_attempt_root: Path,
    finalization_attempt_root: Path,
    replay_root: Path,
) -> JsonObject:
    """Verify one exact post-execution finalizer repair without rebinding production."""
    amendment = load_object(amendment_path)
    expected_keys = {
        "schema_version",
        "status",
        "scope",
        "original_generation",
        "original_finalizer_owner",
        "corrected_finalizer_owner",
        "original_wrapper_owner",
        "corrected_wrapper_owner",
        "regression_test",
        "selected_execution",
        "selected_launch_intent",
        "selected_dispatch_record",
        "failed_finalization",
        "required_output_evidence",
        "execution_attempts_present",
        "execution_attempts_unused",
        "next_finalization_attempt_root",
        "production_outputs_rerun",
        "source_or_model_execution_required",
    }
    if amendment.get("schema_version") == "er_commons.task06g.finalization_amendment.v2":
        expected_keys.update(
            {
                "prior_finalization_amendment",
                "prior_finalization_receipt",
                "prior_readiness_candidate",
            }
        )
    if set(amendment) != expected_keys:
        raise ValueError("finalization amendment fields differ")
    if (
        amendment.get("schema_version")
        not in {
            "er_commons.task06g.finalization_amendment.v1",
            "er_commons.task06g.finalization_amendment.v2",
        }
        or amendment.get("status") != "approved_for_independent_review"
        or amendment.get("scope") != "unused_execution_ordinal_enumeration_only"
        or amendment.get("production_outputs_rerun") is not False
        or amendment.get("source_or_model_execution_required") is not False
        or amendment.get("next_finalization_attempt_root")
        != str(finalization_attempt_root.resolve())
    ):
        raise ValueError("finalization amendment scope differs")
    generation_path = Path(cast(str, spec["generation_spec"])).resolve()
    if verify_reference(cast(JsonObject, amendment["original_generation"])) != generation_path:
        raise ValueError("finalization amendment generation differs")
    generation = load_object(generation_path)
    owners = generation.get("generator_files")
    if not isinstance(owners, list):
        raise ValueError("frozen generation owner inventory is malformed")
    original = amendment.get("original_finalizer_owner")
    if not isinstance(original, dict) or original not in owners:
        raise ValueError("original finalizer owner is not frozen in generation")
    repository_root = generation_path.parents[3]
    corrected = verify_reference(
        cast(JsonObject, amendment["corrected_finalizer_owner"]), root=repository_root
    )
    if corrected != (repository_root / "src/er_commons/task06g/finalization.py").resolve():
        raise ValueError("corrected finalizer owner path differs")
    original_wrapper = amendment.get("original_wrapper_owner")
    if not isinstance(original_wrapper, dict) or original_wrapper not in owners:
        raise ValueError("original finalizer wrapper is not frozen in generation")
    corrected_wrapper = verify_reference(
        cast(JsonObject, amendment["corrected_wrapper_owner"]), root=repository_root
    )
    if corrected_wrapper != (repository_root / "scripts/finalize_task06g_readiness.py").resolve():
        raise ValueError("corrected finalizer wrapper path differs")
    regression = verify_reference(
        cast(JsonObject, amendment["regression_test"]), root=repository_root
    )
    if regression != (repository_root / "tests/test_task06g_orchestration.py").resolve():
        raise ValueError("finalization amendment regression test differs")
    if (
        verify_reference(cast(JsonObject, amendment["selected_execution"]))
        != (execution_attempt_root / "execution.json").resolve()
    ):
        raise ValueError("finalization amendment selected execution differs")
    for field, expected in (
        ("selected_launch_intent", replay_root.parent / "initial_launch_v38/launch_intent.json"),
        (
            "selected_dispatch_record",
            replay_root.parent / "initial_launch_v38/dispatch_record.json",
        ),
        ("failed_finalization", replay_root.parent / "finalization_attempt_v1/failure.json"),
    ):
        if verify_reference(cast(JsonObject, amendment[field])) != expected.resolve():
            raise ValueError(f"finalization amendment {field} differs")
    required = amendment.get("required_output_evidence")
    if not isinstance(required, list) or any(not isinstance(item, dict) for item in required):
        raise ValueError("finalization amendment output evidence is malformed")
    expected_required = [reference(path) for path in _required_paths(spec, replay_root)]
    if required != expected_required:
        raise ValueError("finalization amendment output evidence differs")
    present = amendment.get("execution_attempts_present")
    unused = amendment.get("execution_attempts_unused")
    if (
        not isinstance(present, list)
        or any(not isinstance(item, int) or item < 1 for item in present)
        or present != sorted(set(present))
        or not isinstance(unused, list)
        or any(not isinstance(item, int) or item < 1 for item in unused)
        or unused != sorted(set(unused))
        or set(present) & set(unused)
    ):
        raise ValueError("finalization amendment attempt enumeration is malformed")
    observed_attempts = sorted(
        _ordinal(path, "execution_attempt_v")
        for path in replay_root.parent.glob("execution_attempt_v*")
        if path.is_dir()
    )
    if observed_attempts != present or any(
        (replay_root.parent / f"execution_attempt_v{number}").exists() for number in unused
    ):
        raise ValueError("finalization amendment attempt enumeration differs")
    if amendment.get("schema_version") == "er_commons.task06g.finalization_amendment.v2":
        prior_amendment = verify_reference(
            cast(JsonObject, amendment["prior_finalization_amendment"])
        )
        if prior_amendment.name != "task06g_finalization_amendment_v1.json":
            raise ValueError("prior finalization amendment path differs")
        prior_receipt = verify_reference(cast(JsonObject, amendment["prior_finalization_receipt"]))
        expected_receipt = replay_root.parent / "finalization_attempt_v2/validation_receipt.json"
        if prior_receipt != expected_receipt.resolve():
            raise ValueError("prior finalization receipt path differs")
        prior_candidate = amendment.get("prior_readiness_candidate")
        if not isinstance(prior_candidate, list) or any(
            not isinstance(item, dict) for item in prior_candidate
        ):
            raise ValueError("prior readiness candidate evidence is malformed")
        expected_candidate = replay_root / "readiness_candidates/finalization_attempt_v2"
        if prior_candidate != [
            reference(expected_candidate / name)
            for name in ("artifact_inventory.json", "readiness.json", "completion.json")
        ]:
            raise ValueError("prior readiness candidate evidence differs")
    return reference(amendment_path)


def _required_paths(spec: JsonObject, replay_root: Path) -> list[Path]:
    """Return the explicit finalization evidence paths without reading payload sources."""
    finalization = spec.get("finalization")
    values = (
        finalization.get("required_files")
        if isinstance(finalization, dict)
        else spec.get("finalization_required_files")
    )
    if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
        raise ValueError("execution spec requires finalization evidence paths")
    return [replay_root / cast(str, item) for item in values]


def _verify_external_namespace_closure(
    *,
    spec: JsonObject,
    execution_spec: Path,
    replay_root: Path,
    execution_attempt_root: Path,
    finalization_attempt_root: Path,
    binding_evidence: list[JsonObject],
    preserved_records: list[JsonObject],
) -> list[JsonObject]:
    """Require every sibling namespace to be selected by sealed or ordinal evidence."""
    parent = replay_root.resolve().parent
    if (
        execution_attempt_root.resolve().parent != parent
        or finalization_attempt_root.resolve().parent != parent
    ):
        raise ValueError("Task 06G attempt roots must be siblings of the replay root")
    execution_number = _ordinal(execution_attempt_root, "execution_attempt_v")
    finalization_number = _ordinal(finalization_attempt_root, "finalization_attempt_v")
    roots = {verify_evidence_root_record(item) for item in preserved_records}
    roots.add(Path(str(binding_evidence[0]["path"])).resolve().parent)
    for path in parent.iterdir():
        if path.is_dir() and path.name.startswith("execution_attempt_v"):
            if _ordinal(path, "execution_attempt_v") <= execution_number:
                roots.add(path.resolve())
        if path.is_dir() and path.name.startswith("finalization_attempt_v"):
            if _ordinal(path, "finalization_attempt_v") < finalization_number:
                roots.add(path.resolve())
    declared = set(_ledger_siblings(spec))
    if not declared.issubset(roots):
        raise ValueError("execution-spec ledger root is absent from sealed evidence")
    observed: set[Path] = set()
    for path in parent.iterdir():
        resolved = path.resolve()
        if resolved == replay_root.resolve() or resolved == finalization_attempt_root.resolve():
            continue
        if resolved == execution_spec.resolve():
            continue
        if path.is_symlink() or not path.is_dir():
            raise ValueError(f"unexpected non-directory Task 06G sibling: {path}")
        observed.add(resolved)
    if observed != roots:
        raise ValueError(
            "Task 06G has unenumerated evidence siblings: "
            f"expected={sorted(map(str, roots))}, observed={sorted(map(str, observed))}"
        )
    return [evidence_root_record(path) for path in sorted(roots)]


def _verify_compact_completion(root: Path, kind: str) -> None:
    """Validate a compact completion-last publication and its exact inventory."""
    completion = load_object(root / "completion.json")
    inventory_path = root / "artifact_inventory.json"
    inventory = load_object(inventory_path)
    if (
        completion.get("schema_version") != f"er_commons.task06g.{kind}_completion.v1"
        or completion.get("status") != "complete"
        or completion.get("task04_status") != "not_evaluated"
        or completion.get("completion_last") is not True
    ):
        raise ValueError(f"Task 06G {kind} completion semantics differ")
    inventory_ref = completion.get("artifact_inventory")
    if (
        not isinstance(inventory_ref, dict)
        or verify_reference(inventory_ref, root=root) != inventory_path
    ):
        raise ValueError(f"Task 06G {kind} completion inventory binding differs")
    files = inventory.get("files")
    if not isinstance(files, list) or any(not isinstance(item, dict) for item in files):
        raise ValueError(f"Task 06G {kind} inventory is malformed")
    for item in files:
        verify_reference(cast(JsonObject, item), root=root)
    expected = {str(cast(JsonObject, item)["path"]) for item in files} | {
        "artifact_inventory.json",
        "completion.json",
    }
    observed = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if expected != observed:
        raise ValueError(f"Task 06G {kind} managed-file closure differs")


def _failure(finalization_root: Path, error: Exception) -> None:
    finalization_root.mkdir(parents=True, exist_ok=False)
    (finalization_root / "failure.json").write_bytes(
        canonical_bytes(
            {
                "schema_version": "er_commons.task06g.finalization_failure.v1",
                "status": "failed",
                "error": str(error),
            }
        )
    )


def _verify_readiness_candidate(candidate: Path) -> Path:
    """Verify one immutable three-record readiness candidate after atomic publication."""
    expected = {"artifact_inventory.json", "readiness.json", "completion.json"}
    observed = {path.name for path in candidate.iterdir() if path.is_file()}
    if observed != expected or any(path.is_dir() for path in candidate.iterdir()):
        raise ValueError("readiness candidate managed-file closure differs")
    inventory_path = candidate / "artifact_inventory.json"
    readiness_path = candidate / "readiness.json"
    inventory_bytes = inventory_path.read_bytes()
    readiness_bytes = readiness_path.read_bytes()
    inventory = load_object(inventory_path)
    readiness = load_object(readiness_path)
    completion = load_object(candidate / "completion.json")
    if (
        readiness.get("status") != "ready_for_review"
        or readiness.get("inventory_sha256") != sha256_bytes(inventory_bytes)
        or completion.get("status") != "complete"
        or completion.get("inventory_sha256") != sha256_bytes(inventory_bytes)
        or completion.get("readiness") != content_reference("readiness.json", readiness_bytes)
        or completion.get("execution") != readiness.get("execution")
        or completion.get("finalization_receipt") != readiness.get("finalization_receipt")
        or completion.get("binding_evidence") != readiness.get("binding_evidence")
    ):
        raise ValueError("readiness candidate semantic binding differs")
    external = inventory.get("external_evidence_roots")
    replay_record = inventory.get("replay_root")
    if (
        not isinstance(external, list)
        or any(not isinstance(item, dict) for item in external)
        or not isinstance(replay_record, dict)
    ):
        raise ValueError("readiness inventory root enumeration is malformed")
    for item in external:
        verify_evidence_root_record(cast(JsonObject, item))
    finalization_ref = readiness.get("finalization_receipt")
    if not isinstance(finalization_ref, dict):
        raise ValueError("readiness candidate lacks finalization receipt binding")
    finalization_receipt = load_object(verify_reference(finalization_ref))
    if finalization_receipt.get("status") != "passed":
        raise ValueError("readiness finalization receipt is not passed")
    binding = readiness.get("binding_evidence")
    if not isinstance(binding, list) or any(not isinstance(item, dict) for item in binding):
        raise ValueError("readiness launch binding evidence is malformed")
    for item in binding:
        verify_reference(cast(JsonObject, item))
    _verify_replay_record_excluding_candidate(cast(JsonObject, replay_record), candidate)
    return candidate


def _verify_replay_record_excluding_candidate(record: JsonObject, candidate: Path) -> None:
    """Verify the pre-readiness replay closure while excluding the sealed candidate itself."""
    raw_root, raw_files = record.get("path"), record.get("files")
    if not isinstance(raw_root, str) or not isinstance(raw_files, list):
        raise ValueError("readiness replay-root record is malformed")
    root = Path(raw_root).resolve()
    payload_references = _payload_inventory_references(root)
    for item in raw_files:
        if not isinstance(item, dict):
            raise ValueError("readiness replay-root file reference is malformed")
        relative = item.get("path")
        if not isinstance(relative, str):
            raise ValueError("readiness replay-root file path is malformed")
        path = (root / relative).resolve()
        if path.suffix.lower() in FORBIDDEN_PAYLOAD_SUFFIXES:
            if payload_references.get(path) != item:
                raise ValueError(f"prohibited payload inventory reference differs: {path}")
        else:
            verify_reference(item, root=root)
    observed = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not path.is_relative_to(candidate.resolve())
    }
    expected = {str(cast(JsonObject, item)["path"]) for item in raw_files}
    if observed != expected:
        raise ValueError("pre-readiness replay managed-file closure differs")


def finalize_readiness(
    execution_spec: Path,
    execution_attempt_root: Path,
    finalization_attempt_root: Path,
    replay_root: Path,
    *,
    hooks: FinalizationHooks | None = None,
    finalization_amendment: Path | None = None,
) -> Path:
    """Validate terminal evidence and atomically publish a completion-last candidate."""
    candidate = replay_root / "readiness_candidates" / finalization_attempt_root.name
    if finalization_attempt_root.exists():
        if candidate.is_dir():
            return _verify_readiness_candidate(candidate)
        raise FileExistsError(f"finalization attempt exists: {finalization_attempt_root}")
    active_hooks = hooks or FinalizationHooks()
    try:
        spec = load_object(execution_spec)
        total_cap = execution_total_cap(spec)
        execution, execution_ref = _terminal_execution(execution_attempt_root)
        binding_evidence, preserved_records = _binding_evidence(execution)
        if finalization_amendment is not None:
            binding_evidence.append(
                _verify_finalization_amendment(
                    finalization_amendment,
                    spec=spec,
                    execution_attempt_root=execution_attempt_root,
                    finalization_attempt_root=finalization_attempt_root,
                    replay_root=replay_root,
                )
            )
        evidence = _required_evidence(spec, replay_root)
        external_roots = _verify_external_namespace_closure(
            spec=spec,
            execution_spec=execution_spec,
            replay_root=replay_root,
            execution_attempt_root=execution_attempt_root,
            finalization_attempt_root=finalization_attempt_root,
            binding_evidence=binding_evidence,
            preserved_records=preserved_records,
        )
        ledger_total = _tree_bytes(replay_root) + sum(
            int(item["byte_count"]) for item in external_roots
        )
        if ledger_total >= total_cap:
            raise ValueError("Task 06G cumulative evidence exceeds the configured cap")
        receipt: JsonObject = {
            "schema_version": "er_commons.task06g.finalization_receipt.v1",
            "status": "passed",
            "execution_spec": reference(execution_spec),
            "execution": execution_ref,
            "required_evidence": evidence,
            "binding_evidence": binding_evidence,
            "preserved_evidence_roots": external_roots,
            "observed_bytes_before_finalization": ledger_total,
        }
        finalization_attempt_root.mkdir(parents=True, exist_ok=False)
        receipt_path = finalization_attempt_root / "validation_receipt.json"
        receipt_path.write_bytes(canonical_bytes(receipt))
        finalized_external_roots = [
            *external_roots,
            evidence_root_record(finalization_attempt_root),
        ]
        replay_record = evidence_root_record(replay_root)
        pre_readiness_bytes = int(replay_record["byte_count"]) + sum(
            int(item["byte_count"]) for item in finalized_external_roots
        )
        inventory: JsonObject = {
            "schema_version": "er_commons.task06g.readiness_inventory.v1",
            "execution_spec": reference(execution_spec),
            "replay_root": replay_record,
            "external_evidence_roots": finalized_external_roots,
            "selected_required_evidence": evidence,
            "selected_binding_evidence": binding_evidence,
            "selected_execution": execution_ref,
            "selected_finalization_receipt": reference(receipt_path),
            "file_count": int(replay_record["file_count"])
            + sum(int(item["file_count"]) for item in finalized_external_roots),
            "byte_count": pre_readiness_bytes,
        }
        inventory_bytes = canonical_bytes(inventory)
        readiness: JsonObject = {
            "schema_version": "er_commons.task06g.readiness_receipt.v1",
            "status": "ready_for_review",
            "inventory_sha256": sha256_bytes(inventory_bytes),
            "execution": execution_ref,
            "finalization_receipt": reference(receipt_path),
            "binding_evidence": binding_evidence,
        }
        readiness_bytes = canonical_bytes(readiness)
        completion: JsonObject = {
            "schema_version": "er_commons.task06g.readiness_completion.v1",
            "status": "complete",
            "inventory_sha256": sha256_bytes(inventory_bytes),
            "readiness": content_reference("readiness.json", readiness_bytes),
            "execution": execution_ref,
            "finalization_receipt": reference(receipt_path),
            "binding_evidence": binding_evidence,
        }
        files = {
            "artifact_inventory.json": inventory_bytes,
            "readiness.json": readiness_bytes,
            "completion.json": canonical_bytes(completion),
        }
        projected = pre_readiness_bytes + sum(len(value) for value in files.values())
        if projected > total_cap:
            raise ValueError("prospective finalization would exceed the configured cap")

        def after_write(name: str) -> None:
            if name == "artifact_inventory.json":
                active_hooks.after_inventory()
            elif name == "readiness.json":
                active_hooks.after_readiness()
            elif name == "completion.json":
                active_hooks.after_completion()

        publish_directory_no_clobber(
            candidate,
            files,
            after_write=after_write,
            after_rename=active_hooks.after_rename,
        )
        return _verify_readiness_candidate(candidate)
    except Exception as error:
        if candidate.is_dir():
            pass
        elif not finalization_attempt_root.exists():
            _failure(finalization_attempt_root, error)
        elif not (finalization_attempt_root / "failure.json").exists():
            (finalization_attempt_root / "failure.json").write_bytes(
                canonical_bytes(
                    {
                        "schema_version": "er_commons.task06g.finalization_failure.v1",
                        "status": "failed",
                        "error": str(error),
                    }
                )
            )
        raise
