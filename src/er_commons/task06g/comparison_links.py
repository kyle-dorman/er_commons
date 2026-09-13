"""Source-free link population loading and old/new comparison for Task 06G."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import cast

from er_commons.collection_processing.authority_refs import CollectionArtifactResolver
from er_commons.task06g.core import JsonObject, load_object, reference, verify_reference

NAVIGATION_SOURCES = frozenset({"deir_appendix_a", "deir_main", "deir_appendix_k2_part_1_of_5"})
ORDINARY_PATH = "content/canonical/cross_references.jsonl"
NAVIGATION_PATH = "content/navigation/decisions.jsonl"
TASK04C_LINK_ROOT = Path(
    "pipelines/brisbane_baylands/task_04_navigation_overlay/"
    "navlinkv1-978dbf3f3363eeb4265c75f60efd80bb3995234586e1821f060fe70a9c11bed4"
)


def _objects(value: object, label: str) -> list[JsonObject]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"{label} must be an array of objects")
    return cast(list[JsonObject], value)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be nonempty text")
    return value


def _object(value: object, label: str) -> JsonObject:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return cast(JsonObject, value)


def _jsonl(path: Path) -> list[JsonObject]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL row must be an object: {path}:{line_number}")
        rows.append(value)
    return rows


def _inventory_entry(inventory: JsonObject, relative: str, label: str) -> JsonObject:
    matches = [
        row
        for row in _objects(inventory.get("files"), f"{label} inventory")
        if row.get("path") == relative
    ]
    if len(matches) != 1:
        raise ValueError(f"{label} inventory must bind {relative} exactly once")
    return matches[0]


def _verified_inventory_file(
    *, root: Path, inventory: JsonObject, relative: str, label: str
) -> tuple[Path, JsonObject]:
    entry = _inventory_entry(inventory, relative, label)
    path = root / relative
    observed = reference(path, root=root)
    if observed["sha256"] != entry.get("sha256") or observed["byte_size"] != entry.get("byte_size"):
        raise ValueError(f"{label} artifact differs from its candidate inventory: {relative}")
    return path, observed


def load_collection_link_evidence(
    *,
    data_root: Path,
    collection_root: Path,
    bundle: JsonObject,
    label: str,
    document_input_root: Path | None = None,
) -> tuple[JsonObject, JsonObject]:
    """Load complete ordinary and accepted navigation populations through inventories."""
    accounting = bundle.get("accounting")
    if not isinstance(accounting, dict):
        raise ValueError(f"{label} accounting must be an object")
    ordinary: list[JsonObject] = []
    navigation: list[JsonObject] = []
    provenance: list[JsonObject] = []
    for row in _objects(accounting.get("rows"), f"{label} accounting rows"):
        source_id = _text(row.get("source_id"), f"{label} source_id")
        inventory_ref = _object(
            row.get("candidate_inventory_ref"),
            f"{label} {source_id} candidate inventory ref",
        )
        if document_input_root is None:
            inventory_path = verify_reference(inventory_ref, root=collection_root)
        else:
            resolver = CollectionArtifactResolver(
                document_input_root=document_input_root,
                collection_output_root=collection_root,
            )
            inventory_path = resolver.resolve(
                inventory_ref, expected_authority="document_input_root"
            )
        candidate_root = inventory_path.parent.parent
        inventory = load_object(inventory_path)
        provenance.append(
            {
                "authority": "artifact_root",
                "role": "candidate_inventory",
                "source_id": source_id,
                **reference(inventory_path, root=data_root),
            }
        )
        paths = [ORDINARY_PATH]
        if source_id in NAVIGATION_SOURCES:
            paths.append(NAVIGATION_PATH)
        for relative in paths:
            path, observed = _verified_inventory_file(
                root=candidate_root,
                inventory=inventory,
                relative=relative,
                label=f"{label} {source_id}",
            )
            rows = _jsonl(path)
            if relative == ORDINARY_PATH:
                ordinary.extend(rows)
            else:
                navigation.extend(rows)
            provenance.append(
                {
                    "authority": "artifact_root",
                    "role": (
                        "ordinary_references"
                        if relative == ORDINARY_PATH
                        else "navigation_decisions"
                    ),
                    "source_id": source_id,
                    **reference(path, root=data_root),
                }
            )
    return {"ordinary": ordinary, "navigation": navigation}, {"artifacts": provenance}


def load_task04c_inherited_targets(*, data_root: Path) -> tuple[JsonObject, JsonObject]:
    """Load the exact accepted 28-link Task 04C baseline through completion/inventory."""
    root = data_root / TASK04C_LINK_ROOT
    completion_path = root / "records/completion_record.json"
    inventory_path = root / "records/artifact_inventory.json"
    completion = load_object(completion_path)
    inventory = load_object(inventory_path)
    inventory_ref = reference(inventory_path, root=data_root)
    if (
        completion.get("status") != "complete"
        or completion.get("artifact_inventory_sha256") != inventory_ref["sha256"]
        or completion.get("link_view_id") != root.name
    ):
        raise ValueError("accepted Task 04C completion or inventory binding differs")
    path, link_ref = _verified_inventory_file(
        root=root,
        inventory=inventory,
        relative="link_overlay.jsonl",
        label="Task 04C",
    )
    rows = _jsonl(path)
    targets = {
        _text(row.get("source_toc_entry_id"), "Task 04C navigation entry"): _relative_id(
            row.get("target_id"), "Task 04C navigation target"
        )
        for row in rows
    }
    if len(rows) != 28 or len(targets) != 28:
        raise ValueError("accepted Task 04C link overlay must contain 28 unique links")
    provenance = {
        "completion": {
            "authority": "artifact_root",
            **reference(completion_path, root=data_root),
        },
        "inventory": {"authority": "artifact_root", **inventory_ref},
        "link_overlay": {"authority": "artifact_root", **reference(path, root=data_root)},
    }
    if provenance["link_overlay"]["sha256"] != link_ref["sha256"]:
        raise ValueError("Task 04C link overlay reference differs")
    return targets, provenance


def _relative_id(value: object, label: str) -> str:
    text = _text(value, label)
    _, separator, relative = text.partition("/")
    if not separator or not relative:
        raise ValueError(f"{label} lacks an extraction namespace")
    return relative


def _ordinary_key(row: JsonObject) -> str:
    return _relative_id(row.get("id"), "ordinary reference ID")


def _ordinary_outcome(row: JsonObject) -> JsonObject:
    candidates = []
    for candidate in _objects(row.get("candidates"), "ordinary candidates"):
        candidates.append(
            {
                "target_record_id": _relative_id(
                    candidate.get("target_record_id"), "ordinary target"
                ),
                "target_type": candidate.get("target_type"),
            }
        )
    family = row.get("cross_document_evidence")
    family_semantics = None
    if isinstance(family, dict):
        family_semantics = {
            key: family.get(key)
            for key in (
                "intended_target_source_ids",
                "matched_alias",
                "source_family_id",
                "traversal_rule",
            )
        }
    return {
        "resolution_status": row.get("resolution_status"),
        "unresolved_reason": row.get("unresolved_reason"),
        "candidates": sorted(candidates, key=lambda item: str(item["target_record_id"])),
        "source_family_semantics": family_semantics,
    }


def _family_digest(row: JsonObject | None) -> object:
    if row is None or not isinstance(row.get("cross_document_evidence"), dict):
        return None
    return row["cross_document_evidence"].get("catalog_sha256")


def _source_from_relative(value: str) -> str | None:
    parts = value.split("/")
    return parts[1] if len(parts) >= 3 else None


def _authorized_owners(
    *,
    key: str,
    old: JsonObject | None,
    new: JsonObject | None,
    authorizations: JsonObject,
) -> list[str]:
    owners = set()
    if old is not None and new is not None:
        source_id = _source_from_relative(key)
        old_outcome = _ordinary_outcome(old)
        new_outcome = _ordinary_outcome(new)
        if (
            source_id == "deir_main"
            and old.get("mention_class") == "figure"
            and new.get("mention_class") == "figure"
            and old_outcome
            == {
                "resolution_status": "unresolved",
                "unresolved_reason": "accepted_target_type_unavailable",
                "candidates": [],
                "source_family_semantics": None,
            }
            and new_outcome
            == {
                "resolution_status": "unresolved",
                "unresolved_reason": "no_local_alias",
                "candidates": [],
                "source_family_semantics": None,
            }
        ):
            owners.add("task06f")
    mention_authorities = authorizations.get("final_f1_mentions")
    if isinstance(mention_authorities, dict):
        mention = mention_authorities.get(key)
        if isinstance(mention, dict) and isinstance(mention.get("owner"), str):
            owners.add(mention["owner"])
    target_authorities = authorizations.get("targets")
    if not isinstance(target_authorities, dict):
        raise ValueError("target authorizations must be an object")
    for row in (old, new):
        if row is None:
            continue
        for candidate in _objects(row.get("candidates"), "ordinary candidates"):
            target = candidate.get("target_record_id")
            if isinstance(target, str):
                relative = _relative_id(target, "ordinary target")
                rows = target_authorities.get(relative, [])
                for authority in _objects(rows, f"target authorities for {relative}"):
                    if isinstance(authority.get("owner"), str):
                        owners.add(authority["owner"])
    return sorted(owners)


def compare_link_populations(
    *, baseline: JsonObject, replacement: JsonObject, authorizations: JsonObject
) -> JsonObject:
    """Compare all ordinary and accepted navigation rows and reject unowned changes."""
    old_rows = _objects(baseline.get("ordinary"), "baseline ordinary references")
    new_rows = _objects(replacement.get("ordinary"), "replacement ordinary references")
    if len(old_rows) != 5_088:
        raise ValueError("baseline ordinary-reference population must contain 5,088 rows")
    old = {_ordinary_key(row): row for row in old_rows}
    new = {_ordinary_key(row): row for row in new_rows}
    if len(old) != len(old_rows) or len(new) != len(new_rows):
        raise ValueError("ordinary-reference keys must be unique")
    ordinary_changes = []
    source_family_changes = []
    ordinary_counts: Counter[str] = Counter()
    for key in sorted(set(old) | set(new)):
        old_row = old.get(key)
        new_row = new.get(key)
        old_outcome = _ordinary_outcome(old_row) if old_row is not None else None
        new_outcome = _ordinary_outcome(new_row) if new_row is not None else None
        if old_outcome == new_outcome:
            classification = "unchanged"
            owners = ["task06g_no_change"]
        else:
            classification = (
                "removed" if new_row is None else "added" if old_row is None else "changed"
            )
            owners = _authorized_owners(
                key=key,
                old=old_row,
                new=new_row,
                authorizations=authorizations,
            )
            if not owners:
                raise ValueError(f"unowned ordinary-reference delta: {key}")
        ordinary_counts[classification] += 1
        ordinary_changes.append(
            {
                "mention_key": key,
                "classification": classification,
                "owners": owners,
                "baseline": old_outcome,
                "replacement": new_outcome,
            }
        )
        old_family = _family_digest(old_row)
        new_family = _family_digest(new_row)
        if old_family is not None or new_family is not None:
            source_family_changes.append(
                {
                    "mention_key": key,
                    "classification": (
                        "unchanged" if old_family == new_family else "catalog_rebound"
                    ),
                    "owner": ("task06g_no_change" if old_family == new_family else "task06c"),
                    "baseline_catalog_sha256": old_family,
                    "replacement_catalog_sha256": new_family,
                }
            )

    old_nav_rows = _objects(baseline.get("navigation"), "baseline navigation decisions")
    new_nav_rows = _objects(replacement.get("navigation"), "replacement navigation decisions")
    if len(old_nav_rows) != 560 or len(new_nav_rows) != 560:
        raise ValueError("navigation comparison requires exactly 560 old and new claims")

    def nav_index(rows: list[JsonObject], label: str) -> dict[tuple[str, str], JsonObject]:
        result = {
            (
                _text(row.get("source_id"), f"{label} navigation source"),
                _text(row.get("navigation_entry_id"), f"{label} navigation entry"),
            ): row
            for row in rows
        }
        if len(result) != len(rows):
            raise ValueError(f"duplicate {label} navigation claims")
        return result

    old_nav = nav_index(old_nav_rows, "baseline")
    new_nav = nav_index(new_nav_rows, "replacement")
    if set(old_nav) != set(new_nav):
        raise ValueError("navigation claim identities changed")
    inherited = baseline.get("task04c_baseline_targets")
    if not isinstance(inherited, dict) or len(inherited) != 28:
        raise ValueError("Task 04C inherited navigation target set must contain 28 rows")
    navigation_changes = []
    navigation_counts: Counter[str] = Counter()
    for nav_key in sorted(old_nav):

        def outcome(row: JsonObject) -> JsonObject:
            return {
                "outcome": row.get("outcome"),
                "target_ids": sorted(
                    _relative_id(item, "navigation target")
                    for item in cast(list[object], row.get("candidate_target_ids", []))
                ),
                "match_basis": row.get("match_basis"),
            }

        old_outcome = outcome(old_nav[nav_key])
        new_outcome = outcome(new_nav[nav_key])
        classification = "unchanged" if old_outcome == new_outcome else "changed"
        if classification == "unchanged":
            owners = ["task06g_no_change"]
        else:
            if nav_key[1] in inherited and new_outcome["outcome"] != "resolved_unique":
                raise ValueError(f"inherited Task 04C navigation link lost: {nav_key[1]}")
            target_authorities = _object(authorizations.get("targets"), "target authorizations")
            owners = sorted(
                {
                    str(authority["owner"])
                    for target in [*old_outcome["target_ids"], *new_outcome["target_ids"]]
                    for authority in _objects(
                        target_authorities.get(target, []),
                        f"navigation target authorities for {target}",
                    )
                    if isinstance(authority.get("owner"), str)
                }
            )
            if not owners:
                raise ValueError(f"unowned navigation delta: {nav_key[0]}/{nav_key[1]}")
        navigation_counts[classification] += 1
        navigation_changes.append(
            {
                "source_id": nav_key[0],
                "navigation_entry_id": nav_key[1],
                "classification": classification,
                "owners": owners,
                "baseline": old_outcome,
                "replacement": new_outcome,
            }
        )
    resolved = sum(row.get("outcome") == "resolved_unique" for row in new_nav_rows)
    unresolved = len(new_nav_rows) - resolved
    inherited_rows = []
    for entry_id, expected_target in sorted(inherited.items()):
        matches = [
            row
            for (source_id, candidate_entry), row in new_nav.items()
            if candidate_entry == entry_id
        ]
        if len(matches) != 1:
            raise ValueError(f"inherited Task 04C navigation claim missing: {entry_id}")
        actual = outcome(matches[0])
        targets = actual["target_ids"]
        if actual["outcome"] != "resolved_unique" or len(targets) != 1:
            raise ValueError(f"inherited Task 04C navigation link lost: {entry_id}")
        actual_target = targets[0]
        if actual_target != expected_target:
            target_authorities = _object(authorizations.get("targets"), "target authorizations")
            expected_owners = {
                str(row["owner"])
                for row in _objects(
                    target_authorities.get(str(expected_target), []),
                    "expected navigation target authorities",
                )
                if isinstance(row.get("owner"), str)
            }
            actual_owners = {
                str(row["owner"])
                for row in _objects(
                    target_authorities.get(actual_target, []),
                    "actual navigation target authorities",
                )
                if isinstance(row.get("owner"), str)
            }
            common_owners = expected_owners & actual_owners
            if not common_owners:
                raise ValueError(f"inherited Task 04C navigation target changed: {entry_id}")
        inherited_rows.append(
            {
                "navigation_entry_id": entry_id,
                "baseline_target_id": expected_target,
                "replacement_target_id": actual_target,
                "classification": (
                    "unchanged" if actual_target == expected_target else "mapped_repair"
                ),
                "owner": (
                    "task06g_no_change"
                    if actual_target == expected_target
                    else sorted(common_owners)[0]
                ),
            }
        )
    baseline_ordinary_unresolved = sum(
        row.get("resolution_status") != "resolved" for row in old_rows
    )
    replacement_ordinary_unresolved = sum(
        row.get("resolution_status") != "resolved" for row in new_rows
    )
    return {
        "schema_version": "er_commons.task06g.link_population_comparison.v1",
        "task04_status": "not_evaluated",
        "ordinary": {
            "baseline_population_count": len(old_rows),
            "replacement_population_count": len(new_rows),
            "counts": dict(sorted(ordinary_counts.items())),
            "baseline_unresolved_count": baseline_ordinary_unresolved,
            "replacement_unresolved_count": replacement_ordinary_unresolved,
            "unresolved_delta": (replacement_ordinary_unresolved - baseline_ordinary_unresolved),
            "rows": ordinary_changes,
        },
        "source_family_bindings": source_family_changes,
        "navigation": {
            "baseline_population_count": len(old_nav_rows),
            "replacement_population_count": len(new_nav_rows),
            "replacement_resolved_count": resolved,
            "replacement_unresolved_count": unresolved,
            "counts": dict(sorted(navigation_counts.items())),
            "rows": navigation_changes,
            "inherited_task04c_links": inherited_rows,
            "inherited_task04c_link_count": len(inherited_rows),
        },
    }


__all__ = [
    "compare_link_populations",
    "load_collection_link_evidence",
    "load_task04c_inherited_targets",
]
