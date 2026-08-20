#!/usr/bin/env python3
"""Run Task 03H.2 Gate B's bounded split-versus-contiguous qualification."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from er_commons.chunked_conversion.qualification.gate_b_application import (
    GateBRunRequest,
    run_gate_b,
    run_worker_spec,
)
from er_commons.chunked_conversion.qualification.gate_b_contracts import (
    DEFAULT_CONFIG,
    DEFAULT_SOURCE_ROOT,
)


def main() -> None:
    """Dispatch the public coordinator or one private seam worker."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--max-rss-bytes", type=int, default=8 * 1024**3)
    parser.add_argument("--max-wall-seconds", type=float, default=45 * 60)
    parser.add_argument("--worker-spec", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker_spec is not None:
        run_worker_spec(args.worker_spec.resolve())
        return
    if args.output_root is None:
        parser.error("--output-root is required")
    configured_root = args.data_root or os.environ.get("ER_COMMONS_DATA_ROOT")
    if configured_root is None:
        parser.error("ER_COMMONS_DATA_ROOT or --data-root is required")
    completion = run_gate_b(
        GateBRunRequest(
            source_root=args.source_root.resolve(),
            config_path=args.config.resolve(),
            data_root=Path(configured_root).resolve(),
            output_root=args.output_root.resolve(),
            max_rss_bytes=args.max_rss_bytes,
            max_wall_seconds=args.max_wall_seconds,
        )
    )
    print(completion)


if __name__ == "__main__":
    main()
