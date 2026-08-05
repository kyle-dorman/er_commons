from __future__ import annotations

import copy
import hashlib
import json
from importlib.metadata import version
from pathlib import Path

import pytest
from pydantic import ValidationError

from er_commons.canonical_extraction.tables import clean_table_cells
from er_commons.table_extraction.learned_fallback import (
    VerifiedTableFormerFallback,
    evaluate_prediction,
    unmatched_layout_regions,
)
from er_commons.table_extraction.models import LearnedFallbackConfig
from er_commons.table_extraction.page import column_type_signatures


def policy(**changes: object) -> LearnedFallbackConfig:
    values: dict[str, object] = {
        "enabled": False,
        "minimum_native_text_coverage": 0.9,
        "maximum_bbox_overshoot_pixels": 3.0,
    }
    values.update(changes)
    return LearnedFallbackConfig.model_validate(values)


TOKENS = [
    {"id": 1, "text": "Header"},
    {"id": 2, "text": "Value"},
    {"id": 3, "text": "Alpha"},
    {"id": 4, "text": "1"},
]


def valid_prediction() -> dict[str, object]:
    return {
        "predict_details": {
            "num_rows": 2,
            "num_cols": 2,
            "prediction": {"rs_seq": ["ched", "lcel", "nl", "fcel", "fcel", "nl"]},
            "prediction_bboxes_page": [
                [0.0, 0.0, 200.0, 40.0],
                [0.0, 40.0, 100.0, 100.0],
                [100.0, 40.0, 200.0, 100.0],
            ],
        },
        "tf_responses": [
            {
                "start_row_offset_idx": 0,
                "end_row_offset_idx": 1,
                "start_col_offset_idx": 0,
                "end_col_offset_idx": 2,
                "bbox": {"l": 0.0, "t": 0.0, "r": 200.0, "b": 40.0},
                "text": "Header Value",
                "column_header": True,
            },
            {
                "start_row_offset_idx": 1,
                "end_row_offset_idx": 2,
                "start_col_offset_idx": 0,
                "end_col_offset_idx": 1,
                "bbox": {"l": 0.0, "t": 40.0, "r": 100.0, "b": 100.0},
                "text": "Alpha",
            },
            {
                "start_row_offset_idx": 1,
                "end_row_offset_idx": 2,
                "start_col_offset_idx": 1,
                "end_col_offset_idx": 2,
                "bbox": {"l": 100.0, "t": 40.0, "r": 200.0, "b": 100.0},
                "text": "1",
            },
        ],
    }


def evaluate(prediction: dict[str, object], tokens: list[dict[str, object]] = TOKENS):
    return evaluate_prediction(
        region_id="layout_001",
        region_bbox=[10.0, 20.0, 110.0, 70.0],
        crop_size=(200, 100),
        native_tokens=tokens,
        prediction=prediction,
        policy=policy(),
    )


def test_accepts_source_faithful_span_grid_and_preserves_logical_cells() -> None:
    attempt = evaluate(valid_prediction())

    assert attempt.status == "accepted"
    assert attempt.reason is None
    assert attempt.measurements["native_text_coverage"] == 1.0
    assert attempt.candidate is not None
    assert attempt.candidate["parser"] == "tableformer_accurate"
    assert attempt.candidate["raw_rows"] == [["Header Value", ""], ["Alpha", "1"]]
    assert len(attempt.candidate["logical_cells"]) == 3
    assert attempt.candidate["logical_cells"][0]["column_span"] == 2
    persisted = attempt.candidate["serialized_cells"]
    assert len(persisted) == 3
    assert persisted[0]["start_col_offset_idx"] == 0
    assert persisted[0]["end_col_offset_idx"] == 2
    assert attempt.candidate["columns_pdf_points"] == [
        {"left": 10.0, "right": 60.0},
        {"left": 60.0, "right": 110.0},
    ]


def test_accepts_only_explicit_otsl_empty_positions_without_inventing_text() -> None:
    prediction = valid_prediction()
    prediction["predict_details"]["prediction"]["rs_seq"][-2] = "ecel"
    prediction["tf_responses"] = prediction["tf_responses"][:-1]

    attempt = evaluate(prediction, TOKENS[:-1])

    assert attempt.status == "accepted"
    assert attempt.measurements["otsl_empty_cell_count"] == 1
    assert attempt.candidate is not None
    empty = attempt.candidate["logical_cells"][-1]
    assert empty["text"] == ""
    assert empty["cell_source"] == "otsl_empty"


def test_accepts_source_text_matched_into_an_initially_empty_otsl_cell() -> None:
    prediction = valid_prediction()
    prediction["predict_details"]["prediction"]["rs_seq"][-2] = "ecel"

    attempt = evaluate(prediction)

    assert attempt.status == "accepted"
    assert attempt.candidate is not None
    assert attempt.candidate["logical_cells"][-1]["text"] == "1"
    assert attempt.candidate["logical_cells"][-1]["cell_source"] == "matched_native_text"


def test_clamps_only_bounded_model_bbox_rounding_overshoot() -> None:
    prediction = valid_prediction()
    prediction["predict_details"]["prediction_bboxes_page"][0] = [
        -2.0,
        0.0,
        202.0,
        40.0,
    ]

    attempt = evaluate(prediction)

    assert attempt.status == "accepted"
    assert attempt.measurements["maximum_bbox_overshoot_pixels"] == 2.0
    assert attempt.candidate is not None
    assert attempt.candidate["logical_cells"][0]["bbox_pdf_points_bottom_left"] == [
        10.0,
        50.0,
        110.0,
        70.0,
    ]


def test_uses_original_otsl_grid_when_matched_columns_are_compressed() -> None:
    tokens = [
        {"id": 0, "text": "Left"},
        {"id": 1, "text": "Right"},
    ]
    prediction = {
        "predict_details": {
            # TableFormer derives these counts from matched columns after removing gaps.
            "num_rows": 1,
            "num_cols": 2,
            "prediction": {"rs_seq": ["fcel", "fcel", "fcel", "nl"]},
            "prediction_bboxes_page": [
                [0.0, 0.0, 60.0, 100.0],
                [60.0, 0.0, 140.0, 100.0],
                [140.0, 0.0, 200.0, 100.0],
            ],
            "pdf_cells": [
                {"id": 0, "text": "Left", "bbox": [0.0, 0.0, 50.0, 20.0]},
                {"id": 1, "text": "Right", "bbox": [150.0, 0.0, 200.0, 20.0]},
            ],
            "docling_responses": [
                {
                    "cell_id": 0,
                    "start_row_offset_idx": 0,
                    "end_row_offset_idx": 1,
                    "start_col_offset_idx": 0,
                    "end_col_offset_idx": 1,
                },
                {
                    "cell_id": 1,
                    "start_row_offset_idx": 0,
                    "end_row_offset_idx": 1,
                    "start_col_offset_idx": 2,
                    "end_col_offset_idx": 3,
                },
            ],
        },
        # Returned responses have compressed indexes; evaluation must not use them.
        "tf_responses": [
            {
                "start_row_offset_idx": 0,
                "end_row_offset_idx": 1,
                "start_col_offset_idx": 0,
                "end_col_offset_idx": 1,
                "text": "Left",
            },
            {
                "start_row_offset_idx": 0,
                "end_row_offset_idx": 1,
                "start_col_offset_idx": 1,
                "end_col_offset_idx": 2,
                "text": "Right",
            },
        ],
    }

    attempt = evaluate_prediction(
        region_id="layout_001",
        region_bbox=[10.0, 20.0, 110.0, 70.0],
        crop_size=(200, 100),
        native_tokens=tokens,
        prediction=prediction,
        policy=policy(minimum_rows=1),
    )

    assert attempt.status == "accepted"
    assert attempt.measurements["predicted_columns"] == 2
    assert attempt.measurements["otsl_columns"] == 3
    assert attempt.measurements["otsl_unmatched_cell_count"] == 1
    assert attempt.candidate is not None
    assert attempt.candidate["raw_rows"] == [["Left", "", "Right"]]
    assert attempt.candidate["logical_cells"][1]["cell_source"] == "otsl_unmatched"


def test_recovers_only_uniquely_contained_unmatched_native_tokens() -> None:
    tokens = [
        {
            "id": 0,
            "text": "Left",
            "bbox_crop_pixels_top_left": {"l": 5.0, "t": 10.0, "r": 50.0, "b": 30.0},
        },
        {
            "id": 1,
            "text": "Right",
            "bbox_crop_pixels_top_left": {
                "l": 150.0,
                "t": 10.0,
                "r": 195.0,
                "b": 30.0,
            },
        },
    ]
    prediction = {
        "predict_details": {
            "num_rows": 1,
            "num_cols": 3,
            "prediction": {"rs_seq": ["fcel", "ecel", "fcel", "nl"]},
            "prediction_bboxes_page": [
                [0.0, 0.0, 60.0, 100.0],
                [60.0, 0.0, 140.0, 100.0],
                [140.0, 0.0, 200.0, 100.0],
            ],
            "pdf_cells": [
                {"id": 0, "text": "Left", "bbox": [5.0, 10.0, 50.0, 30.0]},
                {"id": 1, "text": "Right", "bbox": [150.0, 10.0, 195.0, 30.0]},
            ],
            "docling_responses": [
                {
                    "cell_id": 0,
                    "start_row_offset_idx": 0,
                    "end_row_offset_idx": 1,
                    "start_col_offset_idx": 0,
                    "end_col_offset_idx": 1,
                }
            ],
        },
        "tf_responses": [],
    }

    attempt = evaluate_prediction(
        region_id="layout_001",
        region_bbox=[10.0, 20.0, 110.0, 70.0],
        crop_size=(200, 100),
        native_tokens=tokens,
        prediction=prediction,
        policy=policy(minimum_rows=1),
    )

    assert attempt.status == "accepted"
    assert attempt.measurements["tableformer_matched_native_token_count"] == 1
    assert attempt.measurements["geometry_recovered_native_token_count"] == 1
    assert attempt.candidate is not None
    assert attempt.candidate["raw_rows"] == [["Left", "", "Right"]]


def test_abstains_when_printed_leading_text_is_absent_from_the_grid() -> None:
    labels = ["Header A", "Header B", "Body A", "Body B", "Missing Header"]
    boxes = [
        [0.0, 0.0, 80.0, 30.0],
        [120.0, 0.0, 200.0, 30.0],
        [0.0, 60.0, 80.0, 100.0],
        [120.0, 60.0, 200.0, 100.0],
        [85.0, 40.0, 115.0, 50.0],
    ]
    tokens = [
        {
            "id": index,
            "text": text,
            "bbox_crop_pixels_top_left": {
                "l": box[0],
                "t": box[1],
                "r": box[2],
                "b": box[3],
            },
        }
        for index, (text, box) in enumerate(zip(labels, boxes, strict=True))
    ]
    prediction = {
        "predict_details": {
            "num_rows": 2,
            "num_cols": 2,
            "prediction": {"rs_seq": ["ched", "ched", "nl", "fcel", "fcel", "nl"]},
            "prediction_bboxes_page": boxes[:4],
            "pdf_cells": [
                {"id": index, "text": text, "bbox": box}
                for index, (text, box) in enumerate(zip(labels, boxes, strict=True))
            ],
            "docling_responses": [
                {
                    "cell_id": index,
                    "start_row_offset_idx": index // 2,
                    "end_row_offset_idx": index // 2 + 1,
                    "start_col_offset_idx": index % 2,
                    "end_col_offset_idx": index % 2 + 1,
                }
                for index in range(4)
            ],
        },
        "tf_responses": [],
    }

    attempt = evaluate_prediction(
        region_id="layout_001",
        region_bbox=[10.0, 20.0, 110.0, 70.0],
        crop_size=(200, 100),
        native_tokens=tokens,
        prediction=prediction,
        policy=policy(),
    )

    assert attempt.status == "abstained"
    assert attempt.reason == "unmatched_leading_text"
    assert attempt.measurements["unmatched_leading_token_count"] == 1


def test_excludes_one_clipped_top_line_above_the_structural_grid() -> None:
    labels = ["Caption", "or", "Header A", "Header B", "Body A", "Body B"]
    boxes = [
        [20.0, -2.0, 80.0, 14.0],
        [85.0, 3.5, 105.0, 13.0],
        [0.0, 20.0, 80.0, 45.0],
        [120.0, 20.0, 200.0, 45.0],
        [0.0, 60.0, 80.0, 100.0],
        [120.0, 60.0, 200.0, 100.0],
    ]
    tokens = [
        {
            "id": index,
            "text": text,
            "bbox_crop_pixels_top_left": {
                "l": box[0],
                "t": box[1],
                "r": box[2],
                "b": box[3],
            },
        }
        for index, (text, box) in enumerate(zip(labels, boxes, strict=True))
    ]
    prediction = {
        "predict_details": {
            "num_rows": 2,
            "num_cols": 2,
            "prediction": {"rs_seq": ["ched", "ched", "nl", "fcel", "fcel", "nl"]},
            "prediction_bboxes_page": boxes[2:],
            "pdf_cells": [
                {"id": index, "text": text, "bbox": box}
                for index, (text, box) in enumerate(zip(labels, boxes, strict=True))
            ],
            "docling_responses": [
                {
                    "cell_id": index,
                    "start_row_offset_idx": (index - 2) // 2,
                    "end_row_offset_idx": (index - 2) // 2 + 1,
                    "start_col_offset_idx": (index - 2) % 2,
                    "end_col_offset_idx": (index - 2) % 2 + 1,
                }
                for index in range(2, 6)
            ],
        },
        "tf_responses": [],
    }

    attempt = evaluate_prediction(
        region_id="layout_001",
        region_bbox=[10.0, 20.0, 110.0, 70.0],
        crop_size=(200, 100),
        native_tokens=tokens,
        prediction=prediction,
        policy=policy(),
    )

    assert attempt.status == "accepted"
    assert attempt.measurements["top_boundary_fringe_native_token_ids"] == [0, 1]
    assert attempt.measurements["native_text_coverage"] == 1.0


def test_abstains_when_structural_column_geometry_reverses() -> None:
    prediction = {
        "predict_details": {
            "num_rows": 1,
            "num_cols": 2,
            "prediction": {"rs_seq": ["fcel", "fcel", "nl"]},
            "prediction_bboxes_page": [
                [120.0, 0.0, 180.0, 100.0],
                [20.0, 0.0, 100.0, 100.0],
            ],
        },
        "tf_responses": [
            {
                "start_row_offset_idx": 0,
                "end_row_offset_idx": 1,
                "start_col_offset_idx": 0,
                "end_col_offset_idx": 1,
                "text": "Left",
            },
            {
                "start_row_offset_idx": 0,
                "end_row_offset_idx": 1,
                "start_col_offset_idx": 1,
                "end_col_offset_idx": 2,
                "text": "Right",
            },
        ],
    }

    attempt = evaluate_prediction(
        region_id="layout_001",
        region_bbox=[10.0, 20.0, 110.0, 70.0],
        crop_size=(200, 100),
        native_tokens=[{"id": 0, "text": "Left"}, {"id": 1, "text": "Right"}],
        prediction=prediction,
        policy=policy(minimum_rows=1),
    )

    assert attempt.status == "abstained"
    assert attempt.reason == "non_monotonic_grid_geometry"


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (
            lambda value: value["predict_details"].update(
                {"prediction": {"rs_seq": ["ched", "nl", "fcel", "fcel", "nl"]}}
            ),
            "invalid_otsl",
        ),
        (
            lambda value: value["tf_responses"][1].update(
                {"start_col_offset_idx": 0, "end_col_offset_idx": 2}
            ),
            "invalid_grid_coverage",
        ),
        (
            lambda value: value["predict_details"]["prediction_bboxes_page"].__setitem__(
                0, [-4.0, 0.0, 200.0, 40.0]
            ),
            "out_of_bounds_geometry",
        ),
        (
            lambda value: value["tf_responses"][2].update({"text": "111"}),
            "duplicate_native_text",
        ),
    ],
)
def test_abstains_on_invalid_or_unfaithful_predictions(mutate, reason: str) -> None:
    prediction = copy.deepcopy(valid_prediction())
    mutate(prediction)

    attempt = evaluate(prediction)

    assert attempt.status == "abstained"
    assert attempt.reason == reason
    assert attempt.candidate is None


def test_abstains_when_prediction_drops_too_much_native_text() -> None:
    prediction = valid_prediction()
    prediction["tf_responses"][0]["text"] = "Header"

    attempt = evaluate(prediction)

    assert attempt.status == "abstained"
    assert attempt.reason == "native_text_coverage_below_threshold"


def test_only_unmatched_camelot_regions_enter_fallback() -> None:
    regions = [
        {"region_id": "layout_001", "bbox_pdf_points_bottom_left": [0, 0, 10, 10]},
        {"region_id": "layout_002", "bbox_pdf_points_bottom_left": [10, 0, 20, 10]},
    ]
    evidence = {
        "region_matches": [
            {"region_id": "layout_001", "matched": True},
            {"region_id": "layout_002", "matched": False},
        ]
    }

    assert unmatched_layout_regions(evidence, regions) == [regions[1]]


def test_enabled_policy_requires_exact_model_identity() -> None:
    with pytest.raises(ValidationError, match="exact model inventory and hashes"):
        LearnedFallbackConfig(enabled=True)


def test_raw_column_type_signatures_retain_counts_and_fractions() -> None:
    signatures = column_type_signatures(
        [
            ["Name", "Value", "", "—"],
            ["Alpha", "1", "", "-"],
            ["Beta", "2.5", "note", "–"],
        ]
    )

    assert [item["dominant_type"] for item in signatures] == [
        "text",
        "numeric",
        "empty",
        "missing",
    ]
    assert signatures[1]["counts"] == {
        "text": 1,
        "numeric": 2,
        "missing": 0,
        "empty": 0,
    }
    assert signatures[2]["fractions"]["empty"] == pytest.approx(2 / 3)
    assert signatures[3]["counts"]["missing"] == 3


def test_canonical_loader_preserves_logical_spans_without_continuation_cells() -> None:
    candidate = evaluate(valid_prediction()).candidate
    assert candidate is not None

    cells = clean_table_cells(
        candidate["serialized_cells"],
        shape_raw=(2, 2),
        shape_clean=(2, 2),
        cleanup={
            "removed_footer_row_indices": [],
            "removed_filename_row_indices": [],
            "retained_column_indices": [0, 1],
            "effective_column_count": 2,
        },
        table_id="learned_t001",
    )

    assert len(cells) == 3
    assert (cells[0].row_index, cells[0].column_index) == (0, 0)
    assert (cells[0].row_end, cells[0].column_end) == (1, 2)


def test_verified_service_uses_inventory_parent_as_docling_artifacts_root(
    tmp_path: Path,
) -> None:
    inventory_root = tmp_path / "pipelines/models"
    accurate_root = (
        inventory_root
        / "models/docling-project--docling-models/model_artifacts/tableformer/accurate"
    )
    accurate_root.mkdir(parents=True)
    weights = accurate_root / "tableformer_accurate.safetensors"
    model_config = accurate_root / "tm_config.json"
    weights.write_bytes(b"weights")
    model_config.write_text("{}")
    inventory = {
        "models": [
            {
                "purpose": "table_structure",
                "repository": "docling-project/docling-models",
                "requested_revision": "v2.3.0",
                "resolved_commit": "abc123",
                "local_path": "models/docling-project--docling-models",
            }
        ],
        "packages": {
            "docling": version("docling"),
            "docling-ibm-models": version("docling-ibm-models"),
        },
    }
    inventory_path = inventory_root / "model_inventory.json"
    inventory_path.write_text(json.dumps(inventory))
    service = VerifiedTableFormerFallback(
        data_root=tmp_path,
        policy=LearnedFallbackConfig(
            enabled=True,
            model_inventory_relative_path=inventory_path.relative_to(tmp_path),
            expected_weights_sha256=hashlib.sha256(b"weights").hexdigest(),
            expected_model_config_sha256=hashlib.sha256(b"{}").hexdigest(),
        ),
        predictor_factory=lambda _root, _threads: object(),
    )

    assert service.models_root == inventory_root / "models"
    with pytest.raises(TypeError, match="multi_table_predict"):
        service._get_predictor()
