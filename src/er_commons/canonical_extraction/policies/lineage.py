"""Document-scope, producer-lineage, and cross-reference policies."""

from __future__ import annotations

from er_commons.canonical_extraction.bundle import (
    BundleView,
    Record,
    raw_links,
    references,
    regions,
)
from er_commons.canonical_extraction.errors import ContractError
from er_commons.canonical_extraction.identifiers import record_type

MAPPED_CONTENT_COLLECTIONS = (
    "blocks",
    "tables",
    "table_families",
    "figures",
    "images",
)

# A raw link names the project stage that interpreted an asset. These are the
# asset producers that can legitimately supply evidence to that stage.
COMPATIBLE_ASSET_PRODUCERS = {
    "docling": {"docling"},
    "pdfium_router": {"pdfium_router"},
    "camelot_clean_pipeline": {"camelot_clean_pipeline"},
    "project_cleanup": {"camelot_clean_pipeline", "project"},
    "project_family_assignment": {"camelot_clean_pipeline", "project"},
}


def relationships_stay_within_documents(view: BundleView) -> None:
    """Prevent record relationships from crossing source-document scope."""
    document_owned_collections = (
        "pages",
        "sections",
        "blocks",
        "tables",
        "table_families",
        "figures",
        "images",
        "assets",
        "cross_references",
        "conversion_observations",
    )
    for record in view.from_collections(*document_owned_collections):
        document_id = record["document_id"]
        _require_same_document_references(view, record, document_id)
        for region in regions(record):
            if view.page_document_by_id[region["page_id"]] != document_id:
                raise ContractError(f"cross-document region from {record['id']}")

    observations = view.from_collections("routing_observations", "table_stage_observations")
    for observation in observations:
        page_id = observation["page_id"]
        document_id = view.page_document_by_id[page_id]
        _require_same_document_references(view, observation, document_id)
        if record_type(observation["id"]) == "table-stage-observation":
            for table_id in observation["canonical_table_ids"]:
                table_page_ids = {
                    region["page_id"] for region in view.records_by_id[table_id]["regions"]
                }
                if page_id not in table_page_ids:
                    raise ContractError(f"cross-page table mapping from {observation['id']}")


def _require_same_document_references(view: BundleView, record: Record, document_id: str) -> None:
    for target_id in references(record):
        target_document_id = view.records_by_id[target_id].get("document_id")
        if target_document_id is not None and target_document_id != document_id:
            raise ContractError(f"cross-document reference from {record['id']}")


def raw_mapping_coverage_is_complete(view: BundleView) -> None:
    """Require raw lineage for every canonical content record."""
    mapped_ids = {mapping["canonical_record_id"] for mapping in view.bundle["raw_mappings"]}
    required_ids = {record["id"] for record in view.from_collections(*MAPPED_CONTENT_COLLECTIONS)}
    missing = sorted(required_ids - mapped_ids)
    if missing:
        raise ContractError(f"canonical records missing raw mappings: {missing}")


def raw_link_producers_are_compatible(view: BundleView) -> None:
    """Ensure each raw-link interpretation names a compatible asset producer."""
    for record in view.records:
        for link in raw_links(record):
            asset = view.records_by_id[link["asset_id"]]
            allowed_producers = COMPATIBLE_ASSET_PRODUCERS[link["producer"]]
            if asset["producer"] not in allowed_producers:
                raise ContractError(f"raw-link producer differs from asset: {record['id']}")

    for mapping in view.bundle["raw_mappings"]:
        target = view.records_by_id[mapping["canonical_record_id"]]
        for link in mapping["raw_links"]:
            asset = view.records_by_id[link["asset_id"]]
            if asset["document_id"] != target["document_id"]:
                raise ContractError(f"cross-document raw mapping: {mapping['id']}")


def cross_reference_statuses_are_consistent(view: BundleView) -> None:
    """Tie resolution status to the number of resolved targets."""
    for cross_reference in view.bundle["cross_references"]:
        targets = cross_reference["target_record_ids"]
        status = cross_reference["resolution_status"]
        if status == "resolved" and len(targets) != 1:
            raise ContractError("resolved cross-reference requires exactly one target")
        if status == "ambiguous" and len(targets) < 2:
            raise ContractError("ambiguous cross-reference requires multiple targets")
        if status == "unresolved" and targets:
            raise ContractError("unresolved cross-reference cannot have targets")


def caption_links_target_captions(view: BundleView) -> None:
    """Require table and figure caption links to point to caption blocks."""
    for record in view.from_collections("tables", "figures"):
        for block_id in record["caption_block_ids"]:
            block = view.records_by_id[block_id]
            if block["block_type"] != "caption":
                raise ContractError(f"caption link does not target a caption: {record['id']}")
