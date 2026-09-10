"""Historical recipe shape validation remains separate from live writer paths."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from er_commons.document_publication.identity import canonical_digest
from er_commons.document_publication.production_identity import validate_production_identity

ROOT = Path(__file__).parents[1]
RECIPE = (
    ROOT / "benchmarks/er_bench/fixtures/document_publication/v4/task03h_production_identity.json"
)


def _record() -> dict[str, Any]:
    """Load a recorded recipe as JSON evidence without accessing any source."""
    return cast(dict[str, Any], json.loads(RECIPE.read_text()))


def _reseal(record: dict[str, Any]) -> None:
    """Give a malformed synthetic preimage a consistent hash to exercise its schema."""
    digest = canonical_digest(record["preimage"])
    record.update(identity_sha256=digest, extraction_id=f"exv1-{digest}")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("path", "../missing.py", "contained relative path"),
        ("path", "/old/missing.py", "contained relative path"),
        ("sha256", "not-a-digest", "SHA-256"),
        ("byte_size", True, "nonnegative integer"),
        ("byte_size", -1, "nonnegative integer"),
        ("unexpected", 1, "reference is not closed"),
    ],
)
def test_self_consistent_historical_hash_does_not_bypass_nested_schema(
    field: str, value: object, message: str
) -> None:
    record = _record()
    record["preimage"]["document_process_contract"]["owned_code"][0][field] = value
    _reseal(record)
    with pytest.raises(ValueError, match=message):
        validate_production_identity(record)


def test_historical_missing_path_is_readable_but_not_current_writer(tmp_path: Path) -> None:
    record = _record()
    reference = record["preimage"]["document_process_contract"]["owned_code"][0]
    reference["path"] = "historical/removed_wrapper.py"
    _reseal(record)
    assert validate_production_identity(record).value == record["extraction_id"]
    with pytest.raises(ValueError, match="artifact differs"):
        validate_production_identity(record, project_root=tmp_path)


def test_historical_contract_cannot_omit_reference_collection() -> None:
    record = _record()
    del record["preimage"]["collection_process_contract"]["owned_code"]
    _reseal(record)
    with pytest.raises(ValueError, match="contract fields differ"):
        validate_production_identity(record)
