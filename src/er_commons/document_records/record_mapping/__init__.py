"""Public helpers for mapping and validating canonical document records."""

from er_commons.document_records.record_mapping.errors import MappingContractError
from er_commons.document_records.record_mapping.geometry import pdf_bbox_to_render_pixels
from er_commons.document_records.record_mapping.identifiers import make_record_id
from er_commons.document_records.record_mapping.identity import extraction_identity_sha256
from er_commons.document_records.record_mapping.materialize import map_document_records
from er_commons.document_records.record_mapping.validation import validate_bundle_integrity

__all__ = [
    "MappingContractError",
    "extraction_identity_sha256",
    "make_record_id",
    "pdf_bbox_to_render_pixels",
    "map_document_records",
    "validate_bundle_integrity",
]
