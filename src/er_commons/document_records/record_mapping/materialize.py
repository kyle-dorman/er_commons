"""Application shell for mapping parsed evidence into document records."""

from __future__ import annotations

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
    load_record_mapping_inputs,
)
from er_commons.document_records.record_mapping.publication import (
    publish_workspace,
    reserve_workspace,
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


def _owned_paths(config_path: Path, mapping_policy_path: Path) -> tuple[Path, ...]:
    """Return every source/config byte bound into candidate identity."""
    module_root = Path(__file__).parent
    return tuple(sorted(module_root.rglob("*.py"))) + (
        PROJECT_ROOT / "src" / "er_commons" / "cli.py",
        PROJECT_ROOT / "pyproject.toml",
        PROJECT_ROOT / "uv.lock",
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
) -> None:
    """Build and completion-seal one candidate in an isolated workspace."""
    producer_table_bundle = load_producer_table_bundle(inputs.document_root / "producer")
    table_bundle = project_canonical_table_bundle(inputs.document, producer_table_bundle)
    context = build_record_mapping_context(
        config=config,
        inputs=inputs,
        identity=identity,
        table_bundle=table_bundle,
    )
    assets = materialize_assets(
        data_root=data_root,
        candidate_root=staging_root,
        context=context,
        inputs=inputs,
        table_bundle=table_bundle,
    )
    content, report = build_content_records(
        context=context,
        inputs=inputs,
        table_bundle=table_bundle,
        assets=assets,
    )
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
    write_validate_and_seal_candidate(
        root=staging_root,
        identity=identity,
        config=config,
        inputs=inputs,
        table_bundle=table_bundle,
        records=records,
        report=report,
    )


def _preserve_failed_attempt(task_root: Path, staging_root: Path) -> None:
    """Move failed work aside while removing any misleading completion marker."""
    failed_root = task_root / "attempts" / staging_root.name
    failed_root.parent.mkdir(parents=True, exist_ok=True)
    if staging_root.exists():
        staging_root.rename(failed_root)
        (failed_root / "records" / "completion_record.json").unlink(missing_ok=True)


def map_document_records(
    data_root: Path,
    config_path: Path,
    *,
    config_identity_path: Path | None = None,
) -> Path:
    """Publish or checksum-verify the deterministic Appendix P core candidate."""
    config, _config_sha256 = load_record_mapping_config(config_path)
    inputs = load_record_mapping_inputs(data_root, config)
    mapping_policy_relative = getattr(config, "mapping_policy_relative_path", None)
    mapping_policy_path = (
        PROJECT_ROOT / mapping_policy_relative
        if mapping_policy_relative is not None
        else MAPPING_POLICY_PATH
    )
    identity = build_candidate_identity(
        project_root=PROJECT_ROOT,
        config=config,
        inputs=inputs,
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

    workspace = reserve_workspace(task_root, candidate_id, uuid.uuid4().hex)
    try:
        build_candidate_in_workspace(
            data_root=data_root,
            staging_root=workspace.staging_root,
            config=config,
            inputs=inputs,
            identity=identity,
        )
        return publish_workspace(workspace)
    except Exception:
        _preserve_failed_attempt(task_root, workspace.staging_root)
        raise
