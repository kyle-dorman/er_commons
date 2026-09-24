"""Replay source production from sealed page observations without opening a PDF."""

from __future__ import annotations

import copy
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import read_json_object, read_jsonl, sha256_file, write_json_atomic
from er_commons.response_inventory.acceptance import validate_task05d_candidate
from er_commons.response_inventory.full_workflow import build_complete_inventory
from er_commons.response_inventory.observations import PageObservation
from er_commons.response_inventory.qualification import validate_qualification_report
from er_commons.response_inventory.run_spec import (
    ResponseInventoryRunSpecV2,
    load_response_inventory_run_spec,
)
from er_commons.response_inventory.workflow import _load_observations


def replay_saved_source(
    run_spec_path: Path,
    repository_root: Path,
    artifact_root: Path,
    *,
    saved_candidate: Path,
    saved_cache: Path,
    visual_dispositions: Mapping[int, Mapping[str, str]] | None = None,
) -> dict[str, Any]:
    """Renew receipts and review under current code using verified historical evidence.

    The accepted qualification seals every observation and render. Historical
    decisions are never applied automatically: callers must compare the fresh
    review population before passing dispositions on a later invocation.
    """
    validation = validate_task05d_candidate(saved_candidate, artifact_root)
    acceptance = read_json_object(saved_candidate.with_suffix(".acceptance.json"))
    if acceptance.get("completion_id") != validation["completion_id"]:
        raise ValueError("saved evidence acceptance differs from the sealed candidate")
    records = list(read_jsonl(saved_candidate / "inventory/source_records.jsonl"))
    activity = cast(
        dict[str, Any], next(row for row in records if row["record_type"] == "activity")
    )
    spec, _ = load_response_inventory_run_spec(run_spec_path)
    if not isinstance(spec, ResponseInventoryRunSpecV2):
        raise ValueError("saved replay requires a Task 05D run specification")
    source_identity = f"{spec.source.source_id}@{spec.source.recorded_sha256}"
    if not any(ref["identity"] == source_identity for ref in activity["input_refs"]):
        raise ValueError("saved evidence names a different source")
    observations = _load_observations(saved_cache / "ranges/000001-000744/observations.json")
    if observations is None:
        raise ValueError("saved page observations are missing or invalid")
    qualification = cast(
        dict[str, Any], read_json_object(saved_candidate / "diagnostics/qualification.json")
    )
    original_render_root = saved_cache / "qualification"
    validate_qualification_report(qualification, observations, original_render_root)

    def reader(_pdf: Path, first: int, last: int) -> list[PageObservation]:
        """Return exactly the requested saved page range, never reading the source."""
        result = [page for page in observations if first <= page.physical_page <= last]
        if [page.physical_page for page in result] != list(range(first, last + 1)):
            raise ValueError("saved observations do not close the requested range")
        return result

    def qualifier(_pdf: Path, current: Sequence[PageObservation], output: Path) -> dict[str, Any]:
        """Preserve validated render bytes while renewing the independent review base."""
        fresh = copy.deepcopy(qualification)
        for row in fresh["pages"]:
            relative = row["render_path"]
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if sha256_file(target) != row["render_sha256"]:
                    raise ValueError("saved render replay would clobber different evidence")
            else:
                shutil.copy2(original_render_root / relative, target)
            row["visual_disposition"] = None
        validate_qualification_report(fresh, current, output)
        write_json_atomic(
            output / "saved_evidence_provenance.json",
            {
                "schema_version": "er_commons.saved_source_replay.v1",
                "source_pdf_accessed": False,
                "saved_candidate": str(saved_candidate.relative_to(artifact_root)),
                "saved_completion_id": validation["completion_id"],
                "saved_qualification_sha256": sha256_file(
                    saved_candidate / "diagnostics/qualification.json"
                ),
                "saved_observations_sha256": sha256_file(
                    saved_cache / "ranges/000001-000744/observations.json"
                ),
            },
        )
        return fresh

    return build_complete_inventory(
        run_spec_path,
        repository_root,
        artifact_root,
        page_reader=reader,
        page_qualifier=qualifier,
        visual_dispositions=visual_dispositions,
        tool_versions={
            key: value for key, value in activity["tool_versions"].items() if key != "pypdfium2"
        },
    )
