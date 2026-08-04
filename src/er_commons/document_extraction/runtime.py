"""Construct and measure the exact accepted native-only Docling runtime."""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.metadata import version
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from er_commons.document_extraction.producer_config import HeadingHierarchyConfig
from er_commons.source_freeze import sha256_file

PACKAGE_NAMES = (
    "docling",
    "docling-core",
    "docling-parse",
    "docling-ibm-models",
    "huggingface-hub",
    "pypdf",
    "torch",
)


@contextmanager
def offline_docling_environment() -> Iterator[None]:
    """Apply offline guards for one producer invocation and restore process state."""
    names = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
    previous = {name: os.environ.get(name) for name in names}
    os.environ.update({name: "1" for name in names})
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


@contextmanager
def run_log(path: Path) -> Iterator[None]:
    """Capture producer logs and always detach and close the temporary handler."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root_logger = logging.getLogger()
    previous_level = root_logger.level
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    try:
        yield
    finally:
        root_logger.removeHandler(handler)
        root_logger.setLevel(previous_level)
        handler.close()


class ModelFile(BaseModel):
    """One recorded file in an immutable model snapshot."""

    path: str
    sha256: str
    byte_size: int


class ModelRecord(BaseModel):
    """One model snapshot in the accepted Task 03A inventory."""

    purpose: str
    repository: str
    requested_revision: str
    resolved_commit: str
    local_path: str
    license: str | None
    license_reference: str
    byte_size: int
    files: list[ModelFile]


class ModelInventory(BaseModel):
    """Accepted model and package identities."""

    schema_version: str
    generated_at_utc: str
    models: list[ModelRecord]
    packages: dict[str, str]


def verify_model_inventory(
    data_root: Path,
    inventory_path: Path,
) -> tuple[ModelInventory, Path]:
    """Verify every recorded model file and installed package version."""
    inventory = ModelInventory.model_validate_json(inventory_path.read_bytes())
    expected_models = {
        ("layout", "docling-project/docling-layout-heron", "main"),
        ("table_structure", "docling-project/docling-models", "v2.3.0"),
    }
    actual_models = {
        (model.purpose, model.repository, model.requested_revision) for model in inventory.models
    }
    if actual_models != expected_models:
        raise ValueError("model inventory does not match the accepted model set")
    for package in PACKAGE_NAMES:
        if inventory.packages.get(package) != version(package):
            raise ValueError(f"installed package differs from model inventory: {package}")

    inventory_root = inventory_path.parent.resolve()
    for model in inventory.models:
        model_root = (inventory_root / model.local_path).resolve()
        if not model_root.is_relative_to(data_root.resolve()):
            raise ValueError("model snapshot escapes ER_COMMONS_DATA_ROOT")
        total = 0
        for recorded in model.files:
            path = (model_root / recorded.path).resolve()
            if not path.is_relative_to(model_root):
                raise ValueError("model file escapes its snapshot")
            if not path.is_file():
                raise FileNotFoundError(path)
            if path.stat().st_size != recorded.byte_size or sha256_file(path) != recorded.sha256:
                raise ValueError(f"model file differs from inventory: {path}")
            total += recorded.byte_size
        if total != model.byte_size:
            raise ValueError(f"model byte total differs from inventory: {model.repository}")
    return inventory, inventory_root / "models"


def build_converter(
    models_root: Path,
    *,
    thread_count: int,
    heading_hierarchy_options: HeadingHierarchyConfig | None = None,
) -> tuple[Any, Any, Any]:
    """Build the one accepted local, native-text-only Docling converter."""
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.layout_model_specs import DOCLING_LAYOUT_HERON
    from docling.datamodel.pipeline_options import (
        HeadingHierarchyOptions,
        LayoutOptions,
        ThreadedPdfPipelineOptions,
    )
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

    options = ThreadedPdfPipelineOptions(
        accelerator_options=AcceleratorOptions(
            device=AcceleratorDevice.CPU,
            num_threads=thread_count,
        ),
        artifacts_path=models_root,
        enable_remote_services=False,
        allow_external_plugins=False,
        do_picture_classification=False,
        do_picture_description=False,
        do_chart_extraction=False,
        do_table_structure=False,
        do_ocr=False,
        do_code_enrichment=False,
        do_formula_enrichment=False,
        force_backend_text=False,
        generate_page_images=True,
        generate_picture_images=True,
        generate_parsed_pages=True,
        images_scale=2.0,
        layout_options=LayoutOptions(model_spec=DOCLING_LAYOUT_HERON),
        heading_hierarchy_options=HeadingHierarchyOptions(**heading_hierarchy_options.model_dump())
        if heading_hierarchy_options is not None
        else HeadingHierarchyOptions(),
    )
    format_option = PdfFormatOption(
        pipeline_cls=StandardPdfPipeline,
        backend=PyPdfiumDocumentBackend,
        pipeline_options=options,
    )
    assert_native_only(options, format_option, models_root)
    converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={InputFormat.PDF: format_option},
    )
    return converter, options, format_option


def assert_native_only(options: Any, format_option: Any, models_root: Path) -> None:
    """Fail closed if the accepted Task 03A configuration drifts."""
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

    forbidden = {
        "do_ocr": options.do_ocr,
        "enable_remote_services": options.enable_remote_services,
        "allow_external_plugins": options.allow_external_plugins,
        "do_picture_classification": options.do_picture_classification,
        "do_picture_description": options.do_picture_description,
        "do_chart_extraction": options.do_chart_extraction,
        "do_code_enrichment": options.do_code_enrichment,
        "do_formula_enrichment": options.do_formula_enrichment,
    }
    enabled = [name for name, value in forbidden.items() if value]
    if enabled:
        raise ValueError(f"forbidden document-extraction options enabled: {enabled}")
    if options.do_table_structure:
        raise ValueError("TableFormer must remain disabled; the clean table pipeline owns tables")
    if Path(options.artifacts_path).resolve() != models_root.resolve():
        raise ValueError("Docling artifacts path differs from the verified model root")
    if format_option.pipeline_cls is not StandardPdfPipeline:
        raise ValueError("document extraction requires StandardPdfPipeline")
    if format_option.backend is not PyPdfiumDocumentBackend:
        raise ValueError("document extraction requires PyPdfiumDocumentBackend")


def configuration_record(configuration_id: str, options: Any, format_option: Any) -> dict[str, Any]:
    """Serialize the effective runtime rather than relying on defaults."""
    return {
        "configuration_id": configuration_id,
        "package_versions": {package: version(package) for package in PACKAGE_NAMES},
        "pipeline_class": (
            f"{format_option.pipeline_cls.__module__}.{format_option.pipeline_cls.__name__}"
        ),
        "backend_class": f"{format_option.backend.__module__}.{format_option.backend.__name__}",
        "effective_options": options.model_dump(mode="json", serialize_as_any=True),
        "project_owned_llm_repair": False,
        "offline_environment": {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
        },
    }


class MemorySampler:
    """Sample process RSS while one in-process conversion runs."""

    def __init__(self) -> None:
        import psutil  # type: ignore[import-untyped]

        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._sample, daemon=True)
        self.peak_rss_bytes = psutil.Process().memory_info().rss

    def _sample(self) -> None:
        import psutil

        process = psutil.Process()
        while not self._stop.wait(0.05):
            self.peak_rss_bytes = max(
                self.peak_rss_bytes,
                process.memory_info().rss,
            )

    def __enter__(self) -> MemorySampler:
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        import psutil

        self._stop.set()
        self._thread.join()
        self.peak_rss_bytes = max(
            self.peak_rss_bytes,
            psutil.Process().memory_info().rss,
        )
