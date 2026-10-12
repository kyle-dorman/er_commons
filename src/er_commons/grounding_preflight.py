"""Record the frozen panel's context gate through Inspect without inference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from er_commons.grounding_inspect import SavedGroundingSample, evaluate_grounding_samples
from er_commons.grounding_panel import load_panel_samples


def main() -> None:
    """Require explicit frozen inputs; no heuristic counter or inference fallback."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--panel", choices=("dev3", "dev6"), required=True)
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        samples = [
            SavedGroundingSample.model_validate(row)
            for row in load_panel_samples(args.manifest, args.panel)
        ]
        settings = json.loads(args.settings.read_text(encoding="utf-8"))
        logs = evaluate_grounding_samples(
            samples,
            settings=settings,
            artifact_dir=args.output / "requests",
            log_dir=args.output / "inspect",
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if any(log.status != "success" for log in logs):
        raise SystemExit("Inspect preflight recording failed; inspect the saved log")


if __name__ == "__main__":
    main()
