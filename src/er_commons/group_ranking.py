"""Prepare and seal one advisory Task 08A ranking without human decisions."""

import argparse
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons import pilot_context_repair
from er_commons.pilot_context_repair import refresh_cases
from er_commons.response_inventory.release_storage import inventory_identity, read_container

VERSION = "task08a.ranking.v1"
POLICY = "Advisory joint question/rebuttal quality; no labels; stable-ID residual ties"
SCHEMAS = Path(__file__).resolve().parents[2] / "benchmarks/er_bench/schemas/task08a"
DIRECTED = {
    "response_response",
    "response_general_response",
    "general_response_response",
    "general_response_general_response",
}


def encoded(value: Any) -> bytes:
    """Serialize saved records consistently, independently of model behavior."""
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def digest(content: bytes) -> str:
    """Bind exact persisted bytes."""
    return hashlib.sha256(content).hexdigest()


def rows(content: bytes) -> list[dict[str, Any]]:
    """Read source JSONL without changing record order."""
    return [json.loads(line) for line in content.splitlines() if line.strip()]


def indexed(records: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    """Reject duplicate identities before joining records."""
    result = {row[key]: row for row in records}
    if len(result) != len(records):
        raise ValueError(f"Duplicate {key}")
    return result


def checked(path: Path, sha256: str | None = None) -> bytes:
    """Reject symbolic links and changed pinned bytes."""
    if path.is_symlink():
        raise ValueError(f"Symlink input: {path}")
    content = path.read_bytes()
    if sha256 is not None and digest(content) != sha256:
        raise ValueError(f"Checksum mismatch: {path}")
    return content


def under(root: Path, relative: str) -> Path:
    """Keep inventory references within their declared root."""
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Input path escapes root")
    return path


def schema_check(value: dict[str, Any], name: str) -> None:
    """Apply the shared strict record shape before semantic validation."""
    schema = json.loads((SCHEMAS / f"{name}.schema.json").read_bytes())
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
        validate_closure(case, consumed["edges"])
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
    packet = {
        "schema_version": VERSION,
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


def validate_supplements(
    supplements: list[dict[str, Any]],
    context: list[dict[str, Any]],
    pages: dict[str, dict[str, Any]],
) -> None:
    """Keep omitted page text separate and require exact source-page coordinates."""
    units = indexed(context, "unit_id")
    seen = set()
    for row in supplements:
        key = (row["unit_id"], row["page_id"], row["text_start"], row["text_end"])
        if key in seen or row["unit_id"] not in units:
            raise ValueError("Supplement duplicate or unrelated unit")
        seen.add(key)
        page = pages[row["page_id"]]
        start, end = row["text_start"], row["text_end"]
        if not 0 <= start < end <= len(page["raw_text"]):
            raise ValueError("Supplement coordinates invalid")
        if page["raw_text"][start:end] != row["text"]:
            raise ValueError("Supplement source text differs")
        if page["physical_page"] not in units[row["unit_id"]]["source_pages"]:
            raise ValueError("Supplement page outside source unit")


def validate_closure(case: dict[str, Any], edges: list[dict[str, Any]]) -> None:
    """Independently compare graph reachability with the maintained closure adapter."""
    direct_edges = [
        edge
        for edge in edges
        if edge["relation_type"] == "comment_response"
        and edge["source_unit_id"] == case["comment_id"]
    ]
    if {edge["target_unit_id"] for edge in direct_edges} != set(case["direct_response_ids"]):
        raise ValueError("Direct response membership differs from complete graph")
    seen = {case["comment_id"], *case["direct_response_ids"]}
    while True:
        expanded = seen | {
            e["target_unit_id"]
            for e in edges
            if e["relation_type"] in DIRECTED and e["source_unit_id"] in seen
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
        if edge["relation_type"] in DIRECTED and edge["source_unit_id"] in seen
    )
    if required_edges != set(case["relationship_ids"]):
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


def validate_proposal(
    packet: dict[str, Any], proposal: dict[str, Any], input_bytes: bytes, prompt_bytes: bytes
) -> None:
    """Validate complete advisory ordering, exact quotes, and deterministic residual ties."""
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
    units = indexed(packet["source_units"], "unit_id")
    for row in proposal["ranking"]:
        case = candidates[row["comment_id"]]
        if any(not row[key].strip() for key in ("question_quality", "response_quality")):
            raise ValueError("Whitespace-only rationale")
        if any(not value.strip() for value in row["concerns"]):
            raise ValueError("Whitespace-only concern")
        for name in ("question_anchors", "response_anchors"):
            allowed = (
                {case["comment_id"]}
                if name == "question_anchors"
                else set(case["context_unit_ids"]) - {case["comment_id"]}
            )
            for anchor in row[name]:
                if (
                    not anchor["quote"].strip()
                    or anchor["unit_id"] not in allowed
                    or anchor["quote"] not in units[anchor["unit_id"]]["text"]
                ):
                    raise ValueError("Source quote anchor is outside its exact context")
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
        "schema_version": "task08a.handoff.v1",
        "group": packet["group"]["group"],
        "inventory_id": packet["inventory_id"],
        "candidate_count": len(ranked),
        "proposed_order": [row["comment_id"] for row in proposal["ranking"]],
        "next_stage": "08B",
        "human_selection": "pending",
        "human_eligibility": "pending",
        "ranking_is_advisory": True,
        "selection_template": "08B first-use qualification required",
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
                "schema_version": "task08a.validation.v1",
                "status": "passed",
                "source_replay": True,
                "candidate_count": len(ranked),
                "semantic_review_required": True,
            }
        ),
        "adapter.py": Path(__file__).read_bytes(),
        "closure_helper.py": Path(pilot_context_repair.__file__).read_bytes(),
    }
    for name in ("input", "proposal", "handoff", "source_supplements"):
        payloads[f"schemas/{name}.schema.json"] = (SCHEMAS / f"{name}.schema.json").read_bytes()
    manifest = {
        "schema_version": VERSION,
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


def validate(output: Path) -> dict[str, Any]:
    """Recheck exact saved output closure and its complete source-bound reconstruction."""
    manifest_bytes = checked(output / "manifest.json")
    manifest = json.loads(manifest_bytes)
    completion = json.loads(checked(output / "completion.json"))
    if set(manifest) != {
        "schema_version",
        "model",
        "prompt_version",
        "proposal_version",
        "ranking_policy",
        "files",
    } or (manifest["schema_version"] != VERSION or manifest["ranking_policy"] != POLICY):
        raise ValueError("Manifest shared version or policy differs")
    if completion != {
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
        "closure_helper.py",
        *{
            f"schemas/{name}.schema.json"
            for name in ("input", "proposal", "handoff", "source_supplements")
        },
    }
    if set(manifest["files"]) != required:
        raise ValueError("Manifest required payload set differs")
    expected = set(manifest["files"]) | {"manifest.json", "completion.json"}
    actual = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    if actual != expected or any(p.is_symlink() for p in output.rglob("*")):
        raise ValueError("Output managed-file closure differs")
    payloads = {name: checked(under(output, name), sha) for name, sha in manifest["files"].items()}
    for name in ("input", "proposal", "handoff", "source_supplements"):
        if (
            payloads[f"schemas/{name}.schema.json"]
            != (SCHEMAS / f"{name}.schema.json").read_bytes()
        ):
            raise ValueError("Shared schema version differs")
    if payloads["closure_helper.py"] != Path(pilot_context_repair.__file__).read_bytes():
        raise ValueError("Closure helper version differs")
    if payloads["adapter.py"] != Path(__file__).read_bytes():
        raise ValueError("Adapter version differs; use matching version for validation")
    packet, proposal = json.loads(payloads["input.json"]), json.loads(payloads["proposal.json"])
    replay(packet)
    validate_proposal(packet, proposal, payloads["input.json"], payloads["prompt.md"])
    candidates = indexed(packet["candidates"], "comment_id")
    if json.loads(payloads["validation.json"]) != {
        "schema_version": "task08a.validation.v1",
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
        or handoff["candidate_count"] != len(candidates)
        or handoff["inventory_id"] != packet["inventory_id"]
        or handoff["group"] != packet["group"]["group"]
    ):
        raise ValueError("Handoff differs")
    if any(
        manifest[key] != proposal[key] for key in ("model", "prompt_version", "proposal_version")
    ):
        raise ValueError("Manifest proposal binding differs")
    return dict(handoff)


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
    elif args.command == "publish":
        publish(args.input, args.proposal, args.prompt, args.spec, args.output)
    else:
        validate(args.output)
    logging.info("Task08A %s completed: %s", args.command, args.output)


if __name__ == "__main__":
    main()
