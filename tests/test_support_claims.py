"""Protect explicit S candidate selection and frozen judge compatibility."""

import hashlib

import pytest

from er_commons import adequacy_binary as core
from er_commons import adequacy_inspect as native
from er_commons import support_claims


def test_support_candidate_preserves_frozen_default_and_wire_schema():
    """Opt-in wording changes must not mutate historical defaults or output shape."""
    frozen = core.system_prompt("S")
    assert hashlib.sha256(frozen.encode()).hexdigest() == (
        "4d1d2b59cfc38dacc509500e4cbfdc68be20de21377ed7e133fbc4535c7c6266"
    )
    assert native._prompt_version("S", None) == core.SUPPORT_BASIS_PROMPT_VERSION
    assert native._prompt_version("S", support_claims.VERSION) == support_claims.VERSION
    assert core.system_prompt("S", prompt_version=support_claims.VERSION) == support_claims.PROMPT
    assert core.output_json_schema("S", prompt_version=support_claims.VERSION) == (
        core.output_json_schema("S")
    )


def test_support_candidate_cannot_be_selected_for_conclusion():
    """A support-only prompt must be rejected by both conclusion entry points."""
    with pytest.raises(ValueError):
        core.system_prompt("C", prompt_version=support_claims.VERSION)
    with pytest.raises(ValueError):
        native._prompt_version("C", support_claims.VERSION)
