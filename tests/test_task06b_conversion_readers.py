"""Historical metadata readers never execute or freshly hash preserved payloads."""

from pathlib import Path

import pytest

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.artifact_verification import VerificationBudget
from er_commons.document_parsing.content_parsing.conversion_identity import conversion_code_paths
from er_commons.document_parsing.content_parsing.conversion_seal import read_accepted_conversion
from er_commons.document_parsing.content_parsing.evidence import verify_inventory, write_inventory
from er_commons.document_parsing.content_parsing.identity import (
    canonical_json_sha256,
    code_identity,
)


def _seal(root: Path) -> str:
    """Seal a synthetic historical conversion with an absent old code path."""
    (root / "records").mkdir(parents=True)
    producer = root / "documents/example/producer"
    (producer / "docling").mkdir(parents=True)
    (root / "document.json").write_text('{"payload":"old"}')
    for name in ["document.json", "alignment_pages.jsonl", "heading_overlay.jsonl"]:
        (producer / "docling" / name).write_text("{}")
    (producer / "asset_inventory.json").write_text('{"assets":[]}')
    write_json_atomic(
        producer / "docling/conversion_observation.json",
        {
            "source_id": "example",
            "raw_status": "success",
            "status": "complete",
            "errors": [],
            "captured_python_warnings": [],
            "source_manifest_warnings": [],
            "expected_physical_pages": [1, 2],
            "converted_physical_pages": [1, 2],
            "page_coverage_complete": True,
            "asset_count": 0,
            "wall_seconds": 0,
            "cpu_seconds": 0,
            "peak_rss_bytes": 0,
        },
    )
    identity = {
        "identity_schema_version": "er_commons.docling_conversion_identity.v1",
        "source": {"source_id": "example", "sha256": "a" * 64, "pdf_page_count": 2},
        "sealed_release": {"manifest_sha256": "b" * 64},
        "code": {"files": [{"path": "old/absent_adapter.py", "sha256": "c" * 64}]},
    }
    conversion_id = f"dconv1-{canonical_json_sha256(identity)}"
    write_json_atomic(
        root / "records/conversion_identity.json",
        {
            "conversion_id": conversion_id,
            "identity": identity,
        },
    )
    inventory_path = write_inventory(root)
    write_json_atomic(
        root / "records/completion_record.json",
        {
            "schema_version": "er_commons.docling_conversion_completion.v1",
            "conversion_id": conversion_id,
            "status": "complete",
            "source_id": "example",
            "source_sha256": "a" * 64,
            "source_manifest_sha256": "b" * 64,
            "artifact_inventory": "records/artifact_inventory.json",
            "artifact_inventory_sha256": sha256_file(inventory_path),
            "completed_at_utc": "2026-01-01T00:00:00Z",
        },
    )
    return conversion_id


def test_historical_conversion_keeps_identity_without_payload_access(tmp_path, monkeypatch):
    """A descendant can reference the old seal without loading its old implementation."""
    conversion_id = _seal(tmp_path)
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        if path.name == "document.json" or path.suffix == ".pdf":
            raise AssertionError("preserved payload access")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    result = read_accepted_conversion(
        tmp_path, conversion_id, budget=VerificationBudget(), source_id="example"
    )
    assert result["conversion_id"] == conversion_id
    assert result["verification_mode"] == "metadata_checked"
    assert not (tmp_path / "old/absent_adapter.py").exists()
    with pytest.raises(ValueError, match="ID differs"):
        read_accepted_conversion(
            tmp_path, "dconv1-new", budget=VerificationBudget(), source_id="example"
        )


def test_metadata_does_not_claim_same_size_payload_equality(tmp_path):
    """Only deliberate synthetic deep audit catches an unread same-size mutation."""
    conversion_id = _seal(tmp_path)
    payload = tmp_path / "document.json"
    payload.write_text(payload.read_text().replace("old", "new"))
    result = read_accepted_conversion(
        tmp_path, conversion_id, budget=VerificationBudget(), source_id="example"
    )
    assert result["verification_mode"] == "metadata_checked"
    with pytest.raises(ValueError, match="checksum"):
        verify_inventory(tmp_path, result["inventory"])


@pytest.mark.parametrize("mutation", ["extra", "missing", "size", "symlink"])
def test_compact_conversion_rejects_managed_metadata_drift(tmp_path, mutation):
    """Closure, size and containment fail independently of payload hashing."""
    root = tmp_path / "bundle"
    conversion_id = _seal(root)
    payload = root / "document.json"
    if mutation == "extra":
        (root / "extra").write_text("x")
    elif mutation == "missing":
        payload.unlink()
    elif mutation == "size":
        payload.write_text("different-size")
    else:
        outside = tmp_path / "outside"
        outside.write_bytes(payload.read_bytes())
        payload.unlink()
        payload.symlink_to(outside)
    with pytest.raises(ValueError):
        read_accepted_conversion(
            root, conversion_id, budget=VerificationBudget(), source_id="example"
        )


def test_finite_conversion_inventory_ignores_acquisition_and_cli(tmp_path):
    """Actual shared writers invalidate conversion; acquisition and dispatch do not."""
    paths = conversion_code_paths(tmp_path)
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("original")
    baseline = code_identity(paths, repo_root=tmp_path)
    for relative in ["src/er_commons/cli.py", "src/er_commons/source_release/acquisition.py"]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("changed")
    assert code_identity(conversion_code_paths(tmp_path), repo_root=tmp_path) == baseline
    paths[0].write_text("changed shared serializer")
    assert code_identity(conversion_code_paths(tmp_path), repo_root=tmp_path) != baseline


def test_completed_range_consumption_does_not_prepare_current_execution(tmp_path, monkeypatch):
    """Historical range validation uses its frozen behavior, while resume stays strict."""
    from test_chunked_conversion_contract import _inputs

    from er_commons.chunked_conversion.range_contract import build_range_plan
    from er_commons.chunked_conversion.runtime import inputs
    from er_commons.chunked_conversion.runtime.range_store import _completion

    plan = build_range_plan(_inputs())
    (tmp_path / "records").mkdir()
    (tmp_path / "preserved.bin").write_bytes(b"payload")
    for relative in [
        "pages/index.json",
        "records/alignment_pages.jsonl",
        "records/outline.json",
        "records/warnings.json",
        "records/range_observation.json",
        "records/page_projections.json",
    ]:
        path = tmp_path / relative
        path.parent.mkdir(exist_ok=True)
        path.write_text("{}")
    inventory_path = write_inventory(tmp_path)
    completion = _completion(plan, plan.ranges[0], sha256_file(inventory_path))
    write_json_atomic(
        tmp_path / "records/completion_record.json", completion.model_dump(mode="json")
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("completed consumption prepared new execution")

    monkeypatch.setattr(inputs, "prepare_content_parsing", forbidden)
    monkeypatch.setattr(inputs, "behavior_code_identity", forbidden)
    assert (
        inputs.read_accepted_range(tmp_path, plan, completion.range_id, budget=VerificationBudget())
        == completion
    )
    changed = build_range_plan(
        plan.inputs.model_copy(update={"range_conversion_identity": "changed"})
    )
    with pytest.raises(ValueError):
        inputs.read_accepted_range(
            tmp_path, changed, completion.range_id, budget=VerificationBudget()
        )
