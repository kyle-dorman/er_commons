"""Application shell for mapping parsed evidence into document records."""

from __future__ import annotations

import logging
import resource
import sys
import time
import uuid
from pathlib import Path

from er_commons.artifact_io import assert_contained
from er_commons.document_records.record_mapping.assets import materialize_assets
from er_commons.document_records.record_mapping.candidate import (
    write_validate_and_seal_candidate,
)
from er_commons.document_records.record_mapping.candidate_identity import build_candidate_identity
from er_commons.document_records.record_mapping.config import (
    RecordMappingConfig,
    load_record_mapping_config,
)
from er_commons.document_records.record_mapping.constants import (
    MAPPING_POLICY_PATH,
    PROJECT_ROOT,
    SCHEMA_PATH,
)
from er_commons.document_records.record_mapping.content_records import build_content_records
from er_commons.document_records.record_mapping.context import build_record_mapping_context
from er_commons.document_records.record_mapping.inputs import (
    RecordMappingInputs,
    prepare_record_mapping_inputs,
)
from er_commons.document_records.record_mapping.publication import (
    CandidateWorkspace,
    publish_workspace,
    reserve_workspace,
    retain_workspace_without_completion,
    verify_completed_candidate,
)
from er_commons.document_records.record_mapping.record_sets import DocumentRecordSet
from er_commons.document_records.record_mapping.support_records import build_support_records
from er_commons.document_records.record_mapping.table_projection import (
    project_canonical_table_bundle,
)
from er_commons.document_records.record_mapping.tables import (
    load_producer_table_bundle,
)

LOGGER = logging.getLogger(__name__)


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def _observation(name: str, started: float, *, units: int = 0) -> dict[str, object]:
    elapsed = time.perf_counter() - started
    record: dict[str, object] = {
        "schema_version": "er_commons.substage_observation.v1",
        "name": name,
        "processed_units": units,
        "elapsed_seconds": elapsed,
        "throughput_units_per_second": units / elapsed if elapsed > 0 else None,
        "peak_rss_bytes": _peak_rss_bytes(),
    }
    LOGGER.info(
        "record mapping substage=%s units=%s elapsed=%.2fs peak_rss_bytes=%s",
        name,
        units,
        elapsed,
        record["peak_rss_bytes"],
    )
    return record


def _owned_paths(config_path: Path, mapping_policy_path: Path) -> tuple[Path, ...]:
    """Return every source/config byte bound into candidate identity."""
    module_root = Path(__file__).parent
    shared_dependencies = (
        PROJECT_ROOT / "src" / "er_commons" / "artifact_io.py",
        PROJECT_ROOT
        / "src"
        / "er_commons"
        / "document_parsing"
        / "content_parsing"
        / "evidence.py",
        PROJECT_ROOT / "src" / "er_commons" / "document_parsing" / "content_parsing" / "records.py",
        PROJECT_ROOT
        / "src"
        / "er_commons"
        / "document_parsing"
        / "content_parsing"
        / "references.py",
        PROJECT_ROOT / "src" / "er_commons" / "document_parsing" / "content_parsing" / "sources.py",
        PROJECT_ROOT / "src" / "er_commons" / "source_release" / "models.py",
    )
    return tuple(sorted((*module_root.rglob("*.py"), *shared_dependencies))) + (
        PROJECT_ROOT / "src" / "er_commons" / "cli.py",
        SCHEMA_PATH,
        mapping_policy_path,
        config_path.resolve(),
    )


def build_candidate_in_workspace(
    *,
    data_root: Path,
    staging_root: Path,
    config: RecordMappingConfig,
    inputs: RecordMappingInputs,
    identity: dict[str, object],
    prior_observations: tuple[dict[str, object], ...] = (),
) -> None:
    """Build and completion-seal one candidate in an isolated workspace."""
    observations = list(prior_observations)
    started = time.perf_counter()
    producer_table_bundle = load_producer_table_bundle(inputs.document_root / "producer")
    table_bundle = project_canonical_table_bundle(inputs.document, producer_table_bundle)
    observations.append(_observation("table_projection", started, units=len(table_bundle.tables)))
    started = time.perf_counter()
    context = build_record_mapping_context(
        config=config,
        inputs=inputs,
        identity=identity,
        table_bundle=table_bundle,
    )
    observations.append(_observation("context_indexing", started, units=len(context.page_ids)))
    started = time.perf_counter()
    assets = materialize_assets(
        data_root=data_root,
        candidate_root=staging_root,
        context=context,
        inputs=inputs,
        table_bundle=table_bundle,
    )
    observations.append(_observation("asset_registration", started, units=len(assets.records)))
    started = time.perf_counter()
    content, report = build_content_records(
        context=context,
        inputs=inputs,
        table_bundle=table_bundle,
        assets=assets,
    )
    observations.append(_observation("content_mapping", started, units=report.producer_text_count))
    started = time.perf_counter()
    support = build_support_records(
        context=context,
        config=config,
        inputs=inputs,
        table_bundle=table_bundle,
        assets=assets,
        content=content,
    )
    records = DocumentRecordSet.assemble(
        content=content,
        support=support,
        assets=assets.records,
    )
    observations.append(
        _observation("support_and_assembly", started, units=sum(records.counts().values()))
    )
    started = time.perf_counter()
    write_validate_and_seal_candidate(
        root=staging_root,
        identity=identity,
        config=config,
        inputs=inputs,
        table_bundle=table_bundle,
        records=records,
        report=report,
        substage_observations=tuple(observations),
        terminal_observation=lambda: _observation(
            "serialization_validation_inventory",
            started,
            units=sum(records.counts().values()),
        ),
    )


def _preserve_failed_attempt(task_root: Path, workspace: CandidateWorkspace) -> None:
    """Move failed work aside while removing any misleading completion marker."""
    retain_workspace_without_completion(workspace, task_root / "attempts")


def map_document_records(
    data_root: Path,
    config_path: Path,
    *,
    config_identity_path: Path | None = None,
) -> Path:
    """Publish or checksum-verify one deterministic canonical candidate."""
    config, _config_sha256 = load_record_mapping_config(config_path)
    started = time.perf_counter()
    prepared_inputs = prepare_record_mapping_inputs(data_root, config)
    identity_inputs = prepared_inputs.identity_inputs()
    identity_observation = _observation("identity_and_seal_verification", started)
    mapping_policy_relative = getattr(config, "mapping_policy_relative_path", None)
    mapping_policy_path = (
        PROJECT_ROOT / mapping_policy_relative
        if mapping_policy_relative is not None
        else MAPPING_POLICY_PATH
    )
    identity = build_candidate_identity(
        project_root=PROJECT_ROOT,
        config=config,
        inputs=identity_inputs,
        schema_path=SCHEMA_PATH,
        mapping_policy_path=mapping_policy_path,
        owned_paths=_owned_paths(config_identity_path or config_path, mapping_policy_path),
    )
    candidate_id = identity["extraction_id"]
    task_root = assert_contained(
        data_root,
        config.artifact_relative_root.as_posix(),
    )
    final_root = task_root / candidate_id
    if final_root.exists():
        return verify_completed_candidate(final_root, candidate_id)

    started = time.perf_counter()
    inputs = prepared_inputs.semantic_inputs()
    input_observation = _observation(
        "semantic_input_load",
        started,
        units=len(getattr(inputs, "page_route_records", ())),
    )
    workspace = reserve_workspace(task_root, candidate_id, uuid.uuid4().hex)
    try:
        build_candidate_in_workspace(
            data_root=data_root,
            staging_root=workspace.staging_root,
            config=config,
            inputs=inputs,
            identity=identity,
            prior_observations=(identity_observation, input_observation),
        )
        verify_completed_candidate(workspace.staging_root, candidate_id)
        return publish_workspace(workspace)
    except (Exception, KeyboardInterrupt):
        _preserve_failed_attempt(task_root, workspace)
        raise
