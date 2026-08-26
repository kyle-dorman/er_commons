"""Injectable PDF page rendering boundary for Task 04 disposable assets."""

from __future__ import annotations

import logging
from importlib.metadata import version
from pathlib import Path
from typing import Protocol

from er_commons.human_review_support.task04.models import RenderOutput

LOGGER = logging.getLogger(__name__)


class PageRenderer(Protocol):
    """Render selected one-based physical pages into a review directory."""

    name: str
    version: str
    scale: float

    def render(
        self,
        source_pdf: Path,
        physical_pages: set[int],
        output_dir: Path,
        source_id: str,
    ) -> tuple[RenderOutput, ...]:
        """Render selected pages and return their generated files."""
        ...


class PdfiumPageRenderer:
    """Production pypdfium2 adapter used by the first-pass review bundle."""

    name = "pypdfium2"

    def __init__(self, *, scale: float = 1.0) -> None:
        if scale <= 0:
            raise ValueError("render scale must be positive")
        self.scale = scale
        self.version = version("pypdfium2")

    def render(
        self,
        source_pdf: Path,
        physical_pages: set[int],
        output_dir: Path,
        source_id: str,
    ) -> tuple[RenderOutput, ...]:
        """Render selected physical pages with pypdfium2."""
        import pypdfium2 as pdfium  # type: ignore[import-untyped]

        output_dir.mkdir(parents=True, exist_ok=True)
        document = pdfium.PdfDocument(str(source_pdf))
        result: list[RenderOutput] = []
        try:
            for page in sorted(physical_pages):
                if page < 1 or page > len(document):
                    raise ValueError(
                        f"selected page {page} is outside {source_pdf} page count {len(document)}"
                    )
                output = output_dir / f"{source_id}-p{page:05d}.png"
                document[page - 1].render(scale=self.scale).to_pil().save(output)
                result.append(RenderOutput(page, output))
                LOGGER.info(
                    "rendered Task 04 page",
                    extra={"source_id": source_id, "physical_page": page, "path": str(output)},
                )
        finally:
            close = getattr(document, "close", None)
            if callable(close):
                close()
        return tuple(result)


__all__ = ["PageRenderer", "PdfiumPageRenderer"]
