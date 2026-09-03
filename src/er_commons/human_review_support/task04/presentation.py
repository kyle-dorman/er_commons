"""Static HTML presenters for the read-only Task 04 review workspace."""

from __future__ import annotations

import html
import json
from collections import Counter
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path

from er_commons.human_review_support.task04.models import (
    BlockEvidence,
    JsonValue,
    PageEvidence,
    ParserAttempt,
    ParserPageEvidence,
    ReviewCard,
    ReviewItem,
    TableEvidence,
    TableParserEvidence,
)
from er_commons.human_review_support.task04.warning_policy import warning_guidance

_ASSET_PACKAGE = "er_commons.human_review_support.task04.assets"
_REASON_LABELS = {
    "content_rich_early_region": "content-rich sample from the early document region",
    "content_rich_middle_region": "content-rich sample from the middle document region",
    "content_rich_late_region": "content-rich sample from the late document region",
    "main_major_chapter_coverage": "content-bearing page at a major main-report chapter",
    "one_representative_per_normalized_warning_class": (
        "one example of this normalized warning class"
    ),
    "recovered_attempt_history": "earlier failed attempts followed by a successful publication",
    "unresolved_attempt_history": "source still lacks successful publication evidence",
    "missing_publication_evidence": "expected source has no successful publication evidence",
    "main_report_table_cap": "main-report table-family sample",
    "largest_multi_page_appendix_family": (
        "one of this appendix's largest multi-page table families"
    ),
    "toc_false_negative_candidate": "possible TOC missed by the canonical TOC representation",
    "canonical_positive_toc": "TOC recognized by the document extraction",
    "task03i_finding_recheck": "fresh page evidence for the accepted Task 03I repair",
}


def write_review_html(
    root: Path,
    cards: tuple[ReviewCard, ...],
    title: str,
    toc_decisions: Mapping[str, str] | None = None,
    *,
    review_run_id: str = "task04-review",
) -> tuple[Path, ...]:
    """Write readable static assets and a keyboard-navigable review index."""
    root.mkdir(parents=True, exist_ok=True)
    rendered_cards = "\n".join(_render_card(card, index) for index, card in enumerate(cards))
    counts = dict(Counter(card.item.queue.value for card in cards))
    template = files(_ASSET_PACKAGE).joinpath("review.html").read_text()
    index = root / "index.html"
    index.write_text(
        template.replace("__TITLE__", html.escape(title))
        .replace("__CARDS__", rendered_cards)
        .replace("__QUEUE_COUNTS__", json.dumps(counts, sort_keys=True))
        .replace("__TOC_DECISIONS__", json.dumps(dict(toc_decisions or {}), sort_keys=True))
        .replace("__REVIEW_RUN_ID__", json.dumps(review_run_id))
    )
    outputs = [index]
    for name in ("review.css", "review.js"):
        output = root / name
        output.write_text(files(_ASSET_PACKAGE).joinpath(name).read_text())
        outputs.append(output)
    return tuple(outputs)


def _render_card(card: ReviewCard, index: int) -> str:
    """Render one queue item and all disposable page comparisons."""
    item = card.item
    reasons = "; ".join(_REASON_LABELS.get(reason, reason) for reason in item.reasons)
    details = [_candidate_provenance(item)] if item.candidate_id is not None else []
    if item.failure is not None:
        details.append(_failure_details(item))
    if item.warning is not None:
        details.append(_warning_details(item))
    if item.table_family_id is not None:
        details.append(f"<p><strong>Table family:</strong> {html.escape(item.table_family_id)}</p>")
        details.append(render_parser_evidence(item.table_parser_evidence))
    if item.queue.value == "positive_toc":
        details.append(_positive_run_scope(item))
    page_markup = "".join(
        render_page_comparison(page.relative_path, page.evidence) for page in card.rendered_pages
    )
    toc_controls = (
        _toc_controls(item) if item.queue.value in {"table", "toc_review", "positive_toc"} else ""
    )
    return (
        f'<article class="item" data-index="{index}" '
        f'data-queue="{item.queue.value}" hidden>'
        f"<h2>{html.escape(item.review_item_id)}</h2>"
        f"<p><strong>Queue:</strong> {item.queue.value} · "
        f"<strong>Source:</strong> {html.escape(item.source_id or 'missing')}</p>"
        f"<p><strong>Why selected:</strong> {html.escape(reasons)}</p>"
        '<details class="provenance"><summary>Population details</summary><p>'
        f"{html.escape(json.dumps(dict(item.population), sort_keys=True))}</p></details>"
        f"{''.join(details)}{toc_controls}{page_markup}</article>"
    )


def _toc_controls(item: ReviewItem) -> str:
    """Render queue-specific TOC decision controls."""
    candidate_page_id = str(item.population.get("candidate_page_id") or item.review_item_id)
    if item.queue.value == "positive_toc":
        run = item.population.get("positive_run")
        suffix_ids = (
            run.get("suffix_entry_ids", [candidate_page_id])
            if isinstance(run, Mapping)
            else [candidate_page_id]
        )
        encoded_suffix = html.escape(json.dumps(suffix_ids, separators=(",", ":")), quote=True)
        return (
            '<section class="toc-decision" aria-label="TOC false-positive decision">'
            '<div><p class="panel-kicker">TOC false-positive check</p>'
            "<p>Set or clear this page's label. Not TOC applies through the end "
            'of its positive run.</p></div><div class="toc-buttons">'
            f'<button type="button" data-toc-yes data-entry-id="{html.escape(candidate_page_id)}">'
            "TOC (T)</button>"
            '<button class="toc-no" type="button" data-toc-no '
            f'data-entry-id="{html.escape(candidate_page_id)}" '
            f'data-run-suffix-entry-ids="{encoded_suffix}">Not TOC through run end (F)</button>'
            "</div></section>"
        )
    return (
        '<section class="toc-decision" aria-label="TOC false-negative decision">'
        '<div><p class="panel-kicker">TOC false-negative check</p>'
        "<p>Set or clear the label for this full-page-table review run.</p></div>"
        '<div class="toc-buttons">'
        f'<button type="button" data-toc-yes data-entry-id="{html.escape(candidate_page_id)}">'
        "TOC (T)</button>"
        '<button class="toc-no" type="button" data-toc-no '
        f'data-entry-id="{html.escape(candidate_page_id)}">'
        "Not TOC (F)</button></div></section>"
    )


def _positive_run_scope(item: ReviewItem) -> str:
    """Show the machine-positive run represented by one false-positive check."""
    run = item.population.get("positive_run")
    if not isinstance(run, Mapping) or not run:
        return ""
    start = run.get("start_page")
    end = run.get("end_page")
    count = run.get("page_count")
    basis = str(run.get("selection_basis") or "representative")
    return (
        '<p class="run-scope"><strong>Positive run:</strong> '
        f"physical pages {html.escape(str(start))}–{html.escape(str(end))} "
        f"({html.escape(str(count))} pages) · this task is physical page "
        f"{item.physical_pages[0]} · {html.escape(basis.replace('_', ' '))}</p>"
    )


def _candidate_provenance(item: ReviewItem) -> str:
    """Render selected-candidate provenance separately from page evidence."""
    return (
        '<details class="provenance"><summary>Candidate provenance</summary>'
        f"<p>{html.escape(item.candidate_id or '')}</p></details>"
    )


def _failure_details(item: ReviewItem) -> str:
    """Render one complete source attempt history."""
    failure = item.failure
    if failure is None:
        return ""
    recovered = failure.current_status == "recovered_later"
    status = "Recovered later" if recovered else "Still unresolved"
    explanation = (
        "These are historical attempts. This source later produced the selected candidate."
        if recovered
        else "This source does not have a successful Task 03H publication."
    )
    attempts = (
        "".join(
            _attempt_details(attempt.to_record(), number, recovered)
            for number, attempt in enumerate(failure.attempts, start=1)
        )
        or '<p class="empty-evidence">No attempt workspace was retained for this source.</p>'
    )
    return (
        f'<section class="failure-summary"><span class="status-chip '
        f'{"status-recovered" if recovered else "status-unresolved"}">{status}</span>'
        f"<p>{html.escape(explanation)}</p>"
        f"<p><strong>Retained non-success attempts:</strong> {len(failure.attempts)}</p>"
        f"{attempts}</section>"
    )


def _attempt_details(attempt: dict[str, JsonValue], number: int, recovered: bool) -> str:
    """Render one retained non-success attempt diagnostic."""
    return (
        f'<details class="attempt" {"" if recovered else "open"}><summary>'
        f"Attempt {number} · {html.escape(str(attempt['disposition']))} · "
        f"{html.escape(str(attempt['stage']))}</summary>"
        f"<p><strong>{html.escape(str(attempt['failure_class'] or 'No terminal error class'))}"
        "</strong></p>"
        f"<pre>{html.escape(str(attempt['detail']))}</pre>"
        f'<p class="path-note">{html.escape(str(attempt["relative_path"]))}</p></details>'
    )


def _warning_details(item: ReviewItem) -> str:
    """Render normalized warning counts, meaning, and parser evidence."""
    warning = item.warning
    if warning is None:
        return ""
    record = warning.to_record()
    exact = warning.page_anchor_kind.startswith("exact_")
    explanation, action = warning_guidance(warning.warning_class.representative.message)
    return (
        f'<p><span class="status-chip {"status-exact" if exact else "status-context"}">'
        f"{'Exact warning page' if exact else 'Representative context page'}</span></p>"
        f"<p><strong>Owner:</strong> {html.escape(', '.join(warning.warning_class.owners))}</p>"
        f"<p><strong>Code:</strong> {html.escape(', '.join(warning.warning_class.codes))}</p>"
        f"<p><strong>Occurrences:</strong> {warning.warning_class.occurrence_count}</p>"
        f"<p><strong>Raw owner/code observations:</strong> "
        f"{warning.warning_class.raw_occurrence_count}</p>"
        f"<p><strong>Pipeline labels:</strong> "
        f"{html.escape(json.dumps(record['owner_code_counts'], sort_keys=True))}</p>"
        f"<p><strong>Per-source counts:</strong> "
        f"{html.escape(json.dumps(record['source_counts'], sort_keys=True))}</p>"
        f"<p><strong>Normalized class:</strong> "
        f"{html.escape(warning.warning_class.fingerprint)}</p>"
        f"<pre><strong>Representative message:</strong>\n"
        f"{html.escape(warning.warning_class.representative.message)}</pre>"
        '<section class="warning-guidance"><p class="guidance-label">What this means</p>'
        f"<p>{html.escape(explanation)}</p>"
        '<p class="guidance-label">What to check</p>'
        f"<p>{html.escape(action)}</p></section>"
        f"{render_parser_evidence(warning.table_parser_evidence)}"
    )


def render_parser_evidence(evidence: TableParserEvidence | None) -> str:
    """Render compact parser attempts for warning or table evidence."""
    if evidence is None or not evidence.pages:
        return ""
    names = sorted({attempt.parser for page in evidence.pages for attempt in page.attempts})
    open_attribute = " open" if evidence.page_details_open else ""
    pages = "".join(_parser_page(page, open_attribute) for page in evidence.pages)
    return (
        '<section class="parser-guidance">'
        '<p class="guidance-label">Table parser/extractor evidence</p>'
        f"<p>These are the retained attempts for {html.escape(evidence.scope)}. "
        "“Returned” means a parser produced a candidate; “retained” means it survived "
        "the table-stage acceptance and cleanup rules. "
        f"<strong>Parsers represented:</strong> {html.escape(', '.join(names) or 'none')}.</p>"
        f"{pages}</section>"
    )


def _parser_page(page: ParserPageEvidence, open_attribute: str) -> str:
    """Render one physical page of retained parser attempts."""
    selected = (
        ", ".join(f"{name} × {count}" for name, count in page.selected_parser_counts) or "none"
    )
    attempts = "".join(_parser_attempt(attempt) for attempt in page.attempts)
    return (
        f'<details class="parser-page"{open_attribute}><summary>Physical page '
        f"{page.physical_page} · {html.escape(page.route or 'unknown route')}</summary>"
        f"<p><strong>Producer tables:</strong> {page.producer_table_count} · "
        f"<strong>Selected parser output:</strong> {html.escape(selected)}</p>"
        f'<ul class="parser-attempts">{attempts}</ul></details>'
    )


def _parser_attempt(attempt: ParserAttempt) -> str:
    """Render one parser result and its available measurements."""
    labels = {
        "returned": "returned",
        "retained": "retained",
        "matched_regions": "matched regions",
        "region_count": "regions",
        "region_id": "region",
        "predicted_shape": "predicted shape",
        "matched_native_tokens": "matched native tokens",
        "native_tokens": "native tokens",
        "unmatched_leading_tokens": "unmatched leading tokens",
        "reason": "reason",
    }
    details = "; ".join(
        f"{labels.get(key, key.replace('_', ' '))} {value}"
        for key, value in attempt.details.items()
        if value is not None
    )
    return (
        f"<li><strong>{html.escape(attempt.parser)}:</strong> "
        f"{html.escape(attempt.status.replace('_', ' '))}"
        f"{' · ' + html.escape(details) if details else ''}</li>"
    )


def render_page_comparison(path: str, evidence: PageEvidence) -> str:
    """Render source and extracted evidence side by side for a wide display."""
    ordinary = [_block_card(block) for block in evidence.blocks if not block.overlaps_table]
    overlapping = [_block_card(block) for block in evidence.blocks if block.overlaps_table]
    tables = [_table_card(table) for table in evidence.tables]
    parsed = "".join((*tables, *ordinary, _overlap_details(overlapping)))
    if not parsed:
        parsed = '<p class="empty-evidence">No canonical blocks or tables were retained.</p>'
    label = f"Physical page {evidence.physical_page}"
    if evidence.printed_page_label is not None:
        label += f" · printed {html.escape(evidence.printed_page_label)}"
    note = (
        f'<p class="geometry-note">{html.escape(evidence.geometry_note)}</p>'
        if evidence.geometry_note
        else ""
    )
    return (
        '<section class="page-compare"><figure class="page-pane">'
        '<div class="page-canvas">'
        f'<div class="page-surface" style="--page-ratio: '
        f'{evidence.width / evidence.height:.8f}">'
        f'<img loading="lazy" decoding="async" data-src="{html.escape(path)}" '
        f'alt="Rendered physical PDF page {evidence.physical_page}">'
        f'<svg class="page-overlay" viewBox="0 0 {evidence.width:.3f} '
        f'{evidence.height:.3f}" preserveAspectRatio="none">'
        f"{_overlay_rectangles(evidence)}</svg></div></div>"
        f"<figcaption>{label}</figcaption>{_overlay_legend()}</figure>"
        '<section class="parsed-pane"><header class="parsed-header"><div>'
        '<p class="panel-kicker">Parsed evidence</p>'
        f"<h3>{label}</h3></div><span>{len(ordinary)} blocks · {len(tables)} tables</span>"
        f'</header>{note}<div class="parsed-content">{parsed}</div></section></section>'
    )


def _block_card(block: BlockEvidence) -> str:
    """Render one bounded canonical text block."""
    displayed = block.text if len(block.text) <= 1_800 else block.text[:1_799] + "…"
    return (
        f'<section class="block-evidence block-{html.escape(block.block_type)}">'
        f'<header><span class="type-chip">{html.escape(block.block_type)}</span>'
        f"<span>{html.escape(_compact_id(block.identifier))}</span></header>"
        f"<p>{html.escape(displayed)}</p></section>"
    )


def _overlap_details(cards: list[str]) -> str:
    """Group canonical text whose boxes overlap retained table bounds."""
    if not cards:
        return ""
    return (
        '<details class="table-overlap" open><summary>'
        f"{len(cards)} canonical text blocks overlap the table bounds</summary>"
        "<p>These fragments were emitted as standalone document text even though their boxes "
        "fall inside the table region. They may duplicate table-cell content or expose text "
        "that the table grid did not absorb; review them against the source and table.</p>"
        f'<div class="overlap-list">{"".join(cards)}</div></details>'
    )


def _table_card(table: TableEvidence, *, max_rows: int = 24, max_columns: int = 14) -> str:
    """Render a bounded canonical cell grid for source comparison."""
    row_count = table.shape[0] if table.shape else 0
    column_count = table.shape[1] if len(table.shape) > 1 else 0
    shown_rows = min(row_count, max_rows)
    shown_columns = min(column_count, max_columns)
    starts = {
        (
            _json_int(cell.get("row_index"), default=0),
            _json_int(cell.get("column_index"), default=0),
        ): cell
        for cell in table.cells
    }
    rows = _table_rows(starts, shown_rows, shown_columns)
    note = (
        f'<p class="table-note">Showing {shown_rows} of {row_count} rows and '
        f"{shown_columns} of {column_count} columns.</p>"
        if shown_rows < row_count or shown_columns < column_count
        else ""
    )
    return (
        '<section class="table-evidence"><header><div>'
        '<span class="type-chip table-chip">table</span>'
        f"<strong>{html.escape(_compact_id(table.identifier))}</strong></div>"
        f"<span>{html.escape(table.parser or 'unknown parser')} · "
        f"{row_count} × {column_count}</span></header>"
        f'{note}<div class="table-scroll"><table>{"".join(rows)}</table></div></section>'
    )


def _table_rows(
    starts: dict[tuple[int, int], Mapping[str, JsonValue]], rows: int, columns: int
) -> list[str]:
    """Render table rows while respecting bounded row and column spans."""
    covered: set[tuple[int, int]] = set()
    markup: list[str] = []
    for row in range(rows):
        cells: list[str] = []
        for column in range(columns):
            if (row, column) in covered:
                continue
            cell = starts.get((row, column), {})
            row_span = min(max(1, _json_int(cell.get("row_span"), default=1)), rows - row)
            column_span = min(
                max(1, _json_int(cell.get("column_span"), default=1)), columns - column
            )
            covered.update(
                (covered_row, covered_column)
                for covered_row in range(row, row + row_span)
                for covered_column in range(column, column + column_span)
                if (covered_row, covered_column) != (row, column)
            )
            text = str(cell.get("text") or "")
            displayed = text if len(text) <= 800 else text[:799] + "…"
            cells.append(
                f'<td rowspan="{row_span}" colspan="{column_span}">{html.escape(displayed)}</td>'
            )
        markup.append(f"<tr>{''.join(cells)}</tr>")
    return markup


def _overlay_rectangles(evidence: PageEvidence) -> str:
    """Draw canonical block and table regions over the source render."""
    blocks = [_block_rectangle(block, evidence.height) for block in evidence.blocks]
    tables = [_table_rectangle(table, evidence.height) for table in evidence.tables]
    return "".join((*blocks, *tables))


def _block_rectangle(block: BlockEvidence, height: float) -> str:
    """Render one SVG rectangle for valid block geometry."""
    if block.bbox is None:
        return ""
    left, bottom, right, top = block.bbox
    overlay_type = (
        "heading"
        if block.block_type == "heading"
        else "list"
        if block.block_type == "list_item"
        else "text"
    )
    label = f"{block.block_type}: {block.text[:100]}"
    return (
        f'<rect class="overlay-{overlay_type}" x="{left:.3f}" y="{height - top:.3f}" '
        f'width="{max(0.0, right - left):.3f}" height="{max(0.0, top - bottom):.3f}">'
        f"<title>{html.escape(label)}</title></rect>"
    )


def _table_rectangle(table: TableEvidence, height: float) -> str:
    """Render one SVG rectangle for valid table geometry."""
    if table.bbox is None:
        return ""
    left, bottom, right, top = table.bbox
    return (
        f'<rect class="overlay-table" x="{left:.3f}" y="{height - top:.3f}" '
        f'width="{max(0.0, right - left):.3f}" height="{max(0.0, top - bottom):.3f}">'
        f"<title>table: {html.escape(_compact_id(table.identifier))}</title></rect>"
    )


def _overlay_legend() -> str:
    """Return the stable four-class overlay legend."""
    return (
        '<div class="overlay-legend"><span class="legend-text">Text</span>'
        '<span class="legend-heading">Heading</span>'
        '<span class="legend-list">List item</span>'
        '<span class="legend-table">Table</span></div>'
    )


def _compact_id(value: str) -> str:
    """Return the readable terminal component of a canonical identity."""
    return value.rsplit("/", maxsplit=1)[-1]


def _json_int(value: JsonValue, *, default: int) -> int:
    """Read an optional integer-valued presentation field."""
    return value if isinstance(value, int) and not isinstance(value, bool) else default


__all__ = [
    "render_page_comparison",
    "render_parser_evidence",
    "write_review_html",
]
