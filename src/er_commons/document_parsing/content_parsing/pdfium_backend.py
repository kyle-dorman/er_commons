"""Project-owned PDFium backend with rotation-consistent text geometry."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, cast

from docling.backend.pypdfium2_backend import (
    PyPdfiumDocumentBackend,
    PyPdfiumPageBackend,
    get_pdf_page_geometry,
)
from docling.utils.locks import pypdfium2_lock
from docling_core.types.doc import BoundingBox, CoordOrigin  # type: ignore[attr-defined]
from docling_core.types.doc.page import BoundingRectangle, SegmentedPdfPage, TextCell

from er_commons.document_parsing.content_parsing.routing_geometry import (
    DisplayedPageTransform,
)

if TYPE_CHECKING:
    from docling.datamodel.backend_options import PdfBackendOptions
    from docling.datamodel.document import InputDocument


class RotationNormalizedPdfiumPageBackend(PyPdfiumPageBackend):
    """Expose PDFium text cells in the same displayed frame as layout regions."""

    def _transform(self) -> DisplayedPageTransform:
        page = self._require_page()
        size = self.get_size()
        with pypdfium2_lock:
            bbox = tuple(float(value) for value in page.get_bbox())
            rotation = int(page.get_rotation())
        return DisplayedPageTransform.create(
            (float(size.width), float(size.height)),
            (bbox[0], bbox[1], bbox[2], bbox[3]),
            rotation,
        )

    def _compute_text_cells(self) -> list[TextCell]:
        """Build and merge text cells only after native rectangles are displayed."""
        with pypdfium2_lock:
            if not self.text_page:
                self.text_page = self._require_page().get_textpage()
        assert self.text_page is not None
        transform = self._transform()
        cells: list[TextCell] = []
        with pypdfium2_lock:
            for index in range(self.text_page.count_rects()):
                source_rect = tuple(float(value) for value in self.text_page.get_rect(index))
                text = self.text_page.get_text_bounded(*source_rect)
                displayed = transform.to_displayed_rectangle_unclipped(
                    (source_rect[0], source_rect[1], source_rect[2], source_rect[3])
                )
                cells.append(
                    TextCell(
                        index=index,
                        text=text,
                        orig=text,
                        from_ocr=False,
                        rect=BoundingRectangle.from_bounding_box(
                            BoundingBox.from_tuple(displayed, CoordOrigin.BOTTOMLEFT)
                        ).to_top_left_origin(transform.displayed_height),
                    )
                )
        return self._merge_horizontal_cells(cells, transform)

    def _merge_horizontal_cells(
        self,
        cells: list[TextCell],
        transform: DisplayedPageTransform,
        *,
        horizontal_threshold_factor: float = 1.0,
        vertical_threshold_factor: float = 0.5,
    ) -> list[TextCell]:
        """Preserve Docling's merge policy in the corrected displayed frame."""
        if not cells:
            return []
        rows: list[list[TextCell]] = []
        current_row = [cells[0]]
        row_box = cells[0].rect.to_bounding_box()
        row_top, row_bottom, row_height = row_box.t, row_box.b, row_box.height
        for cell in cells[1:]:
            box = cell.rect.to_bounding_box()
            vertical_threshold = row_height * vertical_threshold_factor
            if (
                abs(box.t - row_top) <= vertical_threshold
                and abs(box.b - row_bottom) <= vertical_threshold
            ):
                current_row.append(cell)
                row_top = min(row_top, box.t)
                row_bottom = max(row_bottom, box.b)
                row_height = row_bottom - row_top
            else:
                rows.append(current_row)
                current_row = [cell]
                row_top, row_bottom, row_height = box.t, box.b, box.height
        rows.append(current_row)

        merged = [
            cell
            for row in rows
            for cell in self._merge_row(row, transform, horizontal_threshold_factor)
        ]
        for index, cell in enumerate(merged, 1):
            cell.index = index
        return merged

    def _merge_row(
        self,
        row: list[TextCell],
        transform: DisplayedPageTransform,
        horizontal_threshold_factor: float,
    ) -> list[TextCell]:
        groups: list[list[TextCell]] = []
        current = [row[0]]
        for cell in row[1:]:
            previous = current[-1]
            average_height = (previous.rect.height + cell.rect.height) / 2
            gap = cell.rect.to_bounding_box().l - previous.rect.to_bounding_box().r
            if gap <= average_height * horizontal_threshold_factor:
                current.append(cell)
            else:
                groups.append(current)
                current = [cell]
        groups.append(current)
        return [self._merge_group(group, transform) for group in groups]

    def _merge_group(self, group: list[TextCell], transform: DisplayedPageTransform) -> TextCell:
        if len(group) == 1:
            return group[0]
        displayed_top_left = BoundingBox(
            l=min(cell.rect.to_bounding_box().l for cell in group),
            t=min(cell.rect.to_bounding_box().t for cell in group),
            r=max(cell.rect.to_bounding_box().r for cell in group),
            b=max(cell.rect.to_bounding_box().b for cell in group),
            coord_origin=CoordOrigin.TOPLEFT,
        )
        displayed_bottom_left = displayed_top_left.to_bottom_left_origin(transform.displayed_height)
        source = transform.to_source_rectangle_unclipped(displayed_bottom_left.as_tuple())
        assert self.text_page is not None
        with pypdfium2_lock:
            text = self.text_page.get_text_bounded(*source)
        return TextCell(
            index=group[0].index,
            text=text,
            orig=text,
            rect=BoundingRectangle.from_bounding_box(displayed_top_left),
            from_ocr=False,
        )

    def get_text_in_rect(self, bbox: BoundingBox) -> str:
        """Query native PDFium text using a displayed Docling rectangle."""
        with pypdfium2_lock:
            if not self.text_page:
                self.text_page = self._require_page().get_textpage()
        displayed = bbox.to_bottom_left_origin(self.get_size().height)
        source = self._transform().to_source_rectangle_unclipped(displayed.as_tuple())
        assert self.text_page is not None
        with pypdfium2_lock:
            return cast(str, self.text_page.get_text_bounded(*source))

    def get_segmented_page(self) -> SegmentedPdfPage | None:
        """Publish displayed dimensions together with displayed text cells."""
        if not self.valid:
            return None
        transform = self._transform()
        native = get_pdf_page_geometry(self._require_page())

        def displayed_box(box: BoundingBox) -> BoundingBox:
            source = box.to_bottom_left_origin(transform.canvas_height)
            return cast(
                BoundingBox,
                BoundingBox.from_tuple(
                    transform.to_displayed_rectangle_unclipped(source.as_tuple()),
                    CoordOrigin.BOTTOMLEFT,
                ),
            )

        page_box = BoundingBox(
            l=0.0,
            b=0.0,
            r=transform.displayed_width,
            t=transform.displayed_height,
            coord_origin=CoordOrigin.BOTTOMLEFT,
        )
        dimension = native.model_copy(
            update={
                "angle": 0.0,
                "rect": BoundingRectangle.from_bounding_box(page_box),
                "art_bbox": displayed_box(native.art_bbox),
                "bleed_bbox": displayed_box(native.bleed_bbox),
                "crop_bbox": displayed_box(native.crop_bbox),
                "media_bbox": displayed_box(native.media_bbox),
                "trim_bbox": displayed_box(native.trim_bbox),
            }
        )
        cells = self._compute_text_cells()
        return SegmentedPdfPage(
            dimension=dimension,
            textline_cells=cells,
            char_cells=[],
            word_cells=[],
            has_lines=bool(cells),
            has_words=False,
            has_chars=False,
        )


class RotationNormalizedPdfiumDocumentBackend(PyPdfiumDocumentBackend):
    """Construct project-owned rotation-normalized PDFium page backends."""

    def __init__(
        self,
        in_doc: InputDocument,
        path_or_stream: BytesIO | Path,
        options: PdfBackendOptions | None = None,
    ) -> None:
        super().__init__(in_doc, path_or_stream, options)

    def load_page(self, page_no: int) -> RotationNormalizedPdfiumPageBackend:
        with pypdfium2_lock:
            return RotationNormalizedPdfiumPageBackend(
                self._pdoc,
                self.document_hash,
                page_no,
            )


__all__ = ["RotationNormalizedPdfiumDocumentBackend", "RotationNormalizedPdfiumPageBackend"]
