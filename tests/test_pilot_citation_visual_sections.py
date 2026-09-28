"""Text-only evidence must preserve every visual location without inventing its contents."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from er_commons.pilot_citation_visual_sections import assemble_visual_section, validate_visual_units


@pytest.fixture
def visual_candidate(tmp_path: Path):
    """Create an intact section with text before and after an unreviewed figure."""
    blocks = [
        dict(
            id=i,
            block_type=k,
            canonical_text=t,
            sequence=n,
            content_layer="body",
            section_id="s1" if i != "h2" else "s2",
            document_id="x/document/deir_main",
            regions=[{"page_id": "x/p0001"}],
        )
        for n, (i, k, t) in enumerate(
            [
                ("h1", "heading", "Conclusion"),
                ("b1", "paragraph", "Before figure."),
                ("c1", "caption", "Figure 1: Design"),
                ("b2", "paragraph", "Conditional finding."),
                ("h2", "heading", "Next section"),
            ]
        )
    ]
    sections = [
        dict(
            id="s1",
            document_id="x/document/deir_main",
            heading_block_id="h1",
            section_path_ids=["s1"],
            ordered_child_ids=["h1", "b1", "f1", "c1", "b2"],
        )
    ]
    figures = [
        dict(
            id="f1",
            document_id="x/document/deir_main",
            section_id="s1",
            caption_block_ids=["c1"],
            regions=[{"page_id": "x/p0001"}],
        )
    ]
    files = {}
    for kind, rows in [
        ("blocks", blocks),
        ("sections", sections),
        ("tables", []),
        ("figures", figures),
    ]:
        path = tmp_path / (kind + ".jsonl")
        path.write_text("\n".join(json.dumps(x) for x in rows))
        files[kind] = {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    source = dict(source_id="deir_main", extraction_id="ex", files=files)
    candidates = assemble_visual_section(
        source=source,
        section_id="s1",
        data_root=tmp_path,
        printed_labels_by_page={1: "4-1"},
        metadata={"pdf_url": "http://localhost/source.pdf", "limitations": []},
    )
    return candidates[0], tmp_path


def test_intact_visual_section(visual_candidate):
    """Figure locations remain visible while only source text enters the quote."""
    candidate, root = visual_candidate
    validate_visual_units([candidate], root)
    assert (
        candidate["quote"]
        == "Conclusion\n\nBefore figure.\n\nFigure 1: Design\n\nConditional finding."
    )
    assert [s["kind"] for s in candidate["display_segments"]] == [
        "text",
        "text",
        "figure",
        "text",
        "text",
    ]
    assert candidate["display_segments"][2]["label"] == "Figure — open original PDF"
    assert "not evaluated" not in candidate["quote"]


@pytest.mark.parametrize(
    "change", ["figure_ref", "placeholder", "text", "source", "snapshot", "commentary"]
)
def test_visual_section_rejects_incomplete_or_forged_content(visual_candidate, change):
    """Canonical refs and the display must agree; no silent visual or text omissions."""
    candidate, root = copy.deepcopy(visual_candidate)
    if change == "figure_ref":
        candidate["citation_unit"]["figure_refs"] = []
    elif change == "placeholder":
        candidate["display_segments"].pop(2)
    elif change == "text":
        candidate["anchors"].pop()
    elif change == "source":
        candidate["source_id"] = "other"
    elif change == "snapshot":
        candidate["citation_unit"]["figure_refs"][0]["record"]["caption_block_ids"] = []
    else:
        candidate["quote"] += "\nThis proves the claim."
    with pytest.raises(ValueError):
        validate_visual_units([candidate], root)


def test_visual_section_render_preserves_source_order(visual_candidate):
    """The reviewer sees source text around a figure locator, without audit commentary."""
    from er_commons.pilot_evidence import _source_excerpt_html

    candidate, _ = visual_candidate
    candidate.update(source_url="http://localhost/source.pdf", edition="Draft EIR")
    rendered = _source_excerpt_html(candidate, "E01")
    before = rendered.index("Before figure.")
    figure = rendered.index("Figure — open original PDF")
    after = rendered.index("Conditional finding.")
    assert before < figure < after
    assert "http://localhost/source.pdf#page=1" in rendered
    assert "not evaluated as text evidence" not in rendered
