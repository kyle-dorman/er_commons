"""Compact native Task08E storage with exact external packet and task bindings."""

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from er_commons import pilot_evidence as evidence
from er_commons.pilot_citation_records import bound_bytes

VERSION = "task08e.packet_reference.v1"
_FIELDS = {"storage_revision", "packet_ref", "expanded_task_sha256"}


def compact_tasks(
    tasks: list[dict[str, Any]],
    *,
    packet_paths_by_case: dict[str, Path],
    data_root: Path,
) -> list[dict[str, Any]]:
    """Replace only duplicated packet data after matching exact externally saved bytes."""
    result = []
    cache: dict[Path, tuple[dict[str, Any], str]] = {}
    for task in tasks:
        data = task["data"]
        if _FIELDS & data.keys() or "packet" not in data:
            raise ValueError("Expanded task required for compact storage")
        case_id = data.get("case_label", data.get("case_id"))
        path = packet_paths_by_case[case_id].resolve()
        relative = str(path.relative_to(data_root.resolve()))
        if path not in cache:
            raw = path.read_bytes()
            cache[path] = (json.loads(raw), hashlib.sha256(raw).hexdigest())
        packet, checksum = cache[path]
        if packet != data["packet"] or evidence.digest(packet) != data["packet_sha256"]:
            raise ValueError("External packet differs from prepared task")
        compact = copy.deepcopy({key: value for key, value in data.items() if key != "packet"})
        compact.update(
            storage_revision=VERSION,
            packet_ref={"path": relative, "sha256": checksum},
            expanded_task_sha256=evidence.digest(data),
        )
        result.append({**task, "data": compact})
    return result


def hydrate_tasks(tasks: list[dict[str, Any]], *, data_root: Path) -> list[dict[str, Any]]:
    """Restore verified packets once per call; caller first verifies native task bindings.

    Nothing is cached between calls. Full legacy tasks retain their prior storage
    format; unknown or partially supplied transport metadata is rejected.
    """
    cache: dict[tuple[str, str], dict[str, Any]] = {}
    result = []
    for task in tasks:
        data = task["data"]
        if not _FIELDS & data.keys():
            result.append(task)
            continue
        if (
            data.get("storage_revision") != VERSION
            or "packet" in data
            or not _FIELDS <= data.keys()
        ):
            raise ValueError("Unsupported or mixed packet transport")
        ref = data["packet_ref"]
        if set(ref) != {"path", "sha256"} or Path(ref["path"]).is_absolute():
            raise ValueError("Exact root-relative packet reference required")
        key = (ref["path"], ref["sha256"])
        if key not in cache:
            cache[key] = json.loads(bound_bytes(ref, data_root))
        packet = cache[key]
        if evidence.digest(packet) != data["packet_sha256"]:
            raise ValueError("External packet semantic identity differs")
        expanded = {key: value for key, value in data.items() if key not in _FIELDS}
        expanded["packet"] = packet
        if evidence.digest(expanded) != data["expanded_task_sha256"]:
            raise ValueError("Expanded task identity differs")
        result.append({**task, "data": expanded})
    return result
