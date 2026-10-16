"""Exact counting for the qualified local Qwen runner; never request generation.

The debug-render/tokenize interface is pinned to one measured Ollama build. This
adapter attaches to an already loaded local model and owns no service lifecycle.
The finite model-identity allowlist permits qualification, not an assumed count: every
request still requires the live renderer/tokenizer and before/after identity checks.
"""

from __future__ import annotations

import copy
import hashlib
import shlex
import subprocess
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from er_commons.artifact_io import stable_json_sha256
from er_commons.ollama_request import write_new

MODEL_DIGEST = "cf23721ea6d0c822e492d6eea302074ab8d1ba6540892f4097204dab7064e858"
BINARY_SHA256 = "e2a48452cd0fee2b8cefd8a941607f02b291ed06d43656b3437aa464bf176b84"
RUNNER_SHA256 = "4846b860821f40b2eec564dd8219f02fc13b3034db52b95d9cf6f21f30d38a54"
MODEL_BLOB_SHA256 = "904785a44c461908190278ec082f6ce89317ff7f71559f947970c90c6b42e7dd"
MODEL_NAME = "er09b-qwen-small-48k:v2"
QWEN9B_MODEL_NAME = "er09b-qwen-f16-48k:v1"
QWEN9B_MODEL_DIGEST = "97b30dac070e9ba3f2868b33622ef040b2c6133f00038258fe4a10fd05d3259d"
QWEN9B_MODEL_BLOB_SHA256 = "2c0dc896becdb6a3eb114dc52219aa2dcc3e479fa256e3e8b58f477aabab34ef"
QUALIFIED_MODEL_IDENTITIES = frozenset(
    {
        (MODEL_NAME, MODEL_DIGEST, MODEL_BLOB_SHA256),
        (QWEN9B_MODEL_NAME, QWEN9B_MODEL_DIGEST, QWEN9B_MODEL_BLOB_SHA256),
    }
)
RUNTIME_VERSION = "0.40.2"
CONTEXT = 49152


class CounterIdentityError(ValueError):
    """Exact counting is unavailable because the qualified runtime binding changed."""


@dataclass(frozen=True)
class OllamaCounterConfig:
    """Explicit attachment identity, never inferred from a mutable alias alone."""

    base_url: str
    model: str
    model_digest: str
    runtime_version: str
    server_pid: int
    binary_path: Path
    binary_sha256: str
    runner_path: Path
    runner_sha256: str
    model_blob_path: Path
    model_blob_sha256: str

    def validate(self) -> None:
        """Refuse unsupported builds/models and non-loopback endpoints before any I/O."""
        parsed = urlparse(self.base_url)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
            or parsed.path not in {"", "/", "/v1", "/v1/"}
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise CounterIdentityError("Counter requires an explicit local Ollama root URL")
        if (
            (self.model, self.model_digest, self.model_blob_sha256)
            not in QUALIFIED_MODEL_IDENTITIES
            or self.runtime_version != RUNTIME_VERSION
            or self.binary_sha256 != BINARY_SHA256
            or self.runner_sha256 != RUNNER_SHA256
        ):
            raise CounterIdentityError("This counter supports only the qualified Qwen/Ollama build")
        if type(self.server_pid) is not int or self.server_pid <= 0:
            raise CounterIdentityError("Counter requires the explicit running server PID")
        if not all(
            p.is_absolute() for p in (self.binary_path, self.runner_path, self.model_blob_path)
        ):
            raise CounterIdentityError("Counter asset paths must be absolute")


@dataclass(frozen=True)
class ProcessInfo:
    """Only the process identity fields needed to bind the attached child runner."""

    pid: int
    parent_pid: int
    argv: tuple[str, ...]


def read_processes() -> list[ProcessInfo]:
    """Read process identities without starting, stopping or modifying any service."""
    output = subprocess.check_output(["ps", "-axo", "pid=,ppid=,command="], text=True)
    records = []
    for line in output.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) == 3:
            records.append(ProcessInfo(int(parts[0]), int(parts[1]), tuple(shlex.split(parts[2]))))
    return records


def read_listeners(pid: int) -> list[tuple[str, int]]:
    """Identify this PID's listening sockets without connecting or managing services."""
    output = subprocess.check_output(
        ["lsof", "-nP", "-a", "-p", str(pid), "-iTCP", "-sTCP:LISTEN", "-Fn"], text=True
    )
    sockets = []
    for line in output.splitlines():
        if line.startswith("n"):
            host, port = line[1:].rsplit(":", 1)
            sockets.append((host.strip("[]"), int(port)))
    return sockets


def sha256_file(path: Path) -> str:
    """Hash the actual binary or model bytes, including symlink targets."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _flag(argv: tuple[str, ...], name: str) -> str:
    """Require one unambiguous option/value in a runner command."""
    if argv.count(name) != 1:
        raise CounterIdentityError(f"Runner requires exactly one {name} argument")
    index = argv.index(name)
    if index + 1 == len(argv):
        raise CounterIdentityError(f"Runner argument {name} has no value")
    return argv[index + 1]


class OllamaTokenCounter:
    """Render the complete native request and tokenize with its verified live runner."""

    def __init__(
        self,
        config: OllamaCounterConfig,
        artifact_dir: Path,
        *,
        transport: httpx.BaseTransport | None = None,
        processes: Callable[[], list[ProcessInfo]] = read_processes,
        file_digest: Callable[[Path], str] = sha256_file,
        listeners: Callable[[int], list[tuple[str, int]]] = read_listeners,
    ) -> None:
        """Bind immutable qualification and injectable I/O for invented offline tests."""
        config.validate()
        self.config = config
        self.base_url = config.base_url.rstrip("/").removesuffix("/v1")
        self.last_receipt: Path | None = None
        self.artifact_dir = artifact_dir
        self.transport = transport
        self.processes = processes
        self.file_digest = file_digest
        self.listeners = listeners

    @property
    def model_digest(self) -> str:
        """Supply the explicit model binding required by 09C request preflight."""
        return self.config.model_digest

    def _request(
        self,
        client: httpx.Client,
        base: str,
        route: str,
        directory: Path,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist raw responses before interpreting a narrow read/render/tokenize call."""
        allowed = {"/api/version", "/api/tags", "/api/show", "/api/ps", "/api/chat", "/tokenize"}
        if route not in allowed or (
            route == "/api/chat" and (body is None or body.get("_debug_render_only") is not True)
        ):
            raise CounterIdentityError("Counter permits rendering only, never generation")
        write_new(directory / f"{name}_request.json", {"url": base + route, "body": body})
        response = (
            client.get(base + route) if body is None else client.post(base + route, json=body)
        )
        write_new(
            directory / f"{name}_response.json",
            {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
            },
        )
        response.raise_for_status()
        value = response.json()
        if not isinstance(value, dict):
            raise CounterIdentityError(f"{route} returned a non-object response")
        return value

    def _identity(self, client: httpx.Client, directory: Path, phase: str) -> ProcessInfo:
        """Check assets, parent/child commands and native model identity on both sides."""
        cfg = self.config
        assets = (
            (cfg.binary_path, cfg.binary_sha256),
            (cfg.runner_path, cfg.runner_sha256),
            (cfg.model_blob_path, cfg.model_blob_sha256),
        )
        for path, expected in assets:
            if self.file_digest(path) != expected:
                raise CounterIdentityError(f"Counter asset digest changed: {path}")
        processes = self.processes()
        parents = [p for p in processes if p.pid == cfg.server_pid]
        if len(parents) != 1 or parents[0].argv != (str(cfg.binary_path), "serve"):
            raise CounterIdentityError("Pinned server PID/command is absent or changed")
        children = [
            p
            for p in processes
            if p.parent_pid == cfg.server_pid and p.argv and p.argv[0] == str(cfg.runner_path)
        ]
        if len(children) != 1:
            raise CounterIdentityError("Expected exactly one matching loaded child runner")
        child = children[0]
        if (
            Path(_flag(child.argv, "--model")).resolve() != cfg.model_blob_path.resolve()
            or _flag(child.argv, "--host") != "127.0.0.1"
            or _flag(child.argv, "-c") != str(CONTEXT)
            or _flag(child.argv, "-np") != "1"
            or _flag(child.argv, "--chat-template") != "chatml"
            or "--no-jinja" not in child.argv
            or "--offline" not in child.argv
        ):
            raise CounterIdentityError("Loaded runner model/context/template differs")
        try:
            port = int(_flag(child.argv, "--port"))
        except ValueError as error:
            raise CounterIdentityError("Invalid runner port") from error
        if not 0 < port < 65536:
            raise CounterIdentityError("Invalid runner port")
        server_url = urlparse(self.base_url)
        server_port = server_url.port or 80
        hosts = (
            {server_url.hostname} if server_url.hostname != "localhost" else {"127.0.0.1", "::1"}
        )
        server_sockets = self.listeners(cfg.server_pid)
        runner_sockets = self.listeners(child.pid)
        if not any((host, server_port) in server_sockets for host in hosts):
            raise CounterIdentityError(
                "Native endpoint listener does not belong to pinned server PID"
            )
        if ("127.0.0.1", port) not in runner_sockets:
            raise CounterIdentityError("Tokenize endpoint listener does not belong to runner PID")
        write_new(
            directory / f"{phase}_processes.json",
            {
                "server": asdict(parents[0]),
                "runner": asdict(child),
                "server_listeners": server_sockets,
                "runner_listeners": runner_sockets,
                "assets": [{"path": str(p), "sha256": h} for p, h in assets],
            },
        )
        base = self.base_url
        version = self._request(client, base, "/api/version", directory, f"{phase}_version")
        tags = self._request(client, base, "/api/tags", directory, f"{phase}_tags")
        show = self._request(
            client, base, "/api/show", directory, f"{phase}_show", {"model": cfg.model}
        )
        loaded = self._request(client, base, "/api/ps", directory, f"{phase}_loaded")
        for envelope in (tags, loaded):
            models = envelope.get("models")
            if not isinstance(models, list):
                raise CounterIdentityError("Missing native model inventory")
            matches = [m for m in models if isinstance(m, dict) and m.get("name") == cfg.model]
            if len(matches) != 1 or matches[0].get("digest") != cfg.model_digest:
                raise CounterIdentityError("Live model digest differs from qualified identity")
            if envelope is loaded and matches[0].get("context_length") != CONTEXT:
                raise CounterIdentityError("Loaded model context differs")
        details = show.get("details", {})
        parameters = show.get("parameters", "")
        context_rows = (
            [
                line.split()
                for line in parameters.splitlines()
                if line.strip().startswith("num_ctx ")
            ]
            if isinstance(parameters, str)
            else []
        )
        if (
            version.get("version") != cfg.runtime_version
            or not isinstance(details, dict)
            or details.get("family") != "qwen35"
            or details.get("quantization_level") != "F16"
            or show.get("template") != "{{ .Prompt }}"
            or context_rows != [["num_ctx", str(CONTEXT)]]
        ):
            raise CounterIdentityError("Live runtime/model/template configuration differs")
        return child

    def _validate_request(self, request: dict[str, Any]) -> None:
        """Allow only the qualified text-only native request surface, without extra controls."""
        expected_keys = {
            "model",
            "messages",
            "format",
            "think",
            "stream",
            "truncate",
            "shift",
            "keep_alive",
            "options",
        }
        if set(request) != expected_keys or request.get("model") != self.config.model:
            raise CounterIdentityError("Request model or native field set is not qualified")
        if any(request.get(key) is not False for key in ("think", "stream", "truncate", "shift")):
            raise CounterIdentityError(
                "Request must disable thinking, streaming, truncation and shift"
            )
        options = request.get("options")
        option_keys = {"num_ctx", "num_predict", "temperature", "seed"}
        if not isinstance(options, dict) or set(options) != option_keys:
            raise CounterIdentityError("Request settings differ from qualified 09C allocation")
        if any(type(options[key]) is not int for key in option_keys):
            raise CounterIdentityError(
                "Native numeric options must use the qualified integer types"
            )
        if (
            options["num_ctx"] != CONTEXT
            or options["num_predict"] not in {1500, 3000}
            or options["temperature"] != 0
            or options["seed"] != 42
        ):
            raise CounterIdentityError("Request settings differ from qualified 09C allocation")
        messages = request.get("messages")
        if not isinstance(messages, list) or len(messages) != 2:
            raise CounterIdentityError("Require exactly system and user text messages")
        for message, role in zip(messages, ("system", "user"), strict=True):
            if (
                not isinstance(message, dict)
                or set(message) != {"role", "content"}
                or message["role"] != role
                or not isinstance(message["content"], str)
            ):
                raise CounterIdentityError("Only plain system/user text messages are qualified")
        if not isinstance(request.get("format"), dict) or request.get("keep_alive") != "5m":
            raise CounterIdentityError(
                "Require the qualified structured-output/keep-alive settings"
            )

    def __call__(self, request: dict[str, Any]) -> int:
        """Return an exact verified count or fail closed with immutable raw receipts."""
        self.last_receipt = None
        self._validate_request(request)
        directory = self.artifact_dir / f"{stable_json_sha256(request)}-{uuid.uuid4().hex}"
        directory.mkdir(parents=True, exist_ok=False)
        write_new(directory / "native_request.json", request)
        try:
            with httpx.Client(timeout=180, trust_env=False, transport=self.transport) as client:
                before = self._identity(client, directory, "before")
                rendered_request = copy.deepcopy(request)
                rendered_request["_debug_render_only"] = True
                rendered = self._request(
                    client,
                    self.base_url,
                    "/api/chat",
                    directory,
                    "render",
                    rendered_request,
                )
                debug = rendered.get("_debug_info")
                message = rendered.get("message", {})
                if (
                    not isinstance(debug, dict)
                    or not isinstance(debug.get("rendered_template"), str)
                    or (
                        "image_count" in debug
                        and (type(debug["image_count"]) is not int or debug["image_count"] != 0)
                    )
                    or rendered.get("eval_count")
                    or not isinstance(message, dict)
                    or message.get("content")
                ):
                    raise CounterIdentityError(
                        "Render-only response was absent or generated content"
                    )
                prompt = debug["rendered_template"]
                if not prompt.startswith("<|im_start|>"):
                    raise CounterIdentityError("Rendered chat template is not the qualified ChatML")
                runner_base = f"http://127.0.0.1:{_flag(before.argv, '--port')}"
                tokenized = self._request(
                    client,
                    runner_base,
                    "/tokenize",
                    directory,
                    "tokens",
                    {"content": prompt, "add_special": True, "parse_special": True},
                )
                tokens = tokenized.get("tokens")
                if (
                    not isinstance(tokens, list)
                    or not tokens
                    or any(type(t) is not int or t < 0 for t in tokens)
                ):
                    raise CounterIdentityError(
                        "Runner did not return a nonempty integer token list"
                    )
                after = self._identity(client, directory, "after")
                if before != after:
                    raise CounterIdentityError("Runner identity changed while counting")
                count = len(tokens)
            write_new(
                directory / "receipt.json",
                {
                    "status": "exact",
                    "request_sha256": stable_json_sha256(request),
                    "model_digest": self.config.model_digest,
                    "input_tokens": count,
                    "rendered_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                    "add_special": True,
                    "parse_special": True,
                    "generation_requested": False,
                    "config": {
                        k: str(v) if isinstance(v, Path) else v
                        for k, v in asdict(self.config).items()
                    },
                },
            )
            self.last_receipt = directory / "receipt.json"
            return count
        except Exception as error:
            write_new(
                directory / "failure.json", {"status": "counter_unavailable", "error": repr(error)}
            )
            raise CounterIdentityError(f"Exact counter unavailable: {error}") from error
