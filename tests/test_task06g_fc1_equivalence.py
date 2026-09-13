"""Source-free semantic gates for Task 06G's rebuilt-main FC1 replay."""

from __future__ import annotations

from copy import deepcopy

import pytest

from er_commons.document_records.document_references.fc1_equivalence import (
    AcceptedFc1Packet,
    build_fc1_rebuilt_equivalence,
)
from er_commons.document_records.document_references.figure_aliases import (
    FigureAliasValidationInputs,
    build_caption_figure_aliases,
)
from er_commons.document_records.document_references.relinking_config import (
    AcceptedFc1Evidence,
)

OLD = "exv1-" + "1" * 64
QUALIFIED = "figqualv1-" + "2" * 64
BASE = "exv1-" + "3" * 64
REBUILT = "exv1-" + "4" * 64
SOURCE = "deir_main"


def test_rebuilt_fc1_requires_exact_semantic_equivalence() -> None:
    packet, inputs = _packet_and_rebuilt()
    result = build_fc1_rebuilt_equivalence(
        packet=packet,
        inputs=inputs,
        base_structured_candidate_id=BASE,
        correspondence_ref=_correspondence_ref(),
    )
    assert result["status"] == "passed"
    assert result["accepted_semantic_sha256"] == result["rebuilt_semantic_sha256"]
    assert result["figure_4_8_absent"] is True


def test_rebuilt_fc1_rejects_tampered_accepted_decision() -> None:
    packet, inputs = _packet_and_rebuilt()
    qualification = deepcopy(packet.qualification)
    qualification["decisions"][0]["caption_text"] = "tampered"
    with pytest.raises(ValueError, match="FC1 rebuilt qualification differs"):
        build_fc1_rebuilt_equivalence(
            packet=AcceptedFc1Packet(
                packet.selection, packet.identity, qualification, packet.aliases, packet.entries
            ),
            inputs=inputs,
            base_structured_candidate_id=BASE,
            correspondence_ref=_correspondence_ref(),
        )


def test_rebuilt_fc1_rejects_unmapped_namespace() -> None:
    packet, inputs = _packet_and_rebuilt()
    aliases = deepcopy(list(packet.aliases))
    aliases[0]["targets"][0]["target_id"] = "exv1-" + "9" * 64 + "/figure/deir_main/fig000001"
    with pytest.raises(ValueError, match="FC1 rebuilt aliases differs"):
        build_fc1_rebuilt_equivalence(
            packet=AcceptedFc1Packet(
                packet.selection,
                packet.identity,
                packet.qualification,
                tuple(aliases),
                packet.entries,
            ),
            inputs=inputs,
            base_structured_candidate_id=BASE,
            correspondence_ref=_correspondence_ref(),
        )


def test_rebuilt_fc1_rejects_extra_figure_4_8() -> None:
    packet, inputs = _packet_and_rebuilt()
    blocks = deepcopy(list(inputs.upstream_blocks))
    blocks[0]["canonical_text"] = "Figure 4.8: Unexpected target"
    with pytest.raises(ValueError, match="FC1 rebuilt"):
        build_fc1_rebuilt_equivalence(
            packet=packet,
            inputs=FigureAliasValidationInputs(
                **{**inputs.__dict__, "upstream_blocks": tuple(blocks)}
            ),
            base_structured_candidate_id=BASE,
            correspondence_ref=_correspondence_ref(),
        )


def test_rebuilt_fc1_rejects_other_source() -> None:
    packet, inputs = _packet_and_rebuilt()
    with pytest.raises(ValueError, match="main-only"):
        build_fc1_rebuilt_equivalence(
            packet=packet,
            inputs=FigureAliasValidationInputs(
                **{**inputs.__dict__, "source_id": "deir_appendix_a"}
            ),
            base_structured_candidate_id=BASE,
            correspondence_ref=_correspondence_ref(),
        )


def _packet_and_rebuilt() -> tuple[AcceptedFc1Packet, FigureAliasValidationInputs]:
    old_inputs = _inputs(OLD, QUALIFIED)
    accepted = build_caption_figure_aliases(inputs=old_inputs, first_sequence=1)
    selection = AcceptedFc1Evidence.model_validate(
        {
            "qualification_id": QUALIFIED,
            "source_id": SOURCE,
            **{
                f"{role}_ref": _ref(f"06f/{name}")
                for role, name in (
                    ("completion", "completion.json"),
                    ("inventory", "inventory.json"),
                    ("identity", "identity.json"),
                    ("qualification", "qualification.json"),
                    ("figure_aliases", "figure_aliases.jsonl"),
                    ("target_index_entries", "target_index_entries.jsonl"),
                )
            },
        }
    )
    return (
        AcceptedFc1Packet(
            selection=selection,
            identity={"upstream_candidate_id": OLD},
            qualification=accepted.qualification,
            aliases=accepted.aliases,
            entries=tuple(row.as_json() for row in accepted.entries),
        ),
        _inputs(REBUILT, REBUILT),
    )


def _inputs(upstream: str, candidate: str) -> FigureAliasValidationInputs:
    document = f"{upstream}/document/{SOURCE}"
    section = f"{upstream}/section/{SOURCE}/sec000001"
    page = f"{upstream}/page/{SOURCE}/p000001"
    figures: list[dict[str, object]] = []
    images: list[dict[str, object]] = []
    blocks: list[dict[str, object]] = []
    for sequence in range(1, 275):
        figure_id = f"{upstream}/figure/{SOURCE}/fig{sequence:06d}"
        image_id = f"{upstream}/image/{SOURCE}/img{sequence:06d}"
        block_id = f"{upstream}/block/{SOURCE}/blk{sequence:06d}"
        region = {"page_id": page, "bbox": [1, 2, 3, 4]}
        figures.append(
            {
                "id": figure_id,
                "extraction_id": upstream,
                "document_id": document,
                "section_id": section,
                "sequence": sequence,
                "content_layer": "body",
                "is_toc_row": False,
                "semantic_placement": "inherited_nontext",
                "caption_block_ids": [] if 179 <= sequence <= 240 else [block_id],
                "image_ids": [image_id],
                "regions": [region],
            }
        )
        images.append(
            {
                "id": image_id,
                "extraction_id": upstream,
                "document_id": document,
                "sequence": sequence,
                "regions": [region],
            }
        )
        if sequence <= 178 or sequence >= 241:
            marker = f"Figure {sequence}-1: Target" if sequence <= 178 else "Not a figure"
            blocks.append(
                {
                    "id": block_id,
                    "extraction_id": upstream,
                    "document_id": document,
                    "section_id": section,
                    "sequence": sequence,
                    "canonical_text": marker,
                    "block_type": "caption",
                    "content_layer": "body",
                    "is_toc_row": False,
                    "regions": [region],
                }
            )
    return FigureAliasValidationInputs(
        upstream_candidate_id=upstream,
        candidate_id=candidate,
        source_id=SOURCE,
        source_document_id=document,
        upstream_figures=tuple(figures),
        upstream_images=tuple(images),
        upstream_blocks=tuple(blocks),
        upstream_pages=(
            {
                "id": page,
                "extraction_id": upstream,
                "document_id": document,
                "physical_page_number": 1,
                "sequence": 1,
            },
        ),
    )


def _ref(path: str) -> dict[str, object]:
    return {"authority": "artifact_root", "path": path, "sha256": "a" * 64, "byte_size": 1}


def _correspondence_ref() -> dict[str, object]:
    return _ref("replacement/deir_main/support/missing_chapter_correspondence.json")
