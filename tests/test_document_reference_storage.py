"""Memory-bounded deterministic storage checks for document relinking."""

from pathlib import Path

import pytest

from er_commons.document_records.document_references.storage import read_jsonl, write_jsonl


def test_jsonl_storage_streams_with_byte_equivalent_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """JSONL helpers must avoid whole-file text APIs without changing bytes."""
    source = tmp_path / "source.jsonl"
    source.write_bytes(b'{"a":1,"z":"x"}\n\n{"a":2,"z":"y"}\n')

    original_read_text = Path.read_text
    original_write_text = Path.write_text

    def forbid_read_text(*_args: object, **_kwargs: object) -> str:
        raise AssertionError("read_jsonl must stream instead of calling Path.read_text")

    def forbid_write_text(*_args: object, **_kwargs: object) -> int:
        raise AssertionError("write_jsonl must stream instead of calling Path.write_text")

    monkeypatch.setattr(Path, "read_text", forbid_read_text)
    records = read_jsonl(source)
    monkeypatch.setattr(Path, "read_text", original_read_text)

    target = tmp_path / "target.jsonl"
    monkeypatch.setattr(Path, "write_text", forbid_write_text)
    write_jsonl(target, records)
    monkeypatch.setattr(Path, "write_text", original_write_text)

    assert target.read_bytes() == b'{"a":1,"z":"x"}\n{"a":2,"z":"y"}\n'
