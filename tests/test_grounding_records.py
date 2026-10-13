"""Dependency and observation boundaries for reusable offline grounding records."""

import subprocess
import sys

import pytest

from er_commons.grounding_records import observed_token_counts


def test_record_analysis_does_not_load_inspect_or_transport() -> None:
    """Offline consumers can import the saved-sample model without evaluation infrastructure."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import er_commons.grounding_records; "
            "assert not any(k == 'inspect_ai' or k.startswith('inspect_ai.') "
            "for k in sys.modules); assert 'httpx' not in sys.modules",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("invalid", [None, True, -1, 2.5, "3"])
def test_token_measurements_exclude_reuse_and_noninteger_values(invalid: object) -> None:
    """Only measured native tokens count, including zero but excluding saved-result reuse."""
    records = [
        {"native": {"output": {"tokens": invalid}}},
        {"native": {"output": {"tokens": 0}}},
        {"native": {"output": {"tokens": 5}}},
        {"reused": True, "native": {"output": {"tokens": 7}}},
        {"native": None},
    ]
    assert observed_token_counts(records, "tokens") == [0, 5]
