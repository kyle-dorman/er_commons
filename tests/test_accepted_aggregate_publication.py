"""Exercise accepted aggregate reuse through routing, inventory and atomic publication."""

import os
from dataclasses import replace
from pathlib import Path

import pytest
from test_derived_table_reuse import _no_table_aggregate
from test_document_parsing_application import _prepared, _services, _successful_conversion
from test_ordering_projection import page_projection

from er_commons.artifact_io import (
    artifact_inventory,
    read_json_object,
    sha256_file,
    write_json_atomic,
    write_jsonl,
)
from er_commons.document_parsing.content_parsing import (
    application,
    derived_publication,
)
from er_commons.document_parsing.content_parsing.config import HeadingHierarchyConfig
from er_commons.document_parsing.content_parsing.conversion_seal import (
    ConversionCompletion,
)
from er_commons.document_parsing.content_parsing.evidence import write_inventory
from er_commons.document_parsing.content_parsing.ordering_projection import (
    OrderingProjectionArtifact,
    OrderingTableStageObservation,
    build_ordering_projection,
    capture_table_stage_reference,
    classify_table_evidence,
)


def _accepted_fixture(tmp_path: Path, *, complete_tables: bool = False):
    """Seal a one-page conversion with a preserved binary asset before enabling guards."""
    prepared = _prepared(tmp_path)
    root = tmp_path / "accepted" / prepared.conversion_identity.run_id
    _no_table_aggregate(root)
    _successful_conversion(root / "documents/document/producer")
    page = page_projection(1).model_copy(update={"source_id": "document"})
    ordering = build_ordering_projection(
        [page],
        [
            classify_table_evidence(
                physical_pdf_page=1, route="no_table_route", page_record=None, table_records=[]
            )
        ],
    )
    old = OrderingProjectionArtifact.model_validate_json(
        (root / "records/ordering_projection.json").read_bytes()
    )
    manifest = read_json_object(root / "tables/manifest.json")
    manifest["source_id"] = "document"
    write_json_atomic(root / "tables/manifest.json", manifest)
    projection = old.model_copy(
        update={
            "pages": ordering.pages,
            "decisions": ordering.decisions,
            "table_stage": capture_table_stage_reference(
                root, root / "tables", old.table_stage_observation.as_producer_record()
            ),
        }
    )
    write_json_atomic(root / "records/ordering_projection.json", projection.model_dump(mode="json"))
    (root / "tables/preserved.png").write_bytes(b"preserved image payload")
    if complete_tables:
        _write_complete_tables(root, prepared, page)
    write_json_atomic(
        root / "records/conversion_identity.json",
        {
            "conversion_id": prepared.conversion_identity.run_id,
            "identity": prepared.conversion_identity.payload,
        },
    )
    inventory = write_inventory(root)
    completion = ConversionCompletion(
        conversion_id=prepared.conversion_identity.run_id,
        status="complete",
        source_id="document",
        source_sha256=prepared.source.source_sha256,
        source_manifest_sha256=sha256_file(prepared.source_manifest_path),
        artifact_inventory_sha256=sha256_file(inventory),
        completed_at_utc="2026-01-01T00:00:00Z",
    )
    write_json_atomic(root / "records/completion_record.json", completion.model_dump(mode="json"))
    config = prepared.config.model_copy(
        update={
            "accepted_conversion_id": prepared.conversion_identity.run_id,
            "accepted_conversion_relative_root": root.relative_to(tmp_path),
            "producer_policy_version": "task03e-v1-task03g1a-v1",
            "configuration_id": (
                "docling_native_pypdfium2_heron_layout_heading_hierarchy_tableformer_fallback_cpu"
            ),
            "heading_hierarchy_options": HeadingHierarchyConfig(
                enabled=True,
                use_bookmarks=True,
                use_numbering=True,
                use_style=True,
                max_level=6,
                bookmark_match_threshold=0.8,
            ),
        }
    )
    config_path = tmp_path / "heading.json"
    write_json_atomic(config_path, config.model_dump(mode="json"))
    return replace(prepared, config=config), config_path, root


def _write_complete_tables(root, prepared, page):
    """Add one real canonical table and a sealed positive-route aggregate projection."""
    tables = root / "tables"
    (tables / "no_table_stage.json").unlink()
    write_json_atomic(
        tables / "summary.json",
        {
            "physical_pdf_pages": [1],
            "page_count": 1,
            "logical_table_count": 1,
            "family_count": 1,
            "zero_table_pages": [],
            "review_derivatives_retained": False,
        },
    )
    write_jsonl(tables / "pages.jsonl", [{"physical_pdf_page": 1, "table_count": 1}])
    write_jsonl(tables / "tables.jsonl", [{"table_id": "table1", "physical_pdf_page": 1}])
    write_jsonl(
        tables / "family_assignments.jsonl", [{"table_id": "table1", "family_id": "family1"}]
    )
    write_json_atomic(
        tables / "table_families.json",
        {"families": [{"family_id": "family1", "table_ids": ["table1"]}]},
    )
    write_json_atomic(
        tables / "configuration.json",
        {
            "source_id": prepared.source.source_id,
            "expected_source_sha256": prepared.source.source_sha256,
            "expected_pdf_page_count": prepared.source.source_page_count,
            "detection": prepared.config.table_detection.model_dump(mode="json"),
            "cleanup": prepared.config.table_cleanup.model_dump(mode="json"),
            "learned_fallback": prepared.config.learned_table_fallback.model_dump(mode="json"),
            "routed_pages": [
                {
                    "physical_pdf_page": 1,
                    "route": "full_page_numeric",
                    "layout_regions_pdf_points_bottom_left": [],
                }
            ],
        },
    )
    write_json_atomic(
        tables / "artifact_inventory.json",
        artifact_inventory(tables, {"artifact_inventory.json", "manifest.json"}),
    )
    write_json_atomic(
        tables / "manifest.json",
        {"source_id": "document", "artifact_inventory": "artifact_inventory.json"},
    )
    features = {
        **page.features,
        "text_width_fraction": 0.9,
        "text_height_fraction": 0.9,
        "nonempty_line_count": 100,
        "nonspace_characters_per_square_point": 0.05,
        "digit_fraction": 0.8,
    }
    page = page.model_copy(update={"features": features})
    ordering = build_ordering_projection(
        [page],
        [
            classify_table_evidence(
                physical_pdf_page=1, route="full_page_numeric", page_record=None, table_records=[]
            )
        ],
    )
    observation = OrderingTableStageObservation(
        status="complete",
        document_scope_complete=True,
        routed_pages=(1,),
        routed_page_count=1,
        logical_table_count=1,
        family_assignment_count=1,
        family_count=1,
        zero_table_pages=(),
        manifest="documents/document/producer/tables/manifest.json",
    )
    projection = OrderingProjectionArtifact(
        pages=ordering.pages,
        decisions=ordering.decisions,
        table_stage_observation=observation,
        table_stage=capture_table_stage_reference(root, tables, observation.as_producer_record()),
    )
    write_json_atomic(root / "records/ordering_projection.json", projection.model_dump(mode="json"))


@pytest.mark.parametrize(
    "mutation", [None, "missing_projection", "changed_projection", "asset_size"]
)
@pytest.mark.parametrize("complete_tables", [False, True])
def test_accepted_aggregate_publication_never_opens_payload_or_invokes_extraction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str | None,
    complete_tables: bool,
) -> None:
    """Do not mock the derived stage, inventory writer, publisher or completion verifier."""
    prepared, config_path, root = _accepted_fixture(tmp_path, complete_tables=complete_tables)
    if mutation == "missing_projection":
        (root / "records/ordering_projection.json").unlink()
    elif mutation == "changed_projection":
        path = root / "records/ordering_projection.json"
        path.write_bytes(
            path.read_bytes().replace(b'"source_id": "document"', b'"source_id": "changed!"')
        )
    elif mutation == "asset_size":
        (root / "tables/preserved.png").write_bytes(b"changed")
    original = Path.open

    def guarded(path, *args, **kwargs):
        if path.suffix.lower() in {".pdf", ".png", ".pt", ".safetensors"}:
            pytest.fail(f"source/image/model payload opened: {path}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    original_os_open = os.open

    def guarded_os_open(path, *args, **kwargs):
        if isinstance(path, (str, Path)) and Path(path).suffix.lower() in {".pdf", ".png", ".pt"}:
            pytest.fail(f"source/image/model payload descriptor opened: {path}")
        return original_os_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", guarded_os_open)
    monkeypatch.setattr(application, "prepare_content_parsing", lambda *a, **kw: prepared)
    monkeypatch.setattr(application, "read_accepted_conversion", lambda *a, **kw: None)

    def forbidden(*args, **kwargs):
        pytest.fail("accepted aggregate invoked conversion, PDF routing or table extraction")

    monkeypatch.setattr(application, "ensure_conversion_bundle", forbidden)
    monkeypatch.setattr(derived_publication, "route_complete_document", forbidden)
    monkeypatch.setattr(derived_publication, "run_complete_table_stage", forbidden)
    if mutation is not None:
        with pytest.raises(ValueError):
            application.run_document_parsing(tmp_path, config_path, services=_services())
        assert not (
            tmp_path / prepared.config.artifact_relative_root / prepared.identity.run_id
        ).exists()
        return
    completion = application.run_document_parsing(tmp_path, config_path, services=_services())
    final = completion.parents[1]
    assert read_json_object(final / "records/conversion_input.json")["document_view"] == "heading"
    assert (final / "documents/document/producer/tables/preserved.png").samefile(
        root / "tables/preserved.png"
    )
    assert (
        application.run_document_parsing(tmp_path, config_path, services=_services()) == completion
    )
