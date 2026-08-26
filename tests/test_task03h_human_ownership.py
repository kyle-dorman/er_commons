"""Structural gates for the Task 03H.1 human-ownership refactor."""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_ORCHESTRATION_FUNCTION_LIMIT = 80


def _active_orchestration_paths() -> tuple[str, ...]:
    """Return the runtime owners added during the active Task 03H work."""
    content_root = PROJECT_ROOT / "src/er_commons/document_parsing/content_parsing"
    aggregate_root = PROJECT_ROOT / "src/er_commons/chunked_conversion/runtime"
    fixed = {
        aggregate_root / "aggregate.py",
        aggregate_root / "aggregate_memory.py",
        content_root / "chunked_application.py",
        content_root / "ordering_projection.py",
        content_root / "pdfium_backend.py",
        content_root / "range_projection_reuse.py",
        content_root / "table_stage_reference.py",
    }
    discovered = {
        *aggregate_root.glob("aggregate*publication*.py"),
        *content_root.glob("derived_*_reuse.py"),
        *content_root.glob("*projection*.py"),
    }
    return tuple(str(path.relative_to(PROJECT_ROOT)) for path in sorted(fixed | discovered))


def _source(relative_path: str) -> Path:
    return PROJECT_ROOT / relative_path


def _function_lengths(path: Path) -> dict[str, int]:
    tree = ast.parse(path.read_text())
    return {
        node.name: (node.end_lineno or node.lineno) - node.lineno + 1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _imported_modules(path: Path) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
    return modules


def test_task03h_runtime_functions_remain_human_sized() -> None:
    """Critical orchestration and policy functions stay readable in one sitting."""
    paths = (
        "src/er_commons/document_parsing/content_parsing/application.py",
        "src/er_commons/document_parsing/content_parsing/conversion_execution.py",
        "src/er_commons/document_parsing/content_parsing/conversion_seal.py",
        "src/er_commons/document_parsing/content_parsing/derived_publication.py",
        "src/er_commons/hierarchy_inference/candidate_publication.py",
        "src/er_commons/hierarchy_inference/candidate_storage.py",
        "src/er_commons/hierarchy_inference/candidate_verification.py",
        "src/er_commons/hierarchy_inference/numbering_scopes.py",
        "src/er_commons/hierarchy_inference/single_build.py",
        "src/er_commons/hierarchy_inference/toc_reconciliation.py",
        "src/er_commons/document_records/document_structure/lifecycle.py",
        "src/er_commons/document_records/document_structure/parser_evidence.py",
        "src/er_commons/document_records/document_structure/producer_alignment.py",
        "src/er_commons/document_records/document_structure/replacement_evidence.py",
        "scripts/generate_task03h_configs.py",
        "scripts/task03h_generation/process_templates.py",
        "scripts/task03h_generation/specifications.py",
        "scripts/task03h_generation/production_identity.py",
        "scripts/task03h_generation/workflow.py",
        "src/er_commons/document_publication/task03h_preparation.py",
    )
    for relative_path in paths:
        lengths = _function_lengths(_source(relative_path))
        oversized = {name: length for name, length in lengths.items() if length > 90}
        assert not oversized, f"split oversized functions in {relative_path}: {oversized}"


def test_active_task03h_orchestration_functions_remain_human_sized() -> None:
    """New orchestration code must decompose work into named, readable steps."""
    violations: dict[str, dict[str, int]] = {}
    for relative_path in _active_orchestration_paths():
        lengths = _function_lengths(_source(relative_path))
        oversized = {
            name: length
            for name, length in lengths.items()
            if length > ACTIVE_ORCHESTRATION_FUNCTION_LIMIT
        }
        if oversized:
            violations[relative_path] = oversized
    assert not violations, f"split oversized orchestration functions: {violations}"


def test_task03h_facades_do_not_reabsorb_implementation() -> None:
    """Stable public modules remain navigation surfaces, not hidden mixed owners."""
    maximum_lines = {
        "src/er_commons/document_parsing/content_parsing/application.py": 140,
        "src/er_commons/document_parsing/content_parsing/conversion_bundle.py": 60,
        "src/er_commons/document_parsing/heading_evidence_parsing/pdf_observations.py": 70,
        "src/er_commons/document_records/record_mapping/tables.py": 60,
        "src/er_commons/document_records/document_structure/workflow.py": 90,
        "scripts/generate_task03h_configs.py": 40,
    }
    for relative_path, limit in maximum_lines.items():
        actual = len(_source(relative_path).read_text().splitlines())
        assert actual <= limit, f"split {relative_path}: {actual} lines exceeds {limit}"


def test_ordering_projection_owners_remain_bounded() -> None:
    """Projection policy, records, and storage verification stay separate."""
    limits = {
        "src/er_commons/document_parsing/content_parsing/ordering_projection.py": 180,
        "src/er_commons/document_parsing/content_parsing/ordering_projection_records.py": 340,
        "src/er_commons/document_parsing/content_parsing/table_stage_reference.py": 260,
    }
    for relative_path, limit in limits.items():
        actual = len(_source(relative_path).read_text().splitlines())
        assert actual <= limit, f"split {relative_path}: {actual} lines exceeds {limit}"


def test_pdf_outline_owners_have_bounded_responsibilities() -> None:
    """Outline behavior stays divided by domain responsibility after the split."""
    root = PROJECT_ROOT / "src/er_commons/document_parsing/heading_evidence_parsing"
    paths = sorted(root.glob("outline_*.py"))
    assert paths
    violations: dict[str, dict[str, int]] = {}
    for path in paths:
        line_count = len(path.read_text().splitlines())
        assert line_count <= 350, f"split the responsibilities in {path.name}: {line_count} lines"
        oversized = {
            name: length
            for name, length in _function_lengths(path).items()
            if length > ACTIVE_ORCHESTRATION_FUNCTION_LIMIT
        }
        if oversized:
            violations[path.name] = oversized
    assert not violations, f"split oversized PDF outline functions: {violations}"


def test_task03h_generation_has_named_one_way_owners() -> None:
    """Templates, specs, and identity closure remain separate from the CLI facade."""
    facade_imports = _imported_modules(_source("scripts/generate_task03h_configs.py"))
    assert "task03h_generation.workflow" in facade_imports
    template_source = _source("scripts/task03h_generation/process_templates.py").read_text()
    assert "task03g2_main" not in template_source
    assert "generate_task03g2" not in template_source
    identity_imports = _imported_modules(
        _source("scripts/task03h_generation/production_identity.py")
    )
    assert "task03h_generation.process_templates" not in identity_imports


def test_storage_and_seal_dependencies_point_in_one_direction() -> None:
    """Low-level storage and seal verification cannot depend on workflow owners."""
    forbidden = {
        "src/er_commons/hierarchy_inference/candidate_storage.py": {
            "er_commons.hierarchy_inference.application",
            "er_commons.hierarchy_inference.candidate_publication",
            "er_commons.hierarchy_inference.candidate_verification",
        },
        "src/er_commons/document_parsing/content_parsing/conversion_seal.py": {
            "er_commons.document_parsing.content_parsing.application",
            "er_commons.document_parsing.content_parsing.conversion_execution",
        },
    }
    for relative_path, disallowed in forbidden.items():
        imports = _imported_modules(_source(relative_path))
        assert imports.isdisjoint(disallowed), (
            f"reverse ownership import in {relative_path}: {sorted(imports & disallowed)}"
        )


def test_task03h_migration_adapters_are_not_maintained_runtime() -> None:
    """The MVP hard cut leaves no compatibility adapter or legacy replay entrypoint."""
    removed = (
        "src/er_commons/document_performance/task03h_migration.py",
        "scripts/replay_task03h_legacy.py",
        "scripts/replay_task03h_hierarchy.py",
        "tests/test_task03h_migration.py",
    )
    assert not [relative_path for relative_path in removed if _source(relative_path).exists()]
