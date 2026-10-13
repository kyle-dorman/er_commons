"""Pinned development selection stays label-blind and validates original provenance."""

import copy
import json

import pytest
from test_grounding_inspect import sample
from test_judge_qualification_packets import packet as source_packet

from er_commons import grounding_comparison_panel as panel
from er_commons.artifact_io import stable_json_sha256


def frozen_panel(tmp_path, monkeypatch):
    """Build a tiny invented frozen namespace with inaccessible restricted labels."""
    monkeypatch.setattr(panel, "CASE_COUNTS", {"invented": 1})
    monkeypatch.setattr(panel, "PANELS", {"dev3": ("invented",)})
    source = sample()
    key = source.sample_id
    packet = copy.deepcopy(source.packet)
    packet["id"] = key
    original_source = source_packet()
    answer = {
        "variant_id": key,
        "case_id": "invented",
        "answer": original_source["reference_answer"],
    }
    origin = {"variant_id": key, "root": str(tmp_path)}

    def write(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value))
        return panel.file_binding(path)

    row = {
        "sample_id": key,
        "case_id": "invented",
        "record_origin": origin,
        "origin_root": str(tmp_path),
        "source_input": write("source.json", original_source),
        "packet_sha256": stable_json_sha256(packet),
        "payload_sha256": stable_json_sha256(packet["payload"]),
        "answer_record_sha256": stable_json_sha256(answer),
        "answer_sha256": stable_json_sha256(answer["answer"]),
    }
    manifest = {
        "schema_version": panel.SCHEMA_VERSION,
        "status": "frozen",
        "samples": [row],
        "panels": {"dev3": [key]},
        "source_result": write("result.json", {}),
        "namespace_completion": write("completion.json", {}),
        "answers": write("answers.jsonl", answer),
        "origins": write("origins.jsonl", origin),
        "artifacts": {
            "packets.json": write("packets.json", [packet]),
            "restricted_expectations.json": {"path": "DO_NOT_OPEN"},
        },
    }
    write("manifest.json", manifest)
    return tmp_path / "manifest.json", manifest


def test_selected_development_loader_never_opens_labels(tmp_path, monkeypatch):
    """Only bound originals are read; scoring labels remain inaccessible."""
    path, _ = frozen_panel(tmp_path, monkeypatch)
    samples, bindings = panel.load_development_panel(
        path, "dev3", panel.file_binding(path)["sha256"]
    )
    assert len(samples) == 1
    assert samples[0].expected_score is None and samples[0].stage_expectations is None
    assert bindings["expectations_loaded"] is False


@pytest.mark.parametrize("mutation", ["case", "duplicate", "membership", "full_dev", "source"])
def test_development_loader_rejects_population_and_provenance_changes(
    tmp_path, monkeypatch, mutation
):
    """An explicitly changed manifest hash cannot bypass development or source checks."""
    path, value = frozen_panel(tmp_path, monkeypatch)
    requested = "dev3"
    if mutation == "case":
        value["samples"][0]["case_id"] = "reserved"
    elif mutation == "duplicate":
        value["samples"] *= 2
    elif mutation == "membership":
        value["panels"]["dev3"] = []
    elif mutation == "full_dev":
        requested = "full_dev"
    else:
        (tmp_path / "source.json").write_text("tampered")
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        panel.load_development_panel(path, requested, panel.file_binding(path)["sha256"])


def test_development_manifest_hash_precedes_decoding(tmp_path):
    """Wrong bytes cannot cause payload reads or JSON parsing."""
    path = tmp_path / "manifest.json"
    path.write_text("not JSON")
    with pytest.raises(ValueError, match="SHA-256 differs"):
        panel.load_development_panel(path, "dev3", "0" * 64)


@pytest.mark.parametrize("mutation", ["answer", "question", "evidence", "mapping"])
def test_pinned_manifest_cannot_bind_mismatched_packet_projection(tmp_path, monkeypatch, mutation):
    """Individually valid hashes cannot substitute packet content for bound original inputs."""
    path, manifest = frozen_panel(tmp_path, monkeypatch)
    packets_path = tmp_path / "packets.json"
    packets = json.loads(packets_path.read_text())
    packet = packets[0]
    if mutation == "answer":
        packet["payload"]["answer"]["conclusion"]["text"] = "Different invented conclusion."
    elif mutation == "question":
        packet["payload"]["question"] = "Different invented question?"
    elif mutation == "evidence":
        packet["payload"]["evidence"][0]["full_source_text"] = "Different invented evidence."
    else:
        packet["mappings"]["candidate_points"] = {"different_original": "P1"}
    packet["diagnostics"]["payload_sha256"] = stable_json_sha256(packet["payload"])
    packets_path.write_text(json.dumps(packets))
    manifest["artifacts"]["packets.json"] = panel.file_binding(packets_path)
    manifest["samples"][0]["packet_sha256"] = stable_json_sha256(packet)
    manifest["samples"][0]["payload_sha256"] = stable_json_sha256(packet["payload"])
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="original answer/source projection"):
        panel.load_development_panel(path, "dev3", panel.file_binding(path)["sha256"])


@pytest.mark.parametrize("changed_binding", [False, True])
def test_shared_source_verified_and_decoded_once_per_exact_binding(
    tmp_path, monkeypatch, changed_binding
):
    """Within-load reuse saves shared-source work without accepting altered identities."""
    path, manifest = frozen_panel(tmp_path, monkeypatch)
    monkeypatch.setattr(panel, "CASE_COUNTS", {"invented": 2})
    second = copy.deepcopy(manifest["samples"][0])
    second["sample_id"] = "second"
    second["record_origin"]["variant_id"] = "second"
    answer_path = tmp_path / "answers.jsonl"
    answer = json.loads(answer_path.read_text())
    second_answer = {**answer, "variant_id": "second"}
    second["answer_record_sha256"] = stable_json_sha256(second_answer)
    answer_path.write_text(json.dumps(answer) + "\n" + json.dumps(second_answer))
    manifest["answers"] = panel.file_binding(answer_path)
    origin_path = tmp_path / "origins.jsonl"
    origin_path.write_text(
        json.dumps(manifest["samples"][0]["record_origin"])
        + "\n"
        + json.dumps(second["record_origin"])
    )
    manifest["origins"] = panel.file_binding(origin_path)
    packets_path = tmp_path / "packets.json"
    packets = json.loads(packets_path.read_text())
    second_packet = {**packets[0], "id": "second"}
    second["packet_sha256"] = stable_json_sha256(second_packet)
    packets_path.write_text(json.dumps([*packets, second_packet]))
    manifest["artifacts"]["packets.json"] = panel.file_binding(packets_path)
    if changed_binding:
        second["source_input"]["sha256"] = "0" * 64
    manifest["samples"].append(second)
    manifest["panels"]["dev3"].append("second")
    path.write_text(json.dumps(manifest))
    expected_sha256 = panel.file_binding(path)["sha256"]
    checks, decodes, builds = [], [], []
    original_verify, original_read = panel.verify_binding, type(path).read_text
    original_build = panel.build_packet

    def verify(binding, root):
        if binding["path"] == str(tmp_path / "source.json"):
            checks.append(binding["sha256"])
        return original_verify(binding, root)

    def read(file, *args, **kwargs):
        if file == tmp_path / "source.json":
            decodes.append(True)
        return original_read(file, *args, **kwargs)

    def build(*args, **kwargs):
        builds.append(True)
        return original_build(*args, **kwargs)

    monkeypatch.setattr(panel, "verify_binding", verify)
    monkeypatch.setattr(type(path), "read_text", read)
    monkeypatch.setattr(panel, "build_packet", build)
    if changed_binding:
        with pytest.raises(ValueError, match="checksum"):
            panel.load_development_panel(path, "dev3", expected_sha256)
        assert len(checks) == 2 and len(decodes) == len(builds) == 1
    else:
        samples, bindings = panel.load_development_panel(path, "dev3", expected_sha256)
        assert len(samples) == 2 and len(bindings["sources"]) == 1
        assert len(checks) == len(decodes) == 1
        assert len(builds) == 2
