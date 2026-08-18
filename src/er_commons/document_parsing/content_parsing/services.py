"""Narrow side-effect seams for the complete-document producer."""

from __future__ import annotations

import subprocess
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Protocol, Self

from er_commons.document_parsing.content_parsing.config import HeadingHierarchyConfig
from er_commons.document_parsing.content_parsing.runtime import MemorySampler, build_converter
from er_commons.document_parsing.table_reconstruction.pipeline import run_table_extraction


class ConverterBuilder(Protocol):
    """Construct the accepted converter and its effective configuration."""

    def __call__(
        self,
        models_root: Path,
        *,
        thread_count: int,
        heading_hierarchy_options: HeadingHierarchyConfig | None = None,
    ) -> tuple[Any, Any, Any]: ...


class TableRunner(Protocol):
    """Run the complete table stage inside an explicit artifact root."""

    def __call__(
        self,
        data_root: Path,
        config_path: Path,
        artifact_root_override: Path | None = None,
    ) -> Path: ...


class MemoryObservation(Protocol):
    """Context-managed peak-RSS observation used around conversion."""

    peak_rss_bytes: int

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...


@dataclass(frozen=True)
class GitState:
    """Repository state captured with each producer run."""

    commit: str
    dirty: bool


def read_git_state(repo_root: Path) -> GitState:
    """Read Git state with checked, shell-free subprocess calls."""
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return GitState(commit=commit, dirty=bool(status.strip()))


def utc_now() -> datetime:
    """Return one timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def new_token() -> str:
    """Return an unpredictable token for staging and attempt directory names."""
    return uuid.uuid4().hex


@dataclass(frozen=True)
class ContentParsingServices:
    """Replace only expensive or nondeterministic edges in offline tests."""

    build_converter: ConverterBuilder = build_converter
    run_tables: TableRunner = run_table_extraction
    memory_observation: Callable[[], MemoryObservation] = MemorySampler
    monotonic: Callable[[], float] = time.perf_counter
    process_time: Callable[[], float] = time.process_time
    now: Callable[[], datetime] = utc_now
    new_token: Callable[[], str] = new_token
    read_git_state: Callable[[Path], GitState] = read_git_state
