"""Citation-centric relationship review never infers an aggregate evidence decision."""

# Literal source warning fixtures preserve exact matching behavior.
# ruff: noqa: E501

import copy
import json
import xml.etree.ElementTree as ET

import pytest
from test_group_evidence_live import prepared  # noqa: F401

from er_commons import group_evidence_citation_review as citation
from er_commons.group_evidence_transport import compact_tasks


def queue(tasks):
    """Create native fixture identities without carrying historical human labels."""
    return [
        {**copy.deepcopy(t), "id": i, "project": 8, "annotations": []}
        for i, t in enumerate(tasks, 1)
    ]


def annotation(task, **values):
    """Create explicit fixture choices, leaving omitted links genuinely undecided."""
    return {
        "id": 10,
        "task": task["id"],
        "completed_by": "fixture",
        "result": [
            {
                "from_name": name,
                "to_name": "evidence",
                "type": "textarea" if name.endswith("_note") else "choices",
                "value": {"text" if name.endswith("_note") else "choices": [value]},
            }
            for name, value in values.items()
        ],
    }


def options(tasks, root):
    """Bind the exact trusted queue and form independently of native exported values."""
    return dict(
        expected_tasks=tasks,
        project_id=8,
        actual_form=citation.citation_form(tasks[0]["data"]["project_capacity"]),
        reviewer_id="fixture",
        export_lineage="separate-fixture",
        data_root=root,
    )


def test_citation_queue_exact_sources_no_aggregate_and_optional_claims(prepared):  # noqa: F811
    original, root = prepared
    before = copy.deepcopy(original)
    tasks = citation.prepare_tasks(original, data_root=root)
    assert original == before
    assert len(tasks) == sum(len(t["data"]["packet"]["candidates"]) for t in original)
    form = citation.citation_form(tasks[0]["data"]["project_capacity"])
    ET.fromstring(form)
    assert "outcome" not in form
    assert "source_summary" not in form
    assert "Link another claim" in form
    assert "max-height" not in form
    assert "<hr/>" in tasks[0]["data"]["evidence_html"]
    assert all(
        t["data"]["packet"]
        == next(
            o["data"]["packet"]
            for o in original
            if o["data"]["case_label"] == t["data"]["case_label"]
        )
        for t in tasks
    )
    for task in tasks:
        assert {s["claim"]["claim_id"] for s in task["data"]["slots"]} == {
            c["claim_id"] for c in task["data"]["packet"]["claims"]
        }


def test_blank_saved_links_remain_unreviewed_and_explicit_negative_is_distinct(prepared):  # noqa: F811
    originals, root = prepared
    tasks = citation.prepare_tasks(originals, data_root=root)
    exported = queue(tasks)
    exported[0]["annotations"] = [annotation(exported[0])]
    result = citation.normalize_export(exported, **options(tasks, root))
    assert result["records"][0]["relationships"][0]["relationship"] == "unreviewed"
    assert result["advancing_claim_ids"] == []
    assert result["eligibility"] == "undecided"
    slot = tasks[0]["data"]["slots"][0]["prefix"]
    exported[0]["annotations"] = [annotation(exported[0], **{slot + "_label": "not_support"})]
    result = citation.normalize_export(exported, **options(tasks, root))
    assert result["records"][0]["relationships"][0]["relationship"] == "not_support"
    assert result["records"][0]["source_candidate"]["anchors"]
    assert result["pending_task_ids"] == list(range(2, len(tasks) + 1))


@pytest.mark.parametrize(
    "mutation",
    ["form", "project", "task", "source", "choice", "unknown", "reviewer", "cancelled", "missing"],
)
def test_native_tampering_rejected(prepared, mutation):  # noqa: F811
    originals, root = prepared
    tasks = citation.prepare_tasks(originals, data_root=root)
    exported = queue(tasks)
    opts = options(tasks, root)
    prefix = tasks[0]["data"]["slots"][0]["prefix"]
    exported[0]["annotations"] = [annotation(exported[0], **{prefix + "_label": "supports"})]
    if mutation == "form":
        opts["actual_form"] += "changed"
    elif mutation == "project":
        exported[0]["project"] = 9
    elif mutation == "task":
        opts["expected_tasks"][0]["id"] = 999
    elif mutation == "source":
        exported[0]["data"]["candidate_id"] = "changed"
    elif mutation == "choice":
        exported[0]["annotations"][0]["result"][0]["value"]["choices"] = ["approved"]
    elif mutation == "unknown":
        exported[0]["annotations"][0]["result"][0]["from_name"] = "o999_label"
    elif mutation == "reviewer":
        exported[0]["annotations"][0]["completed_by"] = "someone else"
    elif mutation == "cancelled":
        exported[0]["annotations"][0]["was_cancelled"] = True
    else:
        exported.pop()
    with pytest.raises(ValueError):
        citation.normalize_export(exported, **opts)


def test_compact_canonical_bytes_revalidated_and_provenance_retained(prepared, tmp_path):  # noqa: F811
    originals, root = prepared
    tasks = citation.prepare_tasks(originals, data_root=root)
    paths = {}
    for task in tasks:
        data = task["data"]
        path = root / (data["case_label"] + ".json")
        path.write_text(json.dumps(data["packet"]))
        paths[data["case_label"]] = path
    compact = compact_tasks(tasks, packet_paths_by_case=paths, data_root=root)
    exported = queue(compact)
    result = citation.normalize_export(exported, **options(compact, root))
    assert len(result["pending_task_ids"]) == len(tasks)
    next(iter(paths.values())).write_text("{}")
    with pytest.raises(ValueError):
        citation.normalize_export(exported, **options(compact, root))


def test_display_suppresses_only_known_process_text_preserving_underlying_warnings(prepared):  # noqa: F811
    originals, root = prepared
    candidate = copy.deepcopy(originals[0]["data"]["packet"]["candidates"][0])
    candidate["limitations"] = [
        citation._PROCESS_WARNING,
        "Exact canonical bytes retained. Fresh agent render comparison is not a saved human table-usability or evidence decision.",
        "Figure 2 and its canonical placeholder/captions remain part of the unit boundary. Parent must preserve any unavailable-visual limitation; no map-distance or count inference was made.",
        "Substantive contradictory receptor value.",
    ]
    before = copy.deepcopy(candidate)
    display = citation._source_html(candidate, "E01")
    assert candidate == before
    assert "Task 06H" not in display and "Parent must" not in display
    assert "Fresh agent" not in display and "Astra proposal" not in display
    assert "no map distances or counts were evaluated" in display
    assert "Substantive contradictory receptor value." in display
