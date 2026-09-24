"""Read-only accepted input bindings for the Task 05G consumer.

Compact seals are hashed. Selected JSON/JSONL payloads are size checked against
those seals; source binaries and unselected artifact trees are never opened.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from er_commons.response_inventory import reference_baseline as baseline
from er_commons.response_inventory.contract import build_record_id
from er_commons.response_inventory.reference_replay_spec import (
    HEADER_POLICY,
    INNER_REFERENCE_POLICIES,
)
from er_commons.response_inventory.run_spec import AcceptedTask05D, AcceptedTask05E

JsonObject = dict[str, Any]
COMPACT_LIMIT = 4 * 1024 * 1024


@dataclass(frozen=True)
class ReplayInputs:
    """Verified input records and their ordered, sealed provenance dependencies."""

    source_records: list[JsonObject]
    baseline_outcomes: list[JsonObject]
    baseline_links: list[JsonObject]
    target_rows: list[JsonObject]
    direct_section_children: dict[str, tuple[str, ...]]
    catalog: JsonObject
    registry: JsonObject
    target_limitations: JsonObject
    handoff: JsonObject
    correspondence: JsonObject
    dependencies: list[JsonObject]
    replaced_dependencies: list[JsonObject] = field(default_factory=list)


def contained(root: Path, relative: str) -> Path:
    """Reject traversal, absolute paths, and symlinks that escape an owned root."""
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"input path must be contained and relative: {relative}")
    result = (root / path).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(f"input path escapes root: {relative}")
    return result


def read_object(path: Path, *, digest: str | None = None) -> JsonObject:
    """Read one JSON object, hashing only bounded compact metadata when requested."""
    if path.suffix != ".json":
        raise ValueError(f"source-free input must be JSON: {path}")
    if digest is not None:
        verify_digest(path, digest)
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"input must be a JSON object: {path}")
    return value


def verify_digest(path: Path, digest: str) -> None:
    """Fail before reading forbidden binaries or hashing a large payload."""
    if path.suffix not in {".json", ".jsonl"} or path.stat().st_size > COMPACT_LIMIT:
        raise ValueError(f"not compact source-free metadata: {path}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f"input digest mismatch: {path}")


def read_rows(path: Path) -> list[JsonObject]:
    """Read selected JSONL rows only, rejecting non-object records."""
    if path.suffix != ".jsonl":
        raise ValueError(f"source-free rows must be JSONL: {path}")
    rows = []
    with path.open() as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid JSONL input at {path}:{line_number}: {error.msg}"
                ) from error
            if not isinstance(row, dict):
                raise ValueError(f"JSONL input must contain objects: {path}:{line_number}")
            rows.append(row)
    return rows


def sealed_path(root: Path, reference: Mapping[str, Any], *, compact: bool) -> Path:
    """Resolve a sealed reference and verify its recorded size and optional hash."""
    path = contained(root, str(reference["path"]))
    if path.stat().st_size != reference["byte_size"]:
        raise ValueError(f"input recorded size mismatch: {path}")
    if compact:
        verify_digest(path, str(reference["sha256"]))
    return path


def require_fields(value: Mapping[str, Any], expected: Mapping[str, Any], label: str) -> None:
    """Reject missing or conflicting fields without modifying historic records."""
    for name, item in expected.items():
        if value.get(name) != item:
            raise ValueError(f"{label} differs: {name}")


def inventory_entries(inventory: JsonObject) -> dict[str, JsonObject]:
    """Index a managed inventory while rejecting duplicate paths."""
    rows = inventory["files"]
    result = {row["path"]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError("duplicate managed inventory path")
    return result


def _closed_records(root: Path, completion_digest: str, expected: Mapping[str, Any]) -> JsonObject:
    """Verify completion-last compact records and their exact managed closure."""
    completion = read_object(root / "completion.json", digest=completion_digest)
    require_fields(completion, {"completion_last": True, **expected}, "completion")
    inventory = read_object(root / "artifact_inventory.json", digest=completion["inventory_sha256"])
    entries = inventory_entries(inventory)
    actual = {p.name for p in root.iterdir() if p.is_file()}
    if actual != {*entries, "completion.json", "artifact_inventory.json"} or any(
        p.is_dir() for p in root.iterdir()
    ):
        raise ValueError("accepted records have unexpected or missing files")
    if inventory.get("file_count") != len(entries) or inventory.get("byte_count") != sum(
        r["byte_size"] for r in entries.values()
    ):
        raise ValueError("accepted inventory counts differ")
    for entry in entries.values():
        sealed_path(root, entry, compact=True)
    return inventory


def load_review_chain(pointer_path: Path, artifact_root: Path, freeze: JsonObject) -> JsonObject:
    """Bind acceptance, all seven finalization files, and sampled limitations."""
    pointer = read_object(pointer_path)
    if pointer != freeze["acceptance_pointer"]:
        raise ValueError("Task 06H acceptance pointer differs from frozen authority")
    acceptance_root = contained(artifact_root, pointer["acceptance_relative_path"]) / "records"
    inventory = _closed_records(
        acceptance_root,
        pointer["completion_sha256"],
        {"status": "accepted_with_limitations", "acceptance_id": pointer["acceptance_id"]},
    )
    if set(inventory_entries(inventory)) != {"acceptance.json"}:
        raise ValueError("acceptance inventory must contain exactly acceptance.json")
    acceptance = read_object(
        acceptance_root / "acceptance.json", digest=pointer["acceptance_sha256"]
    )
    if acceptance != freeze["acceptance"]:
        raise ValueError("Task 06H acceptance record differs")
    records = contained(artifact_root, freeze["finalization_relative_root"]) / "records"
    if records.parent.name != pointer["finalization_id"]:
        raise ValueError("mixed finalization root")
    inventory = _closed_records(
        records,
        freeze["finalization_completion_sha256"],
        {
            "status": "complete_pending_explicit_acceptance",
            "finalization_id": pointer["finalization_id"],
        },
    )
    if inventory != freeze["finalization_inventory"]:
        raise ValueError("Task 06H finalization inventory differs")
    handoff = read_object(records / "task05g_handoff.json")
    if handoff != freeze["task05g_handoff"]:
        raise ValueError("Task 06H handoff or warning binding differs")
    candidate = read_object(records / "finalization_candidate.json")
    accepted = acceptance["bindings"]
    require_fields(
        candidate,
        {
            key: accepted[key]
            for key in (
                "finalization_id",
                "sampled_review_merge_id",
                "toc_merge_id",
                "registry_id",
                "target_limitations_id",
                "task05g_handoff_id",
                "mechanical_handoff_id",
            )
        },
        "finalization candidate",
    )
    registry = read_object(records / "usability_registry.json")
    limitations = read_object(records / "target_review_limitations.json")
    toc = read_object(records / "toc_review_decisions.json")
    provenance = read_rows(records / "decision_provenance.jsonl")
    strata = read_object(records / "sample_stratum_confirmations.json")
    require_fields(
        registry,
        {
            "registry_id": accepted["registry_id"],
            "status": "complete_bounded_merge",
            "source_count": 35,
        },
        "registry",
    )
    if (
        len(registry["entries"]) != 35
        or len({r["logical_source_id"] for r in registry["entries"]}) != 35
    ):
        raise ValueError("registry source membership is incomplete")
    require_fields(
        toc,
        {"toc_merge_id": accepted["toc_merge_id"], "status": "complete_bounded_merge"},
        "TOC merge",
    )
    decisions = {r["entry_id"]: r["disposition"] for r in toc["entries"]}
    if len(decisions) != len(toc["entries"]) or len(decisions) != 757:
        raise ValueError("TOC decision population differs")
    if (
        len(provenance) != len(decisions)
        or {r["entry_id"]: r["disposition"] for r in provenance} != decisions
    ):
        raise ValueError("TOC provenance membership differs")
    projection = freeze["review_coverage_projection"]
    if (
        dict(Counter(r["decision_origin"] for r in provenance))
        != projection["decision_origin_counts"]
    ):
        raise ValueError("706 proved / 51 sample-confirmed provenance differs")
    if (
        strata["entries"] != projection["sample_strata"]
        or strata.get("sample_count") != 11
        or strata.get("status") != "complete"
    ):
        raise ValueError("sampled-stratum confirmation differs")
    require_fields(
        limitations,
        {"target_limitations_id": accepted["target_limitations_id"], "target_count": 185},
        "target limitations",
    )
    targets = [
        {
            key: r.get(key)
            for key in (
                "target_id",
                "target_kind",
                "fresh_review_status",
                "text_only_model_eligibility",
            )
        }
        for r in limitations["entries"]
    ]
    if targets != projection["targets"] or len({r["target_id"] for r in targets}) != 185:
        raise ValueError("target review or text-only eligibility differs")
    return {
        "acceptance": acceptance,
        "registry": registry,
        "target_limitations": limitations,
        "handoff": handoff,
        "records_root": records,
        "acceptance_root": acceptance_root,
    }


def _dependency(
    role: str, path: Path, artifact_root: Path, identity: str, digest: str
) -> JsonObject:
    """Describe a verified upstream seal without copying any payload."""
    return {
        "role": role,
        "authority": "artifact_root",
        "path": path.relative_to(artifact_root.resolve()).as_posix(),
        "identity": identity,
        "sha256": digest,
    }


def _load_legacy_inputs(
    inputs: JsonObject, artifact_root: Path, *, replacement: bool = False
) -> tuple[list[JsonObject], list[JsonObject]]:
    """Reuse accepted source/graph checks without verifying obsolete code bindings."""
    from types import SimpleNamespace
    from typing import cast

    from er_commons.response_inventory.run_spec import ResponseReferenceRunSpecV5

    d = AcceptedTask05D.model_validate(inputs["task05d"])
    e = AcceptedTask05E.model_validate(inputs["task05e"])
    adapter = cast(
        ResponseReferenceRunSpecV5, SimpleNamespace(accepted_task05d=d, accepted_task05e=e)
    )
    dependencies = []
    accepted_inputs: list[tuple[str, AcceptedTask05D | AcceptedTask05E]] = [("05d", d), ("05e", e)]
    for stage, accepted in accepted_inputs:
        path = (
            contained(artifact_root, str(accepted.candidate_root)) / "records/stage_completion.json"
        )
        completion = read_object(path)
        inventory = read_object(path.parent / "managed_file_inventory.json")
        if completion.get("status") != "complete_with_warnings":
            raise ValueError(f"{stage} accepted completion status differs")
        if build_record_id(completion) != accepted.completion_id:
            raise ValueError(f"{stage} accepted completion identity differs")
        if build_record_id(inventory) != accepted.inventory_id:
            raise ValueError(f"{stage} accepted inventory identity differs")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        dependencies.append(
            _dependency(
                f"task{stage}_completion", path, artifact_root, accepted.completion_id, digest
            )
        )
    records, units = baseline._load_task05d(adapter, artifact_root)
    baseline._validate_task05e(adapter, artifact_root)
    all_mentions = [row for row in records if row.get("record_type") == "reference_mention"]
    if not replacement:
        baseline._validate_population(all_mentions, units)
    return records, dependencies


def validate_source_replacement(previous: list[JsonObject], current: list[JsonObject]) -> None:
    """Permit only added intra-volume mentions/spans, preserving all source semantics.

    Activity provenance changes on replay. Every other historical field, including
    IDs, raw pages, unit boundaries and report mentions, must remain identical.
    The caller separately validates the new bundle's evidence and accepted seals.
    """
    from er_commons.artifact_io import canonical_json_sha256

    def index(rows: list[JsonObject]) -> dict[str, JsonObject]:
        """Compare complete records after removing only the new activity binding."""
        return {
            canonical_json_sha256({k: v for k, v in row.items() if k != "activity_id"}): row
            for row in rows
            if row["record_type"] != "activity"
        }

    old, new = index(previous), index(current)
    if not old.keys() <= new.keys():
        raise ValueError("source replacement changed or removed historical source evidence")
    added = [new[key] for key in new.keys() - old.keys()]
    mentions = [row for row in added if row["record_type"] == "reference_mention"]
    span_ids = {row["mention_span_id"] for row in mentions}
    if not mentions or any(row["reference_domain"] != "intra_volume" for row in mentions):
        raise ValueError("source replacement must add only intra-volume mentions")
    if any(
        row["record_type"] != "reference_mention"
        and not (row["record_type"] == "source_span" and row["span_id"] in span_ids)
        for row in added
    ):
        raise ValueError("source replacement contains unrelated records")


def _load_baseline(
    inputs: JsonObject, artifact_root: Path, handoff: JsonObject
) -> tuple[list[JsonObject], list[JsonObject], JsonObject]:
    """Verify the accepted nonterminal 05F receipt and its compact managed files."""
    item = inputs["task05f"]
    require_fields(
        item,
        {
            "rules_id": handoff["task05f_rules"],
            "semantic_digest": handoff["task05f_semantic_digest"],
        },
        "05F baseline binding",
    )
    root = contained(artifact_root, item["root"])
    if root.name != item["rules_id"]:
        raise ValueError("05F baseline root identity differs")
    receipt = read_object(root / "records/rule_receipt.json", digest=item["receipt_sha256"])
    require_fields(
        receipt,
        {
            "semantic_digest": item["semantic_digest"],
            "completion_written": False,
            "status": "qualified_rules_complete_review_required",
            "source_pdf_accessed": False,
        },
        "05F receipt",
    )
    inventory = read_object(
        root / "records/managed_file_inventory.json", digest=item["inventory_sha256"]
    )
    entries = inventory_entries(inventory)
    receipt_entries = inventory_entries(receipt)
    managed_ref = receipt_entries.get("records/managed_file_inventory.json")
    if managed_ref is None or managed_ref["sha256"] != item["inventory_sha256"]:
        raise ValueError("05F receipt does not bind the accepted managed inventory")
    sealed_path(root, managed_ref, compact=True)
    if set(receipt_entries) != {*entries, "records/managed_file_inventory.json"}:
        raise ValueError("05F receipt file closure differs")
    for name, entry in entries.items():
        if receipt_entries.get(name) != {k: v for k, v in entry.items() if k != "authority"}:
            raise ValueError("05F receipt inventory differs")
        sealed_path(root, entry, compact=True)
    outcomes = read_rows(root / "outcomes/reference_outcomes.jsonl")
    links = read_rows(root / "links/draft_eir_links.jsonl")
    return (
        outcomes,
        links,
        _dependency(
            "task05f_baseline",
            root / "records/rule_receipt.json",
            artifact_root,
            item["rules_id"],
            item["receipt_sha256"],
        ),
    )


def _qualification_sources(
    policy: str,
    records: list[JsonObject],
    outcomes: list[JsonObject],
    registry: JsonObject,
) -> tuple[set[str], set[str]]:
    """Select physical sources whose existing canonical streams may qualify targets.

    This limits source-free I/O, not resolver eligibility: inner page/table syntax
    requests supplemental aliases, while section collisions request header evidence.
    Final substitutes follow the accepted registry's logical-to-physical mapping.
    """
    if policy not in INNER_REFERENCE_POLICIES:
        return set(), set()
    physical_sources = {
        row["logical_source_id"]: row["selected_source_id"] for row in registry["entries"]
    }
    contexts = baseline._mention_contexts(records)
    inner_sources: set[str] = set()
    header_sources: set[str] = set()
    for outcome in outcomes:
        context = contexts.get(outcome["mention_span_id"], baseline._MentionContext())
        if outcome["requested_target_type"] == "document" and re.search(
            r"\b(?:page|table)\s+(?:\d|[a-z](?:[-.]\d|\b))",
            context.before + " " + context.after,
            re.I,
        ):
            inner_sources.update(
                physical_sources.get(source, source) for source in outcome["routed_source_ids"]
            )
        if (
            policy == HEADER_POLICY
            and outcome["requested_target_type"] == "section"
            and outcome["terminal_reason"] == "exact_target_collision"
        ):
            header_sources.update(
                physical_sources.get(source, source) for source in outcome["routed_source_ids"]
            )
    return inner_sources, header_sources


def load_replay_inputs(
    spec: Mapping[str, Any], repository_root: Path, artifact_root: Path
) -> ReplayInputs:
    """Load only sealed records required by the separately authorized replay."""
    from er_commons.response_inventory.reference_replay_comparison import validate_population
    from er_commons.response_inventory.reference_replay_mechanical import load_mechanical_inputs

    root = artifact_root.resolve()
    pinned = {row["path"]: row["sha256"] for row in spec["repository_bindings"]}
    freeze = read_object(
        contained(repository_root, spec["binding_freeze"]), digest=pinned[spec["binding_freeze"]]
    )
    population = read_object(
        contained(repository_root, spec["population_freeze"]),
        digest=pinned[spec["population_freeze"]],
    )
    inputs = dict(spec["inputs"])
    review = load_review_chain(contained(root, inputs["task06h_pointer"]), root, freeze)
    handoff = review["handoff"]
    replacement = inputs.get("replaces_source_graph")
    historical = replacement or inputs
    for name in ("task05d", "task05e"):
        if historical[name]["revision_id"] != handoff[name + "_revision"]:
            raise ValueError(f"{name} revision differs from accepted handoff")
    records, dependencies = _load_legacy_inputs(inputs, root, replacement=bool(replacement))
    prior_dependencies: list[JsonObject] = []
    if replacement:
        from er_commons.response_inventory.acceptance import validate_task05d_candidate

        validate_task05d_candidate(contained(root, inputs["task05d"]["candidate_root"]), root)
        previous, prior_dependencies = _load_legacy_inputs(replacement, root)
        validate_source_replacement(previous, records)
    outcomes, links, baseline_dependency = _load_baseline(inputs, root, handoff)
    validate_population(outcomes, population)
    dependencies.append(baseline_dependency)
    qualification_sources, header_sources = _qualification_sources(
        spec["policy"], records, outcomes, review["registry"]
    )
    mechanics = load_mechanical_inputs(
        inputs["task06g"],
        root,
        review,
        outcomes,
        qualification_sources=qualification_sources,
        header_sources=header_sources,
    )
    for role, filename, identity in [
        ("task06h_acceptance", "acceptance.json", freeze["acceptance_pointer"]["acceptance_id"]),
        ("task06h_handoff", "task05g_handoff.json", handoff["task05g_handoff_id"]),
        ("task06h_registry", "usability_registry.json", handoff["usability_registry_id"]),
        ("task06h_toc_merge", "toc_review_decisions.json", handoff["toc_merge_id"]),
        (
            "task06h_target_limitations",
            "target_review_limitations.json",
            handoff["target_limitations_id"],
        ),
    ]:
        directory = (
            review["acceptance_root"] if role == "task06h_acceptance" else review["records_root"]
        )
        path = directory / filename
        dependencies.append(
            _dependency(role, path, root, identity, hashlib.sha256(path.read_bytes()).hexdigest())
        )
    dependencies.extend(mechanics["dependencies"])
    review["target_limitations"] = {
        **review["target_limitations"],
        "document_target_mapping": mechanics["correspondence"]["document_target_mapping"],
    }
    return ReplayInputs(
        source_records=records,
        baseline_outcomes=outcomes,
        baseline_links=links,
        target_rows=mechanics["target_rows"],
        direct_section_children=mechanics["direct_section_children"],
        catalog=mechanics["catalog"],
        registry=review["registry"],
        target_limitations=review["target_limitations"],
        handoff=handoff,
        correspondence=mechanics["correspondence"],
        dependencies=dependencies,
        replaced_dependencies=prior_dependencies,
    )
