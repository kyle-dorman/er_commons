"""External service seams for the bounded smoke application."""

from __future__ import annotations

import shutil
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from er_commons.document_extraction.runtime import build_converter, verify_model_inventory
from er_commons.document_extraction.sources import CompleteResolvedSource
from er_commons.smoke_extraction.config import SmokeSpec
from er_commons.smoke_extraction.conversion import RangeDiagnostic, convert_range
from er_commons.smoke_extraction.records import RouteRecord
from er_commons.smoke_extraction.selection import resolve_source_bytes
from er_commons.smoke_extraction.table_stage import run_smoke_tables


@dataclass(frozen=True)
class SmokeServices:
    """Named expensive and nondeterministic edges used by the smoke workflow."""

    resolve_source: Callable[[Path, SmokeSpec, str], CompleteResolvedSource] = resolve_source_bytes
    build_converter: Callable[..., tuple[Any, Any, Any]] = build_converter
    verify_models: Callable[[Path, Path], tuple[Any, Path]] = verify_model_inventory
    convert: Callable[..., RangeDiagnostic] = convert_range
    route: Callable[[Path, dict[str, Any], int, SmokeSpec], RouteRecord] | None = None
    run_tables: Callable[..., dict[int, dict[str, Any]]] = run_smoke_tables
    disk_usage: Callable[[Path], Any] = shutil.disk_usage
    monotonic: Callable[[], float] = time.perf_counter
    new_token: Callable[[], str] = lambda: uuid.uuid4().hex
