"""Metadata-only provenance checks for a prepared document-relink run."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from er_commons.artifact_verification import VerificationBudget
from er_commons.collection_processing.contract import build_collection_handoff_id
from er_commons.document_publication.records import DocumentCompletion
from er_commons.document_records.document_references.relinking_config import (
    DocumentLinkRunSpec,
    ExternalArtifactRef,
    RelinkDocumentSelection,
)
from er_commons.document_records.document_references.types import JsonObject


def validate_base_collection_selection(
    *,
    spec: DocumentLinkRunSpec,
    base_production_identity: JsonObject,
    handoff: JsonObject,
    contract_bundle: JsonObject,
    base_membership_spec: DocumentLinkRunSpec | Sequence[RelinkDocumentSelection] | None = None,
) -> None:
    """Prove selected candidates belong to the sealed base handoff using metadata only.

    This deliberately does not open, hash, or compare document payloads. The run
    specification already seals each selected completion and inventory; this
    check establishes their membership in the declared collection.
    """
    if _object(contract_bundle, "handoff") != handoff:
        raise ValueError("base collection bundle and handoff completion differ")
    preimage = _object(handoff, "identity_preimage")
    if handoff.get("handoff_id") != build_collection_handoff_id(preimage):
        raise ValueError("base collection handoff identity does not derive from its preimage")
    production_id = _text(base_production_identity.get("extraction_id"), "base production ID")
    if (
        handoff.get("status") != "ready"
        or handoff.get("blocking_reasons") != []
        or preimage.get("production_extraction_id") != production_id
        or contract_bundle.get("production_extraction_id") != production_id
    ):
        raise ValueError("base collection is not one ready production lineage")

    accounting = _object(contract_bundle, "accounting")
    ordered_sources = _objects(accounting.get("ordered_sources"), "accounting ordered sources")
    rows = _objects(accounting.get("rows"), "accounting rows")
    embedded = _objects(contract_bundle.get("document_completions"), "document completions")
    if spec.schema_version.endswith(".v2"):
        if base_membership_spec is None:
            raise ValueError("mixed-lineage relink requires its sealed base membership")
        membership = (
            base_membership_spec.documents
            if isinstance(base_membership_spec, DocumentLinkRunSpec)
            else tuple(base_membership_spec)
        )
    else:
        membership = spec.documents
    expected_count = len(membership)
    if not (len(ordered_sources) == len(rows) == len(embedded) == expected_count):
        raise ValueError("base collection membership count differs from relink selection")

    observed_sources: set[str] = set()
    observed_candidates: set[str] = set()
    for ordinal, (selection, source, row, completion_value) in enumerate(
        zip(membership, ordered_sources, rows, embedded, strict=True), start=1
    ):
        completion = DocumentCompletion.model_validate(completion_value)
        source_id = selection.source_id
        candidate_id = selection.source_document.candidate_id
        if source_id in observed_sources or candidate_id in observed_candidates:
            raise ValueError("base collection repeats a selected source or candidate")
        observed_sources.add(source_id)
        observed_candidates.add(candidate_id)
        if (
            source.get("source_id") != source_id
            or completion.source.model_dump(mode="json") != source
            or completion.source.source_id != source_id
            or completion.candidate_id != candidate_id
            or row.get("source_id") != source_id
            or row.get("source_ordinal") != ordinal
            or row.get("candidate_id") != candidate_id
            or row.get("terminal_state") not in {"complete", "complete_with_warnings"}
        ):
            raise ValueError("base collection ordered source membership differs")
        completion_ref = _object(row, "document_completion_ref")
        inventory_ref = _object(row, "candidate_inventory_ref")
        if (
            completion_ref.get("sha256") != selection.source_document.completion_ref.sha256
            or inventory_ref.get("sha256") != selection.source_document.inventory_ref.sha256
            or completion.candidate_inventory.sha256
            != selection.source_document.inventory_ref.sha256
        ):
            raise ValueError("base collection candidate seals differ from relink selection")

    if spec.schema_version.endswith(".v2"):
        _validate_mixed_lineage_mapping(spec=spec, base=membership)


def task06g_base_membership_from_source_slots(
    source_slots: Mapping[str, Any],
    *,
    artifact_root: Path,
    publication_root: Path,
    production_extraction_id: str,
    budget: VerificationBudget,
) -> tuple[RelinkDocumentSelection, ...]:
    """Reconstruct accepted Task 04D output membership from the sealed 06A ledger."""
    if source_slots.get("schema_version") != "er_commons.task06a.source_slots.v1":
        raise ValueError("base membership is not the accepted Task 06A source-slot ledger")
    slots = _objects(source_slots.get("sources"), "Task 06A source slots")
    if len(slots) != 35:
        raise ValueError("Task 06A base membership must contain exactly 35 source slots")
    relative_publication_root = publication_root.resolve().relative_to(artifact_root.resolve())
    documents: list[RelinkDocumentSelection] = []
    observed: set[str] = set()
    for ordinal, slot in enumerate(slots, start=1):
        source_id = _text(slot.get("source_id"), "Task 06A source ID")
        if slot.get("ordinal") != ordinal or source_id in observed:
            raise ValueError("Task 06A source-slot order or uniqueness differs")
        observed.add(source_id)
        task04d = _object(_object(slot, "documents"), "04D")
        accounting = _object(task04d, "accounting_row")
        identity = _object(task04d, "identity")
        candidate_id = _text(identity.get("candidate_id"), "Task 04D candidate ID")
        if (
            identity.get("production_extraction_id") != production_extraction_id
            or accounting.get("source_id") != source_id
            or accounting.get("source_ordinal") != ordinal
            or accounting.get("candidate_id") != candidate_id
            or accounting.get("terminal_state") not in {"complete", "complete_with_warnings"}
        ):
            raise ValueError("Task 06A slot does not identify accepted Task 04D output")

        source_completion = _task04d_publication_ref(
            accounting,
            "document_completion_ref",
            publication_root=relative_publication_root,
        )
        source_inventory = _task04d_publication_ref(
            accounting,
            "candidate_inventory_ref",
            publication_root=relative_publication_root,
        )
        identity_path = Path(_text(task04d.get("identity_path"), "Task 04D identity path"))
        if identity_path.parent.parent.name != candidate_id:
            raise ValueError("Task 06A Task 04D identity path differs from its candidate")

        stages = _object(identity, "stage_completions")
        structured_stage = _object(stages, "structured_document")
        accepted_stage = _object(_object(slot, "accepted_stages"), "structured_document")
        accepted_completion = _object(accepted_stage, "completion")
        if structured_stage != accepted_completion:
            raise ValueError("Task 06A Task 04D structured completion bindings differ")
        structured_completion_path = Path(
            _text(structured_stage.get("path"), "Task 04D structured completion path")
        )
        structured_candidate_id = structured_completion_path.parent.parent.name
        structured_completion = _verified_compact_ref(
            structured_completion_path,
            _text(structured_stage.get("sha256"), "Task 04D structured completion SHA-256"),
            artifact_root=artifact_root,
            budget=budget,
        )
        structured_inventory = _verified_compact_ref(
            structured_completion_path.with_name("artifact_inventory.json"),
            _text(
                accepted_stage.get("artifact_inventory_sha256"),
                "Task 04D structured inventory SHA-256",
            ),
            artifact_root=artifact_root,
            budget=budget,
        )
        documents.append(
            RelinkDocumentSelection.model_validate(
                {
                    "source_id": source_id,
                    "source_document": {
                        "candidate_id": candidate_id,
                        "completion_ref": source_completion,
                        "inventory_ref": source_inventory,
                    },
                    "structured_document": {
                        "candidate_id": structured_candidate_id,
                        "completion_ref": structured_completion,
                        "inventory_ref": structured_inventory,
                    },
                }
            )
        )
    return tuple(documents)


def _task04d_publication_ref(
    accounting: Mapping[str, Any], field: str, *, publication_root: Path
) -> dict[str, Any]:
    """Promote one publication-relative Task 04D accounting seal to artifact authority."""
    value = _object(accounting, field)
    relative = Path(_text(value.get("path"), f"Task 04D {field} path"))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Task 04D accounting reference escapes publication authority")
    return {
        "authority": "artifact_root",
        "path": (publication_root / relative).as_posix(),
        "sha256": _text(value.get("sha256"), f"Task 04D {field} SHA-256"),
        "byte_size": value.get("byte_size"),
    }


def _verified_compact_ref(
    path: Path,
    sha256: str,
    *,
    artifact_root: Path,
    budget: VerificationBudget,
) -> dict[str, Any]:
    """Complete and verify a compact source-slot reference under artifact authority."""
    absolute = (artifact_root / path).resolve()
    if not absolute.is_relative_to(artifact_root.resolve()) or not absolute.is_file():
        raise ValueError("Task 06A compact membership reference escapes or is absent")
    reference = ExternalArtifactRef(
        authority="artifact_root",
        path=path.as_posix(),
        sha256=sha256,
        byte_size=absolute.stat().st_size,
    )
    reference.resolve(
        repository_root=artifact_root,
        artifact_root=artifact_root,
        budget=budget,
        source_id="task04d_base_membership",
    )
    return reference.model_dump(mode="json")


def _validate_mixed_lineage_mapping(
    *,
    spec: DocumentLinkRunSpec,
    base: DocumentLinkRunSpec | Sequence[RelinkDocumentSelection],
) -> None:
    """Require the one accepted ordered base-to-selected Task 06G mapping."""
    base_documents = base.documents if isinstance(base, DocumentLinkRunSpec) else tuple(base)
    if len(spec.documents) != len(base_documents):
        raise ValueError("mixed-lineage selection count differs from base membership")
    expected_changes = {
        "feir_appendix_f1": (
            "deir_appendix_f1",
            "new_source_addition_no_old_entity_equivalence",
            "qualified_substitute_new_source_no_entity_equivalence",
            0,
            (
                (
                    "pipelines/brisbane_baylands/task_06_recovery_v1/06c/"
                    "gate3_inputs_v1/source/records/source_manifest.json"
                ),
            ),
        ),
        "deir_appendix_a": (
            "deir_appendix_a",
            "repeated_heading_many_to_one",
            "accepted_repeated_heading_repair",
            1,
            (
                "pipelines/brisbane_baylands/task_06_recovery_v1/06d/"
                "qualification_v8/completion.json",
            ),
        ),
        "deir_main": (
            "deir_main",
            "missing_chapter_additions_and_fc1_aliases",
            "accepted_missing_chapter_and_fc1_repair",
            1,
            (
                "pipelines/brisbane_baylands/task_06_recovery_v1/06e/"
                "qualification_v17/completion.json",
                "pipelines/brisbane_baylands/task_06_recovery_v1/06f/"
                "qualification_v10/completion.json",
            ),
        ),
    }
    changed: set[str] = set()
    for selected, original in zip(spec.documents, base_documents, strict=True):
        if (
            selected.logical_source_id != original.source_id
            or selected.base_source_id != original.source_id
            or selected.base_source_document != original.source_document
            or selected.base_structured_document != original.structured_document
        ):
            raise ValueError("mixed-lineage base-to-selected mapping differs")
        expected = expected_changes.get(selected.source_id)
        if expected is None:
            if (
                selected.source_id != original.source_id
                or selected.source_document != original.source_document
                or selected.structured_document != original.structured_document
                or selected.change_class != "preserved_semantic"
                or selected.reuse_basis != "sealed_base_candidate_downstream_replay"
                or selected.correspondence_refs != ()
                or selected.evidence_refs != (original.source_document.completion_ref,)
            ):
                raise ValueError("preserved mixed-lineage row differs from base candidate")
            continue
        logical, change_class, reuse_basis, correspondence_count, evidence_paths = expected
        changed.add(selected.source_id)
        if (
            selected.logical_source_id != logical
            or selected.change_class != change_class
            or selected.reuse_basis != reuse_basis
            or selected.source_document == original.source_document
            or selected.structured_document == original.structured_document
            or tuple(ref.path for ref in selected.evidence_refs or ()) != evidence_paths
            or len(selected.correspondence_refs or ()) != correspondence_count
        ):
            raise ValueError("changed mixed-lineage row lacks its accepted authorization")
        if correspondence_count:
            completion_path = Path(selected.structured_document.completion_ref.path)
            structured_root = completion_path.parent.parent
            suffix = (
                "support/repeated_heading_correspondence.json"
                if selected.source_id == "deir_appendix_a"
                else "support/missing_chapter_correspondence.json"
            )
            if (selected.correspondence_refs or ())[0].path != (
                structured_root / suffix
            ).as_posix():
                raise ValueError("changed mixed-lineage correspondence is not candidate-owned")
    if changed != set(expected_changes):
        raise ValueError("mixed-lineage selection does not contain exactly three changed rows")


def _object(value: Mapping[str, Any], field: str) -> JsonObject:
    observed = value.get(field)
    if not isinstance(observed, dict):
        raise ValueError(f"base collection field must be an object: {field}")
    return observed


def _objects(value: object, label: str) -> list[JsonObject]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"base collection field must be an object list: {label}")
    return cast(list[JsonObject], value)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text")
    return value


__all__ = ["task06g_base_membership_from_source_slots", "validate_base_collection_selection"]
