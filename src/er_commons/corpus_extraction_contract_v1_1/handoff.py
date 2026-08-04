"""Exact prerequisite and ready/blocked derivation for handoff v1.1."""

from __future__ import annotations

import json
from typing import Any, cast

from er_commons.corpus_extraction_contract_v1_1.accounting import (
    ScopeEvidence,
    unavailable_source_digest,
    validate_unavailable_sources,
)
from er_commons.corpus_extraction_contract_v1_1.checks import canonical_sha256, fail, verify_ref
from er_commons.corpus_extraction_contract_v1_1.identity import validate_handoff_id
from er_commons.corpus_extraction_contract_v1_1.model import ArtifactReader, JsonObject


def validate_candidate_handoff(
    bundle: JsonObject,
    scope: ScopeEvidence,
    reader: ArtifactReader,
) -> None:
    """Require exact completions and mechanically derived handoff disposition."""
    handoff = cast(JsonObject, bundle["handoff"])
    accounting = cast(JsonObject, bundle["accounting"])
    index = cast(JsonObject, bundle["target_index"])
    resolution = cast(JsonObject, bundle["resolution_completion"])

    _require_exact_prerequisite(
        cast(JsonObject, handoff["accounting_completion_ref"]), accounting, reader, "accounting"
    )
    _require_exact_prerequisite(
        cast(JsonObject, handoff["index_completion_ref"]), index, reader, "index"
    )
    _require_exact_prerequisite(
        cast(JsonObject, handoff["resolution_completion_ref"]),
        resolution,
        reader,
        "resolution",
    )
    if (
        handoff["scope_id"] != accounting["scope_id"]
        or handoff["index_id"] != index["index_id"]
        or handoff["resolution_id"] != resolution["resolution_id"]
        or index["accounting_ref"] != handoff["accounting_completion_ref"]
        or resolution["index_completion_ref"] != handoff["index_completion_ref"]
    ):
        fail("handoff_prerequisite", "handoff references stale prerequisites")

    unavailable = validate_unavailable_sources(
        cast(list[JsonObject], index["unavailable_sources"]), scope, reader
    )
    policy = cast(str, handoff["blocking_policy"])
    policy_value = _read_json_value(cast(JsonObject, handoff["blocking_policy_ref"]), reader)
    if policy_value != policy:
        fail("handoff_policy", "blocking-policy bytes differ from the handoff")
    expected_reasons = _expected_blocking_reasons(policy, scope, unavailable)
    expected_status = "blocked" if expected_reasons else "ready"
    if handoff["status"] != expected_status or handoff["blocking_reasons"] != expected_reasons:
        fail("handoff_policy", "handoff status or blocking reasons do not derive from policy")
    if handoff["task04_status"] != "not_evaluated" or bundle["task04_freezes"]:
        fail("task04_boundary", "Task 03F cannot issue a Task 04 disposition")

    inventory_ref = cast(JsonObject, handoff["artifact_inventory"])
    verify_ref(inventory_ref, reader)
    preimage = cast(JsonObject, handoff["identity_preimage"])
    if _read_json_object(cast(JsonObject, handoff["identity_preimage_ref"]), reader) != preimage:
        fail("handoff_identity", "persisted handoff preimage bytes differ")
    expected_preimage = {
        "schema_version": "er_commons.candidate_handoff_identity.v1_1",
        "production_extraction_id": bundle["production_extraction_id"],
        "scope_id": handoff["scope_id"],
        "accounting_completion_sha256": handoff["accounting_completion_ref"]["sha256"],
        "index_completion_sha256": handoff["index_completion_ref"]["sha256"],
        "resolution_completion_sha256": handoff["resolution_completion_ref"]["sha256"],
        "blocking_policy_sha256": handoff["blocking_policy_ref"]["sha256"],
        "status": expected_status,
        "blocking_reasons_sha256": canonical_sha256(expected_reasons),
        "task04_status": "not_evaluated",
        "managed_inventory_sha256": inventory_ref["sha256"],
    }
    if preimage != expected_preimage:
        fail("handoff_identity", "handoff preimage does not bind exact prerequisites")
    validate_handoff_id(cast(str, handoff["handoff_id"]), preimage)


def _expected_blocking_reasons(
    policy: str,
    scope: ScopeEvidence,
    unavailable: dict[str, JsonObject],
) -> list[JsonObject]:
    if policy == "terminal_failures_allowed":
        return []
    if policy != "all_sources_successful":
        fail("handoff_policy", "unknown handoff blocking policy")
    source_ids = sorted(scope.failed_rows, key=scope.source_ordinals.__getitem__)
    return [
        {
            "code": "terminal_source_failure",
            "source_id": source_id,
            "transaction_id": scope.failed_rows[source_id]["transaction_id"],
            "unavailable_source_sha256": unavailable_source_digest(unavailable[source_id]),
        }
        for source_id in source_ids
    ]


def _require_exact_prerequisite(
    reference: JsonObject,
    expected: JsonObject,
    reader: ArtifactReader,
    label: str,
) -> None:
    if _read_json_object(reference, reader) != expected:
        fail("handoff_prerequisite", f"{label} completion bytes differ")
    if expected.get("status") != "complete" or expected.get("completion_last") is not True:
        fail("handoff_prerequisite", f"{label} prerequisite is not complete")


def _read_json_object(reference: JsonObject, reader: ArtifactReader) -> JsonObject:
    value = _read_json_value(reference, reader)
    if not isinstance(value, dict):
        fail("artifact_json", "referenced artifact must contain one JSON object")
    return value


def _read_json_value(reference: JsonObject, reader: ArtifactReader) -> Any:
    try:
        return json.loads(verify_ref(reference, reader))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail("artifact_json", f"referenced artifact is not valid JSON: {error}")
