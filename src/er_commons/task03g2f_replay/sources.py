"""Source-level preparation for the bounded downstream replay."""

from __future__ import annotations

from pathlib import Path

from er_commons.corpus_extraction.downstream_replay import publish_downstream_replay
from er_commons.cross_reference_enrichment.workflow import run_cross_reference_enrichment
from er_commons.task03g2f_replay.config import SOURCE_CONFIG_SLUGS, ReplayPaths
from er_commons.task03g2f_replay.errors import ReplayValidationError
from er_commons.task03g2f_replay.io import (
    JsonObject,
    json_bytes,
    read_json,
    sha256_file,
    write_exact,
)


class RetainedPilot:
    """Load and verify the three immutable pre-repair document candidates."""

    def __init__(self, paths: ReplayPaths) -> None:
        self.paths = paths

    def document_candidates(self) -> dict[str, Path]:
        """Return source-keyed candidate roots from sealed scope accounting."""
        bundle = read_json(self.paths.retained_bundle)
        accounting = _object(bundle, "accounting", self.paths.retained_bundle)
        rows = accounting.get("rows")
        if not isinstance(rows, list):
            raise ReplayValidationError(
                "RETAINED_ACCOUNTING_ROWS",
                "retained bundle has no accounting row list",
                path=str(self.paths.retained_bundle),
            )
        if len(rows) != len(SOURCE_CONFIG_SLUGS) or not all(isinstance(row, dict) for row in rows):
            raise ReplayValidationError(
                "RETAINED_ACCOUNTING_SHAPE",
                "retained accounting must contain exactly three object rows",
                expected_rows=len(SOURCE_CONFIG_SLUGS),
                observed_rows=len(rows),
            )
        candidates = dict(self._candidate(row) for row in rows)
        expected = set(SOURCE_CONFIG_SLUGS)
        if set(candidates) != expected:
            raise ReplayValidationError(
                "RETAINED_SOURCE_SET",
                "retained pilot does not contain the exact reviewed source set",
                expected=sorted(expected),
                observed=sorted(candidates),
            )
        return candidates

    def _candidate(self, row: JsonObject) -> tuple[str, Path]:
        source_id = str(row.get("source_id"))
        reference = row.get("document_completion_ref")
        if not isinstance(reference, dict):
            raise ReplayValidationError(
                "RETAINED_DOCUMENT_COMPLETION",
                "retained source lacks a successful document completion",
                source_id=source_id,
            )
        completion = self.paths.pilot_root / str(reference.get("path"))
        expected_sha = reference.get("sha256")
        observed_sha = sha256_file(completion)
        if observed_sha != expected_sha:
            raise ReplayValidationError(
                "RETAINED_DOCUMENT_SEAL",
                "retained document completion checksum differs",
                source_id=source_id,
                path=str(completion),
                expected=expected_sha,
                observed=observed_sha,
            )
        return source_id, completion.parents[1]


class SourceReplayer:
    """Replace one source's cross-reference owner and republish its document."""

    def __init__(self, paths: ReplayPaths) -> None:
        self.paths = paths

    def replay(self, source_id: str, source_candidate: Path) -> tuple[Path, Path]:
        """Return the new document root and replacement cross-reference root."""
        completion = self._run_cross_references(source_id, source_candidate)
        document_completion = publish_downstream_replay(
            data_root=self.paths.data_root,
            document_run_spec=self.paths.document_spec,
            source_id=source_id,
            source_candidate_root=source_candidate,
            cross_reference_completion=completion,
        )
        return document_completion.parents[1], completion.parents[1]

    def _run_cross_references(self, source_id: str, candidate: Path) -> Path:
        identity_path = candidate / "records/document_identity.json"
        identity = read_json(identity_path)
        stages = _object(identity, "stage_completions", identity_path)
        semantic = _object(stages, "semantic", identity_path)
        completion = self.paths.data_root / str(semantic.get("path"))
        expected_sha = semantic.get("sha256")
        observed_sha = sha256_file(completion)
        if observed_sha != expected_sha:
            raise ReplayValidationError(
                "SEMANTIC_OWNER_SEAL",
                "semantic completion checksum differs before downstream replay",
                source_id=source_id,
                path=str(completion),
                expected=expected_sha,
                observed=observed_sha,
            )
        semantic_root = completion.parents[1]
        template = self.paths.cross_reference_template(source_id)
        effective = read_json(template)
        effective.update(
            upstream_candidate_id=semantic_root.name,
            upstream_completion_sha256=observed_sha,
            upstream_inventory_sha256=sha256_file(
                semantic_root / "records/artifact_inventory.json"
            ),
        )
        control = self.paths.effective_cross_reference_config(source_id)
        write_exact(control, json_bytes(effective))
        return run_cross_reference_enrichment(
            self.paths.data_root,
            control,
            config_identity_path=template,
        )


def publish_shared_catalog(paths: ReplayPaths) -> None:
    """Copy the checked catalog into the pilot's immutable input namespace."""
    destination = paths.pilot_root / "inputs" / paths.source_family_catalog.name
    write_exact(destination, paths.source_family_catalog.read_bytes())


def _object(value: JsonObject, field: str, path: Path) -> JsonObject:
    nested = value.get(field)
    if not isinstance(nested, dict):
        raise ReplayValidationError(
            "REPLAY_RECORD_SHAPE",
            "required replay record field is not an object",
            path=str(path),
            field=field,
        )
    return nested
