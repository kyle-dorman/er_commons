#!/usr/bin/env python3
"""Build bundle from an explicit extraction review request."""

from er_commons.human_review_support.extraction_review.request import review_command


def main() -> None:
    """Parse explicit request/output paths and call the review owner."""
    review_command("build_bundle")


if __name__ == "__main__":
    main()
