"""Task 06B finite downstream inventory and CLI independence checks."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from er_commons.document_records.document_structure.code_inventory import owned_code_paths
from er_commons.document_records.record_mapping.candidate_identity import owned_code_digest
from er_commons.document_records.record_mapping.materialize import _owned_paths
from er_commons.hierarchy_inference.code_inventory import (
    owned_code_paths as hierarchy_owned_paths,
)

ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "configs/brisbane_baylands_2025_deir_task03e4_semantic_v1.json"


@pytest.mark.parametrize(
    ("relative", "invalidates"),
    [
        ("src/er_commons/cli.py", False),
        ("src/er_commons/response_inventory/review_tool.py", False),
        ("src/er_commons/document_records/document_structure/new_unused_module.py", False),
        ("src/er_commons/document_records/document_structure/normalization.py", True),
        (
            "src/er_commons/document_records/document_structure/repeated_heading_projection.py",
            False,
        ),
        ("src/er_commons/document_records/record_mapping/table_text_ownership.py", True),
        ("src/er_commons/hierarchy_inference/candidate_verification.py", True),
        ("src/er_commons/artifact_io.py", True),
    ],
)
def test_structure_future_identity_dependencies(
    tmp_path: Path, relative: str, invalidates: bool
) -> None:
    """Actual shared behavior invalidates while dispatch and new unrelated files do not."""
    for source in owned_code_paths(ROOT, CONFIG):
        target = tmp_path / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    config = tmp_path / CONFIG.relative_to(ROOT)
    before = owned_code_digest(tmp_path, owned_code_paths(tmp_path, config))
    changed = tmp_path / relative
    changed.parent.mkdir(parents=True, exist_ok=True)
    previous = changed.read_bytes() if changed.is_file() else b""
    changed.write_bytes(previous + b"\n# synthetic behavior perturbation\n")
    after = owned_code_digest(tmp_path, owned_code_paths(tmp_path, config))
    assert (after != before) is invalidates


def test_mapping_and_hierarchy_exclude_cli_and_retain_shared_helpers() -> None:
    """Dispatch changes never become candidate content dependencies."""
    mapping = _owned_paths(CONFIG, CONFIG)
    hierarchy = hierarchy_owned_paths(ROOT)
    assert ROOT / "src/er_commons/cli.py" not in mapping
    assert ROOT / "src/er_commons/cli.py" not in hierarchy
    assert ROOT / "src/er_commons/artifact_io.py" in mapping
    assert ROOT / "src/er_commons/artifact_io.py" in hierarchy
    assert (
        ROOT / "src/er_commons/document_records/record_mapping/table_text_ownership.py" in mapping
    )
    assert all(path.is_file() for path in mapping)
