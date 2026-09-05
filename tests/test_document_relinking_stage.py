"""Source-free owner tests for the additive document relink stage."""

from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from er_commons.document_records.document_references import relink_publication
from er_commons.document_records.document_references.construction import CandidateSource
from er_commons.document_records.document_references.linking_policy import (
    DocumentLinkingPolicy,
    load_document_linking_policy,
)
from er_commons.document_records.document_references.policy import default_mention_policy
from er_commons.document_records.document_references.relink_publication import (
    RelinkIdentityInputs,
    build_relink_identity,
    publish_relink_candidate,
    verify_relink_candidate,
)
from er_commons.document_records.document_references.relinking import (
    DocumentRelinkBuilder,
    NavigationInputs,
)
from er_commons.document_records.document_references.relinking_config import ExternalArtifactRef
from er_commons.document_records.document_references.storage import write_jsonl
from er_commons.source_family_catalog import SourceFamilyCatalog

ROOT = Path(__file__).parents[1]
UPSTREAM = "exv1-" + "1" * 64
SCHEMA_ROOT = ROOT / "benchmarks/er_bench/schemas/document_linking/v1"


def test_navigation_inputs_remap_only_embedded_source_namespace() -> None:
    prior = "exv1-" + "9" * 64
    current = "exv1-" + "8" * 64
    navigation = NavigationInputs(
        entries=(
            {
                "navigation_entry_id": "stable-navigation-id",
                "source_id": "report_alpha",
                "destination_page_ids": [f"{prior}/page/report_alpha/p000001"],
            },
        )
    )

    remapped = navigation.remap_namespace(prior, current)

    assert remapped.entries[0]["navigation_entry_id"] == "stable-navigation-id"
    assert remapped.entries[0]["destination_page_ids"] == [f"{current}/page/report_alpha/p000001"]


def test_builder_preserves_records_adds_only_r6_and_uses_shared_resolution(
    tmp_path: Path,
) -> None:
    identity = build_relink_identity(_identity_inputs())
    candidate = str(identity["extraction_id"])
    source = _source(tmp_path)
    navigation = NavigationInputs(
        entries=(
            {
                "navigation_entry_id": "nav-1",
                "source_id": "report_alpha",
                "model_text": "1 Overview 1",
                "terminal_destination_token": "1",
                "target_type": "section",
                "destination_page_ids": [f"{UPSTREAM}/page/report_alpha/p000001"],
            },
        )
    )

    build = DocumentRelinkBuilder(
        source=source,
        upstream_candidate_id=UPSTREAM,
        candidate_id=candidate,
        source_id="report_alpha",
        mention_policy=default_mention_policy(),
        linking_policy=_linking_policy(),
        source_family_catalog=_catalog(),
        source_family_catalog_sha256="8" * 64,
        navigation=navigation,
    ).build()

    assert len(build.products.target_aliases) == 2
    assert build.products.target_aliases[0]["upstream_alias_id"].startswith(UPSTREAM)
    assert build.products.target_aliases[1]["alias_origin"] == ("linking_v1_r6_body_table_caption")
    assert len(build.products.ordinary_references) == 2
    assert [row["resolution_status"] for row in build.products.ordinary_references] == [
        "resolved",
        "unresolved",
    ]
    assert len(build.products.navigation_decisions) == 1
    assert build.products.navigation_decisions[0]["outcome"] == "resolved_unique"
    assert len(build.products.navigation_links) == 1
    assert all(
        candidate in str(value)
        for value in (
            build.preserved_record_files["canonical/documents.jsonl"][0]["id"],
            build.products.target_aliases[0]["id"],
        )
    )


def test_navigation_r1_uses_structural_marker_only_with_destination_evidence(
    tmp_path: Path,
) -> None:
    identity = build_relink_identity(_identity_inputs())
    source = _source(tmp_path)
    page_id = f"{UPSTREAM}/page/report_alpha/p000001"
    navigation = NavigationInputs(
        entries=(
            {
                "navigation_entry_id": "with-destination",
                "source_id": "report_alpha",
                "model_text": "1 Different extracted title 1",
                "terminal_destination_token": "1",
                "marker_kind": "section",
                "normalized_marker": "1",
                "destination_page_ids": [page_id],
            },
            {
                "navigation_entry_id": "without-destination",
                "source_id": "report_alpha",
                "model_text": "1 Different extracted title",
                "marker_kind": "section",
                "normalized_marker": "1",
            },
        )
    )

    build = DocumentRelinkBuilder(
        source=source,
        upstream_candidate_id=UPSTREAM,
        candidate_id=str(identity["extraction_id"]),
        source_id="report_alpha",
        mention_policy=default_mention_policy(),
        linking_policy=_linking_policy(),
        source_family_catalog=_catalog(),
        source_family_catalog_sha256="8" * 64,
        navigation=navigation,
    ).build()

    assert [row["outcome"] for row in build.products.navigation_decisions] == [
        "resolved_unique",
        "no_text_match",
    ]


def test_identity_changes_for_policy_or_review_bundle() -> None:
    baseline = build_relink_identity(_identity_inputs())
    changed_policy = build_relink_identity(
        RelinkIdentityInputs(**{**_identity_inputs().__dict__, "linking_policy_sha256": "9" * 64})
    )
    changed_review = build_relink_identity(
        RelinkIdentityInputs(
            **{
                **_identity_inputs().__dict__,
                "reviewed_navigation_bundle_id": "navreviewv1-" + "a" * 64,
                "reviewed_navigation_completion_sha256": "b" * 64,
            }
        )
    )

    assert baseline["extraction_id"] != changed_policy["extraction_id"]
    assert baseline["extraction_id"] != changed_review["extraction_id"]
    assert build_relink_identity(_identity_inputs()) == baseline


def test_source_document_boundary_verifies_all_five_reused_stage_seals(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / ("docv1-" + "d" * 64)
    records = source_root / "records"
    records.mkdir(parents=True)
    stage_names = (
        "stable_content_evidence",
        "heading_evidence",
        "mapped_records",
        "hierarchy_decisions",
        "structured_document",
    )
    stage_refs = {}
    for index, stage_name in enumerate(stage_names, start=1):
        path = tmp_path / "stages" / stage_name / "records/completion_record.json"
        path.parent.mkdir(parents=True)
        path.write_text(f'{{"stage": {index}}}\n')
        stage_refs[stage_name] = {
            "path": path.relative_to(tmp_path).as_posix(),
            "sha256": sha256(path.read_bytes()).hexdigest(),
        }
    (records / "document_identity.json").write_text(
        json.dumps(
            {
                "candidate_id": source_root.name,
                "production_extraction_id": "exv1-" + "a" * 64,
                "source": {"source_id": "report_alpha"},
                "stage_completions": stage_refs,
            }
        )
    )
    structured_path = tmp_path / stage_refs["structured_document"]["path"]
    structured_ref = ExternalArtifactRef(
        authority="artifact_root",
        path=stage_refs["structured_document"]["path"],
        sha256=stage_refs["structured_document"]["sha256"],
        byte_size=structured_path.stat().st_size,
    )

    relink_publication._verify_source_document_reuse_boundary(
        source_document_root=source_root,
        artifact_root=tmp_path,
        expected_source_id="report_alpha",
        expected_production_id="exv1-" + "a" * 64,
        selected_structured_completion=structured_ref,
    )
    (tmp_path / stage_refs["mapped_records"]["path"]).write_text("tampered\n")
    with pytest.raises(ValueError, match="reused mapped_records seal differs"):
        relink_publication._verify_source_document_reuse_boundary(
            source_document_root=source_root,
            artifact_root=tmp_path,
            expected_source_id="report_alpha",
            expected_production_id="exv1-" + "a" * 64,
            selected_structured_completion=structured_ref,
        )


def test_writer_is_completion_last_closed_and_no_clobber(tmp_path: Path) -> None:
    identity = build_relink_identity(_identity_inputs())
    candidate = str(identity["extraction_id"])
    source = _source(tmp_path)
    build = DocumentRelinkBuilder(
        source=source,
        upstream_candidate_id=UPSTREAM,
        candidate_id=candidate,
        source_id="report_alpha",
        mention_policy=default_mention_policy(),
        linking_policy=_linking_policy(),
        source_family_catalog=_catalog(),
        source_family_catalog_sha256="8" * 64,
    ).build()
    output = tmp_path / "outputs" / candidate

    completion = publish_relink_candidate(
        root=output,
        source=source,
        build=build,
        identity=identity,
        schema_paths=_schema_paths(),
    )
    assert completion == output / "records/completion_record.json"
    assert (
        publish_relink_candidate(
            root=output,
            source=source,
            build=build,
            identity=identity,
            schema_paths=_schema_paths(),
        )
        == completion
    )

    (output / "navigation/links.jsonl").write_text("changed\n")
    with pytest.raises(ValueError, match="inventory differs"):
        verify_relink_candidate(output, candidate, schema_paths=_schema_paths())


def test_existing_identity_rejects_different_regenerated_linking_outputs(
    tmp_path: Path,
) -> None:
    identity = build_relink_identity(_identity_inputs())
    candidate = str(identity["extraction_id"])
    source = _source(tmp_path)
    build = DocumentRelinkBuilder(
        source=source,
        upstream_candidate_id=UPSTREAM,
        candidate_id=candidate,
        source_id="report_alpha",
        mention_policy=default_mention_policy(),
        linking_policy=_linking_policy(),
        source_family_catalog=_catalog(),
        source_family_catalog_sha256="8" * 64,
    ).build()
    output = tmp_path / "outputs" / candidate
    publish_relink_candidate(
        root=output,
        source=source,
        build=build,
        identity=identity,
        schema_paths=_schema_paths(),
    )
    changed = replace(
        build,
        support={**build.support, "accounting": {**build.support["accounting"], "test": True}},
    )

    with pytest.raises(ValueError, match="support differs"):
        publish_relink_candidate(
            root=output,
            source=source,
            build=changed,
            identity=identity,
            schema_paths=_schema_paths(),
        )


def test_owned_code_digest_includes_machine_link_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[Path] = []

    def digest(path: Path) -> str:
        observed.append(path)
        return "0" * 64

    monkeypatch.setattr(relink_publication, "sha256_file", digest)
    relink_publication._owned_code_bundle_sha256()

    assert any(path.name == "machine_link_resolution.py" for path in observed)


def test_invalid_generated_family_cannot_publish_completion(tmp_path: Path) -> None:
    identity = build_relink_identity(_identity_inputs())
    candidate = str(identity["extraction_id"])
    source = _source(tmp_path)
    valid_build = DocumentRelinkBuilder(
        source=source,
        upstream_candidate_id=UPSTREAM,
        candidate_id=candidate,
        source_id="report_alpha",
        mention_policy=default_mention_policy(),
        linking_policy=_linking_policy(),
        source_family_catalog=_catalog(),
        source_family_catalog_sha256="8" * 64,
    ).build()
    build = replace(
        valid_build,
        products=replace(
            valid_build.products,
            navigation_entries=(
                {
                    "navigation_entry_id": "entry-1",
                    "source_id": "INVALID SOURCE",
                    "lookup_text": "1 Overview",
                },
            ),
        ),
    )
    output = tmp_path / "outputs" / candidate

    with pytest.raises(ValueError, match="invalid relink navigation_entry"):
        publish_relink_candidate(
            root=output,
            source=source,
            build=build,
            identity=identity,
            schema_paths=_schema_paths(),
        )

    assert not output.exists()


def test_output_schema_role_set_is_closed(tmp_path: Path) -> None:
    identity = build_relink_identity(_identity_inputs())
    candidate = str(identity["extraction_id"])
    source = _source(tmp_path)
    build = DocumentRelinkBuilder(
        source=source,
        upstream_candidate_id=UPSTREAM,
        candidate_id=candidate,
        source_id="report_alpha",
        mention_policy=default_mention_policy(),
        linking_policy=_linking_policy(),
        source_family_catalog=_catalog(),
        source_family_catalog_sha256="8" * 64,
    ).build()
    schemas = _schema_paths()
    schemas.pop("support")

    with pytest.raises(ValueError, match="schema roles differ"):
        publish_relink_candidate(
            root=tmp_path / "outputs" / candidate,
            source=source,
            build=build,
            identity=identity,
            schema_paths=schemas,
        )


def test_explicit_parent_relation_fails_closed_until_parent_resolves(tmp_path: Path) -> None:
    identity = build_relink_identity(_identity_inputs())
    source = _source(tmp_path)
    navigation = NavigationInputs(
        entries=(
            {
                "navigation_entry_id": "child",
                "source_id": "report_alpha",
                "lookup_text": "a. Detail",
                "target_type": "section",
            },
            {
                "navigation_entry_id": "parent",
                "source_id": "report_alpha",
                "lookup_text": "1 Overview",
                "target_type": "section",
                "link_claim": False,
            },
        ),
        relations=(
            {
                "relation_id": "rel-1",
                "source_id": "report_alpha",
                "child_entry_id": "child",
                "parent_entry_id": "parent",
            },
        ),
    )
    build = DocumentRelinkBuilder(
        source=source,
        upstream_candidate_id=UPSTREAM,
        candidate_id=str(identity["extraction_id"]),
        source_id="report_alpha",
        mention_policy=default_mention_policy(),
        linking_policy=_linking_policy(),
        source_family_catalog=_catalog(),
        source_family_catalog_sha256="8" * 64,
        navigation=navigation,
    ).build()

    assert [row["outcome"] for row in build.products.navigation_decisions] == ["no_text_match"]


def test_letter_marker_is_retained_and_parent_resolves_before_child(tmp_path: Path) -> None:
    identity = build_relink_identity(_identity_inputs())
    source = _source(tmp_path)
    document = f"{UPSTREAM}/document/report_alpha"
    page = f"{UPSTREAM}/page/report_alpha/p000001"
    parent = f"{UPSTREAM}/section/report_alpha/sec000001"
    child = f"{UPSTREAM}/section/report_alpha/sec000002"
    child_heading = f"{UPSTREAM}/block/report_alpha/blk000004"
    source.record_files["canonical/sections.jsonl"].append(
        {
            "id": child,
            "document_id": document,
            "sequence": 2,
            "heading_block_id": child_heading,
            "parent_section_id": parent,
        }
    )
    source.record_files["canonical/blocks.jsonl"].append(
        _block(
            child_heading,
            document,
            page,
            child,
            4,
            "a. Detail",
            "heading",
            [10, 1, 90, 5],
        )
    )
    source.record_files["canonical/target_aliases.jsonl"].append(
        {
            "id": f"{UPSTREAM}/target-alias/report_alpha/alias000002",
            "document_id": document,
            "sequence": 2,
            "alias_kind": "section",
            "raw_values": ["a. Detail"],
            "normalized_alias": "a. detail",
            "normalization_policy": "nfc_nbsp_ascii_whitespace_casefold_v1",
            "resolution_status": "unique",
            "targets": [{"target_id": child, "target_type": "section"}],
        }
    )
    navigation = NavigationInputs(
        entries=(
            {
                "navigation_entry_id": "child",
                "source_id": "report_alpha",
                "entry_text": "Detail",
                "normalized_marker": "a.",
            },
            {
                "navigation_entry_id": "parent",
                "source_id": "report_alpha",
                "lookup_text": "1 Overview",
                "target_type": "section",
                "link_claim": False,
            },
        ),
        relations=(
            {
                "relation_id": "rel-1",
                "source_id": "report_alpha",
                "child_entry_id": "child",
                "parent_entry_id": "parent",
            },
        ),
    )

    build = DocumentRelinkBuilder(
        source=source,
        upstream_candidate_id=UPSTREAM,
        candidate_id=str(identity["extraction_id"]),
        source_id="report_alpha",
        mention_policy=default_mention_policy(),
        linking_policy=_linking_policy(),
        source_family_catalog=_catalog(),
        source_family_catalog_sha256="8" * 64,
        navigation=navigation,
    ).build()

    assert [row["outcome"] for row in build.products.navigation_decisions] == ["resolved_unique"]
    assert build.support["accounting"]["navigation_entry_count"] == 2
    assert build.support["accounting"]["navigation_claim_count"] == 1


def test_bundle_loader_honors_dispositions_and_real_entry_text_shape(tmp_path: Path) -> None:
    bundle = tmp_path / f"navreviewv1-{'a' * 64}"
    navigation = bundle / "navigation"
    write_jsonl(
        navigation / "text_entries.jsonl",
        [
            {
                "source_id": "report_alpha",
                "toc_text_entry_id": "kept",
                "model_text": "1 Overview 1",
                "terminal_destination_token": "1",
                "table_disposition_id": "accepted",
            },
            {
                "source_id": "report_alpha",
                "toc_text_entry_id": "rejected",
                "model_text": "2 Rejected 2",
                "terminal_destination_token": "2",
                "table_disposition_id": "rejected-disposition",
            },
        ],
    )
    write_jsonl(
        navigation / "dispositions.jsonl",
        [
            {
                "source_id": "report_alpha",
                "disposition_id": "accepted",
                "effective_navigation": True,
            },
            {
                "source_id": "report_alpha",
                "disposition_id": "rejected-disposition",
                "effective_navigation": False,
            },
        ],
    )
    write_jsonl(navigation / "parent_relations.jsonl", [])

    loaded = NavigationInputs.from_bundle_root(bundle, source_id="report_alpha")

    assert [row["toc_text_entry_id"] for row in loaded.entries] == ["kept"]


def test_unsupported_navigation_shape_is_retained_as_unresolved(tmp_path: Path) -> None:
    identity = build_relink_identity(_identity_inputs())
    build = DocumentRelinkBuilder(
        source=_source(tmp_path),
        upstream_candidate_id=UPSTREAM,
        candidate_id=str(identity["extraction_id"]),
        source_id="report_alpha",
        mention_policy=default_mention_policy(),
        linking_policy=_linking_policy(),
        source_family_catalog=_catalog(),
        source_family_catalog_sha256="8" * 64,
        navigation=NavigationInputs(
            entries=(
                {
                    "navigation_entry_id": "chapter",
                    "source_id": "report_alpha",
                    "model_text": "Chapter 3 Project Description",
                },
            )
        ),
    ).build()

    assert build.products.navigation_decisions[0]["outcome"] == "no_text_match"
    assert build.products.navigation_links == ()


def test_machine_navigation_is_projected_when_review_is_absent(tmp_path: Path) -> None:
    source = _source(tmp_path)
    source.record_files["canonical/blocks.jsonl"][0]["is_toc_row"] = True

    navigation = NavigationInputs.from_machine_records(
        source.record_files, source_id="report_alpha"
    )

    assert len(navigation.entries) == 1
    assert navigation.entries[0]["lookup_text"] == "1 Overview"
    assert navigation.entries[0]["machine_navigation"] is True


def test_reviewed_source_with_zero_effective_entries_stays_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle_id = "navreviewv1-" + "a" * 64
    bundle = tmp_path / bundle_id
    write_jsonl(bundle / "navigation/text_entries.jsonl", [])
    write_jsonl(bundle / "navigation/dispositions.jsonl", [])
    write_jsonl(bundle / "navigation/parent_relations.jsonl", [])
    completion = bundle / "records/completion_record.json"
    completion.parent.mkdir(parents=True)
    completion.write_text("{}\n")
    source = _source(tmp_path / "source")
    source.record_files["canonical/blocks.jsonl"][0]["is_toc_row"] = True
    request = SimpleNamespace(
        identity_inputs=SimpleNamespace(
            source_id="report_alpha",
            reviewed_navigation_bundle_id=bundle_id,
            reviewed_navigation_completion_sha256="b" * 64,
        ),
        reviewed_navigation_root=bundle,
        reviewed_navigation_completion_path=completion,
    )
    monkeypatch.setattr(relink_publication, "_verify_digest", lambda *_a, **_k: None)
    monkeypatch.setattr(relink_publication, "_verify_completion_inventory", lambda *_a, **_k: None)

    navigation = relink_publication._load_reviewed_navigation(request, source)

    assert navigation.entries == ()


def _identity_inputs() -> RelinkIdentityInputs:
    return RelinkIdentityInputs(
        source_id="report_alpha",
        source_document_id="docv1-" + "2" * 64,
        structured_candidate_id=UPSTREAM,
        source_document_completion_sha256="3" * 64,
        source_document_inventory_sha256="4" * 64,
        structured_completion_sha256="5" * 64,
        structured_inventory_sha256="6" * 64,
        link_run_spec_sha256="7" * 64,
        linking_policy_sha256="8" * 64,
        source_family_catalog_sha256="9" * 64,
        reviewed_navigation_bundle_id=None,
        reviewed_navigation_completion_sha256=None,
        output_schema_bundle_sha256="a" * 64,
        owned_code_bundle_sha256="b" * 64,
    )


def _schema_paths() -> dict[str, Path]:
    return {
        role: SCHEMA_ROOT / f"{role}.schema.json"
        for role in (
            "identity",
            "manifest",
            "inventory",
            "completion",
            "alias",
            "ordinary_reference",
            "navigation_entry",
            "navigation_relation",
            "navigation_decision",
            "navigation_link",
            "support",
        )
    }


def _linking_policy() -> DocumentLinkingPolicy:
    return load_document_linking_policy(
        ROOT / "configs/linking_policies/document_linking_v1.json",
        schema_path=(
            ROOT / "benchmarks/er_bench/schemas/document_linking/v1/linking_policy.schema.json"
        ),
    )


def _catalog() -> SourceFamilyCatalog:
    return SourceFamilyCatalog.from_bytes(
        json.dumps(
            {
                "schema_version": "er_commons.source_family_catalog.v1",
                "catalog_version": "fixture-v1",
                "source_family_id": "example-family",
                "sources": [
                    {
                        "source": {
                            "source_id": "report_alpha",
                            "sha256": "a" * 64,
                            "pdf_page_count": 1,
                        },
                        "family_root_source_id": "report_alpha",
                        "document_role": "root_report",
                        "parent_source_id": None,
                        "reference_aliases": ["report alpha"],
                    }
                ],
            }
        ).encode()
    )


def _source(tmp_path: Path) -> CandidateSource:
    document = f"{UPSTREAM}/document/report_alpha"
    page = f"{UPSTREAM}/page/report_alpha/p000001"
    section = f"{UPSTREAM}/section/report_alpha/sec000001"
    heading = f"{UPSTREAM}/block/report_alpha/blk000001"
    paragraph = f"{UPSTREAM}/block/report_alpha/blk000002"
    caption = f"{UPSTREAM}/block/report_alpha/blk000003"
    table = f"{UPSTREAM}/table/report_alpha/tbl000001"
    record_files = {
        "canonical/documents.jsonl": [{"id": document, "source_id": "report_alpha", "sequence": 1}],
        "canonical/pages.jsonl": [
            {
                "id": page,
                "document_id": document,
                "sequence": 1,
                "physical_page_number": 1,
            }
        ],
        "canonical/sections.jsonl": [
            {
                "id": section,
                "document_id": document,
                "sequence": 1,
                "heading_block_id": heading,
                "parent_section_id": None,
            }
        ],
        "canonical/blocks.jsonl": [
            _block(heading, document, page, section, 1, "1 Overview", "heading", [10, 90, 90, 100]),
            _block(
                paragraph,
                document,
                page,
                section,
                2,
                "See Section 1.",
                "paragraph",
                [10, 70, 90, 80],
            ),
            _block(
                caption, document, page, section, 3, "Table 2. Results", "caption", [10, 50, 90, 60]
            ),
        ],
        "canonical/tables.jsonl": [
            {
                "id": table,
                "document_id": document,
                "sequence": 1,
                "section_id": section,
                "regions": [{"page_id": page, "bbox": [15, 10, 85, 45]}],
            }
        ],
        "canonical/figures.jsonl": [],
        "canonical/target_aliases.jsonl": [
            {
                "id": f"{UPSTREAM}/target-alias/report_alpha/alias000001",
                "document_id": document,
                "sequence": 1,
                "alias_kind": "section",
                "raw_values": ["1 Overview"],
                "normalized_alias": "1 overview",
                "normalization_policy": "nfc_nbsp_ascii_whitespace_casefold_v1",
                "resolution_status": "unique",
                "targets": [{"target_id": section, "target_type": "section"}],
            }
        ],
        "canonical/cross_references.jsonl": [],
    }
    manifest = {
        "schema_version": "fixture",
        "extraction_id": UPSTREAM,
        "record_files": [
            {"record_type": path.removesuffix(".jsonl"), "path": path} for path in record_files
        ],
        "support_files": [],
    }
    source_root = tmp_path / "structured"
    for path, rows in record_files.items():
        write_jsonl(source_root / path, rows)
    return CandidateSource(source_root, manifest, record_files)


def _block(
    record_id: str,
    document_id: str,
    page_id: str,
    section_id: str,
    sequence: int,
    text: str,
    block_type: str,
    bbox: list[int],
) -> dict[str, object]:
    return {
        "id": record_id,
        "document_id": document_id,
        "sequence": sequence,
        "canonical_text": text,
        "block_type": block_type,
        "content_layer": "body",
        "is_toc_row": False,
        "section_id": section_id,
        "regions": [{"page_id": page_id, "bbox": bbox}],
        "raw_links": [],
    }
