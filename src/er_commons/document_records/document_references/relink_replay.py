"""Connect one reusable relink publication to downstream document replay."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from er_commons.collection_processing.config import load_collection_run_spec
from er_commons.collection_processing.workflow import assemble_collection_handoff
from er_commons.document_publication.downstream_replay import publish_downstream_replay
from er_commons.document_publication.preflight import prepare_accepted_document_run
from er_commons.document_records.document_references.relink_publication import (
    PreparedRelinkRun,
    execute_prepared_document_relink,
    prepare_document_relink_run,
    verify_prepared_link_spec,
)
from er_commons.task06g.comparison_links import TASK04C_LINK_ROOT

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RelinkReplayResult:
    """Compact completion paths for one linked and downstream document replay."""

    linked_completion_path: Path
    document_completion_path: Path


@dataclass(frozen=True)
class CollectionRelinkReplayResult:
    """All document replays and the resulting collection handoff."""

    documents: tuple[RelinkReplayResult, ...]
    handoff_completion_path: Path


def verify_relinked_figure_source_policy(
    linked_completion_path: Path, *, source_id: str, figure_aliases_enabled: bool
) -> int:
    """Reject sealed linked outputs that violate the effective per-source figure policy."""
    candidate_root = linked_completion_path.resolve().parents[1]
    rows_path = candidate_root / "canonical/cross_references.jsonl"
    if not rows_path.is_file():
        raise ValueError(f"linked cross-reference rows are absent: {source_id}")
    figure_count = 0
    with rows_path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"linked cross-reference row is not an object: {source_id}")
            if row.get("mention_class") != "figure":
                continue
            figure_count += 1
            if figure_aliases_enabled:
                continue
            if (
                row.get("resolution_status") != "unresolved"
                or row.get("unresolved_reason") != "accepted_target_type_unavailable"
                or row.get("candidates") != []
                or row.get("cross_document_evidence") is not None
            ):
                raise ValueError(
                    f"disabled source emitted a figure-resolution outcome: {source_id}"
                )
    if not figure_aliases_enabled:
        preservation_path = candidate_root / "support/document_link_preservation.json"
        preservation = json.loads(preservation_path.read_bytes())
        if (
            not isinstance(preservation, dict)
            or preservation.get("schema_version") != "er_commons.document_link_preservation.v1"
            or "derived_figure_alias_count" in preservation
            or (candidate_root / "support/figure_caption_alias_qualification.json").exists()
        ):
            raise ValueError(f"disabled source emitted FC1 support: {source_id}")
    return figure_count


def verify_inherited_navigation_links(data_root: Path, linked_completions: dict[str, Path]) -> int:
    """Require every accepted Task 04C link to survive source-local namespace rebinding."""

    def local_record_id(value: object, *, source_id: str, label: str) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{label} must be a record ID")
        parts = value.split("/")
        if len(parts) < 4 or parts[2] != source_id:
            raise ValueError(f"{label} is not source-local for {source_id}")
        return "/".join(parts[1:])

    overlay_path = data_root / TASK04C_LINK_ROOT / "link_overlay.jsonl"
    overlay_rows = [json.loads(line) for line in overlay_path.read_text().splitlines() if line]
    if len(overlay_rows) != 28 or not all(isinstance(row, dict) for row in overlay_rows):
        raise ValueError("accepted Task 04C navigation overlay must contain 28 rows")
    overlay_keys: set[tuple[str, str]] = set()
    decisions_by_source: dict[str, dict[str, dict[str, object]]] = {}
    for source_id, completion in linked_completions.items():
        path = completion.resolve().parents[1] / "navigation/decisions.jsonl"
        if not path.is_file():
            continue
        decisions: dict[str, dict[str, object]] = {}
        for line in path.read_text().splitlines():
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(row.get("navigation_entry_id"), str):
                raise ValueError(f"linked navigation decision is malformed: {source_id}")
            entry_id = str(row["navigation_entry_id"])
            if entry_id in decisions:
                raise ValueError(f"linked navigation decision is duplicated: {entry_id}")
            decisions[entry_id] = row
        decisions_by_source[source_id] = decisions
    for overlay in overlay_rows:
        source_id = overlay.get("source_id")
        entry_id = overlay.get("source_toc_entry_id")
        if not isinstance(source_id, str) or not isinstance(entry_id, str):
            raise ValueError("accepted Task 04C navigation overlay key is malformed")
        overlay_key = (source_id, entry_id)
        if overlay_key in overlay_keys:
            raise ValueError(f"accepted Task 04C navigation overlay is duplicated: {entry_id}")
        overlay_keys.add(overlay_key)
        expected_target = local_record_id(
            overlay.get("target_id"), source_id=source_id, label="accepted navigation target"
        )
        decision = decisions_by_source.get(source_id, {}).get(entry_id)
        candidates = decision.get("candidate_target_ids") if decision is not None else None
        local_candidates = (
            [
                local_record_id(item, source_id=source_id, label="relinked navigation target")
                for item in candidates
            ]
            if isinstance(candidates, list)
            else []
        )
        if (
            decision is None
            or decision.get("outcome") != "resolved_unique"
            or local_candidates != [expected_target]
        ):
            raise ValueError(f"accepted Task 04C navigation link was not preserved: {entry_id}")
    return len(overlay_rows)


def relink_and_replay_document(
    *,
    data_root: Path,
    link_spec: Path,
    source_id: str,
    repository_root: Path | None = None,
) -> RelinkReplayResult:
    """Publish one linked product, then republish only its document descendants."""
    prepared = prepare_document_relink_run(
        data_root=data_root,
        link_spec=link_spec,
        repository_root=repository_root,
        prepare_publication=True,
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
        budget=prepared.budget,
        role="completion",
        source_id=source_id,
    )
    linked = execute_prepared_document_relink(prepared, source_id=source_id)
    linked_completion = linked.completion_path
    # RelinkExecutionResult also owns the full in-memory RelinkBuild. Release it
    # before downstream publication and before this result enters the collection
    # accumulator; only the sealed completion path crosses this stage boundary.
    del linked
    document_completion = publish_downstream_replay(
        data_root=prepared.artifact_root,
        document_run_spec=prepared.document_spec_path,
        source_id=source_id,
        source_candidate_root=source_completion.parent.parent,
        cross_reference_completion=linked_completion,
        budget=prepared.budget,
        prepared_run=prepare_accepted_document_run(
            prepared.artifact_root,
            prepared.document_spec_path,
            source_id,
            budget=prepared.budget,
            repository_root=prepared.repository_root,
            prepared_inputs=prepared.publication_inputs,
        ),
    )
    return RelinkReplayResult(
        linked_completion_path=linked_completion,
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
        data_root=data_root,
        link_spec=link_spec,
        repository_root=repository_root,
        prepare_publication=True,
    )
    spec = prepared.spec
    collection_spec = prepared.collection_spec_path
    collection, _ = load_collection_run_spec(collection_spec)
    document_run_spec = collection.document_run_spec
    if document_run_spec is None:
        raise ValueError("relink collection requires a document run specification")
    selected_document_spec = (collection_spec.parent / document_run_spec).resolve()
    if collection.document_evidence_mode != "downstream_replay_only":
        raise ValueError("relink collection must forbid document attempts")
    if collection.source_ids != spec.selected_source_ids:
        raise ValueError("relink and collection specifications select different sources")
    if selected_document_spec != prepared.document_spec_path:
        raise ValueError("relink and collection specifications select different document specs")
    LOGGER.info("starting sequential relink replay for %d sources", len(spec.selected_source_ids))
    documents_list: list[RelinkReplayResult] = []
    linked_completions: dict[str, Path] = {}
    disabled_figure_count = 0
    figure_alias_sources = set(spec.figure_alias_source_ids or ())
    for ordinal, source_id in enumerate(spec.selected_source_ids, start=1):
        LOGGER.info(
            "relink replay source %d/%d: %s", ordinal, len(spec.selected_source_ids), source_id
        )
        try:
            result = _relink_and_replay_prepared(prepared, source_id=source_id)
            disabled_figure_count += verify_relinked_figure_source_policy(
                result.linked_completion_path,
                source_id=source_id,
                figure_aliases_enabled=source_id in figure_alias_sources,
            )
            documents_list.append(result)
            linked_completions[source_id] = result.linked_completion_path
        except Exception:
            LOGGER.exception("relink replay failed for source: %s", source_id)
            raise
        LOGGER.info("relink replay completed for source: %s", source_id)
    LOGGER.info(
        "verified per-source figure policy across %d disabled-source mentions",
        disabled_figure_count,
    )
    inherited_navigation_count = verify_inherited_navigation_links(
        prepared.artifact_root, linked_completions
    )
    LOGGER.info("verified %d inherited Task 04C navigation links", inherited_navigation_count)
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
    "verify_relinked_figure_source_policy",
    "verify_inherited_navigation_links",
]
