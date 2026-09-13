"""Gate 1 synthetic relink/publication with strict preserved-input I/O sentinels."""

from __future__ import annotations

import builtins
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from document_publication_test_support import _workspace
from test_document_relinking_stage import (
    UPSTREAM,
    _identity_inputs,
    _schema_paths,
    _source,
)

from er_commons import artifact_io
from er_commons.artifact_io import sha256_file, write_json_atomic
from er_commons.artifact_verification import VerificationBudget
from er_commons.authority_reference import AuthorityReference
from er_commons.document_publication import preflight, storage
from er_commons.document_publication.candidate_identity_validation import (
    verify_identity_and_upstreams,
)
from er_commons.document_publication.candidates import (
    build_candidate_identity,
    write_candidate_identity,
)
from er_commons.document_publication.downstream_replay import publish_downstream_replay
from er_commons.document_publication.identity import canonical_digest
from er_commons.document_publication.records import (
    DOCUMENT_PROCESS_NAMES,
    DOCUMENT_PRODUCT_ROLES,
    ArtifactRef,
    PipelineResult,
)
from er_commons.document_records.document_references import relink_publication
from er_commons.document_records.document_references import storage as link_storage
from er_commons.document_records.record_mapping import publication as record_publication

ROOT = Path(__file__).parents[1]


def _sealed_fixture(tmp_path: Path):
    """Produce a tiny original document and structure using real publication owners."""
    data, spec_path = _workspace(tmp_path)
    run = preflight.prepare_document_run(data, spec_path, "alpha")
    fixture = _source(data / "upstream")
    structured = fixture.root.parent / UPSTREAM
    fixture.root.rename(structured)
    for path in structured.rglob("*.jsonl"):
        path.write_text(path.read_text().replace("report_alpha", "alpha"))
    payload = structured / "support/preserved_payload.json"
    write_json_atomic(payload, {"accepted": "unchanged payload"})
    fixture.manifest["support_files"] = [
        {
            "path": "support/preserved_payload.json",
            "sha256": sha256_file(payload),
            "byte_size": payload.stat().st_size,
            "role": "historical",
            "schema_version": "1.0.0",
        }
    ]
    write_json_atomic(structured / "records/manifest.json", fixture.manifest)
    record_publication.write_inventory(structured)
    structured_completion = structured / "records/completion_record.json"
    write_json_atomic(
        structured_completion,
        {
            "extraction_id": UPSTREAM,
            "status": "complete",
            "completion_last": True,
            "artifact_inventory_sha256": sha256_file(
                structured / "records/artifact_inventory.json"
            ),
        },
    )
    reference = ArtifactRef(
        path=structured_completion.relative_to(data).as_posix(),
        sha256=sha256_file(structured_completion),
    )
    result = PipelineResult(
        source_id="alpha",
        raw_docling_status="SUCCESS",
        processed_pages=[1, 2],
        structured_errors=[],
        warnings=[],
        final_candidate_root=str(structured),
        stage_completions={role: reference for role in DOCUMENT_PRODUCT_ROLES},
        stage_timings={role: 0.0 for role in DOCUMENT_PROCESS_NAMES},
        resource_enforcement="validated_before_document_processes",
    )
    identity = build_candidate_identity(run, content_root=structured, result=result)
    workspace = storage.reserve_candidate_workspace(data / "original", run.final_parent)
    storage.import_content(structured, workspace.staging_root)
    write_candidate_identity(workspace.staging_root / "records", identity, run)
    completion = storage.publish_candidate(
        workspace,
        transaction_id="synthetic-original",
        candidate_id=identity.candidate_id,
        source=run.source,
        processed_pages=[1, 2],
    )
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": "er_commons.source_family_catalog.v1",
                "catalog_version": "fixture",
                "source_family_id": "fixture",
                "sources": [
                    {
                        "source": {
                            "source_id": "alpha",
                            "sha256": run.source.sha256,
                            "pdf_page_count": 2,
                        },
                        "family_root_source_id": "alpha",
                        "document_role": "root_report",
                        "parent_source_id": None,
                        "reference_aliases": ["alpha"],
                    }
                ],
            }
        )
    )
    return data, spec_path, run, structured, completion, catalog_path


def _sentinels(monkeypatch: pytest.MonkeyPatch, preserved: tuple[Path, ...]) -> None:
    """Fail at actual file/hash and execution seams while allowing new-output hashing."""
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.split(".")[0] in {"docling", "torch", "transformers", "pypdf", "fitz"}:
            raise AssertionError(f"model/converter/PDF library access: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    original_open = Path.open

    def guarded_open(path, *args, **kwargs):
        if path.suffix.lower() == ".pdf":
            raise AssertionError(f"source PDF access: {path}")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)

    def forbidden(*args, **kwargs):
        raise AssertionError("fresh source/conversion/model execution")

    monkeypatch.setattr(preflight, "prepare_document_run", forbidden)
    from er_commons.document_publication import process

    monkeypatch.setattr(process, "run_isolated_document", forbidden)
    for module in (artifact_io, storage, link_storage, record_publication, relink_publication):
        original = module.sha256_file

        def guarded_hash(path, _original=original):
            if (
                path.suffix.lower() == ".pdf"
                or path.name == "preserved_payload.json"
                or any(
                    path.is_relative_to(root)
                    and ("canonical" in path.parts or "content" in path.parts)
                    for root in preserved
                )
            ):
                raise AssertionError(f"preserved payload hashing: {path}")
            return _original(path)

        monkeypatch.setattr(module, "sha256_file", guarded_hash)


def test_full_source_free_relink_and_publication(tmp_path, monkeypatch):
    data, spec, old_run, structured, completion, catalog = _sealed_fixture(tmp_path)
    budget = VerificationBudget()
    source_root = completion.parents[1]
    source_inventory = source_root / "records/artifact_inventory.json"
    policy = ROOT / "configs/linking_policies/document_linking_v1.json"
    inputs = replace(
        _identity_inputs(),
        source_id="alpha",
        source_document_id=source_root.name,
        source_document_completion_sha256=sha256_file(completion),
        source_document_inventory_sha256=sha256_file(source_inventory),
        structured_completion_sha256=sha256_file(structured / "records/completion_record.json"),
        structured_inventory_sha256=sha256_file(structured / "records/artifact_inventory.json"),
        linking_policy_sha256=sha256_file(policy),
        source_family_catalog_sha256=sha256_file(catalog),
        reviewed_navigation_bundle_id=None,
        reviewed_navigation_completion_sha256=None,
    )
    _sentinels(monkeypatch, (source_root, structured))
    request = relink_publication.RelinkExecutionRequest(
        structured_root=structured,
        source_document_completion_path=completion,
        source_document_inventory_path=source_inventory,
        linking_policy_path=policy,
        linking_policy_schema_path=ROOT
        / "benchmarks/er_bench/schemas/document_linking/v1/linking_policy.schema.json",
        source_family_catalog_path=catalog,
        output_parent=data / "new-links",
        identity_inputs=inputs,
        output_schema_paths=_schema_paths(),
        budget=budget,
    )
    real_publish = relink_publication.publish_relink_candidate
    released_source_calls = 0

    def publish_after_source_release(**kwargs):
        nonlocal released_source_calls
        assert kwargs["source"].record_files == {}
        released_source_calls += 1
        return real_publish(**kwargs)

    monkeypatch.setattr(
        relink_publication,
        "publish_relink_candidate",
        publish_after_source_release,
    )
    linked = relink_publication.execute_document_relink(request)
    _current_recipe(spec, tmp_path)
    prepared = preflight.prepare_accepted_document_run(
        data, spec, "alpha", budget=budget, repository_root=tmp_path
    )
    published = publish_downstream_replay(
        data_root=data,
        document_run_spec=spec,
        source_id="alpha",
        source_candidate_root=source_root,
        cross_reference_completion=linked.completion_path,
        budget=budget,
        prepared_run=prepared,
    )
    reused_link = relink_publication.execute_document_relink(request)
    assert released_source_calls == 2
    assert reused_link.completion_path == linked.completion_path
    reused_document = publish_downstream_replay(
        data_root=data,
        document_run_spec=spec,
        source_id="alpha",
        source_candidate_root=source_root,
        cross_reference_completion=reused_link.completion_path,
        budget=budget,
        prepared_run=prepared,
    )
    assert reused_document == published
    with pytest.raises(ValueError, match="invocation verification budget"):
        publish_downstream_replay(
            data_root=data,
            document_run_spec=spec,
            source_id="alpha",
            source_candidate_root=source_root,
            cross_reference_completion=reused_link.completion_path,
            budget=VerificationBudget(),
            prepared_run=prepared,
        )
    record = json.loads((published.parent / "document_identity.json").read_text())
    assert record["candidate_id"] != source_root.name
    assert record["source"] == old_run.source.model_dump(mode="json")
    replay = json.loads((published.parent / "downstream_replay.json").read_text())
    assert replay["source_candidate_id"] == source_root.name
    assert replay["reused_stage_completions"]["structured_document"]["path"].startswith("upstream/")
    assert not list((data / "pipelines/test/task_03f").glob("attempts/*"))


def test_v4_downstream_identity_binds_only_controls_it_consumes(tmp_path):
    """A downstream-only replay binds its resolved run spec without fake process refs."""
    _, spec, run, structured, _, _ = _sealed_fixture(tmp_path)
    v4_run = replace(
        run,
        project_root=tmp_path,
        spec=SimpleNamespace(
            schema_version="er_commons.document_run_spec.v4",
            production_extraction_id=run.spec.production_extraction_id,
        ),
    )
    reference = ArtifactRef(
        path=(structured / "records/completion_record.json").relative_to(run.data_root).as_posix(),
        sha256=sha256_file(structured / "records/completion_record.json"),
    )
    result = PipelineResult(
        source_id="alpha",
        raw_docling_status="SUCCESS",
        processed_pages=[1, 2],
        structured_errors=[],
        warnings=[],
        final_candidate_root=str(structured),
        stage_completions={role: reference for role in DOCUMENT_PRODUCT_ROLES},
        stage_timings={role: 0.0 for role in DOCUMENT_PROCESS_NAMES},
        resource_enforcement="validated_before_document_processes",
    )

    with pytest.raises(ValueError, match="lacks sealed process-config references"):
        build_candidate_identity(v4_run, content_root=structured, result=result)
    identity = build_candidate_identity(
        v4_run,
        content_root=structured,
        result=result,
        allow_spec_only_identity=True,
    )
    record = identity.as_record(v4_run)
    assert record.schema_version == "er_commons.document_candidate_identity.v3"
    assert record.resolved_spec_ref is not None
    assert record.resolved_spec_ref.path == spec.relative_to(tmp_path).as_posix()
    assert record.resolved_process_config_refs is None

    controls = storage._recorded_identity_controls(record)
    assert controls["resolved_spec_ref"] == record.resolved_spec_ref.model_dump(mode="json")
    assert "resolved_process_config_refs" not in controls
    assert record.control_digest == canonical_digest(controls)


def test_v4_identity_verification_hashes_resolved_process_specs_as_configs(tmp_path):
    """Fresh v4 candidates verify their six resolved configs under the compact budget."""
    _, spec, run, structured, _, _ = _sealed_fixture(tmp_path)
    v4_run = replace(
        run,
        project_root=tmp_path,
        run_spec_path=structured / "records/completion_record.json",
        spec_sha256=sha256_file(structured / "records/completion_record.json"),
        spec=SimpleNamespace(
            schema_version="er_commons.document_run_spec.v4",
            production_extraction_id=run.spec.production_extraction_id,
        ),
    )
    completion = structured / "records/completion_record.json"
    stage_ref = ArtifactRef(
        path=completion.relative_to(run.data_root).as_posix(),
        sha256=sha256_file(completion),
    )
    config_ref = AuthorityReference(
        authority="artifact_root",
        path=completion.relative_to(run.data_root).as_posix(),
        sha256=sha256_file(completion),
        byte_size=completion.stat().st_size,
    )
    result = PipelineResult(
        source_id="alpha",
        raw_docling_status="SUCCESS",
        processed_pages=[1, 2],
        structured_errors=[],
        warnings=[],
        final_candidate_root=str(structured),
        stage_completions={role: stage_ref for role in DOCUMENT_PRODUCT_ROLES},
        stage_timings={role: 0.0 for role in DOCUMENT_PROCESS_NAMES},
        resource_enforcement="validated_before_document_processes",
        resolved_process_config_refs={role: config_ref for role in DOCUMENT_PROCESS_NAMES},
    )
    identity = build_candidate_identity(v4_run, content_root=structured, result=result)
    candidate = tmp_path / identity.candidate_id
    candidate.mkdir()
    verify_identity_and_upstreams(
        candidate,
        identity=identity.as_record(v4_run).model_dump(mode="json"),
        data_root=run.data_root,
        budget=VerificationBudget(),
    )


def test_compact_candidate_closure_and_explicit_deep_corruption(tmp_path):
    _, _, run, _, completion, _ = _sealed_fixture(tmp_path)
    root = completion.parents[1]
    storage.verify_candidate_metadata(root, root.name, run.source, budget=VerificationBudget())
    payload = root / "content/canonical/blocks.jsonl"
    original = payload.read_bytes()
    payload.write_bytes(original.replace(b"Overview", b"Overviex"))
    storage.verify_candidate_metadata(root, root.name, run.source, budget=VerificationBudget())
    with pytest.raises(ValueError, match="closure"):
        storage.verify_candidate(root, root.name, run.source)
    extra = root / "unexpected.bin"
    extra.write_bytes(b"extra")
    with pytest.raises(ValueError, match="closure"):
        storage.verify_candidate_metadata(root, root.name, run.source, budget=VerificationBudget())


def _current_recipe(spec_path: Path, repository_root: Path) -> None:
    """Give the synthetic new writer a complete current recipe independent of the old one."""
    from er_commons.document_publication.identity import canonical_digest

    spec = json.loads(spec_path.read_text())
    old = json.loads((ROOT / spec["production_identity_relative_path"]).read_text())
    code = repository_root / "writer.py"
    code.write_text("# synthetic current writer\n")
    config = repository_root / "writer_config.json"
    config.write_text("{}\n")
    for role in ("document_process_contract", "collection_process_contract"):
        for key, path in (("owned_code", code), ("artifacts", config)):
            old["preimage"][role][key] = [
                {"path": path.name, "sha256": sha256_file(path), "byte_size": path.stat().st_size}
            ]
    old["preimage"]["production_scope"]["ordered_source_ids"] = ["alpha", "beta"]
    data_root = repository_root / "data"
    manifest_path = data_root / spec["source_manifest_relative_path"]
    completion_path = manifest_path.parent / "completion_record.json"
    manifest = json.loads(manifest_path.read_text())
    old["preimage"]["production_scope"].update(
        source_release_version=spec["source_release_version"],
        source_manifest={
            "path": spec["source_manifest_relative_path"],
            "sha256": sha256_file(manifest_path),
        },
        release_completion={
            "path": completion_path.relative_to(data_root).as_posix(),
            "sha256": sha256_file(completion_path),
        },
        ordered_source_records_sha256=canonical_digest(
            [
                {key: row[key] for key in ("source_id", "sha256", "pdf_page_count")}
                for row in manifest["sources"]
            ]
        ),
    )
    old["identity_sha256"] = canonical_digest(old["preimage"])
    old["extraction_id"] = "exv1-" + old["identity_sha256"]
    recipe = repository_root / "current_recipe.json"
    write_json_atomic(recipe, old)
    spec["production_identity_relative_path"] = recipe.name
    spec["production_extraction_id"] = old["extraction_id"]
    write_json_atomic(spec_path, spec)


def test_prepared_publication_rejects_spec_drift_before_writing(tmp_path):
    data, spec, _, structured, completion, _ = _sealed_fixture(tmp_path)
    _current_recipe(spec, tmp_path)
    budget = VerificationBudget()
    prepared = preflight.prepare_accepted_document_run(
        data, spec, "alpha", budget=budget, repository_root=tmp_path
    )
    spec.write_text(spec.read_text().replace('"retry_limit": 0', '"retry_limit": 1'))
    with pytest.raises(ValueError, match="specification changed"):
        publish_downstream_replay(
            data_root=data,
            document_run_spec=spec,
            source_id="alpha",
            source_candidate_root=completion.parents[1],
            cross_reference_completion=structured / "records/completion_record.json",
            budget=budget,
            prepared_run=prepared,
        )


def test_metadata_reader_requires_recorded_identity_and_unique_membership(tmp_path):
    _, _, run, _, completion, _ = _sealed_fixture(tmp_path)
    root = completion.parents[1]
    inventory_path = root / "records/artifact_inventory.json"
    inventory = json.loads(inventory_path.read_text())
    inventory["files"].append(dict(inventory["files"][0]))
    write_json_atomic(inventory_path, inventory)
    value = json.loads(completion.read_text())
    value["candidate_inventory"]["sha256"] = sha256_file(inventory_path)
    write_json_atomic(completion, value)
    with pytest.raises(ValueError, match="duplicate"):
        storage.verify_candidate_metadata(root, root.name, run.source, budget=VerificationBudget())


def test_historical_production_recipe_survives_missing_implementation_path(tmp_path):
    _, spec, _, _, _, _ = _sealed_fixture(tmp_path)
    _current_recipe(spec, tmp_path)
    from er_commons.document_publication.production_identity import validate_production_identity

    recipe = json.loads((tmp_path / "current_recipe.json").read_text())
    original_id = recipe["extraction_id"]
    (tmp_path / "writer.py").rename(tmp_path / "renamed_writer.py")
    assert validate_production_identity(recipe).value == original_id
    with pytest.raises(ValueError, match="artifact differs"):
        validate_production_identity(recipe, project_root=tmp_path)


def test_v3_document_spec_requires_original_manifest_pairs(tmp_path):
    from er_commons.document_publication.config import load_document_run_spec

    _, spec, _, _, _, _ = _sealed_fixture(tmp_path)
    value = json.loads(spec.read_text())
    value["document_processes"][0]["source_manifest_relative_path"] = (
        "original/source_manifest.json"
    )
    value["document_processes"][0]["source_release_version"] = "original-release"
    write_json_atomic(spec, value)
    with pytest.raises(ValueError, match="require document run spec v3"):
        load_document_run_spec(spec)
    value["schema_version"] = "er_commons.document_run_spec.v3"
    write_json_atomic(spec, value)
    parsed, _ = load_document_run_spec(spec)
    assert parsed.document_processes[0].source_release_version == "original-release"
    value["document_processes"][0].pop("source_release_version")
    write_json_atomic(spec, value)
    with pytest.raises(ValueError, match="selected together"):
        load_document_run_spec(spec)
