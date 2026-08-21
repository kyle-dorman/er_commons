from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from er_commons.document_parsing.content_parsing import chunked_application


def test_derived_failure_retains_standard_producer_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Chunk conversion success must not weaken downstream failure evidence."""
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{}")
    config_path = tmp_path / "config.json"
    config_path.write_text("{}")
    prepared = SimpleNamespace(
        source=SimpleNamespace(source_id="source"),
        source_manifest_path=tmp_path / "source/manifest.json",
        identity=SimpleNamespace(run_id="old-producer"),
    )
    producer_identity = SimpleNamespace(run_id="producer-new", payload={})
    retained: dict[str, Any] = {}

    monkeypatch.setattr(
        chunked_application,
        "load_content_parsing_config",
        lambda _: (SimpleNamespace(artifact_relative_root="task"), "sha"),
    )
    monkeypatch.setattr(
        chunked_application,
        "prepare_content_parsing",
        lambda *args, **kwargs: prepared,
    )
    monkeypatch.setattr(
        chunked_application,
        "ensure_chunked_conversion_bundle",
        lambda *args, **kwargs: SimpleNamespace(
            conversion_id="dconv1-test",
            root=tmp_path / "conversion",
        ),
    )
    monkeypatch.setattr(
        chunked_application,
        "build_content_parsing_identity",
        lambda **kwargs: producer_identity,
    )
    monkeypatch.setattr(
        chunked_application,
        "read_json_object",
        lambda _: {"identity": {}},
    )
    monkeypatch.setattr(chunked_application, "replace", lambda value, **kwargs: value)
    monkeypatch.setattr(chunked_application, "task_artifact_root", lambda *args: tmp_path / "task")
    monkeypatch.setattr(chunked_application, "installed_table_environment", lambda: {})
    monkeypatch.setattr(chunked_application, "code_identity", lambda *args, **kwargs: {})
    monkeypatch.setattr(chunked_application, "parsing_code_paths", lambda _: ())

    def fail_derived(**kwargs: object) -> Path:
        progress = cast(Any, kwargs["progress"])
        progress.stage = "route"
        raise RuntimeError("routing failed")

    def retain(**kwargs: object) -> Path:
        retained.update(kwargs)
        return tmp_path / "task/attempts/failed"

    monkeypatch.setattr(chunked_application, "build_and_publish_derived", fail_derived)
    monkeypatch.setattr(chunked_application, "preserve_failed_attempt", retain)

    request = cast(
        Any,
        SimpleNamespace(
            plan_path=plan_path,
            output_root=tmp_path / "chunked-runs",
        ),
    )
    with pytest.raises(RuntimeError, match="routing failed"):
        chunked_application.run_chunked_document_parsing(
            tmp_path,
            config_path,
            plan_path,
            request=request,
        )

    assert retained["producer_run_id"] == "producer-new"
    assert retained["failed_stage"] == "route"
    assert isinstance(retained["error"], RuntimeError)
