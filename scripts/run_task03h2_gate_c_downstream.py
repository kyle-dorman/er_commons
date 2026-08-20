#!/usr/bin/env python3
"""Run one resumable Gate C downstream qualification stage."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.chunked_conversion.qualification.downstream_application import run_downstream
from er_commons.chunked_conversion.qualification.downstream_contracts import (
    DownstreamRequest,
    DownstreamStage,
)


def main() -> None:
    """Parse CLI arguments and print the typed stage result."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument(
        "--stage",
        choices=tuple(stage.value for stage in DownstreamStage),
        default=DownstreamStage.PRODUCER.value,
    )
    args = parser.parse_args()
    request = DownstreamRequest(
        data_root=args.data_root.resolve(),
        stage=DownstreamStage(args.stage),
    )
    print(run_downstream(request).model_dump_json())


if __name__ == "__main__":
    main()
