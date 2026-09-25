"""Guard native form bindings and the independent-radio browser regression."""

import xml.etree.ElementTree as ET

import pytest

from er_commons.pilot_relevance_form import build_form


def test_radio_names_are_unique_while_export_aliases_stay_semantic():
    """Label Studio 1.23 uses Choice.value as HTML radio name across controls."""
    form = ET.fromstring(build_form(17))
    values = []
    for index in range(1, 18):
        group = form.find(f".//Choices[@name='s{index:03d}_relationship']")
        assert group is not None
        assert group.attrib.get("required", "false") == "false"
        assert [c.attrib["alias"] for c in group] == [
            "direct",
            "supporting",
            "not_relevant",
            "unclear",
        ]
        values.extend(c.attrib["value"] for c in group)
        assert all(c.attrib.get("html") for c in group)
    assert len(set(values)) == len(values)
    assert not form.findall(".//Choice[@selected='true']")
    assert [c.attrib["name"] for c in form.findall(".//Choices[@required='true']")] == [
        "review_status"
    ]


def test_expansion_preserves_existing_control_names_and_adds_independent_controls():
    """Larger generated forms retain bindings used by saved native results."""
    small, large = (ET.fromstring(build_form(n)) for n in (4, 8))

    def controls(root):
        """Index serialized controls by their persisted native names."""
        return {
            e.attrib["name"]: ET.tostring(e)
            for e in root.iter()
            if e.tag in {"TextArea", "Choices"}
        }

    before, after = controls(small), controls(large)
    assert all(after[name] == value for name, value in before.items())
    with pytest.raises(ValueError):
        build_form(0)
