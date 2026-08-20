"""Read-only typed audit of explicit Task 03H.2 evidence roots."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, cast

from er_commons.artifact_io import canonical_json_sha256, sha256_file
from er_commons.chunked_conversion.qualification.diagnostics import QualificationError

TERMINAL_PATHS = frozenset({"records/artifact_inventory.json", "records/completion_record.json"})


@dataclass(frozen=True)
class RecordedClaim:
    """One expected value at a JSON pointer in a managed evidence record."""

    relative_path: str
    pointer: str
    expected: object


@dataclass(frozen=True)
class EvidenceRootSpec:
    """Expected identity, terminal status, and claims for one explicit root."""

    role: str
    root: Path
    expected_id: str
    completion_id_field: str
    statuses: frozenset[str] = frozenset({"complete", "complete_with_warnings"})
    claims: tuple[RecordedClaim, ...] = ()
    canonical_inventory_seal: bool = False
    completion_status_field: str = "status"


@dataclass(frozen=True)
class EvidenceAudit:
    """Verified immutable-root summary without semantic payload loading."""

    role: str
    root: Path
    evidence_id: str
    status: str
    file_count: int
    byte_count: int
    inventory_sha256: str
    completion_sha256: str


@dataclass(frozen=True)
class Task03H2EvidenceSet:
    """The five explicit immutable roots required by the offline oracle."""

    gate_a: EvidenceRootSpec
    gate_b: EvidenceRootSpec
    gate_c: EvidenceRootSpec
    aggregate: EvidenceRootSpec
    downstream: EvidenceRootSpec


def audit_task03h2_evidence(evidence: Task03H2EvidenceSet) -> tuple[EvidenceAudit, ...]:
    """Audit Gate A, Gate B, Gate C, aggregate, and downstream roots in order."""
    return audit_evidence_roots(
        (evidence.gate_a, evidence.gate_b, evidence.gate_c, evidence.aggregate, evidence.downstream)
    )


def audit_evidence_roots(specs: tuple[EvidenceRootSpec, ...]) -> tuple[EvidenceAudit, ...]:
    """Audit explicit roots in caller order without deriving or executing work."""
    if not specs:
        _fail("audit_scope", "$", "at least one explicit root", "empty")
    seen: set[Path] = set()
    results: list[EvidenceAudit] = []
    for spec in specs:
        resolved = spec.root.resolve()
        if resolved in seen:
            _fail("unique_evidence_root", spec.role, "unique root", resolved)
        seen.add(resolved)
        results.append(audit_evidence_root(spec))
    return tuple(results)


def audit_evidence_root(spec: EvidenceRootSpec) -> EvidenceAudit:
    """Validate completion, inventory, managed bytes, identity, and pass claims."""
    root = spec.root.resolve()
    completion_path = root / "records/completion_record.json"
    inventory_path = root / "records/artifact_inventory.json"
    completion = _read_object(completion_path)
    inventory = _read_object(inventory_path)
    _require(
        completion.get(spec.completion_id_field) == spec.expected_id,
        "completion_identity",
        completion_path,
        spec.expected_id,
        completion.get(spec.completion_id_field),
    )
    status = completion.get(spec.completion_status_field)
    _require(
        status in spec.statuses,
        "terminal_status",
        completion_path,
        sorted(spec.statuses),
        status,
    )
    declared_inventory = completion.get("artifact_inventory")
    if declared_inventory is not None:
        _require(
            declared_inventory == "records/artifact_inventory.json",
            "inventory_path",
            completion_path,
            "records/artifact_inventory.json",
            declared_inventory,
        )
    inventory_sha = (
        canonical_json_sha256(inventory)
        if spec.canonical_inventory_seal
        else sha256_file(inventory_path)
    )
    _require(
        completion.get("artifact_inventory_sha256") == inventory_sha,
        "inventory_seal",
        completion_path,
        inventory_sha,
        completion.get("artifact_inventory_sha256"),
    )
    files, byte_count = _verify_inventory(root, inventory, inventory_path)
    for claim in spec.claims:
        _verify_claim(root, claim)
    return EvidenceAudit(
        role=spec.role,
        root=root,
        evidence_id=spec.expected_id,
        status=str(status),
        file_count=len(files),
        byte_count=byte_count,
        inventory_sha256=inventory_sha,
        completion_sha256=sha256_file(completion_path),
    )


def _verify_inventory(
    root: Path, inventory: dict[str, Any], inventory_path: Path
) -> tuple[dict[str, tuple[int, str]], int]:
    raw_files = inventory.get("files")
    if not isinstance(raw_files, list):
        _fail("inventory_shape", inventory_path, "files list", raw_files)
    rows = cast(list[Any], raw_files)
    expected: dict[str, tuple[int, str]] = {}
    for index, row in enumerate(rows):
        row_path = f"{inventory_path}#/files/{index}"
        if not isinstance(row, dict):
            _fail("inventory_entry", row_path, "object", row)
        relative, size, digest = row.get("path"), row.get("byte_size"), row.get("sha256")
        if (
            not isinstance(relative, str)
            or not isinstance(size, int)
            or not isinstance(digest, str)
        ):
            _fail("inventory_entry", row_path, "path, byte_size, sha256", row)
        if not _contained(relative) or relative in expected or relative in TERMINAL_PATHS:
            _fail("inventory_path", row_path, "unique contained managed path", relative)
        expected[relative] = (size, digest)
    actual = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file() and path.relative_to(root).as_posix() not in TERMINAL_PATHS
    }
    if set(actual) != set(expected):
        _fail("managed_file_set", root, sorted(expected), sorted(actual))
    for relative, (size, digest) in expected.items():
        artifact = actual[relative]
        if artifact.stat().st_size != size:
            _fail("artifact_size", artifact, size, artifact.stat().st_size)
        observed = sha256_file(artifact)
        if observed != digest:
            _fail("artifact_checksum", artifact, digest, observed)
    byte_count = sum(size for size, _digest in expected.values())
    if "file_count" in inventory:
        _require(
            inventory["file_count"] == len(expected),
            "inventory_file_count",
            inventory_path,
            len(expected),
            inventory["file_count"],
        )
    declared_bytes = inventory.get("byte_count", inventory.get("byte_size"))
    if declared_bytes is not None:
        _require(
            declared_bytes == byte_count,
            "inventory_byte_count",
            inventory_path,
            byte_count,
            declared_bytes,
        )
    return expected, byte_count


def _verify_claim(root: Path, claim: RecordedClaim) -> None:
    if not _contained(claim.relative_path):
        _fail("claim_path", claim.relative_path, "contained relative path", claim.relative_path)
    path = root / claim.relative_path
    value: Any = _read_object(path)
    for raw_segment in claim.pointer.strip("/").split("/") if claim.pointer != "/" else []:
        segment = raw_segment.replace("~1", "/").replace("~0", "~")
        try:
            value = value[int(segment)] if isinstance(value, list) else value[segment]
        except (KeyError, IndexError, ValueError, TypeError) as error:
            raise QualificationError(
                "recorded_claim_path",
                stage="evidence_audit",
                path=f"{path}#{claim.pointer}",
                expected=claim.expected,
                actual="missing",
            ) from error
    _require(
        value == claim.expected,
        "recorded_pass_claim",
        f"{path}#{claim.pointer}",
        claim.expected,
        value,
    )


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, ValueError, TypeError) as error:
        raise QualificationError(
            "valid_json_object",
            stage="evidence_audit",
            path=path.as_posix(),
            expected="JSON object",
            actual=str(error),
        ) from error
    if not isinstance(value, dict):
        _fail("json_object", path, "object", type(value).__name__)
    return cast(dict[str, Any], value)


def _contained(relative: str) -> bool:
    path = PurePosixPath(relative)
    return bool(relative) and not path.is_absolute() and ".." not in path.parts


def _require(
    condition: bool, invariant: str, path: object, expected: object, actual: object
) -> None:
    if not condition:
        _fail(invariant, path, expected, actual)


def _fail(invariant: str, path: object, expected: object, actual: object) -> None:
    raise QualificationError(
        invariant,
        stage="evidence_audit",
        path=str(path),
        expected=expected,
        actual=actual,
    )
