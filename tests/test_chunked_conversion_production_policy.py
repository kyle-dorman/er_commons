import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from er_commons.artifact_io import canonical_json_sha256, write_json_atomic
from er_commons.chunked_conversion.range_contract import RangePlan, build_range_plan
from er_commons.chunked_conversion.runtime import inputs as runtime_inputs
from er_commons.chunked_conversion.runtime import planning
from er_commons.chunked_conversion.runtime.inputs import (
    RuntimeCodeIdentity,
    VerifiedChunkInputs,
    chunked_run_identity,
)
from er_commons.chunked_conversion.runtime.planning import build_fixed_size_plan
from er_commons.document_parsing.content_parsing import configured_application
from er_commons.document_parsing.content_parsing.configured_application import (
    ChunkedExecutionPolicy,
)
from er_commons.document_parsing.content_parsing.preparation import PreparedContentParsing
from er_commons.document_publication import process_sequence
from er_commons.document_publication.process_inputs import ProcessConfigs

SCRIPT_ROOT = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))
shared = importlib.import_module("task03h_generation.shared")
sys.path.remove(str(SCRIPT_ROOT))
CHUNKED_PAGE_THRESHOLD = shared.CHUNKED_PAGE_THRESHOLD
TASK_CONFIG_ROOT = shared.TASK_CONFIG_ROOT
chunked_policy_paths = shared.chunked_policy_paths


def _prepared(page_count: int = 601) -> PreparedContentParsing:
    payload = {
        "sealed_release": {"release": "v1"},
        "package_versions": {"docling": "test"},
        "model_inventory": {"layout": "test"},
    }
    return cast(
        PreparedContentParsing,
        SimpleNamespace(
            source=SimpleNamespace(
                source_id="large",
                source_sha256="a" * 64,
                source_byte_size=1234,
                source_page_count=page_count,
                source_path=Path("source.pdf"),
            ),
            conversion_identity=SimpleNamespace(run_id="dconv1-source", payload=payload),
            identity=SimpleNamespace(run_id="prv1-monolithic"),
        ),
    )


def _code(*, aggregate: str = "aggregate") -> RuntimeCodeIdentity:
    return RuntimeCodeIdentity("page", "range", "planning", aggregate, "coordinator")


def _policy(path: Path) -> Path:
    write_json_atomic(
        path,
        {
            "schema_version": "er_commons.chunked_execution_policy.v1",
            "mode": "fixed_size",
            "source_selection": {"pdf_page_count_greater_than": 300},
            "target_range_size": 225,
            "hard_maximum": 275,
            "overlap_pages": 1,
            "max_range_rss_bytes": 20 * 1024**3,
            "max_aggregate_rss_bytes": 16 * 1024**3,
            "max_wall_seconds": 14400.0,
        },
    )
    return path


def test_chunk_policy_paths_use_source_neutral_page_threshold() -> None:
    sources = [
        {"source_id": "small", "pdf_page_count": CHUNKED_PAGE_THRESHOLD},
        {"source_id": "large", "pdf_page_count": CHUNKED_PAGE_THRESHOLD + 1},
    ]

    assert chunked_policy_paths(sources) == (TASK_CONFIG_ROOT / "large/chunked_conversion.json",)


def test_generated_policy_records_maintained_threshold() -> None:
    policy = ChunkedExecutionPolicy.model_validate(
        {
            "schema_version": "er_commons.chunked_execution_policy.v1",
            "mode": "fixed_size",
            "source_selection": {"pdf_page_count_greater_than": 300},
            "target_range_size": 225,
            "hard_maximum": 275,
            "overlap_pages": 1,
            "max_range_rss_bytes": 20 * 1024**3,
            "max_aggregate_rss_bytes": 16 * 1024**3,
            "max_wall_seconds": 14400.0,
        }
    )

    assert policy.source_selection.pdf_page_count_greater_than == CHUNKED_PAGE_THRESHOLD


def test_chunk_run_identity_excludes_operational_limits(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{}")
    prepared = SimpleNamespace(conversion_identity=SimpleNamespace(run_id="dconv1-source"))
    plan = SimpleNamespace(plan_id="dplan1-plan")
    verified = VerifiedChunkInputs(
        prepared=cast(Any, prepared),
        plan=cast(Any, plan),
    )
    code = RuntimeCodeIdentity("page", "range", "planning", "aggregate", "coordinator")

    identity = chunked_run_identity(plan_path=plan_path, verified=verified, code=code)

    assert identity["prepared_conversion_id"] == "dconv1-source"
    assert "resource_limits" not in identity
    assert "config_sha256" not in identity


def test_chunk_run_identity_depends_on_plan_bytes_not_config_or_plan_path(tmp_path: Path) -> None:
    first_path = tmp_path / "first/plan.json"
    second_path = tmp_path / "second/renamed.json"
    first_path.parent.mkdir()
    second_path.parent.mkdir()
    first_path.write_text('{"same":true}')
    second_path.write_bytes(first_path.read_bytes())
    prepared = cast(
        Any, SimpleNamespace(conversion_identity=SimpleNamespace(run_id="dconv1-source"))
    )
    verified = VerifiedChunkInputs(prepared=prepared, plan=cast(Any, SimpleNamespace(plan_id="p")))

    assert chunked_run_identity(plan_path=first_path, verified=verified, code=_code()) == (
        chunked_run_identity(plan_path=second_path, verified=verified, code=_code())
    )


def test_fixed_size_plan_has_exact_coverage_and_one_page_overlaps() -> None:
    plan = build_fixed_size_plan(
        _prepared(page_count=601),
        _code(),
        target_range_size=225,
        hard_maximum=275,
    )

    assert tuple(page for item in plan.ranges for page in item.core.pages) == tuple(range(1, 602))
    assert [(item.core.start, item.core.end) for item in plan.ranges] == [
        (1, 225),
        (226, 450),
        (451, 601),
    ]
    assert [(item.read.start, item.read.end) for item in plan.ranges] == [
        (1, 226),
        (225, 451),
        (450, 601),
    ]


def test_content_adaptive_plan_closes_on_native_content_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = (4, 4, 20, 4, 4)

    def features(_path: Path, page_number: int) -> dict[str, object]:
        return {
            "physical_pdf_page": page_number,
            "native_text_rectangle_count": values[page_number - 1],
            "nonspace_character_count": 0,
        }

    monkeypatch.setattr(
        planning,
        "all_page_features",
        lambda _path: tuple(features(_path, page) for page in range(1, 6)),
    )
    plan = planning.build_content_adaptive_plan(
        _prepared(page_count=len(values)),
        _code(),
        target_range_size=225,
        hard_maximum=275,
        max_native_content_units_per_range=8,
    )

    assert [(item.core.start, item.core.end) for item in plan.ranges] == [
        (1, 2),
        (3, 3),
        (4, 5),
    ]
    assert plan.inputs.planner_mode == "content_adaptive"
    assert plan.inputs.max_native_content_units_per_range == 8
    assert plan.inputs.content_profile_sha256 == canonical_json_sha256(
        {
            "source_id": "large",
            "features": [
                {
                    "physical_pdf_page": page_number,
                    "native_text_rectangle_count": value,
                    "nonspace_character_count": 0,
                    "native_content_units": value,
                }
                for page_number, value in enumerate(values, start=1)
            ],
        }
    )


def test_content_adaptive_plan_allows_one_page_over_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        planning,
        "all_page_features",
        lambda _path: tuple(
            {
                "physical_pdf_page": page_number,
                "native_text_rectangle_count": 20,
                "nonspace_character_count": 0,
            }
            for page_number in range(1, 3)
        ),
    )

    plan = planning.build_content_adaptive_plan(
        _prepared(page_count=2),
        _code(),
        max_native_content_units_per_range=8,
    )

    assert [(item.core.start, item.core.end) for item in plan.ranges] == [(1, 1), (2, 2)]


def _native_feature(
    page_number: int,
    *,
    rectangles: int = 4,
    characters: int = 8,
) -> dict[str, object]:
    return {
        "physical_pdf_page": page_number,
        "native_text_rectangle_count": rectangles,
        "nonspace_character_count": characters,
    }


@pytest.mark.parametrize(
    ("features", "expected_page_count", "message"),
    [
        ((_native_feature(1),), 2, "cover every source page exactly once"),
        ((_native_feature(2), _native_feature(1)), 2, "ordered by physical page"),
        ((_native_feature(1), _native_feature(1)), 2, "duplicate physical pages"),
        (
            (
                {
                    "physical_pdf_page": 1,
                    "native_text_rectangle_count": 4,
                },
            ),
            1,
            "missing 'nonspace_character_count'",
        ),
        ((_native_feature(1, rectangles=-1),), 1, "must be at least 0"),
    ],
    ids=("missing-page", "shuffled", "duplicate", "malformed", "negative-count"),
)
def test_content_adaptive_plan_rejects_invalid_native_content_profiles(
    monkeypatch: pytest.MonkeyPatch,
    features: tuple[dict[str, object], ...],
    expected_page_count: int,
    message: str,
) -> None:
    monkeypatch.setattr(planning, "all_page_features", lambda _path: features)

    with pytest.raises(ValueError, match=message):
        planning.build_content_adaptive_plan(
            _prepared(page_count=expected_page_count),
            _code(),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("converter_identity", "dconv1-transplanted"),
        ("sealed_source_release_identity", "stale-release"),
        ("package_identity", "stale-packages"),
        ("model_identity", "stale-models"),
        ("adapter_identity", "stale-page-evidence"),
        ("page_evidence_contract_identity", "stale-page-contract"),
        ("range_conversion_identity", "stale-range-code"),
        ("range_planner_identity", "stale-planner"),
        ("aggregate_merge_identity", "stale-aggregate"),
    ],
)
def test_verify_inputs_rejects_stale_runtime_binding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    prepared = _prepared()
    plan = build_fixed_size_plan(prepared, _code())
    stale = build_range_plan(plan.inputs.model_copy(update={field: value}))
    plan_path = tmp_path / "plan.json"
    write_json_atomic(plan_path, stale.model_dump(mode="json"))
    monkeypatch.setattr(
        runtime_inputs, "load_content_parsing_config", lambda _path: (object(), "x")
    )
    monkeypatch.setattr(
        runtime_inputs,
        "prepare_content_parsing",
        lambda _root, *, config, config_sha256: prepared,
    )

    with pytest.raises(ValueError, match="range plan runtime bindings differ") as raised:
        runtime_inputs.verify_chunk_inputs(tmp_path / "config.json", plan_path, tmp_path, _code())

    assert field in str(raised.value)


def test_verify_inputs_accepts_current_source_and_runtime(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    prepared = _prepared()
    plan = build_fixed_size_plan(prepared, _code())
    plan_path = tmp_path / "plan.json"
    write_json_atomic(plan_path, plan.model_dump(mode="json"))
    monkeypatch.setattr(
        runtime_inputs, "load_content_parsing_config", lambda _path: (object(), "x")
    )
    monkeypatch.setattr(
        runtime_inputs,
        "prepare_content_parsing",
        lambda _root, *, config, config_sha256: prepared,
    )

    verified = runtime_inputs.verify_chunk_inputs(
        tmp_path / "config.json", plan_path, tmp_path, _code()
    )

    assert verified.plan == plan


def test_configured_dispatch_without_policy_uses_monolithic(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    expected = tmp_path / "monolithic/completion.json"
    monkeypatch.setattr(
        configured_application,
        "run_document_parsing",
        lambda data_root, config_path: expected,
    )

    actual = configured_application.run_configured_document_parsing(
        tmp_path, tmp_path / "content_parsing.json"
    )

    assert actual == expected


def test_configured_dispatch_above_threshold_uses_chunking(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    prepared = _prepared()
    policy_path = _policy(tmp_path / "chunked_conversion.json")
    task_root = tmp_path / "artifacts"
    observed: dict[str, Any] = {}
    monkeypatch.setattr(
        configured_application,
        "load_content_parsing_config",
        lambda _path: (SimpleNamespace(artifact_relative_root="artifacts"), "config-sha"),
    )
    monkeypatch.setattr(
        configured_application,
        "prepare_content_parsing",
        lambda _root, *, config, config_sha256: prepared,
    )
    monkeypatch.setattr(configured_application, "task_artifact_root", lambda *_args: task_root)
    monkeypatch.setattr(configured_application, "behavior_code_identity", lambda _root: _code())

    def run_chunked(data_root: Path, config_path: Path, plan_path: Path, *, request: Any) -> Path:
        observed.update(plan=RangePlan.model_validate_json(plan_path.read_bytes()), request=request)
        return tmp_path / "chunked/completion.json"

    monkeypatch.setattr(configured_application, "run_chunked_document_parsing", run_chunked)

    result = configured_application.run_configured_document_parsing(
        tmp_path, tmp_path / "content_parsing.json", policy_path=policy_path
    )

    assert result == tmp_path / "chunked/completion.json"
    assert observed["plan"].inputs.source.physical_page_count == 601
    assert observed["request"].plan_path.parent.name == observed["plan"].plan_id


def test_existing_monolithic_final_wins_even_with_chunk_policy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    prepared = _prepared()
    policy_path = _policy(tmp_path / "chunked_conversion.json")
    task_root = tmp_path / "artifacts"
    (task_root / prepared.identity.run_id).mkdir(parents=True)
    expected = tmp_path / "monolithic/completion.json"
    monkeypatch.setattr(
        configured_application,
        "load_content_parsing_config",
        lambda _path: (SimpleNamespace(artifact_relative_root="artifacts"), "config-sha"),
    )
    monkeypatch.setattr(
        configured_application,
        "prepare_content_parsing",
        lambda _root, *, config, config_sha256: prepared,
    )
    monkeypatch.setattr(configured_application, "task_artifact_root", lambda *_args: task_root)
    monkeypatch.setattr(configured_application, "run_document_parsing", lambda *_args: expected)
    monkeypatch.setattr(
        configured_application,
        "run_chunked_document_parsing",
        lambda *_args, **_kwargs: pytest.fail(
            "chunking must not replace a sealed monolithic final"
        ),
    )

    assert (
        configured_application.run_configured_document_parsing(
            tmp_path, tmp_path / "content_parsing.json", policy_path=policy_path
        )
        == expected
    )


def test_fresh_lineage_uses_original_policy_siblings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_root = tmp_path / "configs/source"
    generated_root = tmp_path / "attempt/effective"
    configs = ProcessConfigs(
        content_parsing=config_root / "content_parsing.json",
        heading_evidence_parsing=config_root / "heading_evidence_parsing.json",
        record_mapping=config_root / "record_mapping.json",
        hierarchy_inference=config_root / "hierarchy_inference.json",
        document_structure=config_root / "document_structure.json",
        document_reference_linking=config_root / "document_reference_linking.json",
    )

    class FakeBinder:
        def initial_configs(self) -> tuple[Path, Path]:
            return (
                generated_root / "content_parsing.json",
                generated_root / "heading_evidence_parsing.json",
            )

        def canonical_config(self, _completion: Path) -> Path:
            return generated_root / "record_mapping.json"

        def correction_config(self, _completion: Path) -> Path:
            return generated_root / "hierarchy_inference.json"

        def semantic_config(self, **_kwargs: Path) -> Path:
            return generated_root / "document_structure.json"

        def cross_reference_config(self, _completion: Path) -> Path:
            return generated_root / "document_reference_linking.json"

        def effective_configs(self) -> ProcessConfigs:
            return configs

    observed: list[tuple[Path, Path | None]] = []

    def configured(_data_root: Path, config_path: Path, *, policy_path: Path | None = None) -> Path:
        observed.append((config_path, policy_path))
        return tmp_path / f"completion-{len(observed)}.json"

    monkeypatch.setattr(process_sequence, "run_configured_document_parsing", configured)
    monkeypatch.setattr(
        process_sequence, "map_document_records", lambda *_args, **_kwargs: tmp_path / "map"
    )
    monkeypatch.setattr(
        process_sequence,
        "infer_document_hierarchy",
        lambda *_args, **_kwargs: tmp_path / "hierarchy",
    )
    monkeypatch.setattr(
        process_sequence,
        "map_document_structure",
        lambda *_args, **_kwargs: tmp_path / "structure",
    )
    monkeypatch.setattr(
        process_sequence,
        "link_document_references",
        lambda *_args, **_kwargs: tmp_path / "links",
    )
    monkeypatch.setattr(
        process_sequence.DocumentProcessSequence,
        "_stage",
        lambda self, name, ordinal, operation: operation(),
    )
    sequence = object.__new__(process_sequence.DocumentProcessSequence)
    sequence.data_root = tmp_path
    sequence.configs = configs
    sequence.diagnostics_root = tmp_path / "attempt"
    sequence.timings = {}
    sequence.binder = cast(Any, FakeBinder())

    sequence.run()

    assert observed == [
        (
            generated_root / "content_parsing.json",
            config_root / "chunked_conversion.json",
        ),
        (
            generated_root / "heading_evidence_parsing.json",
            config_root / "chunked_conversion.json",
        ),
    ]
