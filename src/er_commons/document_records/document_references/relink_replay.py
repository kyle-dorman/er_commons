"""Connect one reusable relink publication to downstream document replay."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from er_commons.collection_processing.config import load_collection_run_spec
from er_commons.collection_processing.workflow import assemble_collection_handoff
from er_commons.document_publication.downstream_replay import publish_downstream_replay
from er_commons.document_records.document_references.relink_publication import (
    PreparedRelinkRun,
    RelinkExecutionResult,
    execute_prepared_document_relink,
    prepare_document_relink_run,
    verify_prepared_link_spec,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RelinkReplayResult:
    """Published linked product and its downstream document descendant."""

    linked: RelinkExecutionResult
    document_completion_path: Path


@dataclass(frozen=True)
class CollectionRelinkReplayResult:
    """All document replays and the resulting collection handoff."""

    documents: tuple[RelinkReplayResult, ...]
    handoff_completion_path: Path


def relink_and_replay_document(
    *,
    data_root: Path,
    link_spec: Path,
    source_id: str,
    repository_root: Path | None = None,
) -> RelinkReplayResult:
    """Publish one linked product, then republish only its document descendants."""
    prepared = prepare_document_relink_run(
        data_root=data_root, link_spec=link_spec, repository_root=repository_root
    )
    return _relink_and_replay_prepared(prepared, source_id=source_id)


def _relink_and_replay_prepared(
    prepared: PreparedRelinkRun, *, source_id: str
) -> RelinkReplayResult:
    """Run one source without reloading the collection-wide specification."""
    verify_prepared_link_spec(prepared)
    selection = prepared.spec.document(source_id)
    source_completion = selection.source_document.completion_ref.resolve(
        repository_root=prepared.repository_root,
        artifact_root=prepared.artifact_root,
    )
    linked = execute_prepared_document_relink(prepared, source_id=source_id)
    document_completion = publish_downstream_replay(
        data_root=prepared.artifact_root,
        document_run_spec=prepared.document_spec_path,
        source_id=source_id,
        source_candidate_root=source_completion.parent.parent,
        cross_reference_completion=linked.completion_path,
    )
    return RelinkReplayResult(
        linked=linked,
        document_completion_path=document_completion,
    )


def relink_replay_and_assemble_collection(
    *,
    data_root: Path,
    link_spec: Path,
    repository_root: Path | None = None,
) -> CollectionRelinkReplayResult:
    """Replay every source sequentially, then assemble its sealed collection once."""
    prepared = prepare_document_relink_run(
        data_root=data_root, link_spec=link_spec, repository_root=repository_root
    )
    spec = prepared.spec
    collection_spec = prepared.collection_spec_path
    collection, _ = load_collection_run_spec(collection_spec)
    selected_document_spec = (collection_spec.parent / collection.document_run_spec).resolve()
    if collection.document_evidence_mode != "downstream_replay_only":
        raise ValueError("relink collection must forbid document attempts")
    if collection.source_ids != spec.selected_source_ids:
        raise ValueError("relink and collection specifications select different sources")
    if selected_document_spec != prepared.document_spec_path:
        raise ValueError("relink and collection specifications select different document specs")
    LOGGER.info("starting sequential relink replay for %d sources", len(spec.selected_source_ids))
    documents_list: list[RelinkReplayResult] = []
    for ordinal, source_id in enumerate(spec.selected_source_ids, start=1):
        LOGGER.info(
            "relink replay source %d/%d: %s", ordinal, len(spec.selected_source_ids), source_id
        )
        try:
            documents_list.append(_relink_and_replay_prepared(prepared, source_id=source_id))
        except Exception:
            LOGGER.exception("relink replay failed for source: %s", source_id)
            raise
        LOGGER.info("relink replay completed for source: %s", source_id)
    verify_prepared_link_spec(prepared)
    LOGGER.info("assembling relink collection handoff")
    handoff = assemble_collection_handoff(prepared.artifact_root, collection_spec)
    LOGGER.info("relink collection handoff completed: %s", handoff)
    return CollectionRelinkReplayResult(
        documents=tuple(documents_list),
        handoff_completion_path=handoff,
    )


__all__ = [
    "CollectionRelinkReplayResult",
    "RelinkReplayResult",
    "relink_and_replay_document",
    "relink_replay_and_assemble_collection",
]
