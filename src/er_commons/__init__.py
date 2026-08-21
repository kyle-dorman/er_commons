"""Lightweight package entrypoints for ER Commons."""


def main() -> None:
    """Load and run the CLI only when the CLI entrypoint is requested."""
    from er_commons.cli import main as cli_main

    cli_main()


__all__ = ["main"]
