"""Source-free controls for conservative running-header qualification."""

from copy import deepcopy

import pytest

from er_commons.response_inventory.reference_replay_headers import qualify_section_headers


def evidence():
    """Create a synthetic promoted header, genuine opener, and canonical furniture."""
    document = "extract/document/synthetic"
    pages = [
        {
            "id": f"p{n}",
            "document_id": document,
            "physical_page_number": n,
            "width_pdf_points": 612.0,
            "height_pdf_points": 792.0,
            "rotation_degrees": 0,
        }
        for n in (1, 2, 3)
    ]
    region = {
        "page_id": "p1",
        "page_width": 612.0,
        "page_height": 792.0,
        "coordinate_space": "producer_pdf",
        "origin": "bottom_left",
        "units": "pdf_points",
        "rotation_degrees": 0,
        "affine_transform": None,
        "render_scale": None,
        "bbox": [72.0, 740.0, 180.0, 750.0],
    }
    heading = {
        "id": "heading",
        "document_id": document,
        "section_id": "section",
        "block_type": "heading",
        "content_layer": "body",
        "is_toc_row": False,
        "canonical_text": "2.3 PUBLIC SERVICES",
        "regions": [region],
    }
    header = deepcopy(heading)
    header.update(
        id="header",
        block_type="page_header",
        content_layer="furniture",
        canonical_text="2.3  Public\nServices",
        section_id="furniture",
    )
    header["regions"][0]["page_id"] = "p2"
    opener = deepcopy(heading)
    opener.update(id="opener", section_id="genuine")
    opener["regions"][0].update(page_id="p3", bbox=[72.0, 620.0, 260.0, 645.0])
    sections = [
        {"id": sid, "document_id": document, "content_layer": "body", "heading_block_id": bid}
        for sid, bid in (("section", "heading"), ("genuine", "opener"))
    ]
    return dict(
        source_id="synthetic",
        candidate_id="candidate",
        blocks=[heading, header, opener],
        sections=sections,
        pages=pages,
    )


def test_header_qualified_but_genuine_heading_preserved_without_mutation():
    inputs = evidence()
    before = deepcopy(inputs)
    result = qualify_section_headers(**inputs)
    assert set(result) == {"section"}
    assert result["section"]["evidence_record_ids"] == ["header", "heading", "p1", "p2", "section"]
    assert result["section"]["candidate_id"] == "candidate"
    assert result["section"]["corroborating_headers"][0]["block_id"] == "header"
    assert qualify_section_headers(**inputs) == result
    assert inputs == before


@pytest.mark.parametrize("index", [0, 1])
@pytest.mark.parametrize(
    "key,value",
    [
        ("is_toc_row", True),
        ("is_toc_row", None),
        ("document_id", "other/document/synthetic"),
        ("canonical_text", "2.4 Public Services"),
        ("canonical_text", ""),
        ("regions", []),
        ("content_layer", "navigation"),
    ],
)
def test_ineligible_heading_or_corroborator_rejected(index, key, value):
    inputs = evidence()
    inputs["blocks"][index][key] = value
    assert qualify_section_headers(**inputs) == {}


@pytest.mark.parametrize("index", [0, 1])
@pytest.mark.parametrize(
    "key,value",
    [
        ("bbox", [72, 740, 180, float("nan")]),
        ("bbox", [72, 740, 180, float("inf")]),
        ("bbox", [180, 740, 72, 750]),
        ("bbox", [72, 740, 700, 750]),
        ("bbox", [True, 740, 180, 750]),
        ("bbox", [72, 740, 180]),
        ("page_width", float("nan")),
        ("page_height", 800),
        ("rotation_degrees", 90),
        ("origin", "unsupported"),
        ("coordinate_space", "image"),
        ("units", "pixels"),
        ("affine_transform", [1, 0, 0, 1, 0, 0]),
        ("render_scale", 2),
        ("page_id", "missing"),
    ],
)
def test_invalid_geometry_rejected(index, key, value):
    inputs = evidence()
    inputs["blocks"][index]["regions"][0][key] = value
    assert qualify_section_headers(**inputs) == {}


def test_different_coordinate_conventions_and_sizes_not_compared():
    inputs = evidence()
    inputs["blocks"][1]["regions"][0]["origin"] = "top_left"
    assert qualify_section_headers(**inputs) == {}
    inputs = evidence()
    inputs["pages"][1]["width_pdf_points"] = 620
    inputs["blocks"][1]["regions"][0]["page_width"] = 620
    assert qualify_section_headers(**inputs) == {}


def test_one_point_boundary_and_multi_region_rejected():
    inputs = evidence()
    inputs["blocks"][1]["regions"][0]["bbox"][0] += 1
    assert set(qualify_section_headers(**inputs)) == {"section"}
    inputs["blocks"][1]["regions"][0]["bbox"][0] += 0.01
    assert qualify_section_headers(**inputs) == {}
    inputs = evidence()
    inputs["blocks"][0]["regions"] *= 2
    assert qualify_section_headers(**inputs) == {}


def test_same_page_or_same_physical_page_is_not_independent():
    inputs = evidence()
    inputs["blocks"][1]["regions"][0]["page_id"] = "p1"
    assert qualify_section_headers(**inputs) == {}
    inputs = evidence()
    inputs["pages"][1]["physical_page_number"] = 1
    assert qualify_section_headers(**inputs) == {}


@pytest.mark.parametrize("part", ["blocks", "sections", "pages"])
def test_duplicate_ids_raise(part):
    inputs = evidence()
    inputs[part].append(deepcopy(inputs[part][0]))
    with pytest.raises(ValueError, match="duplicate"):
        qualify_section_headers(**inputs)


def test_source_and_section_relationships_required():
    inputs = evidence()
    inputs["source_id"] = "different"
    assert qualify_section_headers(**inputs) == {}
    inputs = evidence()
    inputs["blocks"][0]["section_id"] = "genuine"
    assert qualify_section_headers(**inputs) == {}
    inputs = evidence()
    inputs["sections"][0]["document_id"] = "other/document/synthetic"
    assert qualify_section_headers(**inputs) == {}
