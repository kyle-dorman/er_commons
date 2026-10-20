"""Verify sealed development sources and assemble saved-candidate evaluation plans."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.artifact_io import (
    artifact_inventory,
    assert_contained,
    sha256_file,
    stable_json_sha256,
)
from er_commons.target_generation import INITIAL, PANEL, REPO, load_smoke, panel_case_ids


def verified(path: Path, binding: dict[str, Any]) -> Any:
    """Read only bytes matching an accepted checksum and size."""
    if sha256_file(path) != binding["sha256"] or path.stat().st_size != binding["byte_size"]:
        raise ValueError(f"Input binding changed: {path}")
    return json.loads(path.read_text())


def load_plans(data_root: Path, generation_run: Path | None = None) -> list[dict[str, Any]]:
    """Bind a complete fixed-panel run, delivery and selected development references."""
    from er_commons.development_evaluation import prepare_candidate

    if generation_run is None:
        source, identities = _load_saved_run(data_root)
        records, _ = load_smoke(data_root)
    else:
        source, identities, records = _load_panel_run(data_root, generation_run)
    mappings = _load_development_mappings(data_root, [r["case_id"] for r in records])
    reference_root, inventory = _load_reference_inventory(data_root)
    plans = []
    for record, identity in zip(records, identities, strict=True):
        case = record["case_id"]
        directory = source / case
        if json.loads((directory / "result.json").read_text()) != identity:
            raise ValueError("Candidate receipt changed")
        request = directory / "native_request.json"
        if sha256_file(request) != identity["request_sha256"]:
            raise ValueError("Delivery request changed")
        if json.loads((directory / "generation_response.json").read_text())["status_code"] != 200:
            raise ValueError("Candidate lacks successful delivery receipt")
        reference_path = f"curator/cases/{case}.json"
        reference = verified(reference_root / reference_path, inventory[reference_path])
        plans.append(
            prepare_candidate(
                (directory / "candidate.json").read_bytes(),
                identity,
                record,
                mappings[case],
                json.loads(request.read_text()),
                reference["answer"]["conclusion"]["text"],
            )
        )
    return plans


def _load_development_mappings(data_root: Path, case_ids: list[str]) -> dict[str, Any]:
    """Verify development mappings and retain only the declared fixed panel."""
    panel = json.loads(PANEL.read_text())
    binding = panel["inputs"]["evaluator/dev_mappings.jsonl"]
    maps_path = assert_contained(data_root, binding["path_relative_to_data_root"])
    if (
        sha256_file(maps_path) != binding["sha256"]
        or maps_path.stat().st_size != binding["byte_size"]
    ):
        raise ValueError("Development mappings changed")
    mappings = {}
    for line in maps_path.read_text().splitlines():
        record = json.loads(line)
        if record["case_id"] in case_ids:
            if record["case_id"] in mappings:
                raise ValueError("Duplicate selected development mapping")
            mappings[record["case_id"]] = record
    if set(mappings) != set(case_ids):
        raise ValueError("Incomplete development mappings")
    return mappings


def _load_saved_run(data_root: Path) -> tuple[Path, list[dict[str, Any]]]:
    """Verify the accepted target-run seal and unchanged ordered panel identities."""
    result = json.loads((REPO / "docs/specs/task11b_final_result.json").read_text())
    if result["case_ids"] != INITIAL or [r["case_id"] for r in result["candidates"]] != INITIAL:
        raise ValueError("Saved smoke panel changed")
    source = assert_contained(data_root, result["namespace"])
    verified(source / "completion.json", result["artifacts"]["completion.json"])
    if json.loads((source / "completion.json").read_text()) != artifact_inventory(
        source, {"completion.json"}
    ):
        raise ValueError("Saved target run inventory changed")
    return source, result["candidates"]


def _load_reference_inventory(data_root: Path) -> tuple[Path, dict[str, Any]]:
    """Verify release metadata without opening any unselected case content."""
    release = json.loads(
        (REPO / "docs/specs/task09f_question_publication_v2_result.json").read_text()
    )
    release_path = Path(release["completion"]["path"])
    if not release_path.resolve().is_relative_to(data_root.resolve()):
        raise ValueError("Release outside data root")
    seal = verified(release_path, release["completion"])
    inventory = {r["path"]: r for r in seal["inventory"]}
    return release_path.parent, inventory


def _load_panel_run(
    data_root: Path, source: Path
) -> tuple[Path, list[dict[str, Any]], list[dict[str, Any]]]:
    """Accept only complete sealed fixed-panel runs with exact candidate identities."""
    source = source.resolve()
    if not source.is_relative_to(data_root.resolve()):
        raise ValueError("Generation run outside data root")
    if json.loads((source / "completion.json").read_text()) != artifact_inventory(
        source, {"completion.json"}
    ):
        raise ValueError("Saved target run inventory changed")
    manifest = json.loads((source / "manifest.json").read_text())
    summary = json.loads((source / "summary.json").read_text())
    case_ids = manifest["case_ids"]
    panel = next(
        (name for name in ("initial_three", "expanded_six") if case_ids == panel_case_ids(name)),
        None,
    )
    if panel is None or summary["case_ids"] != case_ids:
        raise ValueError("Only complete fixed three/six panels may be evaluated")
    records, bindings = load_smoke(data_root, panel=panel)
    namespace = str(source.relative_to(data_root.resolve()))
    if (
        manifest["bindings"] != bindings
        or manifest["namespace"] != namespace
        or manifest["run_id"] != stable_json_sha256(namespace)
        or manifest["repeat"] not in (1, 2)
        or manifest["attempts_per_case"] != 1
    ):
        raise ValueError("Generation manifest identity/bindings changed")
    identities = summary["results"]
    if [r["case_id"] for r in identities] != case_ids:
        raise ValueError("Incomplete or duplicate candidate panel")
    for identity in identities:
        if (
            identity["status"] != "valid"
            or identity["run_id"] != manifest["run_id"]
            or identity["repeat"] != manifest["repeat"]
            or identity["attempt"] != 1
            or identity["generation_calls"] != 1
            or identity["count_calls"] != 1
        ):
            raise ValueError("Incomplete or inconsistent generation receipt; retain failure")
        expected = stable_json_sha256(
            {
                key: identity[key]
                for key in (
                    "run_id",
                    "case_id",
                    "attempt",
                    "repeat",
                    "request_sha256",
                    "candidate_sha256",
                )
            }
        )
        if identity["candidate_id"] != expected:
            raise ValueError("Candidate identity changed")
    return source, identities, records
