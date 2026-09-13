"""Publish Task 06D v2 decisions from the complete sealed semantic topology."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from er_commons.document_records.document_structure.baseline import (
    load_baseline_candidate,
    prepare_semantic_content_in_place,
    remap_candidate_namespace,
)
from er_commons.document_records.document_structure.parser_evidence import (
    artifact_reference,
    attach_stable_keys_in_place,
    load_producer_evidence,
)
from er_commons.document_records.document_structure.repeated_heading_policy import (
    HeadingTopology,
    TocHeadingEvidence,
    classify_repeated_heading_group,
)
from er_commons.document_records.document_structure.repeated_heading_projection import (
    _heading_topologies_from_records,
    project_repeated_heading_decisions,
)
from er_commons.document_records.document_structure.repeated_heading_qualification import (
    publish_repeated_heading_qualification,
)
from er_commons.document_records.document_structure.replacement_evidence import (
    hierarchy_relevant_keys,
    replacement_dispositions,
)
from er_commons.document_records.document_structure.runtime import (
    load_construction_inputs,
    load_runtime_context,
)
from er_commons.document_records.document_structure.sections import (
    build_document_sections,
)

JsonObject = dict[str, Any]
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _unrepaired_records(
    data_root: Path, config_path: Path
) -> tuple[list[JsonObject], list[JsonObject], tuple[HeadingTopology, ...]]:
    """Reconstruct the complete pre-repair topology from sealed record evidence."""
    context = load_runtime_context(data_root=data_root, config_path=config_path)
    inputs = load_construction_inputs(
        context,
        candidate_id=context.config.baseline_candidate_id,
    )
    baseline = load_baseline_candidate(inputs.baseline_candidate_root)
    collections = remap_candidate_namespace(
        baseline,
        old_extraction_id=inputs.baseline_candidate_id,
        new_extraction_id=inputs.baseline_candidate_id,
    )
    evidence = load_producer_evidence(
        baseline_document=inputs.baseline_document,
        hierarchy_document=inputs.hierarchy_document,
        hierarchy_root=inputs.hierarchy_candidate_root,
    )
    attach_stable_keys_in_place(collections["blocks"], evidence.baseline_key_by_pointer)
    content = prepare_semantic_content_in_place(collections)
    replacement_keys = set(
        replacement_dispositions(
            baseline_document=evidence.baseline_document,
            producer_root=inputs.baseline_producer_root,
            key_by_pointer=evidence.baseline_key_by_pointer,
            relevant_keys=hierarchy_relevant_keys(evidence.hierarchy, []),
        )
    )
    sections, content = build_document_sections(
        content,
        document_id=collections["documents"][0]["id"],
        extraction_id=inputs.baseline_candidate_id,
        source_id=inputs.source_id,
        features=evidence.item_features,
        decisions=evidence.decisions,
        hierarchy=evidence.hierarchy,
        evidence_ref=artifact_reference(
            inputs.hierarchy_candidate_root,
            "artifacts/decisions.jsonl",
        ),
        replacement_keys=replacement_keys,
    )
    return sections, content, _heading_topologies_from_records(sections, content)


def _decisions(recipe: JsonObject, topologies: tuple[HeadingTopology, ...]) -> tuple[Any, ...]:
    by_key = {item.stable_item_key: item for item in topologies}
    if len(by_key) != len(topologies):
        raise ValueError("complete topology contains duplicate stable heading keys")
    decisions = []
    for group in recipe["groups"]:
        keys = tuple(group["heading_stable_keys"])
        if len(keys) != 2:
            raise ValueError("qualification group must name exactly two headings")
        pair = tuple(by_key[key] for key in keys)
        boundary = by_key[group["following_boundary_stable_key"]]
        if boundary.sibling_index != pair[1].sibling_index + 1:
            raise ValueError(
                f"{group['chapter_marker']} boundary is not the immediate next sibling"
            )
        toc = group["toc_evidence"]
        decision = classify_repeated_heading_group(
            pair,
            toc_evidence=(
                TocHeadingEvidence(
                    evidence_ids=tuple(toc["evidence_ids"]),
                    raw_text=toc["raw_text"],
                    terminal_destination_token=toc["terminal_destination_token"],
                ),
            ),
            following_sibling=boundary,
        )
        if decision.status != "eligible" or decision.chapter_marker != group["chapter_marker"]:
            raise ValueError(
                f"{group['chapter_marker']} failed complete-topology qualification: "
                f"{decision.reason_codes}"
            )
        decisions.append(decision)
    return tuple(decisions)


def qualify(data_root: Path, recipe_path: Path, output_root: Path) -> Path:
    """Validate the full projection twice, then publish fresh completion-last evidence."""
    recipe_path = recipe_path.resolve()
    recipe = _load_json(recipe_path)
    if recipe.get("schema_version") != (
        "er_commons.task06d.repeated_heading_qualification_recipe.v2"
    ):
        raise ValueError("unsupported Task 06D qualification recipe")
    input_config = PROJECT_ROOT / recipe["input_document_structure_config"]
    sections, content, topologies = _unrepaired_records(data_root.resolve(), input_config)
    decisions = _decisions(recipe, topologies)
    once = project_repeated_heading_decisions(sections, content, decisions)
    twice = project_repeated_heading_decisions(once.sections, once.content, decisions)
    if twice.sections != once.sections or twice.content != once.content:
        raise ValueError("Task 06D v2 projection is not idempotent")
    expected_removed = {item.absorbed_heading_key for item in decisions}
    retained_keys = {item.get("stable_item_key") for item in once.content}
    if not expected_removed.issubset(retained_keys):
        raise ValueError("Task 06D v2 projection failed to retain every absorbed heading block")
    policy_path = PROJECT_ROOT / recipe["policy_path"]
    schema_path = PROJECT_ROOT / recipe["decision_schema_path"]
    generator_path = Path(__file__).resolve()
    return publish_repeated_heading_qualification(
        output_root.resolve(),
        decisions=decisions,
        source_ref={
            "authority": "task06d_v2_qualification_recipe",
            "relative_path": recipe_path.relative_to(PROJECT_ROOT).as_posix(),
            "identity": f"sha256:{_sha256(recipe_path)}",
            "verification_mode": "complete_sealed_topology_reconstruction",
        },
        policy_ref={
            "path": policy_path.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": _sha256(policy_path),
        },
        schema_ref={
            "path": schema_path.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": _sha256(schema_path),
        },
        decision_schema=_load_json(schema_path),
        generator_ref={
            "path": generator_path.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": _sha256(generator_path),
        },
        human_decision_ref=recipe["human_decision_ref"],
        limitations=tuple(recipe["limitations"]),
    )


def main() -> None:
    """Parse the explicit source-free qualification inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--recipe", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    qualify(args.data_root, args.recipe, args.output_root)


if __name__ == "__main__":
    main()
