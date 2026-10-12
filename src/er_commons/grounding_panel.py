"""Freeze nested Task 09E tuning panels through sealed development-only routing."""

from __future__ import annotations

import argparse
import io
import json
import logging
import re
from pathlib import Path
from typing import Any

import ijson  # type: ignore[import-untyped]

from er_commons.artifact_io import json_bytes, stable_json_sha256
from er_commons.judge_packet_publication import (
    _binding,
    _inventory,
    _load_case_input,
    _planned_binding,
    _publish_output,
    _read,
    _verify_release,
)
from er_commons.judge_packets import build_packet
from er_commons.judge_qualification_packets import selected_rows
from er_commons.synthetic_intake import verify_binding

DEV3 = ("C041", "C037", "C014")
DEV6 = (*DEV3, "C001", "C019", "C056")
_VARIANT = re.compile(r'"variant_id"\s*:\s*"([^"\\]+)"')
_FIELDS = {"variant_id", "case_id", "perturbation_id", "grounding.score", "comparison_eligible"}
# Set before reading answers or model results; lexicographic IDs break category ties.
_EDGE = {"C041": "C01", "C037": "R01", "C014": "O01", "C001": "P08", "C019": "C05", "C056": "P09"}


def selection_metadata(path: Path, allowed: set[str]) -> list[dict[str, Any]]:
    """Inspect only six-case eligible expectation metadata, never reserved payloads."""
    rows = []
    seen: set[str] = set()
    with path.open() as stream:
        for line in stream:
            ids = _VARIANT.findall(line)
            if len(ids) != 1:
                raise ValueError("Ambiguous expectation routing identity")
            key = ids[0]
            if key not in allowed or key.split("-", 1)[0] not in DEV6:
                continue
            metadata = {}
            for prefix, event, value in ijson.parse(io.BytesIO(line.encode())):
                if prefix in _FIELDS and event in {"string", "number", "null", "boolean"}:
                    if prefix in metadata:
                        raise ValueError("Duplicate expectation metadata field")
                    metadata[prefix] = value
            if (
                set(metadata) != _FIELDS
                or metadata["variant_id"] != key
                or metadata["case_id"] != key.split("-", 1)[0]
                or metadata["comparison_eligible"] is not True
                or key in seen
            ):
                raise ValueError("Invalid selected expectation metadata")
            seen.add(key)
            rows.append(metadata)
    expected = {key for key in allowed if key.split("-", 1)[0] in DEV6}
    if seen != expected:
        raise ValueError("Missing development expectation metadata")
    return rows


def choose_samples(metadata: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select four fixed distinct IDs per case with explicit preference fallbacks."""
    selected = []
    for case in DEV6:
        selected.append(
            {
                "sample_id": f"{case}-CONTROL",
                "case_id": case,
                "slot": "control",
                "category": "CONTROL",
                "expected_grounding": 2,
                "selection_reason": "Unchanged approved control; expectation is diagnostic.",
                "coverage_gap": None,
            }
        )
        available = sorted(
            (r for r in metadata if r["case_id"] == case), key=lambda r: r["variant_id"]
        )
        used: set[str] = set()
        for slot, score, preferred in (
            ("grounding_0", 0, {"F02", "F03"}),
            ("grounding_1", 1, {"F01", "F07"}),
            ("edge", "any", {_EDGE[case]}),
        ):
            eligible = [
                r
                for r in available
                if r["variant_id"] not in used and (score == "any" or r["grounding.score"] == score)
            ]
            preferred_rows = [r for r in eligible if r["perturbation_id"] in preferred]
            if not eligible:
                raise ValueError(f"No eligible distinct sample for {case}/{slot}")
            row = (preferred_rows or eligible)[0]
            used.add(row["variant_id"])
            gap = (
                None
                if preferred_rows
                else (
                    f"Preferred categories {sorted(preferred)} unavailable; "
                    "lexicographic eligible fallback."
                )
            )
            selected.append(
                {
                    "sample_id": row["variant_id"],
                    "case_id": case,
                    "slot": slot,
                    "category": row["perturbation_id"],
                    "expected_grounding": row["grounding.score"],
                    "selection_reason": (
                        f"Match {slot}; prefer {sorted(preferred)}; tie-break by variant ID."
                    ),
                    "coverage_gap": gap,
                }
            )
    if len({r["sample_id"] for r in selected}) != 24:
        raise ValueError("Panel requires 24 distinct saved-answer identities")
    return selected


def freeze_panel(
    subsets_path: Path, result_path: Path, release_path: Path, output: Path
) -> dict[str, Any]:
    """Verify upstream seals, freeze grounding packets and keep expectations restricted."""
    subsets, result, release = _read(subsets_path), _read(result_path), _read(release_path)
    if (
        tuple(subsets["panels"]["dev3"]["case_ids"]) != DEV3
        or tuple(subsets["panels"]["dev6"]["case_ids"]) != DEV6
    ):
        raise ValueError("Fixed question panel changed")
    bound_result = verify_binding(subsets["bindings"]["task09a_result"], Path.cwd())
    if result_path.read_bytes() != bound_result.read_bytes():
        raise ValueError("Source result differs from fixed subset binding")
    if result.get("status") != "complete_with_limitations" or release.get("status") != "complete":
        raise ValueError("Require accepted upstream releases")
    root = Path(result["namespace"]).resolve()
    completion_path = verify_binding(result["batch_completion"], root)
    batch = completion_path.parent
    inventory = _inventory(_read(completion_path)["inventory"]["files"])

    def artifact(name: str) -> Path:
        """Require both pointer and sealed inventory agreement before reading."""
        path = verify_binding(result["artifacts"][name], root)
        verify_binding(inventory[path.relative_to(batch).as_posix()], batch)
        return path

    reservation_path = artifact("reservation.json")
    bound_reservation = verify_binding(subsets["bindings"]["reservation"], root)
    if reservation_path.read_bytes() != bound_reservation.read_bytes():
        raise ValueError("Reservation differs from fixed subset binding")
    reservation = _read(reservation_path)
    groups = [
        reservation[k]
        for k in ("development_variant_ids", "final_check_variant_ids", "excluded_variant_ids")
    ]
    if [len(g) for g in groups] != [423, 118, 5] or len(set(sum(groups, []))) != 546:
        raise ValueError("Frozen variant populations differ")
    release_root, release_inventory, dev, allowed_sources, corpus_path = _verify_release(release)
    prepared = _read(verify_binding(inventory["prepared.json"], batch))
    if set(prepared["case_ids"]) != set(dev) or not set(DEV6) <= set(dev):
        raise ValueError("Prepared development membership differs")
    expectations_path, answers_path = artifact("expectations.jsonl"), artifact("answers.jsonl")
    selections = choose_samples(selection_metadata(expectations_path, set(groups[0])))
    variant_ids = {row["sample_id"] for row in selections if row["slot"] != "control"}
    variants, expectations = (
        selected_rows(answers_path, variant_ids),
        selected_rows(expectations_path, variant_ids),
    )
    controls = selected_rows(artifact("controls.jsonl"), {f"{case}-CONTROL" for case in DEV6})
    packets, restricted = [], []
    for row in selections:
        case, key = row["case_id"], row["sample_id"]
        variant = variants.get(key)
        if variant is not None and (
            variant["case_id"] != case or expectations[key]["case_id"] != case
        ):
            raise ValueError("Answer and expectation case mismatch")
        source_path = verify_binding(inventory[f"cases/{case}/input.json"], batch)
        source = _load_case_input(
            source_path,
            case=case,
            release_id=release["release_id"],
            release_root=release_root,
            release_inventory=release_inventory,
            allowed_sources=allowed_sources,
            variant=variant,
        )
        answer = source["reference_answer"] if variant is None else variant["answer"]
        if variant is None and controls[key]["answer"] != answer:
            raise ValueError("Control differs from approved upstream projection")
        packet = build_packet(source, answer, "grounding")
        packet["id"] = key
        packets.append(packet)
        expectation = expectations.get(
            key, {"case_id": case, "grounding": {"score": 2}, "basis": "unchanged approved control"}
        )
        restricted.append({"sample_id": key, "expectation": expectation})
        row.update(
            {
                "source_input": _binding(source_path),
                "source_packet_sha256": source["source_packet_sha256"],
                "answer_sha256": stable_json_sha256(answer),
                "payload_sha256": stable_json_sha256(packet["payload"]),
                "packet_sha256": stable_json_sha256(packet),
                "expectation_sha256": stable_json_sha256(expectation),
            }
        )
    for case in DEV6:
        if len({r["answer_sha256"] for r in selections if r["case_id"] == case}) != 4:
            raise ValueError(f"Four distinct answer contents required for {case}")
    files = {
        "packets.json": json_bytes(packets),
        "restricted_expectations.json": json_bytes(restricted),
    }
    manifest = {
        "schema_version": "task09e.grounding_panel.v1",
        "status": "frozen",
        "subsets": _binding(subsets_path),
        "source_result": _binding(result_path),
        "release_result": _binding(release_path),
        "reservation": _binding(reservation_path),
        "corpus_manifest": _binding(corpus_path),
        "answers": _binding(answers_path),
        "expectations": _binding(expectations_path),
        "panels": {
            name: [r["sample_id"] for r in selections if r["case_id"] in cases]
            for name, cases in (("dev3", DEV3), ("dev6", DEV6))
        },
        "samples": selections,
        "artifacts": {
            name: _planned_binding(output / name, content) for name, content in files.items()
        },
        "frozen_populations": subsets["frozen_populations"],
        "inference_calls": 0,
        "reserved_answer_payloads_decoded": False,
        "test_content_decoded": False,
        "limitations": [
            "Synthetic expectations are diagnostic proposals, not calibrated accuracy.",
            "Purposive tuning panel; no statistical representativeness.",
            "Only selected eligible answer rows decoded; "
            "six-case eligible expectation metadata streamed.",
        ],
    }
    files["manifest.json"] = json_bytes(manifest)
    _publish_output(output, files)
    return manifest


def load_panel_samples(manifest_path: Path, panel: str) -> list[dict[str, Any]]:
    """Load a sealed panel into scorer records; expectations remain outside packets."""
    if panel not in {"dev3", "dev6"}:
        raise ValueError("Only bounded dev3/dev6 panels are supported")
    manifest = _read(manifest_path)
    if (
        manifest.get("schema_version") != "task09e.grounding_panel.v1"
        or manifest.get("status") != "frozen"
    ):
        raise ValueError("Require frozen grounding panel")
    root = manifest_path.parent
    packets_path = verify_binding(manifest["artifacts"]["packets.json"], root)
    expected_path = verify_binding(manifest["artifacts"]["restricted_expectations.json"], root)
    packet_rows = json.loads(packets_path.read_text())
    expectation_rows = json.loads(expected_path.read_text())
    packets = {p["id"]: p for p in packet_rows}
    expected = {r["sample_id"]: r["expectation"] for r in expectation_rows}
    if len(packets) != len(packet_rows) or len(expected) != len(expectation_rows):
        raise ValueError("Duplicate packet or expectation identity")
    rows = manifest["samples"]
    if len(rows) != 24 or len({r["sample_id"] for r in rows}) != 24:
        raise ValueError("Expected 24 distinct frozen samples")
    sample_ids = {r["sample_id"] for r in rows}
    if set(packets) != sample_ids or set(expected) != sample_ids:
        raise ValueError("Packet and expectation populations differ")
    if {r["case_id"] for r in rows} != set(DEV6):
        raise ValueError("Question population differs")
    for case in DEV6:
        case_rows = [r for r in rows if r["case_id"] == case]
        if (
            len(case_rows) != 4
            or len({r["answer_sha256"] for r in case_rows}) != 4
            or {r["slot"] for r in case_rows} != {"control", "grounding_0", "grounding_1", "edge"}
            or any(not r["sample_id"].startswith(f"{case}-") for r in case_rows)
        ):
            raise ValueError("Each question requires four distinct answers and required slots")
    for name, cases in (("dev3", DEV3), ("dev6", DEV6)):
        wanted = [r["sample_id"] for r in rows if r["case_id"] in cases]
        if manifest["panels"][name] != wanted or len(wanted) != len(cases) * 4:
            raise ValueError("Panel membership or nesting differs")
    loaded = []
    for row in rows:
        key = row["sample_id"]
        packet, expectation = packets[key], expected[key]
        if (
            expectation["case_id"] != row["case_id"]
            or stable_json_sha256(packet) != row["packet_sha256"]
            or stable_json_sha256(packet["payload"]) != row["payload_sha256"]
            or stable_json_sha256(expectation) != row["expectation_sha256"]
            or expectation["grounding"]["score"] != row["expected_grounding"]
        ):
            raise ValueError("Frozen packet or expectation identity differs")
        if key in manifest["panels"][panel]:
            loaded.append(
                {
                    "sample_id": key,
                    "case_id": row["case_id"],
                    "scope": "development",
                    "packet": packet,
                    "expected_score": row["expected_grounding"],
                    "category": row["category"],
                    "control": row["slot"] == "control",
                }
            )
    return loaded


def main() -> None:
    """Publish a bounded immutable panel without inference or downloads."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("subsets", "result", "release", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    manifest = freeze_panel(args.subsets, args.result, args.release, args.output)
    logging.basicConfig(level=logging.INFO)
    logging.info("Frozen %d grounding samples at %s", len(manifest["samples"]), args.output)


if __name__ == "__main__":
    main()
