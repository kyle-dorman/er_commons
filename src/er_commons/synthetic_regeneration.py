"""Build fresh development authoring slots without reading prior synthetic payloads.

Only the sealed predecessor's reservation metadata and original authoring inputs
are consumed. Test references and old generated outputs are neither opened nor
hashed. The existing final-check reservation is inherited, never redrawn.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from er_commons.artifact_io import json_bytes, sha256_bytes, sha256_file
from er_commons.synthetic_intake import verify_binding, verify_split
from er_commons.synthetic_records import CATEGORIES

ANNOTATION_VERSION = "task09a2.stage_expectations.v1"
_SLOT = re.compile(r"(C\d{3})-([POFCR]\d{2})-(\d{2})-([0-9a-f]{12})")


def _read(path: Path) -> dict[str, Any]:
    """Read only an explicitly selected, checksum-verified object."""
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"Expected object: {path}")
    return value


def _binding(path: Path) -> dict[str, Any]:
    """Bind the exact file used, with an absolute path for restart checks."""
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
    }


def _inventory(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index metadata without opening any inventory member."""
    result = {row["path"]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate completion inventory path")
    return result


def development_slots(reservation: dict[str, Any], dev: list[str]) -> dict[str, dict[str, str]]:
    """Derive exactly 423 case/category slots from development IDs alone."""
    keys = ("development_variant_ids", "final_check_variant_ids", "excluded_variant_ids")
    partitions = [reservation[key] for key in keys]
    if [len(values) for values in partitions] != [423, 118, 5]:
        raise ValueError("Predecessor reservation must retain 423/118/5 membership")
    flat = [value for values in partitions for value in values]
    if len(set(flat)) != 546:
        raise ValueError("Predecessor reservation contains duplicate or overlapping IDs")
    slots: dict[str, dict[str, str]] = {case_id: {} for case_id in dev}
    for variant_id in partitions[0]:
        match = _SLOT.fullmatch(variant_id)
        if match is None or match[1] not in slots or match[2] not in CATEGORIES:
            raise ValueError(f"Invalid development slot identity: {variant_id}")
        case_id, category = match[1], match[2]
        if category in slots[case_id]:
            raise ValueError(
                f"Duplicate case/category requires an explicit slot map: {case_id}/{category}"
            )
        slots[case_id][category] = variant_id
    if any(not categories for categories in slots.values()):
        raise ValueError("Development slots do not cover all 19 cases")
    return slots


def prepare_regeneration(pointer: Path, data_root: Path) -> dict[str, Any]:
    """Reconstruct fresh source-only packets from pinned predecessor input bytes.

    Do not run the old intake/publication verifier: those walk files outside this
    task's read boundary. Verify only the metadata and development inputs used.
    """
    prior = _read(pointer)
    if prior.get("status") not in {"complete", "complete_with_limitations"}:
        raise ValueError("Predecessor pointer is incomplete")
    completion_path = verify_binding(prior["batch_completion"], data_root)
    batch_root = completion_path.parent
    inventory = _inventory(_read(completion_path)["inventory"]["files"])
    bindings = {
        "predecessor_pointer": _binding(pointer),
        "predecessor_completion": _binding(completion_path),
    }

    def prior_input(relative: str) -> Path:
        """Verify only the explicitly requested predecessor member."""
        path = verify_binding(inventory[relative], batch_root)
        bindings[f"predecessor:{relative}"] = _binding(path)
        return path

    reservation_path = prior_input("published/reservation.json")
    if verify_binding(prior["artifacts"]["reservation.json"], data_root) != reservation_path:
        raise ValueError("Reservation pointer and completion disagree")
    reservation = _read(reservation_path)
    intake = _read(prior_input("intake.json"))
    upstream = intake["source_bindings"]
    # The frozen pointer is small metadata in the repository, outside data_root.
    release_pointer_path = Path(upstream["pointer"]["path"])
    verify_binding(upstream["pointer"], release_pointer_path.parent)
    bindings["release_pointer"] = _binding(release_pointer_path)
    release = _read(release_pointer_path)
    if release.get("status") != "complete" or release["release_id"] != intake["release_id"]:
        raise ValueError("Frozen release identity differs")
    release_completion_path = verify_binding(release["completion"], data_root)
    release_root = release_completion_path.parent
    release_completion = _read(release_completion_path)
    if release_completion.get("status") != "complete":
        raise ValueError("Frozen release completion is incomplete")
    released = _inventory(release_completion["inventory"])
    bindings["release_completion"] = _binding(release_completion_path)
    split_path = verify_binding(release["approved_split"], data_root)
    if verify_binding(upstream["split"], data_root) != split_path:
        raise ValueError("Frozen split binding differs")
    bindings["split"] = _binding(split_path)
    dev, _test = verify_split(_read(split_path))
    if intake["dev_case_ids"] != dev or [row["case_id"] for row in intake["cases"]] != dev:
        raise ValueError("Predecessor intake membership differs from frozen development split")
    slots = development_slots(reservation, dev)
    corpus_path = verify_binding(intake["corpus_manifest_binding"], data_root)
    corpus_relative = corpus_path.relative_to(release_root).as_posix()
    if verify_binding(released[corpus_relative], release_root) != corpus_path:
        raise ValueError("Corpus is absent from frozen release")
    bindings["corpus"] = _binding(corpus_path)
    corpus = _read(corpus_path)
    allowed = {row["source_id"]: row["extraction_id"] for row in corpus["documents"]}
    packets = []
    for original in intake["cases"]:
        case_id = original["case_id"]
        packet = _read(prior_input(f"cases/{case_id}/input.json"))
        packet.pop("requested_categories", None)
        if packet != original:
            raise ValueError(f"Sealed input differs from source-only intake: {case_id}")
        reference = released[f"curator/cases/{case_id}.json"]
        reference_path = verify_binding(reference, release_root)
        if verify_binding(packet["reference_binding"], data_root) != reference_path:
            raise ValueError(f"Development reference binding differs: {case_id}")
        bindings[f"reference:{case_id}"] = _binding(reference_path)
        if packet["release_id"] != release["release_id"]:
            raise ValueError(f"Packet release identity differs: {case_id}")
        if sha256_bytes(json_bytes(packet["sources"])) != packet["source_packet_sha256"]:
            raise ValueError(f"Source packet digest differs: {case_id}")
        for source in packet["sources"]:
            if (
                source["source_id"] not in allowed
                or allowed[source["source_id"]] != source["extraction_id"]
            ):
                raise ValueError(f"Source is outside frozen corpus: {case_id}")
        packet["annotation_version"] = ANNOTATION_VERSION
        packet["regeneration_slots"] = slots[case_id]
        packet["requested_categories"] = sorted(slots[case_id])
        packets.append(packet)
    return {
        "schema_version": "task09a2.intake.v1",
        "annotation_version": ANNOTATION_VERSION,
        "release_id": intake["release_id"],
        "dev_case_ids": dev,
        "cases": packets,
        "restricted_controls": copy.deepcopy(intake["restricted_controls"]),
        "corpus_manifest_binding": bindings["corpus"],
        "source_bindings": bindings,
        "limitations": copy.deepcopy(intake["limitations"]),
        "regeneration": {
            "predecessor_reservation": _binding(reservation_path),
            "development_slot_ids": reservation["development_variant_ids"],
            "preserved_final_check_variant_ids": reservation["final_check_variant_ids"],
            "preserved_excluded_variant_ids": reservation["excluded_variant_ids"],
        },
        "verification": {
            "development_count": 19,
            "development_slot_count": 423,
            "test_content_read": False,
            "predecessor_synthetic_payloads_read": False,
            "reservation_redrawn": False,
            "scope": (
                "Only pinned metadata, original authoring inputs and "
                "development reference bytes verified"
            ),
        },
    }
