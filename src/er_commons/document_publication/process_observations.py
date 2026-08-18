"""Translate process-specific summaries into publication handoff vocabulary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, cast

from er_commons.document_publication.process_validation import ProcessCompletions

DoclingStatus = Literal["SUCCESS", "PARTIAL_SUCCESS", "FAILURE", "SKIPPED"]


def content_parse_page_count(completion: Path) -> int:
    """Read the physical-page count from a verified producer summary."""
    summary = _json(completion.parent / "producer_summary.json")
    value = summary["physical_page_count"]
    if not isinstance(value, int):
        raise ValueError(f"producer page count is invalid: {completion}")
    return value


def content_parse_observations(
    completion: Path,
) -> tuple[DoclingStatus, list[dict[str, object]]]:
    """Read required raw conversion status and structured errors."""
    summary = _json(completion.parent / "producer_summary.json")
    source_id = summary["source_id"]
    producer_root = completion.parents[1] / "documents" / str(source_id) / "producer"
    observation_path = producer_root / "docling" / "conversion_observation.json"
    observation = _json(observation_path) if observation_path.is_file() else {}
    raw = str(observation.get("raw_status", "SUCCESS")).upper()
    if raw not in {"SUCCESS", "PARTIAL_SUCCESS", "FAILURE", "SKIPPED"}:
        raise ValueError(f"unsupported raw Docling status: observed={raw}, path={observation_path}")
    errors = observation.get("errors", [])
    if not isinstance(errors, list):
        raise ValueError(f"producer errors are not a list: {observation_path}")
    return cast(DoclingStatus, raw), list(errors)


def collect_process_warnings(completions: ProcessCompletions) -> list[str]:
    """Collect declared warnings from each verified document product."""
    warnings: list[str] = []
    for role, completion in completions.as_dict().items():
        root = completion.parents[1]
        status = _json(completion).get("status")
        if isinstance(status, str) and status not in {"complete", "success"}:
            warnings.append(f"{role} status: {status}")
        for relative in _summary_paths():
            path = root / relative
            if not path.is_file():
                continue
            summary = _json(path)
            _append_warning_fields(summary, warnings)
            count = summary.get("warning_count")
            if isinstance(count, int) and count > 0:
                warnings.append(f"{role} warning_count: {count}")
        warning_stream = root / "artifacts" / "warnings.jsonl"
        if warning_stream.is_file():
            for line in warning_stream.read_text().splitlines():
                record = json.loads(line)
                code = record.get("code", "warning")
                detail = record.get("detail", "")
                warnings.append(f"{role} {code}: {detail}".rstrip())
    return list(dict.fromkeys(warnings))


def _append_warning_fields(value: object, warnings: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if "warning" in key.casefold() and isinstance(item, list):
                warnings.extend(entry for entry in item if isinstance(entry, str))
            elif isinstance(item, (dict, list)):
                _append_warning_fields(item, warnings)
    elif isinstance(value, list):
        for item in value:
            _append_warning_fields(item, warnings)


def _summary_paths() -> tuple[str, ...]:
    return (
        "records/producer_summary.json",
        "records/manifest.json",
        "records/canonicalization_summary.json",
        "records/summary.json",
        "records/cross_reference_summary.json",
    )


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value
