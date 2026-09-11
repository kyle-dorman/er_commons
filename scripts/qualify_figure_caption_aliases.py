"""Publish a source-free, no-clobber FC1 qualification packet."""

from __future__ import annotations

import argparse
import logging
import os
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.artifact_io import canonical_json_sha256
from er_commons.document_records.document_references.figure_aliases import (
    POLICY_ID,
    FigureAliasValidationInputs,
    build_caption_figure_aliases,
    require_equal,
    validate_caption_figure_alias_evidence,
)
from er_commons.document_records.document_references.linking_policy import (
    load_document_linking_policy,
)
from er_commons.document_records.document_references.storage import (
    read_json,
    read_jsonl,
    sha256_file,
    write_json,
    write_jsonl,
)

_SELECTED_PATHS = {
    "figures": "canonical/figures.jsonl",
    "images": "canonical/images.jsonl",
    "blocks": "canonical/blocks.jsonl",
    "pages": "canonical/pages.jsonl",
}
LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Qualify exact selected canonical records without source or payload hashing."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--structured-root",
        type=Path,
        required=True,
        help="sealed structured candidate root containing records/manifest.json",
    )
    parser.add_argument(
        "--source-id",
        required=True,
        help="source ID whose canonical figure records will be qualified",
    )
    parser.add_argument(
        "--source-document-id",
        required=True,
        help="exact upstream canonical document ID for --source-id",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="fresh no-clobber qualification directory",
    )
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="verify and reuse an existing current-identity packet instead of failing",
    )
    args = parser.parse_args()
    output_existed = args.output_root.resolve().exists()
    result = publish_qualification(
        structured_root=args.structured_root,
        source_id=args.source_id,
        source_document_id=args.source_document_id,
        output_root=args.output_root,
        repository_root=Path(__file__).resolve().parents[1],
        reuse_existing=args.reuse_existing,
    )
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    action = "reused" if output_existed else "published"
    LOGGER.info("qualification_%s path=%s", action, result)


def publish_qualification(
    *,
    structured_root: Path,
    source_id: str,
    source_document_id: str,
    output_root: Path,
    repository_root: Path,
    reuse_existing: bool = False,
) -> Path:
    """Write one atomic completion-last packet and reject an existing namespace."""
    structured = structured_root.resolve()
    output = output_root.resolve()
    preimage, selected, contract_paths = _qualification_context(
        structured_root=structured,
        source_id=source_id,
        source_document_id=source_document_id,
        repository_root=repository_root,
    )
    qualification_id = f"figqualv1-{canonical_json_sha256(preimage)}"
    if output.exists():
        if reuse_existing:
            verify_qualification_packet(
                output,
                structured_root=structured,
                repository_root=repository_root,
                source_id=source_id,
                source_document_id=source_document_id,
                expected_qualification_id=qualification_id,
            )
            return output
        raise FileExistsError(f"qualification output already exists: {output}")
    inputs = _figure_inputs(
        preimage=preimage,
        selected=selected,
        candidate_id=qualification_id,
        source_id=source_id,
        source_document_id=source_document_id,
    )
    build = build_caption_figure_aliases(
        inputs=inputs,
        first_sequence=1,
    )
    _validate_v2_records(
        aliases=list(build.aliases),
        entries=[entry.as_json() for entry in build.entries],
        qualification=build.qualification,
        contract_root=contract_paths[1].parent,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
    try:
        identity = {**preimage, "qualification_id": qualification_id}
        write_json(staging / "identity.json", identity)
        write_json(staging / "qualification.json", build.qualification)
        write_jsonl(staging / "figure_aliases.jsonl", list(build.aliases))
        write_jsonl(
            staging / "target_index_entries.jsonl",
            [entry.as_json() for entry in build.entries],
        )
        managed = [
            "identity.json",
            "qualification.json",
            "figure_aliases.jsonl",
            "target_index_entries.jsonl",
        ]
        inventory = {
            "schema_version": "er_commons.figure_caption_qualification_inventory.v1",
            "qualification_id": qualification_id,
            "files": [
                {
                    "path": relative,
                    "byte_size": (staging / relative).stat().st_size,
                    "sha256": sha256_file(staging / relative),
                }
                for relative in managed
            ],
        }
        write_json(staging / "inventory.json", inventory)
        completion = {
            "schema_version": "er_commons.figure_caption_qualification_completion.v1",
            "qualification_id": qualification_id,
            "status": "complete",
            "completion_last": True,
            "inventory_sha256": sha256_file(staging / "inventory.json"),
            "source_pdf_accessed": False,
            "pdf_or_image_payload_hashed": False,
        }
        write_json(staging / "completion.json", completion)
        os.rename(staging, output)
    except BaseException:
        failed = output.parent / f"{output.name}.failed-{staging.name.rsplit('-', 1)[-1]}"
        if staging.exists():
            os.rename(staging, failed)
        raise
    verify_qualification_packet(
        output,
        structured_root=structured,
        repository_root=repository_root,
        source_id=source_id,
        source_document_id=source_document_id,
        expected_qualification_id=qualification_id,
    )
    return output


def _qualification_context(
    *,
    structured_root: Path,
    source_id: str,
    source_document_id: str,
    repository_root: Path,
) -> tuple[dict[str, object], dict[str, list[dict[str, object]]], tuple[Path, ...]]:
    """Reconstruct the complete current qualification identity preimage."""
    structured = structured_root.resolve()
    manifest = read_json(structured / "records/manifest.json")
    completion_path = structured / "records/completion_record.json"
    inventory_path = structured / "records/artifact_inventory.json"
    completion = read_json(completion_path)
    inventory = read_json(inventory_path)
    if completion.get("artifact_inventory_sha256") != sha256_file(inventory_path):
        raise ValueError("structured completion does not seal its compact inventory")
    if completion.get("status") not in {"complete", "complete_with_warnings"}:
        raise ValueError("structured input is not terminal")
    upstream_candidate_id = str(manifest["extraction_id"])
    selected = {name: read_jsonl(structured / path) for name, path in _SELECTED_PATHS.items()}
    manifest_rows = _unique_metadata_rows(manifest["record_files"], label="manifest")
    inventory_rows = _unique_metadata_rows(inventory["files"], label="inventory")
    selected_bindings = []
    for name, relative in _SELECTED_PATHS.items():
        manifest_row = manifest_rows.get(relative)
        inventory_row = inventory_rows.get(relative)
        if manifest_row is None or inventory_row is None:
            raise ValueError(f"selected record is absent from sealed metadata: {relative}")
        path = structured / relative
        if manifest_row.get("sha256") != inventory_row.get("sha256"):
            raise ValueError(f"selected record digests disagree: {relative}")
        if path.stat().st_size != inventory_row.get("byte_size"):
            raise ValueError(f"selected record byte size differs: {relative}")
        if len(selected[name]) != manifest_row.get("record_count"):
            raise ValueError(f"selected record count differs: {relative}")
        selected_bindings.append(
            {
                "path": relative,
                "record_count": manifest_row["record_count"],
                "recorded_sha256": manifest_row["sha256"],
                "recorded_byte_size": inventory_row["byte_size"],
            }
        )
    code_paths = (
        repository_root / "src/er_commons/document_records/document_references/figure_aliases.py",
        repository_root / "scripts/qualify_figure_caption_aliases.py",
    )
    contract_paths = (
        repository_root / "configs/linking_policies/document_linking_v2.json",
        repository_root / "benchmarks/er_bench/schemas/document_linking/v2/alias.schema.json",
        repository_root / "benchmarks/er_bench/schemas/document_linking/v2/support.schema.json",
        repository_root
        / "benchmarks/er_bench/schemas/document_linking/v2/linking_policy.schema.json",
    )
    policy = load_document_linking_policy(contract_paths[0], schema_path=contract_paths[3])
    if not policy.figure_caption_aliases_enabled:
        raise ValueError("selected qualification policy does not enable FC1")
    preimage: dict[str, object] = {
        "schema_version": "er_commons.figure_caption_qualification_identity.v1",
        "policy_id": POLICY_ID,
        "source_id": source_id,
        "source_document_id": source_document_id,
        "upstream_candidate_id": upstream_candidate_id,
        "structured_manifest_sha256": sha256_file(structured / "records/manifest.json"),
        "structured_completion_sha256": sha256_file(completion_path),
        "structured_inventory_sha256": sha256_file(inventory_path),
        "selected_record_bindings": selected_bindings,
        "owned_code_sha256": {
            str(path.relative_to(repository_root)): sha256_file(path) for path in code_paths
        },
        "policy_and_schema_sha256": {
            str(path.relative_to(repository_root)): sha256_file(path) for path in contract_paths
        },
        "verification_mode": "sealed_identity_and_selected_record_read_no_preserved_payload_hash",
    }
    return preimage, selected, contract_paths


def verify_qualification_packet(
    root: Path,
    *,
    structured_root: Path,
    repository_root: Path,
    source_id: str,
    source_document_id: str,
    expected_qualification_id: str | None = None,
) -> Path:
    """Verify exact managed closure, completion-last evidence, and requested identity."""
    output = root.resolve()
    completion = read_json(output / "completion.json")
    inventory = read_json(output / "inventory.json")
    identity = read_json(output / "identity.json")
    current_preimage, selected, contract_paths = _qualification_context(
        structured_root=structured_root,
        source_id=source_id,
        source_document_id=source_document_id,
        repository_root=repository_root,
    )
    qualification_id = f"figqualv1-{canonical_json_sha256(current_preimage)}"
    require_equal(
        label="qualification identity",
        observed=identity,
        expected={**current_preimage, "qualification_id": qualification_id},
    )
    if expected_qualification_id is not None and qualification_id != expected_qualification_id:
        require_equal(
            label="requested qualification identity",
            observed=qualification_id,
            expected=expected_qualification_id,
        )
    require_equal(
        label="qualification completion",
        observed=completion,
        expected={
            "schema_version": "er_commons.figure_caption_qualification_completion.v1",
            "qualification_id": qualification_id,
            "status": "complete",
            "completion_last": True,
            "inventory_sha256": sha256_file(output / "inventory.json"),
            "source_pdf_accessed": False,
            "pdf_or_image_payload_hashed": False,
        },
    )
    expected_paths = {
        "identity.json",
        "qualification.json",
        "figure_aliases.jsonl",
        "target_index_entries.jsonl",
        "inventory.json",
        "completion.json",
    }
    observed_paths = {str(path.relative_to(output)) for path in output.rglob("*") if path.is_file()}
    missing_paths = sorted(expected_paths - observed_paths)
    extra_paths = sorted(observed_paths - expected_paths)
    if missing_paths or extra_paths:
        raise ValueError(
            "qualification managed-file closure differs: "
            f"missing={missing_paths[:5]!r}; extra={extra_paths[:5]!r}"
        )
    inventory_rows = inventory.get("files", [])
    if not isinstance(inventory_rows, list) or len(inventory_rows) != 4:
        raise ValueError("qualification inventory must contain exactly four rows")
    indexed_inventory = _unique_metadata_rows(inventory_rows, label="qualification inventory")
    managed_paths = {
        "identity.json",
        "qualification.json",
        "figure_aliases.jsonl",
        "target_index_entries.jsonl",
    }
    inventory_paths = set(indexed_inventory)
    missing_inventory_paths = sorted(managed_paths - inventory_paths)
    extra_inventory_paths = sorted(inventory_paths - managed_paths)
    if missing_inventory_paths or extra_inventory_paths:
        raise ValueError(
            "qualification inventory paths differ: "
            f"missing={missing_inventory_paths[:5]!r}; extra={extra_inventory_paths[:5]!r}"
        )
    require_equal(
        label="qualification inventory identity",
        observed=inventory.get("qualification_id"),
        expected=qualification_id,
    )
    require_equal(
        label="qualification completion identity",
        observed=completion.get("qualification_id"),
        expected=qualification_id,
    )
    for row in inventory_rows:
        path = output / str(row["path"])
        require_equal(
            label=f"qualification managed file {row['path']}",
            observed={"byte_size": path.stat().st_size, "sha256": sha256_file(path)},
            expected={"byte_size": row["byte_size"], "sha256": row["sha256"]},
        )
    contract_root = contract_paths[1].parent
    aliases = read_jsonl(output / "figure_aliases.jsonl")
    entries = read_jsonl(output / "target_index_entries.jsonl")
    if any(row.get("alias_origin") != "linking_v2_fc1_body_figure_caption" for row in aliases):
        raise ValueError("qualification aliases contain a non-FC1 row")
    if any(row.get("alias_origin") != "linking_v2_fc1_body_figure_caption" for row in entries):
        raise ValueError("qualification entries contain a non-FC1 row")
    qualification = read_json(output / "qualification.json")
    _validate_v2_records(
        aliases=aliases,
        entries=entries,
        qualification=qualification,
        contract_root=contract_root,
    )
    inputs = _figure_inputs(
        preimage=current_preimage,
        selected=selected,
        candidate_id=qualification_id,
        source_id=source_id,
        source_document_id=source_document_id,
    )
    validate_caption_figure_alias_evidence(
        aliases=aliases,
        entries=entries,
        qualification=qualification,
        inputs=inputs,
    )
    return output / "completion.json"


def _validate_v2_records(
    *,
    aliases: list[dict[str, object]],
    entries: list[dict[str, object]],
    qualification: dict[str, object],
    contract_root: Path,
) -> None:
    """Validate aliases, standalone index entries, and qualification as v2 support."""
    alias_validator = Draft202012Validator(read_json(contract_root / "alias.schema.json"))
    for alias in aliases:
        alias_validator.validate(alias)
    support_validator = Draft202012Validator(read_json(contract_root / "support.schema.json"))
    support_validator.validate(qualification)
    support_validator.validate(
        {
            "schema_version": "er_commons.cross_reference_target_index.v4",
            "upstream_alias_count": 0,
            "derived_table_alias_count": 0,
            "derived_figure_alias_count": len(aliases),
            "alias_origin_counts": {"linking_v2_fc1_body_figure_caption": len(aliases)},
            "entries": entries,
        }
    )


def _figure_inputs(
    *,
    preimage: dict[str, object],
    selected: dict[str, list[dict[str, object]]],
    candidate_id: str,
    source_id: str,
    source_document_id: str,
) -> FigureAliasValidationInputs:
    """Bind one canonical FC1 input object for one build or verification pass."""
    return FigureAliasValidationInputs(
        upstream_candidate_id=str(preimage["upstream_candidate_id"]),
        candidate_id=candidate_id,
        source_id=source_id,
        source_document_id=source_document_id,
        upstream_figures=tuple(selected["figures"]),
        upstream_images=tuple(selected["images"]),
        upstream_blocks=tuple(selected["blocks"]),
        upstream_pages=tuple(selected["pages"]),
    )


def _unique_metadata_rows(rows: object, *, label: str) -> dict[str, dict[str, object]]:
    """Index metadata rows while rejecting duplicate or malformed paths."""
    if not isinstance(rows, list):
        raise ValueError(f"{label} rows are not a list")
    indexed: dict[str, dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise ValueError(f"{label} row lacks a path")
        path = str(row["path"])
        if path in indexed:
            raise ValueError(f"{label} contains duplicate path: {path}")
        indexed[path] = row
    return indexed


if __name__ == "__main__":
    main()
