"""Behavior tests for neutral artifact I/O boundaries."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path

import pytest

from er_commons.artifact_io import (
    file_reference,
    iter_jsonl,
    load_json,
    publish_jsonl_no_clobber,
    read_jsonl,
    write_json_atomic_streaming,
    write_jsonl,
)


class SinglePassRecords:
    """Large generator-like input that rejects accidental replay."""

    def __init__(self, count: int) -> None:
        self.count = count
        self.iterations = 0

    def __iter__(self) -> Iterator[dict[str, object]]:
        self.iterations += 1
        if self.iterations != 1:
            raise AssertionError("records were iterated more than once")
        for index in range(self.count):
            yield {"index": index, "label": f"record-{index}"}


def test_write_jsonl_streams_large_single_pass_input_deterministically(tmp_path: Path) -> None:
    records = SinglePassRecords(20_000)
    target = tmp_path / "nested" / "records.jsonl"

    assert write_jsonl(target, records) == 20_000

    assert records.iterations == 1
    assert target.read_text().splitlines()[0] == '{"index": 0, "label": "record-0"}'
    assert target.read_text().splitlines()[-1] == ('{"index": 19999, "label": "record-19999"}')
    assert not list(target.parent.glob("*.part"))


def test_write_jsonl_keeps_previous_file_when_record_production_fails(tmp_path: Path) -> None:
    target = tmp_path / "records.jsonl"
    original = b'{"status": "complete"}\n'
    target.write_bytes(original)

    def failing_records() -> Iterator[dict[str, object]]:
        yield {"status": "partial"}
        raise RuntimeError("synthetic producer failure")

    with pytest.raises(RuntimeError, match="synthetic producer failure"):
        write_jsonl(target, failing_records())

    assert target.read_bytes() == original
    assert not list(tmp_path.glob("*.part"))


def test_publish_jsonl_accepts_identical_bytes_and_rejects_changes(tmp_path: Path) -> None:
    target = tmp_path / "records.jsonl"
    records = [{"name": "cafe", "value": 1}, {"name": "café", "value": 2}]

    assert publish_jsonl_no_clobber(target, iter(records)) == 2
    original = target.read_bytes()
    assert publish_jsonl_no_clobber(target, iter(records)) == 2

    with pytest.raises(FileExistsError, match="refusing to overwrite changed file"):
        publish_jsonl_no_clobber(target, [{"name": "changed", "value": 3}])

    assert target.read_bytes() == original
    assert original == (b'{"name": "cafe", "value": 1}\n{"name": "caf\xc3\xa9", "value": 2}\n')
    assert not list(tmp_path.glob("*.part"))


def test_malformed_json_and_jsonl_errors_identify_artifact_location(tmp_path: Path) -> None:
    json_path = tmp_path / "broken.json"
    json_path.write_text('{"missing": }')
    with pytest.raises(ValueError, match=r"broken\.json:1:13"):
        load_json(json_path)

    jsonl_path = tmp_path / "broken.jsonl"
    jsonl_path.write_text('{"ok": true}\n\n{"missing": }\n')
    with pytest.raises(ValueError, match=r"broken\.jsonl:3"):
        list(iter_jsonl(jsonl_path))

    object_path = tmp_path / "scalar.jsonl"
    object_path.write_text("[]\n")
    with pytest.raises(ValueError, match=r"expected JSON object: .*scalar\.jsonl:1"):
        read_jsonl(object_path)

    invalid_utf8_json = tmp_path / "invalid-utf8.json"
    invalid_utf8_json.write_bytes(b'{"value":"\xff"}')
    with pytest.raises(ValueError, match=r"invalid UTF-8 JSON artifact .*invalid-utf8\.json"):
        load_json(invalid_utf8_json)

    invalid_utf8_jsonl = tmp_path / "invalid-utf8.jsonl"
    invalid_utf8_jsonl.write_bytes(b'{"value":"\xff"}\n')
    with pytest.raises(ValueError, match=r"invalid UTF-8 JSONL artifact .*invalid-utf8\.jsonl"):
        read_jsonl(invalid_utf8_jsonl)


def test_file_reference_hashes_large_files_and_rejects_escape(tmp_path: Path) -> None:
    root = tmp_path / "root"
    target = root / "nested" / "artifact.bin"
    target.parent.mkdir(parents=True)
    content = bytes(range(256)) * 20_000
    target.write_bytes(content)

    assert file_reference(target, root=root) == {
        "path": "nested/artifact.bin",
        "sha256": hashlib.sha256(content).hexdigest(),
        "byte_size": len(content),
    }

    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    with pytest.raises(ValueError, match="escapes root"):
        file_reference(outside, root=root)


def test_streaming_json_write_is_atomic_and_load_does_not_use_read_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "large.json"
    payload = {"records": [{"index": index} for index in range(10_000)]}
    write_json_atomic_streaming(target, payload)

    monkeypatch.setattr(Path, "read_bytes", lambda _path: pytest.fail("read_bytes used"))
    assert load_json(target) == payload

    original = target.read_text()
    with pytest.raises(TypeError):
        write_json_atomic_streaming(target, {"invalid": object()})
    assert target.read_text() == original
    assert not list(tmp_path.glob("*.part"))
