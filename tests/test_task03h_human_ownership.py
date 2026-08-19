"""Structural gates for the Task 03H.1 human-ownership refactor."""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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


def test_task03h_facades_do_not_reabsorb_implementation() -> None:
    """Stable public modules remain navigation surfaces, not hidden mixed owners."""
    maximum_lines = {
        "src/er_commons/document_parsing/content_parsing/application.py": 140,
        "src/er_commons/document_parsing/content_parsing/conversion_bundle.py": 60,
        "src/er_commons/document_records/record_mapping/tables.py": 60,
        "src/er_commons/document_records/document_structure/workflow.py": 90,
        "scripts/generate_task03h_configs.py": 40,
    }
    for relative_path, limit in maximum_lines.items():
        actual = len(_source(relative_path).read_text().splitlines())
        assert actual <= limit, f"split {relative_path}: {actual} lines exceeds {limit}"


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
