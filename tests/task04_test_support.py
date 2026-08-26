from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from er_commons.document_publication.records import SourceIdentity
from er_commons.human_review_support.task04.models import (
    BlockEvidence,
    BuildRequest,
    PageEvidence,
    RenderOutput,
)
from er_commons.human_review_support.task04.scope_policy import InputScopePolicy
from er_commons.human_review_support.task04.verification import CandidateSeal


@dataclass(frozen=True)
class SyntheticReviewTree:
    data_root: Path
    retained_root: Path
    output_root: Path
    candidate: Path
    source_pdf: Path


def synthetic_build_request(tree: SyntheticReviewTree) -> BuildRequest:
    """Build request that makes the non-production one-source scope explicit."""
    return BuildRequest(
        tree.retained_root,
        tree.data_root,
        tree.output_root,
        input_scope=InputScopePolicy.synthetic_fixture(source_count=1),
    )


class AcceptingCandidateVerifier:
    def __init__(self, *, completion: str = "c" * 64, inventory: str = "b" * 64) -> None:
        self.seal = CandidateSeal(completion, inventory)
        self.sources: list[SourceIdentity] = []

    def verify(self, candidate: Path, source: SourceIdentity) -> CandidateSeal:
        self.sources.append(source)
        return self.seal


class FakeRenderer:
    name = "fake-renderer"
    version = "1.2.3"
    scale = 1.0

    def render(
        self,
        source_pdf: Path,
        physical_pages: set[int],
        output_dir: Path,
        source_id: str,
    ) -> tuple[RenderOutput, ...]:
        output_dir.mkdir(parents=True, exist_ok=True)
        outputs = []
        for page in sorted(physical_pages):
            path = output_dir / f"{source_id}-p{page:05d}.png"
            path.write_bytes(f"render-{page}".encode())
            outputs.append(RenderOutput(page, path))
        return tuple(outputs)


class FailingRenderer(FakeRenderer):
    def render(
        self,
        source_pdf: Path,
        physical_pages: set[int],
        output_dir: Path,
        source_id: str,
    ) -> tuple[RenderOutput, ...]:
        raise RuntimeError("synthetic render failure")


def fake_page_evidence(
    candidate: Path, selected_pages: set[int], source_pdf: Path
) -> dict[int, PageEvidence]:
    return {
        page: PageEvidence(
            page,
            612.0,
            792.0,
            None,
            (
                BlockEvidence(
                    f"block-{page}",
                    "paragraph",
                    "Reviewable body text",
                    (10.0, 20.0, 300.0, 40.0),
                    1,
                ),
            ),
            (),
        )
        for page in selected_pages
    }


def make_synthetic_review_tree(tmp_path: Path) -> SyntheticReviewTree:
    data_root = tmp_path / "data"
    retained = data_root / "pipelines" / "brisbane" / "task03h"
    output = data_root / "pipelines" / "brisbane" / "task04"
    source_id = "appendix_a"
    source_bytes = b"synthetic source PDF bytes"
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    source_pdf = (
        data_root
        / "datasets/ceqa/raw/brisbane_baylands/brisbane_baylands_2025_deir_sources_v1"
        / "sources/model_corpus"
        / f"{source_id}.pdf"
    )
    source_pdf.parent.mkdir(parents=True)
    source_pdf.write_bytes(source_bytes)

    inputs = retained / "inputs"
    inputs.mkdir(parents=True)
    catalog_path = inputs / "source_family_catalog.synthetic.json"
    _write_json(
        catalog_path,
        {
            "sources": [
                {
                    "document_role": "appendix",
                    "parent_source_id": None,
                    "source": {
                        "source_id": source_id,
                        "sha256": source_sha,
                        "byte_size": len(source_bytes),
                        "pdf_page_count": 1,
                    },
                }
            ]
        },
    )
    _write_json(
        inputs / "task03h_preparation_readiness.json",
        {
            "status": "synthetic_fixture_ready",
            "production_extraction_id": f"exv1-{'e' * 64}",
            "catalog": {
                "staged_path": catalog_path.relative_to(data_root).as_posix(),
                "sha256": hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
                "byte_size": catalog_path.stat().st_size,
            },
            "source_scope": {
                "source_count": 1,
                "page_count": 1,
                "byte_count": len(source_bytes),
                "ordered_source_ids": [source_id],
            },
        },
    )
    (retained / "document_publications" / "attempts").mkdir(parents=True)
    (retained / "document_parse_evidence").mkdir(parents=True)
    candidate = retained / "document_publications" / "documents" / source_id / f"docv1-{'a' * 64}"
    canonical = candidate / "content" / "canonical"
    canonical.mkdir(parents=True)
    _write_jsonl(
        canonical / "pages.jsonl",
        [
            {
                "id": f"doc/page/{source_id}/p1",
                "physical_page_number": 1,
                "width_pdf_points": 612,
                "height_pdf_points": 792,
                "printed_page_label": None,
                "ordered_content_ids": ["block-1"],
            }
        ],
    )
    _write_jsonl(
        canonical / "blocks.jsonl",
        [
            {
                "id": "block-1",
                "block_type": "paragraph",
                "canonical_text": "A" * 400,
                "regions": [{"page_id": f"doc/page/{source_id}/p1", "bbox": [10, 20, 300, 40]}],
            }
        ],
    )
    records = candidate / "records"
    records.mkdir()
    _write_json(records / "completion_record.json", {"synthetic": True})
    return SyntheticReviewTree(data_root, retained, output, candidate, source_pdf)


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
