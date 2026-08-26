"""Resolve Task 03H review inputs without interpreting canonical content."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from er_commons.artifact_io import sha256_file
from er_commons.document_publication.records import SourceIdentity
from er_commons.human_review_support.task04.json_io import (
    optional_string,
    read_json_object,
    require_integer,
    require_list,
    require_mapping,
    require_string,
)
from er_commons.human_review_support.task04.models import JsonValue, SourceEvidence
from er_commons.human_review_support.task04.scope_policy import InputScopePolicy
from er_commons.human_review_support.task04.verification import (
    CandidateSeal,
    CandidateVerifier,
    DocumentPublicationVerifier,
    Sha256SourceFileVerifier,
    SourceFileVerifier,
)

LOGGER = logging.getLogger(__name__)

SOURCE_RELEASE_RELATIVE = (
    "datasets/ceqa/raw/brisbane_baylands/"
    "brisbane_baylands_2025_deir_sources_v1/sources/model_corpus"
)


@dataclass(frozen=True)
class DiscoveredInputs:
    """Validated source-level inputs needed by later review stages."""

    catalog_path: Path
    readiness_path: Path
    catalog: dict[str, JsonValue]
    readiness: dict[str, JsonValue]
    sources: tuple[SourceEvidence, ...]

    @property
    def ordered_source_ids(self) -> tuple[str, ...]:
        """Return deterministic source ordering used by all queue builders."""
        return tuple(source.source_id for source in self.sources)

    @property
    def candidates(self) -> dict[str, Path]:
        """Index sources with complete selected candidates."""
        return {
            source.source_id: source.selected_candidate
            for source in self.sources
            if source.selected_candidate is not None
        }


def discover_inputs(
    retained_root: Path,
    data_root: Path,
    *,
    candidate_verifier: CandidateVerifier | None = None,
    source_file_verifier: SourceFileVerifier | None = None,
    input_scope: InputScopePolicy | None = None,
) -> DiscoveredInputs:
    """Validate required Task 03H records and resolve every declared source."""
    inputs_root = retained_root / "inputs"
    catalog_paths = sorted(inputs_root.glob("*source_family_catalog*.json"))
    if len(catalog_paths) != 1:
        raise ValueError(
            f"expected exactly one source-family catalog under {inputs_root}; "
            f"found {len(catalog_paths)}"
        )
    catalog_path = catalog_paths[0]
    readiness_path = inputs_root / "task03h_preparation_readiness.json"
    if not readiness_path.is_file():
        raise ValueError(f"required Task 03H readiness record is missing: {readiness_path}")

    catalog = read_json_object(catalog_path)
    readiness = read_json_object(readiness_path)
    scope_policy = input_scope or InputScopePolicy.production()
    _verify_readiness_catalog(readiness, readiness_path, catalog_path, data_root)
    catalog_source_ids = _catalog_ordered_source_ids(catalog)
    _verify_accepted_scope(readiness, readiness_path, catalog_source_ids, scope_policy)
    source_pdf_root = data_root / SOURCE_RELEASE_RELATIVE
    sources = _resolve_sources(
        catalog,
        retained_root,
        data_root,
        source_pdf_root,
        candidate_verifier or DocumentPublicationVerifier(),
        source_file_verifier or Sha256SourceFileVerifier(),
    )
    _reconcile_readiness_scope(readiness, readiness_path, sources)
    LOGGER.info(
        "discovered Task 04 inputs",
        extra={
            "source_count": len(sources),
            "candidate_source_count": sum(
                source.selected_candidate is not None for source in sources
            ),
            "retained_root": str(retained_root),
        },
    )
    return DiscoveredInputs(catalog_path, readiness_path, catalog, readiness, sources)


def _reconcile_readiness_scope(
    readiness: dict[str, JsonValue],
    readiness_path: Path,
    sources: tuple[SourceEvidence, ...],
) -> None:
    """Require readiness aggregates to equal verified SourceEvidence exactly."""
    scope_path = f"{readiness_path}:$.source_scope"
    scope = require_mapping(readiness.get("source_scope"), path=scope_path)
    expected = {
        "source_count": len(sources),
        "page_count": sum(source.pdf_page_count for source in sources),
        "byte_count": sum(source.byte_size for source in sources),
    }
    for field, catalog_value in expected.items():
        field_path = f"{scope_path}.{field}"
        readiness_value = require_integer(scope.get(field), path=field_path, minimum=1)
        if readiness_value != catalog_value:
            raise ValueError(
                f"readiness/catalog mismatch at {field_path}: "
                f"readiness={readiness_value}, discovered_catalog={catalog_value}"
            )


def _verify_accepted_scope(
    readiness: dict[str, JsonValue],
    readiness_path: Path,
    catalog_ordered_source_ids: tuple[str, ...],
    policy: InputScopePolicy,
) -> None:
    """Reject non-production scope before source files or candidates are inspected."""
    status_path = f"{readiness_path}:$.status"
    status = require_string(readiness.get("status"), path=status_path)
    if status != policy.required_readiness_status:
        raise ValueError(
            f"unaccepted Task 03H readiness at {status_path}: "
            f"expected={policy.required_readiness_status!r}, found={status!r}"
        )
    scope_path = f"{readiness_path}:$.source_scope"
    scope = require_mapping(readiness.get("source_scope"), path=scope_path)
    if len(catalog_ordered_source_ids) != policy.expected_source_count:
        raise ValueError(
            f"unaccepted Task 04 source scope at {scope_path}.source_count: "
            f"required={policy.expected_source_count}, "
            f"discovered_catalog={len(catalog_ordered_source_ids)}"
        )
    declared_count = require_integer(
        scope.get("source_count"), path=f"{scope_path}.source_count", minimum=1
    )
    if declared_count != policy.expected_source_count:
        raise ValueError(
            f"unaccepted readiness source count at {scope_path}.source_count: "
            f"required={policy.expected_source_count}, readiness={declared_count}"
        )
    if policy.require_ordered_source_ids:
        ids_path = f"{scope_path}.ordered_source_ids"
        declared_ids = tuple(
            require_string(value, path=f"{ids_path}[{index}]")
            for index, value in enumerate(
                require_list(scope.get("ordered_source_ids"), path=ids_path)
            )
        )
        if declared_ids != catalog_ordered_source_ids:
            raise ValueError(
                f"readiness/catalog mismatch at {ids_path}: "
                f"readiness={list(declared_ids)!r}, "
                f"discovered_catalog={list(catalog_ordered_source_ids)!r}"
            )


def _verify_readiness_catalog(
    readiness: dict[str, JsonValue],
    readiness_path: Path,
    catalog_path: Path,
    data_root: Path,
) -> None:
    """Bind readiness to the exact catalog bytes staged beside it."""
    record_path = f"{readiness_path}:$.catalog"
    catalog = require_mapping(readiness.get("catalog"), path=record_path)
    relative_path = catalog_path.relative_to(data_root).as_posix()
    declared_path = require_string(catalog.get("staged_path"), path=f"{record_path}.staged_path")
    if declared_path != relative_path:
        raise ValueError(
            f"readiness/catalog path mismatch at {record_path}.staged_path: "
            f"readiness={declared_path!r}, staged_catalog={relative_path!r}"
        )
    actual_sha256 = sha256_file(catalog_path)
    declared_sha256 = require_string(catalog.get("sha256"), path=f"{record_path}.sha256")
    if declared_sha256 != actual_sha256:
        raise ValueError(
            f"readiness/catalog checksum mismatch at {record_path}.sha256: "
            f"readiness={declared_sha256}, staged_catalog={actual_sha256}"
        )
    declared_size = require_integer(
        catalog.get("byte_size"), path=f"{record_path}.byte_size", minimum=1
    )
    actual_size = catalog_path.stat().st_size
    if declared_size != actual_size:
        raise ValueError(
            f"readiness/catalog byte-size mismatch at {record_path}.byte_size: "
            f"readiness={declared_size}, staged_catalog={actual_size}"
        )


def _resolve_sources(
    catalog: dict[str, JsonValue],
    retained_root: Path,
    data_root: Path,
    source_pdf_root: Path,
    candidate_verifier: CandidateVerifier,
    source_file_verifier: SourceFileVerifier,
) -> tuple[SourceEvidence, ...]:
    """Resolve typed source rows and complete publication candidates."""
    entries = require_list(catalog.get("sources"), path="source_catalog.sources")
    sources = [
        _resolve_source(
            entry,
            index,
            retained_root,
            data_root,
            source_pdf_root,
            candidate_verifier,
            source_file_verifier,
        )
        for index, entry in enumerate(entries)
    ]
    ordered = tuple(sorted(sources, key=lambda source: source.source_id))
    ids = [source.source_id for source in ordered]
    if len(ids) != len(set(ids)):
        raise ValueError("source catalog contains duplicate source IDs")
    return ordered


def _catalog_ordered_source_ids(catalog: dict[str, JsonValue]) -> tuple[str, ...]:
    """Read source IDs in the catalog's accepted declared order."""
    entries = require_list(catalog.get("sources"), path="source_catalog.sources")
    return tuple(
        require_string(
            require_mapping(
                require_mapping(value, path=f"source_catalog.sources[{index}]").get("source"),
                path=f"source_catalog.sources[{index}].source",
            ).get("source_id"),
            path=f"source_catalog.sources[{index}].source.source_id",
        )
        for index, value in enumerate(entries)
    )


def _resolve_source(
    value: JsonValue,
    index: int,
    retained_root: Path,
    data_root: Path,
    source_pdf_root: Path,
    candidate_verifier: CandidateVerifier,
    source_file_verifier: SourceFileVerifier,
) -> SourceEvidence:
    """Resolve one source entry with path-qualified field diagnostics."""
    prefix = f"source_catalog.sources[{index}]"
    entry = require_mapping(value, path=prefix)
    source = require_mapping(entry.get("source"), path=f"{prefix}.source")
    source_id = require_string(source.get("source_id"), path=f"{prefix}.source.source_id")
    sha256 = require_string(source.get("sha256"), path=f"{prefix}.source.sha256")
    pdf_page_count = require_integer(
        source.get("pdf_page_count"),
        path=f"{prefix}.source.pdf_page_count",
        minimum=1,
    )
    source_identity = SourceIdentity(
        source_id=source_id,
        sha256=sha256,
        pdf_page_count=pdf_page_count,
    )
    source_dir = retained_root / "document_publications" / "documents" / source_id
    complete = _complete_candidates(source_dir, source_identity, candidate_verifier)
    selected_path, selected_seal = complete[0] if complete else (None, None)
    source_pdf = source_pdf_root / f"{source_id}.pdf"
    verified_source_sha256 = (
        source_file_verifier.verify(source_pdf, sha256) if source_pdf.is_file() else None
    )
    return SourceEvidence(
        source_id=source_id,
        document_role=optional_string(entry.get("document_role"), path=f"{prefix}.document_role"),
        parent_source_id=optional_string(
            entry.get("parent_source_id"), path=f"{prefix}.parent_source_id"
        ),
        sha256=sha256,
        byte_size=require_integer(
            source.get("byte_size"), path=f"{prefix}.source.byte_size", minimum=1
        ),
        pdf_page_count=pdf_page_count,
        source_relative_path=source_pdf.relative_to(data_root).as_posix(),
        source_pdf=source_pdf,
        source_pdf_sha256=verified_source_sha256,
        candidate_ids=tuple(path.name for path, _ in complete),
        selected_candidate=selected_path,
        selected_completion_sha256=(
            selected_seal.completion_sha256 if selected_seal is not None else None
        ),
        selected_inventory_sha256=(
            selected_seal.inventory_sha256 if selected_seal is not None else None
        ),
    )


def _complete_candidates(
    source_dir: Path,
    source: SourceIdentity,
    verifier: CandidateVerifier,
) -> tuple[tuple[Path, CandidateSeal], ...]:
    """Return only candidates accepted by the owning publication verifier."""
    if not source_dir.is_dir():
        return ()
    candidates = sorted(
        path for path in source_dir.iterdir() if path.is_dir() and path.name.startswith("docv1-")
    )
    verified: list[tuple[Path, CandidateSeal]] = []
    for candidate in candidates:
        completion = candidate / "records" / "completion_record.json"
        if not completion.is_file():
            continue
        verified.append((candidate, verifier.verify(candidate, source)))
    return tuple(verified)


__all__ = ["DiscoveredInputs", "SOURCE_RELEASE_RELATIVE", "discover_inputs"]
