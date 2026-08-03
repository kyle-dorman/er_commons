"""One-shot child process for a complete document transaction."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.corpus_extraction.config import load_run_spec
from er_commons.corpus_extraction.content_owners import run_content_owners
from er_commons.source_freeze import write_json_atomic


def main() -> None:
    """Run exactly one document and persist a minimal typed handoff."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--run-spec", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    spec, _digest = load_run_spec(args.run_spec)
    result = run_content_owners(
        data_root=args.data_root,
        project_root=args.project_root,
        run_spec=spec,
        source_id=args.source_id,
    )
    write_json_atomic(args.result, result.model_dump(mode="json"))


if __name__ == "__main__":
    main()
