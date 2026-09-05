from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from er_commons.artifact_io import canonical_json_sha256, json_bytes
from er_commons.navigation_overlay import materialization

REPO_ROOT = Path(__file__).parents[1]
SCHEMA_ROOT = REPO_ROOT / "benchmarks/er_bench/schemas/navigation_overlay/v1/gate_b"
ZERO_VIEW = "navsemanticv1-" + "0" * 64


def test_gate_b_script_requires_an_explicit_repo_root() -> None:
    """The command wrapper keeps checkout selection explicit."""
    script = REPO_ROOT / "scripts/materialize_task04c_gate_b.py"

    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--repo-root" in result.stdout


def test_materialization_changes_only_exact_block_and_table_entities() -> None:
    """Sections stay contextual while both accepted disagreement directions apply."""
    rows = [
        _decision(1, machine=False, human="toc", entities=["block-new", "table-new"]),
        _decision(2, machine=True, human="not_toc", entities=["block-old", "block-body"]),
    ]
    entities = {
        "block-new": _entity(
            "block-new",
            kind="block",
            navigation=False,
            section="section-a",
            pages={"page-1"},
        ),
        "table-new": _entity(
            "table-new",
            kind="table",
            navigation=False,
            section="section-a",
            pages={"page-1"},
        ),
        "block-old": _entity(
            "block-old",
            kind="block",
            navigation=True,
            section="section-b",
            pages={"page-2"},
        ),
        "block-body": _entity(
            "block-body",
            kind="block",
            navigation=False,
            section="section-b",
            pages={"page-2"},
        ),
    }

    applications, dispositions, sections = materialization._materialize_semantic_view(
        rows, entities, semantic_view_id=ZERO_VIEW
    )

    assert [row["application_outcome"] for row in applications] == [
        "applied_human_confirmed_navigation",
        "applied_human_rejected_machine_navigation",
    ]
    assert {row["entity_id"] for row in dispositions} == {
        "block-new",
        "table-new",
        "block-old",
    }
    assert {row["entity_kind"] for row in dispositions} == {"block", "table"}
    assert sections == {"section-a", "section-b"}
    assert all(row["original_machine_placement_preserved"] for row in dispositions)


def test_same_entity_evidence_is_aggregated_deterministically() -> None:
    """A spanning canonical entity receives one override with all page evidence."""
    rows = [
        _decision(2, machine=True, human="not_toc", entities=["block-old"]),
        _decision(1, machine=True, human="not_toc", entities=["block-old"]),
    ]
    entity = _entity(
        "block-old", kind="block", navigation=True, section="section-a", pages={"page-1", "page-2"}
    )

    applications, dispositions, _ = materialization._materialize_semantic_view(
        rows, {"block-old": entity}, semantic_view_id=ZERO_VIEW
    )

    assert len(dispositions) == 1
    assert dispositions[0]["decision_physical_pages"] == [1, 2]
    assert len(dispositions[0]["decision_entry_ids"]) == 2
    assert all(
        app["semantic_disposition_ids"] == [dispositions[0]["disposition_id"]]
        for app in applications
    )


def test_mixed_and_entityless_decisions_fail_closed() -> None:
    """Insufficient page evidence emits application records but no override."""
    mixed = _decision(1, machine=True, human="not_toc", entities=[])
    mixed["mapping_outcome"] = "mixed_page_insufficient_entity_evidence"
    entityless = _decision(2, machine=False, human="not_toc", entities=[])
    entityless["mapping_outcome"] = "no_existing_entity_evidence"

    applications, dispositions, _ = materialization._materialize_semantic_view(
        [mixed, entityless], {}, semantic_view_id=ZERO_VIEW
    )

    assert dispositions == []
    assert [row["application_outcome"] for row in applications] == [
        "unchanged_mixed_page_insufficient_entity_evidence",
        "unchanged_no_existing_entity_evidence",
    ]


def test_run_propagated_decision_keeps_provenance_and_uses_same_semantics() -> None:
    """An accepted run suffix is applied like a card while retaining its evidence."""
    row = _decision(2, machine=False, human="toc", entities=["block-new"])
    suffix = {
        "review_item_id": "reviewitem-" + "a" * 24,
        "run_start_page": 1,
        "run_end_page": 2,
    }
    row["c17_positive_suffix_evidence"] = suffix
    entity = _entity("block-new", kind="block", navigation=False, pages={"page-2"})

    applications, dispositions, _ = materialization._materialize_semantic_view(
        [row], {"block-new": entity}, semantic_view_id=ZERO_VIEW
    )

    assert applications[0]["application_outcome"] == "applied_human_confirmed_navigation"
    assert applications[0]["c17_positive_suffix_evidence"] == suffix
    assert dispositions[0]["effective_navigation"] is True


def test_missing_and_conflicting_entity_evidence_is_rejected() -> None:
    """Missing entities and opposing decisions cannot silently alter semantics."""
    missing = _decision(1, machine=False, human="toc", entities=["absent"])
    with pytest.raises(ValueError, match="missing canonical entity"):
        materialization._materialize_semantic_view([missing], {}, semantic_view_id=ZERO_VIEW)

    rows = [
        _decision(1, machine=False, human="toc", entities=["shared"]),
        _decision(2, machine=True, human="not_toc", entities=["shared"]),
    ]
    entities = {
        "shared": _entity("shared", kind="block", navigation=True, pages={"page-1", "page-2"})
    }
    with pytest.raises(ValueError, match="conflicting entity decisions"):
        materialization._materialize_semantic_view(rows, entities, semantic_view_id=ZERO_VIEW)


def test_identity_preimage_changes_are_rejected() -> None:
    """Both Gate A and Gate B IDs remain derived from their complete preimages."""
    preimage = {"input": "fixed"}
    identity = "navsemanticv1-" + canonical_json_sha256(preimage)
    materialization._require_derived_identity("navsemanticv1-", preimage, identity, "Gate B")

    with pytest.raises(ValueError, match="Gate B identity digest differs"):
        materialization._require_derived_identity(
            "navsemanticv1-", {"input": "changed"}, identity, "Gate B"
        )


def test_changed_canonical_byte_size_is_rejected_without_rehash(tmp_path: Path) -> None:
    """Gate B checks sealed sizes before parsing canonical records."""
    canonical = tmp_path / "blocks.jsonl"
    canonical.write_text("{}\n")

    with pytest.raises(ValueError, match="changed sealed size"):
        materialization._require_sealed_file_size(
            canonical, {"byte_size": canonical.stat().st_size + 1}, "fixture blocks"
        )


def test_entity_extending_to_unreviewed_page_is_rejected() -> None:
    """A page decision cannot reclassify the unreviewed part of a spanning entity."""
    with pytest.raises(ValueError, match="page membership mismatch"):
        materialization._require_exact_page_membership(
            "block-spanning", {"page-reviewed", "page-unreviewed"}, {"page-reviewed"}
        )


def test_reader_inherits_machine_and_rejects_changed_completion_binding(tmp_path: Path) -> None:
    """The reader applies sparse overrides only after completion-to-inventory validation."""
    preimage = {"input": "reader-fixture"}
    view_id = "navsemanticv1-" + canonical_json_sha256(preimage)
    disposition = _semantic_row(view_id)
    accounting = _empty_accounting()
    accounting["changed_content_entity_count"] = 1
    accounting["human_rejected_machine_navigation_entity_count"] = 1
    accounting["changed_block_count"] = 1
    accounting["preserved_section_association_count"] = 1
    specification = {
        "identity_preimage": preimage,
        "semantic_view_id": view_id,
    }
    publication = materialization._publish(
        tmp_path,
        view_id,
        [],
        [disposition],
        specification,
        accounting,
        SCHEMA_ROOT,
    )
    repeated = materialization._publish(
        tmp_path,
        view_id,
        [],
        [disposition],
        specification,
        accounting,
        SCHEMA_ROOT,
    )

    assert repeated == publication
    view = materialization.EffectiveNavigationView(publication)
    assert view.effective_navigation("block-old", machine_navigation=True) is False
    assert view.effective_navigation("unlisted", machine_navigation=True) is True

    completion_path = publication / "records/completion_record.json"
    completion = json.loads(completion_path.read_text())
    completion["artifact_inventory_sha256"] = "f" * 64
    completion_path.write_bytes(json_bytes(completion))
    with pytest.raises(ValueError, match="completion does not bind its inventory"):
        materialization.EffectiveNavigationView(publication)


def test_reader_recomputes_namespace_identity_from_manifest(tmp_path: Path) -> None:
    """A syntactically valid but non-derived namespace is not consumable."""
    view_id = "navsemanticv1-" + "e" * 64
    disposition = _semantic_row(view_id)
    specification = {
        "identity_preimage": {"input": "does-not-match-view-id"},
        "semantic_view_id": view_id,
    }
    publication = materialization._publish(
        tmp_path,
        view_id,
        [],
        [disposition],
        specification,
        _empty_accounting(),
        SCHEMA_ROOT,
    )

    with pytest.raises(ValueError, match="Gate B identity digest differs"):
        materialization.EffectiveNavigationView(publication)


def test_publication_refuses_changed_existing_bytes(tmp_path: Path) -> None:
    """Repeated publication reuses only an exactly identical namespace."""
    preimage = {"input": "no-clobber"}
    view_id = "navsemanticv1-" + canonical_json_sha256(preimage)
    disposition = _semantic_row(view_id)
    specification = {"identity_preimage": preimage, "semantic_view_id": view_id}
    publication = materialization._publish(
        tmp_path,
        view_id,
        [],
        [disposition],
        specification,
        _empty_accounting(),
        SCHEMA_ROOT,
    )
    (publication / "semantic_dispositions.jsonl").write_bytes(b'{"changed":true}\n')

    with pytest.raises(FileExistsError, match="refusing to reuse changed Gate B artifact"):
        materialization._publish(
            tmp_path,
            view_id,
            [],
            [disposition],
            specification,
            _empty_accounting(),
            SCHEMA_ROOT,
        )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"semantic_view_id": "navsemanticv1-" + "f" * 64}, "view differs"),
        ({"overlay_plan_id": "navoverlayplanv1-" + "f" * 64}, "plan differs"),
        ({"effective_navigation": True}, "invalid semantic disposition relation"),
    ],
)
def test_reader_rejects_malformed_semantic_rows(
    tmp_path: Path, change: dict[str, Any], message: str
) -> None:
    """A complete namespace cannot smuggle stale or contradictory overrides."""
    preimage = {"input": message}
    view_id = "navsemanticv1-" + canonical_json_sha256(preimage)
    disposition = _semantic_row(view_id)
    disposition.update(change)
    accounting = _empty_accounting()
    specification = {"identity_preimage": preimage, "semantic_view_id": view_id}
    publication = materialization._publish(
        tmp_path,
        view_id,
        [],
        [disposition],
        specification,
        accounting,
        SCHEMA_ROOT,
    )

    with pytest.raises(ValueError, match=message):
        materialization.EffectiveNavigationView(publication)


def _decision(page: int, *, machine: bool, human: str, entities: list[str]) -> dict[str, Any]:
    entry_id = f"tocpagev1-{page:024x}"
    return {
        "decision_entry_id": entry_id,
        "source_id": "source-a",
        "candidate_id": "docv1-" + "a" * 64,
        "page_id": f"page-{page}",
        "physical_page": page,
        "machine_navigation": machine,
        "disposition": human,
        "decision_origin_class": "accepted_nonvisible_origin_not_preserved",
        "visible_review_item_id": None,
        "c17_positive_suffix_evidence": None,
        "mapping_outcome": "mapped",
        "entity_ids_by_kind": {"blocks": entities, "tables": [], "sections": []},
    }


def _entity(
    entity_id: str,
    *,
    kind: str,
    navigation: bool,
    section: str | None = None,
    pages: set[str] | None = None,
) -> materialization._CanonicalEntity:
    return materialization._CanonicalEntity(
        source_id="source-a",
        candidate_id="docv1-" + "a" * 64,
        entity_kind=kind,
        entity_id=entity_id,
        page_ids=frozenset(pages or {"page-1", "page-2"}),
        section_id=section,
        semantic_placement="toc_content" if navigation else "direct_body",
        is_toc_row=navigation,
    )


def _semantic_row(view_id: str) -> dict[str, Any]:
    return {
        "schema_version": "er_commons.navigation_overlay.v1.semantic_disposition",
        "semantic_view_id": view_id,
        "overlay_plan_id": materialization.ACCEPTED_GATE_A_ID,
        "disposition_id": "navdispv1-" + "a" * 24,
        "source_id": "source-a",
        "candidate_id": "docv1-" + "a" * 64,
        "entity_kind": "block",
        "entity_id": "block-old",
        "canonical_record_path": "content/canonical/blocks.jsonl",
        "decision_entry_ids": ["tocpagev1-" + "b" * 24],
        "decision_page_ids": ["page-1"],
        "decision_physical_pages": [1],
        "machine_section_id": "section-a",
        "machine_semantic_placement": "toc_content",
        "machine_is_toc_row": True,
        "machine_navigation": True,
        "effective_navigation": False,
        "disposition": "human_rejected_machine_navigation",
        "original_machine_placement_preserved": True,
        "reason": "fixture",
    }


def _empty_accounting() -> dict[str, int]:
    return {
        "decision_count": 0,
        "machine_toc_human_toc_count": 0,
        "machine_not_toc_human_not_toc_count": 0,
        "human_confirmed_navigation_decision_count": 0,
        "human_rejected_machine_navigation_decision_count": 0,
        "fail_closed_decision_count": 0,
        "changed_content_entity_count": 0,
        "human_confirmed_navigation_entity_count": 0,
        "human_rejected_machine_navigation_entity_count": 0,
        "changed_block_count": 0,
        "changed_table_count": 0,
        "preserved_section_association_count": 0,
    }
