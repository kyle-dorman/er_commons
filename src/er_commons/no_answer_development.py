"""Sealed A-only full-development candidates; proposal labels are not calibration gold."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from er_commons import no_answer as core

COMPLETION_SHA256 = "0bfe0c71d6da9eccb39eb19e5e01842adca686fe76b8aeca3460486414dc73ea"
EXPECTED_COUNTS = {"clean_abstention": 97, "substantive": 175, "ambiguous": 38}
DEVELOPMENT_QUESTIONS = frozenset(
    (
        "C001 C006 C007 C008 C014 C017 C019 C027 C028 C029 "
        "C036 C037 C041 C042 C045 C050 C051 C054 C056"
    ).split()
)


def _rows(raw: bytes) -> list[dict[str, Any]]:
    """Read sealed JSONL objects without accepting duplicate JSON keys."""
    rows = [json.loads(line, object_pairs_hook=core._unique_object) for line in raw.splitlines()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("A development JSONL records must be objects")
    return rows


def _assemble(
    index: list[dict[str, Any]],
    label_rows: list[dict[str, Any]],
    inventory: dict[str, dict[str, Any]],
    root: Path,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Join exact identities and verify each selected conclusion before model projection."""
    labels_by_id = {row["candidate_id"]: row for row in label_rows}
    if len(labels_by_id) != len(label_rows):
        raise ValueError("Duplicate A development label ID")
    samples: list[dict[str, Any]] = []
    labels: dict[str, str] = {}
    payload_hashes: set[str] = set()
    for row in index:
        candidate_id = row["candidate_id"]
        if candidate_id in labels or candidate_id not in labels_by_id:
            raise ValueError("Duplicate or missing A development candidate label")
        if row["case_id"] not in DEVELOPMENT_QUESTIONS:
            raise ValueError("Non-development A question")
        label_record = labels_by_id[candidate_id]
        label = label_record["proposed_label"]
        if label not in core.CLASSIFICATIONS:
            raise ValueError("Invalid A development proposed label")
        payload_path = Path(row["payload_path"])
        if payload_path.parts != ("payloads", f"{candidate_id}.json"):
            raise ValueError("Unexpected A development payload path")
        binding = inventory[str(payload_path)]
        packet = core.validate_input(
            json.loads(core._read_bound(binding, root), object_pairs_hook=core._unique_object)
        )
        canonical = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        payload_hash = hashlib.sha256(canonical.encode()).hexdigest()
        if payload_hash != row["payload_sha256"] or payload_hash in payload_hashes:
            raise ValueError("A development canonical payload hash mismatch or duplicate")
        if (
            hashlib.sha256(packet["candidate_conclusion"].encode()).hexdigest()
            != row["conclusion_sha256"]
        ):
            raise ValueError("A development conclusion hash mismatch")
        payload_hashes.add(payload_hash)
        labels[candidate_id] = label
        samples.append(
            {
                "sample_id": candidate_id,
                "case_id": row["case_id"],
                "packet": packet,
                "payload_sha256": payload_hash,
                "payload_file_sha256": binding["sha256"],
                "conclusion_sha256": row["conclusion_sha256"],
                "candidate_record": row,
                "label_record": label_record,
                "label_uncertain": bool(
                    label_record.get("author_uncertainty")
                    or label_record.get("reviewer_uncertainty")
                ),
            }
        )
    if set(labels) != set(labels_by_id):
        raise ValueError("A development label and candidate identities differ")
    return samples, labels


def load_full_development(
    pointer_path: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, Any]]:
    """Load all 310 sealed development proposals, retaining all 33 uncertain records."""
    pointer_path = (
        pointer_path or core.REPO / "docs/specs/task09f1_no_answer_candidates_v1_result.json"
    )
    pointer = json.loads(pointer_path.read_text())
    if pointer["completion"]["sha256"] != COMPLETION_SHA256:
        raise ValueError("A development completion differs from pinned publication")
    completion = json.loads(core._read_bound(pointer["completion"]))
    if completion["dataset_id"] != "09f1_a_candidates_20261016_v1":
        raise ValueError("Unexpected A development dataset")
    root = Path(pointer["artifact_root"])
    inventory = {item["path"]: item for item in completion["inventory"]}
    if len(inventory) != len(completion["inventory"]):
        raise ValueError("Duplicate A development inventory path")
    index = _rows(core._read_bound(inventory["candidate_index.jsonl"], root))
    label_rows = _rows(core._read_bound(inventory["labels.jsonl"], root))
    samples, labels = _assemble(index, label_rows, inventory, root)
    uncertain = sum(sample["label_uncertain"] for sample in samples)
    if len(samples) != 310 or Counter(labels.values()) != EXPECTED_COUNTS:
        raise ValueError("A development publication counts differ")
    if {sample["case_id"] for sample in samples} != DEVELOPMENT_QUESTIONS or uncertain != 33:
        raise ValueError("A development coverage or uncertainty counts differ")
    provenance = {
        "dataset_id": completion["dataset_id"],
        "completion_sha256": COMPLETION_SHA256,
        "release_id": completion["release_id"],
        "label_status": "agent_reviewed_proposals_not_human_gold",
        "counts": dict(EXPECTED_COUNTS),
        "candidate_count": len(samples),
        "question_count": len(DEVELOPMENT_QUESTIONS),
        "uncertain_label_count": uncertain,
        "exclusions": [],
        "policy_version": core.POLICY_VERSION,
        "contract_version": core.CONTRACT_VERSION,
    }
    return samples, labels, provenance
