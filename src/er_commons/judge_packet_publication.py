"""Publish explicitly selected development judge inputs without inference."""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from er_commons.artifact_io import (
    file_reference,
    json_bytes,
    publish_bytes_no_clobber,
    sha256_bytes,
    stable_json_sha256,
)
from er_commons.judge_packets import build_packet
from er_commons.judge_qualification_packets import selected_rows
from er_commons.synthetic_intake import verify_binding, verify_split


def _read(path: Path) -> dict[str, Any]:
    """Decode only verified, authorized object content."""
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"Expected object: {path}")
    return value


def _binding(path: Path) -> dict[str, Any]:
    """Bind exact bytes for the external manifest, never the model input."""
    return {**file_reference(path, root=path.parent), "path": str(path.resolve())}


def _inventory(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Reject ambiguous sealed file identities."""
    result = {row["path"]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate inventory path")
    return result


def _verify_release(
    release: dict[str, Any],
) -> tuple[Path, dict[str, dict[str, Any]], list[str], dict[str, str], Path]:
    """Verify the frozen split and corpus without decoding test cases or references."""
    release_root = Path(release["completion"]["path"]).resolve().parent
    release_completion = _read(verify_binding(release["completion"], release_root))
    if release_completion.get("status") != "complete":
        raise ValueError("Release completion is incomplete")
    release_inventory = _inventory(release_completion["inventory"])
    split_path = verify_binding(release["approved_split"], release_root)
    verify_binding(release_inventory[split_path.relative_to(release_root).as_posix()], release_root)
    dev, _ = verify_split(_read(split_path))
    handoff_path = verify_binding(release["handoff"], release_root)
    verify_binding(
        release_inventory[handoff_path.relative_to(release_root).as_posix()], release_root
    )
    handoff = _read(handoff_path)
    if handoff["release_id"] != release["release_id"]:
        raise ValueError("Release handoff identity differs")
    corpus_path = verify_binding(handoff["artifacts"]["corpus"], release_root)
    verify_binding(
        release_inventory[corpus_path.relative_to(release_root).as_posix()], release_root
    )
    documents = _read(corpus_path)["documents"]
    allowed_sources = {row["source_id"]: row["extraction_id"] for row in documents}
    if len(allowed_sources) != len(documents):
        raise ValueError("Duplicate source identity in frozen corpus")
    return release_root, release_inventory, dev, allowed_sources, corpus_path


def _load_selected_variants(
    artifact: Callable[[str], Path], variant_ids: list[str], dev: list[str]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Gate eligibility before loading explicitly selected development answers."""
    variants: dict[str, dict[str, Any]] = {}
    input_bindings = []
    if variant_ids:
        expectations_path = artifact("expectations.jsonl")
        expectations = selected_rows(expectations_path, set(variant_ids))
        if any(row.get("comparison_eligible") is not True for row in expectations.values()):
            raise ValueError("Selected development variant is a comparison exclusion")
        answers_path = artifact("answers.jsonl")
        variants = selected_rows(answers_path, set(variant_ids))
        if any(row["case_id"] not in dev for row in variants.values()):
            raise ValueError("Variant case is outside development split")
        if any(expectations[key]["case_id"] != row["case_id"] for key, row in variants.items()):
            raise ValueError("Selected answer and eligibility case differ")
        input_bindings = [_binding(answers_path), _binding(expectations_path)]

    return variants, input_bindings


def _load_case_input(
    packet_path: Path,
    *,
    case: str,
    release_id: str,
    release_root: Path,
    release_inventory: dict[str, dict[str, Any]],
    allowed_sources: dict[str, str],
    variant: dict[str, Any] | None,
) -> dict[str, Any]:
    """Verify the selected case, corpus membership and exact variant/reference bindings."""
    source = _read(packet_path)
    if source["case_id"] != case or source["release_id"] != release_id:
        raise ValueError("Case or release identity differs")
    if sha256_bytes(json_bytes(source["sources"])) != source["source_packet_sha256"]:
        raise ValueError("Source packet binding differs")
    for evidence in source["sources"]:
        if (
            evidence["source_id"] not in allowed_sources
            or evidence["extraction_id"] != allowed_sources[evidence["source_id"]]
        ):
            raise ValueError("Evidence source is outside the frozen allowed corpus")
    reference_path = verify_binding(source["reference_binding"], release_root)
    verify_binding(
        release_inventory[reference_path.relative_to(release_root).as_posix()], release_root
    )
    # The sealed 09A input already contains the approved reference projection.
    # Verify the exact original bytes without decoding any other release reference.
    if variant is not None:
        if (
            variant["source_packet_hash"] != source["source_packet_sha256"]
            or variant["parent_reference_hash"]
            != sha256_bytes(json_bytes(source["reference_answer"])[:-1])
            or variant["release_id"] != source["release_id"]
            or variant["reference_binding"] != source["reference_binding"]
            or variant["reference_version"] != source["reference_version"]
        ):
            raise ValueError("Variant source/reference binding differs")
    return source


def _planned_binding(path: Path, content: bytes) -> dict[str, Any]:
    """Describe planned bytes identically to a published file binding."""
    return {"path": str(path.resolve()), "sha256": sha256_bytes(content), "byte_size": len(content)}


def _publish_output(output: Path, files: dict[str, bytes]) -> None:
    """Preflight the entire output before writing; accept exact partial publication."""
    if output.exists():
        unexpected = sorted(path.name for path in output.iterdir() if path.name not in files)
        if unexpected:
            raise FileExistsError(f"Unexpected files in packet output: {unexpected}")
        for name, content in files.items():
            path = output / name
            if path.is_symlink() or (
                path.exists() and (not path.is_file() or path.read_bytes() != content)
            ):
                raise FileExistsError(f"refusing to overwrite changed file: {path}")
    for name, content in files.items():
        publish_bytes_no_clobber(output / name, content)


def prepare_packets(
    result_path: Path,
    release_path: Path,
    output: Path,
    *,
    variant_ids: list[str],
    control_cases: list[str],
) -> dict[str, Any]:
    """Build both dimensions for explicit selections, preserving frozen populations."""
    if not variant_ids and not control_cases:
        raise ValueError("Select explicit development variants or control cases")
    if len(set(variant_ids)) != len(variant_ids) or len(set(control_cases)) != len(control_cases):
        raise ValueError("Duplicate selections")
    result, release = _read(result_path), _read(release_path)
    if result.get("status") != "complete_with_limitations" or release.get("status") != "complete":
        raise ValueError("Require completed 09A and 08H handoffs")
    root = Path(result["namespace"]).resolve()
    completion_path = verify_binding(result["batch_completion"], root)
    batch = completion_path.parent
    inventory = _inventory(_read(completion_path)["inventory"]["files"])

    def artifact(name: str) -> Path:
        """Require agreement between the result pointer and sealed batch inventory."""
        path = verify_binding(result["artifacts"][name], root)
        relative = path.relative_to(batch).as_posix()
        verify_binding(inventory[relative], batch)
        return path

    reservation_path = artifact("reservation.json")
    reservation = _read(reservation_path)
    groups = [
        reservation[k]
        for k in ("development_variant_ids", "final_check_variant_ids", "excluded_variant_ids")
    ]
    if [len(g) for g in groups] != [423, 118, 5] or len(set(sum(groups, []))) != 546:
        raise ValueError("Frozen reservation populations differ")
    if not set(variant_ids) <= set(groups[0]):
        raise ValueError("Only development variants may be selected")

    release_root, release_inventory, dev, allowed_sources, corpus_path = _verify_release(release)
    prepared = _read(verify_binding(inventory["prepared.json"], batch))
    if len(prepared["case_ids"]) != 19 or set(prepared["case_ids"]) != set(dev):
        raise ValueError("Prepared intake differs from frozen development split")
    if not set(control_cases) <= set(dev):
        raise ValueError("Control cases must belong to development split")

    variants, input_bindings = _load_selected_variants(artifact, variant_ids, dev)

    selections: list[tuple[str, str, dict[str, Any] | None]] = [
        (key, variants[key]["case_id"], variants[key]) for key in sorted(variants)
    ]
    selections += [(f"{case}-CONTROL", case, None) for case in sorted(control_cases)]
    packets: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    for selection, case, variant in selections:
        packet_path = verify_binding(inventory[f"cases/{case}/input.json"], batch)
        source = _load_case_input(
            packet_path,
            case=case,
            release_id=release["release_id"],
            release_root=release_root,
            release_inventory=release_inventory,
            allowed_sources=allowed_sources,
            variant=variant,
        )
        answer = source["reference_answer"] if variant is None else variant["answer"]
        for dimension in ("grounding", "adequacy"):
            packet = build_packet(source, answer, dimension)
            packet["id"] = f"p{len(packets) + 1:04d}"
            packets.append(packet)
            provenance.append(
                {
                    "id": packet["id"],
                    "selection": selection,
                    "case_id": case,
                    "input": _binding(packet_path),
                    "answer_sha256": stable_json_sha256(answer),
                    "payload_sha256": stable_json_sha256(packet["payload"]),
                }
            )
    packet_bytes, provenance_bytes = json_bytes(packets), json_bytes(provenance)
    manifest = {
        "schema_version": "task09c.packet_publication.v1",
        "packet_count": len(packets),
        "packets": _planned_binding(output / "packets.json", packet_bytes),
        "provenance": _planned_binding(output / "provenance.json", provenance_bytes),
        "source_result": _binding(result_path),
        "release_result": _binding(release_path),
        "reservation": _binding(reservation_path),
        "corpus_manifest": _binding(corpus_path),
        "selected_record_files": input_bindings,
        "development_variants": 423,
        "reserved_final_checks": 118,
        "exclusions": 5,
        "development_cases": 19,
        "test_cases": 30,
        "reserved_answer_payloads_parsed": False,
        "test_content_parsed": False,
        "inference_calls": 0,
    }
    _publish_output(
        output,
        {
            "packets.json": packet_bytes,
            "provenance.json": provenance_bytes,
            "completion.json": json_bytes(manifest),
        },
    )
    return manifest


def main() -> None:
    """Prepare a bounded explicitly named set of judge packets without model calls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant-id", action="append", default=[])
    parser.add_argument("--control-case", action="append", default=[])
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    manifest = prepare_packets(
        args.result,
        args.release,
        args.output,
        variant_ids=args.variant_id,
        control_cases=args.control_case,
    )
    logging.info("Prepared judge packets: %s", json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
