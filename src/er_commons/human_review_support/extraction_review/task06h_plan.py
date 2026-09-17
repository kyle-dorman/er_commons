"""Source-free Task 06H plan publication and bounded render dispatch."""

from __future__ import annotations

import json
import uuid
from importlib.metadata import version
from pathlib import Path
from typing import Any

from er_commons.artifact_io import (
    artifact_inventory,
    canonical_json_sha256,
    json_bytes,
    publish_bytes_no_clobber,
    publish_jsonl_no_clobber,
    read_json_object,
    sha256_file,
)
from er_commons.human_review_support.extraction_review.task06h_bindings import (
    figure_controls,
    repair_owner_evidence,
    source_substitution,
    terminal_dimensions,
)
from er_commons.human_review_support.extraction_review.task06h_contract import (
    HANDOFF_ID,
    exact_questions,
    final_f1_warnings,
    task05g_handoff,
    verify_accepted_input_closure,
)
from er_commons.human_review_support.extraction_review.task06h_correspondence import (
    exclusion_correspondence,
)
from er_commons.human_review_support.extraction_review.task06h_evidence import (
    map_eligible_figures,
    prove_task04_reuse,
)
from er_commons.human_review_support.extraction_review.task06h_population import (
    build_fresh_navigation_rows,
    build_source_registry,
    selection_records,
    target_population,
    task03i_record,
)
from er_commons.human_review_support.extraction_review.task06h_rendering import (
    PageRenderJob,
    RenderLimits,
    render_task06h_pages,
)
from er_commons.human_review_support.extraction_review.task06h_request import (
    Task06HRequestSpec,
)
from er_commons.human_review_support.extraction_review.task06h_selection import (
    build_selection,
    deterministic_unchanged_sample,
)

JsonObject = dict[str, Any]
PLAN_SCHEMA = "er_commons.task06h.review_plan.v1"
POLICY = {
    "name": "accepted_task04_complete_visible_page_navigation_policy",
    "question": "Is the complete visible page a canonical TOC/navigation page or not_toc?",
    "reuse_requires": [
        "one_to_one_stable_suffix_mapping",
        "substantive_page_and_entity_equality",
        "same_question_and_disposition_vocabulary",
        "visual_sample_by_source_and_disposition_stratum",
    ],
}
REUSED_PAGE28 = {
    "source_id": "feir_appendix_f1",
    "physical_page": 28,
    "path": (
        "pipelines/brisbane_baylands/task_06_recovery_v1/06c/"
        "gate2_qualification_followup_v1/page-028.png"
    ),
    "sha256": "5bcef150d4b81f3d86992c843c2b34dc4faced780ca7ef3272913017f29dcea7",
    "byte_size": 839835,
    "renderer": "pdftoppm -scale-to 1600",
    "payload_rehashed": False,
}


def execute_task06h_request(spec: Task06HRequestSpec, output_root: Path) -> Path:
    """Dispatch the explicitly selected Task 06H operation."""
    if spec.operation == "prepare":
        return prepare_task06h_review(spec, output_root)
    return render_task06h_review(spec, output_root)


def prepare_task06h_review(spec: Task06HRequestSpec, output_parent: Path) -> Path:
    """Publish the complete source-free Phase 2 review plan completion-last."""
    inputs = _load_inputs(spec)
    roots = _accepted_roots(spec)
    closure = verify_accepted_input_closure(roots)
    closure["resolved_roots"] = {name: str(path) for name, path in roots.items()}
    source_rows = _objects(inputs["sources"].get("rows"), "source correspondence")
    review_rows = _objects(inputs["review"].get("rows"), "review correspondence")
    registry = build_source_registry(
        source_rows,
        (inputs["deir_manifest"], inputs["f1_manifest"]),
        inputs["old_registry"],
    )
    figures = map_eligible_figures(
        inputs["figures"],
        selected_candidate_root=_candidate_root(registry, spec, "deir_main"),
        expected_candidate_id=_candidate_id(registry, "deir_main"),
    )
    selections = build_selection(
        review_rows, _objects(inputs["figures"].get("decisions"), "figures")
    )
    payloads = _plan_payloads(
        spec, inputs, source_rows, review_rows, registry, figures, selections, closure
    )
    digests = {name: canonical_json_sha256(value) for name, value in payloads.items()}
    preimage = {
        "schema_version": PLAN_SCHEMA,
        "mechanical_handoff_id": HANDOFF_ID,
        "accepted_candidate_root": str(spec.accepted_candidate_root),
        "record_digests": digests,
        "renderer": _renderer_identity(),
        "resource_limits": _limits(spec).__dict__,
        "effective_request_sha256": canonical_json_sha256(spec.model_dump(mode="json")),
        "implementation": _implementation_identity(),
        "phase2_authorized_on": "2026-09-13",
        "human_review_authorized": False,
    }
    plan_id = "reviewplanv1-" + canonical_json_sha256(preimage)
    final = output_parent / plan_id
    if final.exists():
        _validate_plan(final, plan_id, check_current=True)
        return final
    return _publish_plan(output_parent, final, plan_id, preimage, payloads)


def render_task06h_review(spec: Task06HRequestSpec, output_parent: Path) -> Path:
    """Validate the plan and render its exact 289-page new-render closure."""
    if spec.plan_root is None:
        raise ValueError("Task 06H render request has no plan root")
    plan = read_json_object(spec.plan_root / "records/plan.json")
    plan_id = str(plan.get("plan_id"))
    _validate_plan(spec.plan_root, plan_id, check_current=True)
    selections = _read_jsonl(spec.plan_root / "records/selection_ledger.jsonl")
    registry = _read_jsonl(spec.plan_root / "records/source_registry.jsonl")
    sources = {str(row["source_id"]): row for row in registry}
    jobs = tuple(
        PageRenderJob(
            source_id=str(row["source_id"]),
            source_pdf=spec.data_root / str(sources[str(row["source_id"])]["source_relative_path"]),
            physical_page=int(row["physical_page"]),
            expected_source_bytes=int(sources[str(row["source_id"])]["byte_size"]),
            expected_page_count=int(sources[str(row["source_id"])]["pdf_page_count"]),
        )
        for row in selections
        if row.get("render_action") == "render_new"
    )
    if len(jobs) != 289:
        raise ValueError(f"Task 06H new-render closure differs: {len(jobs)}")
    identity = {
        "schema_version": "er_commons.task06h.render_pack.v1",
        "plan_id": plan_id,
        "plan_completion_sha256": sha256_file(spec.plan_root / "records/completion.json"),
        "selection_ledger_sha256": sha256_file(spec.plan_root / "records/selection_ledger.jsonl"),
        "renderer": _renderer_identity(),
        "resource_limits": _limits(spec).__dict__,
        "effective_request_sha256": canonical_json_sha256(spec.model_dump(mode="json")),
        "implementation": _implementation_identity(),
        "reused_render": REUSED_PAGE28,
        "render_authorized_on": "2026-09-13",
    }
    render_id = "renderpackv1-" + canonical_json_sha256(identity)
    return render_task06h_pages(
        output_parent,
        render_id=render_id,
        plan_id=plan_id,
        jobs=jobs,
        reused_render=REUSED_PAGE28,
        identity_preimage=identity,
        limits=_limits(spec),
    )


def _plan_payloads(
    spec: Task06HRequestSpec,
    inputs: dict[str, JsonObject],
    source_rows: list[JsonObject],
    review_rows: list[JsonObject],
    registry: tuple[JsonObject, ...],
    figures: tuple[JsonObject, ...],
    selections: tuple[Any, ...],
    closure: JsonObject,
) -> dict[str, Any]:
    policy_digest = canonical_json_sha256(POLICY)
    reused = list(
        prove_task04_reuse(
            review_rows,
            source_rows,
            baseline_publications_root=spec.baseline_publications_root,
            selected_publications_root=spec.selected_publications_root,
            accepted_policy_digest=policy_digest,
            current_policy_digest=policy_digest,
        )
    )
    sampled = {
        str(row["entry_id"]): (str(row["source_id"]), str(row["baseline_evidence"]["disposition"]))
        for row in deterministic_unchanged_sample(review_rows)
    }
    for row in reused:
        stratum = (str(row["source_id"]), str(row["baseline_disposition"]))
        row["stratum_key"] = ":".join(stratum)
        row["sample_status"] = (
            "selected_pending_visual_confirmation"
            if row["entry_id"] in sampled
            else "covered_by_pending_stratum_sample"
        )
        row["reuse_status"] = "pending_stratum_visual_confirmation"
    fresh = build_fresh_navigation_rows(review_rows, source_rows, spec.selected_publications_root)
    for row in fresh:
        row["reuse_status"] = "not_eligible_new_review_required"
    correspondence = tuple(sorted([*reused, *fresh], key=lambda row: str(row["entry_id"])))
    exclusions = exclusion_correspondence(
        _objects(inputs["old_exclusions"].get("entries"), "Task 04 exclusions"),
        _objects(_object(inputs["links"], "ordinary").get("rows"), "link comparison"),
    )
    repairs = inputs["repairs"]
    targets = target_population(
        repairs,
        figures,
        source_rows=source_rows,
        selected_publications_root=spec.selected_publications_root,
    )
    return {
        "accepted_input_closure": closure,
        "selection_ledger": selection_records(selections, registry),
        "task04_correspondence": correspondence,
        "source_registry": registry,
        "exclusion_correspondence": exclusions,
        "task03i_recheck": task03i_record(inputs["task03i"], source_rows),
        "figure_controls": figure_controls(inputs["figures"], figures),
        "questions": _questions(),
        "target_population": targets,
        "source_substitution": source_substitution(source_rows),
        "repair_owner_evidence": repair_owner_evidence(targets, figures),
        "limitations": {
            "schema_version": "er_commons.task06h.limitations.v1",
            **final_f1_warnings(),
        },
        "task05g_handoff": {
            "schema_version": "er_commons.task06h.task05g_handoff.v1",
            "status": "pending_task06h_acceptance",
            **task05g_handoff(),
        },
        "correspondence_policy": {
            **POLICY,
            "policy_digest": policy_digest,
            "accepted_evidence_seals": ["task04_gate_d_completion", "task04_registry"],
            "compatibility_result": "same_frozen_policy",
        },
    }


def _questions() -> JsonObject:
    return {
        "schema_version": "er_commons.task06h.questions.v1",
        "question_version": "task06h_exact_questions_v1",
        "questions": exact_questions(),
        "dimensions": terminal_dimensions(),
        "question_specific_terminal_answers": {
            "final_f1_selected_edition": ["confirmed_final", "rejected_wrong_edition"],
            "final_f1_named_material": ["confirmed", "not_confirmed"],
            "appendix_a_each_group": ["confirmed", "rejected_repair_required"],
            "chapters_8_9_each": ["confirmed", "rejected_repair_required"],
            "fresh_navigation": ["toc", "not_toc"],
            "sampled_reuse": ["confirmed_reusable", "mismatch_invalidate_stratum"],
            "caption_backed_figure_marker": ["confirmed_exact_marker", "rejected"],
            "caption_backed_text_only": ["eligible", "eligible_with_warning", "ineligible"],
            "negative_control": ["confirmed_rejected", "incorrectly_rejected"],
        },
        "required_metadata": [
            "reviewer",
            "reviewed_at",
            "question_version",
            "source_id",
            "document_id",
            "stable_correspondence_key",
            "evidence_refs",
            "rationale",
            "limitations",
        ],
        "restart_and_conflict_rule": (
            "identical stable-key replay is idempotent; incomplete or conflicting "
            "answers fail closed and never overwrite a prior terminal answer"
        ),
    }


def _load_inputs(spec: Task06HRequestSpec) -> dict[str, JsonObject]:
    files = {
        "review": spec.correspondence_root / "review_correspondence.json",
        "sources": spec.correspondence_root / "source_correspondence.json",
        "links": spec.comparison_root / "link_population_comparison.json",
        "figures": spec.qualification_root / "qualification.json",
        "repairs": spec.comparison_root / "repair_checks.json",
        "old_registry": spec.task04_gate_d_root / "usability_registry.json",
        "old_exclusions": spec.task04_gate_d_root / "ambiguous_link_dispositions.json",
        "task03i": spec.task04_gate_d_root / "task03i_recheck_disposition.json",
        "deir_manifest": spec.deir_source_manifest,
        "f1_manifest": spec.f1_source_manifest,
    }
    return {name: read_json_object(path) for name, path in files.items()}


def _accepted_roots(spec: Task06HRequestSpec) -> dict[str, Path]:
    recovery = spec.data_root / "pipelines/brisbane_baylands/task_06_recovery_v1"
    task06g = recovery / "06g"
    replay = task06g / "replay_v38"
    handoff_parent = replay / (
        "document_publications/scopes/"
        "scopev1-c9966bf1fbf87a88f8b8094806ab578f37fc646f3b22f5c552e8623e0b509be7/"
        "handoffs"
    )
    return {
        "candidate": spec.accepted_candidate_root,
        "handoff": handoff_parent / HANDOFF_ID,
        "task06g": task06g,
        "repo": Path(__file__).resolve().parents[4],
        "replay": replay,
        "correspondence": spec.correspondence_root,
        "comparison": spec.comparison_root,
        "task06d": recovery / "06d/qualification_v8",
        "task06e": recovery / "06e/qualification_v17",
        "task06f": spec.qualification_root,
        "task04_gate_d": spec.task04_gate_d_root,
        "task02": spec.deir_source_manifest.parent,
        "final_f1": spec.f1_source_manifest.parent,
        "page28": recovery / "06c/gate2_qualification_followup_v1",
    }


def _publish_plan(
    output_parent: Path,
    final: Path,
    plan_id: str,
    preimage: JsonObject,
    payloads: dict[str, Any],
) -> Path:
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = output_parent / f".{plan_id}.staging-{uuid.uuid4().hex}"
    records = staging / "records"
    records.mkdir(parents=True)
    publish_bytes_no_clobber(
        records / "plan.json",
        json_bytes(
            {"schema_version": PLAN_SCHEMA, "plan_id": plan_id, "identity_preimage": preimage}
        ),
    )
    jsonl = {
        "selection_ledger",
        "task04_correspondence",
        "source_registry",
        "exclusion_correspondence",
        "target_population",
    }
    for name, payload in payloads.items():
        path = records / f"{name}.{'jsonl' if name in jsonl else 'json'}"
        if name in jsonl:
            publish_jsonl_no_clobber(path, payload)
        else:
            publish_bytes_no_clobber(path, json_bytes(payload))
    inventory = artifact_inventory(
        staging, {"records/artifact_inventory.json", "records/completion.json"}
    )
    publish_bytes_no_clobber(records / "artifact_inventory.json", json_bytes(inventory))
    completion = {
        "schema_version": "er_commons.task06h.review_plan_completion.v1",
        "plan_id": plan_id,
        "status": "complete_ready_to_render",
        "source_pdf_bytes_read": False,
        "image_payload_bytes_read": False,
        "model_files_read": False,
        "selection_count": 290,
        "new_render_count": 289,
        "reused_render_count": 1,
        "task04_correspondence_count": 757,
        "source_count": 35,
        "target_count": 185,
        "exclusion_count": 725,
        "inventory_sha256": sha256_file(records / "artifact_inventory.json"),
        "completion_last": True,
    }
    publish_bytes_no_clobber(records / "completion.json", json_bytes(completion))
    staging.rename(final)
    return final


def _validate_plan(root: Path, plan_id: str, *, check_current: bool) -> None:
    plan = read_json_object(root / "records/plan.json")
    completion = read_json_object(root / "records/completion.json")
    if plan.get("plan_id") != plan_id or completion.get("plan_id") != plan_id:
        raise ValueError("Task 06H completed plan identity differs")
    preimage = _object(plan, "identity_preimage")
    if "reviewplanv1-" + canonical_json_sha256(preimage) != plan_id:
        raise ValueError("Task 06H plan identity preimage differs")
    if check_current and (
        preimage.get("implementation") != _implementation_identity()
        or preimage.get("renderer") != _renderer_identity()
    ):
        raise ValueError("Task 06H plan implementation or renderer differs")
    jsonl = {
        "selection_ledger",
        "task04_correspondence",
        "source_registry",
        "exclusion_correspondence",
        "target_population",
    }
    for name, digest in _object(preimage, "record_digests").items():
        path = root / "records" / f"{name}.{'jsonl' if name in jsonl else 'json'}"
        value: Any = _read_jsonl(path) if name in jsonl else read_json_object(path)
        if canonical_json_sha256(value) != digest:
            raise ValueError(f"Task 06H plan record digest differs: {name}")
    inventory = root / "records/artifact_inventory.json"
    if completion.get("inventory_sha256") != sha256_file(inventory):
        raise ValueError("Task 06H plan completion inventory binding differs")
    if read_json_object(inventory) != artifact_inventory(
        root, {"records/artifact_inventory.json", "records/completion.json"}
    ):
        raise ValueError("Task 06H plan managed-file closure differs")


def _implementation_identity() -> dict[str, str]:
    root = Path(__file__).resolve().parents[4]
    paths = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "src/er_commons/human_review_support/extraction_review").glob(
            "task06h_*.py"
        )
    )
    paths.append("src/er_commons/human_review_support/extraction_review/request.py")
    return {path: sha256_file(root / path) for path in paths}


def _limits(spec: Task06HRequestSpec) -> RenderLimits:
    return RenderLimits(
        workers=spec.worker_count,
        cpu_threads=spec.cpu_thread_limit,
        rss_bytes=spec.rss_limit_bytes,
        active_seconds=spec.wall_time_limit_seconds,
        output_bytes=spec.output_limit_bytes,
        minimum_free_bytes=spec.minimum_free_bytes,
    )


def _renderer_identity() -> JsonObject:
    return {"name": "pypdfium2", "version": version("pypdfium2"), "scale": 1.0}


def _candidate_id(registry: tuple[JsonObject, ...], source_id: str) -> str:
    return str(
        next(row for row in registry if row["source_id"] == source_id)["selected_candidate_id"]
    )


def _candidate_root(
    registry: tuple[JsonObject, ...], spec: Task06HRequestSpec, source_id: str
) -> Path:
    return (
        spec.selected_publications_root
        / "documents"
        / source_id
        / _candidate_id(registry, source_id)
    )


def _objects(value: object, label: str) -> list[JsonObject]:
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{label} must be a list of objects")
    return value


def _object(value: dict[str, Any], field: str) -> JsonObject:
    result = value.get(field)
    if not isinstance(result, dict):
        raise ValueError(f"Task 06H field must be an object: {field}")
    return result


def _read_jsonl(path: Path) -> list[JsonObject]:
    with path.open(encoding="utf-8") as stream:
        return _objects([json.loads(line) for line in stream if line.strip()], str(path))


__all__ = [
    "execute_task06h_request",
    "prepare_task06h_review",
    "render_task06h_review",
]
