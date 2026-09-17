"""Selected mechanical resources for Task 05G, derived from accepted seals."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from er_commons.response_inventory.reference_replay_inputs import (
    _dependency,
    contained,
    inventory_entries,
    read_object,
    read_rows,
    require_fields,
    sealed_path,
)

JsonObject = dict[str, Any]


def _correspondence(root: Path, digest: str) -> dict[str, JsonObject]:
    """Verify the compact correspondence seal without scanning any payload tree."""
    completion = read_object(root / "completion.json", digest=digest)
    require_fields(
        completion, {"status": "complete", "completion_last": True}, "06G correspondence"
    )
    inventory = read_object(sealed_path(root, completion["artifact_inventory"], compact=True))
    entries = inventory_entries(inventory)
    if set(entries) != {
        "provenance.json",
        "source_correspondence.json",
        "target_correspondence.json",
        "review_correspondence.json",
    }:
        raise ValueError("06G correspondence inventory differs")
    return {
        name: read_object(sealed_path(root, entry, compact=True)) for name, entry in entries.items()
    }


def _source_membership(rows: list[JsonObject], registry: JsonObject) -> None:
    """Require the accepted logical/physical/candidate correspondence for all sources."""
    if len(rows) != 35 or len({r["logical_source_id"] for r in rows}) != 35:
        raise ValueError("06G source membership differs")
    if Counter(r["change_class"] for r in rows) != {
        "preserved_semantic": 32,
        "repaired_structure": 2,
        "substituted_new_source": 1,
    }:
        raise ValueError("06G source change classes differ")
    registered = {r["logical_source_id"]: r for r in registry["entries"]}
    for row in rows:
        expected = {
            "selected_source_id": row["selected_physical_source_id"],
            "selected_candidate_id": row["replacement_candidate_id"],
            "change_class": row["change_class"],
        }
        require_fields(
            registered.get(row["logical_source_id"], {}), expected, "06G/06H source membership"
        )
    final = next(r for r in rows if r["logical_source_id"] == "deir_appendix_f1")
    require_fields(
        final,
        {"selected_physical_source_id": "feir_appendix_f1", "semantic_equivalence": False},
        "Final F1 source substitution",
    )


def _target_mapping(
    outcomes: list[JsonObject],
    rows: list[JsonObject],
    sources: list[JsonObject],
    targets: JsonObject,
) -> JsonObject:
    """Normalize namespaces only for suffixes whose sealed comparison permits reuse."""
    by_suffix: dict[str, set[str]] = {}
    for row in rows:
        target = row["target_id"]
        by_suffix.setdefault(target.split("/", 1)[-1], set()).add(target)
    changed = {r["logical_source_id"]: r for r in targets["changed_sources"]}
    source_map = {r["logical_source_id"]: r for r in sources}
    old_ids: set[str] = set()
    for row in outcomes:
        if row.get("target_id"):
            old_ids.add(row["target_id"])
        for field in (
            "global_candidate_target_ids",
            "source_candidate_target_ids",
            "compatible_target_ids",
        ):
            old_ids.update(row.get(field, []))
    mapping = []
    for old in sorted(old_ids):
        suffix = old.split("/", 1)[-1]
        parts = suffix.split("/")
        if len(parts) < 2:
            continue
        source = source_map.get(parts[1])
        if source is None or source["change_class"] == "substituted_new_source":
            continue
        changes = changed.get(parts[1], {})
        removed = {r["target"]["target_id"] for r in changes.get("removed", [])}
        options = by_suffix.get(suffix, set())
        if suffix not in removed and len(options) == 1:
            mapping.append(
                {
                    "baseline_target_id": old,
                    "selected_target_id": next(iter(options)),
                    "classification": "namespace_only",
                }
            )
    added: set[str] = set()
    for source in targets["changed_sources"]:
        for row in source["added"]:
            if not row.get("authorizations"):
                raise ValueError("06G added target lacks accepted owner authorization")
            options = by_suffix.get(row["target"]["target_id"], set())
            if len(options) != 1:
                raise ValueError("06G added target is missing or ambiguous in selected index")
            added.update(options)
    return {
        "sources": sources,
        "targets": targets,
        "target_mapping": mapping,
        "authorized_added_target_ids": sorted(added),
    }


def _main_section_children(
    publication: Path, eligible: list[JsonObject]
) -> dict[str, tuple[str, ...]]:
    """Read main-document section ancestry without admitting non-section children."""
    main = next(r for r in eligible if r["source_id"] == "deir_main")
    sections = [r for r in main["target_records_ref"] if Path(r["path"]).name == "sections.jsonl"]
    if len(sections) != 1:
        raise ValueError("06G selected main must have exactly one section stream")
    section_rows = read_rows(sealed_path(publication, sections[0], compact=False))
    section_ids = {r["id"] for r in section_rows}
    if len(section_ids) != len(section_rows):
        raise ValueError("06G selected main section IDs conflict")
    return {
        r["id"]: tuple(x for x in r.get("ordered_child_ids", []) if x in section_ids)
        for r in section_rows
    }


def _load_selected_index(
    publication: Path, artifact_root: Path, handoff: JsonObject, checkpoint: JsonObject
) -> tuple[Path, JsonObject, list[JsonObject]]:
    """Verify handoff/checkpoint agreement before reading the selected target index."""
    index_ref = handoff["index_completion_ref"]
    checkpoint_index = checkpoint["outputs"]["target_index_completion_ref"]
    index_path = sealed_path(publication, index_ref, compact=False)
    if index_path != contained(artifact_root, checkpoint_index["path"]) or any(
        index_ref[k] != checkpoint_index[k] for k in ("sha256", "byte_size")
    ):
        raise ValueError("selected target index root differs from sealed checkpoint")
    # Large completion contains embedded target rows. Its existing digest is trusted;
    # its compact identity/inventory seals and actual selected payload sizes are checked.
    index = read_object(index_path)
    require_fields(
        index,
        {"index_id": handoff["index_id"], "status": "complete", "completion_last": True},
        "06G target index",
    )
    if index_ref["sha256"] != handoff["identity_preimage"]["index_completion_sha256"]:
        raise ValueError("06G index digest differs from mechanical identity")
    inventory = read_object(sealed_path(publication, index["artifact_inventory"], compact=True))
    entries = inventory_entries(inventory)
    target_ref = index["entries_ref"]
    target_path = sealed_path(publication, target_ref, compact=False)
    recorded = entries.get("target_index.jsonl")
    if recorded is None or any(recorded[k] != target_ref[k] for k in ("sha256", "byte_size")):
        raise ValueError("06G target payload inventory differs")
    rows = read_rows(target_path)
    if len(rows) != index["entry_count"]:
        raise ValueError("06G target index row count differs")
    return index_path, index, rows


def load_mechanical_inputs(
    spec: JsonObject,
    artifact_root: Path,
    review: JsonObject,
    outcomes: list[JsonObject],
    *,
    qualification_sources: set[str] | None = None,
    header_sources: set[str] | None = None,
) -> JsonObject:
    """Follow sealed correspondence to explicit selected index and document roots."""
    accepted = review["acceptance"]["bindings"]
    if (
        spec["readiness_sha256"] != accepted["readiness_sha256"]
        or spec["correspondence_completion_sha256"] != accepted["correspondence_completion_sha256"]
    ):
        raise ValueError("06G mechanical chain differs from accepted 06H")
    readiness_root = contained(artifact_root, spec["readiness_root"])
    completion = read_object(
        readiness_root / "completion.json", digest=spec["readiness_completion_sha256"]
    )
    require_fields(completion, {"status": "complete"}, "06G readiness completion")
    if completion["readiness"]["sha256"] != spec["readiness_sha256"]:
        raise ValueError("06G readiness completion binding differs")
    readiness = read_object(sealed_path(readiness_root, completion["readiness"], compact=True))
    require_fields(
        readiness,
        {"status": "ready_for_review", "inventory_sha256": completion["inventory_sha256"]},
        "06G readiness",
    )
    correspondence_root = contained(artifact_root, spec["correspondence_root"])
    bound = _correspondence(correspondence_root, spec["correspondence_completion_sha256"])
    provenance = bound["provenance.json"]
    sources = bound["source_correspondence.json"]["rows"]
    _source_membership(sources, review["registry"])
    checkpoint = read_object(
        sealed_path(artifact_root, provenance["replacement_handoff_checkpoint"], compact=True)
    )
    require_fields(
        checkpoint,
        {
            "derived_id": accepted["mechanical_handoff_id"],
            "recomputed_id": accepted["mechanical_handoff_id"],
            "verified": True,
        },
        "06G handoff checkpoint",
    )
    handoff_ref = checkpoint["outputs"]["handoff_completion_ref"]
    if handoff_ref["sha256"] != spec["handoff_completion_sha256"]:
        raise ValueError("06G handoff completion binding differs")
    handoff_path = sealed_path(artifact_root, handoff_ref, compact=True)
    handoff = read_object(handoff_path)
    require_fields(
        handoff,
        {
            "handoff_id": accepted["mechanical_handoff_id"],
            "status": "ready",
            "completion_last": True,
            "blocking_reasons": [],
        },
        "06G handoff",
    )
    publication = contained(artifact_root, spec["publication_root"])
    index_path, index, rows = _load_selected_index(publication, artifact_root, handoff, checkpoint)
    index_ref = handoff["index_completion_ref"]
    eligible = index["eligible_candidates"]
    expected = {(r["selected_physical_source_id"], r["replacement_candidate_id"]) for r in sources}
    if len(eligible) != 35 or {(r["source_id"], r["candidate_id"]) for r in eligible} != expected:
        raise ValueError("06G index selected candidates differ")
    children = _main_section_children(publication, eligible)
    catalog_path = contained(artifact_root, spec["catalog"]["path"])
    catalog = read_object(catalog_path, digest=spec["catalog"]["sha256"])
    correspondence = _target_mapping(outcomes, rows, sources, bound["target_correspondence.json"])
    if qualification_sources:
        rows.extend(_qualified_inner_rows(publication, eligible, qualification_sources))
    if header_sources:
        evidence = _qualified_header_evidence(publication, eligible, header_sources)
        rows = [
            {**row, "header_qualification": evidence[row["target_id"]]}
            if row["target_id"] in evidence
            else row
            for row in rows
        ]
    document_targets = index["document_targets"]
    candidate_to_target = {r["candidate_id"]: r["target_id"] for r in document_targets}
    if len(candidate_to_target) != 35 or set(candidate_to_target) != {
        r["replacement_candidate_id"] for r in sources
    }:
        raise ValueError("06G document target candidate membership differs")
    correspondence["document_target_mapping"] = candidate_to_target
    dependencies = [
        _dependency(
            "task06g_handoff",
            handoff_path,
            artifact_root,
            handoff["handoff_id"],
            handoff_ref["sha256"],
        ),
        _dependency(
            "task06g_target_index",
            index_path,
            artifact_root,
            index["index_id"],
            index_ref["sha256"],
        ),
        _dependency(
            "task06g_source_correspondence",
            correspondence_root / "completion.json",
            artifact_root,
            "er_commons.task06g.correspondence_completion.v1",
            spec["correspondence_completion_sha256"],
        ),
        _dependency(
            "source_family_catalog",
            catalog_path,
            artifact_root,
            "source_family_catalog",
            spec["catalog"]["sha256"],
        ),
    ]
    return {
        "target_rows": rows,
        "direct_section_children": children,
        "catalog": catalog,
        "correspondence": correspondence,
        "dependencies": dependencies,
    }


def _canonical_streams(
    publication: Path, candidate: JsonObject, names: tuple[str, ...]
) -> dict[str, list[JsonObject]]:
    """Hash the compact inventory, then size-check only requested canonical streams.

    Payload hashes are inherited from the accepted inventory. Do not expand this
    reader into a tree scan or rehash large canonical payloads during replay.
    """
    inventory_path = sealed_path(publication, candidate["candidate_inventory_ref"], compact=True)
    inventory = inventory_entries(read_object(inventory_path))
    candidate_root = inventory_path.parent.parent
    streams = {}
    for name in names:
        relative = f"content/canonical/{name}.jsonl"
        if relative not in inventory:
            raise ValueError(
                f"candidate {candidate['candidate_id']} lacks canonical stream: {relative}"
            )
        streams[name] = read_rows(sealed_path(candidate_root, inventory[relative], compact=False))
    return streams


def _qualified_inner_rows(
    publication: Path, eligible: list[JsonObject], sources: set[str]
) -> list[JsonObject]:
    """Derive consumer-only aliases from size-checked sealed canonical record streams."""
    from er_commons.response_inventory.reference_replay_qualification import (
        qualify_supplemental_aliases,
    )

    result = []
    for candidate in eligible:
        if candidate["source_id"] not in sources:
            continue
        streams = _canonical_streams(
            publication, candidate, ("blocks", "tables", "pages", "sections")
        )
        qualified = qualify_supplemental_aliases(
            source_id=candidate["source_id"],
            source_ordinal=candidate["source_ordinal"],
            candidate_id=candidate["candidate_id"],
            **streams,
        )
        for row in qualified:
            row["qualification_input_inventory"] = candidate["candidate_inventory_ref"]
        result.extend(qualified)
    return result


def _qualified_header_evidence(
    publication: Path, eligible: list[JsonObject], sources: set[str]
) -> dict[str, JsonObject]:
    """Bind header qualification to selected, inventory-verified canonical streams."""
    from er_commons.response_inventory.reference_replay_headers import qualify_section_headers

    result: dict[str, JsonObject] = {}
    for candidate in eligible:
        if candidate["source_id"] not in sources:
            continue
        streams = _canonical_streams(publication, candidate, ("blocks", "pages", "sections"))
        evidence = qualify_section_headers(
            source_id=candidate["source_id"], candidate_id=candidate["candidate_id"], **streams
        )
        for target, row in evidence.items():
            if target in result:
                raise ValueError(f"duplicate header qualification target: {target}")
            result[target] = {
                **row,
                "qualification_input_inventory": candidate["candidate_inventory_ref"],
            }
    return result
