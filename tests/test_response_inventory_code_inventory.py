"""Task 06B stage invalidation and historical/current-writer boundaries."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pytest

from er_commons.response_inventory.code_inventory import (
    ResponseStage,
    owned_code_digest,
    owned_code_paths,
)
from er_commons.response_inventory.run_spec import (
    load_response_inventory_run_spec,
    response_stage,
    verify_repository_bindings,
)

ROOT = Path(__file__).parents[1]
STAGES: tuple[ResponseStage, ...] = ("source", "relationship", "reference", "presentation")


def _copy_inventory(destination: Path) -> None:
    """Copy only small declared code dependencies into a disposable checkout."""
    for stage in STAGES:
        for path in owned_code_paths(ROOT, stage=stage):
            target = destination / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


@pytest.mark.parametrize(
    ("changed", "affected"),
    [
        ("response_inventory/reference_baseline.py", {"reference"}),
        ("response_inventory/review_tool.py", {"presentation"}),
        ("response_inventory/review_tool_static/app.js", {"presentation"}),
        ("response_inventory/producer.py", {"source"}),
        ("response_inventory/relationship_baseline.py", {"relationship"}),
        ("document_records/document_structure/normalization.py", {"reference"}),
        ("artifact_io.py", set(STAGES)),
        ("response_inventory/contract.py", {"source", "relationship", "reference"}),
        ("response_inventory/cli.py", set()),
        ("source_acquisition.py", set()),
    ],
)
def test_stage_dependency_perturbations(tmp_path: Path, changed: str, affected: set[str]) -> None:
    """Unrelated edits stay local; shared behavior reaches its actual consumers."""
    _copy_inventory(tmp_path)
    before = {stage: owned_code_digest(tmp_path, stage=stage) for stage in STAGES}
    target = tmp_path / "src/er_commons" / changed
    target.parent.mkdir(parents=True, exist_ok=True)
    previous = target.read_bytes() if target.exists() else b""
    target.write_bytes(previous + b"\n# synthetic behavior perturbation\n")
    assert {
        stage for stage in STAGES if owned_code_digest(tmp_path, stage=stage) != before[stage]
    } == affected


@pytest.mark.parametrize(
    ("filename", "stage"),
    [
        ("brisbane_baylands_2025_feir_task05c_pilot_v1.json", "source"),
        ("brisbane_baylands_2025_feir_task05d_complete_v2.json", "source"),
        ("brisbane_baylands_2025_feir_task05e_exact_v3.json", "relationship"),
        ("brisbane_baylands_2025_feir_task05e_review_v4.json", "relationship"),
        ("brisbane_baylands_2025_feir_task05f_exact_v5.json", "reference"),
    ],
)
def test_historical_specs_load_without_old_checkout_but_new_writers_require_current_code(
    tmp_path: Path, filename: str, stage: ResponseStage
) -> None:
    """Recorded config bytes remain readable and cannot impersonate new execution."""
    historical_path = tmp_path / filename
    shutil.copyfile(ROOT / "configs" / filename, historical_path)
    spec, digest = load_response_inventory_run_spec(historical_path)
    assert digest == hashlib.sha256(historical_path.read_bytes()).hexdigest()
    assert response_stage(spec) == stage
    with pytest.raises(ValueError, match="repository binding is missing"):
        verify_repository_bindings(spec, tmp_path)

    _copy_inventory(tmp_path)
    current_bindings = []
    for binding in spec.repository_bindings:
        target = tmp_path / binding.path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / binding.path, target)
        current_bindings.append(
            binding.model_copy(update={"sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
        )
    current = spec.model_copy(
        update={
            "repository_bindings": tuple(current_bindings),
            "producer_code_sha256": owned_code_digest(tmp_path, stage=stage),
        }
    )
    verify_repository_bindings(current, tmp_path)
    with pytest.raises(ValueError, match="producer code digest mismatch"):
        verify_repository_bindings(
            current.model_copy(update={"producer_code_sha256": spec.producer_code_sha256}),
            tmp_path,
        )
