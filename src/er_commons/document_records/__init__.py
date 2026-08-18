"""Map parsed document evidence into repository records and relationships."""

from er_commons.document_records.document_references import link_document_references
from er_commons.document_records.document_structure import map_document_structure
from er_commons.document_records.record_mapping import map_document_records

__all__ = ["link_document_references", "map_document_records", "map_document_structure"]
