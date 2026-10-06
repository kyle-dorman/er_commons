"""Expose no-clobber Task08D preparation and saved-review export commands."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from er_commons.group_claims import SCHEMAS, VERSION, load_prepared, prepare
from er_commons.group_claims_export import normalize_export
from er_commons.group_ranking import digest, encoded


def export_saved(
    prepared: Path,
    native_path: Path,
    identity_path: Path,
    current_project_path: Path,
    reviewer_id: int,
    output: Path,
    authorization_path: Path | None = None,
) -> dict[str, Any]:
    """Bind saved native decisions to the imported project and qualified form.

    The caller captures current project settings and all native tasks read-only.
    This command neither creates annotations nor resolves semantic decisions.
    """
    tasks = load_prepared(prepared)
    identity = json.loads(identity_path.read_bytes())
    project = json.loads(current_project_path.read_bytes())
    native_raw = native_path.read_bytes()
    native = json.loads(native_raw)
    authorization = None
    policy_revision = None
    if authorization_path is not None:
        authorization = json.loads(authorization_path.read_bytes())
        Draft202012Validator(
            json.loads((SCHEMAS / "investigation_authorization.schema.json").read_bytes())
        ).validate(authorization)
        if authorization["project_id"] != identity["project_id"] or authorization[
            "native_export_sha256"
        ] != digest(native_raw):
            raise ValueError("Investigation authorization differs from project or native export")
        policy_revision = authorization["policy_revision"]
    form_bytes = (prepared / "form.xml").read_bytes()
    form_hash = digest(form_bytes)
    # Label Studio may remove the one trailing newline when persisting XML.
    # Accept only this observed serialization difference, never internal edits.
    live_form = project["label_config"].encode()
    form_matches = live_form == form_bytes or live_form + b"\n" == form_bytes
    if (
        project["id"] != identity["project_id"]
        or not form_matches
        or identity["form_sha256"] != form_hash
        or project.get("model_version") != VERSION
        or set(identity["task_ids"]) != {task["id"] for task in native}
    ):
        raise ValueError("Live project, imported task identities or form version differs")
    decisions = normalize_export(
        native,
        tasks,
        project_id=identity["project_id"],
        reviewer_id=reviewer_id,
        export_sha256=digest(native_raw),
        policy_revision=policy_revision,
    )
    schema = "investigation_decisions.schema.json" if authorization else "decisions.schema.json"
    Draft202012Validator(json.loads((SCHEMAS / schema).read_bytes())).validate(decisions)
    approved = [
        {
            **claim,
            "case_id": record["case_id"],
            "question_id": record["question"]["question_id"],
            "question_version": record["question"]["question_version"],
            "question_text_sha256": record["question"]["text_sha256"],
            "packet_sha256": record["packet_sha256"],
            "proposal_sha256": record["proposal_sha256"],
        }
        for record in decisions["records"]
        for claim in record["approved_claims"]
    ]
    handoff = {
        "schema_version": "task08d.handoff.v1",
        "status": decisions["status"],
        "stage": "08D",
        "process_revision": VERSION,
        "prepared": str(prepared.resolve()),
        "prepared_manifest_sha256": digest((prepared / "manifest.json").read_bytes()),
        "project_id": identity["project_id"],
        "reviewer_id": reviewer_id,
        "cases": decisions["records"],
        "advancing_case_ids": decisions["advancing_case_ids"],
        "approved_claims": approved,
        "historical_task06g_commit_pin_failures": 3,
        "human_eligibility": "remains_at_08E",
        "next_action": "Separate authorization required for 08E; unresolved cases remain held.",
    }
    payloads = {
        "native_export.json": native_raw,
        "project_identity.json": identity_path.read_bytes(),
        "current_project.json": current_project_path.read_bytes(),
        "decisions.json": encoded(decisions),
        "approved_claims.json": encoded(approved),
        "handoff.json": encoded(handoff),
    }
    if authorization_path is not None:
        handoff.update(
            policy_revision=policy_revision,
            advancement_scope="08E_investigation_only",
            eligibility="undecided",
            question_scope_resolved=not any(
                record.get("scope_unresolved", True) for record in decisions["records"]
            ),
            authorization_sha256=digest(authorization_path.read_bytes()),
            next_action="08E investigation only; preserve unresolved scope and support chains. "
            "Human evidence and eligibility decisions remain required before 08F.",
        )
        payloads["handoff.json"] = encoded(handoff)
        payloads["policy_authorization.json"] = authorization_path.read_bytes()
    output.mkdir(parents=True, exist_ok=False)
    for name, content in payloads.items():
        (output / name).write_bytes(content)
    completion = {
        "schema_version": "task08d.export_completion.v1",
        "status": decisions["status"],
        "files": {name: digest(raw) for name, raw in payloads.items()},
        "approved_claim_count": len(approved),
    }
    (output / "completion.json").write_bytes(encoded(completion))
    return completion


def main() -> None:
    """Run explicit preparation or normalize only an already saved native export."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("prepare")
    for name in ("packet", "proposal", "output"):
        create.add_argument(f"--{name}", type=Path, required=True)
    export = commands.add_parser("export")
    for name in ("prepared", "native", "identity", "current-project", "output"):
        export.add_argument(f"--{name}", type=Path, required=True)
    export.add_argument("--reviewer-id", type=int, required=True)
    export.add_argument("--authorization", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.packet, args.proposal, args.output)
    else:
        export_saved(
            args.prepared,
            args.native,
            args.identity,
            args.current_project,
            args.reviewer_id,
            args.output,
            args.authorization,
        )
    logging.basicConfig(level=logging.INFO)
    logging.info("Task08D %s artifacts: %s", args.command, args.output)


if __name__ == "__main__":
    main()
