"""Seal advisory v2 orders while reusing the immutable v1 source preparation contract."""

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons import group_ranking as source_adapter
from er_commons import pilot_context_repair
from er_commons.group_ranking import (
    checked,
    digest,
    encoded,
    indexed,
    rows,
    under,
    validate_supplements,
)
from er_commons.pilot_context_repair import refresh_cases
from er_commons.response_inventory.release_storage import inventory_identity, read_container

VERSION = "task08a.ranking.v2"
INPUT_VERSION = source_adapter.VERSION
POLICY = "Advisory order only; at most three use stable IDs without model; no human decisions"
BYPASS_REASON = "ranking not needed—group has at most three candidates"
SCHEMAS = Path(__file__).resolve().parents[2] / "benchmarks/er_bench/schemas/task08a_v2"


def schema_check(value: dict[str, Any], name: str) -> None:
    """Apply strict versioned output schemas, retaining the v1 input contract."""
    directory = source_adapter.SCHEMAS if name in {"input", "source_supplements"} else SCHEMAS
    schema = json.loads((directory / f"{name}.schema.json").read_bytes())
    Draft202012Validator(schema).validate(value)


def prepare(
    data_root: Path,
    inventory_result: Path,
    grouping_directory: Path,
    grouping_sha256: str,
    group: str,
    source_supplements: Path | None = None,
) -> dict[str, Any]:
    """Resolve only the requested group against accepted inventory and planning inputs."""
    bindings: dict[str, dict[str, Any]] = {}

    def read(path: Path, expected: str | None = None) -> bytes:
        """Capture every consumed input for later exact replay."""
        content = checked(path, expected)
        bindings[str(path.resolve())] = {"path": str(path.resolve()), "sha256": digest(content)}
        return content

    result = json.loads(read(inventory_result))
    refs = {}
    for name in (
        "acceptance_pointer",
        "completion",
        "manifest",
        "components",
        "task07_task08_handoff",
        "limitations",
    ):
        ref = result[name]
        content = read(under(data_root, ref["path"]), ref["sha256"])
        if len(content) != ref["size_bytes"]:
            raise ValueError("Pinned inventory size differs")
        refs[name] = json.loads(content)
    release = under(data_root, result["inventory_root"])
    completion, payloads = read_container(release, plan_id=result["plan_id"])
    if inventory_identity(completion) != result["inventory_id"]:
        raise ValueError("Inventory identity differs")
    acceptance = refs["acceptance_pointer"]
    if acceptance["inventory_id"] != result["inventory_id"] or any(
        acceptance[field] != result[name]["sha256"]
        for field, name in (
            ("completion_sha256", "completion"),
            ("manifest_sha256", "manifest"),
            ("handoff_sha256", "task07_task08_handoff"),
        )
    ):
        raise ValueError("Accepted inventory binding differs")
    for dependency in refs["task07_task08_handoff"]["dependencies"]:
        if dependency.get("role") in {"task06h_acceptance", "task06h_handoff"}:
            content = read(under(data_root, dependency["path"]), dependency["sha256"])
            if len(content) != dependency["size_bytes"]:
                raise ValueError("Task06H dependency size differs")
    components = indexed(refs["components"], "role")
    consumed = {}
    for name in ("source_records", "edges", "outcomes"):
        ref = components[name]
        consumed[name] = rows(read(under(data_root, ref["path"]), ref["sha256"]))
    views = rows(payloads["review_views/index.jsonl"])
    groups = json.loads(read(grouping_directory / "groups.json", grouping_sha256))
    manifest = json.loads(read(grouping_directory / "manifest.json"))
    if manifest["files"]["groups.json"] != grouping_sha256:
        raise ValueError("Grouping manifest differs")
    for name, sha in manifest["files"].items():
        read(under(grouping_directory, name), sha)
    all_members = [member for row in groups for member in row["comments"]]
    indexed(all_members, "comment_id")
    matches = [row for row in groups if row["group"] == group]
    if len(matches) != 1:
        raise ValueError("Group must identify exactly one accepted group")
    selected = matches[0]
    if selected["available"] != len(selected["comments"]):
        raise ValueError("Group count differs")
    prior_ref = manifest["input_groups"]
    prior_path = under(data_root, prior_ref["path"])
    read(prior_path, prior_ref["sha256"])
    prior_manifest = json.loads(read(prior_path.parent / "manifest.json"))
    priority_path = Path(prior_manifest["input"])
    if not priority_path.is_absolute():
        priority_path = under(data_root, str(priority_path))
    priority = rows(read(priority_path, prior_manifest["input_sha256"]))
    exclusion_ref = manifest["input_exclusions"]
    exclusions = rows(read(under(data_root, exclusion_ref["path"]), exclusion_ref["sha256"]))
    planning = indexed(priority + exclusions, "comment_id")
    plan_manifest = json.loads(read(priority_path.parent / "manifest.json"))
    category_path = Path(plan_manifest["input_bindings"]["base_categories"])
    if not category_path.is_absolute():
        category_path = under(data_root, str(category_path))
    category_manifest = json.loads(read(category_path.parent / "manifest.json"))
    categories = indexed(
        rows(read(category_path, category_manifest["files"][category_path.name])), "comment_id"
    )
    units = indexed(
        [r for r in consumed["source_records"] if r["record_type"] == "source_unit"], "unit_id"
    )
    edge_index = indexed(consumed["edges"], "edge_id")
    view_index = indexed(views, "root_unit_id")
    seeds = []
    for member in selected["comments"]:
        cid = member["comment_id"]
        if (
            units[cid]["unit_kind"] != "comment"
            or units[cid]["official_label"] != member["comment_label"]
        ):
            raise ValueError("Group source identity differs")
        view = view_index[cid]
        direct = [
            edge_index[e]["target_unit_id"]
            for e in view["edge_ids"]
            if edge_index[e]["relation_type"] == "comment_response"
            and edge_index[e]["source_unit_id"] == cid
        ]
        seeds.append(
            {
                **member,
                "direct_response_ids": direct,
                "context_unit_ids": view["ordered_unit_ids"],
                "relationship_ids": view["edge_ids"],
                "planning_record": planning[cid],
                "category_record": categories[cid],
            }
        )
    cases, context, _ = refresh_cases(
        seeds, consumed["source_records"], consumed["edges"], consumed["outcomes"], views
    )
    for case in cases:
        case.pop("review_state")
        validate_closure(case, consumed["edges"], view_index[case["comment_id"]]["edge_ids"])
    edge_ids = {eid for case in cases for eid in case["relationship_ids"]}
    outcome_ids = {oid for case in cases for oid in case["reference_outcome_ids"]}
    supplements = []
    if source_supplements is not None:
        supplement_record = json.loads(read(source_supplements))
        schema_check(supplement_record, "source_supplements")
        if supplement_record["source_component"] != components["source_records"]:
            raise ValueError("Supplement source component differs")
        supplements = supplement_record["supplements"]
        pages = indexed(
            [r for r in consumed["source_records"] if r["record_type"] == "page"], "page_id"
        )
        validate_supplements(supplements, context, pages)
    pages = indexed(
        [r for r in consumed["source_records"] if r["record_type"] == "page"], "page_id"
    )
    spans = indexed(
        [r for r in consumed["source_records"] if r["record_type"] == "source_span"], "span_id"
    )
    covered_pages: set[str] = set()
    for unit in sorted(context, key=lambda row: row["unit_id"]):
        for span_id in units[unit["unit_id"]]["span_ids"]:
            for fragment in spans[span_id]["fragments"]:
                page_id = fragment["page_id"]
                if page_id in covered_pages:
                    continue
                covered_pages.add(page_id)
                page_text = pages[page_id]["raw_text"]
                if not page_text.strip():
                    raise ValueError("Source context page is empty")
                full_page = {
                    "unit_id": unit["unit_id"],
                    "page_id": page_id,
                    "text_start": 0,
                    "text_end": len(page_text),
                    "text": page_text,
                    "reason": "Complete source page context; adjacent text is not a candidate",
                }
                if not any(
                    all(
                        row[key] == full_page[key]
                        for key in ("unit_id", "page_id", "text_start", "text_end")
                    )
                    for row in supplements
                ):
                    supplements.append(full_page)
    validate_supplements(supplements, context, pages)
    packet = {
        "schema_version": INPUT_VERSION,
        "group": selected,
        "inventory_id": result["inventory_id"],
        "candidates": cases,
        "source_units": context,
        "source_supplements": supplements,
        "edges": [row for row in consumed["edges"] if row["edge_id"] in edge_ids],
        "outcomes": [row for row in consumed["outcomes"] if row["outcome_id"] in outcome_ids],
        "limitations": refs["limitations"],
        "inventory_handoff": refs["task07_task08_handoff"],
        "input_bindings": list(bindings.values()),
        "preparation": {
            "data_root": str(data_root.resolve()),
            "inventory_result": str(inventory_result.resolve()),
            "grouping_directory": str(grouping_directory.resolve()),
            "grouping_sha256": grouping_sha256,
            "group": group,
            "source_supplements": str(source_supplements.resolve()) if source_supplements else None,
        },
    }
    schema_check(packet, "input")
    return packet


def validate_closure(
    case: dict[str, Any], edges: list[dict[str, Any]], accepted_edge_ids: list[str]
) -> None:
    """Independently compare graph reachability with the maintained closure adapter."""
    direct_edges = [
        edge
        for edge in edges
        if edge["relation_type"] == "comment_response"
        and edge["source_unit_id"] == case["comment_id"]
    ]
    if {edge["target_unit_id"] for edge in direct_edges} != set(case["direct_response_ids"]):
        raise ValueError("Direct response membership differs from complete graph")
    membership = [
        edge
        for edge in edges
        if edge["relation_type"] == "general_response_membership"
        and edge["target_unit_id"] == case["comment_id"]
    ]
    if not {edge["edge_id"] for edge in membership} <= set(accepted_edge_ids):
        raise ValueError("Accepted view omits general-response membership")
    seen = {
        case["comment_id"],
        *case["direct_response_ids"],
        *(edge["source_unit_id"] for edge in membership),
    }
    while True:
        expanded = seen | {
            e["target_unit_id"]
            for e in edges
            if e["relation_type"] in source_adapter.DIRECTED and e["source_unit_id"] in seen
        }
        if expanded == seen:
            break
        seen = expanded
    if seen != set(case["context_unit_ids"]):
        raise ValueError("Response closure differs from independent reachability")
    required_edges = {edge["edge_id"] for edge in direct_edges}
    required_edges.update(
        edge["edge_id"]
        for edge in edges
        if edge["relation_type"] in source_adapter.DIRECTED and edge["source_unit_id"] in seen
    )
    required_edges.update(edge["edge_id"] for edge in membership)
    if (
        required_edges != set(case["relationship_ids"])
        or not set(accepted_edge_ids) <= required_edges
    ):
        raise ValueError("Closure relationship membership differs from complete graph")


def replay(packet: dict[str, Any]) -> None:
    """Require every original input and regenerated packet to remain byte-equivalent."""
    schema_check(packet, "input")
    for ref in packet["input_bindings"]:
        checked(Path(ref["path"]), ref["sha256"])
    settings = packet["preparation"]
    fresh = prepare(
        Path(settings["data_root"]),
        Path(settings["inventory_result"]),
        Path(settings["grouping_directory"]),
        settings["grouping_sha256"],
        settings["group"],
        Path(settings["source_supplements"]) if settings["source_supplements"] else None,
    )
    if fresh != packet:
        raise ValueError("Prepared packet differs from accepted source replay")


def small_group_proposal(
    packet: dict[str, Any], input_bytes: bytes, prompt_bytes: bytes
) -> dict[str, Any]:
    """Create only a stable browsing order; never invoke a ranking model."""
    if not 1 <= len(packet["candidates"]) <= 3:
        raise ValueError("Deterministic bypass requires one to three candidates")
    proposal = {
        "schema_version": "task08a.proposal.v2",
        "input_sha256": digest(input_bytes),
        "prompt_version": VERSION,
        "prompt_sha256": digest(prompt_bytes),
        "model": None,
        "preparation_mode": "deterministic",
        "ranking_not_needed_reason": BYPASS_REASON,
        "proposal_version": 1,
        "reranking_reason": None,
        "tie_groups": [],
        "ranking": [
            {"comment_id": cid, "rank": rank}
            for rank, cid in enumerate(sorted(row["comment_id"] for row in packet["candidates"]), 1)
        ],
    }
    validate_proposal(packet, proposal, input_bytes, prompt_bytes)
    return proposal


def validate_proposal(
    packet: dict[str, Any], proposal: dict[str, Any], input_bytes: bytes, prompt_bytes: bytes
) -> None:
    """Validate complete advisory order, model identity, and deterministic bypass."""
    schema_check(proposal, "proposal")
    if proposal["input_sha256"] != digest(input_bytes) or proposal["prompt_sha256"] != digest(
        prompt_bytes
    ):
        raise ValueError("Proposal input or prompt hash differs")
    if proposal["proposal_version"] > 1 and not (proposal["reranking_reason"] or "").strip():
        raise ValueError("Reranking requires a reason")
    candidates = indexed(packet["candidates"], "comment_id")
    ranking = indexed(proposal["ranking"], "comment_id")
    if ranking.keys() != candidates.keys():
        raise ValueError("Ranking must retain exactly every group candidate")
    if [r["rank"] for r in proposal["ranking"]] != list(range(1, len(candidates) + 1)):
        raise ValueError("Ranks must be ordered, unique and consecutive")
    if len(candidates) <= 3:
        if (
            proposal["preparation_mode"] != "deterministic"
            or proposal["model"] is not None
            or proposal["ranking_not_needed_reason"] != BYPASS_REASON
            or list(ranking) != sorted(candidates)
            or proposal["tie_groups"]
        ):
            raise ValueError("Small groups require stable-ID preparation with no model ranking")
    elif (
        proposal["preparation_mode"] != "model_ranked"
        or proposal["model"] != "gpt-6-astra"
        or proposal["ranking_not_needed_reason"] is not None
    ):
        raise ValueError("Larger groups require actual gpt-6-astra ranking")
    seen_ties: set[str] = set()
    for tie in proposal["tie_groups"]:
        if (
            len(set(tie)) != len(tie)
            or seen_ties.intersection(tie)
            or not set(tie) <= ranking.keys()
        ):
            raise ValueError("Invalid or overlapping tie group")
        positions = [ranking[cid]["rank"] for cid in tie]
        if tie != sorted(tie) or positions != list(
            range(min(positions), min(positions) + len(tie))
        ):
            raise ValueError("Residual ties require contiguous stable-ID order")
        seen_ties.update(tie)


def schema_bytes(name: str) -> bytes:
    """Snapshot the precise interface version used for each record family."""
    directory = source_adapter.SCHEMAS if name in {"input", "source_supplements"} else SCHEMAS
    return (directory / f"{name}.schema.json").read_bytes()


def publish(
    input_path: Path, proposal_path: Path, prompt_path: Path, spec_path: Path, output: Path
) -> dict[str, Any]:
    """Publish a fresh, completion-last packet after source and proposal checks."""
    input_bytes, proposal_bytes = checked(input_path), checked(proposal_path)
    packet, proposal = json.loads(input_bytes), json.loads(proposal_bytes)
    prompt_bytes, spec_bytes = checked(prompt_path), checked(spec_path)
    replay(packet)
    validate_proposal(packet, proposal, input_bytes, prompt_bytes)
    candidates = indexed(packet["candidates"], "comment_id")
    ranked = [
        {"candidate": candidates[row["comment_id"]], "proposal": row} for row in proposal["ranking"]
    ]
    handoff = {
        "schema_version": "task08a.handoff.v2",
        "preparation_mode": proposal["preparation_mode"],
        "ranking_not_needed_reason": proposal["ranking_not_needed_reason"],
        "group": packet["group"]["group"],
        "inventory_id": packet["inventory_id"],
        "candidate_count": len(ranked),
        "proposed_order": [row["comment_id"] for row in proposal["ranking"]],
        "next_stage": "08B",
        "human_selection": "pending",
        "human_eligibility": "pending",
        "ranking_is_advisory": True,
        "selection_template": "08B v2 input qualification required",
        "wording_boundary": "Do not use response-containing packet as comment-only 08C input",
    }
    schema_check(handoff, "handoff")
    payloads = {
        "input.json": input_bytes,
        "proposal.json": proposal_bytes,
        "ranked_candidates.json": encoded(ranked),
        "handoff.json": encoded(handoff),
        "prompt.md": prompt_bytes,
        "spec.md": spec_bytes,
        "validation.json": encoded(
            {
                "schema_version": "task08a.validation.v2",
                "status": "passed",
                "source_replay": True,
                "candidate_count": len(ranked),
                "semantic_review_required": True,
            }
        ),
        "adapter.py": Path(__file__).read_bytes(),
        "source_adapter.py": Path(source_adapter.__file__).read_bytes(),
        "closure_helper.py": Path(pilot_context_repair.__file__).read_bytes(),
    }
    for name in ("input", "proposal", "handoff", "source_supplements"):
        payloads[f"schemas/{name}.schema.json"] = schema_bytes(name)
    manifest = {
        "schema_version": VERSION,
        "input_version": INPUT_VERSION,
        "preparation_mode": proposal["preparation_mode"],
        "model": proposal["model"],
        "prompt_version": proposal["prompt_version"],
        "proposal_version": proposal["proposal_version"],
        "ranking_policy": POLICY,
        "files": {name: digest(content) for name, content in payloads.items()},
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, content in {**payloads, "manifest.json": encoded(manifest)}.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(content)
    _validate(output, require_completion=False)
    with (output / "completion.json").open("xb") as handle:
        handle.write(
            encoded(
                {
                    "schema_version": VERSION,
                    "status": "complete",
                    "manifest_sha256": digest(encoded(manifest)),
                }
            )
        )
    return validate(output)


def _validate(output: Path, *, require_completion: bool = True) -> dict[str, Any]:
    """Recheck exact saved output closure and its complete source-bound reconstruction."""
    manifest_bytes = checked(output / "manifest.json")
    manifest = json.loads(manifest_bytes)
    completion = json.loads(checked(output / "completion.json")) if require_completion else None
    if set(manifest) != {
        "schema_version",
        "input_version",
        "preparation_mode",
        "model",
        "prompt_version",
        "proposal_version",
        "ranking_policy",
        "files",
    } or (
        manifest["schema_version"] != VERSION
        or manifest["input_version"] != INPUT_VERSION
        or manifest["ranking_policy"] != POLICY
    ):
        raise ValueError("Manifest shared version or policy differs")
    if require_completion and completion != {
        "schema_version": VERSION,
        "status": "complete",
        "manifest_sha256": digest(manifest_bytes),
    }:
        raise ValueError("Completion binding differs")
    required = {
        "input.json",
        "proposal.json",
        "ranked_candidates.json",
        "handoff.json",
        "prompt.md",
        "spec.md",
        "validation.json",
        "adapter.py",
        "source_adapter.py",
        "closure_helper.py",
        *{
            f"schemas/{name}.schema.json"
            for name in ("input", "proposal", "handoff", "source_supplements")
        },
    }
    if set(manifest["files"]) != required:
        raise ValueError("Manifest required payload set differs")
    expected = set(manifest["files"]) | {"manifest.json"}
    if require_completion:
        expected.add("completion.json")
    actual = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    if actual != expected or any(p.is_symlink() for p in output.rglob("*")):
        raise ValueError("Output managed-file closure differs")
    payloads = {name: checked(under(output, name), sha) for name, sha in manifest["files"].items()}
    for name in ("input", "proposal", "handoff", "source_supplements"):
        if payloads[f"schemas/{name}.schema.json"] != schema_bytes(name):
            raise ValueError("Shared schema version differs")
    if payloads["source_adapter.py"] != Path(source_adapter.__file__).read_bytes():
        raise ValueError("Source adapter version differs")
    if payloads["closure_helper.py"] != Path(pilot_context_repair.__file__).read_bytes():
        raise ValueError("Closure helper version differs")
    if payloads["adapter.py"] != Path(__file__).read_bytes():
        raise ValueError("Adapter version differs; use matching version for validation")
    packet, proposal = json.loads(payloads["input.json"]), json.loads(payloads["proposal.json"])
    replay(packet)
    validate_proposal(packet, proposal, payloads["input.json"], payloads["prompt.md"])
    candidates = indexed(packet["candidates"], "comment_id")
    if json.loads(payloads["validation.json"]) != {
        "schema_version": "task08a.validation.v2",
        "status": "passed",
        "source_replay": True,
        "candidate_count": len(candidates),
        "semantic_review_required": True,
    }:
        raise ValueError("Validation report differs")
    expected_ranked = [
        {"candidate": candidates[r["comment_id"]], "proposal": r} for r in proposal["ranking"]
    ]
    if json.loads(payloads["ranked_candidates.json"]) != expected_ranked:
        raise ValueError("Ranked candidates differ or warnings lost")
    handoff = json.loads(payloads["handoff.json"])
    schema_check(handoff, "handoff")
    if (
        handoff["proposed_order"] != [r["comment_id"] for r in proposal["ranking"]]
        or handoff["preparation_mode"] != proposal["preparation_mode"]
        or handoff["ranking_not_needed_reason"] != proposal["ranking_not_needed_reason"]
        or handoff["candidate_count"] != len(candidates)
        or handoff["inventory_id"] != packet["inventory_id"]
        or handoff["group"] != packet["group"]["group"]
    ):
        raise ValueError("Handoff differs")
    if any(
        manifest[key] != proposal[key]
        for key in ("model", "prompt_version", "proposal_version", "preparation_mode")
    ):
        raise ValueError("Manifest proposal binding differs")
    return dict(handoff)


def validate(output: Path) -> dict[str, Any]:
    """Require a completion seal as well as full source and output replay."""
    if output.is_symlink():
        raise ValueError("Symlink output directory")
    return _validate(output)


def main() -> None:
    """Expose explicit preparation, publication, and read-only validation commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    for name in ("data-root", "inventory-result", "grouping-directory", "output"):
        prep.add_argument(f"--{name}", type=Path, required=True)
    prep.add_argument("--grouping-sha256", required=True)
    prep.add_argument("--group", required=True)
    prep.add_argument("--source-supplements", type=Path)
    bypass = commands.add_parser("prepare-small-order")
    for name in ("input", "prompt", "output"):
        bypass.add_argument(f"--{name}", type=Path, required=True)
    pub = commands.add_parser("publish")
    for name in ("input", "proposal", "prompt", "spec", "output"):
        pub.add_argument(f"--{name}", type=Path, required=True)
    check = commands.add_parser("validate")
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.command == "prepare":
        packet = prepare(
            args.data_root,
            args.inventory_result,
            args.grouping_directory,
            args.grouping_sha256,
            args.group,
            args.source_supplements,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as handle:
            handle.write(encoded(packet))
    elif args.command == "prepare-small-order":
        input_bytes = checked(args.input)
        packet = json.loads(input_bytes)
        replay(packet)
        proposal = small_group_proposal(packet, input_bytes, checked(args.prompt))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as handle:
            handle.write(encoded(proposal))
    elif args.command == "publish":
        publish(args.input, args.proposal, args.prompt, args.spec, args.output)
    else:
        validate(args.output)
    logging.info("Task08A %s completed: %s", args.command, args.output)


if __name__ == "__main__":
    main()
