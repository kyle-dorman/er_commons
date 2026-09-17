"""Synthetic accepted-chain tests; never read external artifacts or source binaries."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.response_inventory.reference_replay_inputs import (
    COMPACT_LIMIT,
    contained,
    inventory_entries,
    load_review_chain,
    read_object,
    sealed_path,
    verify_digest,
)
from er_commons.response_inventory.reference_replay_mechanical import (
    _source_membership,
    _target_mapping,
)

JsonObject = dict[str, Any]
ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: Any) -> str:
    """Write synthetic compact metadata and return its exact digest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal_records(root: Path, fields: JsonObject) -> tuple[str, JsonObject]:
    """Seal a temporary compact-record directory with completion last."""
    entries = []
    for path in sorted(root.iterdir()):
        if path.name in {"completion.json", "artifact_inventory.json"}:
            continue
        entries.append(
            {
                "path": path.name,
                "byte_size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    inventory = {
        "file_count": len(entries),
        "byte_count": sum(r["byte_size"] for r in entries),
        "files": entries,
    }
    inventory_digest = write_json(root / "artifact_inventory.json", inventory)
    completion_digest = write_json(
        root / "completion.json",
        {"completion_last": True, "inventory_sha256": inventory_digest, **fields},
    )
    return completion_digest, inventory


@pytest.fixture
def chain(tmp_path: Path) -> tuple[Path, Path, JsonObject]:
    """Construct all seven synthetic files using only the tracked text-free freeze."""
    freeze = json.loads((ROOT / "docs/specs/task05g_phase1_bindings.json").read_text())
    pointer = freeze["acceptance_pointer"]
    records = tmp_path / freeze["finalization_relative_root"] / "records"
    accepted = freeze["acceptance"]["bindings"]
    write_json(
        records / "finalization_candidate.json",
        {
            k: accepted[k]
            for k in (
                "finalization_id",
                "sampled_review_merge_id",
                "toc_merge_id",
                "registry_id",
                "target_limitations_id",
                "task05g_handoff_id",
                "mechanical_handoff_id",
            )
        },
    )
    write_json(records / "task05g_handoff.json", freeze["task05g_handoff"])
    write_json(
        records / "usability_registry.json",
        {
            "registry_id": accepted["registry_id"],
            "status": "complete_bounded_merge",
            "source_count": 35,
            "entries": [{"logical_source_id": f"source-{i}"} for i in range(35)],
        },
    )
    write_json(
        records / "target_review_limitations.json",
        {
            "target_limitations_id": accepted["target_limitations_id"],
            "target_count": 185,
            "entries": freeze["review_coverage_projection"]["targets"],
        },
    )
    decisions = [{"entry_id": f"toc-{i}", "disposition": "not_toc"} for i in range(757)]
    write_json(
        records / "toc_review_decisions.json",
        {
            "toc_merge_id": accepted["toc_merge_id"],
            "status": "complete_bounded_merge",
            "entries": decisions,
        },
    )
    provenance = [
        {
            **r,
            "decision_origin": (
                "accepted_task04_proved_correspondence"
                if i < 706
                else "accepted_task04_repaired_source_sample_confirmed"
            ),
        }
        for i, r in enumerate(decisions)
    ]
    (records / "decision_provenance.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in provenance)
    )
    write_json(
        records / "sample_stratum_confirmations.json",
        {
            "entries": freeze["review_coverage_projection"]["sample_strata"],
            "status": "complete",
            "sample_count": 11,
        },
    )
    digest, inventory = seal_records(
        records,
        {
            "status": "complete_pending_explicit_acceptance",
            "finalization_id": pointer["finalization_id"],
        },
    )
    freeze["finalization_completion_sha256"] = digest
    freeze["finalization_inventory"] = inventory
    accepted["review_completion_sha256"] = digest
    acceptance = tmp_path / pointer["acceptance_relative_path"] / "records"
    pointer["acceptance_sha256"] = write_json(acceptance / "acceptance.json", freeze["acceptance"])
    pointer["completion_sha256"], _ = seal_records(
        acceptance,
        {"status": "accepted_with_limitations", "acceptance_id": pointer["acceptance_id"]},
    )
    pointer_path = tmp_path / "accepted.json"
    write_json(pointer_path, pointer)
    return tmp_path, pointer_path, freeze


def reseal_finalization(chain: tuple[Path, Path, JsonObject]) -> None:
    """Update fixture envelopes to test semantic checks beyond byte integrity."""
    root, pointer_path, freeze = chain
    pointer = freeze["acceptance_pointer"]
    records = root / freeze["finalization_relative_root"] / "records"
    freeze["finalization_completion_sha256"], freeze["finalization_inventory"] = seal_records(
        records,
        {
            "status": "complete_pending_explicit_acceptance",
            "finalization_id": pointer["finalization_id"],
        },
    )
    freeze["acceptance"]["bindings"]["review_completion_sha256"] = freeze[
        "finalization_completion_sha256"
    ]
    acceptance = root / pointer["acceptance_relative_path"] / "records"
    pointer["acceptance_sha256"] = write_json(acceptance / "acceptance.json", freeze["acceptance"])
    pointer["completion_sha256"], _ = seal_records(
        acceptance,
        {"status": "accepted_with_limitations", "acceptance_id": pointer["acceptance_id"]},
    )
    write_json(pointer_path, pointer)


def test_acceptance_chain_accepts_immutable_preacceptance_candidate(
    chain: tuple[Path, Path, JsonObject],
) -> None:
    """A later accepted pointer proves acceptance without editing historical labels."""
    root, pointer, freeze = chain
    result = load_review_chain(pointer, root, freeze)
    assert result["handoff"]["status"] == "ready_pending_explicit_task06h_acceptance"
    assert result["handoff"]["execution_authorized"] is False
    assert (
        result["handoff"]["final_f1_warning_binding"][
            "other_mentions_not_proven_draft_final_equivalent"
        ]
        == 64
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_pointer",
        "wrong_pointer",
        "missing_completion",
        "mixed_finalization",
        "extra_file",
        "changed_bytes",
    ],
)
def test_rejects_incomplete_or_mixed_acceptance(
    chain: tuple[Path, Path, JsonObject], mutation: str
) -> None:
    """Mechanical-only, partial, mixed, and altered bundles never reach consumers."""
    root, pointer, freeze = chain
    records = root / freeze["finalization_relative_root"] / "records"
    if mutation == "missing_pointer":
        pointer.unlink()
    elif mutation == "wrong_pointer":
        write_json(pointer, {"status": "ready_for_review"})
    elif mutation == "missing_completion":
        (records / "completion.json").unlink()
    elif mutation == "mixed_finalization":
        freeze["finalization_relative_root"] = "older-incomplete"
    elif mutation == "extra_file":
        (records / "unexpected.json").write_text("{}")
    else:
        (records / "usability_registry.json").write_text("{}")
    with pytest.raises((ValueError, FileNotFoundError)):
        load_review_chain(pointer, root, freeze)


@pytest.mark.parametrize(
    "mutation",
    [
        "warning",
        "source_membership",
        "provenance",
        "sample",
        "figure_status",
        "figure_eligible",
        "target_missing",
    ],
)
def test_rejects_semantic_promotions_after_valid_resealing(
    chain: tuple[Path, Path, JsonObject], mutation: str
) -> None:
    """Seals cannot hide warning loss or promotion of sampled review coverage."""
    root, pointer, freeze = chain
    records = root / freeze["finalization_relative_root"] / "records"
    names = {
        "warning": "task05g_handoff.json",
        "source_membership": "usability_registry.json",
        "sample": "sample_stratum_confirmations.json",
        "figure_status": "target_review_limitations.json",
        "figure_eligible": "target_review_limitations.json",
        "target_missing": "target_review_limitations.json",
    }
    if mutation == "provenance":
        path = records / "decision_provenance.jsonl"
        path.write_text(
            path.read_text().replace(
                "accepted_task04_repaired_source_sample_confirmed",
                "accepted_task04_proved_correspondence",
            )
        )
    else:
        path = records / names[mutation]
        value = json.loads(path.read_text())
        if mutation == "warning":
            value["final_f1_warning_binding"][
                "other_mentions_not_proven_draft_final_equivalent"
            ] = 63
        elif mutation == "source_membership":
            value["entries"][1] = value["entries"][0]
        elif mutation == "sample":
            value["sample_count"] = 51
        elif mutation == "figure_status":
            value["entries"][1]["fresh_review_status"] = "individually_equivalent"
        elif mutation == "figure_eligible":
            value["entries"][1]["text_only_model_eligibility"] = True
        else:
            value["entries"].pop()
        write_json(path, value)
    reseal_finalization(chain)
    with pytest.raises(ValueError):
        load_review_chain(pointer, root, freeze)


def test_forbidden_binary_and_large_hash_are_rejected_before_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The hashing helper cannot silently read PDFs/images or large metadata."""
    binary = tmp_path / "source.pdf"
    binary.write_bytes(b"not a PDF")
    large = tmp_path / "large.json"
    large.write_bytes(b" " * (COMPACT_LIMIT + 1))

    def forbidden_read(_: Path) -> bytes:
        raise AssertionError("forbidden path was opened")

    monkeypatch.setattr(Path, "read_bytes", forbidden_read)
    for path in [binary, large]:
        with pytest.raises(ValueError, match="not compact"):
            verify_digest(path, "0" * 64)
    with pytest.raises(ValueError, match="must be JSON"):
        read_object(binary)


def test_containment_and_duplicate_inventory(tmp_path: Path) -> None:
    """Explicit roots reject path traversal, symlink escape, and conflicting seals."""
    with pytest.raises(ValueError):
        contained(tmp_path, "../escape.json")
    (tmp_path / "link").symlink_to(tmp_path.parent)
    with pytest.raises(ValueError):
        contained(tmp_path, "link/escape.json")
    with pytest.raises(ValueError, match="duplicate"):
        inventory_entries({"files": [{"path": "x.json"}, {"path": "x.json"}]})
    path = tmp_path / "x.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="size"):
        sealed_path(tmp_path, {"path": "x.json", "byte_size": 3, "sha256": "0" * 64}, compact=True)


def test_namespace_mapping_requires_proved_source_and_unchanged_target() -> None:
    """A removed target or substituted Final source never inherits Draft equivalence."""
    old = "old/section/deir_main/sec1"
    new = "new/section/deir_main/sec1"
    rows = [{"target_id": new}, {"target_id": "new/document/feir_appendix_f1/doc1"}]
    outcomes = [{"compatible_target_ids": [old, "old/document/deir_appendix_f1/doc1"]}]
    sources = [
        {"logical_source_id": "deir_main", "change_class": "repaired_structure"},
        {"logical_source_id": "deir_appendix_f1", "change_class": "substituted_new_source"},
    ]
    changes = {"changed_sources": [{"logical_source_id": "deir_main", "removed": [], "added": []}]}
    mapping = _target_mapping(outcomes, rows, sources, changes)
    assert mapping["target_mapping"] == [
        {"baseline_target_id": old, "selected_target_id": new, "classification": "namespace_only"}
    ]
    changes["changed_sources"][0]["removed"] = [{"target": {"target_id": "section/deir_main/sec1"}}]
    assert _target_mapping(outcomes, rows, sources, changes)["target_mapping"] == []


def test_source_registry_must_match_selected_candidates() -> None:
    """Equal source counts do not permit a different candidate or edition."""
    rows = []
    for i in range(35):
        logical = "deir_appendix_f1" if i == 34 else f"source-{i}"
        selected = "feir_appendix_f1" if i == 34 else logical
        rows.append(
            {
                "logical_source_id": logical,
                "selected_physical_source_id": selected,
                "replacement_candidate_id": f"doc-{i}",
                "change_class": (
                    "preserved_semantic"
                    if i < 32
                    else "repaired_structure"
                    if i < 34
                    else "substituted_new_source"
                ),
                "semantic_equivalence": i < 34,
            }
        )
    registry = {
        "entries": [
            {
                "logical_source_id": r["logical_source_id"],
                "selected_source_id": r["selected_physical_source_id"],
                "selected_candidate_id": r["replacement_candidate_id"],
                "change_class": r["change_class"],
            }
            for r in rows
        ]
    }
    _source_membership(rows, registry)
    changed = copy.deepcopy(registry)
    changed["entries"][3]["selected_candidate_id"] = "wrong"
    with pytest.raises(ValueError, match="membership"):
        _source_membership(rows, changed)


def test_mechanical_chain_derives_index_paths_and_main_children(tmp_path: Path) -> None:
    """A small synthetic mechanical chain resolves explicit roots and sealed membership."""
    from er_commons.response_inventory.reference_replay_mechanical import load_mechanical_inputs

    def reference(path: Path, root: Path) -> JsonObject:
        """Return a bounded synthetic sealed reference."""
        return {
            "path": path.relative_to(root).as_posix(),
            "byte_size": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    pub = tmp_path / "selected"
    pub.mkdir()
    sections = pub / "main/sections.jsonl"
    sections.parent.mkdir()
    sections.write_text(
        json.dumps(
            {"id": "new/section/deir_main/s1", "ordered_child_ids": ["new/section/deir_main/s2"]}
        )
        + "\n"
        + json.dumps({"id": "new/section/deir_main/s2"})
        + "\n"
    )
    sources = []
    registry = []
    eligible = []
    docs = []
    for i in range(35):
        logical = "deir_appendix_f1" if i == 34 else "deir_main" if i == 32 else f"source-{i}"
        physical = "feir_appendix_f1" if i == 34 else logical
        candidate = f"doc-{i}"
        change = (
            "preserved_semantic"
            if i < 32
            else "repaired_structure"
            if i < 34
            else "substituted_new_source"
        )
        sources.append(
            {
                "logical_source_id": logical,
                "selected_physical_source_id": physical,
                "replacement_candidate_id": candidate,
                "change_class": change,
                "semantic_equivalence": i != 34,
            }
        )
        registry.append(
            {
                "logical_source_id": logical,
                "selected_source_id": physical,
                "selected_candidate_id": candidate,
                "change_class": change,
            }
        )
        eligible.append(
            {
                "source_id": physical,
                "candidate_id": candidate,
                "target_records_ref": [reference(sections, pub)] if i == 32 else [],
            }
        )
        docs.append({"candidate_id": candidate, "target_id": f"new/document/{physical}/doc1"})
    target = pub / "index/target_index.jsonl"
    target.parent.mkdir()
    target.write_text(json.dumps({"target_id": "new/section/deir_main/s1"}) + "\n")
    inv = target.parent / "records/artifact_inventory.json"
    write_json(inv, {"files": [reference(target, target.parent)]})
    index = inv.parent / "completion_record.json"
    write_json(
        index,
        {
            "index_id": "idx",
            "status": "complete",
            "completion_last": True,
            "artifact_inventory": reference(inv, pub),
            "entries_ref": reference(target, pub),
            "entry_count": 1,
            "eligible_candidates": eligible,
            "document_targets": docs,
        },
    )
    handoff = pub / "handoff/records/completion_record.json"
    write_json(
        handoff,
        {
            "handoff_id": "handoff",
            "status": "ready",
            "completion_last": True,
            "blocking_reasons": [],
            "index_id": "idx",
            "index_completion_ref": reference(index, pub),
            "identity_preimage": {"index_completion_sha256": reference(index, pub)["sha256"]},
        },
    )
    checkpoint = tmp_path / "checkpoint.json"
    write_json(
        checkpoint,
        {
            "derived_id": "handoff",
            "recomputed_id": "handoff",
            "verified": True,
            "outputs": {
                "handoff_completion_ref": reference(handoff, tmp_path),
                "target_index_completion_ref": reference(index, tmp_path),
            },
        },
    )
    corr = tmp_path / "correspondence"
    corr.mkdir()
    provenance = {"replacement_handoff_checkpoint": reference(checkpoint, tmp_path)}
    for name, value in [
        ("provenance.json", provenance),
        ("source_correspondence.json", {"rows": sources}),
        ("target_correspondence.json", {"changed_sources": []}),
        ("review_correspondence.json", {}),
    ]:
        write_json(corr / name, value)
    write_json(
        corr / "artifact_inventory.json",
        {
            "files": [
                reference(corr / name, corr)
                for name in [
                    "provenance.json",
                    "source_correspondence.json",
                    "target_correspondence.json",
                    "review_correspondence.json",
                ]
            ]
        },
    )
    corr_digest = write_json(
        corr / "completion.json",
        {
            "status": "complete",
            "completion_last": True,
            "artifact_inventory": reference(corr / "artifact_inventory.json", corr),
        },
    )
    ready = tmp_path / "readiness"
    ready.mkdir()
    ready_digest = write_json(
        ready / "readiness.json", {"status": "ready_for_review", "inventory_sha256": "a" * 64}
    )
    completion_digest = write_json(
        ready / "completion.json",
        {
            "status": "complete",
            "inventory_sha256": "a" * 64,
            "readiness": reference(ready / "readiness.json", ready),
        },
    )
    catalog = tmp_path / "catalog.json"
    catalog_digest = write_json(catalog, {"families": []})
    spec = {
        "readiness_sha256": ready_digest,
        "readiness_completion_sha256": completion_digest,
        "readiness_root": "readiness",
        "correspondence_root": "correspondence",
        "correspondence_completion_sha256": corr_digest,
        "handoff_completion_sha256": reference(handoff, tmp_path)["sha256"],
        "publication_root": "selected",
        "catalog": {"path": "catalog.json", "sha256": catalog_digest},
    }
    review = {
        "acceptance": {
            "bindings": {
                "readiness_sha256": ready_digest,
                "correspondence_completion_sha256": corr_digest,
                "mechanical_handoff_id": "handoff",
            }
        },
        "registry": {"entries": registry},
    }
    result = load_mechanical_inputs(spec, tmp_path, review, [])
    assert result["direct_section_children"]["new/section/deir_main/s1"] == (
        "new/section/deir_main/s2",
    )
    assert (
        result["correspondence"]["document_target_mapping"]["doc-34"]
        == "new/document/feir_appendix_f1/doc1"
    )
    assert [r["role"] for r in result["dependencies"]] == [
        "task06g_handoff",
        "task06g_target_index",
        "task06g_source_correspondence",
        "source_family_catalog",
    ]
    spec["publication_root"] = "wrong"
    with pytest.raises((ValueError, FileNotFoundError)):
        load_mechanical_inputs(spec, tmp_path, review, [])


def test_nonterminal_baseline_uses_exact_receipt_inventory_seal(tmp_path: Path) -> None:
    """The accepted 05F receipt is authoritative without inventing a completion."""
    from er_commons.response_inventory.reference_replay_inputs import _load_baseline

    root = tmp_path / "rules-test"
    (root / "outcomes").mkdir(parents=True)
    (root / "links").mkdir()
    (root / "outcomes/reference_outcomes.jsonl").write_text("{}\n")
    (root / "links/draft_eir_links.jsonl").write_text("{}\n")
    files = []
    for name in ["outcomes/reference_outcomes.jsonl", "links/draft_eir_links.jsonl"]:
        path = root / name
        files.append(
            {
                "path": name,
                "byte_size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    inventory_digest = write_json(
        root / "records/managed_file_inventory.json",
        {"files": [{"authority": "bundle", **r} for r in files]},
    )
    inventory_path = root / "records/managed_file_inventory.json"
    inventory_ref = {
        "path": "records/managed_file_inventory.json",
        "byte_size": inventory_path.stat().st_size,
        "sha256": inventory_digest,
    }
    receipt = {
        "semantic_digest": "semantic",
        "completion_written": False,
        "status": "qualified_rules_complete_review_required",
        "source_pdf_accessed": False,
        "files": [*files, inventory_ref],
    }
    receipt_digest = write_json(root / "records/rule_receipt.json", receipt)
    inputs = {
        "task05f": {
            "root": "rules-test",
            "rules_id": "rules-test",
            "semantic_digest": "semantic",
            "receipt_sha256": receipt_digest,
            "inventory_sha256": inventory_digest,
        }
    }
    handoff = {"task05f_rules": "rules-test", "task05f_semantic_digest": "semantic"}
    outcomes, links, dependency = _load_baseline(inputs, tmp_path, handoff)
    assert outcomes == links == [{}]
    assert dependency["role"] == "task05f_baseline"
    receipt["files"][-1]["sha256"] = "0" * 64
    inputs["task05f"]["receipt_sha256"] = write_json(root / "records/rule_receipt.json", receipt)
    with pytest.raises(ValueError, match="managed inventory"):
        _load_baseline(inputs, tmp_path, handoff)
