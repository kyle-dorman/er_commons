"""Load only the accepted 36-point G calibration panel, keeping labels external.

The accepted selection and completion digests anchor the already reviewed ownership
and source fidelity. No corpus, full candidate pool or held-out payload is opened.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
PANEL_POINTER = REPO / "docs/specs/task09f1_calibration_panels_v1_result.json"
LOCKED_SELECTION_SHA256 = "eefb4a409b6c33f0cbe6aa373de9db14817f92727f1896f9f99f276354d4dac7"
LOCKED_COMPLETION_SHA256 = "25e4c454b32f2005d0f5c6e08600dad9d6118fbbbfc6a2a5d3bc8f15b1f6f134"
DEVELOPMENT_CASES = frozenset(
    "C001 C006 C007 C008 C014 C017 C019 C027 C028 C029 C036 C037 C041 C042 "
    "C045 C050 C051 C054 C056".split()
)


def _checked_bytes(path: Path, digest: str, size: int | None = None) -> bytes:
    """Reject absent or altered artifacts as evaluator errors, before generation."""
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"G panel evaluator artifact loading error: {path}") from exc
    if hashlib.sha256(data).hexdigest() != digest or (size is not None and len(data) != size):
        raise ValueError(f"G panel artifact integrity mismatch: {path}")
    return data


def _panel_path(root: Path, relative: str) -> Path:
    """Keep every loaded payload inside this selected panel, including symlinks."""
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("G panel artifact escapes selected panel")
    return path


def _unique_rows(data: bytes) -> dict[str, dict[str, Any]]:
    """Read sidecar rows without permitting duplicate candidate identities."""
    rows = [json.loads(line) for line in data.splitlines() if line.strip()]
    result = {row["candidate_id"]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate G panel candidate identity")
    return result


def load_panel(
    pointer_path: Path = PANEL_POINTER,
) -> tuple[list[dict[str, Any]], dict[str, bool], dict[str, Any]]:
    """Return frozen model packets, separate accepted labels and audit provenance."""
    pointer = json.loads(pointer_path.read_text())
    if pointer["status"] != "accepted_and_locked_for_development_calibration":
        raise ValueError("G panel must be accepted and locked")
    if pointer["release_id"] != "task09f_20261014_v2":
        raise ValueError("Unexpected G panel release")
    panel = pointer["panels"]["g"]
    root = Path(panel["artifact_root"])
    selection = json.loads(
        _checked_bytes(_panel_path(root, "selection.json"), LOCKED_SELECTION_SHA256)
    )
    completion = json.loads(
        _checked_bytes(_panel_path(root, "completion.json"), LOCKED_COMPLETION_SHA256)
    )
    files = completion["files"]

    def read_selected(relative: str) -> bytes:
        """Load a selected artifact against the locked completion manifest."""
        record = files[relative]
        return _checked_bytes(_panel_path(root, relative), record["sha256"], record["byte_size"])

    inputs = _unique_rows(read_selected("inputs.jsonl"))
    label_rows = _unique_rows(read_selected("labels.jsonl"))
    selected = selection["selection"]
    ids = [row["candidate_id"] for row in selected]
    if (
        len(ids) != 36
        or len(set(ids)) != 36
        or set(inputs) != set(ids)
        or set(label_rows) != set(ids)
    ):
        raise ValueError("G panel must contain exactly the locked 36 unique cases")
    if {row["case_id"] for row in selected} != DEVELOPMENT_CASES:
        raise ValueError("G panel development question scope mismatch")
    samples: list[dict[str, Any]] = []
    labels: dict[str, bool] = {}
    for row in selected:
        sample_id = row["candidate_id"]
        relative = f"payloads/{sample_id}.json"
        path = _panel_path(root, relative)
        if (
            Path(row["payload_path"]).resolve() != path
            or Path(inputs[sample_id]["payload_path"]).resolve() != path
        ):
            raise ValueError("G panel payload identity mismatch")
        data = read_selected(relative)
        digest = hashlib.sha256(data).hexdigest()
        if digest != row["payload_sha256"] or digest != inputs[sample_id]["payload_sha256"]:
            raise ValueError("G panel payload digest mismatch")
        packet = json.loads(data)
        if set(packet) != {"question", "point_text", "evidence"}:
            raise ValueError("G packet contains forbidden or missing fields")
        if any(
            not isinstance(packet[k], str) or not packet[k].strip()
            for k in ("question", "point_text")
        ):
            raise ValueError("G packet question and point must be nonblank")
        evidence = packet["evidence"]
        if not isinstance(evidence, list) or not evidence:
            raise ValueError("G packet evidence must be nonempty")
        occurrences = [entry["occurrence_id"] for entry in evidence]
        if len(set(occurrences)) != len(occurrences) or any(
            not isinstance(value, str) or not value.strip() for value in occurrences
        ):
            raise ValueError("G packet evidence ownership must be unique")
        evidence_bytes = json.dumps(
            evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
        if hashlib.sha256(evidence_bytes).hexdigest() != row["evidence_sha256"] or (
            hashlib.sha256(packet["point_text"].encode()).hexdigest() != row["point_text_sha256"]
        ):
            raise ValueError("G point or owned evidence fidelity mismatch")
        expected = label_rows[sample_id]["expected_supported"]
        if type(expected) is not bool:
            raise ValueError("G accepted label must be a strict boolean")
        labels[sample_id] = expected
        samples.append(
            {
                "sample_id": sample_id,
                "case_id": row["case_id"],
                "packet": packet,
                "metadata": {
                    "payload_sha256": digest,
                    "point_text_sha256": row["point_text_sha256"],
                    "evidence_sha256": row["evidence_sha256"],
                    "owned_citation_ids": occurrences,
                    "applicability": "known_applicable",
                },
            }
        )
    if sum(labels.values()) != 19:
        raise ValueError("G locked label balance must be 19 supported and 17 unsupported")
    return (
        samples,
        labels,
        {
            "release_id": pointer["release_id"],
            "scope": "locked_36_point_development_calibration",
            "selection_sha256": LOCKED_SELECTION_SHA256,
            "completion_sha256": LOCKED_COMPLETION_SHA256,
            "label_status": "accepted_by_Kyle_for_calibration_2026-10-16",
            "ownership_fidelity": "verified_against_locked_reviewed_payloads",
        },
    )
