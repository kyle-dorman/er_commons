"""Verify and execute the pinned TableFormer fallback with retained evidence."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

import numpy as np
import pypdfium2 as pdfium  # type: ignore[import-untyped]
from PIL import Image

from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.document_parsing.table_reconstruction.learned_table_acceptance import (
    evaluate_prediction,
)
from er_commons.document_parsing.table_reconstruction.learned_table_types import (
    BoundingBox,
    FallbackAttempt,
    JsonObject,
    abstain,
)
from er_commons.document_parsing.table_reconstruction.models import LearnedFallbackConfig


@dataclass(frozen=True)
class RegionInputs:
    """Exact rendered crop and native tokens submitted to TableFormer."""

    crop: Image.Image
    native_tokens: list[JsonObject]


def _native_word_tokens(
    text_page: Any,
    region_bbox: list[float],
    *,
    scale: float,
) -> list[JsonObject]:
    """Build deterministic word-like tokens from PDFium native characters."""
    region_left, region_bottom, region_right, region_top = region_bbox
    tokens: list[JsonObject] = []
    characters: list[tuple[str, BoundingBox]] = []

    def flush_word() -> None:
        if not characters:
            return
        text = "".join(character for character, _box in characters)
        left = min(box[0] for _character, box in characters)
        bottom = min(box[1] for _character, box in characters)
        right = max(box[2] for _character, box in characters)
        top = max(box[3] for _character, box in characters)
        tokens.append(
            {
                "id": len(tokens),
                "text": text,
                "bbox_pdf_points_bottom_left": [left, bottom, right, top],
                "bbox_crop_pixels_top_left": {
                    "l": (left - region_left) * scale,
                    "t": (region_top - top) * scale,
                    "r": (right - region_left) * scale,
                    "b": (region_top - bottom) * scale,
                },
            }
        )
        characters.clear()

    for index in range(text_page.count_chars()):
        character = text_page.get_text_range(index, 1)
        try:
            values = tuple(float(value) for value in text_page.get_charbox(index))
            box = cast(BoundingBox, values)
        except Exception:  # PDFium can expose passive characters without geometry.
            flush_word()
            continue
        left, bottom, right, top = box
        center_x = (left + right) / 2
        center_y = (bottom + top) / 2
        inside = region_left <= center_x <= region_right and region_bottom <= center_y <= region_top
        if not inside or not character or character.isspace():
            flush_word()
            continue
        if characters:
            previous_box = characters[-1][1]
            previous_center_y = (previous_box[1] + previous_box[3]) / 2
            starts_new_word = (
                abs(center_y - previous_center_y) > 2.0 or left + 0.5 < previous_box[2]
            )
            if starts_new_word:
                flush_word()
        characters.append((character, box))
    flush_word()
    return tokens


def _crop_box(
    region_bbox: list[float],
    *,
    page_height: float,
    scale: float,
) -> tuple[int, int, int, int]:
    left, bottom, right, top = region_bbox
    return (
        round(left * scale),
        round((page_height - top) * scale),
        round(right * scale),
        round((page_height - bottom) * scale),
    )


def _read_region_inputs(
    pdf_path: Path,
    *,
    page_number: int,
    page_size: tuple[float, float],
    region_bbox: list[float],
    render_scale: float,
) -> RegionInputs | None:
    """Read native text and render exactly one bounded PDF region."""
    document = pdfium.PdfDocument(pdf_path)
    try:
        page = document[page_number - 1]
        text_page = page.get_textpage()
        try:
            tokens = _native_word_tokens(text_page, region_bbox, scale=render_scale)
        finally:
            text_page.close()
        image = page.render(scale=render_scale, rev_byteorder=True).to_pil().convert("RGB")
        page.close()
    finally:
        document.close()

    page_width, page_height = page_size
    crop_box = _crop_box(region_bbox, page_height=page_height, scale=render_scale)
    rendered_width = round(page_width * render_scale)
    if not (0 <= crop_box[0] < crop_box[2] <= rendered_width):
        return None
    return RegionInputs(image.crop(crop_box), tokens)


def _attempt_record(attempt: FallbackAttempt) -> JsonObject:
    """Return the terminal subset persisted beside retained model evidence."""
    return {
        "region_id": attempt.region_id,
        "status": attempt.status,
        "reason": attempt.reason,
        "measurements": attempt.measurements,
        "accepted_candidate": attempt.candidate is not None,
    }


def _build_predictor(models_root: Path, cpu_threads: int) -> Any:
    """Construct Docling's pinned low-level predictor for one bounded crop."""
    from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
    from docling.datamodel.pipeline_options import TableFormerMode, TableStructureOptions
    from docling.models.stages.table_structure.table_structure_model import TableStructureModel

    stage = TableStructureModel(
        enabled=True,
        artifacts_path=models_root,
        options=TableStructureOptions(
            mode=TableFormerMode.ACCURATE,
            do_cell_matching=True,
        ),
        accelerator_options=AcceleratorOptions(
            device=AcceleratorDevice.CPU,
            num_threads=cpu_threads,
        ),
    )
    return stage.tf_predictor


class VerifiedTableFormerFallback:
    """Lazy accurate-TableFormer service bound to one accepted model inventory."""

    def __init__(
        self,
        *,
        data_root: Path,
        policy: LearnedFallbackConfig,
        predictor_factory: Callable[[Path, int], Any] | None = None,
    ) -> None:
        if not policy.enabled or policy.model_inventory_relative_path is None:
            raise ValueError("learned fallback service requires an enabled policy")
        inventory_path = (data_root / policy.model_inventory_relative_path).resolve()
        inventory = json.loads(inventory_path.read_text())
        table_model = next(
            model for model in inventory["models"] if model["purpose"] == "table_structure"
        )
        if (
            table_model["repository"] != "docling-project/docling-models"
            or table_model["requested_revision"] != "v2.3.0"
        ):
            raise ValueError("model inventory does not contain the accepted TableFormer snapshot")
        for package in ("docling", "docling-ibm-models"):
            if inventory["packages"].get(package) != version(package):
                raise ValueError(f"installed package differs from model inventory: {package}")
        model_root = (
            inventory_path.parent
            / table_model["local_path"]
            / "model_artifacts/tableformer/accurate"
        )
        weights_path = model_root / "tableformer_accurate.safetensors"
        config_path = model_root / "tm_config.json"
        if sha256_file(weights_path) != policy.expected_weights_sha256:
            raise ValueError("accurate TableFormer weights differ from fallback policy")
        if sha256_file(config_path) != policy.expected_model_config_sha256:
            raise ValueError("accurate TableFormer config differs from fallback policy")

        self._policy = policy
        self._models_root = inventory_path.parent / "models"
        self._predictor_factory = predictor_factory or _build_predictor
        self._predictor: Any | None = None
        self.model_identity = {
            "inventory_path": policy.model_inventory_relative_path.as_posix(),
            "inventory_sha256": sha256_file(inventory_path),
            "repository": table_model["repository"],
            "requested_revision": table_model["requested_revision"],
            "resolved_commit": table_model["resolved_commit"],
            "weights_sha256": policy.expected_weights_sha256,
            "model_config_sha256": policy.expected_model_config_sha256,
            "mode": "accurate",
            "device": "cpu",
            "cpu_threads": policy.cpu_threads,
        }

    @property
    def models_root(self) -> Path:
        """Return the verified Docling artifact root used for lazy model loading."""
        return self._models_root

    def _get_predictor(self) -> Any:
        if self._predictor is None:
            self._predictor = self._predictor_factory(
                self._models_root,
                self._policy.cpu_threads,
            )
            if not callable(getattr(self._predictor, "multi_table_predict", None)):
                raise TypeError("TableFormer predictor does not expose multi_table_predict")
        return self._predictor

    def _predict(self, inputs: RegionInputs) -> JsonObject:
        """Run one retained crop while preserving original OTSL row/column IDs."""
        prediction = self._get_predictor().multi_table_predict(
            {
                "width": inputs.crop.width,
                "height": inputs.crop.height,
                "image": np.asarray(inputs.crop),
                "tokens": [
                    {
                        "id": token["id"],
                        "text": token["text"],
                        "bbox": token["bbox_crop_pixels_top_left"],
                    }
                    for token in inputs.native_tokens
                ],
            },
            [[0.0, 0.0, float(inputs.crop.width), float(inputs.crop.height)]],
            do_matching=True,
            sort_row_col_indexes=False,
        )[0]
        if not isinstance(prediction, dict):
            raise TypeError("TableFormer prediction is not an object")
        return prediction

    def __call__(
        self,
        *,
        pdf_path: Path,
        page_number: int,
        page_size: tuple[float, float],
        region_id: str,
        region_bbox: list[float],
        evidence_root: Path,
    ) -> FallbackAttempt:
        """Retain exact inputs and return one accepted candidate or abstention."""
        evidence_root.mkdir(parents=True, exist_ok=False)
        write_json_atomic(
            evidence_root / "trigger.json",
            {
                "trigger": "unmatched_heron_region_after_camelot",
                "physical_pdf_page": page_number,
                "region_id": region_id,
                "region_bbox_pdf_points_bottom_left": region_bbox,
                "model_identity": self.model_identity,
            },
        )
        inputs = _read_region_inputs(
            pdf_path,
            page_number=page_number,
            page_size=page_size,
            region_bbox=region_bbox,
            render_scale=self._policy.render_scale,
        )
        if inputs is None:
            attempt = abstain(region_id, "out_of_bounds_geometry", {})
            write_json_atomic(evidence_root / "acceptance.json", _attempt_record(attempt))
            return attempt
        inputs.crop.save(evidence_root / "crop.png", optimize=False, compress_level=9)
        write_json_atomic(
            evidence_root / "native_tokens.json",
            {"tokens": inputs.native_tokens},
        )
        try:
            prediction_started = time.perf_counter()
            prediction = self._predict(inputs)
            inference_seconds = time.perf_counter() - prediction_started
            write_json_atomic(
                evidence_root / "raw_prediction.json",
                {**prediction, "inference_seconds": inference_seconds},
            )
            attempt = evaluate_prediction(
                region_id=region_id,
                region_bbox=region_bbox,
                crop_size=(inputs.crop.width, inputs.crop.height),
                native_tokens=inputs.native_tokens,
                prediction=prediction,
                policy=self._policy,
            )
        except Exception as error:
            write_json_atomic(
                evidence_root / "model_failure.json",
                {"exception_type": type(error).__name__, "message": str(error)},
            )
            attempt = abstain(region_id, "model_failure", {})
        write_json_atomic(evidence_root / "acceptance.json", _attempt_record(attempt))
        return attempt
