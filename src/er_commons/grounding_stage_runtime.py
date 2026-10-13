"""Legacy native stage execution shared by the Inspect grounding adapters.

Owns preflight, bounded native attempts and stage persistence; callers own the
stage graph and final sample aggregation. Historical validation stays unchanged.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from er_commons.artifact_io import stable_json_sha256
from er_commons.grounding_native import is_transient_error, validate_completion
from er_commons.judge_packet_requests import prepare_content_request
from er_commons.judge_qualification import (
    IdentityMismatch,
    call_native_judge,
    check_live_model,
    write_new,
)

Counter = Callable[[dict[str, Any]], int]
Validator = Callable[[str, dict[str, Any]], dict[str, Any]]


async def run_stage(
    *,
    key: str,
    payload: dict[str, Any],
    prompt: str,
    version: str,
    schema: dict[str, Any],
    validator: Validator,
    directory: Path,
    settings: dict[str, Any],
    count_tokens: Counter | None,
    counter_model_digest: str | None,
    fixture: dict[str, Any] | None,
) -> dict[str, Any]:
    """Save one stage, preflight each attempt, and never retry semantic failures."""
    started = time.monotonic()
    directory.mkdir(parents=True, exist_ok=False)
    record: dict[str, Any] = {
        "key": key,
        "kind": key if key in {"conclusion", "abstention"} else "point",
        "status": "input_error",
        "attempts": 0,
        "attempt_records": [],
    }
    write_new(
        directory / "stage_input.json",
        {
            "payload": payload,
            "prompt": prompt,
            "prompt_version": version,
            "schema": schema,
            "settings_sha256": stable_json_sha256(settings),
        },
    )
    try:
        for attempt in range(2):
            prepared = prepare_content_request(
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
                system_prompt=prompt,
                response_schema=schema,
                settings=settings,
                count_tokens=count_tokens,
                counter_model_digest=counter_model_digest,
            )
            write_new(directory / f"preflight_{attempt + 1}.json", prepared)
            record["preflight"] = prepared["diagnostics"]
            if not prepared["diagnostics"]["dispatch_allowed"]:
                record["status"] = prepared["diagnostics"]["status"]
                break
            attempt_dir = directory / f"attempt_{attempt + 1}"
            attempt_dir.mkdir()
            write_new(attempt_dir / "native_request.json", prepared["request"])
            record["attempts"] += 1
            captured: dict[str, Any] = {}
            try:
                if fixture is not None:
                    output = fixture[key]
                    write_new(attempt_dir / "fixture_response.json", output)
                    captured = {
                        "output": output,
                        **(
                            validate_completion(output, settings)
                            if isinstance(output, dict)
                            else {"status": "malformed"}
                        ),
                    }
                else:
                    await asyncio.to_thread(check_live_model, settings, attempt_dir)
                    await call_native_judge(
                        {
                            "settings": settings,
                            "messages": prepared["request"]["messages"],
                            "schema": schema,
                        },
                        attempt_dir,
                        captured,
                        output_validator=validate_completion,
                    )
            except (httpx.HTTPError, OSError, IdentityMismatch, json.JSONDecodeError) as error:
                captured.update(status="runtime_error", error=repr(error))
                write_new(attempt_dir / "failure.json", captured)
                record["attempt_records"].append({"native": captured})
                record.update(status="runtime_error", native=captured)
                if not attempt and is_transient_error(error):
                    continue
                break
            record["attempt_records"].append({"native": captured})
            record.update(status=captured["status"], native=captured)
            if captured["status"] == "complete":
                if (
                    captured["output"]["prompt_eval_count"]
                    != prepared["diagnostics"]["input_tokens"]
                ):
                    record.update(
                        status="context_counter_mismatch", error="Observed input count differs"
                    )
                else:
                    try:
                        result = validator(captured["raw_judgment"], payload)
                    except ValueError as error:
                        record.update(status="schema_error", error=str(error))
                    else:
                        record.update(status="validated", result=result)
            break
    except (ValueError, KeyError) as error:
        record.update(status="input_error", error=str(error))
    record["elapsed_seconds"] = time.monotonic() - started
    write_new(directory / "stage_record.json", record)
    return record
