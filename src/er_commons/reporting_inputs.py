"""Verify and replay the sealed Task 11E development observations without calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from er_commons import development_evaluation as evaluation
from er_commons.artifact_io import sha256_bytes, stable_json_sha256
from er_commons.context_comparison import delivery
from er_commons.reporting_counts import citation_complexity


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject ambiguous JSON keys in provenance and observations."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(content: bytes) -> Any:
    """Parse exact verified bytes with duplicate protection."""
    return json.loads(content, object_pairs_hook=_unique)


class SealedInputs:
    """Read only explicitly selected files bound by the accepted completion."""

    def __init__(self, root: Path, seal: dict[str, Any]) -> None:
        """Index the seal once and reject duplicate or escaping paths."""
        self.root = root.resolve()
        self.files: dict[str, Any] = {}
        self.consumed: dict[str, Any] = {}
        for row in seal["files"]:
            name = row["path"]
            if name in self.files or not (self.root / name).resolve().is_relative_to(self.root):
                raise ValueError(f"Duplicate or escaping sealed path: {name}")
            self.files[name] = row

    def read(self, relative: str) -> bytes:
        """Fail closed on missing, changed or unsealed bytes without broad traversal."""
        if relative not in self.files:
            raise ValueError(f"Unsealed input: {relative}")
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f"Escaping input: {relative}")
        content = _verified(path, self.files[relative])
        self.consumed[relative] = self.files[relative]
        return content

    def json(self, relative: str) -> Any:
        """Deserialize a checksum-verified input."""
        return _json(self.read(relative))


def _verified(path: Path, binding: dict[str, Any]) -> bytes:
    """Check both byte count and digest before parsing."""
    content = path.read_bytes()
    if sha256_bytes(content) != binding["sha256"] or len(content) != binding["byte_size"]:
        raise ValueError(f"Sealed input mismatch: {path}")
    return content


def _same(actual: Any, expected: Any, label: str) -> None:
    """Compare JSON-normalized structures to tolerate persisted tuple/list conversion."""
    if json.loads(json.dumps(actual)) != expected:
        raise ValueError(f"Replay mismatch: {label}")


def _load_observation(
    sealed: SealedInputs,
    slot: dict[str, Any],
    data: dict[str, Any],
    frozen: dict[str, Any],
    preflight: dict[str, Any],
) -> dict[str, Any]:
    """Recompute one exact candidate and its raw judgments using pure evaluator functions."""
    relative = (
        f"observations/{slot['arm']}/{slot['model']}_repeat{slot['repeat']}/{slot['case_id']}"
    )
    summary = sealed.json(f"{relative}/summary.json")
    manifest = sealed.json(f"{relative}/manifest.json")
    identity = {**slot, "run_id": stable_json_sha256({"slot": slot, "preflight": preflight})}
    _same(manifest, identity, "slot manifest")
    _same({key: summary[key] for key in identity}, identity, "slot summary")
    group = next(
        name for name, cases in frozen["exposure_groups"].items() if slot["case_id"] in cases
    )
    result: dict[str, Any] = {
        **slot,
        "model_id": frozen["targets"][slot["model"]]["model"],
        "exposure_group": group,
        "source_path": relative,
        "status": summary["status"],
        "identity": identity,
        "candidate": None,
        "plan": None,
        "report": None,
        "judgments": [],
        "complexity": None,
    }
    if summary["status"] != "completed":
        # Preserve the planned slot even if a future accepted run records non-dispatch.
        result["unavailable_reason"] = summary.get("reason", summary["status"])
        return result
    generation = sealed.json(f"{relative}/generation/result.json")
    if (
        any(generation[key] != identity[key] for key in ("case_id", "repeat", "run_id"))
        or generation["model"] != result["model_id"]
        or generation["returned_model"] != result["model_id"]
        or generation["status"] != "valid"
    ):
        raise ValueError("Cross-slot generation identity or model mismatch")
    candidate = sealed.read(f"{relative}/generation/candidate.json")
    native_bytes = sealed.read(f"{relative}/generation/native_request.json")
    if sha256_bytes(native_bytes) != generation["request_sha256"]:
        raise ValueError("Native generation request mismatch")
    actual_delivery = delivery(_json(native_bytes), generation["provider"])
    _same(
        actual_delivery, sealed.json(f"{relative}/generation/delivery_projection.json"), "delivery"
    )
    _same(sealed.json(f"{relative}/mapping.json"), data["mapping"], "mapping")
    _same(sealed.json(f"{relative}/generation/packet.json"), data["record"], "packet")
    plan = evaluation.prepare_candidate(
        candidate,
        generation,
        data["record"],
        data["mapping"],
        actual_delivery,
        data["reference"],
    )
    _same(plan, sealed.json(f"{relative}/plan.json"), "plan")
    judgments = sealed.json(f"{relative}/judgments.json")
    for judgment in judgments:
        component = judgment["component"]
        judge_model = frozen["targets"]["haiku" if component == "S" else "luna"]["model"]
        if judgment["model"] != judge_model or judgment["returned_model"] != judge_model:
            raise ValueError("Frozen judge model mismatch")
        directory = f"{relative}/judgments/{judgment['sample_id']}"
        _same(judgment, sealed.json(f"{directory}/judgment.json"), "raw judgment")
        item = next((i for i in plan["items"] if i["sample_id"] == judgment["sample_id"]), None)
        if item is None:
            raise ValueError("Orphan judgment")
        _same(item, sealed.json(f"{directory}/item.json"), "judgment item")
        context = sealed.json(f"{directory}/context_envelope.json")
        expected_context_id = stable_json_sha256(
            {k: v for k, v in context.items() if k != "context_id"}
        )
        if (
            context["context_id"] != expected_context_id
            or judgment["context_id"] != expected_context_id
            or context["parent_sample_id"] != judgment["sample_id"]
            or stable_json_sha256(context["prompt"])
            != frozen["effective_prompts_sha256"][slot["arm"]]["judges"][component]
        ):
            raise ValueError("Frozen judge context mismatch")
        _same(context["payload"], item["packet"], "independent judge payload")
    report = evaluation.build_report(plan, judgments)
    _same(report, sealed.json(f"{relative}/report.json"), "report")
    if not report["coverage_complete"]:
        raise ValueError("Completed observation has incomplete evaluation coverage")
    result.update(
        identity=plan["identity"],
        candidate=_json(candidate),
        plan=plan,
        report=report,
        judgments=judgments,
        complexity=citation_complexity(report["automatic"], data["mapping"]),
    )
    return result


def load_development(repo: Path, data_root: Path) -> dict[str, Any]:
    """Replay all declared 11E slots, reading only sealed development inputs and outputs."""
    pointer_path = repo / "docs/specs/task11e_result.json"
    pointer_bytes = pointer_path.read_bytes()
    pointer = _json(pointer_bytes)
    namespace = pointer["namespace"]
    root = (data_root / namespace).resolve()
    if not root.is_relative_to(data_root.resolve()):
        raise ValueError("Escaping development namespace")
    completion_name = f"{namespace}/completion.json"
    completion_bytes = _verified(root / "completion.json", pointer["artifacts"][completion_name])
    sealed = SealedInputs(root, _json(completion_bytes))
    binding = pointer["frozen_configuration"]
    frozen_bytes = _verified(repo / binding["path"], binding)
    frozen = _json(frozen_bytes)
    if sealed.read("frozen_configuration.json") != frozen_bytes:
        raise ValueError("Frozen configuration differs from accepted copy")
    preflight = sealed.json("preflight.json")
    for name, digest in frozen["input_files_sha256"].items():
        if sha256_bytes(sealed.read(name)) != digest:
            raise ValueError("Frozen source binding mismatch")
    data = sealed.json("inputs.json")
    if stable_json_sha256(data) != frozen["source_sha256"]:
        raise ValueError("Frozen development source mismatch")
    cases = pointer["case_ids"]
    groups = frozen["exposure_groups"]
    if (
        len(cases) != len(set(cases))
        or set(data) != set(cases)
        or set(groups["fixed_six"]) & set(groups["remaining_thirteen"])
        or set(groups["fixed_six"] + groups["remaining_thirteen"]) != set(cases)
        or pointer["repeats_per_model_question"] != 3
    ):
        raise ValueError("Invalid development case/exposure/repeat inventory")
    expected = {
        (model, repeat, case)
        for model in frozen["targets"]
        for repeat in (1, 2, 3)
        for case in cases
    }
    slots = preflight["slots"]
    keys = [(s["model"], s["repeat"], s["case_id"]) for s in slots]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError("Duplicate, missing or unexpected planned slots")
    rows = [
        _load_observation(sealed, slot, data[slot["case_id"]], frozen, preflight) for slot in slots
    ]
    # Reuse accepted review records as provenance; do not relabel or override scores.
    reviews = {
        name: sealed.json(name)
        for name in (
            "independent_audit_result.json",
            "source_report_review.json",
            "publication_review.json",
            "manual_haiku_summary.json",
        )
    }
    provenance = [
        {
            "path": "docs/specs/task11e_result.json",
            "root": "repo",
            "sha256": sha256_bytes(pointer_bytes),
            "byte_size": len(pointer_bytes),
        },
        {**binding, "root": "repo"},
        {"path": completion_name, "root": "data", **pointer["artifacts"][completion_name]},
        *[
            {**entry, "path": f"{namespace}/{name}", "root": "data"}
            for name, entry in sorted(sealed.consumed.items())
        ],
    ]
    return {
        "rows": rows,
        "provenance": provenance,
        "frozen_configuration": frozen,
        "source_result": pointer,
        "accepted_reviews": reviews,
        "replay": {
            "planned_answers": len(rows),
            "recomputed_answers": sum(r["report"] is not None for r in rows),
            "new_calls": 0,
        },
    }
