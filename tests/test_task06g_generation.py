"""Focused source-free checks for the frozen Task 06G generation lane."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from er_commons.artifact_io import sha256_file
from er_commons.artifact_verification import VerificationBudget
from er_commons.collection_processing.config import CollectionRunSpec
from er_commons.document_publication import lineage_preflight
from er_commons.document_publication.config import DocumentRunSpec
from er_commons.document_publication.config_generation.task06g_generation import (
    _validate_producer_resolution_pairs,
    check_task06g_generation,
)
from er_commons.document_publication.fresh_preflight import validate_fresh_build_templates
from er_commons.document_publication.lineage_preflight import (
    build_execution_preflight,
    verify_execution_preflight,
)
from er_commons.document_publication.process_inputs import ProcessConfigs
from er_commons.document_publication.published_document import ProducerLineage
from er_commons.document_records.document_references.relink_preflight import (
    task06g_base_membership_from_source_slots,
)
from er_commons.document_records.document_references.relinking_config import DocumentLinkRunSpec
from er_commons.document_records.document_references.spec_preparation import (
    build_task06g_relink_specs,
)

ROOT = Path(__file__).parents[1]


def test_task06g_uses_fc1_capable_alias_schema() -> None:
    """Bind main-document FC1 aliases to the accepted v2 producer schema."""
    link = json.loads((ROOT / "configs/task06/v1/task06g_link_v1.json").read_text())
    alias = link["output_schema_refs"]["alias"]
    assert alias["path"] == "benchmarks/er_bench/schemas/document_linking/v2/alias.schema.json"
    schema = json.loads((ROOT / alias["path"]).read_text())
    assert "linking_v2_fc1_body_figure_caption" in schema["properties"]["alias_origin"]["enum"]


RECIPE = ROOT / "configs/task06/v1/task06g_generation_v1.json"
V38_RECIPE = ROOT / "configs/task06/v4/task06g_generation_v1.json"


def test_task06g_v38_restores_full_source_free_descendant_graph() -> None:
    """Keep the unsealed v38 packet on the reviewed full execution topology."""
    recipe = json.loads(V38_RECIPE.read_bytes())
    execution = json.loads((ROOT / "configs/task06/v4/task06g_execution_v1.json").read_bytes())
    assert recipe["tmux_session"] == "er-commons-06g-replay-v38"
    assert execution["tmux_session"] == recipe["tmux_session"]
    assert execution["command_order"] == [
        "document_feir_appendix_f1",
        "document_deir_appendix_a",
        "document_deir_main",
        "resolve_relink_specs",
        "relink_and_assemble",
        "resolve_comparison_specs",
        "publish_comparison",
        "validate_handoff",
    ]
    assert execution["resource_limits"]["max_output_bytes"] == 52 * 1024**3
    rendered = json.dumps({"recipe": recipe, "execution": execution})
    assert "replay_v38" in rendered
    assert "replay_v37" in rendered
    assert "replay_v36" in rendered
    assert "replay_v35" in rendered


def test_task06g_v38_generation_remains_immutable_after_finalization_amendment() -> None:
    """Keep the executed v38 owner packet historical instead of rewriting its identity."""
    with pytest.raises(ValueError, match=r"generator differs: .*finaliz"):
        check_task06g_generation(V38_RECIPE)


def test_task06g_v38_path_dependent_process_templates_use_fresh_controls() -> None:
    """Prevent a fresh replay from publishing descendants under replay_v32."""
    recipe = json.loads(V38_RECIPE.read_bytes())
    selected = [
        entry["template"]
        for stages in recipe["document_process_templates"]["sources"].values()
        for entry in stages.values()
        if entry["template"].startswith("configs/task06/v4/")
    ]
    assert len(selected) == 10
    assert len(set(selected)) == 10
    for relative in selected:
        rendered = (ROOT / relative).read_text()
        assert "replay_v38" in rendered
        assert "replay_v32" not in rendered


@pytest.mark.parametrize(
    ("role", "mutation"),
    [
        ("record_mapping", "missing_root"),
        ("record_mapping", "wrong_root_pointer"),
        ("record_mapping", "swapped_stage"),
        ("record_mapping", "swapped_order"),
        ("hierarchy_inference", "missing_root"),
        ("hierarchy_inference", "wrong_root_pointer"),
        ("hierarchy_inference", "swapped_stage"),
        ("hierarchy_inference", "swapped_order"),
    ],
)
def test_task06g_producer_runtime_resolution_requires_exact_root_id_pair(
    role: str, mutation: str
) -> None:
    """Reject a missing or cross-authority producer-root binding before generation."""
    recipe = json.loads(RECIPE.read_bytes())
    resolutions = deepcopy(recipe["document_process_templates"]["runtime_resolutions"])
    if mutation == "missing_root":
        resolutions[role].pop(0)
    elif mutation == "wrong_root_pointer":
        resolutions[role][0]["source_pointer"] = "/outputs/candidate_root"
    elif mutation == "swapped_stage":
        resolutions[role][0]["source_stage"] = (
            "heading_evidence_parsing" if role == "record_mapping" else "content_parsing"
        )
    else:
        resolutions[role].reverse()
    with pytest.raises(ValueError, match="root/ID authority pair"):
        _validate_producer_resolution_pairs(resolutions)


def test_task06g_templates_are_executable_and_source_free(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate actual maintained run specs without touching source/model payloads."""
    original = Path.open

    def guarded(path: Path, *args: object, **kwargs: object):
        if path.suffix.lower() in {".pdf", ".png", ".jpg", ".tif", ".pt", ".safetensors"}:
            raise AssertionError(f"prohibited payload opened: {path}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    with pytest.raises(ValueError, match=r"generator differs: .*finaliz"):
        check_task06g_generation(V38_RECIPE)
    DocumentRunSpec.model_validate_json(
        (ROOT / "configs/task06/v4/task06g_document_v1.json").read_bytes()
    )
    CollectionRunSpec.model_validate_json(
        (ROOT / "configs/task06/v4/task06g_collection_v1.json").read_bytes()
    )
    DocumentLinkRunSpec.model_validate_json(
        (ROOT / "configs/task06/v4/task06g_link_v1.json").read_bytes()
    )


def test_task06g_fixed_mixed_lineage_and_fc1_scope() -> None:
    """Lock the three fresh descendants, 32 preserved rows, and main-only FC1 gate."""
    document = json.loads((ROOT / "configs/task06/v1/task06g_document_v1.json").read_bytes())
    fresh = [
        row["source_id"]
        for row in document["document_processes"]
        if row["lineage_mode"] == "fresh_build"
    ]
    assert fresh == ["feir_appendix_f1", "deir_appendix_a", "deir_main"]
    sealed_count = sum(
        row["lineage_mode"] == "sealed_inputs" for row in document["document_processes"]
    )
    assert sealed_count == 32
    link = json.loads((ROOT / "configs/task06/v1/task06g_link_v1.json").read_bytes())
    assert link["figure_alias_source_ids"] == ["deir_main"]


def test_task06g_mixed_lineage_templates_contain_every_fresh_stage() -> None:
    """Admit 32 sealed rows while containing all three v3 fresh outputs and joins."""
    document = DocumentRunSpec.model_validate_json(
        (ROOT / "configs/task06/v1/task06g_document_v1.json").read_bytes()
    )
    declared = Path("pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v32")
    observed_modes: list[str] = []
    for selection in document.document_processes:
        paths = {role: ROOT / relative for role, relative in selection.configs.model_dump().items()}
        parsed = {role: json.loads(path.read_bytes()) for role, path in paths.items()}
        link = parsed["document_reference_linking"]
        fresh_build = selection.lineage_mode == "fresh_build"
        final_root, authorization = validate_fresh_build_templates(
            configs=ProcessConfigs(**paths),
            source_id=selection.source_id,
            disposition=document.hierarchy_disposition(selection.source_id),
            data_root=Path("/Volumes/x10pro/er_commons"),
            declared_artifact_root=declared if fresh_build else None,
            recorded_manifest_digest=(
                Path(link["source_manifest_relative_path"]),
                link["source_manifest_sha256"],
            ),
            parsed_values=parsed,
            reused_roles=(set(selection.reused_completions.selected()) if fresh_build else None),
        )
        if fresh_build:
            assert final_root.is_relative_to(declared)
            assert final_root == Path(parsed["document_structure"]["artifact_relative_root"])
            assert Path(parsed["record_mapping"]["artifact_relative_root"]).name == (
                "document_records"
            )
        else:
            assert any(part.startswith("task_03h") for part in final_root.parts)
        assert authorization is None
        observed_modes.append(selection.lineage_mode)
    assert observed_modes.count("sealed_inputs") == 32
    assert observed_modes.count("fresh_build") == 3


def test_task06g_parent_and_worker_admit_the_same_source_free_mixed_lineage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Carry v4 containment and reused roles through both execution processes."""
    data_root = Path("/Volumes/x10pro/er_commons")
    spec_path = ROOT / "configs/task06/v1/task06g_document_v1.json"
    spec = DocumentRunSpec.model_validate_json(spec_path.read_bytes())
    original = Path.open

    def guarded(path: Path, *args: object, **kwargs: object):
        if path.suffix.lower() in {".pdf", ".png", ".jpg", ".tif", ".pt", ".safetensors"}:
            raise AssertionError(f"prohibited payload opened: {path}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    monkeypatch.setattr(
        lineage_preflight,
        "_derive_producer_lineage",
        lambda *args, **kwargs: ProducerLineage(
            baseline=f"prv1-{'1' * 64}", hierarchy=f"prv1-{'2' * 64}"
        ),
    )
    for source_id in ("feir_appendix_f1", "deir_appendix_a", "deir_main"):
        snapshot = build_execution_preflight(
            data_root=data_root,
            project_root=ROOT,
            run_spec=spec,
            run_spec_sha256=sha256_file(spec_path),
            source_id=source_id,
        )
        configs = verify_execution_preflight(
            snapshot=snapshot,
            expected_digest=snapshot.digest,
            data_root=data_root,
            project_root=ROOT,
            run_spec=spec,
            run_spec_sha256=sha256_file(spec_path),
            source_id=source_id,
        )
        assert snapshot.final_artifact_relative_root == Path(
            "pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v32/document_structure"
        )
        assert set(configs.as_dict()) == set(ProcessConfigs.__dataclass_fields__)


def test_task06g_execution_uses_absolute_staged_specs_and_checkpointed_scope() -> None:
    """Lock the reviewed staged resolver sequence and prevent relative placeholder argv."""
    execution = json.loads((ROOT / "configs/task06/v1/task06g_execution_v1.json").read_bytes())
    assert execution["command_order"] == [
        "document_feir_appendix_f1",
        "document_deir_appendix_a",
        "document_deir_main",
        "resolve_relink_specs",
        "relink_and_assemble",
        "resolve_comparison_specs",
        "publish_comparison",
        "validate_handoff",
    ]
    commands = {row["stage"]: row for row in execution["commands"]}
    for source_id in ("feir_appendix_f1", "deir_appendix_a", "deir_main"):
        command = commands[f"document_{source_id}"]
        assert any(
            value.endswith("/resolved_specs_v1/00_initial/task06g_document_v1.json")
            for value in command["argv"]
        )
        assert command["checkpoint_after"]["stage_key"] == f"document_{source_id}"
    handoff = commands["validate_handoff"]
    assert "{scope_id}" in handoff["argv"]
    assert handoff["runtime_values"][0]["pointer"] == "/outputs/scope_id"
    phases = execution["resolver_closure"]["phase_directories"]
    assert phases[0] == "00_initial"
    assert phases[1:19] == [
        f"document_stages/{source_id}/{ordinal:02d}_{role}"
        for source_id in ("feir_appendix_f1", "deir_appendix_a", "deir_main")
        for ordinal, role in enumerate(
            (
                "content_parsing",
                "heading_evidence_parsing",
                "record_mapping",
                "hierarchy_inference",
                "document_structure",
                "document_reference_linking",
            ),
            start=1,
        )
    ]
    assert phases[19:] == ["10_relink", "20_comparison"]


def test_task06g_generation_closes_generators_and_exact_runtime_pointers() -> None:
    """Retain historical owner shape and exact pointers without asserting current byte equality."""
    recipe = json.loads(RECIPE.read_bytes())
    assert all(
        set(row) == {"authority", "path", "sha256", "byte_size"}
        for row in recipe["generator_files"]
    )
    paths = [row["path"] for row in recipe["generator_files"]]
    assert len(paths) == len(set(paths))
    assert "src/er_commons/task06g/finalization.py" in paths
    pointers = [
        resolution["pointer"]
        for phase in recipe["phases"].values()
        for spec in phase["specs"]
        for resolution in spec["resolutions"]
    ]
    qualified = {
        (spec["destination"], resolution["pointer"])
        for phase in recipe["phases"].values()
        for spec in phase["specs"]
        for resolution in spec["resolutions"]
    }
    assert len(pointers) == len(qualified)
    assert not any("*" in pointer for pointer in pointers)
    checkpoint_paths = {
        resolution.get("checkpoint")
        for phase in recipe["phases"].values()
        for spec in phase["specs"]
        for resolution in spec["resolutions"]
    }
    assert (
        "pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v32/"
        "resolved_specs_v1/00_initial/pre_execution_production_identity_checkpoint.json"
        in checkpoint_paths
    )
    execution = json.loads((ROOT / "configs/task06/v1/task06g_execution_v1.json").read_bytes())
    assert (
        "pre_execution_production_identity.json"
        not in execution["resolver_closure"]["checkpoint_files"]
    )


def test_task06g_pure_relink_builder_reconstructs_replacement_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the maintained pure builder without publishing or reading payloads."""
    preparation = json.loads(
        (ROOT / "configs/task06/v1/task06g_relink_preparation_v1.json").read_bytes()
    )
    link = json.loads((ROOT / "configs/task06/v1/task06g_link_v1.json").read_bytes())
    documents = {row["source_id"]: row for row in link["documents"]}

    def selection(_: Path, __: Path, source_id: str, **___: object) -> dict[str, object]:
        return documents[source_id]

    monkeypatch.setattr(
        "er_commons.document_records.document_references.spec_preparation._document_selection",
        selection,
    )
    monkeypatch.setattr(
        "er_commons.document_records.document_references.spec_preparation._external_reference",
        lambda value, **_: value,
    )
    base = DocumentLinkRunSpec.model_validate_json(
        (ROOT / "configs/brisbane_baylands_2025_deir_task04d_link_v1.json").read_bytes()
    )
    monkeypatch.setattr(
        "er_commons.document_records.document_references.spec_preparation.task06g_base_membership_from_source_slots",
        lambda *_args, **_kwargs: base.documents,
    )
    monkeypatch.setattr(
        "er_commons.document_records.document_references.spec_preparation.validate_base_collection_selection",
        lambda **_: None,
    )
    original_read = __import__(
        "er_commons.document_records.document_references.spec_preparation",
        fromlist=["_read_object"],
    )._read_object

    def read_object(path: Path, **kwargs: object) -> dict[str, object]:
        if path.is_relative_to(tmp_path):
            return {}
        return original_read(path, **kwargs)

    monkeypatch.setattr(
        "er_commons.document_records.document_references.spec_preparation._read_object",
        read_object,
    )
    monkeypatch.setattr(
        "er_commons.document_records.document_references.spec_preparation._task06g_correspondence_refs",
        lambda *_args, source_id, **_kwargs: (
            []
            if source_id == "feir_appendix_f1"
            else [
                {
                    "authority": "artifact_root",
                    "path": "support.json",
                    "sha256": "1" * 64,
                    "byte_size": 1,
                }
            ]
        ),
    )
    built = build_task06g_relink_specs(
        preparation,
        link,
        repo_root=ROOT,
        data_root=tmp_path,
        link_schema=ROOT
        / "benchmarks/er_bench/schemas/document_linking/v1/document_link_run.schema.json",
    )
    assert built["task06g_relink_preparation_v1.json"] == preparation
    assert (
        built["task06g_link_v1.json"]["base_membership_ref"] == preparation["base_membership_ref"]
    )
    rows = {row["source_id"]: row for row in built["task06g_link_v1.json"]["documents"]}
    base_rows = {row.source_id: row for row in base.documents}
    repaired = {"feir_appendix_f1", "deir_appendix_a", "deir_main"}
    for source_id in set(rows) - repaired:
        source_document = rows[source_id]["source_document"]
        assert source_document == base_rows[source_id].source_document.model_dump(mode="json")
        assert "task03j" not in json.dumps(source_document).lower()
    assert rows["feir_appendix_f1"]["logical_source_id"] == "deir_appendix_f1"
    assert rows["deir_appendix_a"]["change_class"] == "repeated_heading_many_to_one"


@pytest.mark.parametrize("mutation", ["candidate", "production", "order"])
def test_task06g_source_slots_reject_non_task04d_base_membership(mutation: str) -> None:
    """Reject Task03J-like candidates, wrong production lineage, and reordered slots."""
    data_root = Path("/Volumes/x10pro/er_commons")
    slots_path = data_root / "pipelines/brisbane_baylands/task_06_recovery_v1/06a/source_slots.json"
    source_slots = json.loads(slots_path.read_bytes())
    value = deepcopy(source_slots)
    if mutation == "candidate":
        value["sources"][0]["documents"]["04D"]["identity"]["candidate_id"] = "docv1-" + "0" * 64
    elif mutation == "production":
        value["sources"][0]["documents"]["04D"]["identity"]["production_extraction_id"] = (
            "exv1-" + "0" * 64
        )
    else:
        value["sources"][0], value["sources"][1] = value["sources"][1], value["sources"][0]
    publication_root = (
        data_root / "pipelines/brisbane_baylands/task_04d_relinked_v1/document_publications"
    )
    with pytest.raises(ValueError):
        task06g_base_membership_from_source_slots(
            value,
            artifact_root=data_root,
            publication_root=publication_root,
            production_extraction_id=(
                "exv1-466e4e9aced080621fa81058acca95a4e37f1d9a63f2362a569bd9205830b5a3"
            ),
            budget=VerificationBudget(),
        )
