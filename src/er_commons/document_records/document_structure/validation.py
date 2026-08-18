"""Public orchestration for canonical semantic-structure validation.

JSON Schema owns individual record shapes. The policy checks below own
relationships that only become meaningful across a complete semantic bundle.
"""

from __future__ import annotations

from typing import Any

from er_commons.document_records.document_structure.bundle import DocumentStructureBundleView
from er_commons.document_records.document_structure.policies.aliases import validate_target_aliases
from er_commons.document_records.document_structure.policies.bridge import (
    BridgeEvidence,
    validate_cross_producer_bridge,
)
from er_commons.document_records.document_structure.policies.control import (
    validate_control_provenance,
)
from er_commons.document_records.document_structure.policies.correspondence import (
    validate_candidate_correspondence,
)
from er_commons.document_records.document_structure.policies.page_labels import validate_page_labels
from er_commons.document_records.document_structure.policies.sections import validate_sections


def validate_document_structure_contract(
    bundle: dict[str, Any],
    *,
    bridge_evidence: BridgeEvidence,
) -> None:
    """Validate cross-record policy after JSON Schema shape validation.

    Callers must validate the bundle against the published Draft 2020-12 schema
    first. This function deliberately assumes required fields and primitive
    types already exist so each failure can describe a semantic relationship.
    """
    validate_control_provenance(bundle["control_provenance"])
    view = DocumentStructureBundleView(bundle)
    validate_sections(view)
    validate_page_labels(view)
    validate_target_aliases(view)
    validate_cross_producer_bridge(view, bridge_evidence)
    validate_candidate_correspondence(bundle["correspondence_report"])
