"""Compare current Task 05G readers/resolver with a sealed historical candidate.

This is a read-only refactor audit, not a replay writer. It deliberately uses the
historical activity ID for byte comparison; the report separately identifies the
current code. It never publishes a candidate, updates pins, or accepts anything.
Run under the documented background supervisor when reading real artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from er_commons.artifact_io import json_bytes, jsonl_bytes
from er_commons.response_inventory.reference_replay_comparison import (
    compare_outcomes,
    validate_activity,
    validate_result,
)
from er_commons.response_inventory.reference_replay_inputs import load_replay_inputs
from er_commons.response_inventory.reference_replay_resolver import resolve_references
from er_commons.response_inventory.reference_replay_spec import (
    HEADER_POLICY,
    INNER_REFERENCE_POLICIES,
    ReferenceReplaySpec,
    contained_path,
    replay_identity,
    required_repository_paths,
)
from er_commons.response_inventory.reference_replay_storage import read_checkpoint
from er_commons.response_inventory.reference_replay_workflow import RESULT_FILES


def verify(result_path: Path, repository: Path, data_root: Path) -> dict[str, Any]:
    """Verify historical closure, then reproduce every result byte using current code."""
    summary = json.loads(result_path.read_text())
    completions = {}
    for stage, ref in summary["checkpoint_seals"].items():
        path = Path(ref["path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != ref["sha256"]:
            raise ValueError(f"historical checkpoint seal differs: {path}")
        completion = json.loads(path.read_text())
        completions[stage] = read_checkpoint(path.parent, completion["bindings"])
    packet_ref = summary["executions"][0]["launch_packet"]
    packet_bytes = Path(packet_ref["path"]).read_bytes()
    if hashlib.sha256(packet_bytes).hexdigest() != packet_ref["sha256"]:
        raise ValueError("historical launch packet seal differs")
    packet = json.loads(packet_bytes)
    request = packet["request_text"].encode()
    if hashlib.sha256(request).hexdigest() != packet["request_sha256"]:
        raise ValueError("historical request seal differs")
    spec = ReferenceReplaySpec.model_validate_json(request).model_dump(
        mode="json", exclude_none=True
    )
    digest = replay_identity(spec)
    if digest != summary["behavior_sha256"]:
        raise ValueError("historical behavior identity differs")
    if summary["candidate_id"] != "replayv1-" + digest:
        raise ValueError("historical candidate identity differs")
    for stage, completion in completions.items():
        bindings = completion["bindings"]
        if bindings["run_spec_sha256"] != digest or bindings["stage"] != stage.removesuffix(
            "_root"
        ):
            raise ValueError(f"historical checkpoint stage/request binding differs: {stage}")
    for key in ("candidate_root", "comparison_root"):
        sealed_root = Path(summary["checkpoint_seals"][key]["path"]).parent
        if Path(summary[key]).resolve() != sealed_root.resolve():
            raise ValueError(f"historical payload root differs from checkpoint seal: {key}")
    inputs = load_replay_inputs(spec, repository, data_root)
    for stage, completion in completions.items():
        if completion["bindings"]["dependencies"] != inputs.dependencies:
            raise ValueError(f"historical checkpoint dependencies differ: {stage}")
    candidate = Path(summary["candidate_root"])
    activity = json.loads((candidate / "records/activity.json").read_text())
    result = resolve_references(
        source_records=inputs.source_records,
        target_rows=inputs.target_rows,
        direct_section_children={
            key: list(value) for key, value in inputs.direct_section_children.items()
        },
        catalog=inputs.catalog,
        registry=inputs.registry,
        target_limitations=inputs.target_limitations,
        handoff=inputs.handoff,
        activity=activity,
        baseline_outcomes=inputs.baseline_outcomes,
        inner_references=spec["policy"] in INNER_REFERENCE_POLICIES,
        header_qualification=spec["policy"] == HEADER_POLICY,
    )
    population = json.loads(contained_path(repository, spec["population_freeze"]).read_text())
    validate_activity(
        activity,
        result,
        expected_input_refs=inputs.dependencies,
        expected_activity_id="activityv1-" + digest,
    )
    validate_result(result, inputs.baseline_outcomes, population, expected_result=result)
    checked = []
    for key, name in RESULT_FILES.items():
        if jsonl_bytes(result[key]) != (candidate / name).read_bytes():
            raise ValueError(f"refactor changed historical result bytes: {name}")
        checked.append(name)
    if json_bytes(result["census"]) != (candidate / "diagnostics/rule_census.json").read_bytes():
        raise ValueError("refactor changed historical census")
    comparison = compare_outcomes(
        inputs.baseline_outcomes,
        result["outcomes"],
        population=population,
        correspondence=inputs.correspondence,
        approved_inner_rules=spec["policy"] in INNER_REFERENCE_POLICIES,
        approved_header_rules=spec["policy"] == HEADER_POLICY,
    )
    if (
        json_bytes(comparison)
        != (Path(summary["comparison_root"]) / "comparison.json").read_bytes()
    ):
        raise ValueError("refactor changed historical comparison bytes")
    return {
        "status": "passed_read_only_equivalence",
        "historical_candidate_id": summary["candidate_id"],
        "historical_checkpoint_seals": summary["checkpoint_seals"],
        "current_repository_bindings": [
            {"path": name, "sha256": hashlib.sha256((repository / name).read_bytes()).hexdigest()}
            for name in sorted(
                required_repository_paths(repository) | {"scripts/verify_task05g_refactor.py"}
            )
        ],
        "census": result["census"],
        "byte_equal_result_files": checked + ["diagnostics/rule_census.json", "comparison.json"],
        "candidate_published": False,
        "acceptance_published": False,
        "source_pdf_accessed": False,
        "model_accessed": False,
    }


def main() -> None:
    """Print one compact audit report; shell redirection controls its output path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.result, Path(__file__).resolve().parents[1], args.data_root)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
