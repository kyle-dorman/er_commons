"""Four explicit source-free consumer stages; execution requires a new authorization."""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import canonical_json_sha256, json_bytes, jsonl_bytes
from er_commons.response_inventory.reference_replay_inputs import ReplayInputs
from er_commons.response_inventory.reference_replay_spec import (
    HEADER_POLICY,
    INNER_REFERENCE_POLICIES,
    contained_path,
    load_replay_spec,
)
from er_commons.response_inventory.reference_replay_storage import (
    publish_checkpoint,
    read_checkpoint,
)

LOGGER = logging.getLogger(__name__)
RESULT_FILES = {
    "outcomes": "outcomes/reference_outcomes.jsonl",
    "links": "links/draft_eir_links.jsonl",
    "diagnostics": "diagnostics/individual_diagnostics.jsonl",
    "forward": "indexes/mention_to_link.jsonl",
    "reverse": "indexes/target_to_links.jsonl",
}


@dataclass(frozen=True)
class ReplayRun:
    """Exact paths and request identity; attempts never select a newest candidate."""

    spec: dict[str, Any]
    digest: str
    repository_root: Path
    artifact_root: Path
    attempt: int = 1
    resume_from: int | None = None

    @property
    def candidate_id(self) -> str:
        """Return the input/behavior identity independent of attempt number."""
        return f"replayv1-{self.digest}"

    @property
    def root(self) -> Path:
        """Resolve the one owned output root after path containment validation."""
        return contained_path(self.artifact_root, self.spec["output_relative_root"])

    def stage_root(self, stage: str, attempt: int | None = None) -> Path:
        """Give each failed attempt its own path without changing semantic identity."""
        ordinal = self.attempt if attempt is None else attempt
        suffix = f"attempt-{ordinal:03d}"
        roots = {
            "prepared": self.root / "plans" / self.digest / suffix,
            "resolved": self.root / "attempts" / self.digest / suffix / "resolved",
            "candidate": self.root / "candidates" / self.candidate_id / suffix,
            "comparison": self.root / "comparisons" / self.candidate_id / suffix,
        }
        return roots[stage]


def open_run(
    run_spec: Path,
    repository_root: Path,
    artifact_root: Path,
    *,
    attempt: int = 1,
    resume_from: int | None = None,
) -> ReplayRun:
    """Validate current writer pins and explicit restart selection before external access."""
    if attempt < 1 or (resume_from is not None and not 0 < resume_from < attempt):
        raise ValueError("attempt must be positive; resume-from must name an earlier attempt")
    spec, digest = load_replay_spec(run_spec, repository_root)
    return ReplayRun(spec, digest, repository_root, artifact_root, attempt, resume_from)


def _authorized(run: ReplayRun) -> None:
    """Reject corpus preparation or execution until its separate replay gate is granted."""
    if run.spec["authorization"]["replay"] is not True:
        raise ValueError("Task 05G replay is not authorized by this request")


def _bindings(run: ReplayRun, stage: str, dependencies: list[dict[str, Any]]) -> dict[str, Any]:
    """Bind a stage to its exact request and accepted dependency set."""
    return {"run_spec_sha256": run.digest, "stage": stage, "dependencies": dependencies}


def _existing_stage(run: ReplayRun, stage: str, bindings: dict[str, Any]) -> Path | None:
    """Reuse only an explicitly selected complete stage; never skip a malformed completion."""
    selected = run.stage_root(stage)
    if selected.exists():
        read_checkpoint(selected, bindings)
        LOGGER.info("Task 05G reusing stage=%s checkpoint=%s", stage, selected)
        return selected
    if run.resume_from is not None:
        prior = run.stage_root(stage, run.resume_from)
        if (prior / "completion.json").exists():
            read_checkpoint(prior, bindings)
            LOGGER.info("Task 05G resuming stage=%s checkpoint=%s", stage, prior)
            return prior
    return None


def _load_inputs(run: ReplayRun) -> ReplayInputs:
    """Import the source-free consumer only after checking execution authorization."""
    from er_commons.response_inventory.reference_replay_inputs import load_replay_inputs

    return load_replay_inputs(run.spec, run.repository_root, run.artifact_root)


def _activity(run: ReplayRun, dependencies: list[dict[str, Any]]) -> dict[str, Any]:
    """Bind every newly authored link to the same ordered verified dependency set."""
    return {
        "schema_version": "er_commons.response_inventory.v2",
        "record_type": "activity",
        "activity_id": f"activityv1-{run.digest}",
        "input_refs": dependencies,
        "policy": run.spec["policy"],
    }


def _prepare(run: ReplayRun, inputs: ReplayInputs) -> Path:
    """Freeze checked input membership without resolving a single reference."""
    from er_commons.response_inventory.reference_replay_comparison import validate_population

    validate_population(inputs.baseline_outcomes, _population(run))
    bindings = _bindings(run, "prepared", inputs.dependencies)
    existing = _existing_stage(run, "prepared", bindings)
    if existing is not None:
        return existing
    root = run.stage_root("prepared")
    payload = {
        "candidate_id": run.candidate_id,
        "dependencies": inputs.dependencies,
        "mention_ids": sorted(row["mention_id"] for row in inputs.baseline_outcomes),
        "source_pdf_accessed": False,
        "model_accessed": False,
        "supplemental_qualified_aliases": [
            row for row in inputs.target_rows if "qualification_input_inventory" in row
        ],
    }
    publish_checkpoint(root, {"prepared_inputs.json": json_bytes(payload)}, bindings)
    return root


def prepare_replay(run: ReplayRun) -> dict[str, Any]:
    """Prepare only the accepted-input checkpoint, without matching or publication."""
    _authorized(run)
    inputs = _load_inputs(run)
    root = _prepare(run, inputs)
    LOGGER.info("Task 05G prepared input checkpoint: %s", root)
    return {"status": "prepared", "checkpoint_root": str(root), "candidate_id": run.candidate_id}


def _resolve(run: ReplayRun, inputs: ReplayInputs) -> dict[str, Any]:
    """Adapt verified inputs to the pure exact resolver; never open a source payload."""
    from er_commons.response_inventory.reference_replay_resolver import resolve_references

    return resolve_references(
        inputs.source_records,
        inputs.target_rows,
        {key: list(value) for key, value in inputs.direct_section_children.items()},
        inputs.catalog,
        inputs.registry,
        inputs.target_limitations,
        inputs.handoff,
        _activity(run, inputs.dependencies),
        inputs.baseline_outcomes,
        header_qualification=run.spec["policy"] == HEADER_POLICY,
        inner_references=run.spec["policy"] in INNER_REFERENCE_POLICIES,
    )


def _payloads(result: dict[str, Any], activity: dict[str, Any]) -> dict[str, bytes]:
    """Serialize only owned derived records, never source units or graph payloads."""
    return {
        **{name: jsonl_bytes(result[key]) for key, name in RESULT_FILES.items()},
        "diagnostics/rule_census.json": json_bytes(result["census"]),
        "records/activity.json": json_bytes(activity),
        "records/dependencies.json": json_bytes({"inputs": activity["input_refs"]}),
    }


def _read_result(root: Path) -> dict[str, Any]:
    """Read verified new owned payloads in their deterministic publication shape."""
    result = {
        key: [json.loads(line) for line in (root / name).read_text().splitlines()]
        for key, name in RESULT_FILES.items()
    }
    return {**result, "census": json.loads((root / "diagnostics/rule_census.json").read_text())}


def _read_bound_result(run: ReplayRun, inputs: ReplayInputs, root: Path) -> dict[str, Any]:
    """Check stored activity/dependency semantics in addition to checkpoint byte closure."""
    from er_commons.response_inventory.reference_replay_comparison import validate_activity

    result = _read_result(root)
    activity = json.loads((root / "records/activity.json").read_text())
    dependencies = json.loads((root / "records/dependencies.json").read_text())
    if dependencies != {"inputs": inputs.dependencies}:
        raise ValueError("05G candidate dependency record differs from accepted inputs")
    validate_activity(
        activity,
        result,
        expected_input_refs=inputs.dependencies,
        expected_activity_id="activityv1-" + run.digest,
    )
    return result


def _population(run: ReplayRun) -> dict[str, Any]:
    """Read the repository-pinned exact baseline membership, not a count-only substitute."""
    value: dict[str, Any] = json.loads(
        contained_path(run.repository_root, run.spec["population_freeze"]).read_text()
    )
    return value


def build_replay(run: ReplayRun) -> dict[str, Any]:
    """Publish a nonterminal working link layer using verified complete checkpoints."""
    _authorized(run)
    inputs = _load_inputs(run)
    _prepare(run, inputs)
    bindings = _bindings(run, "candidate", inputs.dependencies)
    existing = _existing_stage(run, "candidate", bindings)
    if existing is not None:
        return _candidate_summary(run, existing, _read_bound_result(run, inputs, existing))
    resolved_bindings = _bindings(run, "resolved", inputs.dependencies)
    resolved = _existing_stage(run, "resolved", resolved_bindings)
    if resolved is None:
        result = _resolve(run, inputs)
        _validate_result(run, inputs, result, expected=result)
        resolved = run.stage_root("resolved")
        publish_checkpoint(
            resolved, _payloads(result, _activity(run, inputs.dependencies)), resolved_bindings
        )
    result = _read_bound_result(run, inputs, resolved)
    _validate_result(run, inputs, result)
    root = run.stage_root("candidate")
    publish_checkpoint(root, _payloads(result, _activity(run, inputs.dependencies)), bindings)
    return _candidate_summary(run, root, result)


def _candidate_summary(run: ReplayRun, root: Path, result: dict[str, Any]) -> dict[str, Any]:
    """Report working status explicitly without implying final acceptance."""
    return {
        "status": "working_candidate_complete_review_required",
        "candidate_id": run.candidate_id,
        "candidate_root": str(root),
        "semantic_digest": canonical_json_sha256(result),
        "census": result["census"],
        "acceptance_published": False,
        "task05h_execution_authorized": False,
    }


def _validate_result(
    run: ReplayRun,
    inputs: ReplayInputs,
    result: dict[str, Any],
    *,
    expected: dict[str, Any] | None = None,
) -> None:
    """Apply schema, population, provenance, warning and bidirectional closure checks."""
    from er_commons.response_inventory.reference_replay_comparison import (
        validate_activity,
        validate_result,
    )

    validate_activity(
        _activity(run, inputs.dependencies),
        result,
        expected_input_refs=inputs.dependencies,
        expected_activity_id="activityv1-" + run.digest,
    )
    validate_result(result, inputs.baseline_outcomes, _population(run), expected_result=expected)


def compare_replay(run: ReplayRun) -> dict[str, Any]:
    """Compare every baseline mention; an unowned difference prevents completion."""
    _authorized(run)
    inputs = _load_inputs(run)
    root = _existing_stage(run, "candidate", _bindings(run, "candidate", inputs.dependencies))
    if root is None:
        raise ValueError("Task 05G comparison requires a complete selected candidate")
    result = _read_bound_result(run, inputs, root)
    _validate_result(run, inputs, result, expected=_resolve(run, inputs))
    from er_commons.response_inventory.reference_replay_comparison import compare_outcomes

    comparison = compare_outcomes(
        inputs.baseline_outcomes,
        result["outcomes"],
        population=_population(run),
        correspondence=inputs.correspondence,
        approved_header_rules=run.spec["policy"] == HEADER_POLICY,
        approved_inner_rules=run.spec["policy"] in INNER_REFERENCE_POLICIES,
    )
    bindings = _bindings(run, "comparison", inputs.dependencies)
    existing = _existing_stage(run, "comparison", bindings)
    selected = existing or run.stage_root("comparison")
    payloads = {"comparison.json": json_bytes(comparison)}
    if run.spec.get("prior_replay") is not None:
        from er_commons.response_inventory.reference_replay_cycle import (
            compare_rule_cycle,
            prior_outcomes,
        )

        prior = run.spec["prior_replay"]
        cycle = compare_rule_cycle(
            prior_outcomes(prior, run.artifact_root),
            result["outcomes"],
            prior["allowed_change_mentions"],
        )
        payloads["rule_cycle_comparison.json"] = json_bytes(cycle)
    publish_checkpoint(selected, payloads, bindings)
    return {
        "status": "comparison_complete",
        "comparison_root": str(selected),
        **comparison["census"],
    }


def validate_replay(run: ReplayRun) -> dict[str, Any]:
    """Validate selected new artifacts read-only, including deterministic semantic reproduction."""
    _authorized(run)
    inputs = _load_inputs(run)
    root = _existing_stage(run, "candidate", _bindings(run, "candidate", inputs.dependencies))
    if root is None:
        raise ValueError("Task 05G validation requires a complete selected candidate")
    result = _read_bound_result(run, inputs, root)
    _validate_result(run, inputs, result, expected=_resolve(run, inputs))
    return {**_candidate_summary(run, root, result), "status": "valid"}


def main() -> None:
    """Run the explicitly authorized three-stage worker under the maintained supervisor."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-spec", type=Path, required=True)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--resume-from", type=int)
    parser.add_argument("--execute-stages", action="store_true", required=True)
    parser.add_argument(
        "--operation", choices=("all", "prepare", "build", "compare", "validate"), default="all"
    )
    args = parser.parse_args()
    data_root = os.environ.get("ER_COMMONS_DATA_ROOT")
    if not data_root:
        parser.error("ER_COMMONS_DATA_ROOT is required")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run = open_run(
        args.run_spec,
        Path(__file__).resolve().parents[3],
        Path(data_root),
        attempt=args.attempt,
        resume_from=args.resume_from,
    )
    operations = {
        "prepare": prepare_replay,
        "build": build_replay,
        "compare": compare_replay,
        "validate": validate_replay,
    }
    selected = (
        tuple(operations[key] for key in ("prepare", "build", "compare"))
        if args.operation == "all"
        else (operations[args.operation],)
    )
    for operation in selected:
        LOGGER.info(
            "Task 05G starting stage=%s candidate=%s attempt=%s resume_from=%s",
            operation.__name__,
            run.candidate_id,
            run.attempt,
            run.resume_from,
        )
        try:
            result = operation(run)
        except Exception:
            LOGGER.exception(
                "Task 05G failed stage=%s candidate=%s attempt=%s; preserve the attempt",
                operation.__name__,
                run.candidate_id,
                run.attempt,
            )
            raise
        LOGGER.info("Task 05G completed stage=%s result=%s", operation.__name__, result)


if __name__ == "__main__":
    main()
