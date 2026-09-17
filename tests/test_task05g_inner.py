"""Source-free compound reference tests across arbitrary sources and titles."""

from types import SimpleNamespace

import pytest

from er_commons.response_inventory.reference_replay_inner import propose_inner


def row(key, target="one", kind="section", source="report", **kwargs):
    """Create one published alias with no document-specific lookup exception."""
    return dict(lookup_key=key, target_id=target, target_type=kind, source_id=source, **kwargs)


def propose(before="", after="", rows=()):
    """Use the same bounded-context interface as the resolver."""
    return propose_inner(SimpleNamespace(before=before, after=after), {"report"}, list(rows))


@pytest.mark.parametrize("word", ["are", "and", "above", "below", "information"])
def test_ordinary_prose_is_not_letter_identifier(word):
    assert not propose(before=f"the table {word} included in").specific


@pytest.mark.parametrize("label", ["Table A", "Figure 4a", "Section 4.2", "Table C-8", "page 2-21"])
def test_complete_identifier_keeps_specific_protection(label):
    assert propose(before=f"{label} of").specific


@pytest.mark.parametrize(
    "before,key",
    [
        ("Chapter 09, Rail Operations, was included in", "09 | rail operations"),
        ("Chapter 03, Freight Service, which was provided as", "03 freight service"),
        ("Section 7, Daily Demand, of", "7. daily demand"),
        ("Appendix B to", "appendix b: supporting study"),
    ],
)
def test_generic_inner_existing_section(before, key):
    result = propose(before, rows=[row(key), row(key, "wrong-source", source="other")])
    assert result.selected["target_id"] == "one"
    assert result.requested_type == "section"


def test_alias_duplicates_collapse_but_distinct_targets_do_not():
    assert propose("Chapter 03 of", rows=[row("03 freight"), row("03 | freight")]).selected
    result = propose("Chapter 03 of", rows=[row("03 freight"), row("03 freight", "two")])
    assert len(result.candidates) == 2
    assert result.selected is None


def test_named_section_records_unverified_page_qualifier():
    result = propose(
        "The section titled “Northern Rail,” on page 72 of", rows=[row("northern rail")]
    )
    assert result.selected
    assert result.unverified_page_qualifier
    assert result.evidence == ("section titled “Northern Rail,”",)


def test_named_section_does_not_drop_second_citation():
    result = propose(
        "Table 4 and the section titled “Northern Rail,” on page 72 of", rows=[row("northern rail")]
    )
    assert result.specific and result.selected is None


def test_same_identifier_with_different_title_remains_nonlink():
    result = propose("Section 7, Bus Demand, of", rows=[row("7 rail demand")])
    assert result.specific and not result.candidates


def test_ambiguous_table_number_does_not_use_semantic_context():
    result = propose(
        "The parking districts in Table 5 of",
        rows=[
            row("table 5: parking spaces", kind="table"),
            row("table 5: travel demand", "two", "table"),
        ],
    )
    assert result.selected is None and len(result.candidates) == 2


@pytest.mark.parametrize(
    "before", ["Chapters 3 and 4 of", "Section 3 and Section 4 of", "Table 3 through Table 5 of"]
)
def test_multiple_targets_never_become_last_target(before):
    assert (
        propose(before, rows=[row("4 rail"), row("table 5: test", kind="table")]).selected is None
    )


def test_nested_appendix_prefers_attached_reference_over_other_document_citation():
    result = propose("Draft Report Section 4.8 and Appendix B to", rows=[row("appendix b: study")])
    assert result.selected


def test_nested_table_requires_explicit_ancestry():
    target = row("table c-8: mode share", kind="table")
    assert propose("Table C-8 of Appendix C to", rows=[target]).selected is None
    assert propose(
        "Table C-8 of Appendix C to", rows=[{**target, "inner_appendix_identifier": "c"}]
    ).selected


def test_page_requires_qualified_existing_alias():
    context = ", Biological Study, page 2-21, which concludes"
    assert propose(after=context, rows=[row("page 2-21", kind="page")]).selected
    assert propose(after=context, rows=[row("page 37", kind="page")]).selected is None


def test_figures_remain_unsupported_even_with_alias():
    result = propose("Figure 4 of the Transit Study (", rows=[row("figure 4", kind="figure")])
    assert result.specific and result.selected is None


def test_mixed_compound_targets_are_not_silently_dropped():
    result = propose("Table 2 and Section 4 of", rows=[row("4 demand")])
    assert result.specific and result.selected is None


def test_plural_specific_reference_never_falls_back_to_document():
    assert propose("Chapters 3 and 4 of").specific


def test_nested_appendix_ancestry_has_delimited_boundary():
    target = row("table c-8: mode share", kind="table")
    assert propose(
        "Table C-8 of Appendix C to", rows=[{**target, "inner_appendix_identifier": "c.2"}]
    ).selected
    assert (
        propose(
            "Table C-8 of Appendix C to", rows=[{**target, "inner_appendix_identifier": "ca"}]
        ).selected
        is None
    )


@pytest.mark.parametrize(
    "before,after",
    [
        ("Table 2 and Table C-8 of Appendix C to", ""),
        ("Section 4 of", ", Section 5 too"),
        ("Section 2, unrelated words, Section 4 of", ""),
        ("The section titled “Rail,” on page 72 of", ", page 99 too"),
        ("The section titled “Rail,” on page 72 of", ", Tables A and B"),
        ("Table C-8 of Appendix C to", ", section titled “More”"),
    ],
)
def test_no_additional_inner_citation_can_disappear(before, after):
    rows = [
        row("table c-8: mode share", kind="table", inner_appendix_identifier="c"),
        row("4 demand"),
        row("rail"),
    ]
    result = propose(before, after, rows)
    assert result.specific and result.selected is None


@pytest.mark.parametrize(
    "text",
    [
        "Sections A and B of",
        "Tables A and B of",
        "Appendices C and D of",
        "Table 4.",
        "Section A.",
        "Section 4.8.5.a.",
    ],
)
def test_letter_plurals_and_terminal_period_remain_specific(text):
    result = propose(text)
    assert result.specific and result.selected is None


def test_decimal_identifier_keeps_full_value():
    result = propose("Section 4.8 of", rows=[row("4.8 demand"), row("4 unrelated", "two")])
    assert result.selected["target_id"] == "one"


def test_separately_qualified_hierarchical_citation_does_not_block_nested_appendix():
    result = propose(
        "Draft EIR Section 4.8.5.a, Road Study, and Appendix F to",
        rows=[row("appendix f: mobility")],
    )
    assert result.selected
