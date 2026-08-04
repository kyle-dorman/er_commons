"""Restartable scope accounting, indexing, resolution, and handoff."""

from er_commons.corpus_resolution.config import ScopeRunSpec, load_scope_run_spec
from er_commons.corpus_resolution.domain import ScopeHooks, StageHooks
from er_commons.corpus_resolution.workflow import run_scope

__all__ = ["ScopeHooks", "ScopeRunSpec", "StageHooks", "load_scope_run_spec", "run_scope"]
