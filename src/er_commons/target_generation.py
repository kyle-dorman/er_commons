"""Bounded evidence-only Luna smoke generation through native Inspect and OpenAI.

HTTP hooks capture the actual SDK body and count it before generation dispatch.
Every attempt is create-only; uncertain or failed attempts are never rerolled.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import os
import time
from pathlib import Path
from typing import Any, cast

from inspect_ai.model import (
    ChatMessageSystem,
    ChatMessageUser,
    GenerateConfig,
    ResponseSchema,
    get_model,
)
from jsonschema import validate  # type: ignore[import-untyped]
from openai import DefaultAsyncHttpxClient

from er_commons.artifact_io import (
    artifact_inventory,
    assert_contained,
    json_bytes,
    publish_bytes_no_clobber,
    sha256_bytes,
    sha256_file,
    stable_json_sha256,
)
from er_commons.evidence_only import Payload
from er_commons.judge_inspect import _schema
from er_commons.judge_packets import Answer

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "configs/task11b_luna_v1.json"
PROMPT = REPO / "docs/prompts/task11b_luna_v1.md"
PANEL = REPO / "docs/specs/task11a_development_panels_v1.json"
INITIAL = ["C041", "C017", "C019"]
EXPANDED = [*INITIAL, "C014", "C037", "C056"]
COUNT_FIELDS = {
    "model",
    "input",
    "instructions",
    "reasoning",
    "text",
    "tools",
    "tool_choice",
    "parallel_tool_calls",
    "truncation",
}


def save(path: Path, value: Any) -> None:
    """Publish deterministic JSON without replacing prior evidence."""
    publish_bytes_no_clobber(path, json_bytes(value))


def validate_config(config: Any, *, panel_size: int) -> None:
    """Reject invalid budgets and metadata that disagrees with the native transport."""
    if not isinstance(config, dict):
        raise ValueError("Generation configuration must be an object")
    for key in (
        "context_tokens",
        "max_input_tokens",
        "max_output_tokens",
        "max_generation_calls",
        "max_count_calls",
        "max_elapsed_seconds",
        "timeout_seconds",
    ):
        value: Any = config.get(key)
        if type(value) is not int or value <= 0:
            raise ValueError(f"Invalid positive integer generation limit: {key}")
    for key in (
        "max_spend_usd",
        "reserve_input_per_million",
        "reserve_output_per_million",
        "count_cost_allowance_usd",
    ):
        value = config.get(key)
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"Invalid finite generation budget: {key}")
        if value < 0 or (value == 0 and key != "count_cost_allowance_usd"):
            raise ValueError(f"Invalid generation budget: {key}")
    for key, expected in {
        "provider": "openai",
        "base_url": "https://api.openai.com/v1",
        "service_tier": "default",
        "reasoning_summary": "none",
    }.items():
        if config.get(key) != expected:
            raise ValueError(f"Generation transport setting differs: {key}")
    if type(config.get("max_retries")) is not int or config["max_retries"] != 0:
        raise ValueError("Automatic retries are forbidden")
    for key in ("model", "reasoning_effort"):
        if not isinstance(config.get(key), str) or not config[key].strip():
            raise ValueError(f"Missing generation setting: {key}")
    if any(config[key] < panel_size for key in ("max_generation_calls", "max_count_calls")):
        raise ValueError("Call limits do not cover the complete fixed panel")
    if config["max_input_tokens"] + config["max_output_tokens"] > config["context_tokens"]:
        raise ValueError("Input/output limits exceed the declared context window")


def panel_case_ids(panel: str) -> list[str]:
    """Allow only the fixed nested Task 11A panels, never arbitrary case selections."""
    if panel not in {"initial_three", "expanded_six"}:
        raise ValueError("Unsupported development panel")
    return list(INITIAL if panel == "initial_three" else EXPANDED)


def load_smoke(
    data_root: Path, *, panel: str = "initial_three"
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Verify accepted development bindings without opening evaluator/test files."""
    selected_ids = panel_case_ids(panel)
    manifest = json.loads(PANEL.read_text())
    if manifest["initial_three"] != INITIAL or manifest["fixed_six"] != EXPANDED:
        raise ValueError("Fixed panel changed")
    paths = {}
    for key in ("target/dev.jsonl", "completion.json"):
        binding = manifest["inputs"][key]
        path = assert_contained(data_root, binding["path_relative_to_data_root"])
        if sha256_file(path) != binding["sha256"] or path.stat().st_size != binding["byte_size"]:
            raise ValueError(f"Accepted input binding changed: {key}")
        paths[key] = path
    expected = {row["case_id"]: row["target"]["record_sha256"] for row in manifest["cases"]}
    selected = {}
    for line in paths["target/dev.jsonl"].read_bytes().splitlines():
        row = json.loads(line)
        if row["case_id"] in selected_ids:
            if row["case_id"] in selected or sha256_bytes(line) != expected[row["case_id"]]:
                raise ValueError("Duplicate or changed selected record")
            validate_record(row)
            selected[row["case_id"]] = row
    if set(selected) != set(selected_ids):
        raise ValueError("Missing panel case")
    return [selected[key] for key in selected_ids], {
        "panel_sha256": sha256_file(PANEL),
        "task10_completion_sha256": sha256_file(paths["completion.json"]),
        "target_file_sha256": sha256_file(paths["target/dev.jsonl"]),
        "record_sha256": {key: expected[key] for key in selected_ids},
    }


def validate_record(record: dict[str, Any]) -> None:
    """Forbid reference/selection metadata and duplicate local citation IDs."""
    if set(record) != {"schema_version", "case_id", "payload"}:
        raise ValueError("Unexpected target record fields")
    if record["schema_version"] != "task10.evidence_only.v1":
        raise ValueError("Unsupported target schema")
    Payload.model_validate(record["payload"])
    ids = [p["citation_id"] for p in record["payload"]["passages"]]
    if len(ids) != len(set(ids)) or any(not value for value in ids):
        raise ValueError("Duplicate or empty passage citation ID")


def validate_answer(text: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate unchanged answer prose and resolve every case-local citation."""
    value = json.loads(text)
    validate(value, output_schema())
    required = {"status", "conclusion", "supporting_points", "qualifications", "optional_context"}
    if set(value) != required:
        raise ValueError("Answer field inventory differs")
    answer = Answer.model_validate(value)
    points = [
        answer.conclusion,
        *answer.supporting_points,
        *answer.qualifications,
        *answer.optional_context,
    ]
    ids = [point.point_id for point in points]
    if len(ids) != len(set(ids)) or any(not item.strip() for item in ids):
        raise ValueError("Invalid point identities")
    allowed = {p["citation_id"]: p for p in payload["passages"]}
    for point in points:
        if not point.text.strip() or not set(point.citation_ids) <= set(allowed):
            raise ValueError("Empty assertion or unresolved citation")
        if not set(point.applies_to) <= set(ids):
            raise ValueError("Unresolved applies_to")
        if answer.status == "answered" and not point.citation_ids:
            raise ValueError("Uncited substantive assertion")
    if answer.status == "answered" and not answer.supporting_points:
        raise ValueError("Answered candidate lacks supporting points")
    if answer.status == "abstained" and len(points) != 1:
        raise ValueError("Abstention contains other prose")
    return cast(dict[str, Any], value)


def output_schema() -> dict[str, Any]:
    """Use the established answer fields with no model-authored source locators."""
    schema = Answer.model_json_schema()
    schema["properties"].pop("citation_locators")
    value = _schema(schema, "openai")

    def strip_titles(node: Any) -> None:
        """Match native Inspect cosmetic schema normalization."""
        if isinstance(node, dict):
            node.pop("title", None)
            for child in node.values():
                strip_titles(child)
        elif isinstance(node, list):
            for child in node:
                strip_titles(child)

    strip_titles(value)
    return value


def readable(answer: dict[str, Any], payload: dict[str, Any]) -> str:
    """Render readable labels without modifying candidate text or citation IDs."""
    labels = {
        p["citation_id"]: f"{p['title']} / {' > '.join(p['heading_path'])} / "
        f"pages {', '.join(p['printed_labels']) or ', '.join(map(str, p['physical_pages']))}"
        for p in payload["passages"]
    }
    points = [
        answer["conclusion"],
        *answer["supporting_points"],
        *answer["qualifications"],
        *answer["optional_context"],
    ]
    return (
        "\n\n".join(
            point["text"]
            + "\n"
            + "; ".join(f"[{cid}] {labels[cid]}" for cid in point["citation_ids"])
            for point in points
        )
        + "\n"
    )


class ReceiptHooks:
    """Single-attempt HTTP audit and fail-closed context/spending gate."""

    def __init__(self, directory: Path, config: dict[str, Any], deadline: float) -> None:
        """Bind hooks to one immutable case attempt and the declared deadline."""
        self.directory = directory
        self.config = config
        self.deadline = deadline
        self.client: Any = None
        self.expected_input: list[dict[str, Any]] = []
        self.count_calls = 0
        self.generation_calls = 0

    async def request(self, request: Any) -> None:
        """Count exact native request content before allowing generation onto wire."""
        path = request.url.path
        if request.url.host != "api.openai.com":
            raise ValueError("Provider endpoint changed")
        if time.monotonic() >= self.deadline:
            raise ValueError("Run timebox exhausted before provider dispatch")
        body = await request.aread()
        if path.endswith("/responses/input_tokens"):
            if json.loads(body) != json.loads(
                (self.directory / "count_projection.json").read_text()
            ):
                raise ValueError("Counter content differs from generation request")
            self.count_calls += 1
            if self.count_calls > 1:
                raise ValueError("Count retry forbidden")
            save(
                self.directory / "count_dispatch.json",
                {
                    "reserved_cost_usd": self.config["count_cost_allowance_usd"],
                    "actual_cost_usd": None,
                    "request_sha256": sha256_bytes(body),
                },
            )
            publish_bytes_no_clobber(self.directory / "count_request.json", body)
            return
        if not path.endswith("/responses"):
            raise ValueError("Unexpected provider endpoint")
        if (self.directory / "dispatch.json").exists():
            raise ValueError("Generation retry forbidden")
        publish_bytes_no_clobber(self.directory / "native_request.json", body)
        native = json.loads(body)
        if native["model"] != self.config["model"] or native.get("truncation") != "disabled":
            raise ValueError("Native identity/truncation differs")
        if native.get("max_output_tokens") != self.config["max_output_tokens"]:
            raise ValueError("Output cap differs")
        allowed_fields = COUNT_FIELDS | {
            "max_output_tokens",
            "store",
            "service_tier",
            "include",
            "background",
        }
        if (
            native.get("include") != ["reasoning.encrypted_content"]
            or native.get("background") is not False
            or native.get("store") is not False
            or native.get("service_tier") != "default"
        ):
            raise ValueError("Native output/control settings differ")
        if set(native) - allowed_fields:
            raise ValueError("Unknown native fields; count coverage unverified")
        if (
            native["input"] != self.expected_input
            or native["text"]["format"]["schema"] != output_schema()
        ):
            raise ValueError("Native prompt/payload/schema differs")
        if native.get("reasoning") != {"effort": self.config["reasoning_effort"]}:
            raise ValueError("Native reasoning settings differ")
        count_payload = {key: value for key, value in native.items() if key in COUNT_FIELDS}
        save(self.directory / "count_projection.json", count_payload)
        count = await self.client.responses.input_tokens.count(**count_payload)
        tokens = count.input_tokens
        if type(tokens) is not int or tokens <= 0:
            raise ValueError("context_unverified: invalid exact count")
        reserve = (
            tokens * self.config["reserve_input_per_million"]
            + self.config["max_output_tokens"] * self.config["reserve_output_per_million"]
        ) / 1_000_000
        preflight = {
            "native_request_sha256": sha256_bytes(body),
            "input_tokens": tokens,
            "output_reserve": self.config["max_output_tokens"],
            "reserved_generation_cost_usd": reserve,
            "reserved_count_cost_usd": self.config["count_cost_allowance_usd"],
            "actual_count_cost_usd": None,
            "count_response": count.model_dump(mode="json"),
        }
        save(self.directory / "preflight.json", preflight)
        if tokens > self.config["max_input_tokens"] or (
            tokens + self.config["max_output_tokens"] > self.config["context_tokens"]
        ):
            raise ValueError("context_overflow: no truncation permitted")
        if (
            reserve * self.config["max_generation_calls"]
            + self.config["count_cost_allowance_usd"] * self.config["max_count_calls"]
        ) > self.config["max_spend_usd"]:
            raise ValueError("Spending reserve exceeds run ceiling")
        if time.monotonic() >= self.deadline:
            raise ValueError("Run timebox exhausted")
        save(self.directory / "dispatch.json", preflight)
        self.generation_calls += 1

    async def response(self, response: Any) -> None:
        """Preserve full response body/status without persisting credential headers."""
        prefix = "count" if response.request.url.path.endswith("/input_tokens") else "generation"
        publish_bytes_no_clobber(self.directory / f"{prefix}_response.body", await response.aread())
        save(
            self.directory / f"{prefix}_response.json",
            {
                "status_code": response.status_code,
                "request_id": response.headers.get("x-request-id"),
            },
        )


async def generate_one(
    record: dict[str, Any],
    directory: Path,
    config: dict[str, Any],
    prompt: str,
    deadline: float,
    *,
    repeat: int = 1,
) -> dict[str, Any]:
    """Run one native generation, retaining malformed outputs and explicit failures."""
    if type(repeat) is not int or repeat not in (1, 2):
        raise ValueError("Only primary and one stability repeat are allowed")
    validate_record(record)
    hooks = ReceiptHooks(directory, config, deadline)
    hooks.expected_input = [
        {"type": "message", "role": role, "content": [{"type": "input_text", "text": text}]}
        for role, text in (
            ("developer", prompt),
            ("user", json.dumps(record["payload"], ensure_ascii=False)),
        )
    ]
    result: dict[str, Any] = {"case_id": record["case_id"], "attempt": 1, "repeat": repeat}
    client = DefaultAsyncHttpxClient(
        event_hooks={"request": [hooks.request], "response": [hooks.response]}
    )
    try:
        settings = GenerateConfig(
            max_tokens=config["max_output_tokens"],
            max_retries=0,
            max_connections=1,
            timeout=config["timeout_seconds"],
            attempt_timeout=config["timeout_seconds"],
            cache=False,
            reasoning_effort=config["reasoning_effort"],
            reasoning_summary="none",
            response_schema=ResponseSchema.model_validate(
                {"name": "task11b_answer_v1", "json_schema": output_schema(), "strict": True}
            ),
            extra_body={"store": False, "truncation": "disabled"},
        )
        model = get_model(
            f"openai/{config['model']}",
            config=settings,
            memoize=False,
            base_url=config["base_url"],
            responses_api=True,
            responses_store=False,
            max_retries=0,
            streaming=False,
            background=False,
            service_tier="default",
            http_client=client,
        )
        hooks.client = model.api.client  # type: ignore[attr-defined]
        output = await model.generate(
            [
                ChatMessageSystem(content=prompt),
                ChatMessageUser(content=json.dumps(record["payload"], ensure_ascii=False)),
            ]
        )
        save(directory / "inspect_output.json", output.model_dump(mode="json"))
        publish_bytes_no_clobber(directory / "raw_answer.txt", output.completion.encode())
        result.update(
            returned_model=output.model,
            response_id=output.response_id,
            usage=output.usage.model_dump(mode="json") if output.usage else None,
        )
        if output.stop_reason != "stop":
            raise ValueError(f"Noncomplete output: {output.stop_reason}")
        if output.model != config["model"] or output.usage is None:
            raise ValueError("Returned model or usage unverified; accounting uncertain")
        usage = output.usage
        effective_input = (
            usage.input_tokens
            + (usage.input_tokens_cache_read or 0)
            + (usage.input_tokens_cache_write or 0)
        )
        if (
            any(
                value < 0
                for value in (
                    usage.input_tokens,
                    usage.output_tokens,
                    usage.input_tokens_cache_read or 0,
                    usage.input_tokens_cache_write or 0,
                )
            )
            or not 0 < effective_input <= config["max_input_tokens"]
            or usage.output_tokens > config["max_output_tokens"]
        ):
            raise ValueError("Usage exceeds reserve or is invalid; accounting uncertain")
        answer = validate_answer(output.completion, record["payload"])
        save(directory / "candidate.json", answer)
        publish_bytes_no_clobber(
            directory / "candidate.md", readable(answer, record["payload"]).encode()
        )
        result.update(
            status="valid",
            candidate_sha256=sha256_file(directory / "candidate.json"),
        )
    except Exception as error:
        causes: list[dict[str, str]] = []
        cause: BaseException | None = error
        while cause is not None and len(causes) < 8:
            causes.append({"type": type(cause).__name__, "message": str(cause)})
            cause = cause.__cause__
        result.update(
            status="failed",
            failure_type=type(error).__name__,
            failure=str(error),
            failure_causes=causes,
        )
    finally:
        try:
            await client.aclose()
        except Exception as error:
            result.update(
                status="failed",
                cleanup_error=f"{type(error).__name__}: {error}",
            )
            result.setdefault("failure_type", type(error).__name__)
            result.setdefault("failure", f"Client cleanup failed: {error}")
    result.update(count_calls=hooks.count_calls, generation_calls=hooks.generation_calls)
    manifest = directory.parent / "manifest.json"
    result["run_id"] = (
        json.loads(manifest.read_text())["run_id"] if manifest.exists() else "offline_fixture"
    )
    if (directory / "native_request.json").exists():
        result["request_sha256"] = sha256_file(directory / "native_request.json")
    result["candidate_id"] = stable_json_sha256(
        {
            key: result.get(key)
            for key in (
                "run_id",
                "case_id",
                "attempt",
                "repeat",
                "request_sha256",
                "candidate_sha256",
            )
        }
    )
    save(directory / "result.json", result)
    save(directory / "completion.json", artifact_inventory(directory, {"completion.json"}))
    return result


async def run(
    data_root: Path,
    output: Path,
    *,
    config_path: Path = CONFIG,
    prompt_path: Path = PROMPT,
    panel: str = "initial_three",
    repeat: int = 1,
) -> dict[str, Any]:
    """Attempt a complete fixed panel once, retaining exact run and repeat identities."""
    if not data_root.is_dir() or not output.resolve().is_relative_to(data_root.resolve()):
        raise ValueError("Output must be under existing configured external root")
    case_ids = panel_case_ids(panel)
    if type(repeat) is not int or repeat not in (1, 2):
        raise ValueError("Only primary and one stability repeat are allowed")
    records, bindings = load_smoke(data_root, panel=panel)
    config = json.loads(config_path.read_text())
    validate_config(config, panel_size=len(case_ids))
    prompt = prompt_path.read_text()
    identity = {
        "schema_version": "task11b.run.v1",
        "run_id": stable_json_sha256(str(output.resolve().relative_to(data_root.resolve()))),
        "namespace": str(output.resolve().relative_to(data_root.resolve())),
        "case_ids": case_ids,
        "bindings": bindings,
        "config": config,
        "prompt_sha256": sha256_file(prompt_path),
        "schema_sha256": stable_json_sha256(output_schema()),
        "implementation_sha256": {
            name: sha256_file(Path(__file__).with_name(name))
            for name in (
                "target_generation.py",
                "judge_packets.py",
                "evidence_only.py",
                "judge_inspect.py",
                "artifact_io.py",
            )
        },
        "uv_lock_sha256": sha256_file(REPO / "uv.lock"),
        "repeat": repeat,
        "attempts_per_case": 1,
        "total_reserved_cost_usd": (
            config["max_count_calls"] * config["count_cost_allowance_usd"]
            + config["max_generation_calls"]
            * (
                config["max_input_tokens"] * config["reserve_input_per_million"]
                + config["max_output_tokens"] * config["reserve_output_per_million"]
            )
            / 1_000_000
        ),
    }
    if identity["total_reserved_cost_usd"] > config["max_spend_usd"]:
        raise ValueError("Predeclared run liability exceeds spending ceiling")
    if (output / "completion.json").exists():
        if json.loads((output / "completion.json").read_text()) != artifact_inventory(
            output, {"completion.json"}
        ):
            raise ValueError("Run inventory changed")
    if output.exists() and not (output / "manifest.json").exists() and any(output.iterdir()):
        raise ValueError("Output namespace is not empty")
    save(output / "manifest.json", identity)
    publish_bytes_no_clobber(output / "prompt.md", prompt.encode())
    save(output / "output_schema.json", output_schema())
    results = []
    start_path = output / "started.json"
    if not start_path.exists():
        save(start_path, {"started_epoch_seconds": time.time()})
    started = json.loads(start_path.read_text())["started_epoch_seconds"]
    deadline = time.monotonic() + max(0, started + config["max_elapsed_seconds"] - time.time())
    stopped = False
    for record in records:
        directory = output / record["case_id"]
        if directory.exists():
            seal = directory / "completion.json"
            if not seal.exists():
                save(
                    output / "interrupted.json",
                    {
                        "run_id": identity["run_id"],
                        "case_ids": case_ids,
                        "case_status": {
                            key: (
                                "unknown_interrupted"
                                if key == record["case_id"]
                                else "saved_or_not_dispatched"
                            )
                            for key in case_ids
                        },
                        "redispatch_permitted": False,
                    },
                )
                raise ValueError(f"Interrupted attempt; no automatic redispatch: {directory}")
            if json.loads(seal.read_text()) != artifact_inventory(directory, {"completion.json"}):
                raise ValueError("Attempt inventory changed")
            saved = json.loads((directory / "result.json").read_text())
            results.append(saved)
            stopped = stopped or (saved["status"] == "failed" and not saved["generation_calls"])
            continue
        directory.mkdir(exist_ok=False)
        save(directory / "packet.json", record)
        if stopped:
            result = {
                "case_id": record["case_id"],
                "status": "not_dispatched",
                "attempt": 1,
                "repeat": repeat,
                "reason": "Stopped after provider/context/integrity preflight failure",
                "count_calls": 0,
                "generation_calls": 0,
                "run_id": identity["run_id"],
            }
            save(directory / "result.json", result)
            save(directory / "completion.json", artifact_inventory(directory, {"completion.json"}))
        else:
            result = await generate_one(record, directory, config, prompt, deadline, repeat=repeat)
        stopped = stopped or (result["status"] == "failed" and not result["generation_calls"])
        results.append(result)
    summary = {
        "case_ids": case_ids,
        "results": results,
        "generation_calls": sum(r["generation_calls"] for r in results),
        "count_calls": sum(r["count_calls"] for r in results),
        "valid_candidates": sum(r["status"] == "valid" for r in results),
    }
    save(output / "summary.json", summary)
    save(output / "completion.json", artifact_inventory(output, {"completion.json"}))
    return summary


def main() -> None:
    """Expose fixed-panel runs with explicit prompt, configuration and repeat identity."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--prompt", type=Path, default=PROMPT)
    parser.add_argument(
        "--panel", choices=("initial_three", "expanded_six"), default="initial_three"
    )
    parser.add_argument("--repeat", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    root = os.environ.get("ER_COMMONS_DATA_ROOT")
    if not root:
        parser.error("ER_COMMONS_DATA_ROOT must be set")
    logging.basicConfig(level=logging.INFO)
    summary = asyncio.run(
        run(
            Path(root),
            args.output,
            config_path=args.config,
            prompt_path=args.prompt,
            panel=args.panel,
            repeat=args.repeat,
        )
    )
    logging.info("task11b_complete %s", json.dumps(summary))


if __name__ == "__main__":
    main()
