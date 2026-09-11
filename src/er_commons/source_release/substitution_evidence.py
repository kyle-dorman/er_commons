"""Compact accepted-evidence checks for the bounded F1 substitution request."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from er_commons.artifact_io import assert_contained
from er_commons.source_release.qualification_request import QualifiedAcquisitionSpec


def _read_compact(path: Path) -> bytes:
    """Reject oversized or symbolic metadata before reading its bounded bytes."""
    if path.is_symlink() or path.stat().st_size > 1_048_576:
        raise ValueError(f"expected compact regular evidence: {path}")
    return path.read_bytes()


def validate_substitution_evidence(data_root: Path, spec: QualifiedAcquisitionSpec) -> None:
    """Bind exact census IDs and the original manifest seal without PDF reads."""
    provenance = spec.provenance
    census_path = assert_contained(data_root, provenance.census_ref.relative_path)
    raw = _read_compact(census_path)
    if hashlib.sha256(raw).hexdigest() != provenance.census_ref.sha256:
        raise ValueError("F1 census digest differs from the reviewed request")
    census: dict[str, Any] = json.loads(raw)
    if census.get("format") != "er_commons.task06a.f1_substitution_evidence.v1":
        raise ValueError("unsupported F1 census schema")
    selected = census["selected_inventory_records"]
    if len(selected) != 1 or (
        selected[0]["linked_url"] != spec.source_url
        or selected[0]["document_center_id"] != spec.policy.expected_document_center_id
        or selected[0]["label"] != spec.policy.advertised_label
    ):
        raise ValueError("selected source differs from accepted landing inventory")
    wrong = census["wrong_source_records"]
    if len(wrong) != 1 or (
        wrong[0]["source_id"] != provenance.logical_source_id
        or wrong[0]["sha256"] != provenance.wrong_source_sha256
        or census["wrong_source_manifest_path"] != provenance.original_release_ref.relative_path
    ):
        raise ValueError("wrong-source binding differs from accepted census")
    contexts = {row["unit"]["unit_id"] for row in census["revision_contexts"]}
    if contexts != set(provenance.revision_context_unit_ids):
        raise ValueError("revision contexts differ from accepted census")
    manifest_path = assert_contained(data_root, provenance.original_release_ref.relative_path)
    completion = json.loads(_read_compact(manifest_path.parent / "completion_record.json"))
    sealed = completion["manifest"]
    if (
        completion.get("schema_version") != "er_commons.source_release_completion.v1"
        or sealed["local_path"] != provenance.original_release_ref.relative_path
        or sealed["sha256"] != provenance.original_release_ref.sha256
        or manifest_path.stat().st_size != sealed["byte_size"]
    ):
        raise ValueError("original source manifest seal differs from reviewed request")
