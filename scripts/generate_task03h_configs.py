"""CLI facade for deterministic Task 03H production-spec generation."""

from __future__ import annotations

import argparse
from pathlib import Path

from task03h_generation.workflow import generate_task03h

from er_commons.settings import load_settings


def main() -> None:
    """Generate or check every Task 03H config without reading source PDFs/models."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    data_root = (args.data_root or load_settings().data_root).resolve()
    generate_task03h(data_root, check=args.check)


if __name__ == "__main__":
    main()
