"""Grouped source cards preserve native controls, packet identity and saved decisions."""

import copy
import xml.etree.ElementTree as ET

import pytest
from test_group_evidence import native
from test_group_evidence_live import prepared  # noqa: F401

from er_commons import group_evidence_cards as cards
from er_commons import group_evidence_live as live


def controls(form):
    """Compare full native control subtrees, including targets, choices and note behavior."""
    return {
        node.attrib["name"]: ET.tostring(node, encoding="unicode")
        for node in ET.fromstring(form).iter()
        if node.tag in {"Choices", "TextArea"}
    }


def test_grouped_cards_order_and_native_control_parity(prepared):  # noqa: F811
    tasks, _ = prepared
    original = copy.deepcopy(tasks)
    fresh = cards.prepare_tasks(live.bind_project_capacity(tasks))
    assert tasks == original
    for old, new in zip(tasks, fresh, strict=True):
        data = new["data"]
        assert data["packet"] == old["data"]["packet"]
        assert data["candidate_aliases"] == old["data"]["candidate_aliases"]
        assert data["claim"] == old["data"]["claim"]
        assert "reviewer_notes_html" not in data
        if data["slots"][0]["candidate_ids"]:
            card = data["c001_p01_card_html"]
            assert card.index("<h2>E") < card.index("Summary")
            assert card.index("Summary") < card.index("Why retrieved") < card.index("Parsed source")
    legacy = live.claim_form(1)
    form = live.claim_form(1, layout_revision=cards.VERSION)
    assert controls(legacy) == controls(form)
    assert "max-height" not in form and "grid-template-columns" not in form
    assert form.index('value="$c001_p01_card_html"') < form.index('value="$c001_p01_title"')
    assert form.index('name="c001_p01_note"') < form.index("Overall outcome")
    assert 'name="evidence"' in form
    assert "reviewer_notes" not in form


def test_cards_saved_decisions_and_versioned_export(prepared):  # noqa: F811
    tasks, root = prepared
    tasks = cards.prepare_tasks(live.bind_project_capacity(tasks))
    task = tasks[0]
    annotation = native(
        c001_outcome="partial",
        c001_note="Unresolved scope remains.",
        c001_p01_label="partial",
        c001_p01_note="Covered the method; not the outcome.",
        source_summary="Preserved curator note",
    )
    result = live.normalize_claim(
        {**task, "id": 21}, annotation, expected_task=task, export_lineage="cards-fixture"
    )
    assert result["review_complete"]
    assert result["layout_revision"] == cards.VERSION
    assert result["source_summary"] == "Preserved curator note"
    assert result["native_annotation"] == annotation
    exported = [
        {**copy.deepcopy(t), "id": i, "project": 7, "annotations": []}
        for i, t in enumerate(tasks, 1)
    ]
    options = dict(
        expected_tasks=tasks,
        project_id=7,
        actual_form=live.claim_form(1, layout_revision=cards.VERSION),
        reviewer_id="synthetic-only",
        export_lineage="cards-fixture",
        data_root=root,
    )
    assert live.normalize_export(exported, **options)["advancing_claim_ids"] == []
    options["actual_form"] = live.claim_form(1)
    with pytest.raises(ValueError, match="Live form differs"):
        live.normalize_export(exported, **options)
    with pytest.raises(ValueError, match="Unsupported"):
        live.claim_form(1, layout_revision="unknown")
    with pytest.raises(ValueError, match="Fresh expanded"):
        cards.prepare_tasks(tasks)
