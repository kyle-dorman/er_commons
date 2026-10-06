"""Source-free Task08B rendering and ordering tests."""

from copy import deepcopy
from typing import Any

import pytest
from jsonschema import ValidationError  # type: ignore[import-untyped]

from er_commons.group_selection import build_tasks, validate_tasks


def synthetic_queue(count: int = 5) -> list[dict[str, Any]]:
    """Exercise long linked text, supplements and warnings without dataset content."""
    units = []
    candidates = []
    ranking = []
    supplements = []
    for rank in range(1, count + 1):
        cid, rid = f"SYNTHETIC-C{rank}", f"SYNTHETIC-R{rank}"
        units.extend(
            [
                {
                    "unit_id": cid,
                    "official_label": cid,
                    "unit_kind": "comment",
                    "text": f"Synthetic comment {rank}: <literal source> & original concern.",
                    "source_pages": [rank],
                    "span_ids": [f"span-c{rank}"],
                },
                {
                    "unit_id": rid,
                    "official_label": rid,
                    "unit_kind": "response",
                    "text": f"Response {rank} begins.\n"
                    + "Long synthetic linked response.\n" * 100
                    + f"END OF COMPLETE RESPONSE {rank}.",
                    "source_pages": [rank + 10],
                    "span_ids": [f"span-r{rank}"],
                },
            ]
        )
        candidates.append(
            {
                "comment_id": cid,
                "comment_label": cid,
                "context_unit_ids": [cid, rid],
                "reference_outcome_ids": [],
                "planning_record": {"synthetic_warning": "incidental revision retained"},
            }
        )
        ranking.append(
            {
                "comment_id": cid,
                "rank": rank,
                "question_quality": "Synthetic advisory question reason; not selection.",
                "response_quality": "Synthetic response reason; not eligibility.",
                "concerns": ["SYNTHETIC warning: source limitations remain."],
                "question_anchors": [],
                "response_anchors": [],
            }
        )
        supplements.append(
            {
                "unit_id": rid,
                "text": f"COMPLETE FOOTNOTE {rank}.",
                "reason": "Synthetic source-page supplement.",
            }
        )
    packet = {
        "group": {"group": "SYNTHETIC qualification only"},
        "candidates": candidates,
        "source_units": units,
        "source_supplements": supplements,
        "outcomes": [],
        "limitations": {"sampled_review": True},
    }
    return build_tasks(
        packet,
        {"ranking": ranking},
        input_sha256="a" * 64,
        proposal_sha256="b" * 64,
        namespace="synthetic",
        recorded_limitations=["AUTOMATED SOFTWARE QA ONLY; no dataset decisions."],
    )


def test_complete_escaped_source_and_separate_records() -> None:
    """Long source and supplement survive while comment-only material stays isolated."""
    tasks = synthetic_queue()
    data = tasks[0]["data"]
    assert "&lt;literal source&gt; &amp;" in data["comment_html"]
    assert "END OF COMPLETE RESPONSE 1." in data["response_html"]
    assert "COMPLETE FOOTNOTE 1." in data["response_html"]
    assert "response" not in data["original_comment"]["text"]
    assert "response_quality" not in data["original_comment"]
    assert set(tasks[0]) == {"data"}


@pytest.mark.parametrize("change", ["reorder", "truncate", "other_comment", "prefill"])
def test_reject_bad_queue(change: str) -> None:
    """Catch loss of order/source closure and accidental model label insertion."""
    tasks = deepcopy(synthetic_queue())
    if change == "reorder":
        tasks.reverse()
    elif change == "truncate":
        tasks[0]["data"]["response_html"] = "short summary"
    elif change == "other_comment":
        tasks[0]["data"]["response_context"]["units"][0]["unit_kind"] = "comment"
    else:
        tasks[0]["predictions"] = []
    with pytest.raises((ValueError, ValidationError)):
        validate_tasks(tasks)


def test_provenance_preserved_but_not_rendered() -> None:
    """The simplified display retains existing advice and warnings only as provenance."""
    data = synthetic_queue()[0]["data"]
    assert data["advisory"]["question_quality"]
    assert data["source_warnings"]["ranking_concerns"]
    assert "warnings_html" not in data and "advisory_html" not in data
    display = data["comment_html"] + data["response_html"]
    assert "SYNTHETIC warning" not in display
    assert "Synthetic advisory" not in display
    assert "Synthetic source-page supplement." not in display


def test_form_has_only_selection_controls() -> None:
    """Ensure the reusable form does not expose removed controls or provenance panels."""
    from xml.etree import ElementTree

    from er_commons.group_selection import FORM

    tree = ElementTree.fromstring(FORM.read_bytes())
    assert {element.attrib["name"] for element in tree.iter("Choices")} == {
        "selection",
        "selection_reason",
    }
    assert {element.attrib["value"] for element in tree.iter("HyperText")} == {
        "$comment_html",
        "$response_html",
    }


def _v2_ranking_fixture(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch, count: int
) -> tuple[Any, Any, dict[str, Any]]:
    """Seal realistic v2 inputs while replacing only the external source replay boundary."""
    import json

    from er_commons import group_ranking_v2
    from er_commons.group_ranking import digest, encoded

    tasks = synthetic_queue(count)
    packet = {
        "group": {"group": "SYNTHETIC qualification only"},
        "inventory_id": "synthetic-inventory",
        "candidates": [t["data"]["source_warnings"]["candidate_provenance"] for t in tasks],
        "source_units": [
            u
            for t in tasks
            for u in [t["data"]["original_comment"], *t["data"]["response_context"]["units"]]
        ],
        "source_supplements": [
            s for t in tasks for s in t["data"]["response_context"]["supplements"]
        ],
        "outcomes": [],
        "limitations": {"sampled_review": True},
    }
    packet["candidates"].reverse()
    packet["source_supplements"][0]["reason"] = (
        "Complete source page context; adjacent text is not a candidate"
    )
    packet["source_supplements"][0]["text"] = "FULL PAGE <context> & adjacent source."
    packet["source_supplements"][0]["page_id"] = "response-page-1"
    # The upstream full-page deduplication can attach a response page to another comment.
    packet["source_supplements"][0]["unit_id"] = "SYNTHETIC-C1"
    packet["source_supplements"].append(
        {
            "unit_id": "SYNTHETIC-R1",
            "page_id": "unrelated-page",
            "reason": "Complete source page context; adjacent text is not a candidate",
            "text": "UNRELATED PAGE MUST NOT DISPLAY",
        }
    )
    records = tmp_path / "source_records.jsonl"
    records.write_bytes(
        b"".join(
            encoded(
                {
                    "record_type": "source_span",
                    "span_id": unit["span_ids"][0],
                    "fragments": [
                        {
                            "page_id": (
                                "response-page-1"
                                if unit["unit_id"] == "SYNTHETIC-R1"
                                else unit["unit_id"]
                            )
                        }
                    ],
                }
            ).replace(b"\n", b"")
            + b"\n"
            for unit in packet["source_units"]
        )
    )
    component_path = tmp_path / "components.json"
    component_path.write_bytes(
        encoded(
            [
                {
                    "role": "source_records",
                    "path": str(records),
                    "sha256": digest(records.read_bytes()),
                }
            ]
        )
    )
    packet["input_bindings"] = [
        {"path": str(p), "sha256": digest(p.read_bytes())} for p in (component_path, records)
    ]
    packet["preparation"] = {"data_root": str(tmp_path)}
    input_bytes, prompt = encoded(packet), b"Synthetic shared prompt"
    if count <= 3:
        proposal = group_ranking_v2.small_group_proposal(packet, input_bytes, prompt)
    else:
        proposal = {
            "schema_version": "task08a.proposal.v2",
            "input_sha256": digest(input_bytes),
            "prompt_sha256": digest(prompt),
            "prompt_version": group_ranking_v2.VERSION,
            "model": "gpt-6-astra",
            "preparation_mode": "model_ranked",
            "ranking_not_needed_reason": None,
            "proposal_version": 1,
            "reranking_reason": None,
            "tie_groups": [],
            "ranking": [
                {"comment_id": c["comment_id"], "rank": i}
                for i, c in enumerate(packet["candidates"], 1)
            ],
        }
    source_paths = [
        tmp_path / name for name in ("input.json", "proposal.json", "prompt.md", "spec.md")
    ]
    for path, content in zip(
        source_paths, [input_bytes, encoded(proposal), prompt, b"Synthetic spec"], strict=True
    ):
        path.write_bytes(content)
    monkeypatch.setattr(group_ranking_v2, "replay", lambda packet: None)
    ranking_root = tmp_path / "ranking"
    handoff = group_ranking_v2.publish(*source_paths, ranking_root)
    entry = {
        "group": handoff["group"],
        "candidate_count": count,
        "slug": "synthetic",
        "state": "completed",
        "validation": "passed",
        "mode": "model_ranking" if count > 3 else "deterministic_preparation",
        "model": proposal["model"],
        "interface_version": group_ranking_v2.VERSION,
        **{
            name: {
                "path": str(ranking_root / f"{name}.json"),
                "sha256": digest((ranking_root / f"{name}.json").read_bytes()),
            }
            for name in ("input", "proposal", "handoff", "manifest", "completion")
        },
    }
    index_path = tmp_path / "handoff_index.json"
    index_path.write_bytes(encoded({"grouping_sha256": "c" * 64, "groups": [entry]}))
    result_path = tmp_path / "result.json"
    result_path.write_bytes(
        encoded(
            {
                "schema_version": "task08a.remaining_groups.result.v2",
                "status": "complete",
                "grouping_sha256": "c" * 64,
                "artifacts": {
                    "handoff_index": {
                        "path": str(index_path),
                        "sha256": digest(index_path.read_bytes()),
                    }
                },
            }
        )
    )
    assert json.loads((ranking_root / "handoff.json").read_bytes()) == handoff
    return ranking_root, result_path, proposal


@pytest.mark.parametrize("count", [1, 2, 3, 4])
def test_v2_intake_complete_prepare_and_replay(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch, count: int
) -> None:
    """Both saved order modes prepare blank source-bound tasks without invented reasons."""
    from er_commons.group_selection import INTAKE_REVISION, load_prepared, prepare

    root, result, proposal = _v2_ranking_fixture(tmp_path, monkeypatch, count)
    output = tmp_path / "prepared"
    manifest = prepare(root, result, tmp_path, output)
    tasks = load_prepared(output)
    assert manifest["intake_revision"] == INTAKE_REVISION
    assert [t["data"]["comment_id"] for t in tasks] == [
        r["comment_id"] for r in proposal["ranking"]
    ]
    for task, row in zip(tasks, proposal["ranking"], strict=True):
        assert set(task) == {"data"}
        assert task["data"]["advisory"] == row
        assert "ranking_concerns" not in task["data"]["source_warnings"]
    page_task = next(t for t in tasks if t["data"]["comment_id"] == "SYNTHETIC-C1")
    assert "Source page context" in page_task["data"]["response_html"]
    assert "FULL PAGE &lt;context&gt; &amp; adjacent source." in page_task["data"]["response_html"]
    assert "UNRELATED PAGE MUST NOT DISPLAY" not in page_task["data"]["response_html"]
    assert (
        "Complete source page context; adjacent text is not a candidate"
        not in page_task["data"]["response_html"]
    )
    with pytest.raises(FileExistsError):
        prepare(root, result, tmp_path, output)


@pytest.mark.parametrize(
    "mutation", ["hash", "identity", "mode", "model", "version", "blocked", "duplicate", "grouping"]
)
def test_v2_intake_rejects_changed_index_bindings(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    """A complete source seal never excuses invalid indexed identities or readiness."""
    import json

    from er_commons.group_ranking import digest, encoded
    from er_commons.group_selection import verify_ranking

    root, result_path, _ = _v2_ranking_fixture(tmp_path, monkeypatch, 3)
    index_path = tmp_path / "handoff_index.json"
    index = json.loads(index_path.read_bytes())
    row = index["groups"][0]
    if mutation == "hash":
        row["input"]["sha256"] = "0" * 64
    elif mutation == "identity":
        row["candidate_count"] += 1
    elif mutation == "mode":
        row["mode"] = "model_ranking"
    elif mutation == "model":
        row["model"] = "gpt-6-astra"
    elif mutation == "version":
        row["interface_version"] = "task08a.ranking.v1"
    elif mutation == "blocked":
        row["state"] = "blocked"
    elif mutation == "duplicate":
        index["groups"].append(deepcopy(row))
    else:
        index["grouping_sha256"] = "0" * 64
    index_path.write_bytes(encoded(index))
    result = json.loads(result_path.read_bytes())
    result["artifacts"]["handoff_index"]["sha256"] = digest(index_path.read_bytes())
    result_path.write_bytes(encoded(result))
    with pytest.raises(ValueError):
        verify_ranking(root, result_path, tmp_path)


def test_v2_intake_rejects_unbound_index(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """The completion record's index digest is mandatory before reading group entries."""
    from er_commons.group_selection import verify_ranking

    root, result, _ = _v2_ranking_fixture(tmp_path, monkeypatch, 4)
    with (tmp_path / "handoff_index.json").open("ab") as handle:
        handle.write(b"\n")
    with pytest.raises(ValueError, match="Checksum"):
        verify_ranking(root, result, tmp_path)


def test_empty_linked_response_context_stays_explicit_and_source_free() -> None:
    """A valid candidate without links stays reviewable without invented response units."""
    from er_commons.group_selection import _response_html

    tasks = synthetic_queue(1)
    context = {"units": [], "supplements": [], "outcomes": []}
    data = tasks[0]["data"]
    data["response_context"] = context
    data["response_html"] = _response_html(context)
    validate_tasks(tasks)
    assert data["response_html"] == "<p>No linked responses in this handoff.</p>"
    assert data["response_context"] == {"units": [], "supplements": [], "outcomes": []}
    data["response_html"] = "<p>Invented source response.</p>"
    with pytest.raises(ValueError, match="Response display differs"):
        validate_tasks(tasks)
