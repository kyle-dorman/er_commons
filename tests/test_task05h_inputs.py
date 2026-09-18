"""Small synthetic rows exercise release joins and truthful inherited limitations."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

import pytest

from er_commons.response_inventory.release_inputs import ReleaseInputs, verify_reference
from er_commons.response_inventory.release_validation import (
    COVERAGE,
    NONLINK_COUNTS,
    validate_composition,
)


def composition() -> ReleaseInputs:
    """Build all frozen membership counts without copying upstream source payloads."""
    units = [
        {"record_type": "source_unit", "unit_id": f"{kind}-{index}", "unit_kind": kind}
        for kind, count in (("comment", 1011), ("response", 1010), ("general_response", 8))
        for index in range(count)
    ]
    source = list(units)
    binding: dict[str, Any] = {
        "other_mentions_not_proven_draft_final_equivalent": 64,
        "source_substitution": {
            "draft_final_equivalence_proven": False,
            "semantic_equivalence": False,
        },
        "response_specific": [
            {"mention_ids": ["mention-0"], "unit_id": "response-0"},
            {"mention_ids": ["mention-1", "mention-2"], "unit_id": "response-0"},
        ],
    }
    reasons = [reason for reason, count in NONLINK_COUNTS.items() for _ in range(count)]
    outcomes, links, diagnostics = [], [], []
    for index in range(511):
        mention = {
            "mention_id": f"mention-{index}",
            "source_unit_id": "response-0",
            "mention_span_id": f"span-{index}",
            "raw_text_sha256": "raw",
            "reference_domain": "draft_eir",
        }
        source.append({"record_type": "reference_mention", **mention})
        annotation = {"target_id": f"target-{index}", "target_type": "section"}
        warning = None
        if index < 66:
            warning = {
                "binding": copy.deepcopy(binding),
                "draft_final_equivalence_proven": False,
                "response_specific": [
                    item
                    for item in binding["response_specific"]
                    if mention["mention_id"] in item["mention_ids"]
                ],
            }
        outcome = {
            **mention,
            "source_kind": "response",
            "logical_source_ids": ["deir_appendix_f1"] if index < 66 else ["deir_main"],
            "final_f1_warning": warning,
            "input_refs": [],
            "resolver_rule": "exact",
            "target_annotations": [annotation] if index < 468 else [],
            "compatible_target_ids": [annotation["target_id"]] if index < 468 else [],
            "outcome": "resolved" if index < 468 else "terminal_nonlink",
            "link_id": f"link-{index}" if index < 468 else None,
            "terminal_reason": None if index < 468 else reasons[index - 468],
        }
        outcomes.append(outcome)
        if index < 468:
            links.append(
                {
                    **{
                        key: outcome[key]
                        for key in (
                            "mention_id",
                            "source_unit_id",
                            "link_id",
                            "resolver_rule",
                            "input_refs",
                            "final_f1_warning",
                        )
                    },
                    "target_id": annotation["target_id"],
                    "target_annotation": annotation,
                }
            )
        else:
            diagnostics.append(
                {
                    key: outcome[key]
                    for key in ("mention_id", "mention_span_id", "terminal_reason", "input_refs")
                }
            )
    edges = [
        {"edge_id": f"edge-{i}", "source_unit_id": "comment-0", "target_unit_id": "response-0"}
        for i in range(1538)
    ]
    views = [
        {
            "view_id": f"view-{i}",
            "root_unit_id": f"comment-{i}",
            "ordered_unit_ids": [f"comment-{i}"],
            "edge_ids": [],
        }
        for i in range(1011)
    ]
    limitations: dict[str, Any] = {
        "coverage": dict(COVERAGE),
        "final_f1_warning_binding": binding,
        "target_limitations": {
            "entries": [
                {
                    "target_id": f"figure-{i}",
                    "target_kind": "caption_backed_figure",
                    "text_only_model_eligibility": False,
                }
                for i in range(178)
            ]
        },
        "toc_review_decisions": {
            "entries": [{"entry_id": f"toc-{i}", "disposition": "not_toc"} for i in range(757)],
            "merge_policy": (
                "706 proved correspondence reuses plus 51 repaired-source accepted decisions "
                "carried after matching four-stratum sampled confirmation"
            ),
        },
    }
    limitations["decision_provenance"] = [
        {
            "entry_id": f"toc-{i}",
            "disposition": "not_toc",
            "decision_origin": "accepted_task04_proved_correspondence"
            if i < 706
            else "accepted_task04_repaired_source_sample_confirmed",
        }
        for i in range(757)
    ]
    limitations["sample_stratum_confirmations"] = {"stratum_count": 4, "sample_count": 11}
    return ReleaseInputs(
        source,
        edges,
        [{"diagnostic_id": f"diag-{i}"} for i in range(320)],
        views,
        outcomes,
        links,
        diagnostics,
        [],
        [],
        limitations,
        {"accepted_task06h_handoff": {"final_f1_warning_binding": copy.deepcopy(binding)}},
        {},
        "",
    )


def test_exact_composition_is_mechanical_not_human_review() -> None:
    result = validate_composition(composition())
    assert result["counts"]["outcomes"] == 511
    assert result["counts"]["f1_warnings"] == 66
    assert result["mechanical_check_is_human_review"] is False
    assert result["coverage"]["sampled_carries_individually_rereviewed"] is False


@pytest.mark.parametrize(
    "change, message",
    [
        ("foreign_edge", "foreign source unit"),
        ("missing_nonlink", "511/468/43"),
        ("duplicate_link", "duplicate mention_id"),
        ("missing_warning", "annotation/owner association"),
        ("lost_specific", "warning altered"),
        ("lost_64", "warning differs"),
        ("promoted_figure", "178 caption-backed"),
        ("sample_claim", "51 sampled-stratum"),
        ("wrong_anchor", "anchor association"),
        ("wrong_target", "invalid resolved"),
        ("wrong_reason", "diagnostic association"),
        ("missing_view", "review views"),
    ],
)
def test_composition_rejects_drift(change: str, message: str) -> None:
    inputs = composition()
    if change == "foreign_edge":
        inputs.edges[0]["target_unit_id"] = "foreign"
    elif change == "missing_nonlink":
        inputs.reference_diagnostics.pop()
    elif change == "duplicate_link":
        inputs.links.append(inputs.links[0])
    elif change == "missing_warning":
        inputs.outcomes[0]["final_f1_warning"] = None
    elif change == "lost_specific":
        inputs.outcomes[0]["final_f1_warning"]["response_specific"] = []
    elif change == "lost_64":
        inputs.limitations["final_f1_warning_binding"][
            "other_mentions_not_proven_draft_final_equivalent"
        ] = 63
    elif change == "promoted_figure":
        inputs.limitations["target_limitations"]["entries"][0]["text_only_model_eligibility"] = True
    elif change == "sample_claim":
        inputs.limitations["coverage"]["sampled_carries_individually_rereviewed"] = True
    elif change == "wrong_anchor":
        inputs.outcomes[0]["mention_span_id"] = "wrong"
    elif change == "wrong_target":
        inputs.links[0]["target_id"] = "wrong"
    elif change == "wrong_reason":
        inputs.reference_diagnostics[0]["terminal_reason"] = "wrong"
    elif change == "missing_view":
        inputs.graph_views.pop()
    with pytest.raises(ValueError, match=message):
        validate_composition(inputs)


def test_reference_rejects_same_size_compact_drift(tmp_path: Path) -> None:
    path = tmp_path / "control.json"
    original = b'{"value":1}'
    path.write_bytes(original)
    seal = {
        "path": path.name,
        "size_bytes": len(original),
        "sha256": hashlib.sha256(original).hexdigest(),
    }
    assert verify_reference(tmp_path, seal) == path
    path.write_bytes(b'{"value":2}')
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_reference(tmp_path, seal)


@pytest.mark.parametrize("name", ["../escape.json", "source.pdf", "figure.png"])
def test_reference_never_opens_source_or_escaping_paths(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError):
        verify_reference(tmp_path, {"path": name, "size_bytes": 0, "sha256": "0" * 64})


def test_composition_membership_digest_ignores_discovery_order() -> None:
    inputs = composition()
    first = validate_composition(inputs)
    inputs.outcomes.reverse()
    inputs.edges.reverse()
    assert validate_composition(inputs) == first


def test_loader_import_does_not_load_reference_resolvers() -> None:
    """A fresh loader process must not import the historical resolver workflow."""
    import subprocess
    import sys

    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import er_commons.response_inventory.release_inputs; "
            "assert 'er_commons.response_inventory.reference_baseline' not in sys.modules; "
            "assert 'er_commons.response_inventory.reference_replay_inputs' not in sys.modules",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
