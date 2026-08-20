from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNERS = (
    "run_task03h2_gate_a.py",
    "run_task03h2_gate_b.py",
    "run_task03h2_gate_c.py",
    "run_task03h2_gate_c_downstream.py",
)
QUALIFICATION = PROJECT_ROOT / "src/er_commons/chunked_conversion/qualification"


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _functions(path: Path) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]


def test_gate_runners_are_small_application_shells() -> None:
    for filename in RUNNERS:
        path = PROJECT_ROOT / "scripts" / filename
        assert _line_count(path) <= 65, f"runner owns workflow logic: {path}"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        project_imports = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("er_commons")
        ]
        assert project_imports
        assert all(".qualification." in module for module in project_imports)


def test_qualification_modules_and_functions_stay_reviewable() -> None:
    for path in QUALIFICATION.glob("*.py"):
        assert _line_count(path) <= 320, f"split responsibility-owned module: {path}"
        for function in _functions(path):
            assert function.end_lineno is not None
            length = function.end_lineno - function.lineno + 1
            assert length <= 95, f"split function {path}:{function.lineno} ({length} lines)"


def test_tests_use_package_seams_instead_of_loading_runner_files() -> None:
    offenders = []
    for path in (PROJECT_ROOT / "tests").glob("test*chunked_conversion*.py"):
        if _loads_runner_dynamically(path):
            offenders.append(path.name)
    for path in (PROJECT_ROOT / "tests").glob("test_task03h2*.py"):
        if _loads_runner_dynamically(path):
            offenders.append(path.name)
    assert offenders == []


def _loads_runner_dynamically(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "spec_from_file_location"
        for node in ast.walk(tree)
    )
