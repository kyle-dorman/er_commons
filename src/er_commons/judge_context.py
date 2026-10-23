"""Share the frozen Baylands overview across new judge execution paths."""

from __future__ import annotations

import hashlib
from pathlib import Path

OVERVIEW_PATH = Path(__file__).resolve().parents[2] / "docs/prompts/task11d14_document_overview.md"
OVERVIEW_SHA256 = "3b7e196bc74085c947526a060f7f9dae2637505bf7f65da093c624a98970abc5"


def baylands_overview() -> str:
    """Load the exact accepted real-evaluation context, rejecting unversioned drift."""
    content = OVERVIEW_PATH.read_bytes()
    if hashlib.sha256(content).hexdigest() != OVERVIEW_SHA256:
        raise ValueError("Baylands overview changed; version its judge context before dispatch")
    return content.decode("utf-8")


def compose_project_context(prompt: str, summary: str) -> str:
    """Use the frozen envelope layout and never duplicate an existing context prefix."""
    if not isinstance(summary, str) or not summary.strip() or not prompt.strip():
        raise ValueError("Shared summary and prompt must be nonblank")
    prefix = "<project_context>\n" + summary + "\n</project_context>\n\n"
    if prompt.startswith("<project_context>"):
        if not prompt.startswith(prefix):
            raise ValueError("Judge prompt and envelope project context differ")
        return prompt
    return prefix + prompt


def structured_conclusion_prompt(prompt: str) -> str:
    """Compose the new C prompt with the same overview used in real judgments."""
    return compose_project_context(prompt, baylands_overview())
