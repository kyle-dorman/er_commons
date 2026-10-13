"""Read only the sealed Dev3 packets and original records needed for comparison."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from importlib.metadata import version
from pathlib import Path
from typing import Any

import ijson  # type: ignore[import-untyped]

from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_dataset_panel import (
    CASE_COUNTS,
    FULL_DEV_CASE_COUNTS,
    PANELS,
    SCHEMA_VERSION,
)
from er_commons.grounding_records import SavedGroundingSample
from er_commons.judge_packet_requests import packet_content
from er_commons.judge_packets import build_packet
from er_commons.judge_qualification_packets import selected_rows
from er_commons.synthetic_intake import verify_binding

PANEL_SHA256 = "409c1f6d3bacd338da321727efaa623fefde56bd4bf76167b96264240a6d17ab"
PANEL_RELATIVE = (
    "pipelines/brisbane_baylands/task_09/09e_20261011_09a3_small_v1/panel/manifest.json"
)
COUNTS = {"C041": 22, "C037": 27, "C014": 20}


def file_binding(path: Path) -> dict[str, Any]:
    """Bind bytes without interpreting potentially restricted file contents."""
    data = path.read_bytes()
    return {
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(data).hexdigest(),
        "byte_size": len(data),
    }


def selected_packets(path: Path, allowed: set[str]) -> dict[str, dict[str, Any]]:
    """Construct only selected objects from the sealed JSON array using routing IDs."""
    result = {}
    buffered: list[tuple[str, Any]] = []
    builder: Any = None
    selected: bool | None = None
    with path.open("rb") as stream:
        for prefix, event, value in ijson.parse(stream):
            if prefix == "item" and event == "start_map":
                buffered, builder, selected = [], None, None
            if not prefix.startswith("item"):
                continue
            if selected is None:
                buffered.append((event, value))
                if prefix == "item.id" and event == "string":
                    selected = value in allowed
                    if selected:
                        builder = ijson.ObjectBuilder()
                        for old_event, old_value in buffered:
                            builder.event(old_event, old_value)
                    buffered = []
            elif selected:
                builder.event(event, value)
            if prefix == "item" and event == "end_map":
                if selected is None:
                    raise ValueError("Packet lacks routing identity")
                if selected:
                    row = builder.value
                    if row["id"] in result:
                        raise ValueError("Duplicate selected packet")
                    result[row["id"]] = row
    if set(result) != allowed:
        raise ValueError("Selected packets missing")
    return result


def load_dev3(manifest_path: Path) -> tuple[list[SavedGroundingSample], dict[str, Any]]:
    """Verify the fixed panel and original answer/source bindings without loading labels."""
    binding = file_binding(manifest_path)
    if binding["sha256"] != PANEL_SHA256:
        raise ValueError("Task 09E.1 requires the exact preserved 09A.3 panel manifest")
    manifest = json.loads(manifest_path.read_text())
    ids = manifest["panels"]["dev3"]
    if len(ids) != 69 or len(set(ids)) != 69:
        raise ValueError("Require all 69 distinct Dev3 records")
    rows = [r for r in manifest["samples"] if r["sample_id"] in ids]
    if dict(Counter(r["case_id"] for r in rows)) != COUNTS:
        raise ValueError("Frozen Dev3 case counts differ")
    return _load_bound_samples(manifest_path, manifest, ids, rows)


def load_development_panel(
    manifest_path: Path, panel: str, expected_sha256: str
) -> tuple[list[SavedGroundingSample], dict[str, Any]]:
    """Verify an explicitly pinned development selection without opening labels.

    Only the existing sealed combined-dataset schema is supported. Its fixed
    development case populations remain enforced; an explicit hash does not
    authorize arbitrary cases or reserved/test partitions.
    """
    if panel not in {*PANELS, "full_dev"}:
        raise ValueError("Unknown development panel")
    if len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256):
        raise ValueError("Require a lowercase SHA-256 manifest identity")
    if file_binding(manifest_path)["sha256"] != expected_sha256:
        raise ValueError("Development manifest SHA-256 differs")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("status") != "frozen":
        raise ValueError("Require frozen combined development dataset panel")
    full_dev = manifest.get("full_dev", False)
    if type(full_dev) is not bool or (panel == "full_dev" and not full_dev):
        raise ValueError("Full development requires explicit frozen membership")
    rows = manifest["samples"]
    all_ids = [row["sample_id"] for row in rows]
    counts = FULL_DEV_CASE_COUNTS if full_dev else CASE_COUNTS
    if len(set(all_ids)) != len(all_ids) or dict(Counter(row["case_id"] for row in rows)) != counts:
        raise ValueError("Frozen development population differs")
    panels = {**PANELS, "full_dev": tuple(FULL_DEV_CASE_COUNTS)} if full_dev else PANELS
    for name, cases in panels.items():
        wanted = [row["sample_id"] for row in rows if row["case_id"] in cases]
        if manifest["panels"].get(name) != wanted:
            raise ValueError("Frozen development panel membership differs")
    ids = manifest["panels"][panel]
    selected = set(ids)
    return _load_bound_samples(
        manifest_path,
        manifest,
        ids,
        [row for row in rows if row["sample_id"] in selected],
        verify_projection=True,
    )


def _load_bound_samples(
    manifest_path: Path,
    manifest: dict[str, Any],
    ids: list[str],
    rows: list[dict[str, Any]],
    *,
    verify_projection: bool = False,
) -> tuple[list[SavedGroundingSample], dict[str, Any]]:
    """Load originals without labels; verify/decode each exact source binding once per load."""
    root = manifest_path.parent
    paths = {
        name: verify_binding(manifest[name], Path(manifest[name]["path"]).parent)
        for name in ("source_result", "namespace_completion", "answers", "origins")
    }
    packets_path = verify_binding(manifest["artifacts"]["packets.json"], root)
    packets = selected_packets(packets_path, set(ids))
    answers = selected_rows(paths["answers"], set(ids))
    origins = selected_rows(paths["origins"], set(ids))
    samples = []
    sources: dict[str, dict[str, Any]] = {}
    source_cache: dict[str, tuple[Path, dict[str, Any] | None]] = {}
    for row in rows:
        key = row["sample_id"]
        packet, answer, origin = packets[key], answers[key], origins[key]
        if (
            stable_json_sha256(packet) != row["packet_sha256"]
            or stable_json_sha256(packet["payload"]) != row["payload_sha256"]
            or stable_json_sha256(answer) != row["answer_record_sha256"]
            or stable_json_sha256(answer["answer"]) != row["answer_sha256"]
            or origin != row["record_origin"]
            or origin["root"] != row["origin_root"]
            or answer["case_id"] != row["case_id"]
        ):
            raise ValueError("Frozen packet, original answer or origin differs")
        source_key = stable_json_sha256({"binding": row["source_input"], "root": origin["root"]})
        if source_key not in source_cache:
            source = verify_binding(row["source_input"], Path(origin["root"]))
            sources[str(source)] = file_binding(source)
            decoded_source = json.loads(source.read_text()) if verify_projection else None
            source_cache[source_key] = (source, decoded_source)
        _, decoded_source = source_cache[source_key]
        if verify_projection:
            assert decoded_source is not None
            rebuilt = build_packet(decoded_source, answer["answer"], "grounding")
            if any(packet[field] != rebuilt[field] for field in ("payload", "mappings")):
                raise ValueError("Frozen packet differs from original answer/source projection")
        packet_content(packet)
        samples.append(
            SavedGroundingSample(
                sample_id=key,
                case_id=row["case_id"],
                scope="development",
                packet=packet,
                expected_score=None,
                category="comparison_unlabeled",
                control=False,
            )
        )
    order = {key: index for index, key in enumerate(ids)}
    samples.sort(key=lambda sample: order[sample.sample_id])
    return samples, {
        "manifest": file_binding(manifest_path),
        "packets": file_binding(packets_path),
        "inputs": {name: file_binding(path) for name, path in paths.items()},
        "sources": list(sources.values()),
        "sample_ids": ids,
        "case_counts": dict(Counter(row["case_id"] for row in rows)),
        "expectations_loaded": False,
    }


def implementation_identity() -> dict[str, Any]:
    """Bind the complete package source and locked runtime without relying on Git cleanliness."""
    package = Path(__file__).parent
    repository = package.parents[1]
    return {
        "code": [file_binding(path) for path in sorted(package.rglob("*.py"))],
        "lockfile": file_binding(repository / "uv.lock"),
        "packages": {name: version(name) for name in ("inspect-ai", "httpx", "pydantic", "ijson")},
    }
