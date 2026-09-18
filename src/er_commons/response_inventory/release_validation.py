"""Pure all-row closure checks; mechanical composition never claims human review."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

from er_commons.artifact_io import canonical_json_sha256

if TYPE_CHECKING:
    from er_commons.response_inventory.release_inputs import ReleaseInputs

type JsonObject = dict[str, Any]

NONLINK_COUNTS = {
    "exact_target_absent": 19,
    "comment_authored_reference_no_official_response_link": 11,
    "more_specific_appendix_target_requires_resolution": 5,
    "exact_target_collision": 3,
    "appendix_source_route_absent": 2,
    "appendix_q_verification_required": 2,
    "exact_figure_target_absent": 1,
}
COVERAGE = {
    "task04_evidence_proven_reuses": 706,
    "sampled_stratum_carries": 51,
    "sampled_carries_individually_rereviewed": False,
    "caption_backed_figures_unavailable_as_text_only_evidence": 178,
}


def keyed(rows: list[JsonObject], field: str) -> dict[str, JsonObject]:
    """Require unique nonempty identities before any membership comparison."""
    result = {}
    for row in rows:
        identity = row.get(field)
        if not isinstance(identity, str) or not identity or identity in result:
            raise ValueError(f"missing or duplicate {field}: {identity}")
        result[identity] = row
    return result


def _source_graph(inputs: ReleaseInputs) -> dict[str, JsonObject]:
    """Check exact source census and graph/view joins without reconstructing edges."""
    units = keyed(
        [r for r in inputs.source_records if r.get("record_type") == "source_unit"], "unit_id"
    )
    if Counter(row["unit_kind"] for row in units.values()) != {
        "comment": 1011,
        "response": 1010,
        "general_response": 8,
    }:
        raise ValueError("accepted source unit census differs")
    edges = keyed(inputs.edges, "edge_id")
    if len(edges) != 1538:
        raise ValueError("accepted graph edge census differs")
    for edge in edges.values():
        if edge["source_unit_id"] not in units or edge["target_unit_id"] not in units:
            raise ValueError(f"graph edge has foreign source unit: {edge['edge_id']}")
    views = keyed(inputs.graph_views, "view_id")
    comments = {identity for identity, row in units.items() if row["unit_kind"] == "comment"}
    if len(views) != 1011 or {row["root_unit_id"] for row in views.values()} != comments:
        raise ValueError("accepted comment review views do not close source comments")
    for view in views.values():
        if (
            not set(view["ordered_unit_ids"]) <= units.keys()
            or not set(view["edge_ids"]) <= edges.keys()
        ):
            raise ValueError(f"review view has foreign units or edges: {view['view_id']}")
    if len(keyed(inputs.graph_diagnostics, "diagnostic_id")) != 320:
        raise ValueError("accepted graph diagnostic census differs")
    return units


def _warnings(inputs: ReleaseInputs, outcomes: dict[str, JsonObject]) -> list[str]:
    """Retain the exact F1 binding, including its independent other-64 limitation."""
    binding = inputs.limitations["final_f1_warning_binding"]
    if binding != inputs.handoff["accepted_task06h_handoff"]["final_f1_warning_binding"]:
        raise ValueError("Final F1 warning differs from accepted handoff")
    if (
        binding.get("other_mentions_not_proven_draft_final_equivalent") != 64
        or binding["source_substitution"].get("draft_final_equivalence_proven") is not False
        or binding["source_substitution"].get("semantic_equivalence") is not False
    ):
        raise ValueError("Final F1 edition equivalence limitation lost")
    warned = []
    for mention_id, row in outcomes.items():
        warning = row.get("final_f1_warning")
        is_f1 = "deir_appendix_f1" in row.get("logical_source_ids", [])
        if is_f1 != (warning is not None):
            raise ValueError(f"Final F1 warning membership differs: {mention_id}")
        if warning is None:
            continue
        warned.append(mention_id)
        expected_specific = [
            item for item in binding["response_specific"] if mention_id in item["mention_ids"]
        ]
        if (
            warning.get("binding") != binding
            or warning.get("response_specific") != expected_specific
            or warning.get("draft_final_equivalence_proven") is not False
        ):
            raise ValueError(f"Final F1 warning altered: {mention_id}")
        if any(item["unit_id"] != row["source_unit_id"] for item in expected_specific):
            raise ValueError(f"Final F1 response-specific owner differs: {mention_id}")
    specific_ids = {
        identity for item in binding["response_specific"] for identity in item["mention_ids"]
    }
    if len(warned) != 66 or len(specific_ids) != 3 or not specific_ids <= set(warned):
        raise ValueError("Final F1 66-warning / three response-specific mention closure differs")
    return warned


def _limitations(inputs: ReleaseInputs) -> list[str]:
    """Keep inherited sampled coverage and figure identity separate from eligibility."""
    if inputs.limitations["coverage"] != COVERAGE:
        raise ValueError("706 evidence-proven / 51 sampled-stratum coverage differs")
    figures = [
        row
        for row in inputs.limitations["target_limitations"]["entries"]
        if row["target_kind"] == "caption_backed_figure"
    ]
    ids = keyed(figures, "target_id")
    if len(ids) != 178 or any(
        row.get("text_only_model_eligibility") is not False for row in figures
    ):
        raise ValueError(
            "all 178 caption-backed figures must remain unavailable as text-only evidence"
        )
    toc = inputs.limitations["toc_review_decisions"]
    if len(keyed(toc["entries"], "entry_id")) != 757 or toc.get("merge_policy") != (
        "706 proved correspondence reuses plus 51 repaired-source accepted decisions "
        "carried after matching four-stratum sampled confirmation"
    ):
        raise ValueError("inherited TOC sampled-review coverage differs")
    provenance = keyed(inputs.limitations["decision_provenance"], "entry_id")
    if set(provenance) != {row["entry_id"] for row in toc["entries"]} or Counter(
        row["decision_origin"] for row in provenance.values()
    ) != {
        "accepted_task04_proved_correspondence": 706,
        "accepted_task04_repaired_source_sample_confirmed": 51,
    }:
        raise ValueError("706/51 exact provenance membership differs")
    for row in toc["entries"]:
        if row["disposition"] != provenance[row["entry_id"]]["disposition"]:
            raise ValueError("TOC provenance disposition differs")
    strata = inputs.limitations["sample_stratum_confirmations"]
    if strata.get("stratum_count") != 4 or strata.get("sample_count") != 11:
        raise ValueError("sampled-stratum confirmation coverage differs")
    return sorted(ids)


def _validate_outcome_source(
    mention_id: str, outcome: JsonObject, mention: JsonObject, units: dict[str, JsonObject]
) -> None:
    """Keep each outcome attached to its original source unit and text anchor."""
    if outcome["source_unit_id"] not in units or any(
        outcome.get(field) != mention.get(field)
        for field in (
            "source_unit_id",
            "mention_span_id",
            "raw_text_sha256",
            "reference_domain",
        )
    ):
        raise ValueError(f"outcome source/anchor association differs: {mention_id}")
    if outcome["source_kind"] != units[outcome["source_unit_id"]]["unit_kind"]:
        raise ValueError(f"outcome source kind differs: {mention_id}")


def _validate_target_annotations(mention_id: str, outcome: JsonObject) -> dict[str, JsonObject]:
    """Check target membership without promoting figure identity to text evidence."""
    annotations = keyed(outcome["target_annotations"], "target_id")
    if sorted(annotations) != outcome["compatible_target_ids"]:
        raise ValueError(f"target annotation membership differs: {mention_id}")
    for annotation in annotations.values():
        if annotation["target_type"] == "figure" and (
            annotation.get("text_only_model_eligibility") is not False
            or annotation.get("target_limitation") is None
        ):
            raise ValueError(f"figure promoted to text-only evidence: {mention_id}")
    return annotations


def _validate_resolved_link(
    mention_id: str, outcome: JsonObject, link: JsonObject, annotations: dict[str, JsonObject]
) -> None:
    """Require the accepted link and outcome to retain identical owner and annotations."""
    if (
        outcome["outcome"] != "resolved"
        or outcome["terminal_reason"] is not None
        or outcome["compatible_target_ids"] != [link["target_id"]]
        or outcome["source_kind"] == "comment"
        or outcome["reference_domain"] == "appendix_q"
    ):
        raise ValueError(f"invalid resolved reference: {mention_id}")
    if (
        any(
            link.get(field) != outcome.get(field)
            for field in (
                "link_id",
                "source_unit_id",
                "resolver_rule",
                "final_f1_warning",
                "input_refs",
            )
        )
        or link["target_annotation"] != annotations[link["target_id"]]
    ):
        raise ValueError(f"link annotation/owner association differs: {mention_id}")


def _validate_nonlink(mention_id: str, outcome: JsonObject, diagnostic: JsonObject) -> None:
    """Require the explicit nonlink and its diagnostic to agree on the terminal reason."""
    if (
        outcome["outcome"] != "terminal_nonlink"
        or outcome["link_id"] is not None
        or any(
            diagnostic.get(field) != outcome.get(field)
            for field in ("terminal_reason", "mention_span_id", "input_refs")
        )
    ):
        raise ValueError(f"nonlink diagnostic association differs: {mention_id}")


def validate_composition(inputs: ReleaseInputs) -> JsonObject:
    """Validate exact accepted membership, joins, nonlinks and inherited limitations."""
    units = _source_graph(inputs)
    mentions = keyed(
        [r for r in inputs.source_records if r.get("record_type") == "reference_mention"],
        "mention_id",
    )
    official = {
        identity
        for identity, row in mentions.items()
        if row["reference_domain"] in {"draft_eir", "appendix_q"}
    }
    outcomes = keyed(inputs.outcomes, "mention_id")
    links = keyed(inputs.links, "mention_id")
    keyed(inputs.links, "link_id")
    diagnostics = keyed(inputs.reference_diagnostics, "mention_id")
    if (
        len(outcomes) != 511
        or len(links) != 468
        or len(diagnostics) != 43
        or set(outcomes) != official
    ):
        raise ValueError("accepted 511/468/43 reference membership differs")
    if set(links) & set(diagnostics) or set(links) | set(diagnostics) != official:
        raise ValueError("reference link/nonlink partition differs")
    nonlinks: Counter[str] = Counter()
    for mention_id, outcome in outcomes.items():
        _validate_outcome_source(mention_id, outcome, mentions[mention_id], units)
        annotations = _validate_target_annotations(mention_id, outcome)
        if mention_id in links:
            _validate_resolved_link(mention_id, outcome, links[mention_id], annotations)
        else:
            _validate_nonlink(mention_id, outcome, diagnostics[mention_id])
            nonlinks[outcome["terminal_reason"]] += 1
    if dict(nonlinks) != NONLINK_COUNTS:
        raise ValueError("seven accepted nonlink classes differ")
    warned = _warnings(inputs, outcomes)
    figures = _limitations(inputs)
    populations = {
        "units": sorted(units),
        "edges": sorted(row["edge_id"] for row in inputs.edges),
        "outcomes": sorted(outcomes),
        "links": sorted(links),
        "nonlinks": sorted(diagnostics),
        "f1_warnings": sorted(warned),
        "text_only_excluded_figures": figures,
    }
    return {
        "counts": {name: len(rows) for name, rows in populations.items()},
        "nonlink_counts": dict(sorted(nonlinks.items())),
        "membership_digests": {
            name: canonical_json_sha256(rows) for name, rows in populations.items()
        },
        "coverage": dict(COVERAGE),
        "mechanical_check_is_human_review": False,
    }
