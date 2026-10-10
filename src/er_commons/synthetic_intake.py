"""Verified development-only intake for Task 09A synthetic authoring.

Release-wide bytes are audited, but only development reference contents are
parsed. Historical answer metadata stays in restricted controls, never packets.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from er_commons.artifact_io import json_bytes, sha256_bytes, sha256_file

ANSWER_FIELDS = (
    "conclusion",
    "supporting_points",
    "qualifications",
    "optional_context",
    "citation_locators",
)
SOURCE_FIELDS = (
    "occurrence_id",
    "source_id",
    "edition",
    "canonical_target",
    "full_source_text",
    "tables",
    "anchors",
    "excerpt",
    "role",
    "approved_roles",
    "limitations",
    "physical_pages",
    "printed_labels",
    "title",
    "source_url",
    "pdf_url",
    "source_sha256",
    "source_manifest",
    "extraction_id",
)


def _read(path: Path) -> dict[str, Any]:
    """Parse an object only after its caller has established authorization."""
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def verify_binding(binding: dict[str, Any], root: Path) -> Path:
    """Require a contained regular file with the exact recorded bytes."""
    path = (root / str(binding["path"])).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Absent or escaping bound path: {path}")
    if "byte_size" in binding and path.stat().st_size != binding["byte_size"]:
        raise ValueError(f"Bound size changed: {path}")
    if sha256_file(path) != binding["sha256"]:
        raise ValueError(f"Bound checksum changed: {path}")
    return path


def verify_split(split: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Validate frozen membership from metadata without test-content access."""
    dev, test = split["dev"], split["test"]
    if len(dev) != 19 or len(test) != 30 or len(set(dev)) != 19 or len(set(test)) != 30:
        raise ValueError("Expected exactly 19 unique dev and 30 unique test IDs")
    if set(dev) & set(test):
        raise ValueError("Development and test membership overlap")
    if split.get("status") != "approved":
        raise ValueError("Split is not approved")
    return dev, test


def project_answer(answer: dict[str, Any]) -> dict[str, Any]:
    """Copy exact substantive fields; mark status without claiming new approval."""
    return {"status": "answered", **{key: copy.deepcopy(answer[key]) for key in ANSWER_FIELDS}}


def _source_packet(
    sources: list[dict[str, Any]], allowed: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Allow only release corpus evidence, retaining full text and table context."""
    projected = []
    for source in sources:
        document = allowed.get(source["source_id"])
        if document is None or document["extraction_id"] != source["extraction_id"]:
            raise ValueError("Citation is outside the frozen allowed corpus")
        if not source.get("full_source_text"):
            raise ValueError("Citation lacks full canonical source text")
        row = {key: copy.deepcopy(source[key]) for key in SOURCE_FIELDS if key in source}
        row["corpus_eligibility"] = copy.deepcopy(document["inherited_eligibility"])
        projected.append(row)
    return projected


def prepare_intake(pointer: Path, data_root: Path) -> dict[str, Any]:
    """Audit the release and assemble source-only packets for its exact 19 dev IDs."""
    result = _read(pointer)
    if result["status"] != "complete":
        raise ValueError("Release pointer is incomplete")
    completion_path = verify_binding(result["completion"], data_root)
    release_root = completion_path.parent
    completion = _read(completion_path)
    if completion["status"] != "complete":
        raise ValueError("Release completion is incomplete")
    inventory = {row["path"]: row for row in completion["inventory"]}
    if len(inventory) != len(completion["inventory"]):
        raise ValueError("Duplicate inventory path")
    actual = {
        p.relative_to(release_root).as_posix() for p in release_root.rglob("*") if p.is_file()
    }
    if actual != set(inventory) | {"completion.json"}:
        raise ValueError("Release managed inventory differs")
    for binding in inventory.values():
        verify_binding(binding, release_root)
    for value in result.values():
        if isinstance(value, dict) and {"path", "sha256"} <= value.keys():
            verify_binding(value, data_root)
    handoff = _read(verify_binding(result["handoff"], data_root))
    if handoff["release_id"] != result["release_id"]:
        raise ValueError("Release identity changed")
    split = _read(verify_binding(result["approved_split"], data_root))
    dev, test = verify_split(split)
    target_path = verify_binding(result["target_dev"], data_root)
    targets = [json.loads(line) for line in target_path.read_text().splitlines() if line.strip()]
    if [row["case_id"] for row in targets] != dev:
        raise ValueError("Development target IDs differ from split metadata")
    corpus_binding = handoff["artifacts"]["corpus"]
    corpus = _read(verify_binding(corpus_binding, data_root))
    allowed = {row["source_id"]: row for row in corpus["documents"]}
    index_path = verify_binding(handoff["artifacts"]["reference_index"], data_root)
    # This index contains identities and citation links, not questions or answers.
    index = [json.loads(line) for line in index_path.read_text().splitlines() if line.strip()]
    if len(index) != 49 or {row["case_id"] for row in index} != set(dev + test):
        raise ValueError("Reference index membership differs")
    dev_index = {row["case_id"]: row for row in index if row["case_id"] in dev}
    cases, controls = [], []
    for target in targets:
        case_id = target["case_id"]
        row = dev_index[case_id]
        if row["split"] != "dev":
            raise ValueError("Test reference rejected by development allowlist")
        relative = row["reference_record"]
        binding = inventory.get(relative)
        if binding is None or binding["sha256"] != row["reference_sha256"]:
            raise ValueError("Reference index binding differs from release inventory")
        reference_path = verify_binding(binding, release_root)
        reference = _read(reference_path)
        if reference["case_id"] != case_id or reference["question"] != target["question"]:
            raise ValueError("Development question or reference ID changed")
        if reference["final_disposition"] != "approved":
            raise ValueError("Reference lacks final approval")
        sources = _source_packet(reference["citation_occurrences"], allowed)
        absolute_binding = {**binding, "path": str(reference_path)}
        packet = {
            "case_id": case_id,
            "question": target["question"],
            "release_id": result["release_id"],
            "reference_version": reference["proposal_version"],
            "reference_binding": absolute_binding,
            "reference_answer": project_answer(reference["answer"]),
            "sources": sources,
            "limitations": handoff["limitations"],
            "normalization": {
                "kind": "exact_substantive_field_projection_not_new_approval",
                "copied_fields": list(ANSWER_FIELDS),
                "added_fields": {"status": "answered"},
                "excluded": "Historical review notes, edit history and curator provenance prose",
            },
        }
        packet["source_packet_sha256"] = sha256_bytes(json_bytes(sources))
        cases.append(packet)
        controls.append(
            {
                "case_id": case_id,
                "exact_reference_answer": reference["answer"],
                "reference_binding": absolute_binding,
                "human_answer_approval": reference["human_answer_approval"],
            }
        )
    return {
        "schema_version": "task09a.intake.v1",
        "release_id": result["release_id"],
        "dev_case_ids": dev,
        "cases": cases,
        "restricted_controls": controls,
        "corpus_manifest_binding": corpus_binding,
        "source_bindings": {
            "pointer": {
                "path": str(pointer.resolve()),
                "sha256": sha256_file(pointer),
                "byte_size": pointer.stat().st_size,
            },
            "completion": result["completion"],
            "split": result["approved_split"],
            **{
                f"release:{relative}": {**binding, "path": str(release_root / relative)}
                for relative, binding in inventory.items()
            },
        },
        "verification": {
            "release_file_count": len(actual),
            "development_count": len(dev),
            "test_metadata_count": len(test),
            "test_content_parsed": False,
            "release_inventory_sha256_verified": True,
            "source_text_basis": "Exact citation packets in checksum-verified approved release",
            "semantic_source_support_verified": False,
        },
        "limitations": handoff["limitations"],
    }
