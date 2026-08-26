"""Importable application seam for one complete Task 04 review-bundle build."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from er_commons.human_review_support.task04.canonical_evidence import page_review_evidence
from er_commons.human_review_support.task04.config import RENDER_SCALE, review_policy
from er_commons.human_review_support.task04.discovery import DiscoveredInputs, discover_inputs
from er_commons.human_review_support.task04.models import (
    BuildRequest,
    PageEvidence,
    RenderedPage,
    ReviewCard,
    ReviewItems,
)
from er_commons.human_review_support.task04.presentation import write_review_html
from er_commons.human_review_support.task04.records import (
    RecordValidator,
    abandon_publication,
    create_identity,
    publish,
    reserve_publication,
    write_records,
)
from er_commons.human_review_support.task04.rendering import PageRenderer, PdfiumPageRenderer
from er_commons.human_review_support.task04.selection import build_selection
from er_commons.human_review_support.task04.verification import (
    CandidateVerifier,
    SourceFileVerifier,
)

LOGGER = logging.getLogger(__name__)

PageEvidenceLoader = Callable[[Path, set[int], Path], dict[int, PageEvidence]]


def build_review_bundle(
    request: BuildRequest,
    *,
    renderer: PageRenderer | None = None,
    page_evidence_loader: PageEvidenceLoader = page_review_evidence,
    schema_root: Path | None = None,
    candidate_verifier: CandidateVerifier | None = None,
    source_file_verifier: SourceFileVerifier | None = None,
) -> Path:
    """Build, validate, and atomically publish one first-pass review bundle."""
    resolved_schema_root = schema_root or default_schema_root()
    active_renderer = renderer or PdfiumPageRenderer(scale=RENDER_SCALE)
    inputs = discover_inputs(
        request.retained_root,
        request.data_root,
        candidate_verifier=candidate_verifier,
        source_file_verifier=source_file_verifier,
        input_scope=request.input_scope,
    )
    identity = create_identity(
        inputs,
        review_policy(),
        implementation_root=Path(__file__).parent,
        schema_root=resolved_schema_root,
        renderer_name=active_renderer.name,
        renderer_version=active_renderer.version,
        renderer_scale=active_renderer.scale,
    )
    LOGGER.info(
        "starting Task 04 review build",
        extra={"review_run_id": identity.review_run_id, "output_root": str(request.output_root)},
    )
    workspace = reserve_publication(request.output_root, identity.review_run_id)
    try:
        selection = build_selection(
            inputs, request.data_root, identity.review_run_id, identity.policy_sha256
        )
        cards, generated = _build_presentation(
            workspace.staging_root,
            inputs,
            selection.items,
            active_renderer,
            page_evidence_loader,
        )
        html_files = write_review_html(
            workspace.staging_root / "html", cards, "Task 04 first-pass review"
        )
        validator = RecordValidator(resolved_schema_root)
        write_records(
            workspace,
            inputs,
            identity,
            selection,
            cards,
            (*generated, *html_files),
            validator,
            request.data_root,
            active_renderer.name,
            active_renderer.version,
            active_renderer.scale,
        )
        final_root = publish(workspace)
    except Exception:
        abandon_publication(workspace)
        LOGGER.exception(
            "Task 04 review build failed",
            extra={"review_run_id": identity.review_run_id},
        )
        raise
    LOGGER.info(
        "published Task 04 review bundle",
        extra={"review_run_id": identity.review_run_id, "path": str(final_root)},
    )
    return final_root


def _build_presentation(
    staging_root: Path,
    inputs: DiscoveredInputs,
    items: ReviewItems,
    renderer: PageRenderer,
    evidence_loader: PageEvidenceLoader,
) -> tuple[tuple[ReviewCard, ...], tuple[Path, ...]]:
    """Render the selected page union and attach disposable evidence to cards."""
    rendered_by_source: dict[str, dict[int, RenderedPage]] = {}
    generated: list[Path] = []
    for source in inputs.sources:
        candidate = source.selected_candidate
        pages = _selected_pages(items, source.source_id)
        if candidate is None or not pages or not source.source_pdf.is_file():
            continue
        output_dir = staging_root / "html" / "renders" / source.source_id
        outputs = renderer.render(source.source_pdf, pages, output_dir, source.source_id)
        evidence = evidence_loader(candidate, pages, source.source_pdf)
        rendered_by_source[source.source_id] = {
            output.physical_page: RenderedPage(
                output.physical_page,
                output.path.relative_to(staging_root / "html").as_posix(),
                evidence[output.physical_page],
            )
            for output in outputs
        }
        generated.extend(output.path for output in outputs)
    cards = tuple(
        ReviewCard(
            item,
            tuple(
                rendered_by_source.get(item.source_id or "", {})[page]
                for page in item.physical_pages
                if page in rendered_by_source.get(item.source_id or "", {})
            ),
        )
        for item in items
    )
    return cards, tuple(generated)


def _selected_pages(items: ReviewItems, source_id: str) -> set[int]:
    """Return the union of selected physical pages for one source."""
    return {page for item in items if item.source_id == source_id for page in item.physical_pages}


def default_schema_root() -> Path:
    """Resolve checked-in Task 04 schemas from a source checkout."""
    repo_root = Path(__file__).parents[4]
    return repo_root / "benchmarks" / "er_bench" / "schemas" / "task04_review" / "v1"


__all__ = ["PageEvidenceLoader", "build_review_bundle", "default_schema_root"]
