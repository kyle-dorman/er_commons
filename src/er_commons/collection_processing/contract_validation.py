"""Offline validation for current collection-processing contract fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError  # type: ignore[import-untyped]
from pydantic import ValidationError as PydanticValidationError

from er_commons.collection_processing.config import CollectionRunSpec


def validate_collection_contract_fixtures(schema_path: Path, fixture_root: Path) -> int:
    """Validate every JSON fixture under one current v2 schema and return its count."""
    schema = _object(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    fixtures = sorted(fixture_root.rglob("*.json"))
    if not fixtures:
        raise ValueError(f"collection contract fixture directory is empty: {fixture_root}")
    for path in fixtures:
        fixture = _object(path)
        try:
            validator.validate(fixture)
        except ValidationError as error:
            raise ValueError(
                f"collection fixture fails JSON Schema: {path}: {error.message}"
            ) from error
        try:
            CollectionRunSpec.model_validate(fixture)
        except PydanticValidationError as error:
            raise ValueError(
                f"collection fixture fails semantic validation: {path}: {error}"
            ) from error
    return len(fixtures)


def _object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read collection fixture JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


__all__ = ["validate_collection_contract_fixtures"]
