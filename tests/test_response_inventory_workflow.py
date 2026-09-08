"""Source-free integration tests for the bounded Task 05C workflow."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

from er_commons.artifact_io import json_bytes
from er_commons.response_inventory.code_inventory import owned_code_digest
from er_commons.response_inventory.observations import LineObservation, PageObservation
from er_commons.response_inventory.pilot_policy import TASK05C_PILOT_RANGES
from er_commons.response_inventory.qualification import qualification_observation_digest
from er_commons.response_inventory.workflow import _apply_range_boundary_policy, build_pilot

REPOSITORY_ROOT = Path(__file__).parents[1]


def test_only_declared_censored_range_remains_open() -> None:
    ordinary = _apply_range_boundary_policy([_fake_page(page) for page in range(1, 6)], (1, 5))
    censored = _apply_range_boundary_policy(
        [_fake_page(page) for page in range(368, 373)], (368, 372)
    )
    assert ordinary[-1].closes_open_unit is True
    assert censored[-1].closes_open_unit is False


def test_build_is_completion_last_and_reuses_exact_range_receipts(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    run_spec_path = tmp_path / "run_spec.json"
    _write_bound_inputs(artifact_root)
    _write_run_spec(run_spec_path, artifact_root)
    calls: list[tuple[int, int]] = []

    def fake_reader(_path: Path, first: int, last: int) -> list[PageObservation]:
        calls.append((first, last))
        return [_fake_page(page) for page in range(first, last + 1)]

    first = build_pilot(
        run_spec_path,
        REPOSITORY_ROOT,
        artifact_root,
        page_reader=fake_reader,
        page_qualifier=_fake_qualifier,
        visual_dispositions=_accepted_review_dispositions(),
        tool_versions=_fake_tool_versions(),
        completed_at="2026-09-08T12:00:00Z",
    )
    assert calls == list(TASK05C_PILOT_RANGES)
    pilot_root = Path(first["pilot_root"])
    assert (pilot_root / "records/stage_completion.json").is_file()
    assert (pilot_root / "records/managed_file_inventory.json").is_file()
    completion = json.loads((pilot_root / "records/stage_completion.json").read_text())
    assert completion["counts"]["declared_ranges"] == 14
    assert completion["counts"]["emitted_pages"] == 89
    assert completion["counts"]["placement_exceptions"] == 1

    calls.clear()
    second = build_pilot(
        run_spec_path,
        REPOSITORY_ROOT,
        artifact_root,
        page_reader=fake_reader,
        page_qualifier=_fake_qualifier,
        visual_dispositions=_accepted_review_dispositions(),
        tool_versions=_fake_tool_versions(),
        completed_at="2026-09-08T13:00:00Z",
    )
    assert calls == []
    assert second["completion_id"] == first["completion_id"]
    assert second["semantic_digest"] == first["semantic_digest"]
    assert second["reused_ranges"] == 14


def test_interrupted_build_reuses_closed_ranges(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    run_spec_path = tmp_path / "run_spec.json"
    _write_bound_inputs(artifact_root)
    _write_run_spec(run_spec_path, artifact_root)
    calls: list[tuple[int, int]] = []

    def interrupting_reader(_path: Path, first: int, last: int) -> list[PageObservation]:
        calls.append((first, last))
        if (first, last) == TASK05C_PILOT_RANGES[2]:
            raise RuntimeError("simulated interruption")
        return [_fake_page(page) for page in range(first, last + 1)]

    try:
        build_pilot(
            run_spec_path,
            REPOSITORY_ROOT,
            artifact_root,
            page_reader=interrupting_reader,
            page_qualifier=_fake_qualifier,
            tool_versions=_fake_tool_versions(),
        )
    except RuntimeError as error:
        assert "simulated interruption" in str(error)
    else:  # pragma: no cover - failure branch
        raise AssertionError("simulated interruption should escape")
    assert calls == list(TASK05C_PILOT_RANGES[:3])
    failed_key = "000031-000044"
    cache_receipts = list(
        (artifact_root / "pipelines/task05c-test/working/05c/cache").glob(
            f"*/ranges/{failed_key}/receipt.json"
        )
    )
    assert len(cache_receipts) == 1
    failed_receipt = json.loads(cache_receipts[0].read_text())
    assert failed_receipt["status"] == "failed"
    assert failed_receipt["failure"] == "RuntimeError: simulated interruption"

    calls.clear()

    def resumed_reader(_path: Path, first: int, last: int) -> list[PageObservation]:
        calls.append((first, last))
        return [_fake_page(page) for page in range(first, last + 1)]

    result = build_pilot(
        run_spec_path,
        REPOSITORY_ROOT,
        artifact_root,
        page_reader=resumed_reader,
        page_qualifier=_fake_qualifier,
        visual_dispositions=_accepted_review_dispositions(),
        tool_versions=_fake_tool_versions(),
        completed_at="2026-09-08T12:00:00Z",
    )
    assert calls == list(TASK05C_PILOT_RANGES[2:])
    assert result["reused_ranges"] == 2


def test_visual_review_packet_is_nonterminal(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    run_spec_path = tmp_path / "run_spec.json"
    _write_bound_inputs(artifact_root)
    _write_run_spec(run_spec_path, artifact_root)

    def fake_reader(_path: Path, first: int, last: int) -> list[PageObservation]:
        return [_fake_page(page) for page in range(first, last + 1)]

    qualification_calls = 0

    def review_qualifier(
        _pdf_path: Path, observations: Sequence[PageObservation], cache_root: Path
    ) -> dict[str, object]:
        nonlocal qualification_calls
        qualification_calls += 1
        pages = _qualification_pages(observations, cache_root)
        return {
            "schema_version": "er_commons.response_inventory.qualification.v1",
            "render_dpi": 96,
            "comparison_threshold": 0.98,
            "observation_digest": qualification_observation_digest(observations),
            "selected_page_count": len(observations),
            "review_page_count": sum(
                bool(item["fixed_review_page"]) or bool(item["flagged_for_review"])
                for item in pages
            ),
            "pages": pages,
        }

    result = build_pilot(
        run_spec_path,
        REPOSITORY_ROOT,
        artifact_root,
        page_reader=fake_reader,
        page_qualifier=review_qualifier,
        tool_versions=_fake_tool_versions(),
    )
    assert result["status"] == "review_required"
    assert result["unresolved_review_pages"] == sorted(_fixed_review_pages())
    pilot_root = Path(result["pilot_root"])
    assert not (pilot_root / "records/stage_completion.json").exists()
    assert Path(result["review_packet"]).is_file()

    completed = build_pilot(
        run_spec_path,
        REPOSITORY_ROOT,
        artifact_root,
        page_reader=fake_reader,
        page_qualifier=review_qualifier,
        visual_dispositions=_accepted_review_dispositions(),
        tool_versions=_fake_tool_versions(),
        completed_at="2026-09-08T12:00:00Z",
    )
    assert qualification_calls == 1
    assert completed["completion_id"]


def _fake_page(page: int) -> PageObservation:
    text = (
        "General Response 9 is routed to Chapter 16 in Volume 5.\n"
        if page == 38
        else "Response M-OSEC-137\nThe response continues beyond this range.\n"
        if page == 368
        else ""
    )
    lines = (
        (
            LineObservation(
                line_index=0,
                text_start=0,
                text_end=len(text.rstrip("\n")),
                bbox=(72.0, 700.0, 500.0, 714.0),
                character_slot_start=0,
                character_slot_end=len(text.rstrip("\n")),
                italic=page == 368,
                dotted_rule=page == 368,
            ),
        )
        if text
        else ()
    )
    return PageObservation(
        physical_page=page,
        raw_text=text,
        width_points=612,
        height_points=792,
        rotation=0,
        character_slot_count=len(text),
        lines=lines,
        section_opener=page == 38,
    )


def _fake_qualifier(
    _pdf_path: Path, observations: Sequence[PageObservation], cache_root: Path
) -> dict[str, object]:
    pages = _qualification_pages(observations, cache_root)
    return {
        "schema_version": "er_commons.response_inventory.qualification.v1",
        "render_dpi": 96,
        "comparison_threshold": 0.98,
        "observation_digest": qualification_observation_digest(observations),
        "selected_page_count": len(observations),
        "review_page_count": sum(
            bool(item["fixed_review_page"]) or bool(item["flagged_for_review"]) for item in pages
        ),
        "pages": pages,
    }


def _qualification_pages(
    observations: Sequence[PageObservation], cache_root: Path
) -> list[dict[str, object]]:
    render_root = cache_root / "renders_96dpi"
    render_root.mkdir(parents=True, exist_ok=True)
    fixed = _fixed_review_pages()
    pages = []
    for observation in observations:
        render_path = render_root / f"page-{observation.physical_page:04d}.png"
        render_path.write_bytes(b"synthetic-png")
        pages.append(
            {
                "physical_page": observation.physical_page,
                "pdfium_poppler_token_multiset_f1": 1.0,
                "render_path": render_path.relative_to(cache_root).as_posix(),
                "fixed_review_page": observation.physical_page in fixed,
                "flagged_for_review": False,
                "visual_disposition": None,
            }
        )
    return pages


def _fixed_review_pages() -> set[int]:
    return {
        *(page for first, last in TASK05C_PILOT_RANGES for page in (first, last)),
        *range(368, 373),
        *range(551, 556),
        *range(668, 672),
        2,
        4,
        38,
        39,
        83,
        84,
        721,
        722,
        744,
    }


def _accepted_review_dispositions() -> dict[int, str]:
    return {page: "accepted" for page in _fixed_review_pages()}


def _fake_tool_versions() -> dict[str, str]:
    return {"pdftotext": "pdftotext synthetic", "pdftoppm": "pdftoppm synthetic"}


def _write_bound_inputs(root: Path) -> None:
    completion_path = root / "inputs/task05a_completion.json"
    completion_path.parent.mkdir(parents=True)
    completion_path.write_bytes(json_bytes({"status": "complete"}))
    completion_sha = _sha(completion_path)
    acceptance = {
        "status": "accepted",
        "accepted_completion": {
            "path": "records/task05a_completion.json",
            "byte_size": completion_path.stat().st_size,
            "sha256": completion_sha,
        },
    }
    (completion_path.parent / "task05a_acceptance.json").write_bytes(json_bytes(acceptance))
    source_path = root / "sources/feir_volume_4.pdf"
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(b"synthetic-pdf-placeholder")
    release_path = root / "inputs/source_release_completion.json"
    manifest = {
        "sources": [
            {
                "source_id": "feir_volume_4",
                "source_role": "curator_only_response_source",
                "local_path": "sources/feir_volume_4.pdf",
                "sha256": "a" * 64,
                "byte_size": source_path.stat().st_size,
                "pdf_page_count": 744,
                "retrieval_status": "downloaded",
                "validation_status": "valid",
            }
        ]
    }
    manifest_path = root / "inputs/source_manifest.json"
    manifest_path.write_bytes(json_bytes(manifest))
    release_path.write_bytes(
        json_bytes(
            {
                "schema_version": "er_commons.source_release_completion.v1",
                "source_release_version": "brisbane_baylands_2025_deir_sources_v1",
                "manifest": {
                    "local_path": manifest_path.relative_to(root).as_posix(),
                    "byte_size": manifest_path.stat().st_size,
                    "sha256": _sha(manifest_path),
                },
            }
        )
    )


def _write_run_spec(path: Path, root: Path) -> None:
    record_schema = (
        REPOSITORY_ROOT / "benchmarks/er_bench/schemas/response_inventory/v1/records.schema.json"
    )
    run_spec_code = REPOSITORY_ROOT / "src/er_commons/response_inventory/run_spec.py"
    source_path = root / "sources/feir_volume_4.pdf"
    completion_path = root / "inputs/task05a_completion.json"
    release_path = root / "inputs/source_release_completion.json"
    manifest_path = root / "inputs/source_manifest.json"
    payload = {
        "schema_version": "er_commons.response_inventory_run_spec.v1",
        "task_stage": "05c",
        "scope_kind": "representative_pilot",
        "source": {
            "source_id": "feir_volume_4",
            "source_role": "curator_only_response_source",
            "source_release_version": "brisbane_baylands_2025_deir_sources_v1",
            "path": "sources/feir_volume_4.pdf",
            "recorded_sha256": "a" * 64,
            "recorded_byte_size": source_path.stat().st_size,
            "recorded_page_count": 744,
            "retrieval_status": "downloaded",
            "validation_status": "valid",
            "member_of_model_corpus": False,
        },
        "accepted_inputs": [
            _artifact_ref("task05a_completion", completion_path, root),
            _artifact_ref("source_release_completion", release_path, root),
            _artifact_ref("source_manifest", manifest_path, root),
        ],
        "repository_bindings": [
            _repository_ref("response_record_schema", record_schema),
            _repository_ref("producer_run_spec_code", run_spec_code),
        ],
        "producer_code_sha256": owned_code_digest(REPOSITORY_ROOT),
        "page_ranges": [
            {
                "range_id": f"p{first:04d}-p{last:04d}",
                "first_page": first,
                "last_page": last,
            }
            for first, last in TASK05C_PILOT_RANGES
        ],
        "declared_page_count": 89,
        "restart_unit": "declared_page_range",
        "cross_gap_continuations_allowed": False,
        "output_policy": {
            "artifact_relative_root": "pipelines/task05c-test",
            "pilot_namespace_template": "pilots/pilotv1-{activity_hash}",
            "completion_written_last": True,
            "copy_source_payload": False,
            "copy_upstream_payloads": False,
        },
        "cache_policy": {
            "relative_path_template": "working/05c/cache/{activity_hash}",
            "replaceable": True,
            "selected_pages_only": True,
            "retain_range_receipts": True,
        },
        "stop_behavior": {
            "on_source_binding_mismatch": "stop",
            "on_invalid_anchor_or_schema": "stop",
            "on_unclassified_page": "stop",
            "on_new_structural_regime": "stop",
            "on_nondeterministic_semantic_output": "stop",
            "on_unsafe_restart_state": "stop",
            "allow_additional_pages": False,
            "allow_policy_repair_during_run": False,
            "allowed_terminal_warning_codes": ["unit_boundary_ambiguous"],
        },
    }
    path.write_bytes(json_bytes(payload))


def _artifact_ref(role: str, path: Path, root: Path) -> dict[str, object]:
    return {
        "role": role,
        "authority": "artifact_root",
        "path": path.relative_to(root).as_posix(),
        "byte_size": path.stat().st_size,
        "sha256": _sha(path),
    }


def _repository_ref(role: str, path: Path) -> dict[str, object]:
    return {
        "role": role,
        "authority": "repository",
        "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
        "sha256": _sha(path),
    }


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
