"""Replay historical Task15 direct-answer v1 synthetics, not structured-C suites."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from er_commons.adequacy_binary import (
    CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION,
    output_json_schema,
    system_prompt,
    validate_input,
)
from er_commons.adequacy_binary_development import DEVELOPMENT_CASE_IDS
from er_commons.artifact_io import file_reference, stable_json_sha256

Partition = Literal["tuning", "audit", "all"]
PARTITION_SEED = "task15-c-synthetic-v1"
ORIGINAL_SIX = frozenset({"C041", "C017", "C019", "C014", "C037", "C056"})


def _read(path: Path) -> Any:
    """Decode one JSON artifact after its binding has been verified."""
    return json.loads(path.read_text())


def _rows(path: Path) -> list[dict[str, Any]]:
    """Preserve the exact JSONL row order used by label/provenance joins."""
    return [json.loads(line) for line in path.read_text().splitlines()]


def _contained(root: Path, relative: str) -> Path:
    """Reject absolute paths, traversal and symlinks before reading bytes."""
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Publication path escapes root")
    selected = root / path
    if not selected.resolve().is_relative_to(root.resolve()):
        raise ValueError("Publication path escapes root")
    if any(part.is_symlink() for part in [selected, *selected.parents] if part != root.parent):
        raise ValueError("Symlinked publication paths are not allowed")
    return selected


def _verify(root: Path, binding: dict[str, Any]) -> Path:
    """Verify an exact relative artifact binding before parsing it."""
    path = _contained(root, binding["path"])
    if file_reference(path, root=root) != binding:
        raise ValueError(f"Publication binding differs: {binding['path']}")
    return path


def load_publication(
    result_path: Path, *, data_root: Path, partition: Partition
) -> tuple[list[dict[str, Any]], dict[str, bool], dict[str, Any]]:
    """Verify the frozen direct-answer v1 suite and select one requested partition.

    The returned packet has exactly C's three fields. Labels, IDs and review data
    remain sidecars. No historical loader, provider, test or reserved payload is read.
    """
    if partition not in {"tuning", "audit", "all"}:
        raise ValueError("Unknown synthetic partition")
    pointer = _read(result_path)
    if pointer["schema_version"] != "task15.c_synthetic_result.v1":
        raise ValueError("Unknown synthetic publication schema")
    relative = pointer["artifact_root_relative"]
    if not relative.startswith("pipelines/brisbane_baylands/task_15/"):
        raise ValueError("Not a Task 15 publication")
    root = _contained(data_root, relative)
    if pointer["completion"]["path"] != "completion.json":
        raise ValueError("Unexpected completion path")
    completion = _read(_verify(root, pointer["completion"]))
    inventory = completion["inventory"]
    paths = [item["path"] for item in inventory]
    if len(set(paths)) != len(paths) or "completion.json" in paths:
        raise ValueError("Duplicate or recursive completion inventory")
    for binding in inventory:
        _verify(root, binding)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if actual != set(paths) | {"completion.json"}:
        raise ValueError("Publication inventory closure differs")
    manifest = _read(root / "manifest.json")
    if (
        completion["dataset_id"] != pointer["dataset_id"]
        or manifest["dataset_id"] != pointer["dataset_id"]
        or manifest["prompt_version"] != CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION
        or manifest["label_status"] != "agent_proposed_independently_reviewed_not_human_gold"
    ):
        raise ValueError("Publication identity or label status differs")
    catalog = _read(root / "catalog.json")
    prompt_identity = _read(root / "prompt/manifest.json")
    version = CONCLUSION_DIRECT_ANSWER_PROMPT_VERSION
    if (
        manifest["policy_sha256"] != hashlib.sha256((root / "policy.md").read_bytes()).hexdigest()
        or manifest["catalog_sha256"]
        != hashlib.sha256((root / "catalog.json").read_bytes()).hexdigest()
        or (root / "prompt/prompt.txt").read_text() != system_prompt("C", prompt_version=version)
        or _read(root / "prompt/schema.json") != output_json_schema("C", prompt_version=version)
        or prompt_identity["prompt_version"] != version
        or prompt_identity["prompt_sha256"]
        != stable_json_sha256(system_prompt("C", prompt_version=version))
        or prompt_identity["schema_sha256"]
        != stable_json_sha256(output_json_schema("C", prompt_version=version))
    ):
        raise ValueError("Policy, catalog or prompt identity differs")
    slots = [row["slot"] for row in catalog["slots"]]
    if len(slots) != 25 or len(set(slots)) != len(slots):
        raise ValueError("Unexpected catalog slots")
    inputs = _rows(root / "authoring_inputs.jsonl")
    references = {row["case_id"]: row for row in inputs}
    if len(inputs) != 19 or set(references) != DEVELOPMENT_CASE_IDS:
        raise ValueError("Development allowlist differs")
    audit = set(catalog["partitions"]["audit"])
    expected_audit = set(
        sorted(
            DEVELOPMENT_CASE_IDS - ORIGINAL_SIX,
            key=lambda case: hashlib.sha256(f"{PARTITION_SEED}:{case}".encode()).hexdigest(),
        )[:4]
    )
    if catalog["partitions"]["seed"] != PARTITION_SEED or audit != expected_audit:
        raise ValueError("Invalid audit grouping")
    bindings = _read(root / "input_bindings.json")["development_only_files_read"]
    binding_map = {row["case_id"]: row for row in bindings}
    if len(bindings) != 19 or set(binding_map) != DEVELOPMENT_CASE_IDS:
        raise ValueError("Source projection bindings differ")
    for case, row in references.items():
        if row["partition"] != ("audit" if case in audit else "tuning"):
            raise ValueError("Question variants cross partitions")
        binding = binding_map[case]
        if (
            hashlib.sha256(row["reference_conclusion"].encode()).hexdigest()
            != binding["reference_sha256"]
            or hashlib.sha256(row["question"].encode()).hexdigest() != binding["question_sha256"]
        ):
            raise ValueError("Authoring input differs from verified source projection")
    coverage = _rows(root / "coverage.jsonl")
    coverage_keys = [(row["case_id"], row["slot"]) for row in coverage]
    if len(coverage_keys) != 475 or set(coverage_keys) != {
        (case, slot) for case in DEVELOPMENT_CASE_IDS for slot in slots
    }:
        raise ValueError("Incomplete or duplicate coverage")
    provenance = _rows(root / "provenance.jsonl")
    payloads = _rows(root / "judge_inputs.jsonl")
    label_rows = _rows(root / "proposed_labels.jsonl")
    reviews = _rows(root / "reviews.jsonl")
    review_map = {(row["case_id"], row["slot"]): row for row in reviews}
    if len(reviews) != 475 or set(review_map) != set(coverage_keys):
        raise ValueError("Independent reviews do not cover every slot")
    for review in reviews:
        if (
            not review["author"]
            or not review["reviewer"]
            or review["author"] == review["reviewer"]
            or not review["rationale"].strip()
            or review["disposition"] not in {"accepted", "unresolved"}
            or (review["expected_label"] is not None and type(review["expected_label"]) is not bool)
        ):
            raise ValueError("Invalid independent slot review")
    if not (len(provenance) == len(payloads) == len(label_rows) == manifest["sample_count"]):
        raise ValueError("Payload/label/provenance counts differ")
    samples: list[dict[str, Any]] = []
    labels: dict[str, bool] = {}
    seen: dict[str, dict[str, Any]] = {}
    all_labels: dict[str, bool] = {}
    payload_hashes: set[str] = set()
    for number, (source, packet, label) in enumerate(
        zip(provenance, payloads, label_rows, strict=True), start=1
    ):
        sid, case = source["candidate_id"], source["case_id"]
        if sid in seen or case not in references or sid != label["candidate_id"]:
            raise ValueError("Duplicate or misaligned candidate identity")
        reference = references[case]
        packet = validate_input("C", packet)
        digest = stable_json_sha256(packet)
        if (
            source["line_number"] != number
            or source["input_sha256"] != digest
            or digest in payload_hashes
            or packet["question"] != reference["question"]
            or packet["reference_conclusion"] != reference["reference_conclusion"]
            or source["partition"] != reference["partition"]
        ):
            raise ValueError("Candidate input, reference or grouping differs")
        if (
            type(label["expected_label"]) is not bool
            or label["review_disposition"] != "accepted"
            or not label["author"]
            or not label["reviewer"]
            or label["author"] == label["reviewer"]
            or not label["rationale"].strip()
        ):
            raise ValueError("Missing independent review or proposed boolean label")
        for slot in source["slots"]:
            review = review_map[(case, slot)]
            if (
                review["disposition"] != "accepted"
                or review["author"] != label["author"]
                or review["reviewer"] != label["reviewer"]
                or review["expected_label"] != label["expected_label"]
                or review["candidate_sha256"]
                != hashlib.sha256(packet["candidate_conclusion"].encode()).hexdigest()
                or not review["rationale"].strip()
            ):
                raise ValueError("Review does not bind the exact candidate and label")
        seen[sid] = source
        all_labels[sid] = label["expected_label"]
        payload_hashes.add(digest)
        if partition == "all" or source["partition"] == partition:
            samples.append({"sample_id": sid, "case_id": case, "packet": packet})
            labels[sid] = label["expected_label"]
    used: Counter[str] = Counter()
    for row in coverage:
        sid = row["candidate_id"]
        if row["status"] in {"generated", "shared"}:
            if sid not in seen or seen[sid]["case_id"] != row["case_id"]:
                raise ValueError("Coverage references wrong candidate")
            if row["slot"] not in seen[sid]["slots"]:
                raise ValueError("Coverage slot missing from provenance")
            if row["slot"] == "BASE":
                packet = payloads[seen[sid]["line_number"] - 1]
                if (
                    packet["candidate_conclusion"] != packet["reference_conclusion"]
                    or all_labels[sid] is not True
                ):
                    raise ValueError("Baseline changed reference wording or lacks pass proposal")
            used[sid] += 1
        elif row["status"] in {"inapplicable", "unresolved"}:
            if sid is not None or not row["rationale"].strip():
                raise ValueError("Excluded slot has a candidate or no explanation")
            review = review_map[(row["case_id"], row["slot"])]
            if row["status"] == "inapplicable" and (
                review["disposition"] != "accepted"
                or review["expected_label"] is not None
                or review["candidate_sha256"] is not None
            ):
                raise ValueError("Inapplicable slot lacks consistent exclusion review")
        else:
            raise ValueError("Unknown coverage disposition")
    if set(used) != set(seen) or any(
        used[sid] != len(source["slots"]) for sid, source in seen.items()
    ):
        raise ValueError("Orphaned candidate or slot")
    return (
        samples,
        labels,
        {
            "dataset_id": manifest["dataset_id"],
            "partition": partition,
            "label_status": manifest["label_status"],
            "sample_count": len(samples),
            "publication_sample_count": manifest["sample_count"],
            "prompt_version": manifest["prompt_version"],
            "completion": pointer["completion"],
        },
    )
