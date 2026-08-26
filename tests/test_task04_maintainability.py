from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[1] / "src/er_commons/human_review_support/task04"
SCRIPT_ROOT = Path(__file__).parents[1] / "scripts"


def test_task04_modules_and_functions_remain_bounded() -> None:
    violations: list[str] = []
    for path in sorted(PACKAGE_ROOT.glob("*.py")):
        lines = path.read_text().splitlines()
        if len(lines) > 500:
            violations.append(f"{path.name}: module has {len(lines)} lines (limit 500)")
        tree = ast.parse("\n".join(lines), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                if length > 80:
                    violations.append(
                        f"{path.name}:{node.lineno} {node.name} has {length} lines (limit 80)"
                    )
    assert not violations, "\n".join(violations)


def test_task04_cli_scripts_are_thin() -> None:
    for name in ("build_task04_review_bundle.py", "record_task04_finding.py"):
        lines = (SCRIPT_ROOT / name).read_text().splitlines()
        assert len(lines) <= 60, f"{name} has {len(lines)} lines; move logic into the package"


def test_task04_package_respects_ownership_boundaries() -> None:
    violations: list[str] = []
    for path in sorted(PACKAGE_ROOT.glob("*.py")):
        imports = _imports(ast.parse(path.read_text(), filename=str(path)))
        forbidden = [
            name for name in imports if name.startswith(("scripts", "er_commons.document_records"))
        ]
        if forbidden:
            violations.append(f"{path.name}: forbidden imports {forbidden}")
        publication = [
            name for name in imports if name.startswith("er_commons.document_publication")
        ]
        if publication and path.name not in {"discovery.py", "records.py", "verification.py"}:
            violations.append(
                f"{path.name}: publication coupling must stay in discovery/identity/verification"
            )
    assert not violations, "\n".join(violations)


def test_task04_tests_do_not_execute_cli_scripts_as_modules() -> None:
    task04_tests = Path(__file__).parent.glob("*task04*.py")
    offenders = [
        path.name
        for path in task04_tests
        if "runpy" in _imports(ast.parse(path.read_text(), filename=str(path)))
    ]
    assert not offenders, f"Task 04 tests must import public seams, not run scripts: {offenders}"


def test_task04_runbook_uses_canonical_artifact_path_and_derived_anchors() -> None:
    repo_root = Path(__file__).parents[1]
    runbook = (repo_root / "docs/task04_maintainer_runbook.md").read_text()
    finding_guide = (PACKAGE_ROOT / "FINDINGS.md").read_text()
    finding_cli = (SCRIPT_ROOT / "record_task04_finding.py").read_text()

    canonical = "pipelines/brisbane_baylands/task_04_review"
    assert canonical in runbook
    assert canonical in finding_guide
    assert "brisbane_baylands_2025_deir/task04" not in finding_guide
    assert "--evidence-anchor" not in finding_cli
    assert "derives typed anchors" in runbook.lower()


def _imports(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.append(node.module)
    return names
