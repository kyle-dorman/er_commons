"""Shared paths and deterministic JSON/file operations for Task 03H generation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = ROOT / "configs"
TASK_CONFIG_ROOT = CONFIG_ROOT / "task03h"
TASK_TEMPLATE_ROOT = CONFIG_ROOT / "task03h_templates"
MANIFEST_RELATIVE = Path(
    "datasets/ceqa/raw/brisbane_baylands/"
    "brisbane_baylands_2025_deir_sources_v1/records/source_manifest.json"
)
MANIFEST_SHA256 = "fede3e4af815378b77a7f7f54c863ef095328da789859d4f4b25a524f3408f38"
COMPLETION_SHA256 = "d1175d6bf54d2c557293cb7bb0e1191250a9b5db2aef5c9e563ebe01e58767a6"
TASK_ROOT = "pipelines/brisbane_baylands/task_03h"
PARSE_ROOT = f"{TASK_ROOT}/document_parse_evidence"
RECORD_ROOT = f"{TASK_ROOT}/document_records"
HIERARCHY_ROOT = f"{TASK_ROOT}/hierarchy_inference"
PUBLICATION_ROOT = f"{TASK_ROOT}/document_publications"
CATALOG_NAME = "brisbane_baylands_2025_deir_task03h_source_family_catalog_v1.json"
CATALOG_PROJECT_PATH = CONFIG_ROOT / CATALOG_NAME
CATALOG_DATA_RELATIVE = Path(f"{TASK_ROOT}/inputs/{CATALOG_NAME}")
DOCUMENT_SPEC_NAME = "brisbane_baylands_2025_deir_task03h_document_v2.json"
COLLECTION_SPEC_NAME = "brisbane_baylands_2025_deir_task03h_collection_v2.json"
DOCUMENT_SPEC_PATH = CONFIG_ROOT / DOCUMENT_SPEC_NAME
COLLECTION_SPEC_PATH = CONFIG_ROOT / COLLECTION_SPEC_NAME
IDENTITY_RELATIVE = Path(
    "benchmarks/er_bench/fixtures/document_publication/v2/task03h_production_identity.json"
)
IDENTITY_PATH = ROOT / IDENTITY_RELATIVE
TARGET_POLICY = CONFIG_ROOT / "brisbane_baylands_2025_deir_task03g2_target_policy_v1.json"
RESOLUTION_POLICY = CONFIG_ROOT / "brisbane_baylands_2025_deir_task03g2_resolution_policy_v1.json"
ZERO_SHA256 = "0" * 64
ZERO_EXV1 = f"exv1-{ZERO_SHA256}"
ZERO_PRV1 = f"prv1-{ZERO_SHA256}"
ZERO_HCORV1 = f"hcorv1-{ZERO_SHA256}"


def write_or_check(values: dict[Path, dict[str, Any]], *, check: bool) -> None:
    """Write deterministic JSON bytes or report every stale generated path."""
    stale: list[str] = []
    for path, value in values.items():
        encoded = json_bytes(value)
        if check:
            if not path.is_file() or path.read_bytes() != encoded:
                stale.append(path.relative_to(ROOT).as_posix())
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded)
    if stale:
        raise ValueError("generated Task 03H files differ: " + ", ".join(stale))


def json_bytes(value: dict[str, Any]) -> bytes:
    """Serialize one generated object with the established stable formatting."""
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def json_sha256(value: dict[str, Any]) -> str:
    """Hash the exact bytes emitted by :func:`json_bytes`."""
    return hashlib.sha256(json_bytes(value)).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    """Load one required JSON object."""
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    """Hash one exact file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_digest(path: Path, expected: str) -> None:
    """Reject drift in a sealed external input before generation."""
    observed = sha256(path)
    if observed != expected:
        raise ValueError(f"sealed input checksum differs: {path}: {observed}")
