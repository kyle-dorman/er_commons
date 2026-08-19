"""Compiled JSON Schema validators for hierarchy candidate record families."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, validators  # type: ignore[import-untyped]

from er_commons.hierarchy_inference.progress import CandidatePhase, ProgressSnapshot

JsonRecord = dict[str, Any]
ProgressCallback = Callable[[ProgressSnapshot], None]

SINGLETON_DEFINITIONS = {
    "identity": "identity",
    "input_inventory": "input_inventory",
    "hierarchy": "hierarchy",
    "summary": "summary",
}
SEQUENCE_DEFINITIONS = {
    "features": "feature",
    "toc_entries": "toc_entry",
    "reconciliations": "reconciliation",
    "regimes": "regime",
    "decisions": "decision",
    "ambiguities": "diagnostic",
    "warnings": "diagnostic",
}


@dataclass(frozen=True)
class HierarchyRecordValidators:
    """One loaded schema with reusable aggregate and definition validators."""

    aggregate: Any
    by_definition: Mapping[str, Any]

    @classmethod
    def load(cls, schema_path: Path) -> HierarchyRecordValidators:
        """Load one schema and compile every referenced validator exactly once."""
        resolved = schema_path.resolve()
        stat = resolved.stat()
        return _load_validators(resolved, stat.st_size, stat.st_mtime_ns)

    def validate_definition(self, definition: str, record: object) -> None:
        """Validate one record with its already compiled definition validator."""
        self.by_definition[definition].validate(record)

    def validate_bundle_schema(self, bundle: JsonRecord) -> None:
        """Validate the aggregate persisted bundle, accepting resident tuples."""
        self.aggregate.validate(bundle)

    def validate_semantic_schema(
        self,
        records: JsonRecord,
        progress: ProgressCallback | None,
    ) -> None:
        """Validate large semantic sequences with bounded record progress."""
        total = len(SINGLETON_DEFINITIONS) + sum(
            len(records[name]) for name in SEQUENCE_DEFINITIONS
        )
        processed = 0
        self._report_semantic_progress(progress, processed, total)
        for field_name, definition in SINGLETON_DEFINITIONS.items():
            self.validate_definition(definition, records[field_name])
            processed += 1
            if processed % 10_000 == 0 or processed == total:
                self._report_semantic_progress(progress, processed, total)
        for field_name, definition in SEQUENCE_DEFINITIONS.items():
            validator = self.by_definition[definition]
            for record in records[field_name]:
                validator.validate(record)
                processed += 1
                if processed % 10_000 == 0 or processed == total:
                    self._report_semantic_progress(progress, processed, total)

    @staticmethod
    def _report_semantic_progress(
        progress: ProgressCallback | None,
        processed: int,
        total: int,
    ) -> None:
        """Emit one typed schema-validation observation when requested."""
        if progress is not None:
            progress(
                ProgressSnapshot(
                    CandidatePhase.SEMANTIC_SCHEMA_VALIDATION,
                    processed,
                    total,
                    "records",
                )
            )


@lru_cache(maxsize=8)
def _load_validators(
    schema_path: Path,
    _byte_size: int,
    _modified_ns: int,
) -> HierarchyRecordValidators:
    """Cache compiled validators while invalidating when schema file facts change."""
    schema = json.loads(schema_path.read_text())
    type_checker = Draft202012Validator.TYPE_CHECKER.redefine(
        "array", lambda _checker, value: isinstance(value, (list, tuple))
    )
    tuple_validator = validators.extend(Draft202012Validator, type_checker=type_checker)
    definitions = schema["$defs"]
    return HierarchyRecordValidators(
        aggregate=tuple_validator(schema),
        by_definition={
            name: Draft202012Validator(
                {
                    "$schema": schema["$schema"],
                    "$ref": f"#/$defs/{name}",
                    "$defs": definitions,
                }
            )
            for name in definitions
        },
    )
