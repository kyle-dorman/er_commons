"""Assemble independently checkpointed Task08D proposals without accepting labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from er_commons.group_claims import digest, encoded
from er_commons.group_claims_chat import new_journal, prepare_queue, replay
from er_commons.group_claims_inventory import validate_inventory


def reference(path: Path) -> dict[str, str]:
    """Bind exact saved bytes by absolute path for a portable result pointer."""
    return {"path": str(path.resolve()), "sha256": digest(path.read_bytes())}


def read_reference(ref: dict[str, Any]) -> Any:
    """Reject changed bytes before decoding a saved record."""
    path = Path(ref["path"])
    content = path.read_bytes()
    if digest(content) != ref["sha256"]:
        raise ValueError(f"Checksum mismatch: {path}")
    return json.loads(content)


def write_new(path: Path, value: Any) -> None:
    """Preserve prior preparation attempts; identical reruns are harmless."""
    content = encoded(value)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"Refusing to overwrite existing preparation: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)


def assemble(root: Path, output: Path) -> dict[str, Any]:
    """Combine exact per-case model records in frozen input order, with blank decisions.

    Only wrapper hashes change during aggregation. Each original inventory,
    proposal and invocation remains separately checksummed and preserved.
    """
    packet_path = root / "input/packet.json"
    packet = json.loads(packet_path.read_bytes())
    inventories, proposals, bindings = [], [], []
    for source in packet["cases"]:
        cid = source["case_id"]
        single_path = root / "input/cases" / cid / "packet.json"
        single = json.loads(single_path.read_bytes())
        if single["cases"] != [source]:
            raise ValueError(f"Combined/per-case input differs: {cid}")
        paths = {
            name: root / "cases" / cid / f"{name}.json"
            for name in ("inventory", "proposal", "invocation")
        }
        inventory = json.loads(paths["inventory"].read_bytes())
        proposal = json.loads(paths["proposal"].read_bytes())
        validate_inventory(single, inventory, proposal)
        if inventory["model"] != "gpt-6-astra" or proposal["model"] != "gpt-6-astra":
            raise ValueError("Actual Astra proposal required")
        # Invocation is retained as evidence; its model assertion alone cannot
        # establish actual runtime identity. Independent review checks receipts.
        invocation = json.loads(paths["invocation"].read_bytes())
        if (
            invocation.get("actual_model") != "gpt-6-astra"
            or invocation.get("case_id") != cid
            or invocation.get("human_decisions_generated") is not False
            or not invocation.get("worker")
        ):
            raise ValueError(f"Missing actual invocation provenance: {cid}")
        for name, expected in invocation["files"].items():
            if (
                Path(name).name != name
                or digest((paths["invocation"].parent / name).read_bytes()) != expected
            ):
                raise ValueError(f"Invocation file changed: {cid}/{name}")
        if (
            paths["invocation"].parent / "model_input.json"
        ).read_bytes() != single_path.read_bytes():
            raise ValueError(f"Actual model input differs: {cid}")
        inventories.extend(inventory["cases"])
        proposals.extend(proposal["cases"])
        bindings.append(
            {
                "case_id": cid,
                "packet": reference(single_path),
                **{name: reference(path) for name, path in paths.items()},
            }
        )
    inventory = {
        "schema_version": "task08d.inventory.v1",
        "model": "gpt-6-astra",
        "packet_sha256": digest(encoded(packet)),
        "cases": inventories,
    }
    proposal = {
        "schema_version": "task08d.proposal.v1",
        "model": "gpt-6-astra",
        "packet_sha256": digest(encoded(packet)),
        "inventory_sha256": digest(encoded(inventory)),
        "cases": proposals,
    }
    context_notes = json.loads((root / "input/context_notes.json").read_bytes())
    queue = prepare_queue(packet, inventory, proposal, context_notes)
    journal = new_journal(queue)
    replay(queue, journal)
    counts = []
    for case in proposals:
        counts.append(
            {
                "case_id": case["case_id"],
                "claims": len(case["claims"]),
                "assertions": len(
                    next(c for c in inventories if c["case_id"] == case["case_id"])["assertions"]
                ),
                "relationships": {
                    r: sum(c["relationship"] == r for c in case["claims"])
                    for r in ("direct", "supporting", "not-relevant", "unclear")
                },
                "question_gaps": [p for p in case["question_parts"] if p["status"] != "addressed"],
            }
        )
    records = {
        "inventory.json": inventory,
        "proposal.json": proposal,
        "queue.json": queue,
        "journal_initial.json": journal,
        "model_bindings.json": bindings,
        "counts.json": counts,
    }
    for name, value in records.items():
        write_new(output / name, value)
    for card in queue["cards"]:
        path = output / "cards" / card["case_id"] / f"{card['claim_id']}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        content = card["card"].encode()
        if path.exists() and path.read_bytes() != content:
            raise ValueError("Existing card differs")
        if not path.exists():
            path.write_bytes(content)
    result = {
        "schema_version": "task08d.batch_assembly.v1",
        "status": "assembled_pending_independent_review",
        "case_count": len(counts),
        "claim_count": len(queue["cards"]),
        "human_decisions": 0,
        "input": reference(packet_path),
        "artifacts": {name: reference(output / name) for name in records},
    }
    write_new(output / "assembly.json", result)
    return result


def publish(
    root: Path, assembly_dir: Path, reviews: list[Path], validation_path: Path
) -> dict[str, Any]:
    """Seal only a complete independently reviewed batch with zero human decisions."""
    assembly = json.loads((assembly_dir / "assembly.json").read_bytes())
    queue = read_reference(assembly["artifacts"]["queue.json"])
    journal = read_reference(assembly["artifacts"]["journal_initial.json"])
    state = replay(queue, journal)
    expected = [c["case_id"] for c in queue["packet"]["cases"]]
    if len(expected) != 53 or state["event_count"] != 0:
        raise ValueError("Preparation must contain 53 cases and no human review events")
    authoritative = json.loads((root / "input/context_notes.json").read_bytes())
    if authoritative != queue["context_notes"]:
        raise ValueError("Assembled reconciliation and scope context changed")
    if expected != authoritative["all_57_decisions"]["advancing_neutral_ids"]:
        raise ValueError("Prepared queue differs from authoritative saved order")
    if set(authoritative["deferred_ids"]) != {"C013", "C023", "C038", "C057"}:
        raise ValueError("Deferred record set differs")
    model_bindings = read_reference(assembly["artifacts"]["model_bindings.json"])
    bound_cases = {row["case_id"]: row for row in model_bindings}
    if len(bound_cases) != len(expected) or set(bound_cases) != set(expected):
        raise ValueError("Model binding membership differs")
    authors = {}
    for cid, bindings in bound_cases.items():
        for kind in ("inventory", "proposal"):
            original = read_reference(bindings[kind])
            combined = next(c for c in queue[kind]["cases"] if c["case_id"] == cid)
            if original["cases"] != [combined]:
                raise ValueError("Assembled model content differs from reviewed version")
        if read_reference(bindings["packet"])["cases"] != [
            next(c for c in queue["packet"]["cases"] if c["case_id"] == cid)
        ]:
            raise ValueError("Assembled source packet differs")
        invocation = read_reference(bindings["invocation"])
        authors[cid] = invocation["worker"]
    reviewed: dict[str, Any] = {}
    for path in reviews:
        record = json.loads(path.read_bytes())
        if not record.get("reviewer"):
            raise ValueError("Independent reviewer identity required")
        for row in record["cases"]:
            cid = row["case_id"]
            if cid in reviewed or row["status"] != "pass":
                raise ValueError("Duplicate or unresolved semantic review")
            if cid not in bound_cases or record["reviewer"] == authors[cid]:
                raise ValueError("Independent semantic reviewer required")
            for kind in ("proposal", "inventory"):
                if row[f"{kind}_sha256"] != bound_cases[cid][kind]["sha256"]:
                    raise ValueError("Semantic review is stale")
            reviewed[cid] = row
    if set(reviewed) != set(expected):
        raise ValueError("Independent semantic review must cover every case")
    validation = json.loads(validation_path.read_bytes())
    if validation.get("ready") is not True:
        raise ValueError("Final validation is not ready")
    if validation.get("queue_sha256") != assembly["artifacts"]["queue.json"]["sha256"]:
        raise ValueError("Final validation is not bound to the prepared queue")
    source_check = json.loads((root / "review/independent_source_check.json").read_bytes())
    if source_check.get("valid") is not True or source_check.get("input_sha256") != digest(
        encoded(queue["packet"])
    ):
        raise ValueError("Independent source review is stale")
    write_new(assembly_dir / "queue_reference.json", assembly["artifacts"]["queue.json"])
    files: list[Path] = []
    for directory in (root / "input", root / "cases", assembly_dir):
        files.extend(
            p
            for p in directory.rglob("*")
            if p.is_file() and p.name not in {"handoff.json", "manifest.json"}
        )
    files += [
        root / "input/manifest.json",
        *reviews,
        validation_path,
        root / "review/independent_source_check.json",
        root / "preservation_baseline.json",
    ]
    manifest: dict[str, Any] = {
        "schema_version": "task08d.prepared_manifest.v1",
        "files": [reference(p) for p in sorted(set(files))],
    }
    # Verify every byte again before writing the completion-last handoff.
    for ref in manifest["files"]:
        if digest(Path(ref["path"]).read_bytes()) != ref["sha256"]:
            raise ValueError("Artifact changed during publication")
    write_new(assembly_dir / "manifest.json", manifest)
    handoff = {
        "schema_version": "task08d.prepared_handoff.v1",
        "status": "prepared, awaiting human review",
        "phase_a_complete": True,
        "phase_b_complete": False,
        "case_count": 53,
        "claim_count": assembly["claim_count"],
        "human_decisions": 0,
        "advancing_claims": [],
        "deferred_cases": authoritative["deferred_ids"],
        "manifest": reference(assembly_dir / "manifest.json"),
        "queue": assembly["artifacts"]["queue.json"],
        "queue_reference": reference(assembly_dir / "queue_reference.json"),
        "initial_journal": assembly["artifacts"]["journal_initial.json"],
        "review_journal_path": str((root / "human_review/events.jsonl").resolve()),
        "counts": assembly["artifacts"]["counts.json"],
        "context_notes": reference(root / "input/context_notes.json"),
        "validation": reference(validation_path),
        "resume_instructions": reference(assembly_dir / "RESUME.md"),
        "next_action": (
            "Wait for an explicit Phase B request in the separate review chat. "
            "No evidence investigation or answer drafting."
        ),
    }
    write_new(assembly_dir / "handoff.json", handoff)
    return handoff


def main() -> None:
    """Expose restartable assembly without starting review or later stages."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assemble(args.root, args.output)


if __name__ == "__main__":
    main()
