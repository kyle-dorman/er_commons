"""Short application shell for resumable Gate C downstream qualification."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from er_commons.chunked_conversion.qualification.downstream_contracts import (
    DownstreamPaths,
    DownstreamProgress,
    DownstreamRequest,
    DownstreamStage,
    completion_result,
)
from er_commons.chunked_conversion.qualification.downstream_publication import (
    qualify_publication,
)
from er_commons.chunked_conversion.qualification.downstream_report import qualify_report
from er_commons.chunked_conversion.qualification.downstream_stages import (
    qualify_producer,
    qualify_records,
)


@dataclass(frozen=True)
class DownstreamActions:
    """Public stage seams used by the CLI and offline failure tests."""

    producer: Callable[[DownstreamPaths], Path] = qualify_producer
    records: Callable[[DownstreamPaths], object] = qualify_records
    publication: Callable[[DownstreamPaths], Path] = qualify_publication
    report: Callable[[DownstreamPaths], Path] = qualify_report


DEFAULT_ACTIONS = DownstreamActions()


def run_downstream(
    request: DownstreamRequest,
    *,
    actions: DownstreamActions = DEFAULT_ACTIONS,
    monotonic: Callable[[], float] = time.monotonic,
) -> DownstreamProgress:
    """Execute one requested stage and return a typed machine summary."""
    started = monotonic()
    paths = DownstreamPaths(request.data_root)
    if request.stage == DownstreamStage.PRODUCER:
        result: object = str(actions.producer(paths))
    elif request.stage == DownstreamStage.RECORDS:
        completions = actions.records(paths)
        as_dict = getattr(completions, "as_dict", None)
        if not callable(as_dict):
            raise TypeError("records action must return typed process completions")
        result = completion_result(as_dict(), request.data_root)
    elif request.stage == DownstreamStage.PUBLICATION:
        result = str(actions.publication(paths))
    else:
        result = str(actions.report(paths))
    return DownstreamProgress(
        stage=request.stage,
        result=result,
        wall_seconds=monotonic() - started,
    )


__all__ = ["DownstreamActions", "run_downstream"]
