"""Policy for declared differences between canonical v1 and semantic v2."""

from __future__ import annotations

from typing import Any

from er_commons.document_records.document_structure.constants import ALLOWED_DIFFERENCE_CATEGORIES
from er_commons.document_records.document_structure.errors import StructureContractError


def validate_candidate_correspondence(report: dict[str, Any]) -> None:
    """Require a new identity and reject every undeclared baseline change."""
    if report["baseline_candidate_id"] == report["new_candidate_id"]:
        raise StructureContractError(
            "document-structure mapping must create a new candidate identity"
        )
    if report["undeclared_difference_count"] != 0:
        raise StructureContractError("candidate comparison contains undeclared differences")
    if tuple(report["allowed_difference_categories"]) != ALLOWED_DIFFERENCE_CATEGORIES:
        raise StructureContractError("allowed-difference vocabulary differs")
