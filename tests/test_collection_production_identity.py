"""Focused contract tests for collection-only production identity."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from er_commons.artifact_io import sha256_file
from er_commons.collection_processing.production_identity import (
    build_collection_production_identity,
    validate_collection_production_identity,
)


def _file_reference(path: Path, root: Path, authority: str) -> dict[str, object]:
    return {
        "authority": authority,
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
        "byte_size": path.stat().st_size,
    }


def _inputs(tmp_path: Path) -> tuple[Path, Path, dict[str, object]]:
    repository = tmp_path / "repository"
    artifacts = tmp_path / "artifacts"
    repository.mkdir()
    artifacts.mkdir()
    repo_files = {}
    for name in (
        "generation.json",
        "template.json",
        "schema.json",
        "code_a.py",
        "code_b.py",
        "policy_a.json",
        "policy_b.json",
    ):
        path = repository / name
        path.write_text(f"{name}\n")
        repo_files[name] = _file_reference(path, repository, "repository")
    selection = artifacts / "replay_v32/imported_selection.json"
    selection.parent.mkdir()
    selection.write_text('{"source_count":35}\n')
    catalog = artifacts / "replay_v34/inputs/source_catalog.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_text('{"source_count":35}\n')
    selection_ref = _file_reference(selection, artifacts, "artifact_root")
    preimage: dict[str, object] = {
        "schema_version": "er_commons.collection_production_identity_preimage.v1",
        "generation_ref": repo_files["generation.json"],
        "collection_template_ref": repo_files["template.json"],
        "collection_schema_ref": repo_files["schema.json"],
        "owned_code_refs": [repo_files["code_a.py"], repo_files["code_b.py"]],
        "imported_selection_ref": selection_ref,
        "imported_selection_sha256": selection_ref["sha256"],
        "source_catalog_ref": _file_reference(catalog, artifacts, "artifact_root"),
        "source_policy_refs": [repo_files["policy_a.json"], repo_files["policy_b.json"]],
        "output_namespace": (
            "pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v34/document_publications"
        ),
    }
    return repository, artifacts, preimage


def test_collection_production_identity_is_deterministic_and_validates_bytes(
    tmp_path: Path,
) -> None:
    repository, artifacts, preimage = _inputs(tmp_path)
    first = build_collection_production_identity(preimage)
    second = build_collection_production_identity(dict(reversed(list(preimage.items()))))

    assert first == second
    assert first["collection_production_id"] == f"cprodv1-{first['identity_sha256']}"
    validated = validate_collection_production_identity(
        first,
        repository_root=repository,
        artifact_root=artifacts,
        expected_imported_selection_ref=preimage["imported_selection_ref"],
        expected_output_namespace=str(preimage["output_namespace"]),
    )
    assert validated.collection_production_id == first["collection_production_id"]


@pytest.mark.parametrize(
    "field",
    [
        "generation_ref",
        "collection_template_ref",
        "collection_schema_ref",
        "owned_code_refs",
        "imported_selection_ref",
        "source_catalog_ref",
        "source_policy_refs",
    ],
)
def test_collection_production_identity_changes_with_every_bound_role(
    tmp_path: Path, field: str
) -> None:
    _, _, preimage = _inputs(tmp_path)
    original = build_collection_production_identity(preimage)
    changed = copy.deepcopy(preimage)
    if field == "imported_selection_ref":
        item = dict(changed[field])
        item["sha256"] = "f" * 64
        changed[field] = item
        changed["imported_selection_sha256"] = item["sha256"]
    elif field in {"owned_code_refs", "source_policy_refs"}:
        items = list(changed[field])
        item = dict(items[0])
        item["sha256"] = "f" * 64
        items[0] = item
        changed[field] = items
    else:
        item = dict(changed[field])
        item["sha256"] = "f" * 64
        changed[field] = item
    replacement = build_collection_production_identity(changed)
    assert replacement["collection_production_id"] != original["collection_production_id"]


def test_collection_production_identity_rejects_wrong_digest_authority_and_namespace(
    tmp_path: Path,
) -> None:
    _, _, preimage = _inputs(tmp_path)
    wrong_digest = copy.deepcopy(preimage)
    wrong_digest["imported_selection_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="digest differs"):
        build_collection_production_identity(wrong_digest)

    wrong_authority = copy.deepcopy(preimage)
    wrong_authority["generation_ref"]["authority"] = "artifact_root"
    with pytest.raises(ValueError, match="repository authority"):
        build_collection_production_identity(wrong_authority)

    wrong_namespace = copy.deepcopy(preimage)
    wrong_namespace["output_namespace"] = (
        "pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v32/document_publications"
    )
    with pytest.raises(ValueError, match="frozen replay_v33/v34/v35/v36/v37/v38 root"):
        build_collection_production_identity(wrong_namespace)


def test_accepted_collection_namespaces_are_explicit_and_distinct(tmp_path: Path) -> None:
    """Preserve earlier derivations while admitting only the approved v38 descendant."""
    _, _, preimage = _inputs(tmp_path)
    first = build_collection_production_identity(preimage)
    accepted = [
        build_collection_production_identity(
            {
                **preimage,
                "output_namespace": str(preimage["output_namespace"]).replace("replay_v34", value),
            }
        )
        for value in ("replay_v33", "replay_v35", "replay_v36", "replay_v37", "replay_v38")
    ]
    identities = {
        first["collection_production_id"],
        *(row["collection_production_id"] for row in accepted),
    }
    assert len(identities) == 6
    for value in ("replay_v32", "replay_v034", "arbitrary"):
        with pytest.raises(ValueError, match="frozen replay_v33/v34/v35/v36/v37/v38 root"):
            build_collection_production_identity(
                {
                    **preimage,
                    "output_namespace": str(preimage["output_namespace"]).replace(
                        "replay_v34", value
                    ),
                }
            )


def test_collection_production_identity_rejects_unsorted_duplicate_or_extra_fields(
    tmp_path: Path,
) -> None:
    _, _, preimage = _inputs(tmp_path)
    unsorted = copy.deepcopy(preimage)
    unsorted["owned_code_refs"] = list(reversed(unsorted["owned_code_refs"]))
    with pytest.raises(ValueError, match="not sorted"):
        build_collection_production_identity(unsorted)

    repeated = copy.deepcopy(preimage)
    repeated["source_policy_refs"] = [
        repeated["source_policy_refs"][0],
        repeated["source_policy_refs"][0],
    ]
    with pytest.raises(ValueError, match="repeat"):
        build_collection_production_identity(repeated)

    repeated_role = copy.deepcopy(preimage)
    repeated_role["collection_template_ref"] = repeated_role["generation_ref"]
    with pytest.raises(ValueError, match="distinct references"):
        build_collection_production_identity(repeated_role)

    extra = copy.deepcopy(preimage)
    extra["undeclared"] = True
    with pytest.raises(ValueError, match="Extra inputs are not permitted"):
        build_collection_production_identity(extra)


def test_collection_production_identity_validation_rejects_tamper_and_wrong_expectation(
    tmp_path: Path,
) -> None:
    repository, artifacts, preimage = _inputs(tmp_path)
    record = build_collection_production_identity(preimage)
    tampered = copy.deepcopy(record)
    tampered["identity_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="does not derive"):
        validate_collection_production_identity(
            tampered, repository_root=repository, artifact_root=artifacts
        )

    with pytest.raises(ValueError, match="output namespace differs"):
        validate_collection_production_identity(
            record,
            repository_root=repository,
            artifact_root=artifacts,
            expected_output_namespace=str(preimage["output_namespace"]) + "/wrong",
        )

    (repository / "code_a.py").write_text("changed!!\n")
    with pytest.raises(ValueError, match="SHA-256 differs"):
        validate_collection_production_identity(
            record, repository_root=repository, artifact_root=artifacts
        )
