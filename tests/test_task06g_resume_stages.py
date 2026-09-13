"""Source-free tests for Task 06G per-source process resume boundaries."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from er_commons.authority_reference import AuthorityReference
from er_commons.document_publication.config import DocumentProcessSelection
from er_commons.document_publication.process_inputs import ProcessConfigs
from er_commons.document_publication.process_sequence import DocumentProcessSequence


def _reference(role: str) -> AuthorityReference:
    return AuthorityReference(
        authority="artifact_root",
        path=f"accepted/{role}/records/completion_record.json",
        sha256="1" * 64,
        byte_size=123,
    )


def _selection(resume_stage: str, roles: tuple[str, ...]) -> DocumentProcessSelection:
    configs = {
        role: f"configs/{role}.json"
        for role in (
            "content_parsing",
            "heading_evidence_parsing",
            "record_mapping",
            "hierarchy_inference",
            "document_structure",
            "document_reference_linking",
        )
    }
    return DocumentProcessSelection.model_validate(
        {
            "source_id": "alpha",
            "lineage_mode": "fresh_build",
            "resume_stage": resume_stage,
            "reused_completions": {role: _reference(role) for role in roles},
            "configs": configs,
        }
    )


def test_resume_selection_requires_exact_skipped_prefix() -> None:
    assert _selection("heading_evidence_parsing", ("content_parsing",)).resume_stage == (
        "heading_evidence_parsing"
    )
    _selection(
        "document_structure",
        (
            "content_parsing",
            "heading_evidence_parsing",
            "record_mapping",
            "hierarchy_inference",
        ),
    )
    with pytest.raises(ValidationError, match="exact preceding completion set"):
        _selection("document_structure", ("content_parsing",))


class _Binder:
    def __init__(self, configs: ProcessConfigs) -> None:
        self.configs = configs

    def reused_config(self, role: str, _completion: Path, **_bindings: object) -> Path:
        return self.configs.as_dict()[role]

    def initial_config(self, role: str) -> Path:
        return self.configs.as_dict()[role]

    def canonical_config(self, _completion: Path) -> Path:
        return self.configs.record_mapping

    def correction_config(self, _completion: Path) -> Path:
        return self.configs.hierarchy_inference

    def semantic_config(self, **_completions: Path) -> Path:
        return self.configs.document_structure

    def cross_reference_config(self, _completion: Path) -> Path:
        return self.configs.document_reference_linking

    def effective_configs(self) -> ProcessConfigs:
        return self.configs


def _sequence(
    tmp_path: Path, resume_stage: str, reused: dict[str, Path]
) -> DocumentProcessSequence:
    configs = ProcessConfigs(
        **{
            role: tmp_path / f"{role}.json"
            for role in (
                "content_parsing",
                "heading_evidence_parsing",
                "record_mapping",
                "hierarchy_inference",
                "document_structure",
                "document_reference_linking",
            )
        }
    )
    sequence = object.__new__(DocumentProcessSequence)
    sequence.data_root = tmp_path
    sequence.configs = configs
    sequence.diagnostics_root = tmp_path / "attempt"
    sequence.timings = {}
    sequence.resume_stage = resume_stage
    sequence.reused_completions = reused
    sequence.binder = _Binder(configs)
    return sequence


def _completion(tmp_path: Path, owner: str, identity: str) -> Path:
    return tmp_path / owner / identity / "records/completion_record.json"


def test_final_f1_skips_content_owner_and_starts_at_heading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = _completion(tmp_path, "producer", "prv1-" + "1" * 64)
    outputs = iter(
        [
            _completion(tmp_path, "producer", "prv1-" + "2" * 64),
            _completion(tmp_path, "mapping", "exv1-" + "3" * 64),
            _completion(tmp_path, "hierarchy", "hcorv1-" + "4" * 64),
            _completion(tmp_path, "structure", "exv1-" + "5" * 64),
            _completion(tmp_path, "link", "exv1-" + "6" * 64),
        ]
    )
    sequence = _sequence(tmp_path, "heading_evidence_parsing", {"content_parsing": content})
    observed: list[str] = []

    def stage(name: str, _ordinal: int, _operation: object) -> Path:
        observed.append(name)
        sequence.timings[name] = 0.1
        return next(outputs)

    monkeypatch.setattr(sequence, "_stage", stage)
    result = sequence.run()
    assert observed == [
        "heading_evidence_parsing",
        "record_mapping",
        "hierarchy_inference",
        "document_structure",
        "document_reference_linking",
    ]
    assert result.completions.content_parsing == content
    assert set(result.timings) == set(sequence.configs.as_dict())
    assert result.timings["content_parsing"] == 0.0
    assert all(result.timings[name] > 0 for name in observed)


def test_appendix_a_and_main_skip_all_source_and_model_owners(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reused = {
        "content_parsing": _completion(tmp_path, "producer", "prv1-" + "1" * 64),
        "heading_evidence_parsing": _completion(tmp_path, "producer", "prv1-" + "2" * 64),
        "record_mapping": _completion(tmp_path, "mapping", "exv1-" + "3" * 64),
        "hierarchy_inference": _completion(tmp_path, "hierarchy", "hcorv1-" + "4" * 64),
    }
    outputs = iter(
        [
            _completion(tmp_path, "structure", "exv1-" + "5" * 64),
            _completion(tmp_path, "link", "exv1-" + "6" * 64),
        ]
    )
    sequence = _sequence(tmp_path, "document_structure", reused)
    observed: list[str] = []

    def stage(name: str, _ordinal: int, _operation: object) -> Path:
        if name in reused:
            raise AssertionError(f"prohibited skipped owner invoked: {name}")
        observed.append(name)
        sequence.timings[name] = 0.1
        return next(outputs)

    monkeypatch.setattr(sequence, "_stage", stage)
    result = sequence.run()
    assert observed == ["document_structure", "document_reference_linking"]
    assert result.completions.record_mapping == reused["record_mapping"]
    assert set(result.timings) == set(sequence.configs.as_dict())
    assert all(result.timings[name] == 0.0 for name in reused)
    assert all(result.timings[name] > 0 for name in observed)


def test_sequence_rejects_nonprefix_reuse_before_any_owner(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="exact skipped prefix"):
        DocumentProcessSequence(
            data_root=tmp_path,
            project_root=tmp_path,
            source_id="alpha",
            configs=ProcessConfigs(
                **{
                    role: tmp_path / f"{role}.json"
                    for role in (
                        "content_parsing",
                        "heading_evidence_parsing",
                        "record_mapping",
                        "hierarchy_inference",
                        "document_structure",
                        "document_reference_linking",
                    )
                }
            ),
            diagnostics_root=tmp_path / "attempt",
            fresh=True,
            resume_stage="document_structure",
            reused_completions={"content_parsing": tmp_path / "completion.json"},
        )
