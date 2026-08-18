"""Detect and link references within one document's record bundle."""

from er_commons.document_records.document_references.errors import ContractViolation
from er_commons.document_records.document_references.types import (
    DocumentReferenceMention,
    TargetCandidate,
)
from er_commons.document_records.document_references.workflow import link_document_references

__all__ = [
    "ContractViolation",
    "DocumentReferenceMention",
    "TargetCandidate",
    "link_document_references",
]
