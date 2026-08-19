"""Own conversion cache lookup, cache-miss execution, and atomic publication."""

from __future__ import annotations

import platform
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal, cast

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.document_parsing.content_parsing.conversion import run_complete_conversion
from er_commons.document_parsing.content_parsing.conversion_identity import (
    COMMON_HEADING_HIERARCHY,
    effective_runtime_identity,
)
from er_commons.document_parsing.content_parsing.conversion_preflight import PreparedConversion
from er_commons.document_parsing.content_parsing.conversion_seal import (
    ConversionCompletion,
    SealedConversion,
    deep_audit_conversion_bundle,
    verify_conversion_bundle,
)
from er_commons.document_parsing.content_parsing.evidence import write_inventory
from er_commons.document_parsing.content_parsing.publication import (
    preserve_failed_attempt,
    publish_workspace,
    reserve_workspace,
)
from er_commons.document_parsing.content_parsing.runtime import verify_model_files
from er_commons.document_parsing.content_parsing.services import ContentParsingServices

_RETAINED_ATTEMPT_ATTRIBUTE = "_er_commons_retained_conversion_attempt"


def retained_conversion_attempt(error: BaseException) -> Path | None:
    """Return the conversion attempt that already accounts for this failure."""
    value = getattr(error, _RETAINED_ATTEMPT_ATTRIBUTE, None)
    return Path(value) if isinstance(value, str) else None


def _build_converter(
    prepared: PreparedConversion,
    services: ContentParsingServices,
) -> tuple[object, dict[str, object]]:
    """Verify model bytes, then construct Docling only for a cache miss."""
    if sha256_file(prepared.model_inventory_path) != prepared.model_inventory_sha256:
        raise ValueError("model inventory changed after conversion preflight")
    verify_model_files(
        prepared.models_root.parent,
        prepared.model_inventory_path,
        prepared.model_inventory,
    )
    converter, options, format_option = services.build_converter(
        prepared.models_root,
        thread_count=prepared.config.thread_count,
        heading_hierarchy_options=COMMON_HEADING_HIERARCHY,
    )
    if options.document_timeout != prepared.config.document_timeout_seconds:
        raise ValueError("effective Docling timeout differs from conversion config")
    expected = prepared.conversion_identity.payload["conversion_policy"]
    effective = options.heading_hierarchy_options.model_dump(mode="json")
    if effective != expected["heading_hierarchy_options"]:
        raise ValueError("effective Docling hierarchy options differ from conversion identity")
    runtime = effective_runtime_identity(prepared.config, options, format_option)
    if runtime != prepared.runtime:
        raise ValueError("effective Docling runtime differs from prepared producer identity")
    return converter, runtime


@contextmanager
def _conversion_lock(conversion_root: Path, conversion_id: str) -> Iterator[None]:
    """Serialize same-identity conversion work and release the lock after crashes."""
    import fcntl

    lock_root = conversion_root / ".locks"
    lock_root.mkdir(parents=True, exist_ok=True)
    with (lock_root / f"{conversion_id}.lock").open("a+b") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def ensure_conversion_bundle(
    *,
    task_root: Path,
    prepared: PreparedConversion,
    services: ContentParsingServices,
) -> SealedConversion:
    """Checksum-reuse or atomically publish one conversion-only candidate."""
    conversion_root = task_root / "docling_conversions"
    conversion_root.mkdir(parents=True, exist_ok=True)
    conversion_id = prepared.conversion_identity.run_id
    final_root = conversion_root / conversion_id
    if final_root.exists():
        return verify_conversion_bundle(final_root, conversion_id)

    with _conversion_lock(conversion_root, conversion_id):
        if final_root.exists():
            return verify_conversion_bundle(final_root, conversion_id)
        return _publish_conversion_bundle(
            conversion_root=conversion_root,
            final_root=final_root,
            prepared=prepared,
            services=services,
        )


def _publish_conversion_bundle(
    *,
    conversion_root: Path,
    final_root: Path,
    prepared: PreparedConversion,
    services: ContentParsingServices,
) -> SealedConversion:
    """Run one cache-miss conversion and publish its completion marker last."""
    workspace = None
    started_at = services.now()
    started = services.monotonic()
    try:
        workspace = reserve_workspace(
            conversion_root,
            prepared.conversion_identity.run_id,
            token=services.new_token(),
        )
        converter, runtime = _build_converter(prepared, services)
        git_state = services.read_git_state(Path(__file__).resolve().parents[4])
        write_json_atomic(
            workspace.records_root / "conversion_identity.json",
            {
                "conversion_id": prepared.conversion_identity.run_id,
                "identity": prepared.conversion_identity.payload,
            },
        )
        write_json_atomic(workspace.records_root / "runtime_configuration.json", runtime)
        write_json_atomic(
            workspace.records_root / "environment.json",
            {
                "generated_at_utc": services.now().isoformat(),
                "platform": platform.platform(),
                "machine": platform.machine(),
                "git_commit": git_state.commit,
                "git_dirty": git_state.dirty,
            },
        )
        producer_root = (
            workspace.staging_root / "documents" / prepared.source.source_id / "producer"
        )
        output = run_complete_conversion(
            converter=converter,
            source=prepared.source,
            producer_root=producer_root,
            log_path=workspace.staging_root / "logs" / "conversion.log",
            services=services,
        )
        inventory_path = write_inventory(workspace.staging_root)
        if output.observation.status not in {"complete", "complete_with_warnings"}:
            raise RuntimeError("conversion output is not publishable")
        completion = ConversionCompletion(
            conversion_id=prepared.conversion_identity.run_id,
            status=cast(
                Literal["complete", "complete_with_warnings"],
                output.observation.status,
            ),
            source_id=prepared.source.source_id,
            source_sha256=prepared.source.source_sha256,
            source_manifest_sha256=sha256_file(prepared.source_manifest_path),
            artifact_inventory_sha256=sha256_file(inventory_path),
            completed_at_utc=services.now().isoformat(),
        )
        write_json_atomic(
            workspace.records_root / "completion_record.json",
            completion.model_dump(mode="json"),
        )
        sealed = deep_audit_conversion_bundle(
            workspace.staging_root,
            prepared.conversion_identity.run_id,
        )
        publish_workspace(workspace)
        return _relocate_sealed_conversion(sealed, final_root)
    except BaseException as error:
        attempt = preserve_failed_attempt(
            staging_root=workspace.staging_root if workspace is not None else None,
            task_root=conversion_root,
            producer_run_id=prepared.conversion_identity.run_id,
            failed_stage="docling_conversion",
            started_at=started_at,
            finished_at=services.now(),
            wall_seconds=services.monotonic() - started,
            error=error,
            token=services.new_token(),
        )
        setattr(error, _RETAINED_ATTEMPT_ATTRIBUTE, attempt.as_posix())
        raise


def _relocate_sealed_conversion(sealed: SealedConversion, final_root: Path) -> SealedConversion:
    """Retarget already verified staging evidence after its atomic directory rename."""
    return SealedConversion(
        conversion_id=sealed.conversion_id,
        root=final_root,
        completion_path=final_root / "records/completion_record.json",
        inventory_path=final_root / "records/artifact_inventory.json",
        output=sealed.output,
    )
