"""Run a declared document source selection with durable serial progress."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.document_publication.collection_runner import (
    CollectionRunRequest,
    run_document_collection,
)
from er_commons.settings import load_settings


def main() -> int:
    """Require explicit selection; execution may access sources only when authorized."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--document-spec", required=True, type=Path)
    parser.add_argument("--progress-root", required=True, type=Path)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--source-id", action="append", default=[])
    selection.add_argument("--all-sources", action="store_true")
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    return run_document_collection(
        CollectionRunRequest(
            args.document_spec.resolve(),
            args.progress_root.resolve(),
            args.repository_root.resolve(),
            (args.data_root or load_settings().data_root).resolve(),
            tuple(args.source_id),
            args.all_sources,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
