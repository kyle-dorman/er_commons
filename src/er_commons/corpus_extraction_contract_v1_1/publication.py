"""Operational corpus-stage attempt and completion-reference validation."""

from __future__ import annotations

import json
from typing import cast

from er_commons.corpus_extraction_contract_v1_1.checks import fail, verify_ref
from er_commons.corpus_extraction_contract_v1_1.model import ArtifactReader, JsonObject


def validate_stage_attempts(bundle: JsonObject, reader: ArtifactReader) -> None:
    """Require one completed operational envelope for every semantic stage."""
    accounting = cast(JsonObject, bundle["accounting"])
    index = cast(JsonObject, bundle["target_index"])
    resolution = cast(JsonObject, bundle["resolution_completion"])
    handoff = cast(JsonObject, bundle["handoff"])
    expected = {
        "accounting": (accounting["scope_id"], accounting),
        "target_index": (index["index_id"], index),
        "resolution": (resolution["resolution_id"], resolution),
        "handoff": (handoff["handoff_id"], handoff),
    }
    attempts = cast(list[JsonObject], bundle["corpus_stage_attempts"])
    grouped: dict[str, list[JsonObject]] = {stage_type: [] for stage_type in expected}
    observed_order: list[str] = []
    for attempt in attempts:
        stage_type = cast(str, attempt["stage_type"])
        if stage_type not in grouped:
            fail("stage_attempts", "corpus-stage attempt has an unknown stage")
        if not observed_order or observed_order[-1] != stage_type:
            observed_order.append(stage_type)
        grouped[stage_type].append(attempt)
    if observed_order != list(expected) or any(not rows for rows in grouped.values()):
        fail("stage_attempts", "corpus-stage attempts are absent or unordered")

    for stage_type, stage_attempts in grouped.items():
        stage_id, completion = expected[stage_type]
        if [attempt["attempt"] for attempt in stage_attempts] != list(
            range(1, len(stage_attempts) + 1)
        ):
            fail("stage_attempts", "stage attempt numbers are not contiguous")
        for attempt in stage_attempts:
            if attempt["stage_id"] != stage_id:
                fail("stage_attempts", "attempt references the wrong semantic stage")
            for reference in cast(list[JsonObject], attempt["state_event_refs"]):
                verify_ref(reference, reader)
        for attempt in stage_attempts[:-1]:
            if (
                attempt["disposition"] not in {"failed_retryable", "cancelled"}
                or not attempt["failure_class"]
                or attempt["completion_ref"] is not None
            ):
                fail("stage_attempts", "prior attempt is not a retained nonpublication")
        final = stage_attempts[-1]
        if (
            final["disposition"] != "complete"
            or final["failure_class"] is not None
            or final["completion_ref"] is None
        ):
            fail("stage_attempts", "published stage lacks a final completed attempt")
        referenced = _json(cast(JsonObject, final["completion_ref"]), reader)
        if referenced != completion:
            fail("stage_attempts", "stage completion reference differs", subject=stage_type)


def _json(reference: JsonObject, reader: ArtifactReader) -> JsonObject:
    try:
        value = json.loads(verify_ref(reference, reader))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail("artifact_json", f"stage completion is invalid JSON: {error}")
    if not isinstance(value, dict):
        fail("artifact_json", "stage completion must be an object")
    return value
