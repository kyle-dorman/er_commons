"""Prepare source-bound Task 08B queues without assigning human decisions."""

import argparse
import html
import json
import logging
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons import group_ranking, group_ranking_v2
from er_commons.group_ranking import checked, digest, encoded, indexed, rows, under

VERSION = "task08b.selection.v2"
PROCESS_REVISION = "task08.selection_gate.v2"
INTAKE_REVISION = "task08b.intake.v2"
# Explicitly qualified predecessor; every other snapshot and rebuilt task still matches.
LEGACY_PREPARATION_SHA256 = "6f1bfad591ba75356b7211a97c9fbc01cbc928596d1301393f01461a7d33b0b4"
PAGE_CONTEXT_REASON = "Complete source page context; adjacent text is not a candidate"
ROOT = Path(__file__).resolve().parents[2]
FORM = ROOT / "configs/label_studio/task08b_selection_v2.xml"
SCHEMA = ROOT / "benchmarks/er_bench/schemas/task08b/v2/input.schema.json"


def _pre(value: Any) -> str:
    """Escape exact source or provenance text without shortening or rewriting it."""
    text = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False)
    return (
        '<pre style="white-space:pre-wrap;overflow-wrap:anywhere">' + html.escape(text) + "</pre>"
    )


def _unit(unit: dict[str, Any]) -> str:
    """Render every source character and its stable identity and physical pages."""
    pages = ", ".join(str(page) for page in unit["source_pages"])
    return (
        f'<article class="source-unit" data-unit-id="{html.escape(unit["unit_id"])}">'
        f"<h3>{html.escape(unit['official_label'])}</h3><p>Volume 4 · PDF pages {pages}</p>"
        + _pre(unit["text"])
        + "</article>"
    )


def _response_html(context: dict[str, Any]) -> str:
    """Display full linked source and footnotes; keep explanatory metadata undisplayed."""
    rendered = "".join(_unit(unit) for unit in context["units"])
    for supplement in context["supplements"]:
        heading = (
            "Source page context"
            if supplement.get("reason") == PAGE_CONTEXT_REASON
            else "Source footnote"
        )
        rendered += (
            f'<section class="source-supplement"><h4>{heading}</h4>'
            + _pre(supplement["text"])
            + "</section>"
        )
    return rendered or "<p>No linked responses in this handoff.</p>"


def _source_page_ids(packet: dict[str, Any]) -> dict[str, set[str]]:
    """Resolve exact page membership from hash-bound source spans, not supplement owners."""
    bindings = indexed(packet["input_bindings"], "path")
    matches = [ref for ref in bindings.values() if Path(ref["path"]).name == "components.json"]
    if len(matches) != 1:
        raise ValueError("Expected one pinned source component index")
    ref = matches[0]
    components = indexed(json.loads(checked(Path(ref["path"]), ref["sha256"])), "role")
    source = components["source_records"]
    path = under(Path(packet["preparation"]["data_root"]), source["path"])
    if bindings.get(str(path)) != {"path": str(path), "sha256": source["sha256"]}:
        raise ValueError("Source records are not bound by the ranking packet")
    spans = indexed(
        [r for r in rows(checked(path, source["sha256"])) if r["record_type"] == "source_span"],
        "span_id",
    )
    return {
        unit["unit_id"]: {
            fragment["page_id"]
            for span_id in unit["span_ids"]
            for fragment in spans[span_id]["fragments"]
        }
        for unit in packet["source_units"]
    }


def build_tasks(
    packet: dict[str, Any],
    proposal: dict[str, Any],
    *,
    input_sha256: str,
    proposal_sha256: str,
    namespace: str,
    recorded_limitations: list[str],
) -> list[dict[str, Any]]:
    """Render the saved order with distinct original, response and advisory records."""
    candidates = indexed(packet["candidates"], "comment_id")
    units = indexed(packet["source_units"], "unit_id")
    has_page_context = any(
        s.get("reason") == PAGE_CONTEXT_REASON for s in packet["source_supplements"]
    )
    source_pages = _source_page_ids(packet) if has_page_context else {}
    tasks = []
    for ranking in proposal["ranking"]:
        candidate = candidates[ranking["comment_id"]]
        cid = candidate["comment_id"]
        response_ids = [uid for uid in candidate["context_unit_ids"] if uid != cid]
        responses = [units[uid] for uid in response_ids]
        response_pages = {page for uid in response_ids for page in source_pages.get(uid, set())}
        supplements = [
            s
            for s in packet["source_supplements"]
            if (
                s["page_id"] in response_pages
                if s.get("reason") == PAGE_CONTEXT_REASON
                else s["unit_id"] in response_ids
            )
        ]
        outcomes = [
            o for o in packet["outcomes"] if o["outcome_id"] in candidate["reference_outcome_ids"]
        ]
        response_context = {"units": responses, "supplements": supplements, "outcomes": outcomes}
        warnings = {
            "candidate_provenance": candidate,
            "recorded_08a_limitations": recorded_limitations,
            "inherited_limitations": packet["limitations"],
        }
        if "concerns" in ranking:
            warnings["ranking_concerns"] = ranking["concerns"]
        response_html = _response_html(response_context)
        data = {
            "form_version": VERSION,
            "process_revision": PROCESS_REVISION,
            "namespace": namespace,
            "group": packet["group"]["group"],
            "rank": ranking["rank"],
            "candidate_count": len(candidates),
            "comment_id": cid,
            "comment_label": candidate["comment_label"],
            "input_sha256": input_sha256,
            "proposal_sha256": proposal_sha256,
            "title": f"{ranking['rank']} / {len(candidates)} · {candidate['comment_label']}",
            "original_comment": units[cid],
            "comment_source_warnings": [
                "Original extracted comment text; physical source pages "
                "and span IDs remain attached."
            ],
            "response_context": response_context,
            "advisory": ranking,
            "source_warnings": warnings,
            "comment_html": _unit(units[cid]),
            "response_html": response_html,
        }
        tasks.append({"data": data})
    validate_tasks(tasks)
    return tasks


def validate_tasks(tasks: list[dict[str, Any]]) -> None:
    """Require a complete ordered blank queue, exact source display, and no predictions."""
    Draft202012Validator(json.loads(SCHEMA.read_bytes())).validate(tasks)
    if not tasks:
        raise ValueError("Empty selection queue")
    indexed([t["data"] for t in tasks], "comment_id")
    first = tasks[0]["data"]
    for position, task in enumerate(tasks, 1):
        data = task["data"]
        if data["rank"] != position or data["candidate_count"] != len(tasks):
            raise ValueError("Queue order or count differs")
        for key in ("group", "namespace", "input_sha256", "proposal_sha256"):
            if data[key] != first[key]:
                raise ValueError("Mixed queue bindings")
        original = data["original_comment"]
        if original["unit_id"] != data["comment_id"] or original["unit_kind"] != "comment":
            raise ValueError("Original comment identity differs")
        if _unit(original) != data["comment_html"]:
            raise ValueError("Original comment display differs")
        context = data["response_context"]
        if any(unit["unit_kind"] == "comment" for unit in context["units"]):
            raise ValueError("Response context includes another comment")
        if _response_html(context) != data["response_html"]:
            raise ValueError("Response display differs from complete source text")


def verify_ranking(ranking_root: Path, result_path: Path, data_root: Path) -> dict[str, Any]:
    """Verify either a historical result or a group in the sealed v2 completion index."""
    result = json.loads(checked(result_path))
    indexed_result = result.get("schema_version") == "task08a.remaining_groups.result.v2"
    if indexed_result:
        if result.get("status") != "complete":
            raise ValueError("Remaining-group preparation is not complete")
        ref = result["artifacts"]["handoff_index"]
        index = json.loads(checked(under(data_root, ref["path"]), ref["sha256"]))
        if index["grouping_sha256"] != result["grouping_sha256"]:
            raise ValueError("Completion index grouping identity differs")
        matches = [
            row
            for row in index["groups"]
            if under(data_root, row["handoff"]["path"]).resolve()
            == (ranking_root / "handoff.json").resolve()
        ]
        if len(matches) != 1:
            raise ValueError("Ranking must identify exactly one indexed handoff")
        result = matches[0]
        if result.get("validation") != "passed" or result.get("state") not in {
            "completed",
            "preserved",
        }:
            raise ValueError("Indexed ranking is not ready")
    for name in ("handoff", "manifest", "completion", "input", "proposal"):
        ref = result[name]
        path = under(data_root, ref["path"])
        if path.resolve() != (ranking_root / f"{name}.json").resolve():
            raise ValueError("Completion record points to a different ranking")
        checked(path, ref["sha256"])
    manifest = json.loads(checked(ranking_root / "manifest.json"))
    version = manifest["schema_version"]
    validators = {
        group_ranking.VERSION: group_ranking.validate,
        group_ranking_v2.VERSION: group_ranking_v2.validate,
    }
    if version not in validators:
        raise ValueError("Unsupported ranking interface")
    handoff = validators[version](ranking_root)
    packet = json.loads(checked(ranking_root / "input.json"))
    labels = {
        c["comment_id"]: c["comment_label"].removeprefix("Comment ") for c in packet["candidates"]
    }
    if indexed_result:
        proposal = json.loads(checked(ranking_root / "proposal.json"))
        expected_mode = (
            "preserved_v1"
            if version == group_ranking.VERSION
            else {"model_ranked": "model_ranking", "deterministic": "deterministic_preparation"}[
                proposal["preparation_mode"]
            ]
        )
        if (
            result["interface_version"] != version
            or result["mode"] != expected_mode
            or result["model"] != proposal["model"]
            or handoff["group"] != result["group"]
            or handoff["candidate_count"] != result["candidate_count"]
        ):
            raise ValueError("Indexed handoff identities differ")
        return {**result, "inventory_id": handoff["inventory_id"]}
    if (
        [labels[cid] for cid in handoff["proposed_order"]] != result["proposed_order"]
        or handoff["inventory_id"] != result["inventory_id"]
        or handoff["group"] != result["group"]
        or handoff["candidate_count"] != result["candidate_count"]
    ):
        raise ValueError("Completion record and handoff identities differ")
    return dict(result)


def prepare(ranking_root: Path, result_path: Path, data_root: Path, output: Path) -> dict[str, Any]:
    """Publish a fresh trusted queue and interface snapshots; never create annotations."""
    result = verify_ranking(ranking_root, result_path, data_root)
    inputs = checked(ranking_root / "input.json")
    proposals = checked(ranking_root / "proposal.json")
    tasks = build_tasks(
        json.loads(inputs),
        json.loads(proposals),
        input_sha256=digest(inputs),
        proposal_sha256=digest(proposals),
        namespace="dataset",
        recorded_limitations=result.get("limitations", []),
    )
    payloads = {
        "tasks.json": encoded(tasks),
        "form.xml": checked(FORM),
        "input.schema.json": checked(SCHEMA),
        "decisions.schema.json": checked(SCHEMA.with_name("decisions.schema.json")),
        "preparation.py": checked(Path(__file__)),
        "exporter.py": checked(Path(__file__).with_name("group_selection_export.py")),
    }
    manifest = {
        "schema_version": VERSION,
        "intake_revision": INTAKE_REVISION,
        "process_revision": PROCESS_REVISION,
        "state": "prepared_awaiting_human_review",
        "ranking_root": str(ranking_root.resolve()),
        "result_path": str(result_path.resolve()),
        "result_sha256": digest(checked(result_path)),
        "data_root": str(data_root.resolve()),
        "group": result["group"],
        "inventory_id": result["inventory_id"],
        "input_sha256": digest(inputs),
        "proposal_sha256": digest(proposals),
        "proposed_order": [t["data"]["comment_id"] for t in tasks],
        "files": {name: digest(value) for name, value in payloads.items()},
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, content in {**payloads, "manifest.json": encoded(manifest)}.items():
        with (output / name).open("xb") as handle:
            handle.write(content)
    return manifest


def load_prepared(directory: Path) -> list[dict[str, Any]]:
    """Rebuild trusted data from verified upstream bytes before accepting an export."""
    manifest = json.loads(checked(directory / "manifest.json"))
    expected_files = {
        "tasks.json",
        "form.xml",
        "input.schema.json",
        "decisions.schema.json",
        "preparation.py",
        "exporter.py",
    }
    if set(manifest["files"]) != expected_files or manifest["schema_version"] != VERSION:
        raise ValueError("Prepared manifest closure or version differs")
    if manifest.get("intake_revision") not in {None, INTAKE_REVISION}:
        raise ValueError("Unsupported selection intake revision")
    for name, sha in manifest["files"].items():
        checked(directory / name, sha)
    for name, source in (
        ("form.xml", FORM),
        ("input.schema.json", SCHEMA),
        ("decisions.schema.json", SCHEMA.with_name("decisions.schema.json")),
        ("preparation.py", Path(__file__)),
        ("exporter.py", Path(__file__).with_name("group_selection_export.py")),
    ):
        saved = checked(directory / name)
        legacy_preparation = (
            name == "preparation.py"
            and "intake_revision" not in manifest
            and digest(saved) == LEGACY_PREPARATION_SHA256
        )
        if saved != checked(source) and not legacy_preparation:
            raise ValueError("Shared interface changed; explicit version review required")
    result_path = Path(manifest["result_path"])
    checked(result_path, manifest["result_sha256"])
    ranking_root = Path(manifest["ranking_root"])
    result = verify_ranking(ranking_root, result_path, Path(manifest["data_root"]))
    tasks = build_tasks(
        json.loads(checked(ranking_root / "input.json")),
        json.loads(checked(ranking_root / "proposal.json")),
        input_sha256=result["input"]["sha256"],
        proposal_sha256=result["proposal"]["sha256"],
        namespace="dataset",
        recorded_limitations=result.get("limitations", []),
    )
    if encoded(tasks) != checked(directory / "tasks.json"):
        raise ValueError("Prepared tasks differ from bound source rebuild")
    return tasks


def main() -> None:
    """Expose preparation and explicitly requested saved-export validation."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    for arg in ("ranking-root", "result", "data-root", "output"):
        prep.add_argument(f"--{arg}", type=Path, required=True)
    export = commands.add_parser("export")
    for arg in ("prepared", "native-export", "output"):
        export.add_argument(f"--{arg}", type=Path, required=True)
    export.add_argument("--project-id", type=int, required=True)
    export.add_argument("--finish-confirmation", type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.command == "prepare":
        prepare(args.ranking_root, args.result, args.data_root, args.output)
    else:
        from er_commons.group_selection_export import normalize_export

        trusted = load_prepared(args.prepared)
        native_bytes = checked(args.native_export)
        result = normalize_export(
            json.loads(native_bytes),
            trusted,
            project_id=args.project_id,
            export_sha256=digest(native_bytes),
            finish_confirmation=(
                json.loads(checked(args.finish_confirmation)) if args.finish_confirmation else None
            ),
        )
        with args.output.open("xb") as handle:
            handle.write(encoded(result))
    logging.info("Task08B %s completed: %s", args.command, args.output)


if __name__ == "__main__":
    main()
