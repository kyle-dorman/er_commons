"""Stable facade for immutable canonical record-mapping context."""

from er_commons.document_records.record_mapping.context_assembly import (
    build_record_mapping_context,
)
from er_commons.document_records.record_mapping.context_types import (
    PageSize,
    RecordIds,
    RecordMappingContext,
    TraversalContext,
)

__all__ = [
    "PageSize",
    "RecordIds",
    "RecordMappingContext",
    "TraversalContext",
    "build_record_mapping_context",
]
