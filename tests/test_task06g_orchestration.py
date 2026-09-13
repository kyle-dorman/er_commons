"""Focused source-free proof for Task 06G orchestration boundaries."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from er_commons.artifact_io import json_bytes, sha256_file
from er_commons.task06g.core import (
    canonical_bytes,
    derive_identity,
    load_object,
    publish_directory_no_clobber,
    reference,
)
from er_commons.task06g.driver import run_replay
from er_commons.task06g.finalization import (
    FinalizationHooks,
    _verify_compact_completion,
    _verify_reference_inventory,
    _verify_replay_record_excluding_candidate,
    _verify_resolved_closure,
    finalize_readiness,
)
from er_commons.task06g.launch import (
    _validate_collection_prelaunch_ledger,
    _verify_collection_initial_packet,
    _verify_full_initial_packet,
    build_launch_packet,
    launch_resume,
)
from er_commons.task06g.packets import (
    COLLECTION_ONLY_COMPONENT_MAXIMA,
    COLLECTION_ONLY_PREDICTED_MAX_BYTES,
    _compact_input_state,
    collection_only_resource_prediction,
    evidence_root_record,
    preflight_prelaunch,
    preflight_resume,
    resource_ledger,
    verify_collection_only_resource_prediction,
    verify_evidence_root_record,
)
from er_commons.task06g.phases import (
    _roots,
    publish_aggregate,
    publish_checkpoint_inventory,
    resolve_phase,
    verify_existing_phase,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, value: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))
    return path


def test_collection_generation_resolves_only_the_explicit_data_root_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Portable v33 recipes bind the configured artifact authority, not a literal token path."""
    recipe = tmp_path / "repo/configs/task06/v1/generation.json"
    recipe.parent.mkdir(parents=True)
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setattr(
        "er_commons.settings.load_settings",
        lambda: SimpleNamespace(data_root=artifact_root),
    )
    _, repository, artifacts = _roots(
        recipe,
        {"repository_root": "../../..", "data_root": "${ER_COMMONS_DATA_ROOT}"},
    )
    assert repository == (tmp_path / "repo").resolve()
    assert artifacts == artifact_root.resolve()


def test_collection_launch_allows_only_bounded_initial_phase_growth() -> None:
    """Initial resolution may consume its frozen allowance after prelaunch observation."""
    prior = {
        "total_cap_bytes": 1_000_000_000,
        "prospective_external_reserve_bytes": 67_108_864,
        "replay_bytes": 0,
        "maximum_additional_bytes": 900_000_000,
    }
    current = {**prior, "replay_bytes": 200_000, "maximum_additional_bytes": 899_800_000}
    _validate_collection_prelaunch_ledger(prior, current)

    too_large = {
        **current,
        "replay_bytes": COLLECTION_ONLY_COMPONENT_MAXIMA["initial_specs_checkpoint_bytes"] + 1,
    }
    with pytest.raises(ValueError, match="prelaunch accounting is stale"):
        _validate_collection_prelaunch_ledger(prior, too_large)


@pytest.mark.parametrize("change", ["extra", "missing", "altered", "symlink"])
def test_collection_launch_requires_exact_frozen_initial_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    """The byte allowance cannot admit any replay entry outside the frozen packet."""
    replay = tmp_path / "replay"
    initial = replay / "resolved_specs_v1/00_initial"
    expected = {
        "phase_manifest.json": b'{"status":"complete"}\n',
        "receipts/spec.json": b'{"validation":"passed"}\n',
    }
    for relative, content in expected.items():
        path = initial / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    monkeypatch.setattr(
        "er_commons.task06g.phases._phase_files",
        lambda *_args, **_kwargs: ("00_initial", expected),
    )
    if change == "extra":
        _write(replay / "unrelated.json", {"small": True})
    elif change == "missing":
        (initial / "receipts/spec.json").unlink()
    elif change == "altered":
        (initial / "receipts/spec.json").write_bytes(b'{"validation":"failed"}\n')
    else:
        (replay / "unexpected-link").symlink_to(initial / "phase_manifest.json")

    with pytest.raises(ValueError, match="prelaunch replay"):
        _verify_collection_initial_packet(tmp_path / "generation.json", replay)


def test_collection_launch_accepts_exact_frozen_initial_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replay = tmp_path / "replay"
    initial = replay / "resolved_specs_v1/00_initial"
    expected = {
        "phase_manifest.json": b'{"status":"complete"}\n',
        "receipts/spec.json": b'{"validation":"passed"}\n',
    }
    for relative, content in expected.items():
        path = initial / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    monkeypatch.setattr(
        "er_commons.task06g.phases._phase_files",
        lambda *_args, **_kwargs: ("00_initial", expected),
    )

    _verify_collection_initial_packet(tmp_path / "generation.json", replay)


@pytest.mark.parametrize("change", ["extra_phase", "missing", "altered", "symlink"])
def test_full_launch_requires_exact_frozen_initial_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    """A full replay launch byte-compares its complete resolved initial phase."""
    replay = tmp_path / "replay"
    initial = replay / "resolved_specs_v1/00_initial"
    expected = {
        "phase_manifest.json": b'{"status":"complete"}\n',
        "receipts/spec.json": b'{"validation":"passed"}\n',
    }
    for relative, content in expected.items():
        path = initial / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    monkeypatch.setattr(
        "er_commons.task06g.phases._phase_files",
        lambda *_args, **_kwargs: ("00_initial", expected),
    )
    if change == "extra_phase":
        _write(replay / "resolved_specs_v1/10_relink/extra.json", {"small": True})
    elif change == "missing":
        (initial / "receipts/spec.json").unlink()
    elif change == "altered":
        (initial / "receipts/spec.json").write_bytes(b'{"validation":"failed"}\n')
    else:
        (initial / "unexpected-link").symlink_to(initial / "phase_manifest.json")

    with pytest.raises(ValueError, match="full replay"):
        _verify_full_initial_packet(tmp_path / "generation.json", replay)


def test_v38_restores_full_source_free_replay_commands() -> None:
    """Reject the superseded collection-only graph before v38 packet freezing."""
    execution = json.loads(
        (PROJECT_ROOT / "configs/task06/v4/task06g_execution_v1.json").read_bytes()
    )
    assert execution["command_order"][:3] == [
        "document_feir_appendix_f1",
        "document_deir_appendix_a",
        "document_deir_main",
    ]
    assert "relink_and_assemble" in execution["command_order"]
    assert execution["resource_limits"]["max_output_bytes"] == 52 * 1024**3
    assert all(
        "conversion" not in " ".join(command["argv"]).lower()
        and "model" not in " ".join(command["argv"]).lower()
        for command in execution["commands"]
    )


def test_evidence_root_inherits_sealed_payload_digest_without_opening(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cumulative accounting uses producer inventory evidence for preserved images."""
    candidate = tmp_path / "candidate"
    payload = candidate / "tables/page.png"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"preserved")
    digest = sha256_file(payload)
    _write(
        candidate / "records/artifact_inventory.json",
        {
            "file_count": 1,
            "byte_count": payload.stat().st_size,
            "files": [
                {
                    "path": "tables/page.png",
                    "sha256": digest,
                    "byte_size": payload.stat().st_size,
                }
            ],
        },
    )
    original = Path.open

    def guarded(path: Path, *args: object, **kwargs: object):
        if path.suffix == ".png":
            pytest.fail(f"preserved payload opened: {path}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    record = evidence_root_record(candidate)
    assert next(row for row in record["files"] if row["path"] == "tables/page.png") == {
        "path": "tables/page.png",
        "sha256": digest,
        "byte_size": len(b"preserved"),
    }
    assert verify_evidence_root_record(record) == candidate.resolve()


def test_evidence_root_ignores_absent_payload_rows_in_partial_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Partial diagnostics inherit only inventory payloads they actually retain."""
    candidate = tmp_path / "candidate"
    payload = candidate / "tables/present.png"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"present")
    digest = sha256_file(payload)
    _write(
        candidate / "records/artifact_inventory.json",
        {
            "files": [
                {
                    "path": "tables/present.png",
                    "sha256": digest,
                    "byte_size": payload.stat().st_size,
                },
                {
                    "path": "tables/absent.png",
                    "sha256": "0" * 64,
                    "byte_size": 123,
                },
            ]
        },
    )
    original = Path.open

    def guarded(path: Path, *args: object, **kwargs: object):
        if path.suffix == ".png":
            pytest.fail(f"preserved payload opened: {path}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    record = evidence_root_record(candidate)
    payload_rows = [row for row in record["files"] if row["path"].endswith(".png")]
    assert payload_rows == [
        {
            "path": "tables/present.png",
            "sha256": digest,
            "byte_size": len(b"present"),
        }
    ]


def test_evidence_root_inherits_legacy_named_inventory_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Older producer inventories with name fields remain usable without image reads."""
    candidate = tmp_path / "diagnostic"
    payload = candidate / "page-002.png"
    candidate.mkdir()
    payload.write_bytes(b"legacy")
    digest = sha256_file(payload)
    _write(
        candidate / "inventory.json",
        {
            "files": [
                {
                    "name": payload.name,
                    "sha256": digest,
                    "byte_size": payload.stat().st_size,
                }
            ]
        },
    )
    original = Path.open

    def guarded(path: Path, *args: object, **kwargs: object):
        if path.suffix == ".png":
            pytest.fail(f"preserved payload opened: {path}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    record = evidence_root_record(candidate)
    assert next(row for row in record["files"] if row["path"] == payload.name) == {
        "path": payload.name,
        "sha256": digest,
        "byte_size": len(b"legacy"),
    }


def test_payload_inventory_rejects_symlink_and_unnormalized_path(tmp_path: Path) -> None:
    """Inventory evidence itself stays contained and uses one canonical path spelling."""
    outside = _write(tmp_path / "outside.json", {"files": []})
    symlink_root = tmp_path / "symlinked"
    (symlink_root / "records").mkdir(parents=True)
    (symlink_root / "records/artifact_inventory.json").symlink_to(outside)
    with pytest.raises(ValueError, match="contained regular file"):
        evidence_root_record(symlink_root)

    candidate = tmp_path / "unnormalized"
    payload = candidate / "tables/page.png"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"preserved")
    _write(
        candidate / "records/artifact_inventory.json",
        {
            "files": [
                {
                    "path": "tables//page.png",
                    "sha256": sha256_file(payload),
                    "byte_size": payload.stat().st_size,
                }
            ]
        },
    )
    with pytest.raises(ValueError, match="unsafe artifact inventory path"):
        evidence_root_record(candidate)


def _phase_fixture(root: Path) -> tuple[Path, Path]:
    template = _write(root / "template.json", {"fixed": "sealed", "candidate_id": None})
    schema = _write(
        root / "schema.json",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["fixed", "candidate_id"],
            "properties": {
                "fixed": {"const": "sealed"},
                "candidate_id": {"type": "string"},
            },
            "additionalProperties": False,
        },
    )
    completion = _write(root / "completion.json", {"status": "complete"})
    checkpoint = {
        "verified": True,
        "derived_id": "docv1-abc",
        "recomputed_id": "docv1-abc",
        "stage_completion": reference(completion, root=root),
    }
    _write(root / "checkpoint.json", checkpoint)
    generation = {
        "schema_version": "er_commons.task06g.generation.v1",
        "phases": {
            "initial": {
                "directory": "00_initial",
                "specs": [
                    {
                        "template": "template.json",
                        "template_sha256": sha256_file(template),
                        "schema": "schema.json",
                        "schema_sha256": sha256_file(schema),
                        "generator": {"sha256": "0" * 64},
                        "destination": "resolved.json",
                        "resolutions": [
                            {
                                "pointer": "/candidate_id",
                                "checkpoint": "checkpoint.json",
                                "source_pointer": "/derived_id",
                            }
                        ],
                    }
                ],
            }
        },
    }
    return _write(root / "generation.json", generation), root / "resolved"


def test_phase_resolution_is_deterministic_no_clobber_and_allowlisted(tmp_path: Path) -> None:
    generation, output = _phase_fixture(tmp_path)
    phase = resolve_phase(generation, "initial", output)
    first = {
        path.relative_to(phase): path.read_bytes() for path in phase.rglob("*") if path.is_file()
    }
    assert load_object(phase / "resolved.json") == {"fixed": "sealed", "candidate_id": "docv1-abc"}
    assert resolve_phase(generation, "initial", output, resume_existing=True) == phase
    assert first == {
        path.relative_to(phase): path.read_bytes() for path in phase.rglob("*") if path.is_file()
    }
    with pytest.raises(FileExistsError):
        resolve_phase(generation, "initial", output)
    (phase / "resolved.json").write_text("{}\n")
    with pytest.raises(ValueError, match="differs"):
        resolve_phase(generation, "initial", output, resume_existing=True)


def test_prelaunch_accepts_only_exact_published_initial_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    generation, _ = _phase_fixture(repo)
    data = tmp_path / "data"
    replay = data / "replay"
    resolved = replay / "resolved_specs_v1"
    phase = resolve_phase(generation, "initial", resolved)
    monkeypatch.setattr("er_commons.task06g.packets.tmux_is_live", lambda _: False)
    monkeypatch.setattr("er_commons.task06g.packets.live_replay_processes", lambda *_: [])

    receipt = preflight_prelaunch(
        generation,
        replay,
        data / "execution_attempt_v1",
        data / "prelaunch_recovery_v1",
    )
    record = load_object(receipt)
    assert record["initial_phase_state"] == "published_exact"
    assert record["compact_input_state"] == "absent"
    assert record["managed_paths"][0]["file_count"] == len(
        [path for path in phase.rglob("*") if path.is_file()]
    )
    assert verify_existing_phase(generation, "initial", resolved) == phase

    (phase / "resolved.json").write_text("{}\n")
    with pytest.raises(ValueError, match="differs"):
        preflight_prelaunch(
            generation,
            replay,
            data / "execution_attempt_v1",
            data / "prelaunch_recovery_v2",
        )


def test_recovery_receipt_does_not_change_initial_phase_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    generation, _ = _phase_fixture(repo)
    data = tmp_path / "data"
    ordinary_root = data / "ordinary/resolved_specs_v1"
    recovered_replay = data / "recovered"
    ordinary = resolve_phase(generation, "initial", ordinary_root)
    monkeypatch.setattr("er_commons.task06g.packets.tmux_is_live", lambda _: False)
    monkeypatch.setattr("er_commons.task06g.packets.live_replay_processes", lambda *_: [])
    recovery = preflight_prelaunch(
        generation,
        recovered_replay,
        data / "execution_attempt_v1",
        data / "prelaunch_recovery_v1",
    )
    assert load_object(recovery)["initial_phase_state"] == "absent"
    recovered = resolve_phase(
        generation,
        "initial",
        recovered_replay / "resolved_specs_v1",
        prelaunch_recovery_receipt=recovery,
    )
    assert {
        path.relative_to(ordinary).as_posix(): path.read_bytes()
        for path in ordinary.rglob("*")
        if path.is_file()
    } == {
        path.relative_to(recovered).as_posix(): path.read_bytes()
        for path in recovered.rglob("*")
        if path.is_file()
    }


def test_prelaunch_rejects_attempt_root_outside_replay_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A mistyped volume cannot be sealed as the intended fresh attempt."""
    generation, _ = _phase_fixture(tmp_path / "repo")
    data = tmp_path / "data"
    monkeypatch.setattr("er_commons.task06g.packets.tmux_is_live", lambda _: False)
    monkeypatch.setattr("er_commons.task06g.packets.live_replay_processes", lambda *_: [])

    with pytest.raises(ValueError, match="must be siblings"):
        preflight_prelaunch(
            generation,
            data / "replay",
            tmp_path / "mistyped-volume/execution_attempt_v1",
            data / "prelaunch_recovery_v1",
        )


def test_prelaunch_rejects_partial_candidate_unexplained_and_live_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("er_commons.task06g.packets.tmux_is_live", lambda _: False)
    monkeypatch.setattr("er_commons.task06g.packets.live_replay_processes", lambda *_: [])

    def fresh(name: str) -> tuple[Path, Path, Path]:
        root = tmp_path / name
        generation, _ = _phase_fixture(root / "repo")
        data = root / "data"
        return generation, data / "replay", data

    generation, replay, data = fresh("partial")
    _write(replay / "resolved_specs_v1/00_initial/resolved.json", {"partial": True})
    with pytest.raises(ValueError, match="partial"):
        preflight_prelaunch(generation, replay, data / "execution_attempt_v1", data / "receipt")

    generation, replay, data = fresh("candidate")
    _write(replay / "document_records/candidate/records/completion_record.json", {})
    with pytest.raises(ValueError, match="candidate"):
        preflight_prelaunch(generation, replay, data / "execution_attempt_v1", data / "receipt")

    generation, replay, data = fresh("unexplained")
    _write(replay / "mystery/file.json", {})
    with pytest.raises(ValueError, match="unexplained"):
        preflight_prelaunch(generation, replay, data / "execution_attempt_v1", data / "receipt")

    generation, replay, data = fresh("live")
    monkeypatch.setattr(
        "er_commons.task06g.packets.live_replay_processes",
        lambda *_: [{"pid": 99, "ppid": 1, "command": "task06g replay"}],
    )
    with pytest.raises(ValueError, match="process/tmux"):
        preflight_prelaunch(generation, replay, data / "execution_attempt_v1", data / "receipt")


def test_prelaunch_compact_input_closure_is_exact_and_source_free(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    config_root = repo / "configs/task06/v1"
    sources = [f"source_{index:02d}" for index in range(35)]
    catalog_value = {"sources": [{"source": {"source_id": item}} for item in sources]}
    expected_catalog = _write(config_root / "task06g_source_family_catalog_v1.json", catalog_value)
    generation_path = _write(
        config_root / "generation.json",
        {"repository_root": "../../..", "source_order": sources},
    )
    generation = load_object(generation_path)
    replay = tmp_path / "data/replay"
    initial = replay / "resolved_specs_v1/00_initial"
    identity = _write(initial / "production_identity.json", {"extraction_id": "exv1-test"})
    document = _write(initial / "task06g_document_v1.json", {"kind": "document"})
    collection = _write(initial / "task06g_collection_v1.json", {"kind": "collection"})
    catalog = replay / "inputs/task06g_source_family_catalog_v1.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_bytes(expected_catalog.read_bytes())
    assert _compact_input_state(generation_path, generation, replay, "published_exact")[0] == (
        "catalog_only_exact"
    )
    readiness = {
        "status": "ready_for_user_authorized_clean_run",
        "production_extraction_id": "exv1-test",
        "production_identity_sha256": sha256_file(identity),
        "document_run_spec_sha256": sha256_file(document),
        "collection_run_spec_sha256": sha256_file(collection),
        "source_pdf_bytes_read": False,
        "model_files_read": False,
        "producer_identity_derivation_run": False,
        "execution_boundary": "source/model execution not run",
        "source_scope": {
            "source_count": 35,
            "page_count": 49_022,
            "ordered_source_ids": sources,
        },
        "catalog": {"sha256": sha256_file(catalog), "byte_size": catalog.stat().st_size},
    }
    _write(replay / "inputs/task03h_preparation_readiness.json", readiness)
    assert _compact_input_state(generation_path, generation, replay, "published_exact")[0] == (
        "complete_exact"
    )
    readiness["source_pdf_bytes_read"] = True
    _write(replay / "inputs/task03h_preparation_readiness.json", readiness)
    with pytest.raises(ValueError, match="readiness differs"):
        _compact_input_state(generation_path, generation, replay, "published_exact")


def test_preexecution_checkpoint_shares_atomic_initial_phase_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A pre-rename crash cannot expose a checkpoint without its initial specs."""
    destination = tmp_path / "resolved_specs_v1/00_initial"
    files = {
        "task06g_document_v1.json": canonical_bytes({"kind": "document"}),
        "pre_execution_production_identity_checkpoint.json": canonical_bytes({"verified": True}),
        "phase_manifest.json": canonical_bytes({"phase": "initial"}),
    }
    original_rename = Path.rename

    def crash_before_publish(path: Path, target: Path) -> Path:
        if path.name.startswith(".00_initial.staging-"):
            raise RuntimeError("injected pre-publication crash")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", crash_before_publish)
    with pytest.raises(RuntimeError, match="injected"):
        publish_directory_no_clobber(destination, files)
    assert not destination.exists()
    assert not (
        tmp_path / "identity_checkpoints_v1/pre_execution_production_identity.json"
    ).exists()
    staging = list(destination.parent.glob(".00_initial.staging-*"))
    assert len(staging) == 1
    assert {
        path.relative_to(staging[0]).as_posix() for path in staging[0].rglob("*") if path.is_file()
    } == set(files)

    monkeypatch.setattr(Path, "rename", original_rename)
    publish_directory_no_clobber(destination, files)
    with pytest.raises(FileExistsError):
        publish_directory_no_clobber(destination, files)


def test_identity_derivation_is_canonical_and_input_sensitive() -> None:
    assert derive_identity("docv1-", {"a": 1, "b": 2}) == derive_identity(
        "docv1-", {"b": 2, "a": 1}
    )
    assert derive_identity("docv1-", {"a": 1}) != derive_identity("docv1-", {"a": 2})


def test_phase_rejects_wildcard_and_unverified_checkpoint(tmp_path: Path) -> None:
    generation, output = _phase_fixture(tmp_path)
    value = load_object(generation)
    value["phases"]["initial"]["specs"][0]["resolutions"][0]["pointer"] = "/*"
    _write(generation, value)
    with pytest.raises(ValueError, match="non-exact"):
        resolve_phase(generation, "initial", output)
    generation, output = _phase_fixture(tmp_path / "second")
    checkpoint = load_object(tmp_path / "second/checkpoint.json")
    checkpoint["verified"] = False
    _write(tmp_path / "second/checkpoint.json", checkpoint)
    with pytest.raises(ValueError, match="not independently verified"):
        resolve_phase(generation, "initial", output)


def _execution_spec(root: Path, *, ledger_roots: list[Path] | None = None) -> Path:
    return _write(
        root / "execution_spec.json",
        {
            "repository_working_directory": str(root),
            "tmux_session": "er-commons-06g-replay-v1",
            "limits": {
                "max_wall_seconds": 86400,
                "max_rss_bytes": 10 * 1024**3,
                "max_output_bytes": 32 * 1024**3,
                "minimum_free_bytes": 64 * 1024**3,
            },
            "commands": [{"stage": "one", "argv": ["true"]}],
            "ledger_sibling_roots": [str(path) for path in (ledger_roots or [])],
            "finalization_required_files": [
                "resolved_specs_v1/aggregate_v1/resolved_spec_manifest.json",
                "resolved_specs_v1/aggregate_v1/artifact_inventory.json",
                "identity_checkpoints_v1/inventory.json",
                "correspondence_v1/completion.json",
                "comparison_v1/completion.json",
            ],
        },
    )


def _strict_resume_fixture(
    root: Path, *, with_first_process_phase: bool = False
) -> tuple[Path, Path, Path]:
    """Build a source-free resolved initial phase and one failed supervisor attempt."""
    repository = root / "repo"
    data = root / "data"
    repository.mkdir()
    data.mkdir()
    replay = data / "replay"
    resolved = replay / "resolved_specs_v1"
    generation = repository / "generation.json"
    template = repository / "execution_template.json"
    schema = _write(
        repository / "execution_schema.json",
        {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"},
    )
    phase_name = "document_stages/feir_appendix_f1/01_content_parsing"
    checkpoint_name = "document_stage_checkpoints_v1/feir_appendix_f1/01_content_parsing.json"
    execution = {
        "schema_version": "er_commons.task06g.execution_template.v1",
        "repository_working_directory": str(repository),
        "generation_spec": str(generation),
        "tmux_session": "er-commons-06g-replay-v1",
        "resource_limits": {
            "max_wall_seconds": 86400,
            "max_rss_bytes": 10 * 1024**3,
            "max_output_bytes": 32 * 1024**3,
            "minimum_free_bytes": 64 * 1024**3,
        },
        "ledger_sibling_roots": [],
        "resolver_closure": {
            "checkpoint_root": str(replay / "identity_checkpoints_v1"),
            "checkpoint_files": [],
            "process_checkpoint_files": [checkpoint_name] if with_first_process_phase else [],
            "resolved_specs_root": str(resolved),
            "phase_directories": (
                ["00_initial", phase_name, "10_relink", "20_comparison"]
                if with_first_process_phase
                else ["00_initial"]
            ),
        },
    }
    _write(template, execution)
    _write(
        generation,
        {
            "schema_version": "er_commons.task06g.generation.v1",
            "repository_root": ".",
            "data_root": str(data),
            "phases": {
                "initial": {
                    "directory": "00_initial",
                    "specs": [
                        {
                            "template": template.name,
                            "template_sha256": sha256_file(template),
                            "schema": schema.name,
                            "schema_sha256": sha256_file(schema),
                            "generator": {"sha256": "0" * 64},
                            "destination": "task06g_execution_v1.json",
                            "resolutions": [],
                        }
                    ],
                }
            },
        },
    )
    resolve_phase(generation, "initial", resolved)
    execution_spec = resolved / "00_initial/task06g_execution_v1.json"
    if with_first_process_phase:
        phase = resolved / phase_name
        phase.mkdir(parents=True)
        source_template = repository / "content_parsing.json"
        source_template.write_bytes(
            (PROJECT_ROOT / "configs/task06/v1/feir_appendix_f1/content_parsing.json").read_bytes()
        )
        config = phase / "content_parsing.json"
        config.write_bytes(source_template.read_bytes())
        receipt = _write(
            phase / "content_parsing.receipt.json",
            {
                "schema_version": "er_commons.task06g.process_config_receipt.v1",
                "source_id": "feir_appendix_f1",
                "stage": "content_parsing",
                "template": reference(source_template, root=repository),
                "generator": reference(generation, root=repository),
                "resolved": reference(config, root=phase),
                "validation": {"loader": "content_parsing", "passed": True},
            },
        )
        _write(
            phase / "phase_manifest.json",
            {
                "schema_version": "er_commons.task06g.process_config_phase.v1",
                "source_id": "feir_appendix_f1",
                "stage": "content_parsing",
                "generation_spec": reference(generation, root=repository),
                "external_checkpoints": [],
                "managed_files": [
                    reference(config, root=phase),
                    reference(receipt, root=phase),
                ],
                "completion_last": True,
            },
        )
        completion = _write(
            data / "producer/prv1-one/records/completion_record.json", {"status": "complete"}
        )
        inventory = _write(
            data / "producer/prv1-one/records/artifact_inventory.json", {"files": []}
        )
        _write(
            resolved / checkpoint_name,
            {
                "schema_version": "er_commons.task06g.process_identity_checkpoint.v1",
                "source_id": "feir_appendix_f1",
                "stage": "content_parsing",
                "verified": True,
                "derived_id": "prv1-one",
                "recomputed_id": "prv1-one",
                "stage_completion": reference(completion, root=data),
                "stage_inventory": reference(inventory, root=data),
                "resolved_config_ref": reference(config, root=data),
            },
        )
    attempt = data / "execution_attempt_v1"
    attempt.mkdir()
    status = {
        "schema_version": "background_execution_v1",
        "status": "failed",
        "output_root": str(replay.resolve()),
        "attempt_root": str(attempt.resolve()),
        "finished_at": "2026-09-11T00:00:00+00:00",
        "returncode": 1,
    }
    _write(attempt / "status.json", status)
    _write(attempt / "execution.json", status)
    (attempt / "command.log").write_text("failed\n")
    return execution_spec, replay, attempt


def test_resume_preflight_verifies_strict_attempt_and_replay_closure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec, replay, prior = _strict_resume_fixture(tmp_path)
    monkeypatch.setattr("er_commons.task06g.packets.tmux_is_live", lambda _: False)
    monkeypatch.setattr("er_commons.task06g.packets.live_replay_processes", lambda *_: [])
    receipt = preflight_resume(
        spec,
        replay,
        prior,
        replay.parent / "execution_attempt_v2",
        replay.parent / "resume_preflight_v2",
    )
    value = load_object(receipt)
    assert value["prior_attempt_observation"]["state"] == "terminal_failed"
    assert value["replay_observation"]["resolved_phases"] == ["00_initial"]
    assert value["replay_observation"]["identity_checkpoints"] == []


def test_resume_accepts_interruption_during_first_document_process_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use execution dependency order, not terminal relink order, for resume prefixes."""
    spec, replay, prior = _strict_resume_fixture(tmp_path, with_first_process_phase=True)
    monkeypatch.setattr("er_commons.task06g.packets.tmux_is_live", lambda _: False)
    monkeypatch.setattr("er_commons.task06g.packets.live_replay_processes", lambda *_: [])

    receipt = preflight_resume(
        spec,
        replay,
        prior,
        replay.parent / "execution_attempt_v2",
        replay.parent / "resume_preflight_v2",
    )

    observation = load_object(receipt)["replay_observation"]
    assert observation["resolved_phases"] == [
        "00_initial",
        "document_stages/feir_appendix_f1/01_content_parsing",
    ]
    assert observation["process_configs"]["checkpoint_count"] == 1


@pytest.mark.parametrize(
    "mutation",
    [
        "attempt_extra",
        "phase_tamper",
        "replay_extra",
        "future_progress",
        "managed_tamper",
        "partial_identity",
        "live",
    ],
)
def test_resume_preflight_rejects_partial_tampered_unexplained_or_live_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    spec, replay, prior = _strict_resume_fixture(tmp_path)
    monkeypatch.setattr("er_commons.task06g.packets.tmux_is_live", lambda _: False)
    monkeypatch.setattr("er_commons.task06g.packets.live_replay_processes", lambda *_: [])
    if mutation == "attempt_extra":
        (prior / "unexplained").write_text("x")
    elif mutation == "phase_tamper":
        (replay / "resolved_specs_v1/00_initial/task06g_execution_v1.json").write_text("{}\n")
    elif mutation == "replay_extra":
        (replay / "mystery").mkdir()
    elif mutation == "future_progress":
        (replay / "document_progress/attempt_v2").mkdir(parents=True)
    elif mutation == "managed_tamper":
        candidate = replay / "document_publications/documents/example/docv1-test"
        payload = candidate / "content/value.json"
        _write(payload, {"value": 1})
        inventory = _write(
            candidate / "records/artifact_inventory.json",
            {"files": [reference(payload, root=candidate)]},
        )
        _write(
            candidate / "records/completion_record.json",
            {"status": "complete", "artifact_inventory_sha256": sha256_file(inventory)},
        )
        payload.write_text("tampered\n")
    elif mutation == "partial_identity":
        _write(
            replay / "document_publications/documents/example/docv1-test/records/"
            "extraction_identity.json",
            {"extraction_id": "docv1-test"},
        )
    else:
        monkeypatch.setattr(
            "er_commons.task06g.packets.live_replay_processes",
            lambda *_: [{"pid": 42, "command": "replay"}],
        )
    with pytest.raises((ValueError, FileExistsError)):
        preflight_resume(
            spec,
            replay,
            prior,
            replay.parent / "execution_attempt_v2",
            replay.parent / "resume_preflight_v2",
        )


def test_launch_packet_is_complete_and_exact_reuse_rejects_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("er_commons.task06g.launch.tmux_is_live", lambda _: False)
    spec = _execution_spec(tmp_path)
    replay = tmp_path / "replay"
    replay.mkdir()
    packet = tmp_path / "launch"
    attempt = tmp_path / "execution_attempt_v1"
    _, dispatch = build_launch_packet(spec, replay, attempt, packet)
    assert [path.name for path in packet.iterdir()] == [
        "dispatch_record.json",
        "launch_intent.json",
        "packet_manifest.json",
    ] or len(list(packet.iterdir())) == 3
    assert dispatch["driver_argv"][-1] == reference(packet / "launch_intent.json")["sha256"]
    intent = load_object(packet / "launch_intent.json")
    assert (
        sum(path.stat().st_size for path in packet.iterdir())
        <= intent["resource_ledger"]["prospective_external_reserve_bytes"]
    )
    assert intent["progress_root"] == str((replay / "document_progress/attempt_v1").resolve())
    assert intent["environment"]["ER_COMMONS_DATA_ROOT"] == "/Volumes/x10pro/er_commons"
    assert dispatch["supervisor_argv"][0] == "env"
    assert "ER_COMMONS_DATA_ROOT=/Volumes/x10pro/er_commons" in dispatch["supervisor_argv"]
    assert "OMP_NUM_THREADS=4" in dispatch["supervisor_argv"]
    build_launch_packet(spec, replay, attempt, packet, reuse_exact=True)
    (packet / "dispatch_record.json").write_text("{}\n")
    with pytest.raises(ValueError, match="differs"):
        build_launch_packet(spec, replay, attempt, packet, reuse_exact=True)


def test_launch_packet_rejects_bytes_beyond_external_reserve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refuse dispatch when immutable launch metadata outgrows its ledger reserve."""
    monkeypatch.setattr("er_commons.task06g.launch.tmux_is_live", lambda _: False)
    monkeypatch.setattr(
        "er_commons.task06g.launch.resource_ledger",
        lambda replay, siblings: resource_ledger(replay, siblings, reserve=1),
    )
    replay = tmp_path / "replay"
    replay.mkdir()

    with pytest.raises(ValueError, match="launch packet exceeds"):
        build_launch_packet(
            _execution_spec(tmp_path),
            replay,
            tmp_path / "execution_attempt_v1",
            tmp_path / "launch",
        )
    assert not (tmp_path / "launch").exists()


def test_resume_ledger_does_not_double_subtract_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("er_commons.task06g.packets.tmux_is_live", lambda _: False)
    replay = tmp_path / "replay"
    prior = tmp_path / "execution_attempt_v1"
    replay.mkdir()
    prior.mkdir()
    (replay / "artifact.json").write_bytes(b"x" * 100)
    (prior / "command.log").write_bytes(b"x" * 25)
    spec = _execution_spec(tmp_path)
    receipt_path = preflight_resume(
        spec, replay, prior, tmp_path / "execution_attempt_v2", tmp_path / "resume_preflight_v2"
    )
    ledger = load_object(receipt_path)["resource_ledger"]
    assert load_object(receipt_path)["progress_root"] == str(
        (replay / "document_progress/attempt_v2").resolve()
    )
    assert ledger["maximum_additional_bytes"] == ledger["supervisor_max_output_bytes"] - 100
    direct = resource_ledger(replay, [prior])
    assert direct["preserved_sibling_bytes"] == 25


def test_default_external_reserve_accounts_beyond_former_launch_packet_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject a launch packet that outgrows cumulative external accounting."""
    replay = tmp_path / "replay"
    replay.mkdir()
    prior = tmp_path / "prior"
    prior.mkdir()
    (prior / "evidence.json").write_bytes(b"x" * (17 * 1024**2))
    ledger = resource_ledger(replay, [prior])

    assert ledger["prospective_external_reserve_bytes"] == 64 * 1024**2
    assert ledger["supervisor_max_output_bytes"] == (32 * 1024**3 - 17 * 1024**2 - 64 * 1024**2)


def _collection_only_prediction_inputs(
    tmp_path: Path,
) -> tuple[Path, list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    replay = tmp_path / "replay_v33"
    replay.mkdir()
    prior = tmp_path / "preserved_v32"
    completions = [
        reference(_write(prior / f"source_{ordinal:02d}/completion.json", {"ordinal": ordinal}))
        for ordinal in range(35)
    ]
    precedents = [reference(_write(prior / "task04d_scope_completion.json", {"ok": True}))]
    payload = prior / "preserved.pdf"
    payload.write_bytes(b"sealed without reopening")
    _write(
        prior / "records/artifact_inventory.json",
        {
            "files": [
                {
                    "path": payload.name,
                    "sha256": "a" * 64,
                    "byte_size": payload.stat().st_size,
                }
            ]
        },
    )
    return replay, [evidence_root_record(prior)], precedents, completions


def test_collection_only_prediction_binds_frozen_components_and_evidence(
    tmp_path: Path,
) -> None:
    replay, preserved, precedents, completions = _collection_only_prediction_inputs(tmp_path)
    prediction = collection_only_resource_prediction(replay, preserved, precedents, completions)

    assert prediction["component_maxima"] == COLLECTION_ONLY_COMPONENT_MAXIMA
    assert prediction["predicted_maximum_additional_bytes"] == 1_443_089_302
    assert sum(COLLECTION_ONLY_COMPONENT_MAXIMA.values()) == (COLLECTION_ONLY_PREDICTED_MAX_BYTES)
    assert prediction["predicted_headroom_bytes"] == (
        prediction["resource_ledger"]["maximum_additional_bytes"]
        - COLLECTION_ONLY_PREDICTED_MAX_BYTES
    )
    assert prediction["source_payloads_read"] is False
    assert prediction["models_loaded"] is False
    assert (
        verify_collection_only_resource_prediction(
            prediction, replay, preserved, precedents, completions
        )
        == prediction
    )


def test_collection_only_prediction_accepts_exact_remaining_allowance_and_rejects_less(
    tmp_path: Path,
) -> None:
    replay, preserved, precedents, completions = _collection_only_prediction_inputs(tmp_path)
    preserved_bytes = int(preserved[0]["byte_count"])
    exact_cap = preserved_bytes + 64 * 1024**2 + COLLECTION_ONLY_PREDICTED_MAX_BYTES

    prediction = collection_only_resource_prediction(
        replay,
        preserved,
        precedents,
        completions,
        total_cap=exact_cap,
    )
    assert prediction["predicted_headroom_bytes"] == 0
    with pytest.raises(ValueError, match="predicted output exceeds"):
        collection_only_resource_prediction(
            replay,
            preserved,
            precedents,
            completions,
            total_cap=exact_cap - 1,
        )


def test_collection_only_prediction_rejects_stale_sibling_or_basis(
    tmp_path: Path,
) -> None:
    replay, preserved, precedents, completions = _collection_only_prediction_inputs(tmp_path)
    prediction = collection_only_resource_prediction(replay, preserved, precedents, completions)

    (tmp_path / "unexplained_sibling").mkdir()
    with pytest.raises(ValueError, match="stale sibling evidence closure"):
        verify_collection_only_resource_prediction(
            prediction, replay, preserved, precedents, completions
        )
    (tmp_path / "unexplained_sibling").rmdir()
    _write(Path(str(completions[0]["path"])), {"ordinal": "changed"})
    with pytest.raises(ValueError, match="artifact reference mismatch"):
        verify_collection_only_resource_prediction(
            prediction, replay, preserved, precedents, completions
        )


def test_collection_only_prediction_requires_exact_unique_35_completion_basis(
    tmp_path: Path,
) -> None:
    replay, preserved, precedents, completions = _collection_only_prediction_inputs(tmp_path)
    with pytest.raises(ValueError, match="exactly 35"):
        collection_only_resource_prediction(replay, preserved, precedents, completions[:-1])
    with pytest.raises(ValueError, match="repeats pinned completion"):
        collection_only_resource_prediction(
            replay, preserved, precedents, [*completions[:-1], completions[0]]
        )


def test_collection_only_prediction_does_not_open_preserved_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replay, preserved, precedents, completions = _collection_only_prediction_inputs(tmp_path)
    original = Path.open

    def guarded(path: Path, *args: object, **kwargs: object):
        if path.suffix == ".pdf":
            pytest.fail(f"preserved payload opened: {path}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    prediction = collection_only_resource_prediction(replay, preserved, precedents, completions)
    assert prediction["source_payloads_read"] is False


def test_initial_and_resume_bindings_materialize_fresh_progress_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replay = tmp_path / "replay"
    replay.mkdir()
    spec = _write(
        tmp_path / "execution_spec.json",
        {
            **load_object(_execution_spec(tmp_path)),
            "commands": [
                {
                    "stage": "document",
                    "argv": ["runner", "--progress-root", "{progress_root}"],
                    "runtime_values": [
                        {
                            "name": "progress_root",
                            "authority": "launch_binding",
                            "pointer": "/progress_root",
                        }
                    ],
                }
            ],
        },
    )
    monkeypatch.setattr("er_commons.task06g.launch.tmux_is_live", lambda _: False)
    monkeypatch.setattr("er_commons.task06g.packets.tmux_is_live", lambda _: False)
    monkeypatch.setattr("er_commons.task06g.packets.live_replay_processes", lambda *_: [])
    observed: list[list[str]] = []
    monkeypatch.setattr(
        "er_commons.task06g.driver.subprocess.run",
        lambda argv, **_: observed.append(argv),
    )

    launch = tmp_path / "initial_launch_v1"
    build_launch_packet(spec, replay, tmp_path / "execution_attempt_v1", launch)
    initial_binding = launch / "launch_intent.json"
    run_replay(spec, initial_binding, sha256_file(initial_binding))
    assert observed.pop() == [
        "runner",
        "--progress-root",
        str((replay / "document_progress/attempt_v1").resolve()),
    ]

    prior = tmp_path / "execution_attempt_v1"
    prior.mkdir()
    receipt = preflight_resume(
        spec,
        replay,
        prior,
        tmp_path / "execution_attempt_v2",
        tmp_path / "resume_preflight_v2",
    )
    run_replay(spec, receipt, sha256_file(receipt))
    assert observed.pop() == [
        "runner",
        "--progress-root",
        str((replay / "document_progress/attempt_v2").resolve()),
    ]
    dispatched: list[tuple[str, Path, list[str]]] = []
    monkeypatch.setattr(
        "er_commons.task06g.launch.dispatch_tmux",
        lambda session, working_directory, argv: dispatched.append(
            (session, working_directory, argv)
        ),
    )
    resume_launch = launch_resume(receipt)
    resume_record = load_object(resume_launch)
    assert resume_record["tmux_session"] == "er-commons-06g-replay-v1-attempt-v2"
    assert dispatched[0][0] == resume_record["tmux_session"]
    assert dispatched[0][2] == resume_record["supervisor_argv"]


def test_resume_requires_exact_consecutive_no_clobber_namespaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("er_commons.task06g.packets.tmux_is_live", lambda _: False)
    replay = tmp_path / "replay"
    replay.mkdir()
    prior = tmp_path / "execution_attempt_v2"
    prior.mkdir()
    spec = _execution_spec(tmp_path)
    with pytest.raises(ValueError, match="exact next ordinal"):
        preflight_resume(
            spec,
            replay,
            prior,
            tmp_path / "execution_attempt_v3",
            tmp_path / "wrong_receipt_name",
        )
    progress = replay / "document_progress/attempt_v3"
    progress.mkdir(parents=True)
    with pytest.raises(FileExistsError, match="progress root"):
        preflight_resume(
            spec,
            replay,
            prior,
            tmp_path / "execution_attempt_v3",
            tmp_path / "resume_preflight_v3",
        )


def test_resume_launch_rejects_artifacts_changed_after_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("er_commons.task06g.packets.tmux_is_live", lambda _: False)
    monkeypatch.setattr("er_commons.task06g.packets.live_replay_processes", lambda *_: [])
    replay = tmp_path / "replay"
    replay.mkdir()
    (replay / "artifact.json").write_text("before", encoding="utf-8")
    prior = tmp_path / "execution_attempt_v1"
    prior.mkdir()
    spec = _execution_spec(tmp_path)
    receipt = preflight_resume(
        spec,
        replay,
        prior,
        tmp_path / "execution_attempt_v2",
        tmp_path / "resume_preflight_v2",
    )
    (replay / "artifact.json").write_text("after", encoding="utf-8")

    with pytest.raises(ValueError, match="observations are stale"):
        launch_resume(receipt)


def test_collection_resume_treats_attempt17_as_the_base_tmux_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first v33 attempt uses the unsuffixed session despite its inherited ordinal."""
    replay = tmp_path / "replay_v33"
    replay.mkdir()
    prior = tmp_path / "execution_attempt_v17"
    prior.mkdir()
    spec = _write(
        tmp_path / "execution.json",
        {
            "schema_version": "er_commons.task06g.collection_execution_template.v1",
            "tmux_session": "er-commons-06g-replay-v33",
            "initial_attempt_number": 17,
            "ledger_sibling_roots": [],
        },
    )
    inspected: list[str] = []
    monkeypatch.setattr("er_commons.task06g.packets.tmux_is_live", lambda _: False)
    monkeypatch.setattr(
        "er_commons.task06g.packets.live_replay_processes",
        lambda _root, session: inspected.append(session) or [],
    )
    monkeypatch.setattr(
        "er_commons.task06g.packets._verify_prior_attempt",
        lambda *_: {"state": "verified"},
    )
    monkeypatch.setattr(
        "er_commons.task06g.packets._verify_replay_closure",
        lambda *_: {"state": "verified"},
    )
    receipt = preflight_resume(
        spec,
        replay,
        prior,
        tmp_path / "execution_attempt_v18",
        tmp_path / "resume_preflight_v18",
    )
    assert inspected == ["er-commons-06g-replay-v33"]
    assert load_object(receipt)["tmux_session"] == "er-commons-06g-replay-v33-attempt-v18"


def test_driver_verifies_binding_and_exact_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    binding = _write(tmp_path / "binding.json", {"accepted": True})
    spec = _execution_spec(tmp_path)
    observed: list[list[str]] = []

    def fake_run(argv: list[str], **_: Any) -> None:
        observed.append(argv)

    monkeypatch.setattr("er_commons.task06g.driver.subprocess.run", fake_run)
    run_replay(spec, binding, sha256_file(binding))
    assert observed == [["true"]]
    with pytest.raises(ValueError, match="digest mismatch"):
        run_replay(spec, binding, "0" * 64)


def test_driver_preserves_failed_child_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A failed reviewed command leaves its exact child exception in the durable log."""
    binding = _write(tmp_path / "binding.json", {"accepted": True})
    spec = _execution_spec(tmp_path)

    def fail(argv: list[str], **_: Any) -> None:
        raise subprocess.CalledProcessError(1, argv, output="exact child failure\n")

    monkeypatch.setattr("er_commons.task06g.driver.subprocess.run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        run_replay(spec, binding, sha256_file(binding))
    assert capsys.readouterr().out == "exact child failure\n"


def test_collection_driver_preserves_handoff_checkpoint_before_comparison_interruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A comparison interruption cannot erase the already verified collection boundary."""
    completion = _write(tmp_path / "handoff_completion.json", {"status": "ready"})
    binding = _write(tmp_path / "binding.json", {"accepted": True})
    checkpoint = tmp_path / "identity_checkpoints_v1/stages/collection_handoff.json"
    spec = _write(
        tmp_path / "execution_spec.json",
        {
            "schema_version": "er_commons.task06g.collection_execution_template.v1",
            "repository_working_directory": str(tmp_path),
            "generation_spec": str(tmp_path / "generation.json"),
            "command_order": ["assemble_handoff", "resolve_comparison_specs"],
            "commands": [
                {
                    "stage": "assemble_handoff",
                    "argv": ["assemble"],
                    "checkpoint_after": {
                        "stage_key": "collection_handoff",
                        "path": str(checkpoint),
                        "completion_source": "stdout_handoff",
                    },
                },
                {"stage": "resolve_comparison_specs", "argv": ["compare"]},
            ],
        },
    )
    calls = 0

    def run(argv: list[str], **_: Any) -> SimpleNamespace:
        nonlocal calls
        calls += 1
        if calls == 1:
            return SimpleNamespace(stdout=f"handoff_completion={completion}\n")
        raise subprocess.CalledProcessError(1, argv, output="comparison interrupted\n")

    published: list[tuple[str, Path]] = []
    monkeypatch.setattr("er_commons.task06g.driver.subprocess.run", run)
    monkeypatch.setattr(
        "er_commons.task06g.driver.publish_stage_checkpoint",
        lambda _generation, stage, _completion, path, **_kwargs: published.append((stage, path)),
    )
    with pytest.raises(subprocess.CalledProcessError):
        run_replay(spec, binding, sha256_file(binding))
    assert published == [("collection_handoff", checkpoint)]
    assert calls == 2


def test_resume_driver_exactly_reuses_stage_and_closure_publications(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    completion = _write(tmp_path / "handoff_completion.json", {"status": "ready"})
    binding = _write(
        tmp_path / "resume_receipt.json",
        {
            "schema_version": "er_commons.task06g.resume_receipt.v1",
            "status": "accepted",
        },
    )
    checkpoint_root = tmp_path / "identity_checkpoints_v1"
    resolved_root = tmp_path / "resolved_specs_v1"
    spec = _write(
        tmp_path / "execution_spec.json",
        {
            "repository_working_directory": str(tmp_path),
            "generation_spec": str(tmp_path / "generation.json"),
            "commands": [
                {
                    "stage": "handoff",
                    "argv": ["true"],
                    "checkpoint_after": {
                        "stage_key": "collection_handoff",
                        "path": str(checkpoint_root / "stages/collection_handoff.json"),
                        "completion_source": "stdout_handoff",
                    },
                }
            ],
            "resolver_closure": {
                "checkpoint_root": str(checkpoint_root),
                "checkpoint_files": ["stages/collection_handoff.json"],
                "resolved_specs_root": str(resolved_root),
                "phase_directories": ["00_initial"],
            },
        },
    )
    calls: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        "er_commons.task06g.driver.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout=f"handoff_completion={completion}\n"),
    )
    monkeypatch.setattr(
        "er_commons.task06g.driver.publish_stage_checkpoint",
        lambda *_args, resume_existing=False, **_kwargs: calls.append(
            ("checkpoint", resume_existing)
        ),
    )
    monkeypatch.setattr(
        "er_commons.task06g.driver.publish_checkpoint_inventory",
        lambda *_args, resume_existing=False, **_kwargs: calls.append(
            ("inventory", resume_existing)
        ),
    )
    monkeypatch.setattr(
        "er_commons.task06g.driver.publish_aggregate",
        lambda *_args, resume_existing=False, **_kwargs: calls.append(
            ("aggregate", resume_existing)
        ),
    )

    run_replay(spec, binding, sha256_file(binding))

    assert calls == [("checkpoint", True), ("inventory", True), ("aggregate", True)]


def test_checkpoint_inventory_and_aggregate_resume_require_exact_bytes(tmp_path: Path) -> None:
    checkpoint_root = tmp_path / "identity_checkpoints_v1"
    checkpoint = _write(
        checkpoint_root / "stages/document.json",
        {"verified": True, "derived_id": "docv1-one", "recomputed_id": "docv1-one"},
    )
    inventory = publish_checkpoint_inventory(checkpoint_root, ["stages/document.json"])
    assert (
        publish_checkpoint_inventory(
            checkpoint_root, ["stages/document.json"], resume_existing=True
        )
        == inventory
    )
    with pytest.raises(FileExistsError, match="collision"):
        publish_checkpoint_inventory(checkpoint_root, ["stages/document.json"])
    checkpoint.write_bytes(canonical_bytes({"verified": False}))
    with pytest.raises(FileExistsError, match="collision"):
        publish_checkpoint_inventory(
            checkpoint_root, ["stages/document.json"], resume_existing=True
        )

    resolved_root = tmp_path / "resolved_specs_v1"
    phase = resolved_root / "00_initial"
    production_checkpoint = _write(
        phase / "pre_execution_production_identity_checkpoint.json",
        {"verified": True, "derived_id": "exv1-one", "recomputed_id": "exv1-one"},
    )
    _write(
        phase / "phase_manifest.json",
        {"managed_files": [reference(production_checkpoint, root=phase)]},
    )
    aggregate = publish_aggregate(resolved_root, ["00_initial"], production_checkpoint)
    assert (
        publish_aggregate(
            resolved_root,
            ["00_initial"],
            production_checkpoint,
            resume_existing=True,
        )
        == aggregate
    )
    with pytest.raises(FileExistsError, match="already exists"):
        publish_aggregate(resolved_root, ["00_initial"], production_checkpoint)
    production_checkpoint.write_bytes(canonical_bytes({"verified": False}))
    with pytest.raises(ValueError, match="differs"):
        publish_aggregate(
            resolved_root,
            ["00_initial"],
            production_checkpoint,
            resume_existing=True,
        )


def test_collection_aggregate_binds_only_collection_identity_and_handoff_checkpoint(
    tmp_path: Path,
) -> None:
    """Collection-only resolution closes no inherited document-process checkpoints."""
    resolved = tmp_path / "resolved_specs_v1"
    for phase in ("00_initial", "20_comparison"):
        _write(resolved / phase / "phase_manifest.json", {"phase": phase})
    pre_execution = _write(
        resolved / "00_initial/pre_execution_collection_identity_checkpoint.json",
        {"verified": True, "derived_id": "cprodv1-one", "recomputed_id": "cprodv1-one"},
    )
    aggregate = publish_aggregate(
        resolved,
        ["00_initial", "20_comparison"],
        pre_execution,
        process_checkpoint_names=[],
        pre_execution_manifest_field="pre_execution_collection_identity_checkpoint",
    )
    manifest = load_object(aggregate / "resolved_spec_manifest.json")
    assert manifest["pre_execution_collection_identity_checkpoint"]["path"] == (
        "00_initial/pre_execution_collection_identity_checkpoint.json"
    )
    assert "pre_execution_production_identity_checkpoint" not in manifest
    assert manifest["process_identity_checkpoints"] == []


def test_resolved_closure_verifies_production_checkpoint_from_resolved_root(
    tmp_path: Path,
) -> None:
    resolved_root = tmp_path / "resolved_specs_v1"
    phase = resolved_root / "00_initial"
    checkpoint = _write(
        phase / "pre_execution_production_identity_checkpoint.json",
        {"verified": True, "derived_id": "exv1-one", "recomputed_id": "exv1-one"},
    )
    _write(
        phase / "phase_manifest.json",
        {
            "managed_files": [reference(checkpoint, root=phase)],
        },
    )
    aggregate = publish_aggregate(resolved_root, ["00_initial"], checkpoint)

    _verify_resolved_closure(
        aggregate,
        spec={
            "resolver_closure": {
                "phase_directories": ["00_initial"],
                "process_checkpoint_files": [],
            }
        },
        artifact_root=tmp_path,
    )


def test_resolved_closure_requires_each_document_phase_and_process_checkpoint(
    tmp_path: Path,
) -> None:
    """Bind staged configs and owning identity checkpoints into terminal closure."""
    resolved_root = tmp_path / "resolved_specs_v1"
    initial = resolved_root / "00_initial"
    production = _write(
        initial / "pre_execution_production_identity_checkpoint.json",
        {"verified": True, "derived_id": "exv1-one", "recomputed_id": "exv1-one"},
    )
    _write(
        initial / "phase_manifest.json",
        {"managed_files": [reference(production, root=initial)]},
    )
    phase_name = "document_stages/deir_main/01_content_parsing"
    phase = resolved_root / phase_name
    config = _write(phase / "content_parsing.json", {"source_id": "deir_main"})
    receipt = _write(phase / "content_parsing.receipt.json", {"stage": "content_parsing"})
    completion = _write(tmp_path / "evidence/prv1-one/records/completion_record.json", {})
    inventory = _write(tmp_path / "evidence/prv1-one/records/artifact_inventory.json", {})
    _write(
        phase / "phase_manifest.json",
        {
            "external_checkpoints": [],
            "managed_files": [
                reference(config, root=phase),
                reference(receipt, root=phase),
            ],
        },
    )
    checkpoint_name = "document_stage_checkpoints_v1/deir_main/01_content_parsing.json"
    _write(
        resolved_root / checkpoint_name,
        {
            "schema_version": "er_commons.task06g.process_identity_checkpoint.v1",
            "source_id": "deir_main",
            "stage": "content_parsing",
            "stage_completion": {
                "authority": "artifact_root",
                **reference(completion, root=tmp_path),
            },
            "stage_inventory": {
                "authority": "artifact_root",
                **reference(inventory, root=tmp_path),
            },
            "resolved_config_ref": {
                "authority": "artifact_root",
                **reference(config, root=tmp_path),
            },
            "derived_id": "prv1-one",
            "recomputed_id": "prv1-one",
            "verified": True,
        },
    )
    aggregate = publish_aggregate(
        resolved_root,
        ["00_initial", phase_name],
        production,
        process_checkpoint_names=[checkpoint_name],
    )
    spec = {
        "resolver_closure": {
            "phase_directories": ["00_initial", phase_name],
            "process_checkpoint_files": [checkpoint_name],
        }
    }
    _verify_resolved_closure(aggregate, spec=spec, artifact_root=tmp_path)

    missing = {
        "resolver_closure": {
            "phase_directories": ["00_initial", phase_name],
            "process_checkpoint_files": [],
        }
    }
    with pytest.raises(ValueError, match="external closure differs"):
        _verify_resolved_closure(aggregate, spec=missing, artifact_root=tmp_path)


def test_finalizer_requires_terminal_success_and_writes_completion_last(tmp_path: Path) -> None:
    replay = tmp_path / "replay"
    attempt = tmp_path / "execution_attempt_v1"
    replay.mkdir()
    launch_root = tmp_path / "initial_launch_v1"
    spec = _execution_spec(tmp_path, ledger_roots=[launch_root])
    for relative in load_object(spec)["finalization_required_files"]:
        _write(replay / relative, {"status": "complete"})
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("er_commons.task06g.launch.tmux_is_live", lambda _: False)
        _, dispatch = build_launch_packet(spec, replay, attempt, launch_root)
    attempt.mkdir()
    _write(
        attempt / "execution.json",
        {
            "status": "succeeded",
            "returncode": 0,
            "reason": None,
            "surviving_pids": [],
            "command": dispatch["driver_argv"],
        },
    )
    candidate = finalize_readiness(spec, attempt, tmp_path / "finalization_attempt_v1", replay)
    assert load_object(candidate / "completion.json")["status"] == "complete"
    assert set(path.name for path in candidate.iterdir()) == {
        "artifact_inventory.json",
        "readiness.json",
        "completion.json",
    }
    assert (
        finalize_readiness(spec, attempt, tmp_path / "finalization_attempt_v1", replay) == candidate
    )


def test_finalizer_preserves_failure_without_readiness(tmp_path: Path) -> None:
    replay = tmp_path / "replay"
    attempt = tmp_path / "execution_attempt_v1"
    replay.mkdir()
    attempt.mkdir()
    spec = _execution_spec(tmp_path)
    _write(attempt / "execution.json", {"status": "failed", "returncode": 1, "reason": "boom"})
    finalization = tmp_path / "finalization_attempt_v1"
    with pytest.raises(ValueError, match="not succeeded"):
        finalize_readiness(spec, attempt, finalization, replay)
    assert (finalization / "failure.json").is_file()
    assert not (replay / "readiness_candidates").exists()


@pytest.mark.parametrize(
    "hook_name",
    ["after_inventory", "after_readiness", "after_completion"],
)
def test_finalizer_preserves_interrupted_staging_before_rename(
    tmp_path: Path, hook_name: str
) -> None:
    replay, attempt, spec = _successful_finalization_fixture(tmp_path)

    def interrupt() -> None:
        raise RuntimeError(f"interrupted {hook_name}")

    hooks = FinalizationHooks(**{hook_name: interrupt})
    finalization = tmp_path / "finalization_attempt_v1"
    with pytest.raises(RuntimeError, match=hook_name):
        finalize_readiness(spec, attempt, finalization, replay, hooks=hooks)
    assert (finalization / "failure.json").is_file()
    assert not (replay / "readiness_candidates/finalization_attempt_v1").exists()
    assert any(
        path.name.startswith(".finalization_attempt_v1.staging-")
        for path in (replay / "readiness_candidates").iterdir()
    )


def test_finalizer_reuses_exact_candidate_after_post_rename_interruption(tmp_path: Path) -> None:
    replay, attempt, spec = _successful_finalization_fixture(tmp_path)

    def interrupt() -> None:
        raise RuntimeError("interrupted after rename")

    finalization = tmp_path / "finalization_attempt_v1"
    with pytest.raises(RuntimeError, match="after rename"):
        finalize_readiness(
            spec,
            attempt,
            finalization,
            replay,
            hooks=FinalizationHooks(after_rename=interrupt),
        )
    candidate = replay / "readiness_candidates/finalization_attempt_v1"
    assert finalize_readiness(spec, attempt, finalization, replay) == candidate


def _successful_finalization_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Build one minimal terminal chain for source-free finalizer tests."""
    replay = tmp_path / "replay"
    attempt = tmp_path / "execution_attempt_v1"
    replay.mkdir()
    launch_root = tmp_path / "initial_launch_v1"
    spec = _execution_spec(tmp_path, ledger_roots=[launch_root])
    for relative in load_object(spec)["finalization_required_files"]:
        _write(replay / relative, {"status": "complete"})
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("er_commons.task06g.launch.tmux_is_live", lambda _: False)
        _, dispatch = build_launch_packet(spec, replay, attempt, launch_root)
    attempt.mkdir()
    _write(
        attempt / "execution.json",
        {
            "status": "succeeded",
            "returncode": 0,
            "reason": None,
            "surviving_pids": [],
            "command": dispatch["driver_argv"],
        },
    )
    return replay, attempt, spec


def test_finalizer_accepts_abandoned_staging_from_sealed_launch_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("er_commons.task06g.packets.tmux_is_live", lambda _: False)
    monkeypatch.setattr("er_commons.task06g.launch.tmux_is_live", lambda _: False)
    data = tmp_path / "data"
    repo = tmp_path / "repo"
    replay = data / "replay"
    replay.mkdir(parents=True)
    abandoned = data / ".initial_launch_v1.staging-abandoned"
    _write(abandoned / "partial.json", {"status": "abandoned"})
    generation = _write(repo / "generation.json", {"tmux_session": "er-commons-06g-replay-v1"})
    attempt = data / "execution_attempt_v1"
    recovery = preflight_prelaunch(generation, replay, attempt, data / "prelaunch_recovery_v1")
    launch = data / "initial_launch_v1"
    spec = _execution_spec(repo, ledger_roots=[launch])
    for relative in load_object(spec)["finalization_required_files"]:
        _write(replay / relative, {"status": "complete"})
    _, dispatch = build_launch_packet(
        spec,
        replay,
        attempt,
        launch,
        binding_path=recovery,
    )
    attempt.mkdir()
    _write(
        attempt / "execution.json",
        {
            "status": "succeeded",
            "returncode": 0,
            "reason": None,
            "surviving_pids": [],
            "command": dispatch["driver_argv"],
        },
    )
    candidate = finalize_readiness(spec, attempt, data / "finalization_attempt_v1", replay)
    inventory = load_object(candidate / "artifact_inventory.json")
    roots = {item["path"] for item in inventory["external_evidence_roots"]}
    assert str(abandoned.resolve()) in roots


def test_finalizer_rejects_unexplained_sibling(tmp_path: Path) -> None:
    replay, attempt, spec = _successful_finalization_fixture(tmp_path)
    (tmp_path / "unexplained").mkdir()
    with pytest.raises(ValueError, match="unenumerated evidence siblings"):
        finalize_readiness(spec, attempt, tmp_path / "finalization_attempt_v1", replay)


def test_finalizer_preserves_existing_attempts_without_inventing_unused_ordinals(
    tmp_path: Path,
) -> None:
    """An explicitly unused attempt number is not missing evidence."""
    replay = tmp_path / "replay"
    attempt = tmp_path / "execution_attempt_v3"
    replay.mkdir()
    launch_root = tmp_path / "initial_launch_v1"
    spec = _execution_spec(tmp_path, ledger_roots=[launch_root])
    for relative in load_object(spec)["finalization_required_files"]:
        _write(replay / relative, {"status": "complete"})
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("er_commons.task06g.launch.tmux_is_live", lambda _: False)
        _, dispatch = build_launch_packet(spec, replay, attempt, launch_root)
    (tmp_path / "execution_attempt_v1").mkdir()
    attempt.mkdir()
    _write(
        attempt / "execution.json",
        {
            "status": "succeeded",
            "returncode": 0,
            "reason": None,
            "surviving_pids": [],
            "command": dispatch["driver_argv"],
        },
    )

    candidate = finalize_readiness(spec, attempt, tmp_path / "finalization_attempt_v1", replay)

    inventory = load_object(candidate / "artifact_inventory.json")
    roots = {item["path"] for item in inventory["external_evidence_roots"]}
    assert str((tmp_path / "execution_attempt_v1").resolve()) in roots
    assert not (tmp_path / "execution_attempt_v2").exists()


def test_finalizer_verifies_payloads_from_sealed_inventory_without_hashing(
    tmp_path: Path,
) -> None:
    """Readiness revalidation keeps prohibited payload bytes unopened."""
    root = tmp_path / "replay"
    payload = root / "producer/crop.png"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"png")
    _write(
        root / "producer/records/artifact_inventory.json",
        {
            "files": [
                {"path": "crop.png", "sha256": "0" * 64, "byte_size": 3},
            ]
        },
    )
    record = evidence_root_record(root)

    _verify_replay_record_excluding_candidate(
        record, root / "readiness_candidates/finalization_attempt_v3"
    )


def test_finalizer_semantically_rejects_hashed_but_nonterminal_compact_closure(
    tmp_path: Path,
) -> None:
    root = tmp_path / "correspondence_v1"
    payload = _write(root / "source_correspondence.json", {"rows": []})
    inventory = _write(
        root / "artifact_inventory.json",
        {"files": [reference(payload, root=root)]},
    )
    _write(
        root / "completion.json",
        {
            "schema_version": "er_commons.task06g.correspondence_completion.v1",
            "status": "complete",
            "task04_status": "not_evaluated",
            "artifact_inventory": reference(inventory, root=root),
            "completion_last": False,
        },
    )
    with pytest.raises(ValueError, match="completion semantics differ"):
        _verify_compact_completion(root, "correspondence")


def test_finalizer_semantically_rejects_checkpoint_identity_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "identity_checkpoints_v1"
    checkpoint = _write(
        root / "stage.json",
        {"verified": True, "derived_id": "one", "recomputed_id": "two"},
    )
    _write(root / "inventory.json", {"files": [reference(checkpoint, root=root)]})
    with pytest.raises(ValueError, match="identity recomputation differs"):
        _verify_reference_inventory(root, "inventory.json", expected_paths={"stage.json"})


def test_orchestration_rejects_pdf_and_model_payload_references(tmp_path: Path) -> None:
    for name in ("source.pdf", "page.png", "model.safetensors"):
        path = tmp_path / name
        path.write_bytes(b"not opened")
        with pytest.raises(ValueError, match="prohibited payload access"):
            reference(path)
