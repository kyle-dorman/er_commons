"""Build the corrected Task 03J final-pass reviewer after Gate C approval."""

from __future__ import annotations

import logging
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.artifact_io import canonical_json_sha256, json_bytes
from er_commons.human_review_support.task04.application import build_presentation
from er_commons.human_review_support.task04.canonical_evidence import page_review_evidence
from er_commons.human_review_support.task04.discovery import DiscoveredInputs
from er_commons.human_review_support.task04.final_inputs import discover_task03j_inputs
from er_commons.human_review_support.task04.json_io import (
    read_json_object,
    require_integer,
    require_list,
    require_mapping,
    require_string,
)
from er_commons.human_review_support.task04.models import (
    JsonObject,
    JsonValue,
    ReviewItem,
    ReviewQueue,
)
from er_commons.human_review_support.task04.presentation import write_review_html
from er_commons.human_review_support.task04.records import RecordValidator
from er_commons.human_review_support.task04.rendering import PageRenderer, PdfiumPageRenderer
from er_commons.human_review_support.task04.selection import SelectionResult, build_selection
from er_commons.human_review_support.task04.toc_decisions import (
    decision_record,
    discover_prior_toc_decisions,
    load_toc_decisions,
)
from er_commons.human_review_support.task04.toc_models import (
    PageKey,
    TocDisposition,
    parse_toc_censuses,
)
from er_commons.human_review_support.task04.toc_page_shapes import (
    decided_not_toc_run_suffixes,
)
from er_commons.human_review_support.task04.toc_review_selection import (
    PositiveTocSelection,
    TocSelection,
    basic_project_information_pages,
    build_positive_toc_items,
    build_toc_review_selection,
    intentional_blank_pages,
    navigation_continuation_pages,
    obvious_navigation_heading_pages,
    recognized_toc_run_suffixes,
)
from er_commons.human_review_support.task04.toc_table_filters import full_page_table_pages

LOGGER = logging.getLogger(__name__)
FINAL_REVIEW_RUN_ID = "reviewv1-task03j-final-c17"
FINAL_REVIEW_SCHEMA_VERSION = "er_commons.task04a_review.v1.gate_c_execution"


@dataclass(frozen=True)
class _ReviewPlan:
    """All deterministic selections and records prepared before rendering."""

    items: tuple[ReviewItem, ...]
    base: SelectionResult
    toc: TocSelection
    positives: PositiveTocSelection
    decisions: dict[str, TocDisposition]
    finding_recheck: dict[str, Any]


@dataclass(frozen=True)
class _CensusCounts:
    """Gate B census totals needed by the compact Gate C manifest."""

    candidate_pages: int
    ambiguous_aliases: int
    ambiguous_links: int

    @classmethod
    def from_gate_a(cls, gate_a: JsonObject) -> _CensusCounts:
        """Validate and count the three populations used by Gate C."""
        records = require_list(
            gate_a.get("toc_candidate_census"), path="gate_a.toc_candidate_census"
        )
        candidate_pages = 0
        ambiguous_aliases = 0
        ambiguous_links = 0
        for index, value in enumerate(records):
            path = f"gate_a.toc_candidate_census[{index}]"
            census = require_mapping(value, path=path)
            candidate_pages += len(
                require_list(census.get("candidate_pages"), path=f"{path}.candidate_pages")
            )
            ambiguous_aliases += len(
                require_list(
                    census.get("ambiguous_toc_aliases"), path=f"{path}.ambiguous_toc_aliases"
                )
            )
            ambiguous_links += len(
                require_list(
                    census.get("ambiguous_reference_links"),
                    path=f"{path}.ambiguous_reference_links",
                )
            )
        return cls(candidate_pages, ambiguous_aliases, ambiguous_links)


def build_task03j_final_review(
    data_root: Path,
    gate_a_path: Path,
    output_root: Path,
    *,
    renderer: PageRenderer | None = None,
    toc_decisions_path: Path | None = None,
) -> Path:
    """Publish the six-queue final reviewer without rehashing large files."""
    gate_a = read_json_object(gate_a_path)
    _require_gate_a(gate_a)
    if output_root.exists():
        raise FileExistsError(f"final review output already exists: {output_root}")
    staging = output_root.parent / f".{output_root.name}.staging"
    if staging.exists():
        raise FileExistsError(f"staging output already exists: {staging}")
    staging.mkdir(parents=True)
    try:
        inputs = discover_task03j_inputs(data_root)
        plan = _build_review_plan(
            data_root,
            inputs,
            gate_a,
            output_root.parent,
            toc_decisions_path,
        )
        active_renderer = renderer or PdfiumPageRenderer(scale=1.0)
        cards, generated = build_presentation(
            staging, inputs, plan.items, active_renderer, page_review_evidence
        )
        html_files = write_review_html(
            staging / "html",
            cards,
            "Task 03J final review",
            plan.decisions,
            review_run_id=FINAL_REVIEW_RUN_ID,
        )
        selection = _selection_record(
            plan.items,
            plan.base.populations,
            plan.toc.population,
            plan.positives.population,
        )
        toc_register = _toc_register(plan.toc.items, plan.decisions)
        _write_review_records(staging, selection, toc_register, plan)
        manifest = _execution_record(
            gate_a,
            inputs,
            plan.items,
            generated,
            html_files,
            selection,
            toc_register,
            plan.finding_recheck,
            active_renderer,
        )
        schema_root = Path(__file__).parents[4] / "benchmarks/er_bench/schemas/task04a_review/v1"
        RecordValidator(schema_root).validate("gate_c_execution", manifest)
        _write_json(staging / "records/gate_c_execution.json", manifest)
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    LOGGER.info("published corrected Task 03J reviewer at %s", output_root)
    return output_root


def _build_review_plan(
    data_root: Path,
    inputs: DiscoveredInputs,
    gate_a: JsonObject,
    review_parent: Path,
    explicit_decisions_path: Path | None,
) -> _ReviewPlan:
    """Resolve decisions and selections before any rendering side effects."""
    policy_sha256 = str(gate_a["policy_sha256"])
    decisions, excluded_positive_pages = _prepare_toc_decisions(
        inputs, gate_a, review_parent, explicit_decisions_path
    )
    base = build_selection(inputs, data_root, FINAL_REVIEW_RUN_ID, policy_sha256)
    toc, positives = _build_toc_selections(
        inputs, gate_a, policy_sha256, decisions, excluded_positive_pages
    )
    recheck_items, finding_recheck = _finding_recheck_items(
        data_root, inputs.candidates, policy_sha256
    )
    return _ReviewPlan(
        items=(*base.items, *recheck_items, *toc.items, *positives.items),
        base=base,
        toc=toc,
        positives=positives,
        decisions=decisions,
        finding_recheck=finding_recheck,
    )


def _prepare_toc_decisions(
    inputs: DiscoveredInputs,
    gate_a: JsonObject,
    review_parent: Path,
    explicit_path: Path | None,
) -> tuple[dict[str, TocDisposition], set[PageKey]]:
    """Load human labels and expand known false-positive run suffixes."""
    prior_path = explicit_path or discover_prior_toc_decisions(review_parent)
    decisions = load_toc_decisions(prior_path)
    census = gate_a["toc_candidate_census"]
    _require_known_decisions(census, decisions)
    boundaries = basic_project_information_pages(inputs.candidates)
    basic_pages, basic_entries = recognized_toc_run_suffixes(census, boundaries)
    _merge_auto_false_positive_decisions(decisions, basic_entries)
    _, decided_entries = decided_not_toc_run_suffixes(census, decisions)
    _merge_auto_false_positive_decisions(decisions, decided_entries)
    return decisions, basic_pages


def _build_toc_selections(
    inputs: DiscoveredInputs,
    gate_a: JsonObject,
    policy_sha256: str,
    decisions: dict[str, TocDisposition],
    auto_false_positive_pages: set[PageKey],
) -> tuple[TocSelection, PositiveTocSelection]:
    """Build false-negative and false-positive TOC review queues."""
    census = gate_a["toc_candidate_census"]
    toc = build_toc_review_selection(
        census,
        FINAL_REVIEW_RUN_ID,
        policy_sha256,
        full_page_table_pages=full_page_table_pages(inputs.candidates),
        prior_decisions=decisions,
    )
    positives = build_positive_toc_items(
        census,
        FINAL_REVIEW_RUN_ID,
        policy_sha256,
        excluded_heading_pages=obvious_navigation_heading_pages(inputs.candidates),
        navigation_shaped_pages=navigation_continuation_pages(inputs.candidates),
        excluded_review_pages=intentional_blank_pages(inputs.candidates),
        auto_false_positive_pages=auto_false_positive_pages,
    )
    return toc, positives


def _merge_auto_false_positive_decisions(
    decisions: dict[str, TocDisposition], auto_entry_ids: set[str]
) -> None:
    """Add deterministic false positives without overwriting contrary human labels."""
    conflicts = sorted(entry_id for entry_id in auto_entry_ids if decisions.get(entry_id) == "toc")
    if conflicts:
        raise ValueError(
            "Basic Project Information auto-rejection conflicts with human TOC decisions: "
            f"{conflicts}"
        )
    decisions.update(dict.fromkeys(auto_entry_ids, "not_toc"))


def _require_known_decisions(censuses: object, decisions: dict[str, TocDisposition]) -> None:
    """Reject imported decisions that cannot be mapped to the frozen census."""
    known = {page.entry_id for census in parse_toc_censuses(censuses) for page in census.pages}
    unknown = decisions.keys() - known
    if unknown:
        raise ValueError(f"TOC decisions are absent from the frozen census: {sorted(unknown)}")


def _require_gate_a(record: JsonObject) -> None:
    """Require the approved complete Gate B census."""
    if record.get("pass") != "task03j_final" or record.get("status") != "source_free_prepared":
        raise ValueError("Gate C requires the task03j_final Gate A record")
    census = record.get("toc_candidate_census")
    if not isinstance(census, list) or len(census) != 35:
        raise ValueError("Gate C requires the complete 35-source Gate B census")


def _finding_recheck_items(
    data_root: Path, candidates: dict[str, Path], policy_sha256: str
) -> tuple[tuple[ReviewItem, ...], dict[str, Any]]:
    """Make fresh valid-page cards for the accepted Task 03I finding."""
    path = data_root / (
        "pipelines/brisbane_baylands/task_04_review/"
        "reviewv1-task03h-first-7e8e89a40907adba/records/finding_register.json"
    )
    register = read_json_object(path)
    findings = register.get("findings")
    if not isinstance(findings, list) or len(findings) != 1:
        raise ValueError("expected exactly one accepted Task 03I finding")
    finding = require_mapping(findings[0], path=f"{path}:$.findings[0]")
    evidence = require_mapping(finding.get("evidence"), path=f"{path}:$.findings[0].evidence")
    source_id = require_string(
        evidence.get("source_id"), path=f"{path}:$.findings[0].evidence.source_id"
    )
    raw_pages = require_list(
        evidence.get("physical_pages"),
        path=f"{path}:$.findings[0].evidence.physical_pages",
    )
    pages = tuple(
        sorted(
            require_integer(page, path=f"{path}:$.findings[0].evidence.physical_pages[]", minimum=1)
            for page in raw_pages
        )
    )
    candidate_id = candidates[source_id].name
    items = tuple(
        ReviewItem(
            ReviewQueue.VALID_PAGE,
            f"{FINAL_REVIEW_RUN_ID}/finding-recheck/{source_id}/p{page:05d}",
            source_id,
            candidate_id,
            (page,),
            ("task03i_finding_recheck",),
            {"finding_recheck": True, "policy_sha256": policy_sha256},
        )
        for page in pages
    )
    record = {
        "schema_version": "er_commons.task04a_review.v1.task03i_finding_recheck",
        "review_run_id": FINAL_REVIEW_RUN_ID,
        "status": "machine_evidence_bound_pending_human_confirmation",
        "finding_id": require_string(
            finding.get("finding_id"), path=f"{path}:$.findings[0].finding_id"
        ),
        "source_id": source_id,
        "physical_pages": list(pages),
        "task03j_review_item_ids": [item.review_item_id for item in items],
    }
    return items, record


def _selection_record(
    items: tuple[ReviewItem, ...],
    populations: dict[str, int],
    toc: dict[str, int],
    positive_toc: dict[str, int],
) -> dict[str, Any]:
    """Record exact queue selections and bounded population accounting."""
    return {
        "schema_version": "er_commons.task04a_review.v1.selection_manifest",
        "review_run_id": FINAL_REVIEW_RUN_ID,
        "pass": "task03j_final",
        "queue_counts": dict(Counter(item.queue.value for item in items)),
        "base_populations": populations,
        "toc_population": toc,
        "positive_toc_population": positive_toc,
        "items": [item.to_record() for item in items],
    }


def _toc_register(
    items: tuple[ReviewItem, ...], decisions: dict[str, TocDisposition]
) -> dict[str, Any]:
    """Create the visible TOC register with imported decisions retained."""
    return {
        "schema_version": "er_commons.task04a_toc_review_register.v1",
        "review_run_id": FINAL_REVIEW_RUN_ID,
        "status": "pending_human_review",
        "entries": [
            {
                "entry_id": str(item.population["candidate_page_id"]),
                "source_id": item.source_id,
                "physical_page": item.physical_pages[0],
                "disposition": decisions.get(str(item.population["candidate_page_id"])),
            }
            for item in items
        ],
    }


def _execution_record(
    gate_a: JsonObject,
    inputs: DiscoveredInputs,
    items: tuple[ReviewItem, ...],
    generated: tuple[Path, ...],
    html_files: tuple[Path, ...],
    selection: dict[str, Any],
    toc_register: dict[str, Any],
    finding: dict[str, Any],
    renderer: PageRenderer,
) -> dict[str, Any]:
    """Assemble the schema-validated corrected Gate C execution record."""
    census_counts = _CensusCounts.from_gate_a(gate_a)
    gate_inputs = require_mapping(gate_a.get("inputs"), path="gate_a.inputs")
    task03j = require_mapping(gate_inputs.get("task03j"), path="gate_a.inputs.task03j")
    return {
        "schema_version": FINAL_REVIEW_SCHEMA_VERSION,
        "review_run_id": FINAL_REVIEW_RUN_ID,
        "pass": "task03j_final",
        "status": "machine_generation_complete_human_review_pending",
        "source_count": len(inputs.sources),
        "candidate_page_count": census_counts.candidate_pages,
        "rendered_page_count": len(generated),
        "gate_a_preparation_review_run_id": str(gate_a["review_run_id"]),
        "task03j_production_extraction_id": require_string(
            task03j.get("production_extraction_id"),
            path="gate_a.inputs.task03j.production_extraction_id",
        ),
        "ambiguous_toc_alias_count": census_counts.ambiguous_aliases,
        "ambiguous_reference_link_count": census_counts.ambiguous_links,
        "human_register_entry_count": len(toc_register["entries"]),
        "human_review_status": "pending",
        "task03i_finding_recheck_status": finding["status"],
        "source_reads": [],
        "renderer": {
            "name": renderer.name,
            "version": renderer.version,
            "scale": renderer.scale,
        },
        "html_files": [path.name for path in html_files],
        "selection_manifest": {
            "queue_counts": selection["queue_counts"],
            "review_item_count": len(items),
            "toc_policy": ("exclude_recognized_and_controls_then_review_each_full_page_table_run"),
        },
        "large_file_hashing": "not_recomputed_mvp;sealed_upstream_checksums_retained",
        "register_sha256": canonical_json_sha256(toc_register),
    }


def _write_review_records(
    staging: Path,
    selection: dict[str, Any],
    toc_register: dict[str, Any],
    plan: _ReviewPlan,
) -> None:
    """Write compact review records together before the execution manifest."""
    records = staging / "records"
    _write_json(records / "selection_manifest.json", selection)
    _write_json(records / "toc_review_register.json", toc_register)
    _write_json(
        records / "toc_review_decisions.json",
        decision_record(FINAL_REVIEW_RUN_ID, plan.decisions),
    )
    _write_json(records / "task03i_finding_recheck.json", plan.finding_recheck)


def _write_json(path: Path, value: JsonValue) -> None:
    """Write one deterministic JSON record beneath staging."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


__all__ = ["FINAL_REVIEW_RUN_ID", "build_task03j_final_review"]
