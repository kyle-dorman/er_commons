"""Immutable launch packets and detached Task 06G dispatch."""

from __future__ import annotations

import shlex
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from er_commons.task06g.core import (
    JsonObject,
    canonical_bytes,
    content_reference,
    load_object,
    publish_directory_no_clobber,
    reference,
    verify_reference,
)
from er_commons.task06g.packets import (
    COLLECTION_ONLY_COMPONENT_MAXIMA,
    COLLECTION_ONLY_PREDICTED_MAX_BYTES,
    DEFAULT_TOTAL_BYTES,
    enumerate_sibling_evidence,
    execution_limits,
    repository_root,
    resource_ledger,
    tmux_is_live,
    verify_evidence_root_record,
    verify_resume_receipt_current,
)


def _validate_prepared_inputs(execution_spec: Path, replay: Path) -> None:
    """Verify the exact compact preparation closure before sealing a launch packet."""
    execution = load_object(execution_spec)
    generation_path = Path(cast(str, execution["generation_spec"])).resolve()
    generation = load_object(generation_path)
    from er_commons.task06g.phases import _roots

    _, _, artifact_root = _roots(generation_path, generation)
    _verify_full_initial_packet(generation_path, replay)
    initial = replay / "resolved_specs_v1/00_initial"
    document_spec = initial / "task06g_document_v1.json"
    collection_spec = initial / "task06g_collection_v1.json"
    identity_path = initial / "production_identity.json"
    phase_manifest = initial / "phase_manifest.json"
    checkpoint = initial / "pre_execution_production_identity_checkpoint.json"
    for path in (document_spec, collection_spec, identity_path, phase_manifest, checkpoint):
        if not path.is_file():
            raise ValueError(f"initial resolved closure is incomplete: {path}")
    phase = load_object(phase_manifest)
    managed = cast(list[JsonObject], phase.get("managed_files", []))
    for row in managed:
        verify_reference(row, root=initial)
    expected_initial = {str(row["path"]) for row in managed} | {"phase_manifest.json"}
    observed_initial = {
        path.relative_to(initial).as_posix() for path in initial.rglob("*") if path.is_file()
    }
    if observed_initial != expected_initial:
        raise ValueError("initial resolved phase contains an unexplained managed file")
    production = load_object(identity_path)
    check = load_object(checkpoint)
    if (
        check.get("verified") is not True
        or check.get("derived_id") != check.get("recomputed_id")
        or check.get("derived_id") != production.get("extraction_id")
    ):
        raise ValueError("pre-execution production identity checkpoint differs")

    inputs = replay / "inputs"
    expected = {"task06g_source_family_catalog_v1.json", "task03h_preparation_readiness.json"}
    if not inputs.is_dir():
        raise ValueError("prepared compact input directory is absent")
    observed = {path.name for path in inputs.iterdir() if path.is_file()}
    if observed != expected or any(path.is_dir() for path in inputs.iterdir()):
        raise ValueError("prepared compact input closure differs")
    catalog_path = inputs / "task06g_source_family_catalog_v1.json"
    readiness = load_object(inputs / "task03h_preparation_readiness.json")
    document_ref, collection_ref, identity_ref, catalog_ref = (
        reference(document_spec),
        reference(collection_spec),
        reference(identity_path),
        reference(catalog_path),
    )
    source_scope = readiness.get("source_scope")
    catalog = readiness.get("catalog")
    if not isinstance(source_scope, dict) or not isinstance(catalog, dict):
        raise ValueError("preparation readiness lacks source scope or catalog")
    if (
        readiness.get("status") != "ready_for_user_authorized_clean_run"
        or readiness.get("production_extraction_id") != production.get("extraction_id")
        or readiness.get("production_identity_sha256") != identity_ref["sha256"]
        or readiness.get("document_run_spec_sha256") != document_ref["sha256"]
        or readiness.get("collection_run_spec_sha256") != collection_ref["sha256"]
        or source_scope.get("source_count") != 35
        or source_scope.get("page_count") != 49_022
        or readiness.get("source_pdf_bytes_read") is not False
        or readiness.get("model_files_read") is not False
        or readiness.get("producer_identity_derivation_run") is not False
        or readiness.get("execution_boundary") != "source/model execution not run"
        or catalog.get("staged_path") != catalog_path.relative_to(artifact_root).as_posix()
        or catalog.get("sha256") != catalog_ref["sha256"]
        or catalog.get("byte_size") != catalog_ref["byte_size"]
    ):
        raise ValueError("prepared input readiness differs from the accepted Task 06G closure")
    for name in ("document_publications", "document_records", "document_links"):
        root = replay / name
        if root.exists() and any(root.rglob("completion_record.json")):
            raise ValueError("prepared replay root already contains a completed candidate")


def _validate_collection_prepared_inputs(execution_spec: Path, replay: Path) -> None:
    """Verify the exact v33 initial phase and all pinned imported document evidence."""
    from er_commons.artifact_verification import VerificationBudget
    from er_commons.collection_processing.preflight import prepare_collection_run
    from er_commons.collection_processing.production_identity import (
        validate_collection_production_identity,
    )
    from er_commons.task06g.phases import _roots

    spec = load_object(execution_spec)
    generation_path = Path(cast(str, spec["generation_spec"])).resolve()
    generation = load_object(generation_path)
    _, repository, artifacts = _roots(generation_path, generation)
    _verify_collection_initial_packet(generation_path, replay)
    initial = replay / "resolved_specs_v1/00_initial"
    closure = cast(JsonObject, spec["resolver_closure"])
    collection_spec = Path(cast(str, closure["collection_spec"])).resolve()
    if (
        execution_spec.resolve() != (initial / "task06g_collection_execution_v1.json").resolve()
        or collection_spec != (initial / "task06g_collection_only_v1.json").resolve()
    ):
        raise ValueError("collection-only launch specs are outside the resolved initial phase")
    identity_path = initial / "collection_production_identity.json"
    selection_path = initial / "task06g_imported_document_selection_v1.json"
    checkpoint_path = initial / "pre_execution_collection_identity_checkpoint.json"
    phase_manifest = initial / "phase_manifest.json"
    required = (
        execution_spec,
        collection_spec,
        identity_path,
        selection_path,
        checkpoint_path,
        phase_manifest,
    )
    if any(not path.is_file() for path in required):
        raise ValueError("collection-only initial resolved closure is incomplete")
    phase = load_object(phase_manifest)
    managed = phase.get("managed_files")
    if not isinstance(managed, list) or any(not isinstance(row, dict) for row in managed):
        raise ValueError("collection-only initial phase manifest is malformed")
    for row in managed:
        verify_reference(cast(JsonObject, row), root=initial)
    expected = {str(cast(JsonObject, row)["path"]) for row in managed} | {"phase_manifest.json"}
    observed = {
        path.relative_to(initial).as_posix() for path in initial.rglob("*") if path.is_file()
    }
    if observed != expected:
        raise ValueError("collection-only initial phase contains an unexplained managed file")
    checkpoint = load_object(checkpoint_path)
    identity = load_object(identity_path)
    if (
        checkpoint.get("verified") is not True
        or checkpoint.get("derived_id") != checkpoint.get("recomputed_id")
        or checkpoint.get("derived_id") != identity.get("collection_production_id")
    ):
        raise ValueError("pre-execution collection identity checkpoint differs")
    selection_ref = cast(
        JsonObject, cast(JsonObject, checkpoint["outputs"])["imported_selection_ref"]
    )
    validated = validate_collection_production_identity(
        identity,
        repository_root=repository,
        artifact_root=artifacts,
        expected_imported_selection_ref=selection_ref,
        expected_output_namespace=replay.joinpath("document_publications")
        .resolve()
        .relative_to(artifacts)
        .as_posix(),
    )
    run = prepare_collection_run(
        artifacts,
        collection_spec,
        budget=VerificationBudget(),
    )
    if (
        run.collection_production_id != validated.collection_production_id
        or run.imported_selection is None
        or len(run.imported_selection.candidates) != 35
        or tuple(item.physical_source_id for item in run.imported_selection.candidates)
        != run.collection_spec.source_ids
        or run.extraction_root != (replay / "document_publications").resolve()
    ):
        raise ValueError("collection-only prepared input closure differs")
    if run.extraction_root.exists():
        raise ValueError("collection-only output root must be absent before initial launch")


def _verify_collection_initial_packet(generation_spec: Path, replay: Path) -> None:
    """Require the complete prelaunch replay tree to equal the frozen initial packet."""
    from er_commons.task06g.phases import _phase_files

    resolved = replay / "resolved_specs_v1"
    directory, files = _phase_files(generation_spec, "initial", resolved)
    if directory != "00_initial":
        raise ValueError("collection-only initial packet uses an unexpected phase directory")

    expected_files = {
        Path("resolved_specs_v1") / directory / relative: content
        for relative, content in files.items()
    }
    expected_paths = set(expected_files)
    for path in expected_files:
        expected_paths.update(path.parents)
    expected_paths.discard(Path("."))

    if not replay.is_dir() or replay.is_symlink():
        raise ValueError("collection-only prelaunch replay is not a real directory")
    observed_paths: set[Path] = set()
    for path in replay.rglob("*"):
        relative = path.relative_to(replay)
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(
                f"collection-only prelaunch replay contains an invalid path: {relative}"
            )
        observed_paths.add(relative)
    if observed_paths != expected_paths:
        raise ValueError("collection-only prelaunch replay differs from frozen initial packet")
    for relative, content in expected_files.items():
        if (replay / relative).read_bytes() != content:
            raise ValueError("collection-only prelaunch replay differs from frozen initial packet")


def _verify_full_initial_packet(generation_spec: Path, replay: Path) -> None:
    """Regenerate and byte-compare the full replay's frozen initial resolved packet."""
    from er_commons.task06g.phases import _phase_files

    resolved = replay / "resolved_specs_v1"
    directory, files = _phase_files(generation_spec, "initial", resolved)
    if directory != "00_initial":
        raise ValueError("full replay initial packet uses an unexpected phase directory")
    initial = resolved / directory
    expected_paths = {Path(relative) for relative in files}
    observed_paths = {
        path.relative_to(initial)
        for path in initial.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if (
        not initial.is_dir()
        or initial.is_symlink()
        or observed_paths != expected_paths
        or any(path.is_symlink() for path in initial.rglob("*"))
    ):
        raise ValueError("full replay initial phase differs from frozen initial packet")
    for relative, content in files.items():
        if (initial / relative).read_bytes() != content:
            raise ValueError("full replay initial phase differs from frozen initial packet")
    unexplained = [path for path in resolved.iterdir() if path.name != directory]
    if unexplained:
        raise ValueError("full replay contains a prelaunch resolved phase beyond initial")


def _driver(execution_spec: Path, binding: JsonObject) -> list[str]:
    return [
        "uv",
        "run",
        "python",
        "scripts/run_task06g_replay.py",
        "--execution-spec",
        str(execution_spec.resolve()),
        "--binding-path",
        cast(str, binding["path"]),
        "--binding-sha256",
        cast(str, binding["sha256"]),
    ]


def _environment() -> dict[str, str]:
    """Return the exact source-free/offline/thread environment sealed for every attempt."""
    return {
        "ER_COMMONS_DATA_ROOT": "/Volumes/x10pro/er_commons",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "OMP_NUM_THREADS": "4",
        "MKL_NUM_THREADS": "4",
        "OPENBLAS_NUM_THREADS": "4",
        "NUMEXPR_NUM_THREADS": "4",
        "PYTHONUNBUFFERED": "1",
    }


def _progress_root(replay: Path, attempt: Path, spec: JsonObject | None = None) -> Path:
    """Map one exact execution-attempt ordinal to its fresh progress namespace."""
    prefix = "execution_attempt_v"
    suffix = attempt.name.removeprefix(prefix)
    if not attempt.name.startswith(prefix) or not suffix.isdigit() or int(suffix) < 1:
        raise ValueError(f"invalid execution attempt root name: {attempt.name}")
    namespace = (
        "collection_progress"
        if spec is not None
        and spec.get("schema_version") == "er_commons.task06g.collection_execution_template.v1"
        else "document_progress"
    )
    return (replay / namespace / f"attempt_v{int(suffix)}").resolve()


def _supervisor(
    driver: list[str], replay: Path, attempt: Path, limits: JsonObject, environment: dict[str, str]
) -> list[str]:
    command = [
        "env",
        *(f"{name}={value}" for name, value in sorted(environment.items())),
        "uv",
        "run",
        "python",
        "-m",
        "er_commons.document_publication.background_execution",
        "--attempt-root",
        str(attempt.resolve()),
        "--output-root",
        str(replay.resolve()),
    ]
    defaults: dict[str, int | float] = {
        "max_swap_growth_bytes": 0,
        "sample_seconds": 0.1,
        "disk_sample_seconds": 1.0,
        "termination_grace_seconds": 15.0,
    }
    for name in ("max_seconds", "max_rss_bytes", "max_output_bytes", "min_free_bytes", *defaults):
        command.extend((f"--{name.replace('_', '-')}", str(limits.get(name, defaults.get(name)))))
    return [*command, "--", *driver]


def _records(
    execution_spec: Path,
    replay: Path,
    attempt: Path,
    launch: Path,
    recovery: Path | None,
    requested_start: str,
) -> tuple[dict[str, bytes], JsonObject]:
    spec = load_object(execution_spec)
    limits = dict(execution_limits(spec))
    preserved_roots = enumerate_sibling_evidence(
        replay.parent,
        excluded=[replay, attempt, launch, execution_spec],
    )
    recovery_record: JsonObject | None = None
    if recovery is None:
        if preserved_roots:
            raise ValueError("ordinary initial launch has unexplained evidence siblings")
    else:
        recovery_record = load_object(recovery)
        inherited = recovery_record.get("preserved_evidence_roots")
        if not isinstance(inherited, list) or any(not isinstance(item, dict) for item in inherited):
            raise ValueError("prelaunch recovery lacks explicit preserved evidence roots")
        expected_roots = {verify_evidence_root_record(cast(JsonObject, item)) for item in inherited}
        expected_roots.add(recovery.parent.resolve())
        if {Path(str(item["path"])).resolve() for item in preserved_roots} != expected_roots:
            raise ValueError("recovery-aware launch has unexplained evidence siblings")
    sibling_paths = [Path(str(item["path"])) for item in preserved_roots]
    total_cap = cast(int, limits["max_output_bytes"])
    ledger = (
        resource_ledger(replay, sibling_paths)
        if total_cap == DEFAULT_TOTAL_BYTES
        else resource_ledger(replay, sibling_paths, total_cap=total_cap)
    )
    collection_envelope: JsonObject | None = None
    if spec.get("schema_version") == "er_commons.task06g.collection_execution_template.v1":
        generation_path = Path(cast(str, spec["generation_spec"])).resolve()
        generation = load_object(generation_path)
        policy = generation.get("resource_policy")
        if (
            not isinstance(policy, dict)
            or policy.get("predicted_maximum_additional_bytes")
            != COLLECTION_ONLY_PREDICTED_MAX_BYTES
            or cast(int, ledger["maximum_additional_bytes"]) < COLLECTION_ONLY_PREDICTED_MAX_BYTES
        ):
            raise ValueError("collection-only resource envelope no longer fits")
        collection_envelope = {
            "mode": "collection_only_pinned_v32",
            "component_maxima": dict(COLLECTION_ONLY_COMPONENT_MAXIMA),
            "predicted_maximum_additional_bytes": COLLECTION_ONLY_PREDICTED_MAX_BYTES,
            "predicted_headroom_bytes": cast(int, ledger["maximum_additional_bytes"])
            - COLLECTION_ONLY_PREDICTED_MAX_BYTES,
            "source_payloads_read": False,
            "models_loaded": False,
        }
        if recovery_record is not None:
            prior_ledger = recovery_record.get("resource_ledger")
            prior_envelope = recovery_record.get("collection_only_resource_envelope")
            if (
                not isinstance(prior_ledger, dict)
                or not isinstance(prior_envelope, dict)
                or prior_envelope.get("predicted_maximum_additional_bytes")
                != COLLECTION_ONLY_PREDICTED_MAX_BYTES
                or prior_envelope.get("source_payloads_read") is not False
                or prior_envelope.get("models_loaded") is not False
            ):
                raise ValueError("collection-only prelaunch accounting is stale")
            _validate_collection_prelaunch_ledger(prior_ledger, ledger)
    limits["max_output_bytes"] = min(
        cast(int, limits["max_output_bytes"]), cast(int, ledger["supervisor_max_output_bytes"])
    )
    intent: JsonObject = {
        "schema_version": "er_commons.task06g.launch_intent.v1",
        "requested_start_time": requested_start,
        "working_directory": str(repository_root(spec)),
        "execution_spec": reference(execution_spec),
        "prelaunch_recovery_receipt": reference(recovery) if recovery else None,
        "replay_root": str(replay.resolve()),
        "attempt_root": str(attempt.resolve()),
        "progress_root": str(_progress_root(replay, attempt, spec)),
        "tmux_session": spec.get("tmux_session"),
        "log_path": str((attempt / "command.log").resolve()),
        "environment": _environment(),
        "resource_limits": limits,
        "resource_ledger": ledger,
        "preserved_evidence_roots": preserved_roots,
        "driver_argv_recipe": ["scripts/run_task06g_replay.py", "<launch-intent-ref>"],
    }
    if collection_envelope is not None:
        intent["collection_only_resource_envelope"] = collection_envelope
    intent_bytes = canonical_bytes(intent)
    intent_ref = content_reference("launch_intent.json", intent_bytes)
    driver = _driver(
        execution_spec,
        {"path": str((launch / "launch_intent.json").resolve()), "sha256": intent_ref["sha256"]},
    )
    dispatch: JsonObject = {
        "schema_version": "er_commons.task06g.dispatch_record.v1",
        "launch_intent": intent_ref,
        "driver_argv": driver,
        "supervisor_argv": _supervisor(driver, replay, attempt, limits, _environment()),
    }
    files = {"launch_intent.json": intent_bytes, "dispatch_record.json": canonical_bytes(dispatch)}
    files["packet_manifest.json"] = canonical_bytes(
        {
            "schema_version": "er_commons.task06g.launch_packet.v1",
            "files": [content_reference(name, content) for name, content in sorted(files.items())],
        }
    )
    external_reserve = cast(int, ledger["prospective_external_reserve_bytes"])
    launch_packet_bytes = sum(len(content) for content in files.values())
    if launch_packet_bytes > external_reserve:
        raise ValueError("launch packet exceeds its prospective external resource reserve")
    return files, dispatch


def _validate_collection_prelaunch_ledger(
    prior: JsonObject,
    current: JsonObject,
) -> None:
    """Allow only the frozen initial-packet growth after the prelaunch snapshot."""
    fields = ("replay_bytes", "maximum_additional_bytes")
    if any(not isinstance(prior.get(name), int) for name in fields) or any(
        not isinstance(current.get(name), int) for name in fields
    ):
        raise ValueError("collection-only prelaunch ledger is malformed")
    prior_replay = cast(int, prior["replay_bytes"])
    current_replay = cast(int, current["replay_bytes"])
    initial_allowance = COLLECTION_ONLY_COMPONENT_MAXIMA["initial_specs_checkpoint_bytes"]
    if (
        prior.get("total_cap_bytes") != current.get("total_cap_bytes")
        or prior.get("prospective_external_reserve_bytes")
        != current.get("prospective_external_reserve_bytes")
        or current_replay < prior_replay
        or current_replay - prior_replay > initial_allowance
        or cast(int, current["maximum_additional_bytes"])
        > cast(int, prior["maximum_additional_bytes"])
    ):
        raise ValueError("collection-only prelaunch accounting is stale")


def build_launch_packet(
    execution_spec: Path,
    replay_root: Path,
    attempt_root: Path,
    launch_root: Path,
    *,
    binding_path: Path | None = None,
    reuse_exact: bool = False,
) -> tuple[Path, JsonObject]:
    """Publish or exactly verify one immutable initial launch packet."""
    spec = load_object(execution_spec)
    session = spec.get("tmux_session")
    if not isinstance(session, str) or attempt_root.exists() or tmux_is_live(session):
        raise ValueError("launch requires an inactive exact session and absent attempt root")
    if spec.get("schema_version") == "er_commons.task06g.collection_execution_template.v1":
        generation_path = Path(cast(str, spec["generation_spec"])).resolve()
        generation = load_object(generation_path)
        namespaces = generation.get("namespaces")
        if not isinstance(namespaces, dict):
            raise ValueError("collection-only generation lacks frozen namespaces")
        from er_commons.task06g.phases import _roots

        _, _, artifact_root = _roots(generation_path, generation)
        expected_replay = artifact_root / cast(str, namespaces.get("replay_root"))
        expected_attempt = artifact_root / cast(str, namespaces.get("attempt_root"))
        expected_launch = artifact_root / cast(str, namespaces.get("launch_root"))
        if (
            replay_root.resolve() != expected_replay.resolve()
            or attempt_root.resolve() != expected_attempt.resolve()
            or launch_root.resolve() != expected_launch.resolve()
        ):
            raise ValueError("collection-only launch paths differ from frozen namespaces")
    if spec.get("schema_version") in {
        "er_commons.task06g.execution_template.v1",
        "er_commons.task06g.collection_execution_template.v1",
    }:
        minimum_free = cast(int, execution_limits(spec)["min_free_bytes"])
        replay_free = shutil.disk_usage(replay_root).free
        attempt_free = shutil.disk_usage(attempt_root.parent).free
        if replay_free < minimum_free or attempt_free < minimum_free:
            raise ValueError("launch requires at least the reviewed minimum free bytes")
        if spec.get("schema_version") == "er_commons.task06g.collection_execution_template.v1":
            _validate_collection_prepared_inputs(execution_spec, replay_root)
        else:
            _validate_prepared_inputs(execution_spec, replay_root)
    requested = datetime.now(UTC).isoformat()
    if launch_root.exists():
        if not reuse_exact:
            raise FileExistsError(f"launch packet already exists: {launch_root}")
        requested = cast(
            str, load_object(launch_root / "launch_intent.json")["requested_start_time"]
        )
    files, dispatch = _records(
        execution_spec, replay_root, attempt_root, launch_root, binding_path, requested
    )
    if launch_root.exists():
        observed = {
            path.relative_to(launch_root).as_posix(): path.read_bytes()
            for path in launch_root.rglob("*")
            if path.is_file()
        }
        if observed != files:
            raise ValueError("existing launch packet differs from exact deterministic rebuild")
    else:
        publish_directory_no_clobber(launch_root, files)
    return launch_root / "dispatch_record.json", dispatch


def dispatch_tmux(session: str, working_directory: Path, argv: list[str]) -> None:
    """Dispatch one exact argv in detached tmux without argument interpolation."""
    command = "cd " + shlex.quote(str(working_directory.resolve())) + " && exec " + shlex.join(argv)
    subprocess.run(["tmux", "new-session", "-d", "-s", session, command], check=True)


def launch_initial(
    execution_spec: Path,
    replay_root: Path,
    attempt_root: Path,
    launch_root: Path,
    *,
    binding_path: Path | None = None,
    reuse_exact: bool = False,
) -> Path:
    """Seal an initial packet, then dispatch exactly its supervisor argv."""
    dispatch_path, dispatch = build_launch_packet(
        execution_spec,
        replay_root,
        attempt_root,
        launch_root,
        binding_path=binding_path,
        reuse_exact=reuse_exact,
    )
    spec = load_object(execution_spec)
    dispatch_tmux(
        cast(str, spec["tmux_session"]),
        repository_root(spec),
        cast(list[str], dispatch["supervisor_argv"]),
    )
    return dispatch_path


def launch_resume(receipt_path: Path) -> Path:
    """Verify one resume receipt and dispatch its reduced fresh attempt."""
    receipt, execution_spec, spec = verify_resume_receipt_current(receipt_path)
    replay = Path(cast(str, receipt["replay_root"]))
    attempt = Path(cast(str, receipt["next_attempt_root"]))
    progress = Path(cast(str, receipt["progress_root"]))
    expected_progress = _progress_root(replay, attempt, spec)
    attempt_number = int(attempt.name.removeprefix("execution_attempt_v"))
    expected_receipt_root = replay.parent / f"resume_preflight_v{attempt_number}"
    expected_session = f"{spec['tmux_session']}-attempt-v{attempt_number}"
    if (
        attempt.parent.resolve() != replay.parent.resolve()
        or receipt_path.parent.resolve() != expected_receipt_root.resolve()
        or progress.resolve() != expected_progress
        or receipt.get("tmux_session") != expected_session
    ):
        raise ValueError("resume receipt attempt paths or session differ from its exact ordinal")
    if attempt.exists() or progress.exists() or tmux_is_live(cast(str, receipt["tmux_session"])):
        raise ValueError("resume launch requires fresh attempt, progress, and tmux namespaces")
    limits = dict(execution_limits(spec))
    ledger = cast(JsonObject, receipt["resource_ledger"])
    limits["max_output_bytes"] = ledger["supervisor_max_output_bytes"]
    binding = reference(receipt_path)
    driver = _driver(execution_spec, binding)
    supervisor = _supervisor(driver, replay, attempt, limits, _environment())
    record = {
        "schema_version": "er_commons.task06g.resume_launch.v1",
        "resume_receipt": binding,
        "driver_argv": driver,
        "supervisor_argv": supervisor,
        "tmux_session": receipt["tmux_session"],
    }
    launch_path = receipt_path.parent / "resume_launch_record.json"
    if launch_path.exists():
        raise FileExistsError(f"resume launch record exists: {launch_path}")
    launch_path.write_bytes(canonical_bytes(record))
    dispatch_tmux(cast(str, receipt["tmux_session"]), repository_root(spec), supervisor)
    return launch_path
