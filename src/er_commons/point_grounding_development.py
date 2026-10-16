"""Load the sealed G development pool; proposed labels never enter model packets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from er_commons import point_grounding as core
from er_commons import point_grounding_panel as panel

POOL_POINTER = panel.REPO / "docs/specs/task09f1_grounding_candidates_v2_result.json"
LOCKED_COMPLETION_SHA256 = "49e5cf7fc1349c1563bcfc535540f6601c45f3e0176540f1bc6fd0075941aee8"
UNRESOLVED_IDS = frozenset({"G-C001-032", "G-C017-033", "G-C028-017", "G-C036-022"})


def _digest(value: Any) -> str:
    """Match the publication's canonical JSON digest for owned evidence."""
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load_development(
    pointer_path: Path = POOL_POINTER,
) -> tuple[list[dict[str, Any]], dict[str, bool], dict[str, Any]]:
    """Verify frozen identities, reviews and payloads, then exclude four null labels.

    The completion seal anchors reviewed source fidelity without reopening corpus or
    held-out content. Calibration overlap is checked against its independent seal.
    """
    pointer = json.loads(pointer_path.read_text())
    if pointer["status"] != "complete" or pointer["release_id"] != "task09f_20261014_v2":
        raise ValueError("Unexpected G development publication")
    root = Path(pointer["artifact_root"])
    completion = json.loads(
        panel._checked_bytes(panel._panel_path(root, "completion.json"), LOCKED_COMPLETION_SHA256)
    )
    if (
        completion["status"] != "complete"
        or completion["release_id"] != pointer["release_id"]
        or set(completion["development_ids"]) != panel.DEVELOPMENT_CASES
    ):
        raise ValueError("G development completion scope mismatch")
    inventory = {row["path"]: row for row in completion["inventory"]}
    if len(inventory) != len(completion["inventory"]):
        raise ValueError("Duplicate G development inventory identity")

    def read(relative: str) -> bytes:
        """Require every consumed artifact to match the pinned completion inventory."""
        record = inventory[relative]
        return panel._checked_bytes(
            panel._panel_path(root, relative), record["sha256"], record["byte_size"]
        )

    validation = json.loads(read("validation.json"))
    if (
        validation["status"] != "passed"
        or validation["errors"]
        or any(
            validation[key] is not True
            for key in (
                "development_only",
                "source_fidelity_and_ownership",
                "label_separation",
                "original_reference_hashes_verified",
                "no_test_or_reserved_case_content_loaded",
            )
        )
    ):
        raise ValueError("G development publication validation failed")
    inputs = panel._unique_rows(read("candidates.jsonl"))
    reviews = panel._unique_rows(read("labels_reviews.jsonl"))
    if len(inputs) != 615 or set(inputs) != set(reviews):
        raise ValueError("G development must contain 615 unique reviewed candidates")
    if {row["case_id"] for row in inputs.values()} != panel.DEVELOPMENT_CASES:
        raise ValueError("G development question scope mismatch")
    calibration, calibration_labels, calibration_provenance = panel.load_panel()
    calibration_by_id = {row["sample_id"]: row for row in calibration}
    samples: list[dict[str, Any]] = []
    labels: dict[str, bool] = {}
    exclusions = []
    for sample_id, row in inputs.items():
        case_id = row["case_id"]
        if not sample_id.startswith(f"G-{case_id}-"):
            raise ValueError("G development candidate/question identity mismatch")
        label = reviews[sample_id]
        review = label["review"]
        expected = label["proposed_supported"]
        if (
            review["candidate_id"] != sample_id
            or review["author"] == review["reviewer"]
            or label["author_proposed_supported"] is not expected
            or review["reviewed_supported"] is not expected
            or label["human_approved"] is not False
        ):
            raise ValueError("G development independent review mismatch")
        if expected is None:
            if (
                sample_id not in UNRESOLVED_IDS
                or review["disposition"] != "unresolved"
                or (row["eligible_for_future_calibration"] is not False)
            ):
                raise ValueError("Unexpected unresolved G development candidate")
            exclusions.append({"sample_id": sample_id, "reason": review["rationale"]})
            continue
        if (
            type(expected) is not bool
            or review["disposition"] != "agree"
            or (row["eligible_for_future_calibration"] is not True)
        ):
            raise ValueError("G development binary label must be independently agreed")
        relative = f"payloads/{sample_id}.json"
        if row["payload_path"] != relative:
            raise ValueError("G development payload identity mismatch")
        data = read(relative)
        digest = hashlib.sha256(data).hexdigest()
        packet = core.validate_input(json.loads(data), citation_ids=row["citation_ids"])
        if (
            digest != row["payload_sha256"]
            or _digest(packet["evidence"]) != row["evidence_sha256"]
            or hashlib.sha256(packet["point_text"].encode()).hexdigest() != row["point_text_sha256"]
        ):
            raise ValueError("G development owned payload fidelity mismatch")
        if sample_id in calibration_by_id and (
            packet != calibration_by_id[sample_id]["packet"]
            or expected is not calibration_labels[sample_id]
        ):
            raise ValueError("G development calibration overlap mismatch")
        labels[sample_id] = expected
        samples.append(
            {
                "sample_id": sample_id,
                "case_id": case_id,
                "packet": packet,
                "metadata": {
                    "payload_sha256": digest,
                    "point_text_sha256": row["point_text_sha256"],
                    "evidence_sha256": row["evidence_sha256"],
                    "owned_citation_ids": row["citation_ids"],
                    "applicability": "known_applicable",
                    "mechanisms": row["mechanisms"],
                    "role": row["role"],
                    "calibration_overlap": sample_id in calibration_by_id,
                },
            }
        )
    if (
        len(samples) != 611
        or sum(labels.values()) != 247
        or {row["sample_id"] for row in exclusions} != UNRESOLVED_IDS
        or not set(calibration_by_id).issubset(labels)
        or len(calibration_by_id) != 36
    ):
        raise ValueError("G development eligible counts or calibration overlap mismatch")
    return (
        samples,
        labels,
        {
            "release_id": pointer["release_id"],
            "scope": "full_611_point_development_comparison",
            "completion_sha256": LOCKED_COMPLETION_SHA256,
            "label_status": "independently_reviewed_agent_proposals_not_human_gold",
            "ownership_fidelity": "verified_against_sealed_reviewed_payloads",
            "published_candidates": 615,
            "eligible_candidates": 611,
            "supported": 247,
            "unsupported": 364,
            "excluded_unresolved": exclusions,
            "calibration_overlap_count": 36,
            "calibration_overlap_ids": sorted(calibration_by_id),
            "calibration_provenance": calibration_provenance,
        },
    )
