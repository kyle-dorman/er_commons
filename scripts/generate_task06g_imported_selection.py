"""Generate or check the exact Task 06G v32 imported-document selection."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.collection_processing.selection_generation import (
    write_imported_selection,
)


def main() -> None:
    """Parse explicit roots and produce no-clobber deterministic bytes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--document-input-root", type=Path, required=True)
    parser.add_argument("--retained-collection-spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    write_imported_selection(
        data_root=args.data_root,
        document_input_root=args.document_input_root,
        retained_collection_spec=args.retained_collection_spec,
        output=args.output,
        check=args.check,
    )


if __name__ == "__main__":
    main()
