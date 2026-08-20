#!/usr/bin/env python3
"""Run Task 03H.2 Gate C's restartable G1 qualification."""

import argparse
from pathlib import Path

from er_commons.chunked_conversion.qualification.contracts import GateCRequest, ResourceLimits
from er_commons.chunked_conversion.qualification.gate_c_application import (
    run_aggregate_worker,
    run_gate_c,
    run_range_worker,
)
from er_commons.chunked_conversion.qualification.gate_c_inputs import (
    DEFAULT_CONFIG,
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_SOURCE_ROOT,
    resolve_data_root,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--stop-after-ranges", type=int)
    parser.add_argument("--max-range-rss-bytes", type=int, default=8 * 1024**3)
    parser.add_argument("--max-aggregate-rss-bytes", type=int, default=10 * 1024**3)
    parser.add_argument("--max-wall-seconds", type=float, default=2700.0)
    parser.add_argument("--worker-spec", type=Path)
    parser.add_argument("--aggregate-spec", type=Path)
    args = parser.parse_args()
    if args.worker_spec and args.aggregate_spec:
        parser.error("select at most one worker mode")
    if args.worker_spec:
        run_range_worker(args.worker_spec.resolve())
        return 0
    if args.aggregate_spec:
        run_aggregate_worker(args.aggregate_spec.resolve())
        return 0
    data_root = resolve_data_root(args.data_root)
    limits = {"max_wall_seconds": args.max_wall_seconds}
    request = GateCRequest(
        data_root=data_root,
        source_root=(args.source_root or data_root / DEFAULT_SOURCE_ROOT).resolve(),
        output_root=(args.output_root or data_root / DEFAULT_OUTPUT_ROOT).resolve(),
        config_path=args.config.resolve(),
        stop_after_ranges=args.stop_after_ranges,
        range_limits=ResourceLimits(max_rss_bytes=args.max_range_rss_bytes, **limits),
        aggregate_limits=ResourceLimits(max_rss_bytes=args.max_aggregate_rss_bytes, **limits),
    )
    print(run_gate_c(request, project_root=PROJECT_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
