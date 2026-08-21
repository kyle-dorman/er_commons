"""Completion-last storage for live converted-page range evidence."""

from __future__ import annotations

import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_io import (
    artifact_inventory,
    iter_jsonl,
    read_json_object,
    sha256_file,
    write_json_atomic,
    write_jsonl,
)
from er_commons.chunked_conversion.page_evidence import PageEvidence
from er_commons.chunked_conversion.page_evidence_store import (
    read_page_evidence,
    write_page_evidence,
)
from er_commons.chunked_conversion.range_contract import (
    PlannedRange,
    RangeCompletion,
    RangePlan,
    validate_range_completion,
)
from er_commons.chunked_conversion.runtime.diagnostics import ChunkedConversionError
from er_commons.chunked_conversion.runtime.docling_adapter import RangeConversion
from er_commons.document_parsing.content_parsing.evidence import verify_inventory


@dataclass(frozen=True)
class VerifiedConvertedRange:
    """Deep-verified live range evidence ready for aggregate consumption."""

    planned: PlannedRange
    pages: tuple[PageEvidence, ...]
    outline: tuple[dict[str, Any], ...]
    alignment_pages: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]
    observation: dict[str, Any]
    completion: RangeCompletion
    root: Path


class ConvertedRangeStore:
    """Publish and verify the live page-evidence format used by chunk-conversion workers."""

    def __init__(self, run_root: Path, plan: RangePlan) -> None:
        self.run_root = run_root
        self.plan = plan

    def final_root(self, range_id: str) -> Path:
        """Return the immutable final directory for one range identity."""
        return self.run_root / "ranges" / range_id

    def verify(self, range_id: str) -> VerifiedConvertedRange:
        """Deep-audit identity, inventory, page coverage, and supporting records."""
        planned = self._planned(range_id)
        return self._verify_root(self.final_root(range_id), planned, stage="range_reuse")

    def _verify_root(
        self, root: Path, planned: PlannedRange, *, stage: str
    ) -> VerifiedConvertedRange:
        """Apply identical deep validation to staging and final range layouts."""
        range_id = planned.range_id
        completion_path = root / "records/completion_record.json"
        inventory_path = root / "records/artifact_inventory.json"
        try:
            completion = RangeCompletion.model_validate_json(completion_path.read_bytes())
            validate_range_completion(self.plan, completion, path=root.as_posix())
            if completion.artifact_inventory_sha256 != sha256_file(inventory_path):
                raise ChunkedConversionError(
                    "range_inventory_seal",
                    stage=stage,
                    path=inventory_path.as_posix(),
                    expected=completion.artifact_inventory_sha256,
                    actual=sha256_file(inventory_path),
                )
            verify_inventory(root, read_json_object(inventory_path))
            pages = read_page_evidence(root / "pages", load_rasters=False)
            if tuple(page.page_no for page in pages) != planned.read.pages:
                raise ChunkedConversionError(
                    "range_page_coverage",
                    stage=stage,
                    path=(root / "pages/index.json").as_posix(),
                    expected=planned.read.pages,
                    actual=tuple(page.page_no for page in pages),
                )
            alignment = tuple(iter_jsonl(root / "records/alignment_pages.jsonl"))
            alignment_pages = tuple(_page_no(row, root, stage=stage) for row in alignment)
            if alignment_pages != planned.read.pages:
                raise ChunkedConversionError(
                    "range_alignment_coverage",
                    stage=stage,
                    path=(root / "records/alignment_pages.jsonl").as_posix(),
                    expected=planned.read.pages,
                    actual=alignment_pages,
                )
            outline = _dict_tuple(root / "records/outline.json", "outline", stage=stage)
            warning_rows = _string_tuple(root / "records/warnings.json", "warnings", stage=stage)
            observation = read_json_object(root / "records/range_observation.json")
            if observation.get("range_id") != range_id:
                raise ChunkedConversionError(
                    "range_observation_identity",
                    stage=stage,
                    path=(root / "records/range_observation.json").as_posix(),
                    expected=range_id,
                    actual=observation.get("range_id"),
                )
            return VerifiedConvertedRange(
                planned=planned,
                pages=pages,
                outline=outline,
                alignment_pages=alignment,
                warnings=warning_rows,
                observation=observation,
                completion=completion,
                root=root,
            )
        except ChunkedConversionError:
            raise
        except Exception as error:
            raise ChunkedConversionError(
                "invalid_converted_range",
                stage=stage,
                path=root.as_posix(),
                context={"range_id": range_id, "detail": str(error)},
            ) from error

    def publish(self, planned: PlannedRange, conversion: RangeConversion) -> VerifiedConvertedRange:
        """Publish a newly converted range through retained staging and completion last."""
        final = self.final_root(planned.range_id)
        if final.exists():
            return self.verify(planned.range_id)
        attempts = self.run_root / "attempts"
        attempts.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f"{planned.range_id}.", dir=attempts))
        try:
            compact = tuple(_compact(page) for page in conversion.pages)
            write_page_evidence(staging / "pages", compact)
            write_json_atomic(
                staging / "records/outline.json", {"outline": list(conversion.outline)}
            )
            write_jsonl(staging / "records/alignment_pages.jsonl", conversion.alignment_pages)
            write_json_atomic(
                staging / "records/warnings.json", {"warnings": list(conversion.warnings)}
            )
            write_json_atomic(
                staging / "records/range_observation.json",
                {
                    "range_id": planned.range_id,
                    "core": planned.core.model_dump(mode="json"),
                    "read": planned.read.model_dump(mode="json"),
                    "converted_pages": list(planned.read.pages),
                    "wall_seconds": conversion.wall_seconds,
                    "cpu_seconds": conversion.cpu_seconds,
                    "peak_worker_rss_bytes": conversion.peak_rss_bytes,
                    "warning_count": len(conversion.warnings),
                },
            )
            inventory_path = staging / "records/artifact_inventory.json"
            inventory = artifact_inventory(
                staging,
                excluded={"records/artifact_inventory.json", "records/completion_record.json"},
            )
            write_json_atomic(inventory_path, inventory)
            verify_inventory(staging, inventory)
            completion = _completion(self.plan, planned, sha256_file(inventory_path))
            write_json_atomic(
                staging / "records/completion_record.json", completion.model_dump(mode="json")
            )
            self._verify_root(staging, planned, stage="range_publication")
            final.parent.mkdir(parents=True, exist_ok=True)
            staging.rename(final)
            return self.verify(planned.range_id)
        except BaseException as error:
            retain_failure(staging, error, stage="range_conversion")
            raise

    def _planned(self, range_id: str) -> PlannedRange:
        planned = next((item for item in self.plan.ranges if item.range_id == range_id), None)
        if planned is None:
            raise ChunkedConversionError(
                "foreign_range",
                stage="range_reuse",
                path=range_id,
                expected=[item.range_id for item in self.plan.ranges],
                actual=range_id,
            )
        return planned


def retain_failure(root: Path, error: BaseException, *, stage: str) -> Path:
    """Write one structured retained failure without impersonating completion."""
    records = root / "records"
    records.mkdir(parents=True, exist_ok=True)
    failure_path = records / "failure.json"
    diagnostic = (
        error.as_record()
        if isinstance(error, ChunkedConversionError)
        else {
            "error_type": type(error).__name__,
            "code": "unexpected_error",
            "stage": stage,
            "path": root.as_posix(),
            "message": str(error),
        }
    )
    write_json_atomic(
        failure_path,
        {
            "schema_version": "er_commons.chunked_conversion_failure.v1",
            "status": "failed",
            **diagnostic,
            "traceback": traceback.format_exc(),
            "retained": True,
            "completion_published": False,
        },
    )
    return failure_path


def _completion(plan: RangePlan, planned: PlannedRange, inventory_sha256: str) -> RangeCompletion:
    return RangeCompletion(
        plan_id=plan.plan_id,
        range_id=planned.range_id,
        source=plan.inputs.source,
        core=planned.core,
        read=planned.read,
        overlap_owners=planned.overlap_owners,
        range_conversion_identity=plan.inputs.range_conversion_identity,
        expected_pages=planned.read.pages,
        converted_pages=planned.read.pages,
        successful_pages=planned.read.pages,
        overlap_pages=tuple(page for page in planned.read.pages if not planned.core.contains(page)),
        core_owned_pages=planned.core.pages,
        artifact_inventory_path="records/artifact_inventory.json",
        artifact_inventory_sha256=inventory_sha256,
    )


def _compact(page: PageEvidence) -> PageEvidence:
    from er_commons.chunked_conversion.page_evidence_store import compact_page_evidence

    return compact_page_evidence(page)


def _dict_tuple(path: Path, key: str, *, stage: str) -> tuple[dict[str, Any], ...]:
    value = read_json_object(path).get(key)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ChunkedConversionError("record_shape", stage=stage, path=path.as_posix())
    return tuple(cast(list[dict[str, Any]], value))


def _string_tuple(path: Path, key: str, *, stage: str) -> tuple[str, ...]:
    value = read_json_object(path).get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ChunkedConversionError("record_shape", stage=stage, path=path.as_posix())
    return tuple(cast(list[str], value))


def _page_no(record: dict[str, Any], root: Path, *, stage: str) -> int:
    value = record.get("page_no")
    if not isinstance(value, int) or value < 1:
        raise ChunkedConversionError(
            "alignment_page_number",
            stage=stage,
            path=(root / "records/alignment_pages.jsonl").as_posix(),
            actual=value,
        )
    return value


__all__ = ["ConvertedRangeStore", "VerifiedConvertedRange", "retain_failure"]
