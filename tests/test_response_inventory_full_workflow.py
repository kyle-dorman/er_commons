"""Source-free integration tests for the exact Task 05D working workflow."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from er_commons.response_inventory import full_workflow
from er_commons.response_inventory.acceptance import publish_task05d_acceptance
from er_commons.response_inventory.observations import LineObservation, PageObservation
from er_commons.response_inventory.qualification import qualification_observation_digest

REPOSITORY_ROOT = Path(__file__).parents[1]
CONFIG_PATH = REPOSITORY_ROOT / "configs/brisbane_baylands_2025_feir_task05d_complete_v2.json"


def test_full_workflow_is_review_gated_completion_last_and_receipt_reused(
    tmp_path: Path, monkeypatch: object
) -> None:
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    reader_calls: list[tuple[int, int]] = []
    qualifier_calls = 0

    def fake_reader(_path: Path, first: int, last: int) -> list[PageObservation]:
        reader_calls.append((first, last))
        return [_page(page) for page in range(first, last + 1)]

    def fake_qualifier(
        _path: Path, observations: Sequence[PageObservation], cache_root: Path
    ) -> dict[str, object]:
        nonlocal qualifier_calls
        qualifier_calls += 1
        render_root = cache_root / "renders_96dpi"
        render_root.mkdir(parents=True, exist_ok=True)
        pages = []
        for observation in observations:
            render = render_root / f"page-{observation.physical_page:04d}.png"
            render.write_bytes(b"synthetic-png")
            digest = hashlib.sha256(render.read_bytes()).hexdigest()
            pages.append(
                {
                    "physical_page": observation.physical_page,
                    "pdfium_poppler_token_multiset_f1": 1.0,
                    "pdfium_text_sha256": "1" * 64,
                    "poppler_text_sha256": "2" * 64,
                    "render_path": render.relative_to(cache_root).as_posix(),
                    "render_byte_size": render.stat().st_size,
                    "render_sha256": digest,
                    "render_id": "renderv1-" + f"{observation.physical_page:064x}",
                    "review_reasons": [],
                    "fixed_review_page": False,
                    "flagged_for_review": False,
                    "visual_disposition": None,
                }
            )
        return {
            "schema_version": "er_commons.response_inventory.qualification.v2",
            "render_dpi": 96,
            "comparison_threshold": 0.98,
            "observation_digest": qualification_observation_digest(observations),
            "selected_page_count": len(observations),
            "review_page_count": 0,
            "pages": pages,
        }

    monkeypatch.setattr(full_workflow, "verify_repository_bindings", lambda *_args: None)
    monkeypatch.setattr(full_workflow, "_verify_full_artifact_bindings", lambda *_args: None)
    monkeypatch.setattr(full_workflow, "_accepted_signature_baseline", lambda *_args: frozenset())

    first = full_workflow.build_complete_inventory(
        CONFIG_PATH,
        REPOSITORY_ROOT,
        artifact_root,
        page_reader=fake_reader,
        page_qualifier=fake_qualifier,
        tool_versions=_tool_versions(),
    )
    assert reader_calls == [(1, 744)]
    assert qualifier_calls == 1
    assert first["status"] == "review_required"
    candidate_root = Path(first["candidate_root"])
    assert not (candidate_root / "records/stage_completion.json").exists()
    source_runtime_path = Path(first["review_packet"]).parent / "source_pass_runtime.json"
    assert source_runtime_path.is_file()

    report = json.loads(Path(first["review_packet"]).read_text())
    decisions = {
        int(row["physical_page"]): {
            "status": "accepted",
            "reviewer": "source-free-test",
            "reason": "synthetic evidence accepted",
            "evidence_id": row["render_id"],
        }
        for row in report["pages"]
        if row["review_reasons"]
    }
    reader_calls.clear()
    second = full_workflow.build_complete_inventory(
        CONFIG_PATH,
        REPOSITORY_ROOT,
        artifact_root,
        page_reader=fake_reader,
        page_qualifier=fake_qualifier,
        visual_dispositions=decisions,
        tool_versions=_tool_versions(),
        completed_at="2026-09-08T12:00:00Z",
    )
    assert reader_calls == []
    assert qualifier_calls == 1
    assert second["reused_ranges"] == 1
    completion_path = candidate_root / "records/stage_completion.json"
    assert completion_path.is_file()
    runtime_path = candidate_root / "diagnostics/runtime_resources.json"
    runtime = json.loads(runtime_path.read_text())
    assert runtime["schema_version"] == "er_commons.response_inventory.runtime_resources.v2"
    assert runtime["elapsed_seconds"] == pytest.approx(
        runtime["source_pass_elapsed_seconds"] + runtime["closure_elapsed_seconds"],
        abs=1e-6,
    )
    assert runtime["maximum_resident_memory_bytes"] == max(
        runtime["source_pass_maximum_resident_memory_bytes"],
        runtime["closure_maximum_resident_memory_bytes"],
    )
    assert runtime["candidate_size_bytes"] == sum(
        path.stat().st_size for path in candidate_root.rglob("*") if path.is_file()
    )
    completion = json.loads(completion_path.read_text())
    assert completion["status"] == "complete_with_warnings"
    assert completion["counts"]["declared_ranges"] == 1
    assert completion["counts"]["emitted_pages"] == 744
    assert completion["counts"]["open_range_boundary_diagnostics"] == 0
    assert completion["counts"]["source_response_heading_absent_diagnostics"] == 1
    assert len(completion["warnings"]) == 1
    assert completion["warnings"][0].startswith("source_response_heading_absent:")
    records_path = candidate_root / "inventory/source_records.jsonl"
    records = [json.loads(line) for line in records_path.read_text().splitlines()]
    assert not any(
        record.get("record_type") == "diagnostic"
        and record.get("code") == "unit_boundary_ambiguous"
        for record in records
    )
    assert any(
        record.get("record_type") == "source_unit" and record.get("official_label") == "Comment B-7"
        for record in records
    )
    assert not any(
        record.get("observed_label") == "Response A-1"
        or record.get("official_label") == "Response A-1"
        for record in records
    )
    acceptance = publish_task05d_acceptance(
        candidate_root,
        artifact_root,
        accepted_by="source-free-test",
        accepted_at="2026-09-09T12:00:00Z",
    )
    assert acceptance["completion_status"] == "complete_with_warnings"
    assert acceptance["accepted_warning_counts"] == {"source_response_heading_absent": 1}


def test_failed_candidate_publication_removes_staging_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate_root = tmp_path / "revisionv1-test"
    payloads = {
        "diagnostics/runtime_resources.json": json.dumps({"candidate_size_bytes": 0}).encode()
    }

    def fail_validation(*_args: object, **_kwargs: object) -> None:
        raise ValueError("synthetic managed-file failure")

    monkeypatch.setattr(full_workflow, "validate_managed_files", fail_validation)
    with pytest.raises(ValueError, match="synthetic managed-file failure"):
        full_workflow._publish_candidate_atomically(  # noqa: SLF001
            candidate_root,
            payloads,
            {"inventory_id": "fileinventoryv1-test"},
            {"completion_id": "completionv1-test"},
        )
    assert not candidate_root.exists()
    assert not list(tmp_path.glob(".revisionv1-test.staging-*"))


def _page(page: int) -> PageObservation:
    styles: dict[int, dict[str, bool]] = {}
    if page == 38:
        text = (
            "General Response 9 maximum building height topic is routed to Chapter 16 in Volume 5."
        )
    elif 39 <= page <= 46:
        number = page - 38
        text = f"13.2.{number} GENERAL RESPONSE {number}: SYNTHETIC TOPIC"
        styles[0] = {"bold": True}
    elif page == 155:
        text = "Comment A-1\nFirst comment.\n"
        styles[0] = {"bold": True, "solid_rule": True}
    elif page == 156:
        text = "Continued first comment.\n"
    elif page == 157:
        text = "Comment A-2\nSecond comment.\nResponse A-2\nSecond response.\n"
        styles[0] = {"bold": True, "solid_rule": True}
        styles[2] = {"italic": True, "dotted_rule": True}
    elif page == 682:
        text = "Comment B-7\nSeventh comment.\nResponse B-7\nSeventh response.\n"
        styles[0] = {"italic": True, "dotted_rule": True}
        styles[2] = {"italic": True, "dotted_rule": True}
    else:
        text = ""
    lines = []
    offset = 0
    for index, value in enumerate(text.splitlines(keepends=True)):
        content = value.rstrip("\r\n")
        end = offset + len(content)
        style = styles.get(index, {})
        lines.append(
            LineObservation(
                line_index=index,
                text_start=offset,
                text_end=end,
                bbox=(72.0, 700.0 - index * 20, 500.0, 714.0 - index * 20),
                character_slot_start=offset,
                character_slot_end=end,
                bold=style.get("bold", False),
                italic=style.get("italic", False),
                solid_rule=style.get("solid_rule", False),
                dotted_rule=style.get("dotted_rule", False),
            )
        )
        offset += len(value)
    return PageObservation(
        physical_page=page,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=tuple(lines),
        section_opener=page == 38,
        closes_open_unit=page == 744,
    )


def _tool_versions() -> dict[str, str]:
    return {"pdftotext": "pdftotext synthetic", "pdftoppm": "pdftoppm synthetic"}
