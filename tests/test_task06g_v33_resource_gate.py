"""Focused cumulative-accounting proof for the collection-only v33 allowance."""

from __future__ import annotations

from pathlib import Path

from er_commons.task06g.packets import DEFAULT_RESERVE_BYTES, DEFAULT_TOTAL_BYTES, resource_ledger

V33_REMAINING_ALLOWANCE = 4_063_944_139


def test_accounting_includes_preserved_attempt16_at_exact_v33_allowance(
    tmp_path: Path,
) -> None:
    replay = tmp_path / "replay_v33"
    replay.mkdir()
    prior = tmp_path / "all_prior_replay_roots"
    prior.mkdir()
    attempt16 = tmp_path / "execution_attempt_v16"
    attempt16.mkdir()
    required_preserved = DEFAULT_TOTAL_BYTES - DEFAULT_RESERVE_BYTES - V33_REMAINING_ALLOWANCE
    with (prior / "sealed-evidence.bin").open("wb") as stream:
        stream.truncate(required_preserved - 1)
    (attempt16 / "execution.json").write_bytes(b"x")

    ledger = resource_ledger(replay, [prior, attempt16])

    assert ledger["preserved_sibling_bytes"] == required_preserved
    assert ledger["maximum_additional_bytes"] == V33_REMAINING_ALLOWANCE
    assert ledger["prospective_external_reserve_bytes"] == 64 * 1024**2
    assert resource_ledger(replay, [prior])["maximum_additional_bytes"] > (V33_REMAINING_ALLOWANCE)
