"""Freeze the eligible 09A.3 development dataset without reopening legacy partitions."""

from __future__ import annotations

import copy
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

import ijson  # type: ignore[import-untyped]

from er_commons.artifact_io import json_bytes, stable_json_sha256
from er_commons.grounding_panel import DEV3, DEV6
from er_commons.grounding_stages import point_inputs
from er_commons.judge_packet_publication import (
    _binding,
    _inventory,
    _load_case_input,
    _planned_binding,
    _publish_output,
    _read,
    _verify_release,
)
from er_commons.judge_packet_requests import packet_content
from er_commons.judge_packets import build_packet
from er_commons.judge_qualification_packets import selected_rows
from er_commons.synthetic_intake import verify_binding

SCHEMA_VERSION = "task09e.grounding_dataset_panel.v1"
CASE_COUNTS = dict(zip(DEV6, (22, 27, 20, 23, 22, 22), strict=True))
PANELS = {"dev3": DEV3, "dev6": DEV6, "dev6_additions": DEV6[len(DEV3) :]}


def _eligible_metadata(path: Path, allowed: set[str]) -> list[dict[str, Any]]:
    """Read only routing scalars globally, selecting eligible rows from the six fixed cases."""
    rows = []
    seen: set[str] = set()
    eligible = 0
    for line in path.read_text().splitlines():
        row: dict[str, Any] = {}
        for prefix, event, value in ijson.parse(io.BytesIO(line.encode())):
            if prefix in {"variant_id", "case_id", "comparison_eligible"}:
                if event not in {"string", "boolean"} or prefix in row:
                    raise ValueError("Invalid or duplicate dataset routing field")
                row[prefix] = value
        if set(row) != {"variant_id", "case_id", "comparison_eligible"}:
            raise ValueError("Missing dataset routing metadata")
        if type(row["comparison_eligible"]) is not bool or row["variant_id"] in seen:
            raise ValueError("Invalid eligibility or duplicate variant identity")
        seen.add(row["variant_id"])
        if row["comparison_eligible"] != (row["variant_id"] in allowed):
            raise ValueError("Eligibility differs from sealed development reservation")
        eligible += row["comparison_eligible"]
        if row["case_id"] in DEV6 and row["comparison_eligible"]:
            rows.append(row)
    if len(seen) != 442 or eligible != 430 or not allowed <= seen:
        raise ValueError("Combined dataset must retain 442 variants and 430 eligible proposals")
    if dict(Counter(r["case_id"] for r in rows)) != CASE_COUNTS:
        raise ValueError("Fixed six-case eligible counts differ")
    return sorted(rows, key=lambda r: (DEV6.index(r["case_id"]), r["variant_id"]))


def _external_binding(binding: dict[str, Any]) -> Path:
    """Verify an explicitly pinned external pointer without walking any contained payloads."""
    path = Path(binding["path"])
    if not path.is_absolute():
        raise ValueError("External pointer must be absolute")
    return verify_binding(binding, path.parent)


def _sealed_file(path: Path, root: Path, inventory: dict[str, dict[str, Any]]) -> Path:
    """Resolve one file inside its pinned origin root and verify its inventory binding."""
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    return verify_binding(inventory[relative], root)


def freeze_dataset_panel(result_path: Path, release_path: Path, output: Path) -> dict[str, Any]:
    """Bind eligible combined answers, source packets and restricted proposals without inference."""
    result, release = _read(result_path), _read(release_path)
    if (
        result.get("schema_version") != "task09a3.final_result.v1"
        or result.get("status") != "complete_with_limitations"
        or result.get("annotation_version") != "task09a2.stage_expectations.v1"
    ):
        raise ValueError("Require the accepted combined 09A.3 result")
    root = Path(result["namespace"]).resolve()
    completion = verify_binding(result["namespace_completion"], root)
    current_inventory = _inventory(_read(completion)["inventory"]["files"])
    predecessor_path = _external_binding(result["predecessor_result"])
    predecessor = _read(predecessor_path)
    base_completion = _external_binding(predecessor["batch_completion"])
    base = base_completion.parent.resolve()
    base_inventory = _inventory(_read(base_completion)["inventory"]["files"])
    inventories = {root: current_inventory, base: base_inventory}

    def artifact(name: str) -> Path:
        """Require pointer and namespace seal agreement for each consumed publication file."""
        path = verify_binding(result["artifacts"][name], root)
        return _sealed_file(path, root, current_inventory)

    publication = _read(artifact("manifest.json"))
    if _external_binding(publication["base_completion"]) != base_completion:
        raise ValueError("Combined publication base completion differs")
    answers_path, expectations_path = artifact("answers.jsonl"), artifact("expectations.jsonl")
    origins_path = artifact("record_origins.jsonl")
    reservation_path = artifact("reservation.json")
    reservation = _read(reservation_path)
    groups = [
        reservation[k]
        for k in ("development_variant_ids", "excluded_variant_ids", "final_check_variant_ids")
    ]
    if [len(g) for g in groups] != [430, 12, 0] or len(set(sum(groups, []))) != 442:
        raise ValueError("Combined development reservation differs")
    selection = _eligible_metadata(expectations_path, set(groups[0]))
    ids = {row["variant_id"] for row in selection}
    answers = selected_rows(answers_path, ids)
    expectations = selected_rows(expectations_path, ids)
    origins = selected_rows(origins_path, ids)
    release_root, release_inventory, dev, allowed, corpus = _verify_release(release)
    if release.get("status") != "complete" or not set(DEV6) <= set(dev):
        raise ValueError("Require unchanged six-case development membership")
    rows, packets, restricted = [], [], []
    for selected in selection:
        key, case = selected["variant_id"], selected["case_id"]
        answer, expectation = answers[key], expectations[key]
        origin = Path(origins[key]["root"]).resolve()
        if origin not in inventories or set(origins[key]) != {"variant_id", "root"}:
            raise ValueError("Record origin is outside the pinned publication roots")
        source_path = _sealed_file(
            origin / "cases" / case / "input.json", origin, inventories[origin]
        )
        source = _load_case_input(
            source_path,
            case=case,
            release_id=release["release_id"],
            release_root=release_root,
            release_inventory=release_inventory,
            allowed_sources=allowed,
            variant=answer,
        )
        if (
            answer["case_id"] != case
            or expectation["case_id"] != case
            or expectation["comparison_eligible"] is not True
        ):
            raise ValueError("Selected answer, expectation or eligible case differs")
        for field in (
            "source_packet_hash",
            "parent_reference_hash",
            "reference_binding",
            "reference_version",
            "release_id",
            "annotation_version",
        ):
            if expectation[field] != answer[field]:
                raise ValueError("Answer and expectation source identities differ")
        for record in (answer, expectation):
            for value in record["provenance"].values():
                if isinstance(value, dict) and "path" in value:
                    path = verify_binding(value, origin)
                    _sealed_file(path, origin, inventories[origin])
        packet = build_packet(source, answer["answer"], "grounding")
        packet["id"] = key
        packets.append(packet)
        restricted.append({"sample_id": key, "expectation": expectation})
        rows.append(
            {
                "sample_id": key,
                "case_id": case,
                "category": expectation["perturbation_id"],
                "origin_root": str(origin),
                "record_origin": origins[key],
                "source_input": _binding(source_path),
                "answer_sha256": stable_json_sha256(answer["answer"]),
                "answer_record_sha256": stable_json_sha256(answer),
                "packet_sha256": stable_json_sha256(packet),
                "payload_sha256": stable_json_sha256(packet["payload"]),
                "expectation_sha256": stable_json_sha256(expectation),
                "expected_grounding": expectation["grounding"]["score"],
            }
        )
    files = {
        "packets.json": json_bytes(packets),
        "restricted_expectations.json": json_bytes(restricted),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "frozen",
        "source_result": _binding(result_path),
        "release_result": _binding(release_path),
        "namespace_completion": _binding(completion),
        "base_completion": _binding(base_completion),
        "corpus_manifest": _binding(corpus),
        "answers": _binding(answers_path),
        "expectations": _binding(expectations_path),
        "origins": _binding(origins_path),
        "reservation": _binding(reservation_path),
        "selection": "all_comparison_eligible_no_controls",
        "global_variants": 442,
        "global_eligible": 430,
        "case_counts": CASE_COUNTS,
        "panels": {
            name: [r["sample_id"] for r in rows if r["case_id"] in cases]
            for name, cases in PANELS.items()
        },
        "samples": rows,
        "artifacts": {name: _planned_binding(output / name, data) for name, data in files.items()},
        "inference_calls": 0,
        "reserved_test_payloads_decoded": False,
        "limitations": [
            "Synthetic stage expectations are diagnostic proposals, not calibrated truth."
        ],
    }
    files["manifest.json"] = json_bytes(manifest)
    _publish_output(output, files)
    return manifest


def load_dataset_panel_samples(manifest_path: Path, panel: str) -> list[dict[str, Any]]:
    """Load only frozen eligible records; stage proposals stay outside model-visible packets."""
    if panel not in PANELS:
        raise ValueError("Require dev3, dev6 or dev6_additions")
    manifest = _read(manifest_path)
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("status") != "frozen":
        raise ValueError("Require frozen combined dataset panel")
    rows = manifest["samples"]
    ids = [r["sample_id"] for r in rows]
    if len(ids) != len(set(ids)) or dict(Counter(r["case_id"] for r in rows)) != CASE_COUNTS:
        raise ValueError("Frozen selected population differs")
    for name, cases in PANELS.items():
        if manifest["panels"][name] != [r["sample_id"] for r in rows if r["case_id"] in cases]:
            raise ValueError("Panel membership or exact nesting differs")
    root = manifest_path.parent
    packet_rows = json.loads(
        verify_binding(manifest["artifacts"]["packets.json"], root).read_text()
    )
    expected_rows = json.loads(
        verify_binding(manifest["artifacts"]["restricted_expectations.json"], root).read_text()
    )
    packets = {r["id"]: r for r in packet_rows}
    expected = {r["sample_id"]: r["expectation"] for r in expected_rows}
    if (
        len(packets) != len(packet_rows)
        or len(expected) != len(expected_rows)
        or set(packets) != set(ids)
        or set(expected) != set(ids)
    ):
        raise ValueError("Packet and expectation populations differ")
    result = []
    for row in rows:
        key = row["sample_id"]
        packet, expectation = packets[key], expected[key]
        if (
            stable_json_sha256(packet) != row["packet_sha256"]
            or stable_json_sha256(packet["payload"]) != row["payload_sha256"]
            or stable_json_sha256(expectation) != row["expectation_sha256"]
            or expectation["case_id"] != row["case_id"]
            or expectation.get("comparison_eligible") is not True
            or expectation["grounding"]["score"] != row["expected_grounding"]
        ):
            raise ValueError("Frozen packet or expectation binding differs")
        if key not in manifest["panels"][panel]:
            continue
        packet_content(packet)
        stages = copy.deepcopy(expectation["grounding"])
        mapping = packet["mappings"]["candidate_points"]
        required = [p["point"]["point_id"] for p in point_inputs(packet)]
        try:
            expected_ids = [mapping[p["point_id"]] for p in stages["point_expectations"]]
        except KeyError as error:
            raise ValueError("Unknown stage expectation point identity") from error
        if expected_ids != required:
            raise ValueError("Stage expectations must exactly cover ordered non-conclusion points")
        for point in stages["point_expectations"]:
            point["point_id"] = mapping[point["point_id"]]
        stages["unsupported_premise_point_ids"] = [
            mapping[point_id] for point_id in stages["unsupported_premise_point_ids"]
        ]
        result.append(
            {
                "sample_id": key,
                "case_id": row["case_id"],
                "scope": "development",
                "packet": packet,
                "expected_score": row["expected_grounding"],
                "category": row["category"],
                "control": False,
                "stage_expectations": stages,
            }
        )
    return result
