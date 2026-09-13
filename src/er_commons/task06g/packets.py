"""Preflight and cumulative resource-ledger boundaries for Task 06G."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from er_commons.artifact_io import sha256_bytes, sha256_file
from er_commons.task06g.core import (
    FORBIDDEN_PAYLOAD_SUFFIXES,
    JsonObject,
    canonical_bytes,
    load_object,
    publish_directory_no_clobber,
    reference,
    verify_reference,
)

DEFAULT_TOTAL_BYTES = 32 * 1024**3
DEFAULT_RESERVE_BYTES = 64 * 1024**2
COLLECTION_ONLY_COMPONENT_MAXIMA: dict[str, int] = {
    "collection_publication_bytes": 235_064_214,
    "comparison_correspondence_bytes": 512 * 1024**2,
    "initial_specs_checkpoint_bytes": 64 * 1024**2,
    "attempt_log_terminal_metadata_bytes": 64 * 1024**2 + 65_536,
    "interrupted_staging_bytes": 256 * 1024**2,
    "finalization_readiness_bytes": 256 * 1024**2,
}
COLLECTION_ONLY_PREDICTED_MAX_BYTES = 1_443_089_302

if sum(COLLECTION_ONLY_COMPONENT_MAXIMA.values()) != COLLECTION_ONLY_PREDICTED_MAX_BYTES:
    raise RuntimeError("collection-only resource component maxima differ from their frozen total")


def _tree_bytes(root: Path) -> int:
    """Account regular-file bytes without opening payloads or following symlinks."""
    if not root.exists():
        return 0
    total = 0
    for directory, folders, files in os.walk(root):
        for name in folders + files:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError(f"resource accounting rejects symlink: {path}")
        total += sum((Path(directory) / name).stat().st_size for name in files)
    return total


def evidence_root_record(root: Path) -> JsonObject:
    """Seal small files and inherit inventory digests for prohibited payloads."""
    resolved = root.resolve()
    if not resolved.is_dir() or resolved.is_symlink():
        raise ValueError(f"evidence root must be a real directory: {root}")
    payload_references = _payload_inventory_references(resolved)
    files: list[JsonObject] = []
    for directory, folders, names in os.walk(resolved):
        for name in folders + names:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError(f"evidence enumeration rejects symlink: {path}")
        for name in sorted(names):
            path = Path(directory) / name
            if path.suffix.lower() in FORBIDDEN_PAYLOAD_SUFFIXES:
                inherited = payload_references.get(path.resolve())
                if inherited is None:
                    raise ValueError(f"prohibited payload lacks sealed inventory evidence: {path}")
                files.append(inherited)
            else:
                files.append(reference(path, root=resolved))
    files.sort(key=lambda item: str(item["path"]))
    return {
        "path": str(resolved),
        "file_count": len(files),
        "byte_count": sum(int(item["byte_size"]) for item in files),
        "files": files,
    }


def verify_evidence_root_record(value: JsonObject) -> Path:
    """Verify a sealed evidence root has exactly the enumerated managed files."""
    raw_root = value.get("path")
    raw_files = value.get("files")
    if not isinstance(raw_root, str) or not isinstance(raw_files, list):
        raise ValueError("evidence-root record requires path and files")
    root = Path(raw_root).resolve()
    payload_references = _payload_inventory_references(root)
    if len(raw_files) != len(
        {str(item.get("path")) for item in raw_files if isinstance(item, dict)}
    ):
        raise ValueError("evidence-root record repeats a file")
    for item in raw_files:
        if not isinstance(item, dict):
            raise ValueError("evidence-root file reference is malformed")
        relative = item.get("path")
        if not isinstance(relative, str):
            raise ValueError("evidence-root file path is malformed")
        path = (root / relative).resolve()
        if path.suffix.lower() in FORBIDDEN_PAYLOAD_SUFFIXES:
            if payload_references.get(path) != item:
                raise ValueError(f"prohibited payload inventory reference differs: {path}")
        else:
            verify_reference(item, root=root)
    observed = evidence_root_record(root)
    if observed != value:
        raise ValueError(f"evidence-root managed closure differs: {root}")
    return root


def _payload_inventory_references(root: Path) -> dict[Path, JsonObject]:
    """Resolve payload digests from contained producer inventories without opening payloads."""
    references: dict[Path, JsonObject] = {}
    inventory_paths = set(root.rglob("artifact_inventory.json")) | set(root.rglob("inventory.json"))
    for inventory_path in sorted(inventory_paths):
        if (
            inventory_path.is_symlink()
            or not inventory_path.is_file()
            or not inventory_path.resolve().is_relative_to(root)
        ):
            raise ValueError(
                f"artifact inventory is not a contained regular file: {inventory_path}"
            )
        inventory = load_object(inventory_path)
        rows = inventory.get("files")
        if not isinstance(rows, list):
            continue
        owner = (
            inventory_path.parent.parent
            if inventory_path.parent.name == "records"
            else inventory_path.parent
        )
        for row in rows:
            if not isinstance(row, dict):
                continue
            raw_relative = row.get("path", row.get("name"))
            if not isinstance(raw_relative, str):
                continue
            relative = Path(raw_relative)
            if (
                not raw_relative
                or raw_relative == "."
                or raw_relative != relative.as_posix()
                or relative.is_absolute()
                or ".." in relative.parts
            ):
                raise ValueError(f"unsafe artifact inventory path: {inventory_path}")
            candidate = (owner / relative).resolve()
            if (
                candidate.suffix.lower() not in FORBIDDEN_PAYLOAD_SUFFIXES
                or not candidate.is_relative_to(owner.resolve())
                or not candidate.is_relative_to(root)
            ):
                continue
            size = row.get("byte_size")
            digest = row.get("sha256")
            if candidate.is_symlink():
                raise ValueError(f"prohibited payload inventory metadata differs: {candidate}")
            if not candidate.exists():
                continue
            if (
                not candidate.is_file()
                or not isinstance(size, int)
                or candidate.stat().st_size != size
                or not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise ValueError(f"prohibited payload inventory metadata differs: {candidate}")
            inherited = {
                "path": candidate.relative_to(root).as_posix(),
                "sha256": digest,
                "byte_size": size,
            }
            existing = references.get(candidate)
            if existing is not None and existing != inherited:
                raise ValueError(f"conflicting payload inventory references: {candidate}")
            references[candidate] = inherited
    return references


def enumerate_sibling_evidence(parent: Path, *, excluded: list[Path]) -> list[JsonObject]:
    """Exhaustively seal direct sibling namespaces without pattern or recency selection."""
    resolved_parent = parent.resolve()
    excluded_set = {path.resolve() for path in excluded}
    records: list[JsonObject] = []
    for path in sorted(resolved_parent.iterdir() if resolved_parent.exists() else []):
        resolved = path.resolve()
        if resolved in excluded_set:
            continue
        if path.is_symlink() or not path.is_dir():
            raise ValueError(f"unexpected non-directory evidence sibling: {path}")
        records.append(evidence_root_record(path))
    return records


def execution_limits(spec: JsonObject) -> JsonObject:
    """Normalize the accepted execution-template limit names for the supervisor."""
    value = spec.get("resource_limits", spec.get("limits"))
    if not isinstance(value, dict):
        raise ValueError("execution spec requires resource limits")
    normalized: JsonObject = {
        "max_seconds": value.get("max_seconds", value.get("max_wall_seconds")),
        "max_rss_bytes": value.get("max_rss_bytes"),
        "max_output_bytes": value.get("max_output_bytes"),
        "min_free_bytes": value.get("min_free_bytes", value.get("minimum_free_bytes")),
    }
    for name in (
        "max_swap_growth_bytes",
        "sample_seconds",
        "disk_sample_seconds",
        "termination_grace_seconds",
    ):
        if name in value:
            normalized[name] = value[name]
    required = ("max_seconds", "max_rss_bytes", "max_output_bytes", "min_free_bytes")
    if any(
        not isinstance(normalized.get(name), int | float) or normalized[name] <= 0
        for name in required
    ):
        raise ValueError("execution spec contains invalid finite resource limits")
    return normalized


def execution_total_cap(spec: JsonObject) -> int:
    """Use the sealed output cap, retaining the legacy-fixture default."""
    value = spec.get("resource_limits", spec.get("limits"))
    if value is None:
        return DEFAULT_TOTAL_BYTES
    return cast(int, execution_limits(spec)["max_output_bytes"])


def repository_root(spec: JsonObject) -> Path:
    """Resolve the accepted execution-template working-directory field."""
    value = spec.get("repository_working_directory", spec.get("repository_root"))
    if not isinstance(value, str):
        raise ValueError("execution spec requires repository_working_directory")
    return Path(value).resolve()


def tmux_is_live(name: str) -> bool:
    """Return whether one exact tmux session exists; never select by prefix."""
    return (
        subprocess.run(
            ["tmux", "has-session", "-t", f"={name}"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def _process_ancestors() -> set[int]:
    """Return this preflight's process ancestry so its own argv is not a false match."""
    ancestors: set[int] = set()
    current = os.getpid()
    while current > 1 and current not in ancestors:
        ancestors.add(current)
        result = subprocess.run(
            ["ps", "-o", "ppid=", "-p", str(current)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        raw = result.stdout.strip()
        if result.returncode != 0 or not raw.isdigit():
            break
        current = int(raw)
    return ancestors


def live_replay_processes(replay_root: Path, tmux_name: str) -> list[JsonObject]:
    """Find non-ancestral processes tied to this exact replay root or tmux name."""
    result = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,command="],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    excluded = _process_ancestors()
    needles = (str(replay_root.resolve()), tmux_name)
    matches: list[JsonObject] = []
    for line in result.stdout.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
            continue
        pid, ppid, command = int(fields[0]), int(fields[1]), fields[2]
        if pid in excluded or not any(needle in command for needle in needles):
            continue
        matches.append({"pid": pid, "ppid": ppid, "command": command})
    return matches


def _compact_input_state(
    generation_spec: Path, generation: JsonObject, replay_root: Path, initial_state: str
) -> tuple[str, list[JsonObject]]:
    """Verify the only two permitted compact prepared inputs without source access."""
    inputs = replay_root / "inputs"
    if not inputs.exists():
        return "absent", []
    if not inputs.is_dir() or inputs.is_symlink():
        raise ValueError("compact input namespace is not a real directory")
    allowed = {
        "task06g_source_family_catalog_v1.json",
        "task03h_preparation_readiness.json",
    }
    observed_names = {path.name for path in inputs.iterdir()}
    unexplained = sorted(observed_names - allowed)
    if unexplained:
        raise ValueError(f"unexplained compact input paths: {unexplained}")
    if any(not path.is_file() or path.is_symlink() for path in inputs.iterdir()):
        raise ValueError("compact input closure contains a non-file")
    catalog = inputs / "task06g_source_family_catalog_v1.json"
    readiness = inputs / "task03h_preparation_readiness.json"
    if readiness.exists() and not catalog.exists():
        raise ValueError("compact readiness exists without its staged catalog")
    if catalog.exists():
        recipe_root = generation_spec.resolve().parent
        repository_root = (recipe_root / str(generation["repository_root"])).resolve()
        expected_catalog = (
            repository_root / "configs/task06/v1/task06g_source_family_catalog_v1.json"
        )
        if catalog.read_bytes() != expected_catalog.read_bytes():
            raise ValueError("staged source-family catalog differs from frozen input")
    if readiness.exists():
        if initial_state != "published_exact":
            raise ValueError("compact readiness cannot precede an exact initial phase")
        value = load_object(readiness)
        initial = replay_root / "resolved_specs_v1/00_initial"
        identity = load_object(initial / "production_identity.json")
        required = {
            "status": "ready_for_user_authorized_clean_run",
            "production_extraction_id": identity.get("extraction_id"),
            "production_identity_sha256": sha256_file(initial / "production_identity.json"),
            "document_run_spec_sha256": sha256_file(initial / "task06g_document_v1.json"),
            "collection_run_spec_sha256": sha256_file(initial / "task06g_collection_v1.json"),
            "source_pdf_bytes_read": False,
            "model_files_read": False,
            "producer_identity_derivation_run": False,
            "execution_boundary": "source/model execution not run",
        }
        if any(value.get(key) != expected for key, expected in required.items()):
            raise ValueError("compact preparation readiness differs from exact initial controls")
        scope = value.get("source_scope")
        catalog_ref = value.get("catalog")
        if (
            not isinstance(scope, dict)
            or scope.get("source_count") != 35
            or scope.get("page_count") != 49_022
            or scope.get("ordered_source_ids") != generation.get("source_order")
            or not isinstance(catalog_ref, dict)
            or catalog_ref.get("sha256") != sha256_file(catalog)
            or catalog_ref.get("byte_size") != catalog.stat().st_size
        ):
            raise ValueError("compact preparation scope or catalog binding differs")
    refs = [reference(path, root=replay_root) for path in sorted(inputs.iterdir())]
    if readiness.exists():
        return "complete_exact", refs
    return "catalog_only_exact" if catalog.exists() else "empty_namespace", refs


def _collection_input_state(replay_root: Path) -> tuple[str, list[JsonObject]]:
    """Require v33 imported inputs to live only in its atomically resolved initial phase."""
    inputs = replay_root / "inputs"
    if not inputs.exists():
        return "not_applicable_imported_selection", []
    if not inputs.is_dir() or inputs.is_symlink() or any(inputs.iterdir()):
        raise ValueError("collection-only replay has an unexplained legacy inputs namespace")
    return "empty_namespace", []


def _prelaunch_replay_observation(
    generation_spec: Path, generation: JsonObject, replay_root: Path
) -> JsonObject:
    """Classify only the accepted pre-supervisor replay paths and reject all others."""
    if not replay_root.exists():
        return {
            "replay_state": "absent",
            "initial_phase_state": "absent",
            "initial_phase_manifest": None,
            "compact_input_state": "absent",
            "managed_paths": [],
            "resolver_staging": [],
        }
    if not replay_root.is_dir() or replay_root.is_symlink():
        raise ValueError("replay namespace is not a real directory")
    allowed_top = {"resolved_specs_v1", "inputs"}
    unexpected_top = sorted(
        path.name for path in replay_root.iterdir() if path.name not in allowed_top
    )
    if unexpected_top:
        raise ValueError(f"unexplained replay paths or candidate output: {unexpected_top}")
    candidate_markers = sorted(
        path.relative_to(replay_root).as_posix()
        for name in ("completion_record.json", "completion.json")
        for path in replay_root.rglob(name)
    )
    if candidate_markers:
        raise ValueError(
            f"prelaunch replay contains completed candidate markers: {candidate_markers}"
        )
    resolved = replay_root / "resolved_specs_v1"
    staging: list[JsonObject] = []
    initial_state = "absent"
    initial_manifest: JsonObject | None = None
    if resolved.exists():
        if not resolved.is_dir() or resolved.is_symlink():
            raise ValueError("resolved-spec namespace is not a real directory")
        for child in sorted(resolved.iterdir()):
            if child.name == "00_initial":
                continue
            if (
                child.name.startswith(".00_initial.staging-")
                and child.is_dir()
                and not child.is_symlink()
            ):
                staging.append(evidence_root_record(child))
                continue
            raise ValueError(f"unexplained resolved-spec path: {child}")
        initial = resolved / "00_initial"
        if initial.exists():
            if not initial.is_dir() or not (initial / "phase_manifest.json").is_file():
                raise ValueError("existing initial phase is partial, not atomically published")
            from er_commons.task06g.phases import verify_existing_phase

            verify_existing_phase(generation_spec, "initial", resolved)
            initial_state = "published_exact"
            initial_manifest = reference(initial / "phase_manifest.json", root=replay_root)
    if generation.get("schema_version") == "er_commons.task06g_collection_generation.v1":
        compact_state, compact_refs = _collection_input_state(replay_root)
    else:
        compact_state, compact_refs = _compact_input_state(
            generation_spec, generation, replay_root, initial_state
        )
    managed: list[JsonObject] = []
    if initial_state == "published_exact":
        managed.append(evidence_root_record(resolved / "00_initial"))
    managed.extend(compact_refs)
    return {
        "replay_state": "recoverable",
        "initial_phase_state": initial_state,
        "initial_phase_manifest": initial_manifest,
        "compact_input_state": compact_state,
        "managed_paths": managed,
        "resolver_staging": staging,
    }


def resource_ledger(
    replay_root: Path,
    sibling_roots: list[Path],
    *,
    total_cap: int = DEFAULT_TOTAL_BYTES,
    reserve: int = DEFAULT_RESERVE_BYTES,
) -> JsonObject:
    """Compute cumulative accounting without subtracting replay bytes twice."""
    replay_bytes = _tree_bytes(replay_root)
    sibling_bytes = sum(_tree_bytes(path) for path in sibling_roots)
    supervisor_max = total_cap - sibling_bytes - reserve
    additional = total_cap - replay_bytes - sibling_bytes - reserve
    if supervisor_max <= 0 or additional <= 0:
        raise ValueError("Task 06G cumulative output allowance is exhausted")
    return {
        "total_cap_bytes": total_cap,
        "replay_bytes": replay_bytes,
        "preserved_sibling_bytes": sibling_bytes,
        "prospective_external_reserve_bytes": reserve,
        "supervisor_max_output_bytes": supervisor_max,
        "maximum_additional_bytes": additional,
    }


def _verified_references(values: Sequence[JsonObject], *, label: str) -> list[JsonObject]:
    """Normalize a nonempty, unique set of source-free evidence references."""
    if not values:
        raise ValueError(f"collection-only prediction requires {label}")
    normalized: list[JsonObject] = []
    paths: set[Path] = set()
    for value in values:
        path = verify_reference(value)
        if path in paths:
            raise ValueError(f"collection-only prediction repeats {label}: {path}")
        paths.add(path)
        normalized.append(reference(path))
    return normalized


def _current_sibling_roots(replay_root: Path) -> set[Path]:
    """Discover the exact direct-directory evidence closure beside one replay."""
    parent = replay_root.resolve().parent
    observed: set[Path] = set()
    for path in parent.iterdir() if parent.exists() else []:
        if path.resolve() == replay_root.resolve():
            continue
        if path.is_symlink() or not path.is_dir():
            raise ValueError(f"unexpected collection-only evidence sibling: {path}")
        observed.add(path.resolve())
    return observed


def collection_only_resource_prediction(
    replay_root: Path,
    preserved_evidence_roots: Sequence[JsonObject],
    precedent_references: Sequence[JsonObject],
    pinned_completion_references: Sequence[JsonObject],
    *,
    total_cap: int = DEFAULT_TOTAL_BYTES,
    reserve: int = DEFAULT_RESERVE_BYTES,
) -> JsonObject:
    """Build the sealed resource envelope for the approved collection-only replay."""
    if len(pinned_completion_references) != 35:
        raise ValueError("collection-only prediction requires exactly 35 pinned completions")
    preserved_paths: list[Path] = []
    preserved_bindings: list[JsonObject] = []
    for value in preserved_evidence_roots:
        path = verify_evidence_root_record(value)
        preserved_paths.append(path)
        preserved_bindings.append(
            {
                "path": str(path),
                "file_count": value["file_count"],
                "byte_count": value["byte_count"],
                "record_sha256": sha256_bytes(canonical_bytes(value)),
            }
        )
    if len(set(preserved_paths)) != len(preserved_paths):
        raise ValueError("collection-only prediction repeats a preserved evidence root")
    if _current_sibling_roots(replay_root) != set(preserved_paths):
        raise ValueError("collection-only prediction has stale sibling evidence closure")

    precedents = _verified_references(precedent_references, label="precedent references")
    completions = _verified_references(
        pinned_completion_references, label="pinned completion references"
    )
    ledger = resource_ledger(
        replay_root,
        preserved_paths,
        total_cap=total_cap,
        reserve=reserve,
    )
    predicted = COLLECTION_ONLY_PREDICTED_MAX_BYTES
    available = cast(int, ledger["maximum_additional_bytes"])
    if predicted > available:
        raise ValueError("collection-only predicted output exceeds the remaining allowance")
    basis: JsonObject = {
        "preserved_evidence_roots": sorted(
            preserved_bindings, key=lambda item: cast(str, item["path"])
        ),
        "precedent_references": precedents,
        "pinned_completion_references": completions,
    }
    return {
        "schema_version": "er_commons.task06g.collection_only_resource_prediction.v1",
        "status": "fits",
        "mode": "collection_only_pinned_v32",
        "component_maxima": dict(COLLECTION_ONLY_COMPONENT_MAXIMA),
        "predicted_maximum_additional_bytes": predicted,
        "resource_ledger": ledger,
        "predicted_headroom_bytes": available - predicted,
        "basis": basis,
        "basis_sha256": sha256_bytes(canonical_bytes(basis)),
        "source_payloads_read": False,
        "models_loaded": False,
    }


def verify_collection_only_resource_prediction(
    prediction: JsonObject,
    replay_root: Path,
    preserved_evidence_roots: Sequence[JsonObject],
    precedent_references: Sequence[JsonObject],
    pinned_completion_references: Sequence[JsonObject],
    *,
    total_cap: int = DEFAULT_TOTAL_BYTES,
    reserve: int = DEFAULT_RESERVE_BYTES,
) -> JsonObject:
    """Recompute the collection-only envelope and reject stale evidence or allowance."""
    observed = collection_only_resource_prediction(
        replay_root,
        preserved_evidence_roots,
        precedent_references,
        pinned_completion_references,
        total_cap=total_cap,
        reserve=reserve,
    )
    if observed != prediction:
        raise ValueError("collection-only resource prediction is stale")
    return observed


def preflight_prelaunch(
    generation_spec: Path, replay_root: Path, attempt_root: Path, output_root: Path
) -> Path:
    """Seal source-free recovery observations before any supervisor attempt exists."""
    replay_root = replay_root.resolve()
    attempt_root = attempt_root.resolve()
    output_root = output_root.resolve()
    if attempt_root.parent != replay_root.parent or output_root.parent != replay_root.parent:
        raise ValueError("prelaunch replay, attempt, and receipt roots must be siblings")
    _attempt_number(attempt_root)
    if output_root.exists():
        raise FileExistsError(f"prelaunch receipt root already exists: {output_root}")
    generation = load_object(generation_spec)
    if generation.get("schema_version") == "er_commons.task06g_generation.v1":
        from er_commons.document_publication.config_generation.task06g_generation import (
            check_task06g_generation,
        )

        check_task06g_generation(generation_spec)
    elif generation.get("schema_version") == "er_commons.task06g_collection_generation.v1":
        from er_commons.task06g.collection_generation import check_collection_generation

        check_collection_generation(generation_spec)
        namespaces = generation.get("namespaces")
        if not isinstance(namespaces, dict):
            raise ValueError("collection-only generation lacks frozen namespaces")
        from er_commons.task06g.phases import _roots

        _, _, artifact_root = _roots(generation_spec, generation)
        expected_replay = artifact_root / cast(str, namespaces.get("replay_root"))
        expected_attempt = artifact_root / cast(str, namespaces.get("attempt_root"))
        expected_recovery = artifact_root / cast(str, namespaces.get("recovery_root"))
        if (
            replay_root != expected_replay.resolve()
            or attempt_root != expected_attempt.resolve()
            or output_root != expected_recovery.resolve()
        ):
            raise ValueError("collection-only prelaunch paths differ from frozen namespaces")
    tmux_name = generation.get("tmux_session", "er-commons-06g-replay-v1")
    if not isinstance(tmux_name, str):
        raise ValueError("tmux_session must be a string")
    matching_processes = live_replay_processes(replay_root, tmux_name)
    if attempt_root.exists() or tmux_is_live(tmux_name) or matching_processes:
        raise ValueError(
            "prelaunch recovery requires absent attempt root and every replay process/tmux"
        )
    observation = _prelaunch_replay_observation(generation_spec, generation, replay_root)
    preserved_roots = enumerate_sibling_evidence(
        replay_root.parent,
        excluded=[replay_root, attempt_root, output_root, generation_spec],
    )
    record: JsonObject = {
        "schema_version": "er_commons.task06g.prelaunch_recovery.v1",
        "status": "accepted",
        "generation_spec": reference(generation_spec),
        "replay_root": str(replay_root.resolve()),
        "attempt_root": str(attempt_root.resolve()),
        "tmux_session": tmux_name,
        "supervisor_started": False,
        "process_inspection": {
            "matching_processes": matching_processes,
            "tmux_session_live": False,
        },
        **observation,
        "preserved_external_bytes": _tree_bytes(replay_root.parent) - _tree_bytes(replay_root),
        "preserved_evidence_roots": preserved_roots,
    }
    if generation.get("schema_version") == "er_commons.task06g_collection_generation.v1":
        ledger = resource_ledger(replay_root, [Path(str(item["path"])) for item in preserved_roots])
        if cast(int, ledger["maximum_additional_bytes"]) < COLLECTION_ONLY_PREDICTED_MAX_BYTES:
            raise ValueError("collection-only prelaunch resource envelope no longer fits")
        record["resource_ledger"] = ledger
        record["collection_only_resource_envelope"] = {
            "mode": "collection_only_pinned_v32",
            "component_maxima": dict(COLLECTION_ONLY_COMPONENT_MAXIMA),
            "predicted_maximum_additional_bytes": COLLECTION_ONLY_PREDICTED_MAX_BYTES,
            "predicted_headroom_bytes": cast(int, ledger["maximum_additional_bytes"])
            - COLLECTION_ONLY_PREDICTED_MAX_BYTES,
            "source_payloads_read": False,
            "models_loaded": False,
        }
    publish_directory_no_clobber(output_root, {"recovery_receipt.json": canonical_bytes(record)})
    return output_root / "recovery_receipt.json"


def _attempt_number(path: Path) -> int:
    prefix = "execution_attempt_v"
    if not path.name.startswith(prefix) or not path.name[len(prefix) :].isdigit():
        raise ValueError(f"invalid execution attempt root name: {path.name}")
    number = int(path.name[len(prefix) :])
    if number < 1:
        raise ValueError("execution attempt ordinal must be positive")
    return number


def _verify_prior_attempt(attempt_root: Path, replay_root: Path) -> JsonObject:
    """Verify and seal the supervisor-owned prior-attempt file closure."""
    allowed = {"status.json", "command.log", "execution.json"}
    observed = {path.name for path in attempt_root.iterdir()}
    if not observed.issubset(allowed):
        raise ValueError("prior execution attempt has unexplained managed files")
    if any(not path.is_file() or path.is_symlink() for path in attempt_root.iterdir()):
        raise ValueError("prior execution attempt contains a non-file or symlink")
    if "status.json" not in observed:
        if observed:
            raise ValueError("prior execution attempt has evidence without supervisor status")
        return {
            "state": "interrupted_before_status",
            "evidence": evidence_root_record(attempt_root),
        }
    status = load_object(attempt_root / "status.json")
    if (
        status.get("schema_version") != "background_execution_v1"
        or status.get("output_root") != str(replay_root.resolve())
        or status.get("attempt_root") != str(attempt_root.resolve())
        or status.get("status") not in {"starting", "running", "failed", "succeeded"}
    ):
        raise ValueError("prior execution status differs from its supervised attempt")
    execution_path = attempt_root / "execution.json"
    if execution_path.exists():
        if "command.log" not in observed:
            raise ValueError("prior terminal execution lacks its durable command log")
        execution = load_object(execution_path)
        if execution != status or "finished_at" not in execution:
            raise ValueError("prior terminal execution and final status differ")
        state = (
            "terminal_succeeded" if execution.get("status") == "succeeded" else "terminal_failed"
        )
    else:
        if status.get("status") == "succeeded":
            raise ValueError("prior successful status lacks terminal execution evidence")
        state = "interrupted"
    return {"state": state, "evidence": evidence_root_record(attempt_root)}


def _verify_managed_publication(root: Path) -> JsonObject:
    """Verify one completion-last publication's exact inventory and bytes."""
    records = root / "records"
    inventory_path = records / "artifact_inventory.json"
    completion_path = records / "completion_record.json"
    if not inventory_path.is_file() or not completion_path.is_file():
        raise ValueError(f"partial publication occupies final namespace: {root}")
    inventory = load_object(inventory_path)
    completion = load_object(completion_path)
    files = inventory.get("files")
    if not isinstance(files, list) or any(not isinstance(item, dict) for item in files):
        raise ValueError(f"malformed publication inventory: {inventory_path}")
    managed: set[str] = set()
    for raw in files:
        item = cast(JsonObject, raw)
        path = verify_reference(item, root=root)
        relative = path.relative_to(root.resolve()).as_posix()
        if relative in managed or relative in {
            "records/artifact_inventory.json",
            "records/completion_record.json",
        }:
            raise ValueError(f"publication inventory repeats a managed path: {root}")
        managed.add(relative)
    observed = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    allowed_unmanaged = {
        "records/artifact_inventory.json",
        "records/completion_record.json",
        "records/identity_preimage.json",
    }
    if observed - managed - allowed_unmanaged or managed - observed:
        raise ValueError(f"publication managed-file closure differs: {root}")
    inventory_ref = reference(inventory_path, root=root)
    declared = completion.get("artifact_inventory")
    if isinstance(declared, dict):
        if declared.get("sha256") != inventory_ref["sha256"]:
            raise ValueError(f"publication completion inventory binding differs: {root}")
    elif completion.get("artifact_inventory_sha256") != inventory_ref["sha256"]:
        raise ValueError(f"publication completion inventory digest differs: {root}")
    return reference(completion_path, root=root)


def _verify_process_config_closure(
    resolved: Path, artifact_root: Path, repository_root: Path
) -> JsonObject:
    """Verify Task 06G per-stage config phases and their semantic checkpoints."""
    from er_commons.task06g.staged_process_configs import STAGE_ORDER

    phases_root = resolved / "document_stages"
    checkpoints_root = resolved / "document_stage_checkpoints_v1"
    phase_keys: set[tuple[str, str]] = set()
    checkpoint_keys: set[tuple[str, str]] = set()
    if phases_root.exists():
        for source_root in phases_root.iterdir():
            if source_root.name.startswith("."):
                continue
            if not source_root.is_dir() or source_root.is_symlink():
                raise ValueError("process-config source namespace is not a real directory")
            for phase_root in source_root.iterdir():
                if phase_root.name.startswith("."):
                    continue
                if (
                    not phase_root.is_dir()
                    or phase_root.is_symlink()
                    or not (phase_root / "phase_manifest.json").is_file()
                ):
                    raise ValueError(f"partial process-config final namespace: {phase_root}")
        for manifest_path in sorted(phases_root.rglob("phase_manifest.json")):
            phase_root = manifest_path.parent
            manifest = load_object(manifest_path)
            source_id, stage = manifest.get("source_id"), manifest.get("stage")
            managed = manifest.get("managed_files")
            external = manifest.get("external_checkpoints")
            if (
                manifest.get("schema_version") != "er_commons.task06g.process_config_phase.v1"
                or manifest.get("completion_last") is not True
                or not isinstance(source_id, str)
                or not isinstance(stage, str)
                or not isinstance(managed, list)
                or not isinstance(external, list)
            ):
                raise ValueError(f"malformed process-config phase: {phase_root}")
            generation_ref = manifest.get("generation_spec")
            if not isinstance(generation_ref, dict):
                raise ValueError(f"process-config phase lacks generation binding: {phase_root}")
            verify_reference(generation_ref, root=repository_root)
            ordinal = STAGE_ORDER.index(stage) + 1 if stage in STAGE_ORDER else 0
            if phase_root.relative_to(phases_root) != Path(source_id, f"{ordinal:02d}_{stage}"):
                raise ValueError(
                    f"process-config phase path differs from its identity: {phase_root}"
                )
            for item in managed:
                if not isinstance(item, dict):
                    raise ValueError(f"malformed process-config managed reference: {phase_root}")
                verify_reference(item, root=phase_root)
            for item in external:
                if not isinstance(item, dict):
                    raise ValueError(f"malformed process-config checkpoint reference: {phase_root}")
                verify_reference(item, root=artifact_root)
            expected = {str(cast(JsonObject, item)["path"]) for item in managed} | {
                "phase_manifest.json"
            }
            observed = {
                path.relative_to(phase_root).as_posix()
                for path in phase_root.rglob("*")
                if path.is_file() or path.is_symlink()
            }
            if observed != expected:
                raise ValueError(f"process-config phase managed closure differs: {phase_root}")
            config_path = phase_root / f"{stage}.json"
            receipt = load_object(phase_root / f"{stage}.receipt.json")
            validation = receipt.get("validation")
            if (
                receipt.get("schema_version") != "er_commons.task06g.process_config_receipt.v1"
                or receipt.get("source_id") != source_id
                or receipt.get("stage") != stage
                or not isinstance(validation, dict)
                or validation.get("passed") is not True
                or not isinstance(validation.get("loader"), str)
                or receipt.get("resolved") != reference(config_path, root=phase_root)
            ):
                raise ValueError(f"process-config receipt differs: {phase_root}")
            for key in ("template", "generator"):
                item = receipt.get(key)
                if not isinstance(item, dict):
                    raise ValueError(f"process-config receipt lacks {key}: {phase_root}")
                verify_reference(item, root=repository_root)
            phase_keys.add((source_id, stage))
        unexplained_phase_files = [
            path
            for path in phases_root.rglob("*")
            if (path.is_file() or path.is_symlink())
            and not any(part.startswith(".") for part in path.relative_to(phases_root).parts)
            and not any(
                path.is_relative_to(manifest.parent)
                for manifest in phases_root.rglob("phase_manifest.json")
            )
        ]
        if unexplained_phase_files:
            raise ValueError("process-config namespace contains unexplained partial files")
    if checkpoints_root.exists():
        if any(
            path.is_symlink() or (path.is_file() and path.suffix != ".json")
            for path in checkpoints_root.rglob("*")
        ):
            raise ValueError("process checkpoint namespace contains unexplained files")
        for path in sorted(checkpoints_root.rglob("*.json")):
            checkpoint = load_object(path)
            source_id, stage = checkpoint.get("source_id"), checkpoint.get("stage")
            if (
                checkpoint.get("schema_version")
                != "er_commons.task06g.process_identity_checkpoint.v1"
                or checkpoint.get("verified") is not True
                or checkpoint.get("derived_id") != checkpoint.get("recomputed_id")
                or not isinstance(source_id, str)
                or not isinstance(stage, str)
            ):
                raise ValueError(f"invalid process identity checkpoint: {path}")
            for key in ("stage_completion", "stage_inventory", "resolved_config_ref"):
                item = checkpoint.get(key)
                if not isinstance(item, dict):
                    raise ValueError(f"process checkpoint lacks {key}: {path}")
                verify_reference(item, root=artifact_root)
            checkpoint_keys.add((source_id, stage))
    if not checkpoint_keys.issubset(phase_keys):
        raise ValueError("process checkpoints exist without their resolved config phases")
    for source_id in {source for source, _ in phase_keys | checkpoint_keys}:
        phase_stages = [stage for stage in STAGE_ORDER if (source_id, stage) in phase_keys]
        checkpoint_stages = [
            stage for stage in STAGE_ORDER if (source_id, stage) in checkpoint_keys
        ]
        if phase_stages != list(STAGE_ORDER[: len(phase_stages)]) or checkpoint_stages != list(
            STAGE_ORDER[: len(checkpoint_stages)]
        ):
            raise ValueError(f"process stages are not a semantic prefix: {source_id}")
        if len(phase_stages) - len(checkpoint_stages) not in {0, 1}:
            raise ValueError(f"process config/checkpoint chain has a gap: {source_id}")
    return {
        "resolved_phase_count": len(phase_keys),
        "checkpoint_count": len(checkpoint_keys),
        "phase_keys": [list(item) for item in sorted(phase_keys)],
        "checkpoint_keys": [list(item) for item in sorted(checkpoint_keys)],
    }


def _verify_replay_closure(
    execution_spec: Path, spec: JsonObject, replay_root: Path, prior_attempt_number: int
) -> JsonObject:
    """Classify the exact source-free replay state and verify its semantic checkpoint chain."""
    allowed_top = {
        "inputs",
        "resolved_specs_v1",
        "document_progress",
        "collection_progress",
        "document_parse_evidence",
        "document_records",
        "document_publications",
        "document_links",
        "identity_checkpoints_v1",
        "correspondence_v1",
        "comparison_v1",
    }
    unexplained = sorted(
        path.name for path in replay_root.iterdir() if path.name not in allowed_top
    )
    if unexplained:
        raise ValueError(f"unexplained replay paths: {unexplained}")
    collection_only = (
        spec.get("schema_version") == "er_commons.task06g.collection_execution_template.v1"
    )
    progress = replay_root / ("collection_progress" if collection_only else "document_progress")
    progress_attempts: list[JsonObject] = []
    if progress.exists():
        if not progress.is_dir() or progress.is_symlink():
            raise ValueError("document progress namespace is not a real directory")
        allowed_progress = {f"attempt_v{number}" for number in range(1, prior_attempt_number + 1)}
        observed_progress = {path.name for path in progress.iterdir()}
        if not observed_progress.issubset(allowed_progress):
            raise ValueError("document progress contains an unexplained or future attempt")
        for path in sorted(progress.iterdir()):
            progress_attempts.append(evidence_root_record(path))
    generation_value = spec.get("generation_spec")
    if not isinstance(generation_value, str):
        raise ValueError("Task 06G resume requires the frozen generation spec")
    generation_spec = Path(generation_value).resolve()
    generation = load_object(generation_spec)
    raw_data_root = generation.get("data_root", ".")
    if raw_data_root == "${ER_COMMONS_DATA_ROOT}":
        from er_commons.settings import load_settings

        artifact_root = load_settings().data_root.resolve()
    else:
        artifact_root = (generation_spec.parent / str(raw_data_root)).resolve()
    repository_root = (
        generation_spec.parent / str(generation.get("repository_root", "."))
    ).resolve()
    execution_name = (
        "task06g_collection_execution_v1.json" if collection_only else "task06g_execution_v1.json"
    )
    expected_execution = (replay_root / "resolved_specs_v1/00_initial" / execution_name).resolve()
    if execution_spec.resolve() != expected_execution:
        raise ValueError("resume execution spec is outside the exact initial resolved phase")

    from er_commons.task06g.phases import (
        publish_aggregate,
        publish_checkpoint_inventory,
        publish_stage_checkpoint,
        verify_existing_phase,
    )

    closure = spec.get("resolver_closure")
    if not isinstance(closure, dict):
        raise ValueError("resume execution spec lacks resolver closure")
    phase_names = closure.get("phase_directories")
    checkpoint_names = closure.get("checkpoint_files")
    process_checkpoint_names = closure.get("process_checkpoint_files")
    if (
        not isinstance(phase_names, list)
        or any(not isinstance(item, str) for item in phase_names)
        or not isinstance(checkpoint_names, list)
        or any(not isinstance(item, str) for item in checkpoint_names)
        or not isinstance(process_checkpoint_names, list)
        or any(not isinstance(item, str) for item in process_checkpoint_names)
    ):
        raise ValueError("resume resolver closure enumerations are malformed")
    resolved = replay_root / "resolved_specs_v1"
    present_phases: list[str] = []
    if resolved.is_dir():
        allowed_resolved = set(cast(list[str], phase_names)) | {
            "aggregate_v1",
            "document_stages",
            "document_stage_checkpoints_v1",
        }
        for child in sorted(resolved.iterdir()):
            if child.name.startswith(".") and ".staging-" in child.name:
                continue
            if child.name not in allowed_resolved:
                raise ValueError(f"unexplained resolved-spec path: {child}")
        for phase in cast(list[str], phase_names):
            if (resolved / phase).exists():
                if not phase.startswith("document_stages/"):
                    verify_existing_phase(generation_spec, phase.split("_", 1)[1], resolved)
                present_phases.append(phase)
        if present_phases != cast(list[str], phase_names)[: len(present_phases)]:
            raise ValueError("resolved-spec phases are not a consecutive semantic prefix")
    checkpoint_root = replay_root / "identity_checkpoints_v1"
    present_checkpoints: list[str] = []
    if checkpoint_root.exists():
        if not checkpoint_root.is_dir() or checkpoint_root.is_symlink():
            raise ValueError("identity checkpoint namespace is not a real directory")
        observed_checkpoints = sorted(
            path.relative_to(checkpoint_root).as_posix()
            for path in checkpoint_root.rglob("*.json")
            if path.name != "inventory.json"
        )
        expected_prefix = cast(list[str], checkpoint_names)[: len(observed_checkpoints)]
        if observed_checkpoints != sorted(expected_prefix):
            raise ValueError("identity checkpoints are not the frozen semantic prefix")
        for name in expected_prefix:
            path = checkpoint_root / name
            checkpoint = load_object(path)
            completion_ref = checkpoint.get("stage_completion")
            if not isinstance(completion_ref, dict):
                raise ValueError(f"identity checkpoint lacks stage completion: {path}")
            completion = verify_reference(completion_ref, root=artifact_root)
            publish_stage_checkpoint(
                generation_spec,
                str(checkpoint.get("stage_key")),
                completion,
                path,
                resume_existing=True,
            )
            present_checkpoints.append(name)
        inventory = checkpoint_root / "inventory.json"
        if inventory.exists():
            if len(present_checkpoints) != len(checkpoint_names):
                raise ValueError("checkpoint inventory exists before the full semantic chain")
            publish_checkpoint_inventory(
                checkpoint_root, cast(list[str], checkpoint_names), resume_existing=True
            )
    process_configs = (
        {
            "resolved_phase_count": 0,
            "checkpoint_count": 0,
            "phase_keys": [],
            "checkpoint_keys": [],
        }
        if collection_only
        else _verify_process_config_closure(resolved, artifact_root, repository_root)
    )
    aggregate = resolved / "aggregate_v1"
    if aggregate.exists():
        expected_process_keys = [
            [parts[1], Path(parts[2]).stem.split("_", 1)[1]]
            for name in cast(list[str], process_checkpoint_names)
            if len(parts := Path(name).parts) == 3
        ]
        if (
            len(present_phases) != len(phase_names)
            or len(present_checkpoints) != len(checkpoint_names)
            or process_configs.get("phase_keys") != sorted(expected_process_keys)
            or (process_configs.get("checkpoint_keys") != sorted(expected_process_keys))
        ):
            raise ValueError("resolved aggregate exists before its full dependency chain")
        publish_aggregate(
            resolved,
            cast(list[str], phase_names),
            resolved
            / cast(
                str,
                closure.get(
                    "pre_execution_identity_checkpoint",
                    "00_initial/pre_execution_production_identity_checkpoint.json",
                ),
            ),
            process_checkpoint_names=cast(list[str], process_checkpoint_names),
            pre_execution_manifest_field=cast(
                str,
                closure.get(
                    "pre_execution_manifest_field",
                    "pre_execution_production_identity_checkpoint",
                ),
            ),
            resume_existing=True,
        )
    publications: list[JsonObject] = []
    for records in sorted(replay_root.rglob("records")):
        if any(
            part.startswith(".") or part in {"attempts", "document_progress", "collection_progress"}
            for part in records.parts
        ):
            continue
        if (records / "artifact_inventory.json").exists() or (
            records / "completion_record.json"
        ).exists():
            publications.append(_verify_managed_publication(records.parent))
        else:
            raise ValueError(
                f"partial publication records occupy a final namespace: {records.parent}"
            )
    return {
        "state": "verified",
        "resolved_phases": present_phases,
        "identity_checkpoints": present_checkpoints,
        "terminal_publications": publications,
        "process_configs": process_configs,
        "progress_attempts": progress_attempts,
        "evidence": evidence_root_record(replay_root),
    }


def preflight_resume(
    execution_spec: Path,
    replay_root: Path,
    prior_attempt_root: Path,
    next_attempt_root: Path,
    output_root: Path,
) -> Path:
    """Validate an explicit prior attempt and seal a fresh-attempt resume receipt."""
    if output_root.exists() or next_attempt_root.exists():
        raise FileExistsError("resume output or next attempt root already exists")
    spec = load_object(execution_spec)
    session = spec.get("tmux_session")
    if not isinstance(session, str):
        raise ValueError("execution spec lacks an exact tmux session")
    prior_number, next_number = (
        _attempt_number(prior_attempt_root),
        _attempt_number(next_attempt_root),
    )
    if next_number != prior_number + 1:
        raise ValueError("resume attempt ordinals must be consecutive")
    attempt_parent = replay_root.parent.resolve()
    expected_output = attempt_parent / f"resume_preflight_v{next_number}"
    collection_only = (
        spec.get("schema_version") == "er_commons.task06g.collection_execution_template.v1"
    )
    next_progress = (
        replay_root
        / ("collection_progress" if collection_only else "document_progress")
        / f"attempt_v{next_number}"
    )
    if (
        prior_attempt_root.parent.resolve() != attempt_parent
        or next_attempt_root.parent.resolve() != attempt_parent
        or output_root.resolve() != expected_output.resolve()
    ):
        raise ValueError("resume attempt and receipt paths must match the exact next ordinal")
    if next_progress.exists():
        raise FileExistsError("next progress root already exists")
    initial_number = cast(int, spec.get("initial_attempt_number", 1))
    if prior_number < initial_number:
        raise ValueError("resume prior attempt predates this execution contract")
    prior_session = (
        session if prior_number == initial_number else f"{session}-attempt-v{prior_number}"
    )
    next_session = f"{session}-attempt-v{next_number}"
    tied_sessions = [
        session,
        *(f"{session}-attempt-v{number}" for number in range(initial_number + 1, next_number + 1)),
    ]
    matching_processes = live_replay_processes(replay_root, prior_session)
    live_sessions = [name for name in tied_sessions if tmux_is_live(name)]
    if live_sessions or matching_processes:
        raise ValueError("prior or next replay process/tmux session is live")
    if (
        not replay_root.is_dir()
        or replay_root.is_symlink()
        or not prior_attempt_root.is_dir()
        or prior_attempt_root.is_symlink()
    ):
        raise ValueError("resume requires explicit replay and prior-attempt roots")
    strict_task06g = spec.get("schema_version") in {
        "er_commons.task06g.execution_template.v1",
        "er_commons.task06g.collection_execution_template.v1",
    }
    if strict_task06g:
        prior_observation = _verify_prior_attempt(prior_attempt_root, replay_root)
        replay_observation = _verify_replay_closure(execution_spec, spec, replay_root, prior_number)
    else:
        terminal = prior_attempt_root / "execution.json"
        prior_observation = {
            "state": "legacy_fixture",
            "evidence": evidence_root_record(prior_attempt_root),
        }
        replay_observation = {
            "state": "legacy_fixture",
            "evidence": evidence_root_record(replay_root),
        }
    terminal = prior_attempt_root / "execution.json"
    prior_ref = reference(terminal, root=prior_attempt_root) if terminal.is_file() else None
    raw_siblings = spec.get("ledger_sibling_roots", [])
    if not isinstance(raw_siblings, list) or any(
        not isinstance(item, str) for item in raw_siblings
    ):
        raise ValueError("ledger_sibling_roots must be explicit paths")
    preserved_roots = enumerate_sibling_evidence(
        replay_root.parent,
        excluded=[replay_root, next_attempt_root, output_root, execution_spec],
    )
    preserved_paths = {Path(str(item["path"])).resolve() for item in preserved_roots}
    if not {Path(cast(str, item)).resolve() for item in raw_siblings}.issubset(preserved_paths):
        raise ValueError("resume ledger omits an execution-spec evidence root")
    ledger = resource_ledger(
        replay_root,
        [Path(str(item["path"])) for item in preserved_roots],
        total_cap=execution_total_cap(spec),
    )
    collection_envelope: JsonObject | None = None
    if collection_only:
        if cast(int, ledger["maximum_additional_bytes"]) < COLLECTION_ONLY_PREDICTED_MAX_BYTES:
            raise ValueError("collection-only resume resource envelope no longer fits")
        collection_envelope = {
            "mode": "collection_only_pinned_v32",
            "component_maxima": dict(COLLECTION_ONLY_COMPONENT_MAXIMA),
            "predicted_maximum_additional_bytes": COLLECTION_ONLY_PREDICTED_MAX_BYTES,
            "predicted_headroom_bytes": cast(int, ledger["maximum_additional_bytes"])
            - COLLECTION_ONLY_PREDICTED_MAX_BYTES,
            "source_payloads_read": False,
            "models_loaded": False,
        }
    record: JsonObject = {
        "schema_version": "er_commons.task06g.resume_receipt.v1",
        "status": "accepted",
        "execution_spec": reference(execution_spec),
        "replay_root": str(replay_root.resolve()),
        "prior_attempt_root": str(prior_attempt_root.resolve()),
        "prior_execution": prior_ref,
        "next_attempt_root": str(next_attempt_root.resolve()),
        "progress_root": str(next_progress.resolve()),
        "tmux_session": next_session,
        "process_inspection": {
            "matching_processes": matching_processes,
            "checked_tmux_sessions": tied_sessions,
            "live_tmux_sessions": live_sessions,
        },
        "prior_attempt_observation": prior_observation,
        "replay_observation": replay_observation,
        "resource_ledger": ledger,
        "preserved_evidence_roots": preserved_roots,
    }
    if collection_envelope is not None:
        record["collection_only_resource_envelope"] = collection_envelope
    publish_directory_no_clobber(output_root, {"resume_receipt.json": canonical_bytes(record)})
    return output_root / "resume_receipt.json"


def verify_resume_receipt_current(receipt_path: Path) -> tuple[JsonObject, Path, JsonObject]:
    """Recompute every mutable resume precondition immediately before dispatch."""
    receipt = load_object(receipt_path)
    if (
        receipt.get("schema_version") != "er_commons.task06g.resume_receipt.v1"
        or receipt.get("status") != "accepted"
    ):
        raise ValueError("resume receipt is not accepted")
    execution_ref = receipt.get("execution_spec")
    if not isinstance(execution_ref, dict):
        raise ValueError("resume receipt lacks execution spec reference")
    execution_spec = verify_reference(execution_ref)
    spec = load_object(execution_spec)
    raw_paths = [
        receipt.get("replay_root"),
        receipt.get("prior_attempt_root"),
        receipt.get("next_attempt_root"),
        receipt.get("progress_root"),
    ]
    if any(not isinstance(item, str) for item in raw_paths):
        raise ValueError("resume receipt path bindings are malformed")
    replay_root, prior_attempt_root, next_attempt_root, progress_root = (
        Path(cast(str, item)).resolve() for item in raw_paths
    )
    prior_number = _attempt_number(prior_attempt_root)
    next_number = _attempt_number(next_attempt_root)
    session = spec.get("tmux_session")
    if not isinstance(session, str) or next_number != prior_number + 1:
        raise ValueError("resume receipt attempt ordinal or tmux binding differs")
    expected_receipt_root = replay_root.parent / f"resume_preflight_v{next_number}"
    collection_only = (
        spec.get("schema_version") == "er_commons.task06g.collection_execution_template.v1"
    )
    expected_progress = (
        replay_root
        / ("collection_progress" if collection_only else "document_progress")
        / f"attempt_v{next_number}"
    )
    expected_session = f"{session}-attempt-v{next_number}"
    if (
        receipt_path.parent.resolve() != expected_receipt_root.resolve()
        or prior_attempt_root.parent != replay_root.parent
        or next_attempt_root.parent != replay_root.parent
        or progress_root != expected_progress.resolve()
        or receipt.get("tmux_session") != expected_session
    ):
        raise ValueError("resume receipt attempt paths or session differ from its exact ordinal")
    if next_attempt_root.exists() or progress_root.exists():
        raise ValueError("resume launch requires fresh attempt and progress namespaces")

    initial_number = cast(int, spec.get("initial_attempt_number", 1))
    if prior_number < initial_number:
        raise ValueError("resume prior attempt predates this execution contract")
    tied_sessions = [
        session,
        *(f"{session}-attempt-v{number}" for number in range(initial_number + 1, next_number + 1)),
    ]
    prior_session = (
        session if prior_number == initial_number else f"{session}-attempt-v{prior_number}"
    )
    matching_processes = live_replay_processes(replay_root, prior_session)
    live_sessions = [name for name in tied_sessions if tmux_is_live(name)]
    if matching_processes or live_sessions:
        raise ValueError("prior or next replay process/tmux session is live")

    if spec.get("schema_version") in {
        "er_commons.task06g.execution_template.v1",
        "er_commons.task06g.collection_execution_template.v1",
    }:
        prior_observation = _verify_prior_attempt(prior_attempt_root, replay_root)
        replay_observation = _verify_replay_closure(execution_spec, spec, replay_root, prior_number)
    else:
        prior_observation = {
            "state": "legacy_fixture",
            "evidence": evidence_root_record(prior_attempt_root),
        }
        replay_observation = {
            "state": "legacy_fixture",
            "evidence": evidence_root_record(replay_root),
        }
    if prior_observation != receipt.get(
        "prior_attempt_observation"
    ) or replay_observation != receipt.get("replay_observation"):
        raise ValueError("resume receipt observations are stale")

    raw_preserved = receipt.get("preserved_evidence_roots")
    if not isinstance(raw_preserved, list) or any(
        not isinstance(item, dict) for item in raw_preserved
    ):
        raise ValueError("resume receipt preserved evidence roots are malformed")
    for item in raw_preserved:
        verify_evidence_root_record(cast(JsonObject, item))
    observed_preserved = enumerate_sibling_evidence(
        replay_root.parent,
        excluded=[replay_root, next_attempt_root, receipt_path.parent, execution_spec],
    )
    if observed_preserved != raw_preserved:
        raise ValueError("resume receipt sibling evidence closure is stale")
    observed_ledger = resource_ledger(
        replay_root,
        [Path(str(item["path"])) for item in observed_preserved],
        total_cap=execution_total_cap(spec),
    )
    if observed_ledger != receipt.get("resource_ledger"):
        raise ValueError("resume receipt resource ledger is stale")
    if collection_only:
        expected_envelope = {
            "mode": "collection_only_pinned_v32",
            "component_maxima": dict(COLLECTION_ONLY_COMPONENT_MAXIMA),
            "predicted_maximum_additional_bytes": COLLECTION_ONLY_PREDICTED_MAX_BYTES,
            "predicted_headroom_bytes": cast(int, observed_ledger["maximum_additional_bytes"])
            - COLLECTION_ONLY_PREDICTED_MAX_BYTES,
            "source_payloads_read": False,
            "models_loaded": False,
        }
        if (
            cast(int, observed_ledger["maximum_additional_bytes"])
            < COLLECTION_ONLY_PREDICTED_MAX_BYTES
            or receipt.get("collection_only_resource_envelope") != expected_envelope
        ):
            raise ValueError("resume receipt collection-only resource envelope is stale")
    return receipt, execution_spec, spec
