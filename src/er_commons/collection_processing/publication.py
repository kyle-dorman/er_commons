"""Completion-last, no-clobber publication for deterministic stage builds."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from er_commons.collection_processing.attempts import AttemptJournal
from er_commons.collection_processing.domain import (
    PublishedStage,
    StageBuild,
    StageHooks,
)
from er_commons.collection_processing.storage import (
    file_ref,
    json_bytes,
    managed_inventory,
)

LOGGER = logging.getLogger(__name__)


class StagePublisher:
    """Atomically publish or exactly reuse one complete deterministic build."""

    def __init__(self, extraction_root: Path, scope_id: str) -> None:
        self._extraction_root = extraction_root.resolve()
        self._scope_root = self._extraction_root / "scopes" / scope_id
        self._journal = AttemptJournal(self._extraction_root, self._scope_root)

    def publish(self, build: StageBuild, hooks: StageHooks | None = None) -> PublishedStage:
        """Publish a new stage or verify and reconcile its exact prior result."""
        active_hooks = hooks or StageHooks()
        final_root = self._scope_root / build.name.directory / build.identity
        completion_path = final_root / "records" / "completion_record.json"
        started = time.monotonic()
        LOGGER.info(
            "Starting collection stage stage=%s stage_id=%s",
            build.name.value,
            build.identity,
        )
        if final_root.exists():
            self._verify(final_root, build)
            self._journal.reconcile_published(
                build.name, build.identity, completion_path, active_hooks
            )
            LOGGER.info(
                "Reused collection stage stage=%s stage_id=%s wall_seconds=%.3f",
                build.name.value,
                build.identity,
                time.monotonic() - started,
            )
            return self._published(build, completion_path)

        try:
            attempt = self._journal.reserve(build.name, build.identity)
            self._write_staging(attempt.staging_root, build)
            staged_completion = attempt.staging_root / "records" / "completion_record.json"
            active_hooks.before_publish(staged_completion)
            final_root.parent.mkdir(parents=True, exist_ok=True)
            if final_root.exists():
                raise FileExistsError(f"stage destination exists: {final_root}")
            attempt.staging_root.rename(final_root)
            active_hooks.after_publish(completion_path)
            self._journal.complete(
                attempt,
                build.name,
                build.identity,
                completion_path,
                active_hooks,
            )
            self._verify(final_root, build)
        except Exception:
            LOGGER.exception(
                "Collection stage failed stage=%s stage_id=%s wall_seconds=%.3f",
                build.name.value,
                build.identity,
                time.monotonic() - started,
            )
            raise
        LOGGER.info(
            "Published collection stage stage=%s stage_id=%s wall_seconds=%.3f",
            build.name.value,
            build.identity,
            time.monotonic() - started,
        )
        return self._published(build, completion_path)

    @staticmethod
    def _write_staging(root: Path, build: StageBuild) -> None:
        for relative, value in build.payloads.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        records = root / "records"
        records.mkdir(parents=True, exist_ok=True)
        (records / "artifact_inventory.json").write_bytes(
            json_bytes(managed_inventory(build.payloads))
        )
        (records / "completion_record.json").write_bytes(json_bytes(build.completion))

    @staticmethod
    def _verify(final_root: Path, build: StageBuild) -> None:
        completion = final_root / "records" / "completion_record.json"
        inventory = final_root / "records" / "artifact_inventory.json"
        if not completion.is_file() or not inventory.is_file():
            raise ValueError("stage destination lacks completion or inventory")
        if json.loads(completion.read_bytes()) != build.completion:
            raise ValueError("stage completion differs from recomputed content")
        if json.loads(inventory.read_bytes()) != managed_inventory(build.payloads):
            raise ValueError("stage inventory differs from recomputed content")
        excluded = {"records/artifact_inventory.json", "records/completion_record.json"}
        observed = {
            path.relative_to(final_root).as_posix(): path.read_bytes()
            for path in final_root.rglob("*")
            if path.is_file() and path.relative_to(final_root).as_posix() not in excluded
        }
        if observed != build.payloads:
            raise ValueError("stage managed-file closure differs")

    def _published(self, build: StageBuild, completion_path: Path) -> PublishedStage:
        return PublishedStage(
            completion_path=completion_path,
            completion_ref=file_ref(completion_path, self._extraction_root),
            attempts=self._journal.records(build.name, build.identity),
        )
