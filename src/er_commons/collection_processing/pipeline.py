"""Readable branch-and-join publication sequence for one collection."""

from __future__ import annotations

from pathlib import Path

from er_commons.collection_processing.accounting import AccountingBuilder, AccountingInputs
from er_commons.collection_processing.bundle import ContractBundleWriter
from er_commons.collection_processing.contract import JsonObject
from er_commons.collection_processing.cross_document_linking import (
    CrossDocumentLinkBuilder,
    CrossDocumentLinkInputs,
)
from er_commons.collection_processing.domain import CollectionHooks
from er_commons.collection_processing.handoff_assembly import (
    HandoffAssembler,
    HandoffAssemblyInputs,
)
from er_commons.collection_processing.preflight import CollectionRun
from er_commons.collection_processing.publication import StagePublisher
from er_commons.collection_processing.record_target_indexing import (
    RecordTargetIndexBuilder,
    RecordTargetIndexInputs,
)
from er_commons.document_publication.published_document import DocumentTerminalEvidence


class CollectionPipeline:
    """Publish accounting, index, resolution, handoff, then validate their join."""

    def __init__(self, run: CollectionRun, hooks: CollectionHooks) -> None:
        self._run = run
        self._hooks = hooks
        self._publisher = StagePublisher(run.extraction_root, run.scope_id)

    def publish(self, evidence: tuple[DocumentTerminalEvidence, ...]) -> Path:
        """Build and publish all four identity-owned stages in dependency order."""
        selection_sha256 = self._selection_sha256()
        accounting_build = AccountingBuilder().build(
            AccountingInputs(
                scope_id=self._run.scope_id,
                scope_kind=self._run.document_spec.scope_kind,
                production_extraction_id=self._run.document_spec.production_extraction_id,
                evidence=evidence,
                collection_production_id=self._run.collection_production_id,
                imported_selection_sha256=selection_sha256,
            )
        )
        accounting_stage = self._publisher.publish(accounting_build, self._hooks.accounting)
        index_build = RecordTargetIndexBuilder().build(
            RecordTargetIndexInputs(
                extraction_root=self._run.extraction_root,
                production_extraction_id=self._run.document_spec.production_extraction_id,
                scope_id=self._run.scope_id,
                accounting=accounting_build.completion,
                accounting_stage=accounting_stage,
                evidence=evidence,
                ordering_policy_version=self._run.collection_spec.ordering_policy_version,
                target_policy_sha256=self._run.collection_spec.target_policy_sha256,
                collection_production_id=self._run.collection_production_id,
                imported_selection_sha256=selection_sha256,
                artifact_resolver=self._run.artifact_resolver,
            )
        )
        index_stage = self._publisher.publish(index_build, self._hooks.target_index)
        resolution_build = CrossDocumentLinkBuilder().build(
            CrossDocumentLinkInputs(
                extraction_root=self._run.extraction_root,
                data_root=self._run.data_root,
                catalog_relative_path=self._run.collection_spec.source_family_catalog_relative_path,
                production_extraction_id=self._run.document_spec.production_extraction_id,
                scope_id=self._run.scope_id,
                index=index_build.completion,
                index_stage=index_stage,
                evidence=evidence,
                resolution_policy_sha256=self._run.collection_spec.resolution_policy_sha256,
                collection_production_id=self._run.collection_production_id,
                imported_selection_sha256=selection_sha256,
                artifact_resolver=self._run.artifact_resolver,
            )
        )
        resolution_stage = self._publisher.publish(resolution_build, self._hooks.resolution)
        handoff_build = HandoffAssembler().build(
            HandoffAssemblyInputs(
                production_extraction_id=self._run.document_spec.production_extraction_id,
                scope_id=self._run.scope_id,
                accounting=accounting_build.completion,
                accounting_stage=accounting_stage,
                index=index_build.completion,
                index_stage=index_stage,
                resolution=resolution_build.completion,
                resolution_stage=resolution_stage,
                blocking_policy=self._run.collection_spec.blocking_policy,
                collection_production_id=self._run.collection_production_id,
                imported_selection_sha256=selection_sha256,
            )
        )
        handoff_stage = self._publisher.publish(handoff_build, self._hooks.handoff)
        self._publish_bundle(
            selection_sha256=selection_sha256,
            evidence=evidence,
            accounting=accounting_build.completion,
            index=index_build.completion,
            resolution=resolution_build.completion,
            handoff=handoff_build.completion,
            stage_attempts=[
                *accounting_stage.attempts,
                *index_stage.attempts,
                *resolution_stage.attempts,
                *handoff_stage.attempts,
            ],
        )
        return handoff_stage.completion_path

    def _selection_sha256(self) -> str | None:
        """Return the frozen imported-selection digest for recovery stages."""
        reference = self._run.collection_spec.imported_selection_ref
        return reference.sha256 if reference is not None else None

    def _publish_bundle(
        self,
        *,
        selection_sha256: str | None,
        evidence: tuple[DocumentTerminalEvidence, ...],
        accounting: JsonObject,
        index: JsonObject,
        resolution: JsonObject,
        handoff: JsonObject,
        stage_attempts: list[JsonObject],
    ) -> None:
        """Publish the final contract only after all stage completions exist."""
        self._bundle_writer(selection_sha256).publish(
            evidence=evidence,
            accounting=accounting,
            index=index,
            resolution=resolution,
            handoff=handoff,
            stage_attempts=stage_attempts,
        )

    def _bundle_writer(self, selection_sha256: str | None) -> ContractBundleWriter:
        """Configure the bundle writer with the closed imported-evidence envelope."""
        if self._run.collection_production_id is None:
            return ContractBundleWriter(self._run)
        spec = self._run.collection_spec
        selection = self._run.imported_selection
        if (
            selection is None
            or selection_sha256 is None
            or spec.collection_production_identity_ref is None
            or spec.imported_selection_ref is None
        ):
            raise ValueError("collection recovery bundle lacks frozen controls")
        selection_ref = spec.imported_selection_ref.model_dump(mode="json")
        return ContractBundleWriter(
            self._run,
            collection_production_id=self._run.collection_production_id,
            imported_selection_sha256=selection_sha256,
            collection_production_identity_ref=(
                spec.collection_production_identity_ref.model_dump(mode="json")
            ),
            imported_selection_ref=selection_ref,
            imported_document_evidence={
                "selection_ref": selection_ref,
                "selection_sha256": selection_sha256,
                "document_input_root_relative_path": (selection.document_input_root_relative_path),
                "document_production_identity_ref": (
                    selection.document_production_identity_ref.model_dump(mode="json")
                ),
                "document_run_spec_ref": selection.document_run_spec_ref.model_dump(mode="json"),
                "selections": [item.model_dump(mode="json") for item in selection.candidates],
            },
        )
