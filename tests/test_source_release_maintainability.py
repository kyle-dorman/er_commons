"""Objective readability and import-boundary gates for source release code."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path("src/er_commons/source_release")


def test_application_shell_is_short_and_injects_side_effects() -> None:
    source = (ROOT / "application.py").read_text()
    assert len(source.splitlines()) <= 150
    assert "SourceReleaseServices" in source
    assert "session_factory" in source
    assert "clock" in source


def test_source_release_functions_have_bounded_responsibilities() -> None:
    for path in ROOT.glob("*.py"):
        source = path.read_text()
        assert len(source.splitlines()) <= 360, path
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                assert length <= 100, f"split {path.name}:{node.name} ({length} lines)"


def test_importing_models_does_not_load_network_or_pdf_stacks() -> None:
    code = """
import sys
from er_commons.source_release.models import SourceRole
for name in ('requests', 'bs4', 'pikepdf', 'pypdf'):
    assert name not in sys.modules, name
assert SourceRole.MODEL_CORPUS.value == 'model_corpus'
"""
    subprocess.run([sys.executable, "-c", code], check=True)
