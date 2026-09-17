"""Bounded, restartable Task 06H PDF-page rendering."""

import multiprocessing
import os
import re
import shutil
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import psutil  # type: ignore[import-untyped]

from er_commons.artifact_io import (
    artifact_inventory,
    file_reference,
    json_bytes,
    publish_bytes_no_clobber,
    read_json_object,
    sha256_file,
    write_json_atomic,
)
from er_commons.human_review_support.extraction_review.task06h_render_identity import (
    validate_render_identity,
)


@dataclass(frozen=True)
class RenderLimits:
    workers: int = 1
    cpu_threads: int = 2
    rss_bytes: int = 2 * 1024**3
    active_seconds: float = 3600.0
    output_bytes: int = 1024**3
    minimum_free_bytes: int = 2 * 1024**3

    def __post_init__(self) -> None:
        if self.workers != 1 or self.cpu_threads != 2:
            raise ValueError("Task 06H rendering requires one worker and two CPU threads")
        if min(self.rss_bytes, self.output_bytes, self.minimum_free_bytes) <= 0:
            raise ValueError("Task 06H byte limits must be positive")
        if self.active_seconds <= 0:
            raise ValueError("Task 06H active-time limit must be positive")


@dataclass(frozen=True)
class PageRenderJob:
    source_id: str
    source_pdf: Path
    physical_page: int
    expected_source_bytes: int
    expected_page_count: int

    def __post_init__(self) -> None:
        if re.fullmatch(r"[A-Za-z0-9_.-]+", self.source_id) is None:
            raise ValueError(f"unsafe Task 06H source ID: {self.source_id!r}")
        if self.physical_page < 1 or self.expected_source_bytes < 1:
            raise ValueError("page and expected source bytes must be positive")
        if self.expected_page_count < self.physical_page:
            raise ValueError("selected page exceeds expected source page count")

    @property
    def key(self) -> str:
        return f"{self.source_id}-p{self.physical_page:05d}"

    @property
    def output_relative_path(self) -> Path:
        return Path("review_cache") / self.source_id / f"{self.key}.png"


class PageRenderer(Protocol):
    name: str
    version: str
    scale: float

    def render_page(
        self, job: PageRenderJob, output: Path, check: Callable[[], None], poll: float
    ) -> None: ...


class PdfiumSequentialRenderer:
    name = "pypdfium2"
    scale = 1.0

    def __init__(self) -> None:
        from importlib.metadata import version

        self.version = version("pypdfium2")

    def render_page(
        self, job: PageRenderJob, output: Path, check: Callable[[], None], poll: float
    ) -> None:
        process = multiprocessing.get_context("spawn").Process(
            target=_pdfium_worker,
            args=(
                str(job.source_pdf.resolve()),
                job.physical_page,
                job.expected_page_count,
                str(output),
            ),
        )
        process.start()
        try:
            while process.is_alive():
                process.join(poll)
                check()
            if process.exitcode != 0:
                raise RuntimeError(f"pypdfium2 render subprocess failed: {job.key}")
        except BaseException:
            if process.is_alive():
                process.terminate()
                process.join(5)
            if process.is_alive():
                process.kill()
                process.join()
            raise


def _pdfium_worker(source: str, page: int, page_count: int, output: str) -> None:
    import pypdfium2 as pdfium  # type: ignore[import-untyped]

    document = pdfium.PdfDocument(source)
    try:
        if len(document) != page_count:
            raise ValueError("source PDF page count differs")
        document[page - 1].render(scale=1.0).to_pil().save(output, format="PNG")
    finally:
        close = getattr(document, "close", None)
        if callable(close):
            close()


def render_task06h_pages(
    output_parent: Path,
    *,
    render_id: str,
    plan_id: str,
    identity_preimage: dict[str, Any],
    jobs: Sequence[PageRenderJob],
    reused_render: dict[str, Any],
    renderer: PageRenderer | None = None,
    limits: RenderLimits | None = None,
    monitor_interval_seconds: float = 0.1,
) -> Path:
    """Render the exact page set, resume checkpoints, and publish completion last."""
    limits = limits or RenderLimits()
    validate_render_identity(render_id, identity_preimage, reused_render)
    if monitor_interval_seconds <= 0:
        raise ValueError("Task 06H resource monitor interval must be positive")
    ordered = _validate_jobs(jobs)
    final = output_parent / render_id
    if final.exists():
        _validate_final(final, render_id, plan_id, identity_preimage, ordered)
        return final
    staging = output_parent / f".{render_id}.staging"
    output_parent.mkdir(parents=True, exist_ok=True)
    staging.mkdir(exist_ok=True)
    if (staging / "records/completion.json").is_file():
        _validate_final(staging, render_id, plan_id, identity_preimage, ordered)
        staging.rename(final)
        return final
    _recover_staging(staging, ordered, render_id, plan_id)
    state_path = staging / "records" / "render_state.json"
    state = _load_state(state_path, render_id, plan_id)
    started, process = time.monotonic(), psutil.Process()

    def active() -> float:
        return float(state["cumulative_active_seconds"]) + time.monotonic() - started

    for name in "OMP_NUM_THREADS OPENBLAS_NUM_THREADS MKL_NUM_THREADS NUMEXPR_NUM_THREADS".split():
        os.environ[name] = str(limits.cpu_threads)
    _check_resources(staging, output_parent, limits, process, active())
    actual_renderer = renderer
    try:
        for job in ordered:
            checkpoint = staging / "records" / "page_checkpoints" / f"{job.key}.json"
            if checkpoint.exists():
                continue
            if actual_renderer is None:
                actual_renderer = PdfiumSequentialRenderer()
            _render_one(
                staging,
                output_parent,
                job,
                render_id,
                plan_id,
                actual_renderer,
                limits,
                process,
                active,
                monitor_interval_seconds,
            )
            state["cumulative_active_seconds"] = active()
            started = time.monotonic()
            write_json_atomic(state_path, state)
        _check_resources(staging, output_parent, limits, process, active())
        return _publish_completion(
            staging,
            final,
            render_id,
            plan_id,
            ordered,
            reused_render,
            limits,
            identity_preimage,
            lambda: _check_resources(staging, output_parent, limits, process, active()),
        )
    except BaseException:
        state["cumulative_active_seconds"] = active()
        write_json_atomic(state_path, state)
        raise


def _render_one(
    staging: Path,
    output_parent: Path,
    job: PageRenderJob,
    render_id: str,
    plan_id: str,
    renderer: PageRenderer,
    limits: RenderLimits,
    process: psutil.Process,
    active: Callable[[], float],
    interval: float,
) -> None:
    before = _source_stat(job.source_pdf)
    if before[0] != job.expected_source_bytes:
        raise ValueError(f"source byte size differs without hashing: {job.source_id}")
    output = staging / job.output_relative_path
    temporary = output.with_suffix(output.suffix + ".part")
    output.parent.mkdir(parents=True, exist_ok=True)

    def resource_check() -> None:
        _check_resources(staging, output_parent, limits, process, active())

    resource_check()
    try:
        renderer.render_page(job, temporary, resource_check, interval)
        resource_check()
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise ValueError(f"renderer did not produce a non-empty PNG: {job.key}")
        if _source_stat(job.source_pdf) != before:
            raise RuntimeError(f"source changed during rendering: {job.source_id}")
        os.replace(temporary, output)
        checkpoint = {
            "schema_version": "er_commons.task06h.page_render_checkpoint.v1",
            "render_id": render_id,
            "plan_id": plan_id,
            "source_id": job.source_id,
            "physical_page": job.physical_page,
            "renderer": {
                "name": renderer.name,
                "version": renderer.version,
                "scale": renderer.scale,
            },
            "source_stat": dict(zip(("size", "mtime_ns", "device", "inode"), before, strict=True)),
            "output": file_reference(output, root=staging),
        }
        publish_bytes_no_clobber(
            staging / "records" / "page_checkpoints" / f"{job.key}.json",
            json_bytes(checkpoint),
        )
        _check_resources(staging, output_parent, limits, process, active())
    finally:
        temporary.unlink(missing_ok=True)


def _recover_staging(
    staging: Path, jobs: Sequence[PageRenderJob], render_id: str, plan_id: str
) -> None:
    checkpoints = staging / "records" / "page_checkpoints"
    checkpoints.mkdir(parents=True, exist_ok=True)
    (staging / "review_cache").mkdir(exist_ok=True)
    for name in ("render_inventory.json", "render_request.json", "artifact_inventory.json"):
        (staging / "records" / name).unlink(missing_ok=True)
    for path in sorted(staging.rglob("*.part")):
        if path.is_file() and path.resolve().is_relative_to(staging.resolve()):
            path.unlink()
    allowed = {Path("records/render_state.json")}
    by_key = {job.key: job for job in jobs}
    for job in jobs:
        allowed.add(job.output_relative_path)
        allowed.add(Path("records/page_checkpoints") / f"{job.key}.json")
    files = [path for path in staging.rglob("*") if path.is_file()]
    unexpected = sorted(
        path.relative_to(staging) for path in files if path.relative_to(staging) not in allowed
    )
    if unexpected:
        raise ValueError(f"unexpected Task 06H staging members: {unexpected}")
    for key, job in by_key.items():
        output = staging / job.output_relative_path
        checkpoint = checkpoints / f"{key}.json"
        if output.exists() and not checkpoint.exists():
            output.unlink()
        elif checkpoint.exists():
            _validate_checkpoint(
                checkpoint, output, job, staging, render_id, plan_id, verify_source=True
            )


def _validate_checkpoint(
    path: Path,
    output: Path,
    job: PageRenderJob,
    staging: Path,
    render_id: str,
    plan_id: str,
    *,
    verify_source: bool,
) -> None:
    value = read_json_object(path)
    expected = (render_id, plan_id, job.source_id, job.physical_page)
    actual = (
        value.get("render_id"),
        value.get("plan_id"),
        value.get("source_id"),
        value.get("physical_page"),
    )
    if actual != expected or not output.is_file():
        raise ValueError(f"invalid Task 06H checkpoint closure: {job.key}")
    reference = value.get("output")
    if not isinstance(reference, dict) or reference != file_reference(output, root=staging):
        raise ValueError(f"Task 06H checkpoint output differs: {job.key}")
    if verify_source:
        source_stat = value.get("source_stat")
        names = ("size", "mtime_ns", "device", "inode")
        if not isinstance(source_stat, dict) or any(
            type(source_stat.get(name)) is not int for name in names
        ):
            raise ValueError(f"invalid Task 06H source stat: {job.key}")
        recorded = tuple(source_stat[name] for name in names)
        if _source_stat(job.source_pdf) != recorded:
            raise ValueError(f"Task 06H checkpoint source stat differs: {job.key}")


def _publish_completion(
    staging: Path,
    final: Path,
    render_id: str,
    plan_id: str,
    jobs: Sequence[PageRenderJob],
    reused_render: dict[str, Any],
    limits: RenderLimits,
    identity_preimage: dict[str, Any],
    resource_check: Callable[[], None],
) -> Path:
    pages = [
        read_json_object(staging / "records" / "page_checkpoints" / f"{job.key}.json")
        for job in jobs
    ]
    render_inventory = {
        "schema_version": "er_commons.task06h.render_inventory.v1",
        "render_id": render_id,
        "plan_id": plan_id,
        "identity_preimage": identity_preimage,
        "new_renders": pages,
        "reused_external_renders": [reused_render],
        "new_render_count": len(jobs),
        "reused_render_count": 1,
    }
    records = staging / "records"
    publish_bytes_no_clobber(records / "render_inventory.json", json_bytes(render_inventory))
    renderer_record = pages[0]["renderer"]
    if any(page.get("renderer") != renderer_record for page in pages):
        raise ValueError("Task 06H checkpoint renderer identities differ")
    if "renderer" in identity_preimage and identity_preimage["renderer"] != renderer_record:
        raise ValueError("Task 06H renderer differs from its identity preimage")
    request = {
        "render_id": render_id,
        "plan_id": plan_id,
        "identity_preimage": identity_preimage,
        "renderer": renderer_record,
        "limits": limits.__dict__,
    }
    publish_bytes_no_clobber(records / "render_request.json", json_bytes(request))
    inventory = artifact_inventory(
        staging, {"records/artifact_inventory.json", "records/completion.json"}
    )
    publish_bytes_no_clobber(records / "artifact_inventory.json", json_bytes(inventory))
    completion = {
        "schema_version": "er_commons.task06h.render_completion.v1",
        "render_id": render_id,
        "plan_id": plan_id,
        "status": "complete_ready_for_human_review",
        "new_render_count": len(jobs),
        "reused_render_count": 1,
        "inventory_sha256": sha256_file(records / "artifact_inventory.json"),
        "completion_last": True,
    }
    resource_check()
    if (
        sum(path.stat().st_size for path in staging.rglob("*") if path.is_file())
        + len(json_bytes(completion))
        > limits.output_bytes
    ):
        raise RuntimeError("Task 06H all-staging-bytes output limit exceeded")
    publish_bytes_no_clobber(records / "completion.json", json_bytes(completion))
    if final.exists():
        raise FileExistsError(f"Task 06H final appeared during publication: {final}")
    staging.rename(final)
    return final


def _validate_final(
    root: Path,
    render_id: str,
    plan_id: str,
    identity_preimage: dict[str, Any],
    jobs: Sequence[PageRenderJob],
) -> None:
    completion = read_json_object(root / "records" / "completion.json")
    request = read_json_object(root / "records" / "render_request.json")
    if (
        completion.get("render_id") != render_id
        or completion.get("plan_id") != plan_id
        or completion.get("status") != "complete_ready_for_human_review"
        or completion.get("new_render_count") != len(jobs)
    ):
        raise ValueError("completed Task 06H render does not match the request")
    if request.get("identity_preimage") != identity_preimage:
        raise ValueError("completed Task 06H identity preimage differs")
    if "renderer" in identity_preimage and request.get("renderer") != identity_preimage["renderer"]:
        raise ValueError("completed Task 06H renderer binding differs")
    for job in jobs:
        _validate_checkpoint(
            root / "records" / "page_checkpoints" / f"{job.key}.json",
            root / job.output_relative_path,
            job,
            root,
            render_id,
            plan_id,
            verify_source=False,
        )
    inventory = root / "records" / "artifact_inventory.json"
    if completion.get("inventory_sha256") != sha256_file(inventory):
        raise ValueError("completed Task 06H inventory digest differs")
    sealed = read_json_object(inventory)
    actual = artifact_inventory(
        root, {"records/artifact_inventory.json", "records/completion.json"}
    )
    if sealed != actual:
        raise ValueError("completed Task 06H render membership differs")


def _validate_jobs(jobs: Sequence[PageRenderJob]) -> tuple[PageRenderJob, ...]:
    ordered = tuple(sorted(jobs, key=lambda job: (job.source_id, job.physical_page)))
    keys = [job.key for job in ordered]
    if not ordered or len(keys) != len(set(keys)):
        raise ValueError("Task 06H render jobs must be non-empty and unique")
    return ordered


def _load_state(path: Path, render_id: str, plan_id: str) -> dict[str, Any]:
    if not path.exists():
        value: dict[str, Any] = {
            "schema_version": "er_commons.task06h.render_state.v1",
            "render_id": render_id,
            "plan_id": plan_id,
            "cumulative_active_seconds": 0.0,
        }
        write_json_atomic(path, value)
        return value
    value = read_json_object(path)
    if value.get("render_id") != render_id or value.get("plan_id") != plan_id:
        raise ValueError("Task 06H render state identity differs")
    elapsed = value.get("cumulative_active_seconds")
    if not isinstance(elapsed, (int, float)) or elapsed < 0:
        raise ValueError("Task 06H cumulative active time is invalid")
    return value


def _source_stat(path: Path) -> tuple[int, int, int, int]:
    value = path.stat()
    return value.st_size, value.st_mtime_ns, value.st_dev, value.st_ino


def _check_resources(
    staging: Path,
    output_parent: Path,
    limits: RenderLimits,
    process: psutil.Process,
    active_seconds: float,
) -> None:
    rss = process.memory_info().rss
    for child in process.children(recursive=True):
        try:
            rss += child.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    staging_bytes = sum(path.stat().st_size for path in staging.rglob("*") if path.is_file())
    if rss > limits.rss_bytes:
        raise RuntimeError("Task 06H process-plus-children RSS limit exceeded")
    if active_seconds > limits.active_seconds:
        raise RuntimeError("Task 06H cumulative active wall-time limit exceeded")
    if staging_bytes > limits.output_bytes:
        raise RuntimeError("Task 06H all-staging-bytes output limit exceeded")
    if shutil.disk_usage(output_parent).free < limits.minimum_free_bytes:
        raise RuntimeError("Task 06H minimum free-space limit violated")
