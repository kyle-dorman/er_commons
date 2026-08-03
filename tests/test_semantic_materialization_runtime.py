"""Focused input and review-boundary tests for semantic materialization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from er_commons.canonical_extraction.publication import write_json
from er_commons.semantic_materialization.config import SemanticMaterializationConfig
from er_commons.semantic_materialization.errors import SemanticMaterializationInvariantError
from er_commons.semantic_materialization.review import build_semantic_review_cache
from er_commons.semantic_materialization.runtime import _source_pdf

CANDIDATE_ID = "exv1-" + "a" * 64


def test_source_pdf_rejects_same_size_checksum_tamper(tmp_path: Path) -> None:
    accepted_bytes = b"accepted-pdf"
    tampered_bytes = b"tampered-pdf"
    assert len(accepted_bytes) == len(tampered_bytes)
    expected_sha256 = hashlib.sha256(accepted_bytes).hexdigest()
    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(tampered_bytes)
    config = _source_config(expected_sha256)
    _write_source_manifest(
        tmp_path,
        sha256=expected_sha256,
        byte_size=len(accepted_bytes),
        local_path=source_path.name,
    )

    with pytest.raises(
        SemanticMaterializationInvariantError,
        match="source PDF checksum matches the source manifest and configuration",
    ) as caught:
        _source_pdf(tmp_path, config)

    assert caught.value.expected == expected_sha256
    assert caught.value.observed == hashlib.sha256(tampered_bytes).hexdigest()


def test_existing_review_cache_uses_supplied_page_sample(tmp_path: Path) -> None:
    candidate_root = tmp_path / "candidate"
    write_json(
        candidate_root / "records" / "extraction_identity.json",
        {"extraction_id": CANDIDATE_ID},
    )
    review_root = tmp_path / CANDIDATE_ID
    write_json(
        review_root / "review_manifest.json",
        {
            "candidate_id": CANDIDATE_ID,
            "pages": [{"physical_page_number": 2}],
        },
    )

    with pytest.raises(
        SemanticMaterializationInvariantError,
        match="review cache uses the configured page sample",
    ) as caught:
        build_semantic_review_cache(
            review_root=review_root,
            source_pdf=tmp_path / "unused.pdf",
            candidate_root=candidate_root,
            review_pages=(2, 4),
        )

    assert caught.value.expected == (2, 4)
    assert caught.value.observed == (2,)


def _source_config(expected_sha256: str) -> SemanticMaterializationConfig:
    source = SimpleNamespace(source_id="deir_appendix_p", source_sha256=expected_sha256)
    return cast(
        SemanticMaterializationConfig,
        SimpleNamespace(source=source, source_manifest_relative_path=Path("source_manifest.json")),
    )


def _write_source_manifest(root: Path, *, sha256: str, byte_size: int, local_path: str) -> None:
    (root / "source_manifest.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "deir_appendix_p",
                        "sha256": sha256,
                        "byte_size": byte_size,
                        "local_path": local_path,
                    }
                ]
            }
        )
    )
