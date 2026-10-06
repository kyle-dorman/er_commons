"""Exercise the publication boundary without a service or dataset annotation."""

import json

import pytest
from test_group_claims_export import v2_fixture

from er_commons import group_claims_workflow as workflow
from er_commons.group_ranking import digest, encoded


def inputs(tmp_path, monkeypatch):
    """Use separately tested normalization with a trusted source-free fixture."""
    trusted, native = v2_fixture()
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    (prepared / "form.xml").write_text("<View/>")
    (prepared / "manifest.json").write_text("{}")
    monkeypatch.setattr(workflow, "load_prepared", lambda path: trusted)
    values = {
        "native.json": native,
        "identity.json": {"project_id": 2, "task_ids": [1], "form_sha256": digest(b"<View/>")},
        "project.json": {"id": 2, "label_config": "<View/>", "model_version": workflow.VERSION},
    }
    for name, value in values.items():
        (tmp_path / name).write_bytes(encoded(value))
    return prepared


def test_flattened_claims_keep_case_question_and_source_bindings(tmp_path, monkeypatch):
    prepared = inputs(tmp_path, monkeypatch)
    output = tmp_path / "export"
    result = workflow.export_saved(
        prepared,
        tmp_path / "native.json",
        tmp_path / "identity.json",
        tmp_path / "project.json",
        4,
        output,
    )
    assert result["status"] == "complete"
    claims = json.loads((output / "approved_claims.json").read_bytes())
    assert len(claims) == 2
    assert all(c["case_id"] == "synthetic" and c["question_id"] == "q1" for c in claims)
    assert all(c["packet_sha256"] == "a" * 64 for c in claims)
    assert all(c["question_version"] == "v1" for c in claims)
    assert claims[1]["target_claim_version"]
    with pytest.raises(FileExistsError):
        workflow.export_saved(
            prepared,
            tmp_path / "native.json",
            tmp_path / "identity.json",
            tmp_path / "project.json",
            4,
            output,
        )


@pytest.mark.parametrize("change", ["form", "task", "model"])
def test_foreign_live_form_or_import_identity_rejected(tmp_path, monkeypatch, change):
    prepared = inputs(tmp_path, monkeypatch)
    path = tmp_path / ("identity.json" if change == "task" else "project.json")
    record = json.loads(path.read_bytes())
    record[{"form": "label_config", "task": "task_ids", "model": "model_version"}[change]] = (
        [99] if change == "task" else "changed"
    )
    path.write_bytes(encoded(record))
    with pytest.raises(ValueError, match="differs"):
        workflow.export_saved(
            prepared,
            tmp_path / "native.json",
            tmp_path / "identity.json",
            tmp_path / "project.json",
            4,
            tmp_path / "export",
        )
    assert not (tmp_path / "export").exists()


def test_server_removing_one_terminal_newline_preserves_raw_export(tmp_path, monkeypatch):
    """Permit the observed server serialization without changing captured live bytes."""
    prepared = inputs(tmp_path, monkeypatch)
    (prepared / "form.xml").write_text("<View/>\n")
    identity_path = tmp_path / "identity.json"
    identity = json.loads(identity_path.read_bytes())
    identity["form_sha256"] = digest(b"<View/>\n")
    identity_path.write_bytes(encoded(identity))
    raw_live = (tmp_path / "project.json").read_bytes()
    workflow.export_saved(
        prepared,
        tmp_path / "native.json",
        identity_path,
        tmp_path / "project.json",
        4,
        tmp_path / "export",
    )
    assert (tmp_path / "export/current_project.json").read_bytes() == raw_live


def test_internal_form_whitespace_changes_still_rejected(tmp_path, monkeypatch):
    """Do not broaden terminal-newline tolerance into arbitrary form normalization."""
    prepared = inputs(tmp_path, monkeypatch)
    (prepared / "form.xml").write_text("<View>\n</View>\n")
    identity_path = tmp_path / "identity.json"
    identity = json.loads(identity_path.read_bytes())
    identity["form_sha256"] = digest(b"<View>\n</View>\n")
    identity_path.write_bytes(encoded(identity))
    project_path = tmp_path / "project.json"
    project = json.loads(project_path.read_bytes())
    project["label_config"] = "<View></View>"
    project_path.write_bytes(encoded(project))
    with pytest.raises(ValueError, match="differs"):
        workflow.export_saved(
            prepared, tmp_path / "native.json", identity_path, project_path, 4, tmp_path / "export"
        )


def investigation_authorization(tmp_path):
    """Bind the explicit policy opt-in to one exact synthetic saved export."""
    path = tmp_path / "authorization.json"
    path.write_bytes(
        encoded(
            {
                "schema_version": "task08d.policy_authorization.v1",
                "policy_revision": "task08d.investigation.v1",
                "actor": "Synthetic reviewer",
                "statement": "Allow investigation with unresolved scope and support chains.",
                "interpretation": "Synthetic policy qualification only; no eligibility approval.",
                "project_id": 2,
                "native_export_sha256": digest((tmp_path / "native.json").read_bytes()),
            }
        )
    )
    return path


def test_investigation_opt_in_preserves_native_and_authorization(tmp_path, monkeypatch):
    """A bound policy receipt survives publication without modifying saved labels."""
    prepared = inputs(tmp_path, monkeypatch)
    native_path = tmp_path / "native.json"
    native = json.loads(native_path.read_bytes())
    for result in native[0]["annotations"][0]["result"]:
        if result["from_name"] == "gaps_status":
            result["value"] = {"choices": ["unresolved"]}
    native_path.write_bytes(encoded(native))
    authorization = investigation_authorization(tmp_path)
    output = tmp_path / "export"
    workflow.export_saved(
        prepared,
        native_path,
        tmp_path / "identity.json",
        tmp_path / "project.json",
        4,
        output,
        authorization,
    )
    handoff = json.loads((output / "handoff.json").read_bytes())
    assert handoff["advancement_scope"] == "08E_investigation_only"
    assert handoff["eligibility"] == "undecided"
    assert not handoff["question_scope_resolved"]
    assert handoff["cases"][0]["fields"]["gaps_status"] == "unresolved"
    assert (output / "native_export.json").read_bytes() == native_path.read_bytes()
    assert (output / "policy_authorization.json").read_bytes() == authorization.read_bytes()


@pytest.mark.parametrize("field,value", [("project_id", 99), ("native_export_sha256", "0" * 64)])
def test_foreign_policy_authorization_rejected(tmp_path, monkeypatch, field, value):
    """A policy decision for another project or annotation cannot release this export."""
    prepared = inputs(tmp_path, monkeypatch)
    authorization = investigation_authorization(tmp_path)
    receipt = json.loads(authorization.read_bytes())
    receipt[field] = value
    authorization.write_bytes(encoded(receipt))
    with pytest.raises(ValueError, match="authorization differs"):
        workflow.export_saved(
            prepared,
            tmp_path / "native.json",
            tmp_path / "identity.json",
            tmp_path / "project.json",
            4,
            tmp_path / "export",
            authorization,
        )
    assert not (tmp_path / "export").exists()
