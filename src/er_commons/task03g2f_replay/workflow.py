"""Short application shell for the bounded Task 03G.2f replay."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from er_commons.collection_processing.workflow import assemble_collection_handoff
from er_commons.task03g2f_replay.audit import PilotReplayAuditor
from er_commons.task03g2f_replay.config import ReplayPaths
from er_commons.task03g2f_replay.errors import ReplayValidationError
from er_commons.task03g2f_replay.inventory import (
    AttemptSnapshot,
    require_unchanged,
    serialize_snapshot,
    snapshot_attempts,
)
from er_commons.task03g2f_replay.io import (
    JsonObject,
    json_bytes,
    read_json,
    sha256_file,
    write_exact,
)
from er_commons.task03g2f_replay.sources import (
    RetainedPilot,
    SourceReplayer,
    publish_shared_catalog,
)

EXPECTED_RESOLUTIONS = 18


@dataclass(frozen=True)
class ReplayOutcome:
    """Final report and its immutable artifact location."""

    report: JsonObject
    report_path: Path


@dataclass(frozen=True)
class ScopePublication:
    """Paths and parsed evidence from an exactly reused scope publication."""

    bundle_path: Path
    handoff_path: Path
    bundle: JsonObject


class Task03G2FReplay:
    """Coordinate only the reviewed downstream replay and its evidence checks."""

    def __init__(self, paths: ReplayPaths) -> None:
        self.paths = paths

    def execute(self) -> ReplayOutcome:
        """Run the replay, prove attempt isolation, and write its audit report."""
        publish_shared_catalog(self.paths)
        old_candidates = RetainedPilot(self.paths).document_candidates()
        before = snapshot_attempts(self.paths.forbidden_attempt_roots)
        new_candidates, cross_roots = self._replay_sources(old_candidates)

        audit = PilotReplayAuditor().audit(
            old_candidates=old_candidates,
            new_candidates=new_candidates,
            new_cross_reference_roots=cross_roots,
        )
        self._require_attempt_isolation(before, "source replay")
        publication = self._publish_scope_with_exact_reuse()
        self._require_attempt_isolation(before, "scope replay")

        report = audit.as_json()
        report.update(self._scope_evidence(publication, before))
        report_path = self.paths.replay_report(str(report["new_scope_id"]))
        write_exact(report_path, json_bytes(report))
        return ReplayOutcome(report=report, report_path=report_path)

    def _replay_sources(
        self, old_candidates: dict[str, Path]
    ) -> tuple[dict[str, Path], dict[str, Path]]:
        documents: dict[str, Path] = {}
        cross_references: dict[str, Path] = {}
        replayer = SourceReplayer(self.paths)
        for source_id, candidate in old_candidates.items():
            documents[source_id], cross_references[source_id] = replayer.replay(
                source_id, candidate
            )
        return documents, cross_references

    def _publish_scope_with_exact_reuse(self) -> ScopePublication:
        first_handoff = assemble_collection_handoff(self.paths.data_root, self.paths.scope_spec)
        first_bundle = first_handoff.parents[3] / "contract_bundle.json"
        bundle_bytes = first_bundle.read_bytes()
        handoff_bytes = first_handoff.read_bytes()

        second_handoff = assemble_collection_handoff(self.paths.data_root, self.paths.scope_spec)
        second_bundle = second_handoff.parents[3] / "contract_bundle.json"
        if second_bundle != first_bundle or second_bundle.read_bytes() != bundle_bytes:
            raise ReplayValidationError(
                "SCOPE_REUSE",
                "identical scope invocation did not reuse exact bundle bytes",
                first=str(first_bundle),
                second=str(second_bundle),
            )
        if second_handoff != first_handoff or second_handoff.read_bytes() != handoff_bytes:
            raise ReplayValidationError(
                "HANDOFF_REUSE",
                "identical scope invocation did not reuse exact handoff bytes",
                first=str(first_handoff),
                second=str(second_handoff),
            )
        return ScopePublication(first_bundle, first_handoff, read_json(first_bundle))

    def _require_attempt_isolation(self, before: AttemptSnapshot, operation: str) -> None:
        after = snapshot_attempts(self.paths.forbidden_attempt_roots)
        require_unchanged(before, after, operation=operation)

    @staticmethod
    def _scope_evidence(publication: ScopePublication, attempts: AttemptSnapshot) -> JsonObject:
        bundle = publication.bundle
        accounting = _required_object(bundle, "accounting")
        target_index = _required_object(bundle, "target_index")
        resolutions = _required_object(bundle, "resolution_completion")
        handoff = _required_object(bundle, "handoff")
        counts = _required_object(resolutions, "counts")
        if (
            counts.get("total") != EXPECTED_RESOLUTIONS
            or counts.get("resolved") != EXPECTED_RESOLUTIONS
        ):
            raise ReplayValidationError(
                "RESOLUTION_COUNTS",
                "repaired corpus resolution does not match the reviewed pilot",
                expected={"total": EXPECTED_RESOLUTIONS, "resolved": EXPECTED_RESOLUTIONS},
                observed=counts,
            )
        return {
            "new_scope_id": accounting["scope_id"],
            "index_id": target_index["index_id"],
            "resolution_id": resolutions["resolution_id"],
            "resolution_counts": counts,
            "handoff_id": handoff["handoff_id"],
            "handoff_status": handoff["status"],
            "contract_bundle_sha256": sha256_file(publication.bundle_path),
            "handoff_completion_sha256": sha256_file(publication.handoff_path),
            "identical_reuse": True,
            "attempt_snapshot": serialize_snapshot(attempts),
        }


def _required_object(record: JsonObject, field: str) -> JsonObject:
    value = record.get(field)
    if not isinstance(value, dict):
        raise ReplayValidationError(
            "SCOPE_RECORD_SHAPE",
            "scope bundle field is not an object",
            field=field,
        )
    return value
