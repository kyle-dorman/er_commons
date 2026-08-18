"""Small structural gates for the shared artifact-I/O boundary."""

from __future__ import annotations

import ast
from pathlib import Path

MODULE = Path("src/er_commons/artifact_io.py")


def test_artifact_io_stays_a_compact_neutral_boundary() -> None:
    source = MODULE.read_text()
    assert len(source.splitlines()) <= 320
    assert "collection_processing" not in source
    assert "source_release" not in source


def test_streaming_jsonl_writer_does_not_materialize_its_input() -> None:
    tree = ast.parse(MODULE.read_text())
    writer = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_write_jsonl"
    )
    calls = [node for node in ast.walk(writer) if isinstance(node, ast.Call)]
    assert not any(isinstance(call.func, ast.Name) and call.func.id == "list" for call in calls)
    assert not any(
        isinstance(call.func, ast.Attribute) and call.func.attr in {"write_text", "write_bytes"}
        for call in calls
    )


def test_public_functions_remain_bounded_and_documented() -> None:
    tree = ast.parse(MODULE.read_text())
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            assert length <= 45, f"split {node.name} ({length} lines)"
            if not node.name.startswith("_"):
                assert ast.get_docstring(node), f"document public boundary {node.name}"
