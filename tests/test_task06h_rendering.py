"""Focused source-free tests for the Task 06H rendering owner."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from pypdf import PdfWriter

from er_commons.artifact_io import canonical_json_sha256
from er_commons.human_review_support.extraction_review import task06h_rendering
from er_commons.human_review_support.extraction_review.task06h_rendering import (
    PageRenderJob,
    PdfiumSequentialRenderer,
    RenderLimits,
    render_task06h_pages,
)


class FakeRenderer:
    """Deterministic renderer with optional failure and source mutation."""

    name = "fake-pdfium"
    version = "1.0"
    scale = 1.0

    def __init__(
        self,
        *,
        fail_page: int | None = None,
        mutate_source: bool = False,
        output_size: int = 16,
        delay: float = 0.0,
    ) -> None:
        self.fail_page = fail_page
        self.mutate_source = mutate_source
        self.output_size = output_size
        self.delay = delay
        self.calls: list[int] = []
        self.close_calls = 0

    def render_page(
        self, job: PageRenderJob, temporary_output: Path, check: object, poll: float
    ) -> None:
        self.calls.append(job.physical_page)
        temporary_output.write_bytes(b"p" * self.output_size)
        assert callable(check)
        check()
        if self.delay:
            time.sleep(self.delay)
        if self.mutate_source:
            job.source_pdf.write_bytes(job.source_pdf.read_bytes() + b"changed")
        if self.fail_page == job.physical_page:
            raise RuntimeError("synthetic renderer failure")

    def close(self) -> None:
        self.close_calls += 1


def _jobs(tmp_path: Path, pages: tuple[int, ...] = (1, 2)) -> tuple[PageRenderJob, ...]:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"synthetic-pdf")
    return tuple(
        PageRenderJob(
            source_id="deir_main",
            source_pdf=source,
            physical_page=page,
            expected_source_bytes=source.stat().st_size,
            expected_page_count=max(pages),
        )
        for page in pages
    )


def _reuse() -> dict[str, object]:
    return {
        "source_id": "f1",
        "physical_page": 28,
        "path": "preserved/page-028.png",
        "sha256": "a" * 64,
        "payload_rehashed": False,
    }


def _identity(tag: str) -> dict[str, object]:
    return {"schema_version": "synthetic.task06h.render.v1", "tag": tag}


def _render_id(tag: str) -> str:
    return "renderpackv1-" + canonical_json_sha256(_identity(tag))


def test_render_publishes_exact_closure_and_final_reuse_opens_no_source(
    tmp_path: Path,
) -> None:
    jobs = _jobs(tmp_path)
    renderer = FakeRenderer()
    final = render_task06h_pages(
        tmp_path / "out",
        render_id=_render_id("test"),
        identity_preimage=_identity("test"),
        plan_id="reviewplanv1-test",
        jobs=jobs,
        reused_render=_reuse(),
        renderer=renderer,
    )

    assert renderer.calls == [1, 2]
    completion = json.loads((final / "records/completion.json").read_text())
    inventory = json.loads((final / "records/render_inventory.json").read_text())
    request = json.loads((final / "records/render_request.json").read_text())
    assert completion["status"] == "complete_ready_for_human_review"
    assert inventory["new_render_count"] == 2
    assert inventory["reused_external_renders"] == [_reuse()]
    assert request["identity_preimage"] == _identity("test")
    jobs[0].source_pdf.unlink()

    unused = FakeRenderer(fail_page=1)
    assert (
        render_task06h_pages(
            tmp_path / "out",
            render_id=_render_id("test"),
            identity_preimage=_identity("test"),
            plan_id="reviewplanv1-test",
            jobs=jobs,
            reused_render=_reuse(),
            renderer=unused,
        )
        == final
    )
    assert unused.calls == []

    staging = tmp_path / "out" / f".{_render_id('test')}.staging"
    final.rename(staging)
    assert (
        render_task06h_pages(
            tmp_path / "out",
            render_id=_render_id("test"),
            identity_preimage=_identity("test"),
            plan_id="reviewplanv1-test",
            jobs=jobs,
            reused_render=_reuse(),
            renderer=unused,
        )
        == final
    )
    assert unused.calls == []


def test_resume_reuses_checkpoint_and_accumulates_active_time(tmp_path: Path) -> None:
    jobs = _jobs(tmp_path)
    first = FakeRenderer(fail_page=2, delay=0.01)
    with pytest.raises(RuntimeError, match="synthetic renderer failure"):
        render_task06h_pages(
            tmp_path / "out",
            render_id=_render_id("resume"),
            identity_preimage=_identity("resume"),
            plan_id="reviewplanv1-resume",
            jobs=jobs,
            reused_render=_reuse(),
            renderer=first,
            monitor_interval_seconds=0.002,
        )
    staging = tmp_path / "out" / f".{_render_id('resume')}.staging"
    state = json.loads((staging / "records/render_state.json").read_text())
    assert state["cumulative_active_seconds"] > 0
    assert (staging / "records/page_checkpoints/deir_main-p00001.json").is_file()
    assert not (staging / "review_cache/deir_main/deir_main-p00002.png.part").exists()

    second = FakeRenderer()
    final = render_task06h_pages(
        tmp_path / "out",
        render_id=_render_id("resume"),
        identity_preimage=_identity("resume"),
        plan_id="reviewplanv1-resume",
        jobs=jobs,
        reused_render=_reuse(),
        renderer=second,
    )
    assert second.calls == [2]
    final_state = json.loads((final / "records/render_state.json").read_text())
    assert final_state["cumulative_active_seconds"] >= state["cumulative_active_seconds"]


def test_recovery_discards_safe_orphans_without_merging_bytes(tmp_path: Path) -> None:
    jobs = _jobs(tmp_path, (1,))
    staging = tmp_path / "out" / f".{_render_id('orphan')}.staging"
    output = staging / jobs[0].output_relative_path
    output.parent.mkdir(parents=True)
    output.write_bytes(b"old-orphan")
    output.with_suffix(".png.part").write_bytes(b"partial-orphan")

    renderer = FakeRenderer(output_size=7)
    final = render_task06h_pages(
        tmp_path / "out",
        render_id=_render_id("orphan"),
        identity_preimage=_identity("orphan"),
        plan_id="reviewplanv1-orphan",
        jobs=jobs,
        reused_render=_reuse(),
        renderer=renderer,
    )
    assert (final / jobs[0].output_relative_path).read_bytes() == b"p" * 7
    assert renderer.calls == [1]


def test_recovery_rejects_foreign_staging_member(tmp_path: Path) -> None:
    jobs = _jobs(tmp_path, (1,))
    foreign = tmp_path / "out" / f".{_render_id('foreign')}.staging/review_cache/foreign.bin"
    foreign.parent.mkdir(parents=True)
    foreign.write_bytes(b"foreign")

    with pytest.raises(ValueError, match="unexpected Task 06H staging members"):
        render_task06h_pages(
            tmp_path / "out",
            render_id=_render_id("foreign"),
            identity_preimage=_identity("foreign"),
            plan_id="reviewplanv1-foreign",
            jobs=jobs,
            reused_render=_reuse(),
            renderer=FakeRenderer(),
        )


def test_source_stat_change_prevents_checkpoint(tmp_path: Path) -> None:
    jobs = _jobs(tmp_path, (1,))
    with pytest.raises(RuntimeError, match="source changed during rendering"):
        render_task06h_pages(
            tmp_path / "out",
            render_id=_render_id("source-change"),
            identity_preimage=_identity("source-change"),
            plan_id="reviewplanv1-source-change",
            jobs=jobs,
            reused_render=_reuse(),
            renderer=FakeRenderer(mutate_source=True),
        )
    staging = tmp_path / "out" / f".{_render_id('source-change')}.staging"
    assert not (staging / "records/page_checkpoints/deir_main-p00001.json").exists()
    assert not (staging / jobs[0].output_relative_path).exists()


def test_monitor_counts_temporary_bytes_during_render(tmp_path: Path) -> None:
    jobs = _jobs(tmp_path, (1,))
    limits = RenderLimits(output_bytes=512, minimum_free_bytes=1)
    with pytest.raises(RuntimeError, match="all-staging-bytes"):
        render_task06h_pages(
            tmp_path / "out",
            render_id=_render_id("output-limit"),
            identity_preimage=_identity("output-limit"),
            plan_id="reviewplanv1-output-limit",
            jobs=jobs,
            reused_render=_reuse(),
            renderer=FakeRenderer(output_size=4096, delay=0.03),
            limits=limits,
            monitor_interval_seconds=0.002,
        )


def test_elapsed_time_from_failed_run_is_enforced_on_resume(tmp_path: Path) -> None:
    jobs = _jobs(tmp_path, (1,))
    with pytest.raises(RuntimeError, match="synthetic renderer failure"):
        render_task06h_pages(
            tmp_path / "out",
            render_id=_render_id("time"),
            identity_preimage=_identity("time"),
            plan_id="reviewplanv1-time",
            jobs=jobs,
            reused_render=_reuse(),
            renderer=FakeRenderer(fail_page=1, delay=0.02),
            monitor_interval_seconds=0.002,
        )
    staging = tmp_path / "out" / f".{_render_id('time')}.staging"
    elapsed = json.loads((staging / "records/render_state.json").read_text())[
        "cumulative_active_seconds"
    ]

    with pytest.raises(RuntimeError, match="cumulative active wall-time"):
        render_task06h_pages(
            tmp_path / "out",
            render_id=_render_id("time"),
            identity_preimage=_identity("time"),
            plan_id="reviewplanv1-time",
            jobs=jobs,
            reused_render=_reuse(),
            renderer=FakeRenderer(),
            limits=RenderLimits(active_seconds=elapsed / 2, minimum_free_bytes=1),
        )


def test_job_and_policy_closure_are_strict(tmp_path: Path) -> None:
    jobs = _jobs(tmp_path, (1,))
    with pytest.raises(ValueError, match="non-empty and unique"):
        render_task06h_pages(
            tmp_path / "out",
            render_id=_render_id("duplicates"),
            identity_preimage=_identity("duplicates"),
            plan_id="reviewplanv1-duplicates",
            jobs=(jobs[0], jobs[0]),
            reused_render=_reuse(),
            renderer=FakeRenderer(),
        )
    with pytest.raises(ValueError, match="one worker and two CPU threads"):
        RenderLimits(workers=2)


def test_identity_preimage_drift_is_rejected_before_render(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="identity preimage"):
        render_task06h_pages(
            tmp_path / "out",
            render_id=_render_id("original"),
            identity_preimage=_identity("changed"),
            plan_id="reviewplanv1-binding",
            jobs=_jobs(tmp_path, (1,)),
            reused_render=_reuse(),
            renderer=FakeRenderer(),
        )


def test_pdfium_supervisor_terminates_hung_child_on_resource_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class HungProcess:
        exitcode = None

        def __init__(self) -> None:
            self.alive = True
            self.terminated = False

        def start(self) -> None:
            pass

        def is_alive(self) -> bool:
            return self.alive

        def join(self, timeout: float | None = None) -> None:
            pass

        def terminate(self) -> None:
            self.terminated = True
            self.alive = False

        def kill(self) -> None:
            self.alive = False

    child = HungProcess()

    class FakeContext:
        def Process(self, **kwargs: object) -> HungProcess:  # noqa: N802
            return child

    monkeypatch.setattr(task06h_rendering.multiprocessing, "get_context", lambda _: FakeContext())
    job = _jobs(tmp_path, (1,))[0]

    with pytest.raises(RuntimeError, match="hard synthetic resource breach"):
        PdfiumSequentialRenderer().render_page(
            job,
            tmp_path / "page.png.part",
            lambda: (_ for _ in ()).throw(RuntimeError("hard synthetic resource breach")),
            0.001,
        )
    assert child.terminated is True


def test_real_pdfium_subprocess_renders_only_a_synthetic_page(tmp_path: Path) -> None:
    source = tmp_path / "synthetic.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with source.open("wb") as stream:
        writer.write(stream)
    job = PageRenderJob("synthetic", source, 1, source.stat().st_size, 1)

    final = render_task06h_pages(
        tmp_path / "out",
        render_id=_render_id("real-subprocess"),
        identity_preimage=_identity("real-subprocess"),
        plan_id="reviewplanv1-real-subprocess",
        jobs=(job,),
        reused_render=_reuse(),
        monitor_interval_seconds=0.01,
    )
    assert (final / job.output_relative_path).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
