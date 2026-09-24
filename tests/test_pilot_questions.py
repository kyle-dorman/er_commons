"""Exercise the comment-only projection and human approval boundary."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from er_commons.pilot_questions import PREDICTION_VERSION, build_trial_task, normalize_review


def _write(path: Path, data: Any) -> str:
    """Save fixture bytes and return their exact checksum."""
    content = json.dumps(data).encode()
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


@pytest.fixture
def packet(tmp_path: Path) -> Path:
    """Provide minimal comment-only evidence with deliberately untrusted extra fields."""
    original = "Comment <A>\r\nWhat about housing?\r\n"
    digest = hashlib.sha256(original.encode()).hexdigest()
    source = {
        "schema_version": "er_commons.task07b.comment_drafting_input.v1",
        "comment_id": "unit-a",
        "comment_label": "A",
        "original_comment": original,
        "original_comment_sha256": digest,
        "source_pages": [10],
        "source_span_ids": ["span-a"],
        "source_note": "Keep exact text.",
        "official_response": "EXCLUDED_RESPONSE",
    }
    proposal = {
        "schema_version": "er_commons.task07b.concern_proposal.v1",
        "comment_id": "unit-a",
        "comment_label": "A",
        "input_comment_sha256": digest,
        "proposal_version": "test-v1",
        "concerns": ["What about <housing>?"],
        "draft_note": "",
        "model": None,
        "official_response": "EXCLUDED_RESPONSE",
    }
    _write(tmp_path / "proposal.json", proposal)
    prompt = tmp_path / "drafting_prompt.md"
    prompt.write_text("Use only the comment.")
    _write(
        tmp_path / "packet_manifest.json",
        {
            "schema_version": "er_commons.task07b.drafting_packet_manifest.v1",
            "selected_case_id": "unit-a",
            "comment_label": "A",
            "original_comment_sha256": digest,
            "files": {
                "comment_input.json": _write(tmp_path / "comment_input.json", source),
                "drafting_prompt.md": hashlib.sha256(prompt.read_bytes()).hexdigest(),
            },
        },
    )
    return tmp_path


def _annotation(status: str = "approved", text: str = "1. Edited concern.") -> dict[str, Any]:
    """Construct a saved human annotation with explicit task and reviewer binding."""
    return {
        "id": 22,
        "task": 7,
        "completed_by": 3,
        "result": [
            {
                "from_name": "review_status",
                "to_name": "comment",
                "type": "choices",
                "value": {"choices": [status]},
            },
            {
                "from_name": "concerns",
                "to_name": "comment",
                "type": "textarea",
                "value": {"text": [text]},
            },
        ],
    }


def test_projection_preserves_source_and_excludes_response(packet: Path) -> None:
    task = build_trial_task(packet)
    assert "EXCLUDED_RESPONSE" not in json.dumps(task)
    assert task["data"]["original_comment"] == "Comment <A>\r\nWhat about housing?\r\n"
    assert "&lt;A&gt;\r\n" in task["data"]["comment_html"]
    assert "&lt;housing&gt;" in task["data"]["proposal_html"]
    assert "annotations" not in task
    prediction = task["predictions"][0]
    assert [r["from_name"] for r in prediction["result"]] == ["concerns"]
    with pytest.raises(ValueError):
        normalize_review({**task, "id": 7}, prediction, expected_task=task)


def test_prediction_selection_preserves_distinct_proposal_versions(packet: Path) -> None:
    """One project selector must seed every packet without losing draft provenance."""
    tasks = []
    for version in ("trial-v1", "remaining-case-v1"):
        proposal = json.loads((packet / "proposal.json").read_bytes())
        proposal["proposal_version"] = version
        proposal_hash = _write(packet / "proposal.json", proposal)
        task = build_trial_task(packet)
        assert task["data"]["original_proposal"]["proposal_version"] == version
        assert task["data"]["proposal_sha256"] == proposal_hash
        tasks.append(task)

    selected = [
        prediction
        for task in tasks
        for prediction in task["predictions"]
        if prediction["model_version"] == PREDICTION_VERSION
    ]
    assert len(selected) == len(tasks)
    for task, prediction in zip(tasks, selected, strict=True):
        assert prediction["result"][0]["value"]["text"] == [task["data"]["proposal_text"]]


@pytest.mark.parametrize("filename", ["comment_input.json", "drafting_prompt.md"])
def test_packet_checksum_tampering(packet: Path, filename: str) -> None:
    with (packet / filename).open("ab") as handle:
        handle.write(b" ")
    with pytest.raises(ValueError, match="Checksum mismatch"):
        build_trial_task(packet)


@pytest.mark.parametrize("field", ["comment_id", "comment_label", "input_comment_sha256"])
def test_proposal_identity_tampering(packet: Path, field: str) -> None:
    proposal = json.loads((packet / "proposal.json").read_bytes())
    proposal[field] = "other"
    _write(packet / "proposal.json", proposal)
    with pytest.raises(ValueError, match="identity mismatch"):
        build_trial_task(packet)


@pytest.mark.parametrize("status", ["approved", "unclear", "needs_context"])
def test_review_preserves_edits_and_provenance(packet: Path, status: str) -> None:
    task = {**build_trial_task(packet), "id": 7}
    text = "1. Edited concern.\r\n  Continued.\r\n2. Another concern.  \r\n"
    review = normalize_review(
        task, _annotation(status, text), expected_task=build_trial_task(packet)
    )
    assert review["concerns"] == text
    assert review["eligible_for_next_stage"] is (status == "approved")
    assert review["original_proposal"]["concerns"] == ["What about <housing>?"]
    assert review["proposal_sha256"] == task["data"]["proposal_sha256"]
    assert review["reviewer"] == 3


@pytest.mark.parametrize("text", ["", "  ", "Unnumbered", "1. ", "1. Fine\n2. ", "2. Fine"])
def test_approved_requires_numbered_nonempty_items(packet: Path, text: str) -> None:
    with pytest.raises(ValueError, match="numbered"):
        normalize_review(
            {**build_trial_task(packet), "id": 7},
            _annotation(text=text),
            expected_task=build_trial_task(packet),
        )


@pytest.mark.parametrize("status", ["unclear", "needs_context"])
def test_unresolved_may_retain_empty_list(packet: Path, status: str) -> None:
    review = normalize_review(
        {**build_trial_task(packet), "id": 7},
        _annotation(status, ""),
        expected_task=build_trial_task(packet),
    )
    assert not review["eligible_for_next_stage"]


@pytest.mark.parametrize(
    "change", ["duplicate", "foreign", "extra", "cancel", "task", "status", "multi"]
)
def test_invalid_review_rejected(packet: Path, change: str) -> None:
    annotation = _annotation()
    if change == "duplicate":
        annotation["result"].append(annotation["result"][0])
    elif change == "foreign":
        annotation["result"][0]["to_name"] = "response"
    elif change == "extra":
        annotation["result"][0]["from_name"] = "rating"
    elif change == "cancel":
        annotation["was_cancelled"] = True
    elif change == "task":
        annotation["task"] = 8
    elif change == "status":
        annotation["result"][0]["value"]["choices"] = ["great"]
    elif change == "multi":
        annotation["result"][1]["value"]["text"] = ["1. One", "2. Two"]
    with pytest.raises(ValueError):
        normalize_review(
            {**build_trial_task(packet), "id": 7},
            annotation,
            expected_task=build_trial_task(packet),
        )


def test_resealed_source_still_must_match_original_identity(packet: Path) -> None:
    source = json.loads((packet / "comment_input.json").read_bytes())
    source["original_comment"] += "Changed meaning."
    manifest = json.loads((packet / "packet_manifest.json").read_bytes())
    manifest["files"]["comment_input.json"] = _write(packet / "comment_input.json", source)
    _write(packet / "packet_manifest.json", manifest)
    with pytest.raises(ValueError, match="text identity mismatch"):
        build_trial_task(packet)


def test_cli_no_clobber(packet: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from er_commons.pilot_questions import main

    output = packet / "task.json"
    monkeypatch.setattr(
        "sys.argv",
        ["pilot_questions", "prepare", "--drafting-dir", str(packet), "--output", str(output)],
    )
    main()
    saved = output.read_bytes()
    assert len(json.loads(saved)) == 1
    with pytest.raises(FileExistsError):
        main()
    assert output.read_bytes() == saved


@pytest.mark.parametrize(
    "field",
    [
        "original_comment",
        "comment_id",
        "source_span_ids",
        "proposal_sha256",
        "original_proposal",
        "comment_html",
    ],
)
def test_exported_task_tampering_rejected(packet: Path, field: str) -> None:
    expected = build_trial_task(packet)
    exported = {**build_trial_task(packet), "id": 7}
    exported["data"][field] = "tampered"
    with pytest.raises(ValueError, match="verified drafting packet"):
        normalize_review(exported, _annotation(), expected_task=expected)


def test_draft_note_is_readonly_and_html_escaped(packet: Path) -> None:
    proposal = json.loads((packet / "proposal.json").read_bytes())
    proposal["draft_note"] = "Missing <prior context>; do not assume an answer."
    _write(packet / "proposal.json", proposal)
    task = build_trial_task(packet)
    assert "Draft note:" in task["data"]["proposal_html"]
    assert "Missing &lt;prior context&gt;" in task["data"]["proposal_html"]
    assert task["data"]["original_proposal"]["draft_note"] == proposal["draft_note"]
    assert [r["from_name"] for r in task["predictions"][0]["result"]] == ["concerns"]
    assert "Missing" not in task["data"]["proposal_text"]


def test_empty_note_preserves_existing_proposal_display(packet: Path) -> None:
    task = build_trial_task(packet)
    assert task["data"]["proposal_html"] == "<ol><li>What about &lt;housing&gt;?</li></ol>"
