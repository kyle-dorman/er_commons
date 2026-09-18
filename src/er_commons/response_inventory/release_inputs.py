"""Read-only, source-free composition of the exact accepted Task 05 components.

Compact controls are hashed; large inherited files are size checked. Task 05D/E
records additionally pass their original semantic/anchor validator. No producer,
resolver, PDF, image, or model entrypoint is imported or invoked here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, NamedTuple

from er_commons.artifact_io import (
    canonical_json_sha256,
    read_json_object,
    read_jsonl,
    sha256_file,
)
from er_commons.response_inventory.contract import semantic_bundle_digest, validate_record_bundle
from er_commons.response_inventory.release_spec import contained_path
from er_commons.response_inventory.release_validation import validate_composition

type JsonObject = dict[str, Any]
COMPACT_LIMIT = 4 * 1024 * 1024


def verify_digest(path: Path, digest: str) -> None:
    """Hash only bounded source-free metadata, never source binaries or large trees."""
    if path.suffix not in {".json", ".jsonl"} or path.stat().st_size > COMPACT_LIMIT:
        raise ValueError(f"not compact source-free metadata: {path}")
    if sha256_file(path) != digest:
        raise ValueError(f"input digest mismatch: {path}")


def read_object(path: Path, *, digest: str | None = None) -> JsonObject:
    """Read a selected JSON object after its optional compact seal check."""
    if path.suffix != ".json":
        raise ValueError(f"source-free object must be JSON: {path}")
    if digest is not None:
        verify_digest(path, digest)
    return dict(read_json_object(path))


def read_rows(path: Path) -> list[JsonObject]:
    """Read selected object rows only, preserving original payloads in memory."""
    if path.suffix != ".jsonl":
        raise ValueError(f"source-free rows must be JSONL: {path}")
    return [dict(row) for row in read_jsonl(path)]


def require_fields(value: JsonObject, expected: JsonObject, label: str) -> None:
    """Reject missing or conflicting associations in otherwise sealed controls."""
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise ValueError(f"{label} field differs: {key}")


def _closed_records(root: Path, completion_digest: str, expected: JsonObject) -> JsonObject:
    """Verify the compact 06H completion/inventory chain and its exact file closure."""
    completion = read_object(root / "completion.json", digest=completion_digest)
    require_fields(completion, {"completion_last": True, **expected}, "06H completion")
    inventory = read_object(root / "artifact_inventory.json", digest=completion["inventory_sha256"])
    entries = {item["path"]: item for item in inventory["files"]}
    if len(entries) != len(inventory["files"]):
        raise ValueError("duplicate 06H managed inventory path")
    actual = {path.name for path in root.iterdir() if path.is_file()}
    if actual != {*entries, "completion.json", "artifact_inventory.json"} or any(
        path.is_dir() for path in root.iterdir()
    ):
        raise ValueError("accepted 06H records have unexpected or missing files")
    if inventory.get("file_count") != len(entries) or inventory.get("byte_count") != sum(
        item["byte_size"] for item in entries.values()
    ):
        raise ValueError("accepted 06H inventory counts differ")
    for item in entries.values():
        if item["byte_size"] > COMPACT_LIMIT or not item.get("sha256"):
            raise ValueError("06H review records require compact digest seals")
        verify_reference(root, item)
    return inventory


@dataclass(frozen=True)
class ReleaseInputs:
    """Accepted records in memory and compact references retained by the release."""

    source_records: list[JsonObject]
    edges: list[JsonObject]
    graph_diagnostics: list[JsonObject]
    graph_views: list[JsonObject]
    outcomes: list[JsonObject]
    links: list[JsonObject]
    reference_diagnostics: list[JsonObject]
    dependencies: list[JsonObject]
    components: list[JsonObject]
    limitations: JsonObject
    handoff: JsonObject
    accounting: JsonObject
    semantic_digest: str


class SourceGraphInputs(NamedTuple):
    """Name the accepted source/graph payloads at the composition boundary."""

    source_records: list[JsonObject]
    edges: list[JsonObject]
    diagnostics: list[JsonObject]
    views: list[JsonObject]
    components: list[JsonObject]


def verify_reference(root: Path, reference: JsonObject) -> Path:
    """Check relative metadata size and compact digest without opening large trees."""
    path = contained_path(root, reference["path"])
    if path.suffix not in {".json", ".jsonl"}:
        raise ValueError(f"05H source-free reference must be JSON/JSONL: {path}")
    size = reference.get("size_bytes", reference.get("byte_size"))
    if not isinstance(size, int) or path.stat().st_size != size:
        raise ValueError(f"05H input size differs: {path}")
    if reference.get("sha256") is not None and size <= COMPACT_LIMIT:
        verify_digest(path, reference["sha256"])
    return path


def _checkpoint(root: Path, reference: JsonObject) -> JsonObject:
    """Validate bounded inherited checkpoint controls and exact managed membership."""
    path = verify_reference(root, reference)
    completion = read_object(path)
    if completion.get("status") != "complete":
        raise ValueError(f"05G checkpoint is not complete: {path}")
    names = [item["path"] for item in completion["inventory"]]
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate checkpoint file: {path}")
    actual = {p.relative_to(path.parent).as_posix() for p in path.parent.rglob("*") if p.is_file()}
    if actual != set(names) | {"completion.json"}:
        raise ValueError(f"05G checkpoint managed closure differs: {path}")
    for item in completion["inventory"]:
        verify_reference(path.parent, item)
    return completion


def _component(
    root: Path,
    owner: Path,
    inventory: list[JsonObject],
    name: str,
    role: str,
    id_field: str,
    rows: list[JsonObject],
) -> JsonObject:
    """Describe one retained external payload without duplicating its contents."""
    matches = [item for item in inventory if item["path"] == name]
    if len(matches) != 1:
        raise ValueError(f"component is absent or duplicated in inventory: {name}")
    seal = matches[0]
    verify_reference(owner, seal)
    return {
        "role": role,
        "authority": "artifact_root",
        "owner_revision": owner.parent.name if owner.name.startswith("attempt-") else owner.name,
        "path": (owner / name).relative_to(root).as_posix(),
        "schema_version": rows[0].get("schema_version") if rows else None,
        "record_count": len(rows),
        "record_semantic_digest": canonical_json_sha256(rows),
        "id_field": id_field,
        "sha256": seal.get("sha256"),
        "size_bytes": seal.get("size_bytes", seal.get("byte_size")),
        "check_mode": "accepted_digest_and_size"
        if seal.get("sha256")
        else "accepted_semantic_digest_and_size",
    }


def _verify_source_graph_owner(
    stage: str,
    owner: Path,
    completion: JsonObject,
    inventory: JsonObject,
    dependency: JsonObject,
    accepted_semantic_digest: str,
) -> None:
    """Check one accepted bundle's identity and file closure before reading its rows."""
    require_fields(
        completion,
        {
            "completion_id": dependency["identity"],
            "inventory_id": inventory["inventory_id"],
            "stage": stage,
        },
        stage,
    )
    acceptance = read_object(owner.with_suffix(".acceptance.json"))
    require_fields(
        acceptance,
        {
            "completion_id": completion["completion_id"],
            "semantic_digest": accepted_semantic_digest,
        },
        f"{stage} acceptance",
    )
    names = [item["path"] for item in inventory["files"]]
    actual = {p.relative_to(owner).as_posix() for p in owner.rglob("*") if p.is_file()}
    if len(names) != len(set(names)) or actual != set(names) | {
        "records/stage_completion.json",
        "records/managed_file_inventory.json",
    }:
        raise ValueError(f"{stage} managed closure differs")
    for item in inventory["files"]:
        verify_reference(owner, item)


def _source_graph(
    binding: JsonObject,
    root: Path,
    dependencies: dict[str, JsonObject],
) -> SourceGraphInputs:
    """Validate the original bundles and their accepted semantic digests read-only."""
    schema = read_object(
        Path(__file__).resolve().parents[3]
        / "benchmarks/er_bench/schemas/response_inventory/v1/records.schema.json"
    )
    owners = {
        stage: contained_path(root, dependencies[f"task{stage}_completion"]["path"]).parent.parent
        for stage in ("05d", "05e")
    }
    inventories = {
        stage: read_object(owner / "records/managed_file_inventory.json")
        for stage, owner in owners.items()
    }
    completions = {
        stage: read_object(owner / "records/stage_completion.json")
        for stage, owner in owners.items()
    }
    for stage, owner in owners.items():
        _verify_source_graph_owner(
            stage,
            owner,
            completions[stage],
            inventories[stage],
            dependencies[f"task{stage}_completion"],
            binding["accepted_component_semantic_digests"][f"task{stage}"],
        )
    source = read_rows(owners["05d"] / "inventory/source_records.jsonl")
    edges = read_rows(owners["05e"] / "graph/review_edges.jsonl")
    diagnostics = read_rows(owners["05e"] / "diagnostics/individual_diagnostics.jsonl")
    views = read_rows(owners["05e"] / "review_views/review_views.jsonl")
    derived = [read_object(owners["05e"] / "records/activity.json"), *edges, *diagnostics, *views]
    validate_record_bundle([*source, inventories["05d"], completions["05d"]], schema)
    validate_record_bundle([*source, *derived, inventories["05e"], completions["05e"]], schema)
    for stage, rows in (("05d", source), ("05e", derived)):
        if (
            semantic_bundle_digest(rows)
            != binding["accepted_component_semantic_digests"][f"task{stage}"]
        ):
            raise ValueError(f"{stage} accepted semantic digest differs")
    components = [
        _component(root, owners[stage], inventories[stage]["files"], name, role, field, rows)
        for stage, name, role, field, rows in [
            (
                "05d",
                "inventory/source_records.jsonl",
                "source_records",
                "record_type_specific",
                source,
            ),
            ("05e", "graph/review_edges.jsonl", "edges", "edge_id", edges),
            (
                "05e",
                "diagnostics/individual_diagnostics.jsonl",
                "graph_diagnostics",
                "diagnostic_id",
                diagnostics,
            ),
            ("05e", "review_views/review_views.jsonl", "graph_views", "view_id", views),
        ]
    ]
    selected = {item["path"] for item in components}
    for stage, owner in owners.items():
        for item in inventories[stage]["files"]:
            if (owner / item["path"]).relative_to(root).as_posix() in selected:
                continue
            metadata = read_object(owner / item["path"])
            components.append(
                _component(
                    root,
                    owner,
                    inventories[stage]["files"],
                    item["path"],
                    f"task{stage}_" + Path(item["path"]).stem,
                    "singleton",
                    [metadata],
                )
            )
    return SourceGraphInputs(source, edges, diagnostics, views, components)


def _associations(binding: JsonObject, controls: dict[str, JsonObject]) -> JsonObject:
    """Reject individually valid seals belonging to different accepted candidates."""
    acceptance = controls["acceptance_pointer"]
    if acceptance != binding["task05g_acceptance"]:
        raise ValueError("05G acceptance pointer differs from frozen acceptance")
    handoff = controls["task05h_handoff"]
    require_fields(
        handoff,
        {
            "candidate_id": binding["task05g_candidate_id"],
            "semantic_digest": binding["task05g_semantic_digest"],
        },
        "05H handoff",
    )
    expected_deps = [
        {k: v for k, v in item.items() if k != "size_bytes"} for item in binding["dependencies"]
    ]
    if handoff["dependencies"] != expected_deps:
        raise ValueError("05H handoff dependency associations differ")
    for name, value in controls.items():
        if "bindings" in value and value["bindings"].get("dependencies") != expected_deps:
            raise ValueError(f"05G checkpoint dependency associations differ: {name}")
    for stage in ("candidate", "comparison"):
        completion = controls[f"{stage}_root_completion"]
        if handoff[f"{stage}_checkpoint_id"] != completion["checkpoint_id"] or handoff[
            f"{stage}_root"
        ] != str(Path(binding["seals"][f"{stage}_root_completion"]["path"]).parent):
            raise ValueError(f"05G {stage} handoff association differs")
    if acceptance["finalization_checkpoint_id"] != controls["finalization_completion"][
        "checkpoint_id"
    ] or acceptance["finalization_root"] != str(
        Path(binding["seals"]["finalization_completion"]["path"]).parent
    ):
        raise ValueError("05G acceptance finalization association differs")
    return handoff


def _review_provenance(
    root: Path,
    dependencies: dict[str, JsonObject],
    acceptance: JsonObject,
) -> tuple[JsonObject, list[JsonObject]]:
    """Read exact 06H coverage provenance and its seals without mutating caller state."""
    records = contained_path(root, dependencies["task06h_handoff"]["path"]).parent
    accepted = acceptance["bindings"]
    inventory = _closed_records(
        records,
        accepted["review_completion_sha256"],
        {
            "finalization_id": accepted["finalization_id"],
            "status": "complete_pending_explicit_acceptance",
        },
    )
    candidate = read_object(records / "finalization_candidate.json")
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
        "06H finalization candidate",
    )
    provenance = {
        "decision_provenance": read_rows(records / "decision_provenance.jsonl"),
        "sample_stratum_confirmations": read_object(records / "sample_stratum_confirmations.json"),
    }
    references = [
        {
            "role": "task06h_" + Path(item["path"]).stem,
            "authority": "artifact_root",
            "identity": accepted["finalization_id"],
            "path": (records / item["path"]).relative_to(root).as_posix(),
            "size_bytes": item["byte_size"],
            "sha256": item["sha256"],
        }
        for item in inventory["files"]
    ]
    return provenance, references


def _reference_outcomes(
    root: Path, candidate: Path, inventory: list[JsonObject], accepted_digest: str
) -> tuple[dict[str, list[JsonObject]], list[JsonObject], str]:
    """Verify the whole accepted replay, retaining only its three release components."""
    files = {
        "outcomes": "outcomes/reference_outcomes.jsonl",
        "links": "links/draft_eir_links.jsonl",
        "diagnostics": "diagnostics/individual_diagnostics.jsonl",
        "forward": "indexes/mention_to_link.jsonl",
        "reverse": "indexes/target_to_links.jsonl",
    }
    result = {key: read_rows(candidate / name) for key, name in files.items()}
    reference_digest = canonical_json_sha256(
        {**result, "census": read_object(candidate / "diagnostics/rule_census.json")}
    )
    if reference_digest != accepted_digest:
        raise ValueError("05G accepted semantic digest differs")
    components: list[JsonObject] = []
    for key, role, field in (
        ("outcomes", "outcomes", "mention_id"),
        ("links", "links", "link_id"),
        ("diagnostics", "reference_diagnostics", "diagnostic_id"),
    ):
        components.append(
            _component(
                root,
                candidate,
                inventory,
                files[key],
                role,
                field,
                result[key],
            )
        )
    return result, components, reference_digest


def _inherited_limitations(
    binding: JsonObject,
    root: Path,
    dependencies: dict[str, JsonObject],
    handoff: JsonObject,
) -> tuple[JsonObject, list[JsonObject]]:
    """Collect the accepted warnings, coverage, and their exact review provenance."""
    inherited = read_object(contained_path(root, dependencies["task06h_handoff"]["path"]))
    if (
        handoff["accepted_task06h_handoff"] != inherited
        or inherited["final_f1_warning_binding"] != binding["inherited_warning_binding"]
    ):
        raise ValueError("06H handoff or Final F1 warning inheritance differs")
    limitations = {
        "coverage": binding["coverage"],
        "final_f1_warning_binding": binding["inherited_warning_binding"],
        **{
            key: read_object(contained_path(root, dependencies[role]["path"]))
            for key, role in (
                ("registry", "task06h_registry"),
                ("target_limitations", "task06h_target_limitations"),
                ("toc_review_decisions", "task06h_toc_merge"),
                ("acceptance", "task06h_acceptance"),
            )
        },
    }
    graph_owner = contained_path(root, dependencies["task05e_completion"]["path"]).parent.parent
    limitations["graph_review_census"] = read_object(graph_owner / "diagnostics/review_census.json")
    provenance, review_dependencies = _review_provenance(
        root, dependencies, limitations["acceptance"]
    )
    limitations.update(provenance)
    return limitations, review_dependencies


def load_release_inputs(binding: JsonObject, artifact_root: Path) -> ReleaseInputs:
    """Load only the explicitly frozen accepted JSON components; never write state."""
    root = artifact_root.resolve()
    controls = {
        name: (
            _checkpoint(root, ref)
            if name.endswith("completion")
            else read_object(verify_reference(root, ref))
        )
        for name, ref in binding["seals"].items()
    }
    handoff = _associations(binding, controls)
    dependencies = {item["role"]: item for item in binding["dependencies"]}
    if len(dependencies) != len(binding["dependencies"]):
        raise ValueError("duplicate accepted dependency role")
    for ref in [*binding["dependencies"], *binding["source_graph_closure_metadata"]]:
        verify_reference(root, ref)
    source_graph = _source_graph(binding, root, dependencies)
    references, reference_components, reference_digest = _reference_outcomes(
        root,
        contained_path(root, handoff["candidate_root"]),
        controls["candidate_root_completion"]["inventory"],
        binding["task05g_semantic_digest"],
    )
    components = [*source_graph.components, *reference_components]
    limitations, review_dependencies = _inherited_limitations(binding, root, dependencies, handoff)
    finalization_root = Path(binding["seals"]["finalization_completion"]["path"]).parent
    review_dependencies.extend(
        {
            "role": "task05g_" + Path(item["path"]).stem,
            "authority": "artifact_root",
            "identity": controls["finalization_completion"]["checkpoint_id"],
            **item,
            "path": (finalization_root / item["path"]).as_posix(),
        }
        for item in controls["finalization_completion"]["inventory"]
    )
    inputs = ReleaseInputs(
        source_records=source_graph.source_records,
        edges=source_graph.edges,
        graph_diagnostics=source_graph.diagnostics,
        graph_views=source_graph.views,
        outcomes=references["outcomes"],
        links=references["links"],
        reference_diagnostics=references["diagnostics"],
        dependencies=[
            *binding["dependencies"],
            *[
                {"role": name, "authority": "artifact_root", **ref}
                for name, ref in binding["seals"].items()
            ],
            *binding["source_graph_closure_metadata"],
            *review_dependencies,
        ],
        components=components,
        limitations=limitations,
        handoff=handoff,
        accounting={},
        semantic_digest="",
    )
    accounting = validate_composition(inputs)
    digest = canonical_json_sha256(
        {
            "components": components,
            "accounting": accounting,
            "limitations": limitations,
            "upstream_semantic_digests": binding["accepted_component_semantic_digests"],
            "reference_semantic_digest": reference_digest,
        }
    )
    return replace(inputs, accounting=accounting, semantic_digest=digest)
