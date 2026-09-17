"""Measured synthetic 511-row headroom and real, harmless supervisor limit stops."""

from __future__ import annotations

import copy
import json
import sys
import threading
import time
from pathlib import Path
from typing import Any

import psutil  # type: ignore[import-untyped]
import pytest
from test_task05g_resolver import fixture, population

from er_commons.artifact_io import json_bytes, jsonl_bytes
from er_commons.document_publication.background_execution import ExecutionLimits, supervise
from er_commons.response_inventory.reference_replay_comparison import (
    validate_population,
    validate_result,
)
from er_commons.response_inventory.reference_replay_resolver import resolve_references


def test_synthetic_511_row_resolution_has_measured_resource_headroom(tmp_path: Path) -> None:
    """Exercise real pure resolution and validation; report measured synthetic cost only."""
    args = fixture()
    mention, unit = args["source_records"]
    old = args["baseline_outcomes"][0]
    args["source_records"] = []
    args["baseline_outcomes"] = []
    for index in range(511):
        identity = {
            "mention_id": f"mention-{index:03d}",
            "mention_span_id": f"span-{index:03d}",
            "source_unit_id": f"unit-{index:03d}",
        }
        args["source_records"].extend(
            [
                {**copy.deepcopy(mention), **identity},
                {**copy.deepcopy(unit), "unit_id": identity["source_unit_id"]},
            ]
        )
        args["baseline_outcomes"].append({**copy.deepcopy(old), **identity})
    frozen = population(args)
    process = psutil.Process()
    rss_samples = [process.memory_info().rss]
    stopped = threading.Event()

    def sample() -> None:
        """Sample process RSS throughout pure synthetic resolution and closure checking."""
        while not stopped.wait(0.005):
            rss_samples.append(process.memory_info().rss)

    sampler = threading.Thread(target=sample, daemon=True)
    started = time.monotonic()
    sampler.start()
    try:
        validate_population(args["baseline_outcomes"], frozen)
        result = resolve_references(**args)
        validate_result(result, args["baseline_outcomes"], frozen, expected_result=result)
        payloads = {
            name: json_bytes(value) if isinstance(value, dict) else jsonl_bytes(value)
            for name, value in result.items()
        }
        for name, data in payloads.items():
            (tmp_path / f"{name}.json").write_bytes(data)
    finally:
        stopped.set()
        sampler.join()
    elapsed = time.monotonic() - started
    rss_samples.append(process.memory_info().rss)
    measurements = {
        "synthetic_mentions": 511,
        "sampled_peak_rss_bytes": max(rss_samples),
        "elapsed_seconds": elapsed,
        "serialized_output_bytes": sum(map(len, payloads.values())),
        "measurement_scope": "synthetic pure resolver and closure; not production throughput",
    }
    (tmp_path / "resource_measurements.json").write_bytes(json_bytes(measurements))
    print(json.dumps(measurements, sort_keys=True))
    assert len(result["outcomes"]) == 511
    # Require substantial headroom beneath the approved launch maxima.
    assert measurements["sampled_peak_rss_bytes"] < 2 * 1024**3
    assert elapsed < 180
    assert measurements["serialized_output_bytes"] < 200 * 1024**2


@pytest.mark.parametrize("stop", ["timeout", "output"])
def test_real_supervisor_retains_synthetic_limit_failure(tmp_path: Path, stop: str) -> None:
    """Stop a harmless Python sleeper/writer and preserve its terminal accounting."""
    output = tmp_path / "working" / "05g"
    output.mkdir(parents=True)
    partial = output / "partial.json"
    attempt = tmp_path / "supervisor-attempt"
    payload_size = 200_000 if stop == "output" else 2
    script = (
        "import time; from pathlib import Path; "
        f"Path({str(partial)!r}).write_bytes(b'x'*{payload_size}); "
        "print('synthetic partial output retained', flush=True); time.sleep(3)"
    )
    values: dict[str, Any] = {
        "max_seconds": 0.5 if stop == "timeout" else 2,
        "max_rss_bytes": 1024**3,
        "max_output_bytes": 1_000_000 if stop == "timeout" else 100_000,
        "min_free_bytes": 0,
        # Isolate the intended synthetic stop from unrelated machine swap activity.
        "max_swap_growth_bytes": 2**40,
        "sample_seconds": 0.01,
        "disk_sample_seconds": 0.02,
        "termination_grace_seconds": 0.1,
    }
    record = supervise(
        [sys.executable, "-c", script],
        attempt_root=attempt,
        output_root=output,
        limits=ExecutionLimits(**values),
    )
    assert record["status"] == "failed"
    reason = "elapsed_seconds" if stop == "timeout" else "peak_output_bytes"
    assert record["reason"] == "budget_exceeded:" + reason
    assert record["returncode"] is not None
    assert not record["surviving_pids"]
    assert partial.stat().st_size == payload_size
    assert json.loads((attempt / "execution.json").read_text()) == record
    assert (attempt / "command.log").exists()
    assert not list(output.rglob("completion.json"))
