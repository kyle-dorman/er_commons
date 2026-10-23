"""Completion-preserving Task15Y execution with a fully reserved round budget."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

from er_commons import required_support_coverage as core
from er_commons.artifact_io import sha256_file, stable_json_sha256

REPO = Path(__file__).resolve().parents[2]
CASES = {"C014", "C017", "C019", "C037", "C041", "C056"}

ALL19_CASES = CASES | {
    "C001",
    "C006",
    "C007",
    "C008",
    "C027",
    "C028",
    "C029",
    "C036",
    "C042",
    "C045",
    "C050",
    "C051",
    "C054",
}
CODE = {
    "src/er_commons/required_support_coverage.py",
    "src/er_commons/required_support_coverage_inspect.py",
    "src/er_commons/required_support_coverage_run.py",
    "src/er_commons/judge_inspect.py",
    "configs/judge_models_v1.json",
    "docs/prompts/task15y_required_support_coverage_v1.txt",
    "uv.lock",
}
LOGGER = logging.getLogger(__name__)
REPETITIONS = 3
ATTEMPTS_PER_REPETITION = 3
MAX_WIRE_ATTEMPTS_PER_SAMPLE = REPETITIONS * ATTEMPTS_PER_REPETITION
MAX_OUTPUT_TOKENS = 4096
REQUEST_ENVELOPE_BYTES = 4096
CONCURRENCY = 16


def save(path: Path, value: Any) -> None:
    """Create and durably flush a receipt; an existing receipt is never overwritten."""
    with path.open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def read(path: Path) -> Any:
    """Load one explicitly named local JSON artifact."""
    return json.loads(path.read_text())


def input_byte_bound(packet: dict[str, Any]) -> int:
    """Bound one serialized request with fixed room for provider envelope fields."""
    return (
        len(core.system_prompt().encode())
        + len(json.dumps(core.output_json_schema(), ensure_ascii=False).encode())
        + len(json.dumps(packet, ensure_ascii=False).encode())
        + REQUEST_ENVELOPE_BYTES
    )


def sealed_inventory(root: Path, seal: dict[str, Any], label: str) -> dict[str, str]:
    """Verify every sealed file and reject additions before trusting its provenance."""
    inventory = {}
    for entry in seal["files"]:
        path = root / entry["path"]
        if (
            not path.resolve().is_relative_to(root.resolve())
            or path.is_symlink()
            or path.stat().st_size != entry["byte_size"]
            or sha256_file(path) != entry["sha256"]
        ):
            raise ValueError(f"{label} inventory differs")
        inventory[entry["path"]] = entry["sha256"]
    actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    if actual != set(inventory) | {"completion.json"}:
        raise ValueError(f"{label} contains unsealed files")
    return inventory


def budget_bound(samples: list[dict[str, Any]], pricing: dict[str, Any]) -> Decimal:
    """Reserve all three repetitions and three attempts using byte-token upper bounds."""
    rates = [Decimal(str(pricing[key])) for key in ("input_per_million", "output_per_million")]
    if (
        any(not rate.is_finite() or rate <= 0 for rate in rates)
        or rates[0] < Decimal(".125")
        or rates[1] < Decimal(".5")
    ):
        raise ValueError("Invalid reservation pricing")
    inputs = sum(input_byte_bound(sample["packet"]) for sample in samples)
    return (
        (Decimal(inputs) * rates[0] + Decimal(len(samples) * MAX_OUTPUT_TOKENS) * rates[1])
        * MAX_WIRE_ATTEMPTS_PER_SAMPLE
        / 1_000_000
    )


def continuation_accounting(
    root: Path, manifest: dict[str, Any], samples: list[dict[str, Any]], bound: Decimal
) -> dict[str, Any]:
    """Verify the sealed failed ancestor and carry sent liabilities into its sole successor."""
    link = manifest.get("continuation_of")
    if link is None:
        return {}
    ancestor = Path(link["execution_root"])
    if ancestor.resolve() != root.resolve().parent / "round1" or root.name != "round1_continue_v1":
        raise ValueError("Continuation must be the named sibling of the original Round1")
    seal_path = ancestor / "completion.json"
    if sha256_file(seal_path) != link["completion_sha256"]:
        raise ValueError("Ancestor completion differs")
    seal = read(seal_path)
    if seal.get("status") != "sealed_stopped_operational_failure_not_qualification":
        raise ValueError("Ancestor is not a sealed stopped attempt")
    inventory = sealed_inventory(ancestor, seal, "Ancestor")
    previous = read(ancestor / "manifest.json")
    if previous["execution_root"] != str(ancestor.resolve()):
        raise ValueError("Ancestor execution root differs")
    for name in (
        "samples.jsonl",
        "expected_labels.json",
        "checkpoint_ids.json",
        "system_prompt.txt",
        "input_schema.json",
        "output_schema.json",
        "reference_bindings.json",
        "authored_variants.jsonl",
        "independent_review.json",
    ):
        if manifest["files"].get(name) != inventory.get(name):
            raise ValueError(f"Continuation changed semantic input: {name}")
    for field in (
        "prompt_sha256",
        "output_schema_sha256",
        "reference_completion_sha256",
        "pricing",
    ):
        if manifest[field] != previous[field]:
            raise ValueError(f"Continuation changed frozen contract: {field}")
    for name, digest in previous["code_sha256"].items():
        if name != "src/er_commons/required_support_coverage_run.py":
            if manifest["code_sha256"].get(name) != digest:
                raise ValueError(f"Continuation changed semantic code: {name}")
    claim = read(ancestor / "paid_run_claim.json")
    if Decimal(claim["reserved_usd"]) != bound or claim["cap_usd"] != "10":
        raise ValueError("Original budget reservation differs")
    rows = read(ancestor / "checkpoint/results.json")
    if any(row.get("valid") or row.get("covered") is not None for row in rows):
        raise ValueError("Continuation cannot replace semantic judgments")
    counts: Counter[str] = Counter()
    lookup = {stable_json_sha256(s["packet"]): s for s in samples}
    for name in inventory:
        if name.startswith("checkpoint/wire/request_") and name.endswith(".json"):
            body = read(ancestor / name)
            key = stable_json_sha256(json.loads(body["input"][1]["content"][0]["text"]))
            if key not in lookup or body.get("prompt_cache_retention") != "in_memory":
                raise ValueError("Ancestor wire identity or cache failure differs")
            counts[key] += 1
    status = read(ancestor / "checkpoint/status.json")
    if sum(counts.values()) != status["wire_attempts"] or not counts:
        raise ValueError("Ancestor attempt accounting differs")
    allowed = Counter(stable_json_sha256(s["packet"]) for s in samples)
    if any(count > 1 or allowed[key] != 1 for key, count in counts.items()):
        raise ValueError("Continuation requires at most one prior attempt per unique payload")
    retained = sum(
        (
            budget_bound([lookup[key]], manifest["pricing"]) / MAX_WIRE_ATTEMPTS_PER_SAMPLE * count
            for key, count in counts.items()
        ),
        Decimal(0),
    )
    return {
        "continuation_of": link,
        "prior_attempt_counts": dict(counts),
        "prior_wire_attempts": sum(counts.values()),
        "prior_reserved_usd": str(retained),
        "released_unsent_reservation_usd": str(bound - retained),
        "remaining_wire_attempts": len(samples) * MAX_WIRE_ATTEMPTS_PER_SAMPLE
        - sum(counts.values()),
        "retained_liability_policy": (
            "Original full reserve includes prior sent bounds and remaining attempts; not additive"
        ),
        "checkpoint_transport_retries": 1,
    }


def all19_binding(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Bind the sole approved expansion to exact reviewed bytes and a shared claim."""
    from dotenv import dotenv_values

    pointer_path = REPO / "docs/specs/task15y_all19_preparation_result.json"
    pointer = read(pointer_path)
    expected_seal = "bc1765e7881c4cab97253ec10aa2d4fa2efb0129929e9fc1c764c3635af9fc74"
    data_root = os.environ.get("ER_COMMONS_DATA_ROOT") or dotenv_values(REPO / ".env").get(
        "ER_COMMONS_DATA_ROOT"
    )
    if not data_root:
        raise ValueError("Explicit artifact root required")
    prepared = (Path(data_root) / pointer["artifact_root_relative"]).resolve()
    if (
        pointer["completion"]["sha256"] != expected_seal
        or manifest.get("preparation_pointer_sha256") != sha256_file(pointer_path)
        or manifest.get("prepared_inputs_root") != str(prepared)
        or root.resolve() != prepared.with_name(prepared.name + "_round1")
        or "continuation_of" in manifest
    ):
        raise ValueError("All19 preparation identity or sole execution root differs")
    seal_path = prepared / "completion.json"
    if sha256_file(seal_path) != expected_seal:
        raise ValueError("All19 preparation seal differs")
    seal = read(seal_path)
    inventory = sealed_inventory(prepared, seal, "All19 preparation")
    for name in (
        "samples.jsonl",
        "expected_labels.json",
        "checkpoint_ids.json",
        "system_prompt.txt",
        "input_schema.json",
        "output_schema.json",
    ):
        if manifest["files"].get(name) != inventory.get("suite/" + name):
            raise ValueError(f"All19 changed approved input: {name}")
    source = read(prepared / "manifest.json")
    if (
        manifest["reference_completion_sha256"] != source["reference_completion_sha256"]
        or sha256_file(REPO / "docs/prompts/task15y_required_support_coverage_v1.txt")
        != source["prompt_sha256"]
        or (root / "system_prompt.txt").read_text() != core.system_prompt()
        or read(root / "output_schema.json") != core.output_json_schema()
    ):
        raise ValueError("All19 semantic contract differs")
    return {
        "execution_mode": "all19",
        "prepared_completion_sha256": expected_seal,
        "shared_claim_path": str(prepared.with_name(prepared.name + "_paid_run_claim.json")),
    }


def shared_all19_claim(root: Path, reservation: dict[str, Any], *, create: bool) -> None:
    """Reserve exactly one paid all19 namespace, outside the immutable preparation."""
    if reservation.get("execution_mode") != "all19":
        return
    path = Path(reservation["shared_claim_path"])
    claim = {
        "execution_root": str(root.resolve()),
        "manifest_sha256": reservation["manifest_sha256"],
        "prepared_completion_sha256": reservation["prepared_completion_sha256"],
        "reserved_usd": reservation["reserved_usd"],
        "cap_usd": reservation["cap_usd"],
    }
    if create:
        save(path, claim)
    elif read(path) != claim:
        raise ValueError("All19 shared paid claim differs")


def validate_population(
    samples: list[dict[str, Any]],
    labels: dict[str, bool],
    checkpoints: list[str],
    *,
    is_all19: bool,
) -> None:
    """Require the approved population and a checkpoint spanning its required points."""
    checkpoint_count = 84 if is_all19 else 20
    ids = [s["sample_id"] for s in samples]
    if (
        not (len(ids) == 585 if is_all19 else 20 <= len(ids) <= 180)
        or len(set(ids)) != len(ids)
        or set(ids) != set(labels)
        or any(type(value) is not bool for value in labels.values())
        or {s["case_id"] for s in samples} != (ALL19_CASES if is_all19 else CASES)
        or len(checkpoints) != checkpoint_count
        or len(set(checkpoints)) != checkpoint_count
        or not set(checkpoints) <= set(ids)
    ):
        raise ValueError("Coverage population, labels or checkpoint differs")
    for sample in samples:
        core.validate_input(sample["packet"])
    points = {(s["case_id"], s["packet"]["required_reference_point"]["point_id"]) for s in samples}
    checkpoint_samples = [s for s in samples if s["sample_id"] in checkpoints]
    if (
        len(points) != (42 if is_all19 else 10)
        or {
            (s["case_id"], s["packet"]["required_reference_point"]["point_id"])
            for s in checkpoint_samples
        }
        != points
        or {labels[s["sample_id"]] for s in checkpoint_samples} != {True, False}
    ):
        raise ValueError("Checkpoint must span all required points and both labels")
    if is_all19:
        for case_id, point_id in points:
            point_labels = [
                labels[s["sample_id"]]
                for s in checkpoint_samples
                if s["case_id"] == case_id
                and s["packet"]["required_reference_point"]["point_id"] == point_id
            ]
            if sorted(point_labels) != [False, True]:
                raise ValueError("All19 checkpoint needs both labels for each point")


def prepare(root: Path) -> tuple[list[dict[str, Any]], dict[str, bool], list[str], dict[str, Any]]:
    """Verify frozen authoring, code and settings before construction of any provider."""
    from er_commons import judge_inspect

    if judge_inspect.profile("openai_generation").model != "gpt-6-luna":
        raise ValueError("Native coverage model changed")
    manifest = read(root / "manifest.json")
    if manifest.get("execution_root") != str(root.resolve()):
        raise ValueError("Frozen execution root differs; copied budgets cannot dispatch")
    required = {"samples.jsonl", "expected_labels.json", "checkpoint_ids.json"}
    if not required <= manifest["files"].keys() or not CODE <= manifest["code_sha256"].keys():
        raise ValueError("Missing required artifact or code binding")
    for name, digest in manifest["files"].items():
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
            raise ValueError("Unsafe artifact path")
        if sha256_file(path) != digest:
            raise ValueError(f"Frozen artifact differs: {name}")
    for name, digest in manifest["code_sha256"].items():
        path = REPO / name
        if not path.resolve().is_relative_to(REPO) or sha256_file(path) != digest:
            raise ValueError(f"Frozen code differs: {name}")
    if (
        manifest["prompt_sha256"] != stable_json_sha256(core.system_prompt())
        or manifest["output_schema_sha256"] != stable_json_sha256(core.output_json_schema())
        or manifest.get("review_approved") is not True
        or len(manifest.get("reference_completion_sha256", "")) != 64
    ):
        raise ValueError("Contract or independent review binding missing")
    samples = [json.loads(line) for line in (root / "samples.jsonl").read_text().splitlines()]
    labels = read(root / "expected_labels.json")
    checkpoints = read(root / "checkpoint_ids.json")
    mode = manifest.get("execution_mode", "pilot")
    if mode not in {"pilot", "all19"}:
        raise ValueError("Unknown coverage execution mode")
    expansion = all19_binding(root, manifest) if mode == "all19" else {}
    is_all19 = mode == "all19"
    validate_population(samples, labels, checkpoints, is_all19=is_all19)
    pricing = manifest["pricing"]
    if is_all19 and (
        Decimal(str(pricing["input_per_million"])) != Decimal(".25")
        or Decimal(str(pricing["output_per_million"])) != Decimal(".5")
    ):
        raise ValueError("All19 approved reservation rates differ")
    if pricing.get("verified_on") != "2026-10-23" or not pricing.get("source", "").startswith(
        "https://developers.openai.com/"
    ):
        raise ValueError("Verified current pricing basis required")
    bound = budget_bound(samples, pricing)
    cap = "30" if is_all19 else "10"
    if bound > Decimal(cap):
        raise ValueError(f"Whole-round reservation exceeds ${cap}: {bound}")
    if is_all19 and bound != Decimal("24.97518"):
        raise ValueError("All19 approved reservation differs")
    return (
        samples,
        labels,
        checkpoints,
        {
            "manifest_sha256": sha256_file(root / "manifest.json"),
            "reserved_usd": str(bound),
            "cap_usd": cap,
            **expansion,
            "slots": len(samples) * REPETITIONS,
            "maximum_wire_attempts": len(samples) * MAX_WIRE_ATTEMPTS_PER_SAMPLE,
            "repetitions": REPETITIONS,
            "transport_retries": ATTEMPTS_PER_REPETITION - 1,
            "concurrency": CONCURRENCY,
            "retained_liability_policy": "Full round reserve retained; uncertain charges included",
            **continuation_accounting(root, manifest, samples, bound),
        },
    )


class WireGate:
    """Validate actual native requests and durably count all wire attempts before send."""

    def __init__(
        self,
        root: Path,
        samples: list[dict[str, Any]],
        schema: dict[str, Any],
        prior_counts: dict[str, int] | None = None,
    ) -> None:
        """Bind only the phase's allowed payloads, schema, and bounded attempt inventory."""
        self.root = root
        self.allowed = Counter(stable_json_sha256(s["packet"]) for s in samples)
        self.counts: Counter[str] = Counter(
            {key: value for key, value in (prior_counts or {}).items() if key in self.allowed}
        )
        self.schema = schema
        self.stopped: str | None = None
        self.total = 0
        self.rate_limits = 0
        self.server_errors = 0
        self.input_bounds = {
            stable_json_sha256(item["packet"]): input_byte_bound(item["packet"]) for item in samples
        }

    async def request(self, request: Any) -> None:
        """Reject counters, drift, forbidden extras and excess attempts before the wire."""
        if self.stopped:
            raise ValueError(self.stopped)
        try:
            if str(request.url) != "https://api.openai.com/v1/responses":
                raise ValueError("Only the native Responses generation endpoint is authorized")
            body = json.loads(await request.aread())
            messages = body.get("input", [])
            if len(messages) != 2 or [m.get("role") for m in messages] != ["developer", "user"]:
                raise ValueError("Unexpected model-visible messages")
            texts = []
            for message in messages:
                content = message.get("content")
                if not isinstance(content, list) or len(content) != 1:
                    raise ValueError("Unexpected message content")
                if content[0].get("type") != "input_text":
                    raise ValueError("Nontext message content")
                texts.append(content[0]["text"])
            payload = json.loads(texts[1])
            key = stable_json_sha256(payload)
            if texts[0] != core.system_prompt() or key not in self.allowed:
                raise ValueError("Prompt or candidate payload differs")
            if (
                body.get("model") != "gpt-6-luna"
                or body.get("max_output_tokens") != MAX_OUTPUT_TOKENS
                or body.get("reasoning", {}).get("effort") != "medium"
                or body.get("store") is not False
                or body.get("stream", False)
                or body.get("service_tier") != "default"
                or body.get("prompt_cache_retention") != "24h"
                or body.get("text", {}).get("format", {}).get("schema") != self.schema
                or body.get("truncation") != "disabled"
                or any(
                    k in body
                    for k in (
                        "tools",
                        "instructions",
                        "previous_response_id",
                        "temperature",
                        "top_p",
                    )
                )
            ):
                raise ValueError("Native controls or schema differ")
            if len(json.dumps(body, ensure_ascii=False).encode()) > self.input_bounds[key]:
                raise ValueError("Actual request exceeds reserved input byte bound")
            if self.counts[key] >= self.allowed[key] * MAX_WIRE_ATTEMPTS_PER_SAMPLE:
                raise ValueError("Transport attempt allowance exhausted")
            self.counts[key] += 1
            self.total += 1
            save(self.root / f"request_{self.total:04d}.json", body)
        except Exception as error:
            self.stopped = str(error)
            raise

    async def response(self, response: Any) -> None:
        """Stop new sends on fatal provider errors or rate limits pending review."""
        if response.status_code >= 500:
            self.server_errors += 1
            if self.server_errors >= 2:
                self.stopped = "Repeated provider server failures"
        if response.is_success:
            try:
                await response.aread()
                body = response.json()
                usage = body.get("usage", {})
                incoming, outgoing = usage.get("input_tokens"), usage.get("output_tokens")
                if (
                    body.get("model") != "gpt-6-luna"
                    or type(incoming) is not int
                    or type(outgoing) is not int
                    or not 0 < incoming <= max(self.input_bounds.values())
                    or not 0 <= outgoing <= MAX_OUTPUT_TOKENS
                ):
                    self.stopped = "Unverified returned model or usage exceeds reservation"
            except (ValueError, TypeError, AttributeError):
                self.stopped = "Malformed successful provider response; accounting uncertain"
        if response.status_code in (400, 401, 403, 404):
            self.stopped = f"Fatal provider HTTP {response.status_code}"
        if response.status_code == 429:
            self.rate_limits += 1
            # Fail closed rather than let retries perpetuate a saturated connection pool.
            self.stopped = "Provider rate limit; lower concurrency requires a reviewed continuation"


def effective_transport_retries(reservation: dict[str, Any], phase: str) -> int:
    """Leave one prior attempt per checkpoint slot within the original three-attempt cap."""
    return (
        1
        if "continuation_of" in reservation and phase == "checkpoint"
        else ATTEMPTS_PER_REPETITION - 1
    )


def authorize_phase(root: Path, phase: str, reservation: dict[str, Any]) -> None:
    """Create the sole paid claim or verify it and the checkpoint before continuation."""
    if phase == "checkpoint":
        shared_all19_claim(root, reservation, create=True)
        if "continuation_of" in reservation:
            save(
                root.parent / "round1_successor_claim.json",
                {
                    "continuation_of": reservation["continuation_of"],
                    "successor_root": str(root.resolve()),
                    "successor_manifest_sha256": reservation["manifest_sha256"],
                },
            )
        save(root / "paid_run_claim.json", reservation)
    elif phase == "remainder":
        shared_all19_claim(root, reservation, create=False)
        if "continuation_of" in reservation:
            claim = read(root.parent / "round1_successor_claim.json")
            if claim != {
                "continuation_of": reservation["continuation_of"],
                "successor_root": str(root.resolve()),
                "successor_manifest_sha256": reservation["manifest_sha256"],
            }:
                raise ValueError("Continuation successor claim differs")
        if read(root / "paid_run_claim.json") != reservation:
            raise ValueError("Paid claim differs; no fresh budget namespace permitted")
        review = read(root / "checkpoint_review.json")
        if review.get("approved") is not True or review.get(
            "checkpoint_results_sha256"
        ) != sha256_file(root / "checkpoint/results.json"):
            raise ValueError("Explicit checkpoint review required")
        if reservation.get("execution_mode") == "all19":
            status = read(root / "checkpoint/status.json")
            rows = read(root / "checkpoint/results.json")
            if (
                review.get("checkpoint_status_sha256")
                != sha256_file(root / "checkpoint/status.json")
                or status.get("stop_reason") is not None
                or len(rows) != 252
                or sum(row.get("valid") is not True for row in rows) >= 2
                or review.get("no_systematic_rule_failure") is not True
            ):
                raise ValueError("All19 checkpoint stop or review gate failed")
    else:
        raise ValueError("Unknown coverage phase")


def judgment_rows(
    logs: list[Any], samples: list[dict[str, Any]], labels: dict[str, bool]
) -> list[dict[str, Any]]:
    """Keep every planned repetition, representing missing/invalid results without labels."""
    observed: dict[tuple[str, int], dict[str, Any]] = {}
    for log_index, log in enumerate(logs):
        for sample in log.samples or []:
            score = next(iter((sample.scores or {}).values()), None)
            metadata = (score.metadata or {}) if score else {}
            valid = metadata.get("status") == "evaluated" and sample.error is None
            key = (str(sample.id), sample.epoch)
            if key in observed:
                raise ValueError("Duplicate sample repetition in native logs")
            observed[key] = {
                "sample_id": sample.id,
                "epoch": sample.epoch,
                "expected": labels[str(sample.id)],
                "valid": valid,
                "status": "unavailable" if sample.error else metadata.get("status", "unavailable"),
                "covered": metadata.get("covered") if valid else None,
                "result": metadata.get("result") if valid else None,
                "error": sample.error.model_dump(mode="json")
                if sample.error
                else metadata.get("error"),
                "score": score.model_dump(mode="json") if score else None,
                "usage": {
                    name: value.model_dump(mode="json")
                    for name, value in sample.model_usage.items()
                },
                "native_log": {
                    "directory": "logs",
                    "log_index": log_index,
                    "sample_id": sample.id,
                    "epoch": sample.epoch,
                },
            }
    rows = []
    for item in samples:
        for epoch in range(1, REPETITIONS + 1):
            rows.append(
                observed.get(
                    (item["sample_id"], epoch),
                    {
                        "sample_id": item["sample_id"],
                        "epoch": epoch,
                        "expected": labels[item["sample_id"]],
                        "valid": False,
                        "status": "unavailable",
                        "covered": None,
                        "result": None,
                        "error": "No native result for planned slot",
                        "usage": None,
                        "native_log": None,
                    },
                )
            )
    return rows


async def execute(root: Path, phase: str) -> None:
    """Run one create-only phase; full reservation survives partial and failed execution."""
    from dotenv import load_dotenv
    from inspect_ai import eval_async
    from inspect_ai.util._json import json_schema_dump

    from er_commons import required_support_coverage_inspect as native

    samples, labels, checkpoints, reservation = prepare(root)
    authorize_phase(root, phase, reservation)
    subset = [s for s in samples if (s["sample_id"] in checkpoints) == (phase == "checkpoint")]
    directory = root / phase
    directory.mkdir()
    save(directory / "dispatch_claim.json", reservation | {"phase": phase, "variants": len(subset)})
    if not subset:
        save(directory / "results.json", [])
        return
    load_dotenv(REPO / ".env")
    task = native.build_task(
        "openai_generation",
        subset,
        {s["sample_id"]: labels[s["sample_id"]] for s in subset},
        epochs=REPETITIONS,
    )
    assert task.model is not None and task.config.response_schema is not None
    for frozen_config in (task.config, task.model.config):
        if (
            frozen_config.max_tokens != MAX_OUTPUT_TOKENS
            or frozen_config.reasoning_effort != "medium"
            or frozen_config.max_retries != ATTEMPTS_PER_REPETITION - 1
            or frozen_config.max_connections != CONCURRENCY
            or frozen_config.timeout != 120
            or frozen_config.attempt_timeout != 45
            or frozen_config.cache is not False
            or frozen_config.adaptive_connections is not False
        ):
            raise ValueError("Frozen native execution settings differ")
    if task.time_limit != 150:
        raise ValueError("Frozen sample timeout differs")
    for config in (task.config, task.model.config):
        config.max_retries = effective_transport_retries(reservation, phase)
        config.extra_body = {
            **(config.extra_body or {}),
            "service_tier": "default",
            "prompt_cache_retention": "24h",
        }
    api: Any = task.model.api
    api.streaming = False
    client = api.client
    client.max_retries = 0
    schema = json_schema_dump(task.config.response_schema.json_schema)
    wire_root = directory / "wire"
    wire_root.mkdir()
    gate = WireGate(wire_root, subset, schema, reservation.get("prior_attempt_counts"))
    client._client.event_hooks["request"].append(gate.request)
    client._client.event_hooks["response"].append(gate.response)
    try:
        logs = await eval_async(
            [task],
            log_dir=str(directory / "logs"),
            max_samples=CONCURRENCY,
            log_format="json",
            log_model_api=True,
            fail_on_error=False,
            retry_on_error=0,
        )
    except Exception as error:
        gate.stopped = gate.stopped or f"Native evaluation failure: {type(error).__name__}: {error}"
        logs = []
    rows = judgment_rows(logs, subset, labels)
    save(directory / "results.json", rows)
    save(
        directory / "status.json",
        {
            "statuses": [log.status for log in logs],
            "wire_attempts": gate.total,
            "stop_reason": gate.stopped,
            "rate_limits": gate.rate_limits,
            "retained_round_liability_usd": reservation["reserved_usd"],
        },
    )
    LOGGER.info("Coverage phase completed: %s; %d judgment records", phase, len(rows))


def main() -> None:
    """Expose explicit preparation or one authorized phase; never auto-start Round 2."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--phase", choices=("checkpoint", "remainder", "prepare"), required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.phase == "prepare":
        LOGGER.info("Verified reservation: %s", prepare(args.root)[3])
    else:
        asyncio.run(execute(args.root, args.phase))


if __name__ == "__main__":
    main()
