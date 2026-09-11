"""Source-general qualification fixtures for exact caption-backed figure aliases."""

from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import ValidationError

from er_commons.document_records.document_references.figure_aliases import (
    ALIAS_ORIGIN,
    FigureAliasValidationInputs,
    build_caption_figure_aliases,
    parse_leading_figure_marker,
    validate_caption_figure_alias_evidence,
)
from er_commons.document_records.document_references.storage import (
    read_json,
    read_jsonl,
    sha256_file,
    write_json,
    write_jsonl,
)

UPSTREAM = "exv1-" + "1" * 64
CANDIDATE = "exv1-" + "2" * 64
SOURCE = "coastal_report"
ROOT = Path(__file__).parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "qualify_figure_caption_aliases",
    ROOT / "scripts/qualify_figure_caption_aliases.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_QUALIFICATION_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_QUALIFICATION_MODULE)
publish_qualification = _QUALIFICATION_MODULE.publish_qualification
verify_qualification_packet = _QUALIFICATION_MODULE.verify_qualification_packet


@pytest.mark.parametrize(
    ("caption", "expected"),
    [
        ("Figure 4.8-5: Habitat", "figure 4.8-5"),
        ("FIGURE\tES-1 : Location", "figure es-1"),
        ("Figure 9-1a: Detail", "figure 9-1a"),
        ("Figure 4.8-5. Habitat", None),
        ("Figure 4.8-5 - Habitat", None),
        ("Map. Figure 4.8-5: Habitat", None),
        ("Figure 4.8:5: Habitat", "figure 4.8"),
        ("Figure ABC: Habitat", None),
    ],
)
def test_complete_leading_marker_grammar(caption: str, expected: str | None) -> None:
    parsed = parse_leading_figure_marker(caption)
    assert (parsed[1] if parsed is not None else None) == expected


def test_marker_grammar_is_ascii_and_raw_spelling_order_is_total() -> None:
    assert parse_leading_figure_marker("FİGURE 2-1: Unicode lookalike") is None
    records = _records(("2-1", "First"), ("2-1", "Second"))
    records["blocks"][0]["canonical_text"] = "figure 2-1: First"
    records["blocks"][1]["canonical_text"] = "Figure 2-1: Second"
    assert _build(records).aliases[0]["raw_values"] == ["Figure 2-1", "figure 2-1"]


@pytest.mark.parametrize(
    ("caption_text", "reason"),
    [
        ("Map showing Figure 2-1: Habitat", "figure_marker_not_leading"),
        ("FİGURE 2-1: Habitat", "leading_figure_marker_absent_or_invalid"),
        ("Figure ABC: Habitat", "leading_figure_marker_absent_or_invalid"),
        ("Figure 2-1. Habitat", "leading_figure_marker_absent_or_invalid"),
        ("Figure 2-1 - Habitat", "leading_figure_marker_absent_or_invalid"),
    ],
)
def test_invalid_leading_marker_reason_is_not_misclassified_as_later_marker(
    caption_text: str, reason: str
) -> None:
    records = _records(("2-1", "Plan"))
    records["blocks"][0]["canonical_text"] = caption_text
    assert _build(records).qualification["decisions"][0]["reason"] == reason


def test_eligible_alias_retains_attachment_classification_page_and_usability() -> None:
    records = _records(("4.8-5", "Habitat"))

    build = _build(records)

    assert len(build.aliases) == 1
    alias = build.aliases[0]
    assert alias["normalized_alias"] == "figure 4.8-5"
    assert alias["alias_origin"] == ALIAS_ORIGIN
    assert alias["resolution_status"] == "unique"
    target = alias["targets"][0]
    assert target["evidence_physical_page_number"] == 7
    assert target["evidence_image_record_ids"] == [f"{CANDIDATE}/image/{SOURCE}/img000001"]
    assert target["attachment_provenance"]["caption_block_ids"] == [
        f"{CANDIDATE}/block/{SOURCE}/blk000001"
    ]
    assert target["classification_provenance"] == {
        "figure_content_layer": "body",
        "figure_is_toc_row": False,
        "figure_semantic_placement": "inherited_nontext",
        "figure_section_id": f"{CANDIDATE}/section/{SOURCE}/sec000001",
        "caption_section_id": f"{CANDIDATE}/section/{SOURCE}/sec000001",
        "caption_block_type": "caption",
        "caption_content_layer": "body",
        "caption_is_toc_row": False,
    }
    assert target["structural_target_status"] == "eligible"
    assert target["text_only_evidence_status"] == "not_evaluated_pending_task06h"
    assert build.qualification["eligible_figure_count"] == 1
    assert build.qualification["target_edge_count"] == 1
    assert build.qualification["zero_target_figure_count"] == 0
    assert build.qualification["one_target_alias_count"] == 1
    assert build.qualification["multiple_target_alias_count"] == 0


def test_repeated_attachment_evidence_deduplicates_without_losing_counts() -> None:
    records = _records(("2-4a", "Plan"))
    figure = records["figures"][0]
    figure["caption_block_ids"] *= 2
    figure["image_ids"] *= 3

    build = _build(records)

    assert len(build.aliases[0]["targets"]) == 1
    provenance = build.aliases[0]["targets"][0]["attachment_provenance"]
    assert provenance["repeated_caption_reference_count"] == 1
    assert provenance["repeated_image_reference_count"] == 2


def test_same_marker_collision_is_explicit_and_target_deduplicated() -> None:
    records = _records(("3-7", "First"), ("3-7", "Second"))

    build = _build(records)

    assert len(build.aliases) == 1
    assert build.aliases[0]["resolution_status"] == "ambiguous"
    assert len(build.aliases[0]["targets"]) == 2
    assert build.qualification["collision_group_count"] == 1
    assert build.qualification["ambiguous_alias_count"] == 1
    assert build.qualification["target_edge_count"] == 2
    assert build.qualification["multiple_target_alias_count"] == 1


def test_more_specific_markers_never_create_less_specific_target() -> None:
    records = _records(("4.8-5", "First"), ("4.8-8", "Second"))
    build = _build(records)

    assert {entry.lookup_key for entry in build.entries} == {"figure 4.8-5", "figure 4.8-8"}
    assert not [entry for entry in build.entries if entry.lookup_key == "figure 4.8"]


@pytest.mark.parametrize(
    ("mutation", "reason", "eligibility"),
    [
        ("missing_caption", "missing_caption", "rejected"),
        ("missing_image", "missing_image", "rejected"),
        ("dangling_caption", "dangling_caption_attachment", "rejected"),
        ("dangling_image", "dangling_image_attachment", "rejected"),
        ("multiple_captions", "multiple_captions", "review_required"),
        ("multiple_images", "multiple_images", "review_required"),
        ("caption_furniture", "caption_not_body", "rejected"),
        ("caption_toc", "caption_toc_or_unclassified", "rejected"),
        ("figure_furniture", "figure_not_body", "rejected"),
        ("figure_toc", "figure_toc_or_unclassified", "rejected"),
        ("figure_placement", "figure_semantic_placement_unqualified", "rejected"),
        ("later_marker", "figure_marker_not_leading", "rejected"),
        ("cross_document", "cross_document_attachment", "rejected"),
        ("cross_section", "cross_section_attachment", "rejected"),
        ("page_mismatch", "attachment_page_mismatch", "rejected"),
        ("wrong_caption_family", "caption_attachment_wrong_record_family", "rejected"),
        ("wrong_image_family", "image_attachment_wrong_record_family", "rejected"),
        ("wrong_extraction", "attachment_extraction_identity_mismatch", "rejected"),
    ],
)
def test_ineligible_and_unqualified_shapes_are_accounted(
    mutation: str, reason: str, eligibility: str
) -> None:
    records = _records(("7-1", "Map"))
    _mutate(records, mutation)

    build = _build(records)

    assert build.aliases == ()
    decision = build.qualification["decisions"][0]
    assert decision["reason"] == reason
    assert decision["eligibility"] == eligibility
    assert decision["structural_target_status"] == eligibility
    assert decision["text_only_evidence_status"] == "not_evaluated_pending_task06h"


@pytest.mark.parametrize(
    ("shared_family", "reason"),
    [
        ("caption", "caption_attached_to_multiple_figures"),
        ("image", "image_attached_to_multiple_figures"),
    ],
)
def test_shared_attachment_is_rejected_for_every_affected_figure(
    shared_family: str, reason: str
) -> None:
    records = _records(("2-1", "First"), ("2-2", "Second"))
    key = "caption_block_ids" if shared_family == "caption" else "image_ids"
    records["figures"][1][key] = list(records["figures"][0][key])

    build = _build(records)

    reasons = [row["reason"] for row in build.qualification["decisions"]]
    assert reasons.count(reason) == 2


def test_input_order_does_not_affect_aliases() -> None:
    records = _records(("ES-1", "Location"), ("2-1", "Plan"))
    first = _build(records)
    reversed_records = {key: list(reversed(value)) for key, value in records.items()}
    second = _build(reversed_records)

    assert first == second


def test_contradictory_duplicate_records_fail_closed() -> None:
    records = _records(("2-1", "Plan"))
    duplicate = deepcopy(records["images"][0])
    duplicate["sequence"] = 999
    records["images"].append(duplicate)

    with pytest.raises(ValueError, match="contradictory duplicate image"):
        _build(records)


def test_source_document_and_other_source_namespaces_fail_closed() -> None:
    records = _records(("2-1", "Plan"))
    records["images"][0]["id"] = str(records["images"][0]["id"]).replace(
        f"/{SOURCE}/", "/other_report/"
    )
    records["figures"][0]["image_ids"] = [records["images"][0]["id"]]
    decision = _build(records).qualification["decisions"][0]
    assert decision["reason"] == "image_attachment_wrong_record_family"
    with pytest.raises(ValueError, match="source document"):
        build_caption_figure_aliases(
            inputs=FigureAliasValidationInputs(
                upstream_candidate_id=UPSTREAM,
                candidate_id=CANDIDATE,
                source_id=SOURCE,
                source_document_id=f"{UPSTREAM}/document/other_report",
                upstream_figures=(),
                upstream_images=(),
                upstream_blocks=(),
                upstream_pages=(),
            ),
            first_sequence=1,
        )


@pytest.mark.parametrize(
    ("mutation", "diagnostic"),
    [
        ("image", "FC1 aliases differs.*evidence_image_record_ids"),
        ("caption", "FC1 aliases differs.*evidence_source_record_id"),
        ("page", "FC1 target-index entries differs.*evidence_page_id"),
        ("target", "FC1 target-index entries differs.*target_record_id"),
        ("count", "FC1 qualification differs.*target_edge_count"),
    ],
)
def test_semantic_validator_rejects_provenance_and_accounting_mutations(
    mutation: str, diagnostic: str
) -> None:
    records = _records(("2-1", "Plan"))
    build = _build(records)
    aliases = deepcopy(list(build.aliases))
    entries = [entry.as_json() for entry in build.entries]
    qualification = deepcopy(build.qualification)
    if mutation == "image":
        aliases[0]["targets"][0]["evidence_image_record_ids"][0] += "-wrong"
    elif mutation == "caption":
        aliases[0]["targets"][0]["evidence_source_record_id"] += "-wrong"
    elif mutation == "page":
        entries[0]["evidence_page_id"] += "-wrong"
    elif mutation == "target":
        entries[0]["target_record_id"] += "-wrong"
    else:
        qualification["target_edge_count"] = 2
    with pytest.raises(ValueError, match=diagnostic):
        validate_caption_figure_alias_evidence(
            aliases=aliases,
            entries=entries,
            qualification=qualification,
            inputs=_inputs(records),
        )


def test_qualification_packet_is_no_clobber_and_rejects_changed_input_identity(
    tmp_path: Path,
) -> None:
    structured = tmp_path / "structured"
    records = _records(("2-1", "Plan"))
    _write_structured_fixture(structured, records, extraction_id=UPSTREAM)
    output = tmp_path / "qualification-v1"

    publish_qualification(
        structured_root=structured,
        source_id=SOURCE,
        source_document_id=f"{UPSTREAM}/document/{SOURCE}",
        output_root=output,
        repository_root=ROOT,
    )
    with pytest.raises(FileExistsError):
        publish_qualification(
            structured_root=structured,
            source_id=SOURCE,
            source_document_id=f"{UPSTREAM}/document/{SOURCE}",
            output_root=output,
            repository_root=ROOT,
        )
    publish_qualification(
        structured_root=structured,
        source_id=SOURCE,
        source_document_id=f"{UPSTREAM}/document/{SOURCE}",
        output_root=output,
        repository_root=ROOT,
        reuse_existing=True,
    )

    manifest = structured / "records/manifest.json"
    value = __import__("json").loads(manifest.read_text())
    value["extraction_id"] = "exv1-" + "9" * 64
    write_json(manifest, value)
    with pytest.raises(ValueError, match="identity differs"):
        publish_qualification(
            structured_root=structured,
            source_id=SOURCE,
            source_document_id=f"{UPSTREAM}/document/{SOURCE}",
            output_root=output,
            repository_root=ROOT,
            reuse_existing=True,
        )


@pytest.mark.parametrize(
    ("mutation", "exception", "diagnostic"),
    [
        (
            "omission",
            ValueError,
            "managed-file closure differs: missing=.*target_index_entries.jsonl",
        ),
        ("duplicate", ValueError, "inventory must contain exactly four rows"),
        ("qualification", ValueError, "FC1 qualification differs.*target_edge_count"),
        ("alias", ValidationError, "'figure' was expected"),
        ("identity_digest", ValueError, "qualification identity differs.*owned_code_sha256"),
        ("non_fc1", ValueError, "aliases contain a non-FC1 row"),
    ],
)
def test_packet_verifier_rejects_closure_and_semantic_tampering(
    tmp_path: Path,
    mutation: str,
    exception: type[Exception],
    diagnostic: str,
) -> None:
    structured = tmp_path / "structured"
    records = _records(("2-1", "Plan"))
    _write_structured_fixture(structured, records, extraction_id=UPSTREAM)
    output = tmp_path / "qualification"
    document_id = f"{UPSTREAM}/document/{SOURCE}"
    publish_qualification(
        structured_root=structured,
        source_id=SOURCE,
        source_document_id=document_id,
        output_root=output,
        repository_root=ROOT,
    )
    if mutation == "omission":
        (output / "target_index_entries.jsonl").unlink()
    elif mutation == "duplicate":
        inventory = __import__("json").loads((output / "inventory.json").read_text())
        inventory["files"].append(deepcopy(inventory["files"][0]))
        write_json(output / "inventory.json", inventory)
        _reseal_completion(output)
    elif mutation == "qualification":
        qualification = __import__("json").loads((output / "qualification.json").read_text())
        qualification["target_edge_count"] = 2
        write_json(output / "qualification.json", qualification)
        _reseal_inventory_and_completion(output, "qualification.json")
    elif mutation == "identity_digest":
        identity = read_json(output / "identity.json")
        digest_key = next(iter(identity["owned_code_sha256"]))
        identity["owned_code_sha256"][digest_key] = "0" * 64
        write_json(output / "identity.json", identity)
        _reseal_inventory_and_completion(output, "identity.json")
    elif mutation == "non_fc1":
        aliases = read_jsonl(output / "figure_aliases.jsonl")
        entries = read_jsonl(output / "target_index_entries.jsonl")
        extra_alias = deepcopy(aliases[0])
        extra_alias["id"] += "-extra"
        extra_alias["alias_origin"] = "upstream_v2"
        extra_entry = deepcopy(entries[0])
        extra_entry["alias_record_id"] = extra_alias["id"]
        extra_entry["alias_origin"] = "upstream_v2"
        _QUALIFICATION_MODULE._validate_v2_records(
            aliases=[extra_alias],
            entries=[extra_entry],
            qualification=read_json(output / "qualification.json"),
            contract_root=ROOT / "benchmarks/er_bench/schemas/document_linking/v2",
        )
        write_jsonl(output / "figure_aliases.jsonl", [*aliases, extra_alias])
        write_jsonl(output / "target_index_entries.jsonl", [*entries, extra_entry])
        _reseal_inventory_and_completion(output, "figure_aliases.jsonl")
        _reseal_inventory_and_completion(output, "target_index_entries.jsonl")
    else:
        aliases = read_jsonl(output / "figure_aliases.jsonl")
        aliases[0]["alias_kind"] = "section"
        write_jsonl(output / "figure_aliases.jsonl", aliases)
        _reseal_inventory_and_completion(output, "figure_aliases.jsonl")
    with pytest.raises(exception, match=diagnostic):
        verify_qualification_packet(
            output,
            structured_root=structured,
            repository_root=ROOT,
            source_id=SOURCE,
            source_document_id=document_id,
        )


def _reseal_inventory_and_completion(root: Path, relative: str) -> None:
    inventory = read_json(root / "inventory.json")
    for row in inventory["files"]:
        if row["path"] == relative:
            path = root / relative
            row["byte_size"] = path.stat().st_size
            row["sha256"] = sha256_file(path)
    write_json(root / "inventory.json", inventory)
    _reseal_completion(root)


def _reseal_completion(root: Path) -> None:
    completion = read_json(root / "completion.json")
    completion["inventory_sha256"] = sha256_file(root / "inventory.json")
    write_json(root / "completion.json", completion)


def _build(records: dict[str, list[dict[str, object]]]):
    return build_caption_figure_aliases(
        inputs=_inputs(records),
        first_sequence=4,
    )


def _inputs(
    records: dict[str, list[dict[str, object]]],
) -> FigureAliasValidationInputs:
    return FigureAliasValidationInputs(
        upstream_candidate_id=UPSTREAM,
        candidate_id=CANDIDATE,
        source_id=SOURCE,
        source_document_id=f"{UPSTREAM}/document/{SOURCE}",
        upstream_figures=records["figures"],
        upstream_images=records["images"],
        upstream_blocks=records["blocks"],
        upstream_pages=records["pages"],
    )


def _records(*captions: tuple[str, str]) -> dict[str, list[dict[str, object]]]:
    document = f"{UPSTREAM}/document/{SOURCE}"
    section = f"{UPSTREAM}/section/{SOURCE}/sec000001"
    page = f"{UPSTREAM}/page/{SOURCE}/p000007"
    rows: dict[str, list[dict[str, object]]] = {
        "pages": [
            {
                "id": page,
                "extraction_id": UPSTREAM,
                "document_id": document,
                "physical_page_number": 7,
                "sequence": 7,
            }
        ],
        "figures": [],
        "images": [],
        "blocks": [],
    }
    for sequence, (identifier, title) in enumerate(captions, start=1):
        figure_id = f"{UPSTREAM}/figure/{SOURCE}/fig{sequence:06d}"
        image_id = f"{UPSTREAM}/image/{SOURCE}/img{sequence:06d}"
        block_id = f"{UPSTREAM}/block/{SOURCE}/blk{sequence:06d}"
        region = {"page_id": page, "bbox": [1, 2, 3, 4]}
        rows["figures"].append(
            {
                "id": figure_id,
                "extraction_id": UPSTREAM,
                "document_id": document,
                "section_id": section,
                "sequence": sequence,
                "content_layer": "body",
                "is_toc_row": False,
                "semantic_placement": "inherited_nontext",
                "caption_block_ids": [block_id],
                "image_ids": [image_id],
                "regions": [region],
            }
        )
        rows["images"].append(
            {
                "id": image_id,
                "extraction_id": UPSTREAM,
                "document_id": document,
                "sequence": sequence,
                "regions": [region],
            }
        )
        rows["blocks"].append(
            {
                "id": block_id,
                "extraction_id": UPSTREAM,
                "document_id": document,
                "section_id": section,
                "sequence": sequence,
                "canonical_text": f"Figure {identifier}: {title}",
                "block_type": "caption",
                "content_layer": "body",
                "is_toc_row": False,
                "regions": [region],
            }
        )
    return rows


def _mutate(records: dict[str, list[dict[str, object]]], mutation: str) -> None:
    figure, image, caption = records["figures"][0], records["images"][0], records["blocks"][0]
    if mutation == "missing_caption":
        figure["caption_block_ids"] = []
    elif mutation == "missing_image":
        figure["image_ids"] = []
    elif mutation == "dangling_caption":
        records["blocks"] = []
    elif mutation == "dangling_image":
        records["images"] = []
    elif mutation == "multiple_captions":
        figure["caption_block_ids"] = [
            *figure["caption_block_ids"],
            f"{UPSTREAM}/block/{SOURCE}/other",
        ]
    elif mutation == "multiple_images":
        figure["image_ids"] = [*figure["image_ids"], f"{UPSTREAM}/image/{SOURCE}/other"]
    elif mutation == "caption_furniture":
        caption["content_layer"] = "furniture"
    elif mutation == "caption_toc":
        caption["is_toc_row"] = True
    elif mutation == "figure_furniture":
        figure["content_layer"] = "furniture"
    elif mutation == "figure_toc":
        figure["is_toc_row"] = True
    elif mutation == "figure_placement":
        figure["semantic_placement"] = "toc_content"
    elif mutation == "later_marker":
        caption["canonical_text"] = "Map showing Figure 7-1: Habitat"
    elif mutation == "cross_document":
        caption["document_id"] = f"{UPSTREAM}/document/other_report"
    elif mutation == "cross_section":
        caption["section_id"] = f"{UPSTREAM}/section/{SOURCE}/sec999999"
    elif mutation == "page_mismatch":
        image["regions"] = [{"page_id": f"{UPSTREAM}/page/{SOURCE}/p000008"}]
    elif mutation == "wrong_caption_family":
        figure["caption_block_ids"] = [
            str(figure["caption_block_ids"][0]).replace("/block/", "/table/")
        ]
    elif mutation == "wrong_image_family":
        figure["image_ids"] = [str(figure["image_ids"][0]).replace("/image/", "/asset/")]
    elif mutation == "wrong_extraction":
        image["extraction_id"] = "exv1-" + "9" * 64
    else:  # pragma: no cover - fixture contract
        raise AssertionError(mutation)


def _write_structured_fixture(
    root: Path,
    records: dict[str, list[dict[str, object]]],
    *,
    extraction_id: str,
) -> None:
    paths = {
        "pages": "canonical/pages.jsonl",
        "blocks": "canonical/blocks.jsonl",
        "figures": "canonical/figures.jsonl",
        "images": "canonical/images.jsonl",
    }
    record_files = []
    inventory_files = []
    for name, relative in paths.items():
        path = root / relative
        write_jsonl(path, records[name])
        digest = sha256_file(path)
        record_files.append(
            {
                "path": relative,
                "record_type": name,
                "record_count": len(records[name]),
                "sha256": digest,
            }
        )
        inventory_files.append(
            {"path": relative, "byte_size": path.stat().st_size, "sha256": digest}
        )
    write_json(
        root / "records/manifest.json",
        {"extraction_id": extraction_id, "record_files": record_files},
    )
    write_json(
        root / "records/artifact_inventory.json",
        {"files": inventory_files},
    )
    write_json(
        root / "records/completion_record.json",
        {
            "status": "complete",
            "artifact_inventory_sha256": sha256_file(root / "records/artifact_inventory.json"),
        },
    )
