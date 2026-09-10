"""Qualify an explicitly selected document/collection input namespace."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from er_commons.document_publication.input_preparation import (
    InputPreparationRequest,
    prepare_document_inputs,
)
from er_commons.settings import load_settings


def main() -> None:
    """Resolve settings only after explicit command arguments are parsed."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("document-spec", "collection-spec", "output-root"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--resume-existing", action="store_true")
    args = parser.parse_args()
    result = prepare_document_inputs(
        InputPreparationRequest(
            args.document_spec,
            args.collection_spec,
            args.output_root,
            args.data_root or load_settings().data_root,
            args.repository_root,
            args.resume_existing,
        )
    )
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).info("Preparation readiness: %s", result)


if __name__ == "__main__":
    main()
