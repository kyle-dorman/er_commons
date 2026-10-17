"""Verify sealed development sources and assemble saved-candidate evaluation plans."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons.artifact_io import artifact_inventory, assert_contained, sha256_file
from er_commons.target_generation import INITIAL, PANEL, REPO, load_smoke


def verified(path: Path, binding: dict[str, Any]) -> Any:
    """Read only bytes matching an accepted checksum and size."""
    if sha256_file(path) != binding["sha256"] or path.stat().st_size != binding["byte_size"]:
        raise ValueError(f"Input binding changed: {path}")
    return json.loads(path.read_text())


def load_plans(data_root: Path) -> list[dict[str, Any]]:
    """Bind saved initial-panel candidates, delivery and development references only."""
    from er_commons.development_evaluation import prepare_candidate

    records, _ = load_smoke(data_root)
    mappings = _load_development_mappings(data_root)
    source, identities = _load_saved_run(data_root)
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


def _load_development_mappings(data_root: Path) -> dict[str, Any]:
    """Verify the development mapping file and retain only the initial three cases."""
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
        if record["case_id"] in INITIAL:
            mappings[record["case_id"]] = record
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
