"""Prepare current writer controls and original source releases once per invocation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from er_commons.document_publication.preflight import DocumentRun

from er_commons.artifact_io import assert_contained
from er_commons.artifact_verification import VerificationBudget
from er_commons.authority_reference import AuthorityReference, authority_root_for_path
from er_commons.document_parsing.content_parsing.sources import load_sealed_manifest_metadata
from er_commons.document_publication.config import DocumentRunSpec
from er_commons.document_publication.identity import canonical_digest
from er_commons.document_publication.production_identity import validate_production_identity
from er_commons.document_publication.records import SourceIdentity
from er_commons.document_publication.sources import (
    manifest_selection_for,
    resolve_manifest_source_metadata,
)


def file_stamp(path: Path) -> tuple[int, int, int, int]:
    """Detect changes to prepared inputs without rereading their accepted bytes."""
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino


@dataclass(frozen=True)
class PreparedPublicationInputs:
    """Run-local checked current recipe and original per-source identities."""

    data_root: Path
    repository_root: Path
    spec_path: Path
    spec: DocumentRunSpec
    spec_sha256: str
    sources: Mapping[str, SourceIdentity]
    budget: VerificationBudget
    stamps: Mapping[Path, tuple[int, int, int, int]]

    def verify(self, data_root: Path, spec_path: Path, source_id: str) -> None:
        """Reject changed specs, roots, membership or prepared source evidence."""
        if data_root.resolve() != self.data_root or spec_path.resolve() != self.spec_path:
            raise ValueError("prepared publication roots/specification differ")
        if source_id not in self.sources:
            raise ValueError(f"prepared publication source absent: {source_id}")
        for path, expected in self.stamps.items():
            if file_stamp(path) != expected:
                raise ValueError(f"prepared publication input changed: {path}")


def prepare_publication_inputs(
    data_root: Path,
    spec_path: Path,
    *,
    repository_root: Path,
    budget: VerificationBudget,
) -> PreparedPublicationInputs:
    """Verify the new writer recipe and load each original release exactly once."""
    data_root, repository_root, spec_path = (
        data_root.resolve(),
        repository_root.resolve(),
        spec_path.resolve(),
    )
    digest = budget.hash_file(
        spec_path, root=spec_path.parent, role="run_descriptor", source_id="shared"
    )
    spec = DocumentRunSpec.model_validate(
        budget.read_json(
            spec_path, root=spec_path.parent, role="run_descriptor", source_id="shared"
        )
    )
    identity_path = _production_identity_path(
        spec, repository_root=repository_root, data_root=data_root, budget=budget
    )
    identity_root = authority_root_for_path(
        identity_path, repository_root=repository_root, artifact_root=data_root
    )
    record = budget.read_json(
        identity_path, root=identity_root, role="identity_preimage", source_id="shared"
    )
    if not isinstance(record, dict):
        raise ValueError("production identity must be an object")
    production = validate_production_identity(
        record,
        project_root=repository_root,
        artifact_root=data_root,
        budget=budget,
        expected_source_ids=[item.source_id for item in spec.document_processes],
        expected_scope_kind=spec.scope_kind,
    )
    if production.value != spec.production_extraction_id:
        raise ValueError("publication production identity differs")
    baseline = load_sealed_manifest_metadata(data_root, spec, budget)
    manifests = {(spec.source_release_version, spec.source_manifest_path): baseline}
    sources = {}
    for process in spec.document_processes:
        selection = manifest_selection_for(spec, process.source_id)
        key = (selection.source_release_version, selection.source_manifest_path)
        if key not in manifests:
            manifests[key] = load_sealed_manifest_metadata(data_root, selection, budget)
        sources[process.source_id] = resolve_manifest_source_metadata(
            data_root, spec, process.source_id, budget, manifest=manifests[key]
        )
    scope = _recorded_scope(data_root, spec, sources, budget)
    validate_production_identity(record, expected_scope=scope)
    return PreparedPublicationInputs(
        data_root,
        repository_root,
        spec_path,
        spec,
        digest,
        MappingProxyType(sources),
        budget,
        MappingProxyType(capture_verified_stamps(budget)),
    )


def _production_identity_path(
    spec: DocumentRunSpec,
    *,
    repository_root: Path,
    data_root: Path,
    budget: VerificationBudget,
) -> Path:
    """Resolve historical repository identities or a v4 declared authority."""
    reference: AuthorityReference | None = spec.production_identity_ref
    if reference is not None:
        return reference.resolve(
            repository_root=repository_root,
            artifact_root=data_root,
            budget=budget,
            role="identity_preimage",
        )
    relative = spec.production_identity_relative_path
    if relative is None:
        raise ValueError("document specification lacks a production identity")
    return assert_contained(repository_root, relative.as_posix())


def _recorded_scope(
    data_root: Path,
    spec: DocumentRunSpec,
    sources: Mapping[str, SourceIdentity],
    budget: VerificationBudget,
) -> dict[str, object]:
    """Bind the original baseline seal and ordered selected physical source records."""
    completion_path = data_root / spec.source_manifest_path.parent / "completion_record.json"
    completion = budget.read_json(
        completion_path, root=data_root, role="completion", source_id="shared"
    )
    if not isinstance(completion, dict) or not isinstance(completion.get("manifest"), dict):
        raise ValueError("source release lacks manifest seal")
    manifest_ref = completion["manifest"]
    assert isinstance(manifest_ref, dict)
    completion_digests = [
        item["sha256"]
        for item in budget.observations
        if item["path"] == str(completion_path) and item["verification_mode"] == "bytes_verified"
    ]
    if not completion_digests:
        raise ValueError("source release completion was not verified")
    ordered = [sources[item.source_id].model_dump(mode="json") for item in spec.document_processes]
    return {
        "source_release_version": spec.source_release_version,
        "source_manifest_sha256": manifest_ref["sha256"],
        "release_completion_sha256": completion_digests[-1],
        "ordered_source_records_sha256": canonical_digest(ordered),
    }


def capture_verified_stamps(budget: VerificationBudget) -> dict[Path, tuple[int, int, int, int]]:
    """Reject input changes between first verification and prepared-state capture."""
    stamps = {}
    for item in budget.observations:
        if "file_stamp" not in item:
            continue
        path = Path(item["path"])
        stamp = item["file_stamp"]
        if file_stamp(path) != stamp:
            raise ValueError(f"input changed during preparation: {path}")
        stamps[path] = stamp
    return stamps


def verify_prepared_document_run(
    run: DocumentRun, data_root: Path, spec_path: Path, source_id: str, budget: VerificationBudget
) -> None:
    """Reject caller-supplied prepared state outside its exact invocation contract."""
    if run.verification_budget is not budget:
        raise ValueError("prepared publication must share its invocation verification budget")
    if (
        run.data_root.resolve() != data_root.resolve()
        or run.run_spec_path != spec_path.resolve()
        or run.source.source_id != source_id
    ):
        raise ValueError("prepared publication run source, data root, or spec differs")
    digest = budget.hash_file(
        spec_path, role="run_descriptor", source_id=source_id, root=spec_path.parent
    )
    if digest != run.spec_sha256:
        raise ValueError("prepared publication specification changed")
    if run.verification_budget is not budget:
        raise ValueError("prepared publication requires its shared invocation budget")
    spec = DocumentRunSpec.model_validate(
        budget.read_json(
            spec_path, root=spec_path.parent, role="run_descriptor", source_id=source_id
        )
    )
    if spec != run.spec:
        raise ValueError("prepared publication model differs from sealed specification")
