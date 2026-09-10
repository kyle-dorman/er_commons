"""Thin explicit-input interfaces for the three source-free navigation stages."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import fields
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from er_commons.artifact_io import read_json_object

from .input_specs import MaterializationBindings, PreparationBindings, ReconciliationBindings
from .materialization import GateBMaterializationRequest, prepare_and_publish_gate_b
from .preparation import GateAPreparationRequest, prepare_and_publish_gate_a
from .reconciliation import GateCReconciliationRequest, prepare_and_publish_gate_c


def main(stage: str, argv: Sequence[str] | None = None) -> int:
    """Read one complete invocation spec; paths resolve relative to that spec."""
    parser = argparse.ArgumentParser(description=f"Source-free navigation {stage}")
    parser.add_argument("--input-spec", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args(argv)
    spec_path = args.input_spec.resolve()
    raw = read_json_object(spec_path)
    if stage == "prepare":
        publication = _publish(
            raw,
            spec_path,
            args.output_root,
            GateAPreparationRequest,
            PreparationBindings,
            prepare_and_publish_gate_a,
        )
    elif stage == "materialize":
        publication = _publish(
            raw,
            spec_path,
            args.output_root,
            GateBMaterializationRequest,
            MaterializationBindings,
            prepare_and_publish_gate_b,
        )
    elif stage == "reconcile":
        publication = _publish(
            raw,
            spec_path,
            args.output_root,
            GateCReconciliationRequest,
            ReconciliationBindings,
            prepare_and_publish_gate_c,
        )
    else:
        raise ValueError(f"unsupported navigation operation: {stage}")
    print(f"navigation_{stage}={publication}")
    return 0


def _publish[
    RequestT: (GateAPreparationRequest, GateBMaterializationRequest, GateCReconciliationRequest)
](
    raw: dict[str, Any],
    spec_path: Path,
    output_root: Path,
    request_type: type[RequestT],
    binding_type: type[BaseModel],
    publish: Callable[[RequestT], Path],
) -> Path:
    """Construct the matching immutable request from a closed input object."""
    required = {field.name for field in fields(request_type)} - {"output_parent"}
    if set(raw) != required:
        raise ValueError(f"input spec fields differ: expected {sorted(required)}")
    values: dict[str, Any] = {"output_parent": output_root.resolve()}
    for name, value in raw.items():
        if name == "bindings":
            values[name] = binding_type.model_validate(value)
        elif isinstance(value, str) and value:
            values[name] = (spec_path.parent / value).resolve()
        else:
            raise ValueError(f"input spec {name} must be a nonempty path")
    return publish(request_type(**values))
