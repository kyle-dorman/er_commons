"""A graph repair cannot silently alter the report-link source population."""

from copy import deepcopy

import pytest

from er_commons.response_inventory.reference_replay_inputs import validate_source_replacement


def source_rows():
    """Keep stable source evidence and one report mention in a tiny fixture."""
    return [
        {"record_type": "activity", "activity_id": "old"},
        {"record_type": "source_unit", "unit_id": "u", "activity_id": "old"},
        {"record_type": "page", "raw_text": "Response A-1 and A-2"},
        {"record_type": "reference_mention", "reference_domain": "draft_eir", "mention_id": "r"},
    ]


def repaired_rows():
    """Add only a list item and its exact source span."""
    rows = source_rows()
    rows[0]["activity_id"] = rows[1]["activity_id"] = "new"
    return rows + [
        {
            "record_type": "reference_mention",
            "reference_domain": "intra_volume",
            "mention_span_id": "s",
        },
        {"record_type": "source_span", "span_id": "s"},
    ]


def test_replacement_preserves_report_population():
    validate_source_replacement(source_rows(), repaired_rows())


@pytest.mark.parametrize(
    "index,field,value",
    [(1, "unit_id", "changed"), (2, "raw_text", "edited"), (3, "mention_id", "new-report")],
)
def test_replacement_rejects_changed_source(index, field, value):
    rows = deepcopy(repaired_rows())
    rows[index][field] = value
    with pytest.raises(ValueError, match="historical source evidence"):
        validate_source_replacement(source_rows(), rows)


def test_replacement_rejects_unrelated_addition():
    with pytest.raises(ValueError, match="unrelated"):
        validate_source_replacement(
            source_rows(), repaired_rows() + [{"record_type": "source_unit", "unit_id": "extra"}]
        )


def test_replacement_rejects_new_report_reference():
    rows = repaired_rows()
    rows[-2]["reference_domain"] = "draft_eir"
    with pytest.raises(ValueError, match="intra-volume"):
        validate_source_replacement(source_rows(), rows)
