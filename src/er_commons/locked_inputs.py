"""Task 13 split-specific, sealed inputs with the unchanged 11E projections.

Generation receives only ``record``. References and evaluator mappings remain
separate. No mixed label dataset or reserved judge challenge is opened.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from types import ModuleType
from typing import Any, Literal, cast

from er_commons import context_projection
from er_commons.artifact_io import sha256_bytes, stable_json_sha256
from er_commons.reporting_inputs import SealedInputs
from er_commons.target_generation import validate_record

Split = Literal["dev", "test"]


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate keys rather than silently changing sealed identities."""
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"Duplicate input key: {key}")
        value[key] = item
    return value


def _json(raw: bytes) -> Any:
    """Decode one already verified artifact, rejecting ambiguous keys."""
    return json.loads(raw, object_pairs_hook=_unique)


def _contained(root: Path, name: str) -> Path:
    """Resolve a declared artifact path without allowing external reads."""
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Input outside permitted root: {name}")
    return path


class _Sources:
    """Record every exact consumed source without traversing sibling content."""

    def __init__(self, repo: Path, data_root: Path) -> None:
        """Separate checkout bindings from external publication bindings."""
        self.repo = repo.resolve()
        self.data_root = data_root.resolve()
        self.provenance: dict[str, dict[str, Any]] = {}

    def read(self, path: Path, binding: dict[str, Any] | None = None) -> bytes:
        """Verify size/hash before returning bytes and preserve their provenance."""
        path = path.resolve()
        if not any(path.is_relative_to(root) for root in (self.repo, self.data_root)):
            raise ValueError("Source outside checkout and data root")
        raw = path.read_bytes()
        actual = {"sha256": sha256_bytes(raw), "byte_size": len(raw)}
        if binding is not None and any(actual[key] != binding[key] for key in actual):
            raise ValueError(f"Input binding changed: {path}")
        self.provenance[str(path)] = {"path": str(path), **actual}
        return raw

    def pointer(self, name: str) -> dict[str, Any]:
        """Read an explicit tracked acceptance pointer, never discover publications."""
        return cast(dict[str, Any], _json(self.read(self.repo / "docs/specs" / name)))

    def publication(self, binding: dict[str, Any]) -> SealedInputs:
        """Index only completion metadata, without reading its listed artifacts."""
        path = _contained(self.data_root, binding["path"])
        seal = _json(self.read(path, binding))
        rows = seal.get("files", seal.get("inventory"))
        if rows is None:
            rows = [
                {**entry, "path": str(_contained(self.data_root, name).relative_to(path.parent))}
                for name, entry in seal["artifacts"].items()
            ]
        return SealedInputs(path.parent, {"files": rows})

    def sealed(self, source: SealedInputs, name: str) -> bytes:
        """Read one selected file through its seal and record its exact binding."""
        raw = source.read(name)
        path = _contained(source.root, name)
        self.provenance[str(path)] = {**source.files[name], "path": str(path)}
        return raw


def validate_roster(split: dict[str, Any], mode: Split) -> list[str]:
    """Require the approved disjoint 19/30 split before opening selected content."""
    if mode not in ("dev", "test") or split.get("status") != "approved":
        raise ValueError("An explicit approved dev/test split is required")
    dev, test = split.get("dev"), split.get("test")
    if (
        not isinstance(dev, list)
        or not isinstance(test, list)
        or len(dev) != 19
        or len(test) != 30
        or any(
            not isinstance(case, str) or not re.fullmatch(r"C\d{3}", case) for case in dev + test
        )
        or len(set(dev + test)) != 49
    ):
        raise ValueError("Expected exactly 19 distinct development and 30 distinct test cases")
    return list(split[mode])


def _rows(raw: bytes, cases: list[str]) -> dict[str, Any]:
    """Require exact ordered coverage from a split-only JSONL artifact."""
    rows = [_json(line) for line in raw.splitlines() if line.strip()]
    if [row["case_id"] for row in rows] != cases:
        raise ValueError("Split rows differ from the exact approved roster")
    return {row["case_id"]: row for row in rows}


def _document(source_id: str) -> str:
    """Apply the frozen neutral appendix label to its physical document parts.

    Catalog multipart IDs retain their complete opaque identity in each passage;
    the document label describes the appendix, as for unsplit appendix PDFs.
    Part numbering is only an explicitly validated filename suffix, not evidence.
    """
    if source_id == "deir_main":
        return "EIR main document"
    match = re.fullmatch(
        r"(?:deir|feir)_appendix_([a-z])([0-9]+)?(?:_part_([1-9][0-9]*)_of_([1-9][0-9]*))?",
        source_id,
    )
    if match is None or (match[3] is not None and int(match[3]) > int(match[4])):
        raise ValueError(f"Unrecognized frozen source label: {source_id}")
    return "EIR Appendix " + match[1].upper() + ("." + match[2] if match[2] else "")


def project_record(
    record: dict[str, Any], mapping: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reuse 11E neutral projection while preserving evidence and evaluator identity."""
    validate_record(record)
    if mapping["case_id"] != record["case_id"] or mapping["payload_sha256"] != stable_json_sha256(
        record["payload"]
    ):
        raise ValueError("Evaluator mapping does not bind its target")
    locators = context_projection.build_locator_map(
        record,
        {
            passage["citation_id"]: {
                "document": _document(passage["source_id"]),
                "title": passage["title"],
                "heading_path": passage["heading_path"],
            }
            for passage in record["payload"]["passages"]
        },
    )
    projected = context_projection.project_target(
        record,
        locators,
        summary="unused identity-only placeholder",
        prompt="unused identity-only placeholder",
    )
    result = {**record, "payload": projected["payload"]}
    projected_mapping = copy.deepcopy(mapping)
    projected_mapping["payload_sha256"] = stable_json_sha256(result["payload"])
    return result, projected_mapping


def planned_slots(case_ids: list[str], *, mode: Split = "test") -> list[dict[str, Any]]:
    """Retain all model/question/repeat slots in stable order, without sampling."""
    expected = 30 if mode == "test" else 19
    if mode not in ("dev", "test") or len(case_ids) != expected or len(set(case_ids)) != expected:
        raise ValueError("Invalid slot roster")
    return [
        {
            "arm": "test30" if mode == "test" else "development_replay",
            "model": model,
            "condition": "openai_generation" if model == "luna" else "anthropic_generation",
            "repeat": repeat,
            "case_id": case,
        }
        for model in ("luna", "haiku")
        for repeat in (1, 2, 3)
        for case in case_ids
    ]


def _load(repo: Path, data_root: Path, mode: Split) -> dict[str, Any]:
    """Assemble one authorized split from exact publications and frozen transforms."""
    sources = _Sources(repo, data_root)
    accepted = sources.pointer("task11e_result.json")
    binding = accepted["frozen_configuration"]
    frozen = _json(sources.read(_contained(repo, binding["path"]), binding))
    for key in ("prompt", "context"):
        raw = sources.read(_contained(repo, frozen[f"{key}_path"]))
        if sha256_bytes(raw) != frozen[f"{key}_sha256"]:
            raise ValueError(f"Frozen {key} changed")
    task10 = sources.pointer("task10_final_result.json")
    publication = sources.publication(task10["completion"])
    cases = validate_roster(_json(sources.sealed(publication, "split.json")), mode)
    records = _rows(sources.sealed(publication, f"target/{mode}.jsonl"), cases)
    mappings = _rows(sources.sealed(publication, f"evaluator/{mode}_mappings.jsonl"), cases)
    reference_pointer = sources.pointer("task09f_question_publication_v2_result.json")
    references_source = sources.publication(reference_pointer["completion"])
    d6 = sources.publication(sources.pointer("task11d6_result.json")["completion"])
    script = "labels/publish_labels_v5.py"
    script_bytes = sources.sealed(d6, script)
    transform = ModuleType("_task13_frozen_reference_projection")
    transform.__file__ = str(d6.root / script)
    # Execute the exact verified implementation without reopening it or writing
    # Python cache files into the preserved source publication.
    exec(compile(script_bytes, transform.__file__, "exec"), transform.__dict__)
    inputs, references = {}, {}
    for case in cases:
        record, mapping = project_record(records[case], mappings[case])
        original_reference = _json(sources.sealed(references_source, f"curator/cases/{case}.json"))
        if original_reference["case_id"] != case:
            raise ValueError("Reference case identity changed")
        transform.RECORDS.clear()
        transform.add(
            "references",
            case,
            case,
            original_reference["answer"],
            {"approval_status": "inherited_approved_reference"},
            original_reference,
            heldout=mode == "test",
        )
        derivative = transform.RECORDS[0]
        private = _json(
            sources.sealed(d6, f"labels/publication_v5/private/{derivative['new_id']}.json")
        )
        if (
            not derivative["eligible"]
            or derivative["retirement_reasons"]
            or private != derivative["private_original"]
            or derivative["payload"]["question"] != record["payload"]["question"]
        ):
            raise ValueError("Frozen reference projection mismatch")
        reference = derivative["payload"]["conclusion"]["text"]
        references[case] = {
            "question": record["payload"]["question"],
            "reference_conclusion": reference,
            "derived_record_id": derivative["new_id"],
            "original_reference_sha256": stable_json_sha256(
                original_reference["answer"]["conclusion"]["text"]
            ),
        }
        inputs[case] = {
            "record": record,
            "mapping": mapping,
            "reference": reference,
            "original_record_sha256": stable_json_sha256(records[case]),
            "reference_publication_sha256": None,
        }
    reference_hash = stable_json_sha256(references)
    for item in inputs.values():
        item["reference_publication_sha256"] = reference_hash
    return {
        "schema_version": "task13.locked_inputs.v1",
        "split": mode,
        "case_ids": cases,
        "inputs": inputs,
        "references": references,
        "slots": planned_slots(cases, mode=mode),
        "frozen_configuration": frozen,
        "provenance": list(sources.provenance.values()),
        "inputs_sha256": stable_json_sha256(inputs),
        "reference_projection_sha256": reference_hash,
        "provider_calls": 0,
    }


def load_locked(repo: Path, data_root: Path) -> dict[str, Any]:
    """Load exactly 30 authorized test inputs; never open development or challenge rows."""
    return _load(repo, data_root, "test")


def load_development_replay(repo: Path, data_root: Path) -> dict[str, Any]:
    """Explicit offline-only development preparation for preflight equivalence checks."""
    result = _load(repo, data_root, "dev")
    result["schema_version"] = "task13.development_replay_inputs.v1"
    return result
