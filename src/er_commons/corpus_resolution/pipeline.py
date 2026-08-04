"""Readable branch-and-join publication sequence for one corpus scope."""

from __future__ import annotations

from pathlib import Path

from er_commons.corpus_extraction.outcomes import DocumentTerminalEvidence
from er_commons.corpus_resolution.accounting import AccountingBuilder, AccountingInputs
from er_commons.corpus_resolution.bundle import ContractBundleWriter
from er_commons.corpus_resolution.domain import ScopeHooks
from er_commons.corpus_resolution.handoff import HandoffBuilder, HandoffInputs
from er_commons.corpus_resolution.indexing import TargetIndexBuilder, TargetIndexInputs
from er_commons.corpus_resolution.preflight import ScopeRun
from er_commons.corpus_resolution.publication import StagePublisher
from er_commons.corpus_resolution.resolution import ResolutionBuilder, ResolutionInputs


class CorpusPipeline:
    """Publish accounting, index, resolution, handoff, then validate their join."""

    def __init__(self, run: ScopeRun, hooks: ScopeHooks) -> None:
        self._run = run
        self._hooks = hooks
        self._publisher = StagePublisher(run.extraction_root, run.scope_id)

    def publish(self, evidence: tuple[DocumentTerminalEvidence, ...]) -> Path:
        """Build and publish all four identity-owned stages in dependency order."""
        accounting_build = AccountingBuilder().build(
            AccountingInputs(
                scope_id=self._run.scope_id,
                scope_kind=self._run.document_spec.scope_kind,
                production_extraction_id=self._run.document_spec.production_extraction_id,
                evidence=evidence,
            )
        )
        accounting_stage = self._publisher.publish(accounting_build, self._hooks.accounting)

        index_build = TargetIndexBuilder().build(
            TargetIndexInputs(
                extraction_root=self._run.extraction_root,
                production_extraction_id=self._run.document_spec.production_extraction_id,
                scope_id=self._run.scope_id,
                accounting=accounting_build.completion,
                accounting_stage=accounting_stage,
                evidence=evidence,
                ordering_policy_version=self._run.scope_spec.ordering_policy_version,
                target_policy_sha256=self._run.scope_spec.target_policy_sha256,
            )
        )
        index_stage = self._publisher.publish(index_build, self._hooks.target_index)

        resolution_build = ResolutionBuilder().build(
            ResolutionInputs(
                extraction_root=self._run.extraction_root,
                data_root=self._run.data_root,
                catalog_relative_path=self._run.scope_spec.corpus_catalog_relative_path,
                production_extraction_id=self._run.document_spec.production_extraction_id,
                scope_id=self._run.scope_id,
                index=index_build.completion,
                index_stage=index_stage,
                evidence=evidence,
                resolution_policy_sha256=self._run.scope_spec.resolution_policy_sha256,
            )
        )
        resolution_stage = self._publisher.publish(resolution_build, self._hooks.resolution)

        handoff_build = HandoffBuilder().build(
            HandoffInputs(
                production_extraction_id=self._run.document_spec.production_extraction_id,
                scope_id=self._run.scope_id,
                accounting=accounting_build.completion,
                accounting_stage=accounting_stage,
                index=index_build.completion,
                index_stage=index_stage,
                resolution=resolution_build.completion,
                resolution_stage=resolution_stage,
                blocking_policy=self._run.scope_spec.blocking_policy,
            )
        )
        handoff_stage = self._publisher.publish(handoff_build, self._hooks.handoff)

        ContractBundleWriter(self._run).publish(
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
