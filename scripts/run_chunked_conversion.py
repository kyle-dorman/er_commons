#!/usr/bin/env python3
"""Run or resume one explicit restartable chunk-conversion plan."""

import argparse
from pathlib import Path

from er_commons.chunked_conversion.runtime import (
    ChunkedConversionRequest,
    ResourceLimits,
    run_aggregate_worker,
    run_range_worker,
)
from er_commons.chunked_conversion.runtime.inputs import resolve_data_root
from er_commons.document_parsing.content_parsing.chunked_application import (
    run_chunked_document_parsing,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--conversion-root", type=Path)
    parser.add_argument("--stop-after-ranges", type=int)
    parser.add_argument("--max-range-rss-bytes", type=int, default=20 * 1024**3)
    parser.add_argument("--max-aggregate-rss-bytes", type=int, default=16 * 1024**3)
    parser.add_argument("--max-wall-seconds", type=float, default=14400.0)
    parser.add_argument("--worker-spec", type=Path)
    parser.add_argument("--aggregate-spec", type=Path)
    args = parser.parse_args()
    if args.worker_spec:
        run_range_worker(args.worker_spec.resolve())
        return 0
    if args.aggregate_spec:
        run_aggregate_worker(args.aggregate_spec.resolve())
        return 0
    required = (args.config, args.plan, args.run_root, args.conversion_root)
    if any(value is None for value in required):
        parser.error(
            "coordinator mode requires --config, --plan, --run-root, and --conversion-root"
        )
    data_root = resolve_data_root(args.data_root)
    limits = {"max_wall_seconds": args.max_wall_seconds}
    request = ChunkedConversionRequest(
        data_root=data_root,
        config_path=args.config.resolve(),
        plan_path=args.plan.resolve(),
        output_root=args.run_root.resolve(),
        conversion_root=args.conversion_root.resolve(),
        stop_after_ranges=args.stop_after_ranges,
        range_limits=ResourceLimits(max_rss_bytes=args.max_range_rss_bytes, **limits),
        aggregate_limits=ResourceLimits(max_rss_bytes=args.max_aggregate_rss_bytes, **limits),
    )
    print(
        run_chunked_document_parsing(
            data_root,
            args.config.resolve(),
            args.plan.resolve(),
            request=request,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
