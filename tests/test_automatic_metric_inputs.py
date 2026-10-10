"""Invented identity and delivery fixtures never require corpus files or model calls."""

import copy

import pytest

from er_commons.automatic_metric_inputs import (
    build_catalog,
    resolve_citations,
    resolve_receipt,
    resolve_references,
    source_unit,
)


def source(raw="O1", unit="section-1", document="deir", roles=None):
    """Build an invented locator with the exact maintained 09A source shape."""
    return {
        "occurrence_id": raw,
        "source_id": document,
        "extraction_id": "extract-1",
        "canonical_target": {
            "unit_id": unit,
            "unit_type": "section",
            "document_id": f"extract-1/document/{document}",
            "citation_label": "Identical heading",
        },
        "approved_roles": roles or [],
    }


def answer(*ids):
    """Build only the substantive answer point lists read by link resolution."""
    return {
        "status": "answered",
        "conclusion": {"point_id": "P1", "text": "Claim", "citation_ids": list(ids)},
        "supporting_points": [],
        "qualifications": [],
        "optional_context": [],
    }


def receipt():
    """Give an invented full-section anchor inventory and one delivery receipt."""
    unit = list(source_unit(source()))
    return {
        "schema_version": "task09d.retrieval_receipt.v1",
        "condition": "single_query_top5",
        "unit_budget": 5,
        "ranked_depth": 1,
        "ranking_exhausted": False,
        "invented": True,
        "provenance": "invented fixture only",
        "required_anchor_ids": [{"canonical_unit": unit, "anchor_ids": ["a", "b"]}],
        "search_record_mapping": [{"search_record_id": "fragment", "canonical_unit": unit}],
        "hits": [
            {
                "rank": 1,
                "canonical_unit": unit,
                "search_record_id": "fragment",
                "delivered": True,
                "delivered_anchor_ids": ["a", "b"],
                "anchor_ids": ["a", "b"],
            }
        ],
    }


def test_identity_ignores_labels_but_separates_documents_and_units():
    """Same heading does not merge units, and changed heading does not split one."""
    rows = [source(), source("O2", "section-2"), source("O3", document="appendix")]
    result = resolve_citations(answer("O1", "O2", "O3"), build_catalog(rows))
    assert len(result.units) == 3
    changed = copy.deepcopy(rows[0])
    changed["canonical_target"]["citation_label"] = "Renamed title"
    assert source_unit(changed) == source_unit(rows[0])


def test_aliases_and_duplicate_attempts_keep_audit_without_extra_credit():
    """Only verified aliases collapse; repeated links retain their original point."""
    catalog = build_catalog([source()], {"alias": "O1"})
    result = resolve_citations(answer("O1", "alias", "alias", "missing", "missing"), catalog)
    assert len(result.units) == 1
    assert result.invalid_tokens == {"str:missing"}
    assert len(result.attempts) == 5


def test_local_packet_labels_need_scoped_mapping():
    """S1 in different packets must recover different canonical units."""
    rows = [source(), source("O2", "section-2")]
    catalog = build_catalog(rows)
    first = resolve_citations(answer("S1"), catalog, {"O1": "S1"})
    second = resolve_citations(answer("S1"), catalog, {"O2": "S1"})
    assert first.units != second.units
    assert resolve_citations(answer("S1"), catalog).invalid_tokens == {"str:S1"}
    ambiguous = resolve_citations(answer("S1"), catalog, {"O1": "S1", "O2": "S1"})
    assert ambiguous.invalid_tokens == {"str:S1"}
    assert ambiguous.attempts[0]["status"] == "ambiguous"


def test_unknown_and_ambiguous_are_invalid_but_known_missing_locator_is_unavailable():
    """Infrastructure loss never becomes an answer citation error."""
    missing = source("broken")
    del missing["canonical_target"]
    catalog = build_catalog([source(), source(unit="other"), missing])
    result = resolve_citations(answer("O1", "unknown", "broken"), catalog)
    assert result.invalid_tokens == {"str:O1", "str:unknown"}
    assert not result.available
    assert [attempt["status"] for attempt in result.attempts] == [
        "ambiguous",
        "invalid",
        "unavailable",
    ]


def test_malformed_citation_items_preserved_and_type_distinguished():
    """Invalid JSON types cannot collide with literal string tokens or vanish."""
    result = resolve_citations(answer(2, "2", {"id": "O1"}, None, 2), build_catalog([source()]))
    assert len(result.invalid_tokens) == 4
    assert len(result.attempts) == 5
    malformed = answer()
    malformed["conclusion"]["citation_ids"] = "O1"
    result = resolve_citations(malformed, build_catalog([source()]))
    assert not result.units and result.invalid_tokens == {"str:O1"}
    assert "malformed_answer" in result.diagnostics[0]


def test_support_wins_and_missing_reference_locator_is_unavailable():
    """Role aggregation merges canonical aliases before support/context precedence."""
    rows = [source(roles=["optional_context"]), source("O2", roles=["required_support"])]
    result = resolve_references(rows, build_catalog(rows))
    assert result.support == {source_unit(rows[0])}
    assert not result.context and result.available
    del rows[1]["canonical_target"]
    assert not resolve_references(rows, build_catalog(rows)).available


def test_missing_and_empty_receipts_are_distinct():
    """No synthetic receipt is fabricated; an explicit empty delivery is measurable."""
    catalog = build_catalog([source()])
    assert not resolve_receipt(None, catalog).available
    empty = receipt()
    empty["hits"] = []
    result = resolve_receipt(empty, catalog)
    assert result.available and not result.units


def test_parent_id_without_complete_delivered_anchors_cannot_earn_credit():
    """A complete index hit and a delivered fragment are different evidence sets."""
    data = receipt()
    data["hits"][0]["delivered_anchor_ids"] = ["a"]
    result = resolve_receipt(data, build_catalog([source()]))
    assert result.available and not result.units
    assert result.ranked_units == ((1, source_unit(source())),)
    assert result.diagnostics


def test_fragments_can_cover_a_unit_only_through_explicit_anchor_union():
    """Two actually delivered fragments may jointly establish full-unit coverage."""
    data = receipt()
    data["hits"][0]["delivered_anchor_ids"] = ["a"]
    data["hits"][0]["anchor_ids"] = ["a"]
    data["hits"].append(
        {**data["hits"][0], "rank": 2, "delivered_anchor_ids": ["b"], "anchor_ids": ["b"]}
    )
    data["ranked_depth"] = 2
    result = resolve_receipt(data, build_catalog([source()]))
    assert result.units == {source_unit(source())}
    assert result.ranked_units == ((2, source_unit(source())),)


def test_deeper_rank_is_diagnostic_only():
    """A ranked full hit beyond delivery budget is not model-visible evidence."""
    data = receipt()
    data["hits"][0].update(rank=10, delivered=False, delivered_anchor_ids=[])
    result = resolve_receipt(data, build_catalog([source()]))
    assert result.available and not result.units
    assert not result.ranked_units
    assert "ranked_diagnostics_unavailable" in result.diagnostics


@pytest.mark.parametrize(
    "mutation", ["mapping", "anchors", "namespace", "rank", "budget", "provenance"]
)
def test_malformed_receipt_is_unavailable_not_measured_zero(mutation):
    """Unverifiable delivery infrastructure blocks scoring rather than counting misses."""
    data = receipt()
    if mutation == "mapping":
        data["search_record_mapping"] = []
    elif mutation == "anchors":
        data["required_anchor_ids"] = []
    elif mutation == "namespace":
        data["hits"][0]["canonical_unit"][0] = "wrong-source"
    elif mutation == "rank":
        data["hits"][0]["rank"] = True
    elif mutation == "budget":
        data["hits"][0]["rank"] = 10
    else:
        del data["provenance"]
    assert not resolve_receipt(data, build_catalog([source()])).available


def test_verified_packet_mapping_missing_source_is_infrastructure_failure():
    """A mapped known source missing from the verified catalog cannot penalize the answer."""
    result = resolve_citations(answer("S1"), build_catalog([]), {"known-source": "S1"})
    assert not result.available and not result.invalid_tokens


@pytest.mark.parametrize("value", [None, "broken", ["O1"]])
def test_unextractable_answer_or_point_preserves_raw_and_blocks_scoring(value):
    """Unknown row structure cannot disappear while a valid conclusion scores perfectly."""
    malformed = answer("O1")
    malformed["supporting_points"] = [value]
    result = resolve_citations(malformed, build_catalog([source()]))
    assert not result.available
    assert result.attempts[-1]["raw"] == value
    assert not resolve_citations(value, build_catalog([source()])).available


def test_ranked_diagnostics_require_complete_observed_prefix():
    """Absent depth and absent ranked anchor evidence are not measured misses."""
    data = receipt()
    del data["ranked_depth"]
    result = resolve_receipt(data, build_catalog([source()]))
    assert result.available and result.units
    assert result.ranked_depth == 0 and not result.ranked_units
    data = receipt()
    del data["hits"][0]["anchor_ids"]
    result = resolve_receipt(data, build_catalog([source()]))
    assert result.available and not result.ranked_units


def test_missing_link_field_cannot_disappear_from_malformed_point():
    """A malformed point without citation membership makes extraction unavailable."""
    malformed = answer("O1")
    malformed["supporting_points"] = [{"text": "unsupported claim"}]
    result = resolve_citations(malformed, build_catalog([source()]))
    assert not result.available
    assert result.attempts[-1]["raw"] == {"text": "unsupported claim"}


def test_missing_packet_mapping_is_unavailable_when_namespace_is_declared():
    result = resolve_citations(answer("S1"), build_catalog([source()]), packet_local=True)
    assert not result.available
    assert not result.invalid_tokens
    assert result.attempts[0]["raw"] == "S1"
    assert "missing_packet_local_mapping" in result.diagnostics


def test_released_required_role_is_support():
    rows = [source(roles=["required"])]
    result = resolve_references(rows, build_catalog(rows))
    assert result.available
    assert result.support == {source_unit(rows[0])}


@pytest.mark.parametrize("roles", [["required", "unknown"], ["required", {}]])
def test_mixed_unknown_or_malformed_roles_fail_closed(roles):
    rows = [source(roles=roles)]
    result = resolve_references(rows, build_catalog(rows))
    assert not result.available
    assert not result.support


def test_answer_prose_and_abstention_do_not_replace_actual_links():
    """Semantic reversal and abstention keep the same mechanical citation set."""
    catalog = build_catalog([source()])
    original = answer("O1", "missing")
    changed = copy.deepcopy(original)
    changed["conclusion"]["text"] = "The opposite conclusion is true."
    changed["status"] = "abstained"
    first = resolve_citations(original, catalog)
    second = resolve_citations(changed, catalog)
    assert first.units == second.units
    assert first.invalid_tokens == second.invalid_tokens
    assert resolve_citations(answer(), catalog).units == frozenset()


def test_table_and_extraction_namespace_are_part_of_identity():
    """Local ID reuse across extraction versions or section/table kinds is distinct."""
    section = source()
    table = source("table-occurrence")
    table["canonical_target"]["unit_type"] = "table"
    revised = source("revised-occurrence")
    revised["extraction_id"] = "extract-2"
    revised["canonical_target"]["document_id"] = "extract-2/document/deir"
    result = resolve_citations(
        answer("O1", "table-occurrence", "revised-occurrence"),
        build_catalog([section, table, revised]),
    )
    assert len(result.units) == 3


@pytest.mark.parametrize("reverse", [False, True])
def test_alias_shadowing_and_chains_are_rejected_independently_of_order(reverse):
    """Aliases cannot change an occurrence's meaning or target a newly created alias."""
    rows = [source(), source("O2", "section-2")]
    for entries, message in (
        ([("alias", "O1"), ("O1", "O2")], "conflicts with an existing occurrence"),
        ([("alias", "O1"), ("chain", "alias")], "verified occurrence target"),
    ):
        aliases = dict(reversed(entries) if reverse else entries)
        with pytest.raises(ValueError, match=message):
            build_catalog(rows, aliases)


def test_aliases_may_restate_existing_equivalent_occurrences():
    """Explicit same-identity aliases remain valid without changing the original index."""
    rows = [source(), source("O2")]
    catalog = build_catalog(rows, {"alias": "O1", "O1": "O2"})
    result = resolve_citations(answer("alias", "O1", "O2"), catalog)
    assert result.available and not result.invalid_tokens
    assert result.units == {source_unit(rows[0])}


def test_conflicting_source_kind_fields_make_identity_unavailable():
    """Two source locator fields cannot silently disagree about section/table identity."""
    row = source()
    row["canonical_target"]["kind"] = "table"
    result = resolve_citations(answer("O1"), build_catalog([row]))
    assert not result.available
    assert result.attempts[0]["status"] == "unavailable"
    row["canonical_target"]["kind"] = "section"
    assert source_unit(row)[2] == "section"


@pytest.mark.parametrize("field", ["condition", "provenance"])
@pytest.mark.parametrize("value", [42, {"name": "invented"}, "   "])
def test_receipt_condition_and_provenance_require_nonblank_strings(field, value):
    """Truthy malformed provenance cannot certify an available retrieval result."""
    data = receipt()
    data[field] = value
    result = resolve_receipt(data, build_catalog([source()]))
    assert not result.available
    assert result.receipt == data


def test_unused_search_record_mappings_must_use_known_canonical_units():
    """Validate the entire supplied mapping rather than only rows exercised by hits."""
    data = receipt()
    data["search_record_mapping"].append(
        {
            "search_record_id": "unused",
            "canonical_unit": ["unknown", "extract-1", "section", "section-1"],
        }
    )
    result = resolve_receipt(data, build_catalog([source()]))
    assert not result.available
    assert "Unknown canonical unit" in result.diagnostics[0]


@pytest.mark.parametrize("field", ["required_anchor_ids", "search_record_mapping", "hits"])
@pytest.mark.parametrize("value", [{"row": "not an array"}, [None]])
def test_malformed_receipt_row_containers_are_unavailable(field, value):
    """Broken JSON containers yield receipt diagnostics instead of attribute errors."""
    data = receipt()
    data[field] = value
    result = resolve_receipt(data, build_catalog([source()]))
    assert not result.available
    assert f"{field} must be an array of objects" in result.diagnostics[0]


def test_unobserved_large_ranking_depth_does_not_allocate_a_claimed_prefix():
    """Diagnostic eligibility depends on actual recorded hits, not a declared allocation."""
    data = receipt()
    data["ranked_depth"] = 10**18
    result = resolve_receipt(data, build_catalog([source()]))
    assert result.available and result.units
    assert result.ranked_depth == 0 and not result.ranked_units
    assert result.diagnostics == ("ranked_diagnostics_unavailable",)


def test_incomplete_delivery_diagnostics_have_canonical_order():
    """Persisted diagnostic ordering is stable independently of receipt hit order."""
    rows = [source(), source("O2", "section-2")]
    data = receipt()
    data["ranked_depth"] = 2
    data["search_record_mapping"] = []
    data["required_anchor_ids"] = [
        {"canonical_unit": list(source_unit(row)), "anchor_ids": ["a", "b"]} for row in rows
    ]
    data["hits"] = [
        {
            "rank": rank,
            "canonical_unit": list(source_unit(row)),
            "delivered": True,
            "delivered_anchor_ids": ["a"],
            "anchor_ids": ["a", "b"],
        }
        for rank, row in enumerate(reversed(rows), start=1)
    ]
    result = resolve_receipt(data, build_catalog(rows))
    assert result.available and not result.units
    assert result.diagnostics == tuple(
        f"incomplete_delivered_unit: {source_unit(row)}" for row in rows
    )
