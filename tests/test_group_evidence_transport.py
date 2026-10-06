"""Independent compact-packet storage tests retain exact native and source bindings."""

import copy
import json

import pytest
from test_group_evidence import native
from test_group_evidence_live import prepared as prepared

from er_commons import group_evidence_live as live
from er_commons import group_evidence_transport as transport


def compact_fixture(tasks, root):
    """Save invented external packets and compact unchanged source-free task data."""
    paths = {}
    for task in tasks:
        data = task["data"]
        path = root / (data["case_label"] + ".json")
        path.write_text(json.dumps(data["packet"]))
        paths[data["case_label"]] = path
    return transport.compact_tasks(tasks, packet_paths_by_case=paths, data_root=root), paths


def export(tasks, root):
    """Simulate exact saved native decisions against original compact task bindings."""
    exported = [
        {**copy.deepcopy(task), "id": index, "project": 7, "annotations": []}
        for index, task in enumerate(tasks, 21)
    ]
    exported[0]["annotations"] = [
        native(
            c001_p01_label="supports",
            c001_outcome="supported",
            source_summary="Saved edited summary",
        )
    ]
    return live.normalize_export(
        exported,
        expected_tasks=tasks,
        project_id=7,
        actual_form=live.claim_form(1),
        reviewer_id="synthetic-only",
        export_lineage="transport-test",
        data_root=root,
    )


def test_compact_roundtrip_preserves_visible_fields_and_saved_review(prepared):
    tasks, root = prepared
    tasks = tasks[:2]
    compact, _ = compact_fixture(tasks, root)
    assert transport.hydrate_tasks(compact, data_root=root) == tasks
    for original, native_task in zip(tasks, compact, strict=True):
        assert "packet" not in native_task["data"]
        assert all(
            native_task["data"][key] == value
            for key, value in original["data"].items()
            if key != "packet"
        )
    before = export(tasks, root)["records"][0]
    after = export(compact, root)["records"][0]
    assert {key: after[key] for key in before} == before
    assert after["storage_revision"] == transport.VERSION
    assert after["native_task_sha256"] == live.evidence.digest(compact[0]["data"])
    assert after["task_sha256"] == compact[0]["data"]["expanded_task_sha256"]


@pytest.mark.parametrize(
    "mutation", ["missing", "root_escape", "raw_tamper", "semantic", "expanded", "revision"]
)
def test_compact_source_and_task_mutations_rejected(prepared, mutation):
    tasks, root = prepared
    compact, paths = compact_fixture(tasks[:1], root)
    export(compact, root)
    data = compact[0]["data"]
    if mutation == "missing":
        paths[data["case_label"]].unlink()
    elif mutation == "root_escape":
        data["packet_ref"]["path"] = "../outside.json"
    elif mutation == "raw_tamper":
        path = paths[data["case_label"]]
        path.write_text(path.read_text() + "\n")  # Same semantic packet, changed sealed bytes.
    elif mutation == "semantic":
        data["packet_sha256"] = "0" * 64
    elif mutation == "expanded":
        data["expanded_task_sha256"] = "0" * 64
    else:
        data["storage_revision"] = "unknown"
    with pytest.raises((ValueError, FileNotFoundError)):
        export(compact, root)


def test_native_binding_rejected_before_external_packet_open(prepared):
    tasks, root = prepared
    compact, paths = compact_fixture(tasks[:1], root)
    changed = {**copy.deepcopy(compact[0]), "id": 21, "project": 7, "annotations": []}
    changed["data"]["claim_html"] += "Changed native presentation"
    next(iter(paths.values())).unlink()
    with pytest.raises(ValueError, match="queue task"):
        live.normalize_export(
            [changed],
            expected_tasks=compact,
            project_id=7,
            actual_form=live.claim_form(1),
            reviewer_id="synthetic-only",
            export_lineage="transport-test",
            data_root=root,
        )


def test_compactor_requires_exact_prepared_packet(prepared):
    tasks, root = prepared
    compact, paths = compact_fixture(tasks[:1], root)
    with pytest.raises(ValueError, match="Expanded task"):
        transport.compact_tasks(compact, packet_paths_by_case=paths, data_root=root)
    path = next(iter(paths.values()))
    packet = json.loads(path.read_text())
    packet["case_id"] = "other-case"
    path.write_text(json.dumps(packet))
    with pytest.raises(ValueError, match="External packet differs"):
        transport.compact_tasks(tasks[:1], packet_paths_by_case=paths, data_root=root)
