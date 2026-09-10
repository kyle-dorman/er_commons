"""Explicit deep regression audit over selected document relink inputs."""

import argparse
import json
import logging
from pathlib import Path

from er_commons.artifact_io import atomic_text_writer
from er_commons.navigation_overlay.relink_run_validation import (
    run_gate_c_validation,
)
from er_commons.navigation_overlay.validation_spec import load_validation_spec

LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Run an explicitly selected deep regression audit; this reads payload bytes."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", choices=["deep-regression-audit"], required=True)
    parser.add_argument("--validation-spec", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--link-spec", type=Path, required=True)
    parser.add_argument("--navigation-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reviewed-input-root", type=Path)
    parser.add_argument("--semantic-dispositions", type=Path)
    args = parser.parse_args()
    validation = load_validation_spec(args.validation_spec)
    if (args.reviewed_input_root is None) != (args.semantic_dispositions is None):
        parser.error("--reviewed-input-root and --semantic-dispositions must be supplied together")
    evidence = run_gate_c_validation(
        data_root=args.data_root,
        link_spec_path=args.link_spec,
        repository_root=Path(__file__).resolve().parents[1],
        navigation_root=args.navigation_root,
        validation=validation,
        reviewed_input_root=args.reviewed_input_root,
        semantic_dispositions_path=args.semantic_dispositions,
    )
    with atomic_text_writer(args.output) as stream:
        json.dump(evidence, stream, indent=2, sort_keys=True)
        stream.write("\n")
    LOGGER.info("wrote Gate C evidence to %s", args.output)


if __name__ == "__main__":
    main()
