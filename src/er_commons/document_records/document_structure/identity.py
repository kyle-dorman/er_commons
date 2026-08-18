"""Expanded, non-circular identity for document-structure candidates."""

from __future__ import annotations

import copy
import hashlib
import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import rfc8785

from er_commons.artifact_io import sha256_file
from er_commons.document_records.document_structure.config import DocumentStructureConfig
from er_commons.document_records.document_structure.inputs import DocumentStructureInputs
from er_commons.document_records.record_mapping.candidate_identity import owned_code_digest
from er_commons.document_records.record_mapping.identity import extraction_identity_sha256

JsonObject = dict[str, Any]
_CANDIDATE_ID_PREFIX = re.compile(r"^exv1-[0-9a-f]{64}(?=/|$)")
_CANDIDATE_SCOPED_RECORD_ID = re.compile(r"^exv1-[0-9a-f]{64}/")
_BRIDGE_ID_PLACEHOLDER = "<EXTRACTION_ID>"


def _canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def normalized_bridge_preimage(
    entries: Sequence[JsonObject],
) -> list[JsonObject]:
    """Remove only candidate-ID prefixes from canonical bridge targets.

    The bridge rows must name candidate-scoped canonical records, while the
    candidate ID itself binds the bridge. Hashing this explicit preimage breaks
    that cycle without discarding stable keys, producer pointers, dispositions,
    target record types, or local target identities.
    """
    normalized = copy.deepcopy(list(entries))
    for entry in normalized:
        canonical_ids = entry.get("canonical_record_ids")
        if not isinstance(canonical_ids, list):
            raise ValueError("bridge entry canonical_record_ids must be a list")
        for index, record_id in enumerate(canonical_ids):
            if (
                not isinstance(record_id, str)
                or _CANDIDATE_SCOPED_RECORD_ID.match(record_id) is None
            ):
                raise ValueError("mapped bridge targets must use a candidate-scoped record ID")
            canonical_ids[index] = _CANDIDATE_ID_PREFIX.sub(_BRIDGE_ID_PLACEHOLDER, record_id)
    return normalized


def normalized_bridge_preimage_sha256(entries: Sequence[JsonObject]) -> str:
    """Hash the ordered, candidate-ID-independent bridge preimage."""
    return _canonical_json_sha256(normalized_bridge_preimage(entries))


def normalized_support_preimage_sha256(value: Any) -> str:
    """Hash support after replacing exact or record-scoped candidate IDs."""

    def normalize(item: Any) -> Any:
        if isinstance(item, str):
            return _CANDIDATE_ID_PREFIX.sub(_BRIDGE_ID_PLACEHOLDER, item)
        if isinstance(item, list):
            return [normalize(child) for child in item]
        if isinstance(item, dict):
            return {key: normalize(child) for key, child in item.items()}
        return item

    return _canonical_json_sha256(normalize(copy.deepcopy(value)))


def build_document_structure_identity(
    *,
    project_root: Path,
    config_path: Path,
    config: DocumentStructureConfig,
    inputs: DocumentStructureInputs,
    bridge_entries: Sequence[JsonObject],
    support_preimages: Mapping[str, Any],
    owned_paths: Iterable[Path],
) -> JsonObject:
    """Bind every accepted v2 identity input and derive the new exv1 ID."""
    semantic_spec_path = project_root / config.semantic_spec_relative_path
    semantic_schema_path = project_root / config.semantic_schema_relative_path
    code_paths = tuple(owned_paths)
    if not code_paths:
        raise ValueError("semantic identity must bind at least one owned code path")
    producer_inputs: JsonObject = {
        "baseline": {
            "producer_run_id": inputs.baseline_producer.run_id,
            "completion": inputs.baseline_producer.completion_ref.as_dict(),
            "inventory": inputs.baseline_producer.inventory_ref.as_dict(),
        },
        "hierarchy": {
            "producer_run_id": inputs.hierarchy_producer.run_id,
            "completion": inputs.hierarchy_producer.completion_ref.as_dict(),
            "inventory": inputs.hierarchy_producer.inventory_ref.as_dict(),
        },
        "comparison": (
            inputs.producer_comparison_ref.as_dict()
            if inputs.producer_comparison_ref is not None
            else None
        ),
    }
    hierarchy_correction: JsonObject = {
        "candidate_id": config.hierarchy_candidate_id,
        "completion": inputs.hierarchy_completion_ref.as_dict(),
        "inventory": inputs.hierarchy_inventory_ref.as_dict(),
    }
    if config.control_profile == "task03e2d_bounded":
        assert inputs.bounded_acceptance_ref is not None
        hierarchy_correction.update(
            {
                "semantic_file_set_sha256": inputs.control_provenance["semantic_file_set_sha256"],
                "aggregate_semantic_sha256": inputs.control_provenance["aggregate_semantic_sha256"],
                "bounded_control": inputs.control_provenance,
                "bounded_acceptance": inputs.bounded_acceptance_ref.as_dict(),
            }
        )
    else:
        hierarchy_correction["strict_control"] = inputs.control_provenance
    identity: JsonObject = {
        "schema_version": "er_commons.extraction_identity.v2",
        "extraction_version_name": config.candidate_version_name,
        "materialization_scope": {
            "scope_kind": "document_candidate",
            "release_status": "non_release_candidate",
            "source_id": config.source.source_id,
            "source_sha256": config.source.source_sha256,
            "physical_page_count": config.source.physical_page_count,
            "source_manifest": inputs.source_manifest_ref.as_dict(),
        },
        "baseline_canonical": {
            "candidate_id": config.baseline_candidate_id,
            "completion": inputs.baseline_completion_ref.as_dict(),
            "inventory": inputs.baseline_inventory_ref.as_dict(),
        },
        "producer_inputs": producer_inputs,
        "hierarchy_correction": hierarchy_correction,
        "semantic_contract": {
            "policy_version": config.semantic_policy_version,
            "specification": {
                "path": config.semantic_spec_relative_path.as_posix(),
                "sha256": sha256_file(semantic_spec_path),
            },
            "schema": {
                "path": config.semantic_schema_relative_path.as_posix(),
                "sha256": sha256_file(semantic_schema_path),
            },
            "configuration": {
                "path": config_path.relative_to(project_root).as_posix(),
                "sha256": sha256_file(config_path),
            },
            "bridge_preimage_sha256": normalized_bridge_preimage_sha256(bridge_entries),
            "support_preimage_sha256s": {
                role: normalized_support_preimage_sha256(payload)
                for role, payload in sorted(support_preimages.items())
            },
            "owned_code_bundle_sha256": owned_code_digest(
                project_root, tuple(sorted(path.resolve() for path in code_paths))
            ),
        },
    }
    digest = extraction_identity_sha256(identity)
    identity["extraction_id"] = f"exv1-{digest}"
    identity["identity_sha256"] = digest
    return identity
