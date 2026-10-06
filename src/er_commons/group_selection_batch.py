"""Restartable, create-only preparation of separate Task 08B review projects."""

import argparse
import fcntl
import json
import logging
from pathlib import Path
from typing import Any

import requests
from jsonschema import ValidationError  # type: ignore[import-untyped]

from er_commons import group_selection
from er_commons.group_ranking import checked, digest, encoded, under

NEXT_ACTION = (
    "Await human selections; at most three, fewer welcome. Unanswered candidates remain "
    "unreviewed. Export requires full-inventory reconciliation and explicit group completion."
)


class LabelStudio:
    """Small authenticated API boundary; never changes existing tasks or annotations."""

    def __init__(self, url: str, token: str) -> None:
        """Keep credentials in memory and out of saved receipts."""
        self.url = url.rstrip("/")
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Token {token}"

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Make one bounded request without retrying potentially successful writes."""
        response = self.session.request(method, self.url + path, timeout=120, **kwargs)
        response.raise_for_status()
        return response.json()

    def projects(self) -> list[dict[str, Any]]:
        """Read all project metadata, including historical and unrelated projects."""
        results: list[dict[str, Any]] = []
        page = 1
        while True:
            value = self.request("GET", f"/api/projects/?page={page}&page_size=100")
            if isinstance(value, list):
                return results + value
            rows = value["results"]
            results.extend(rows)
            if not value.get("next"):
                return results
            page += 1

    def project(self, project_id: int) -> dict[str, Any]:
        """Read current form and queue settings before accepting a project."""
        return dict(self.request("GET", f"/api/projects/{project_id}/"))

    def tasks(self, project_id: int) -> list[dict[str, Any]]:
        """Export all tasks, explicitly including untouched candidates."""
        return list(
            self.request(
                "GET", f"/api/projects/{project_id}/export?exportType=JSON&download_all_tasks=true"
            )
        )

    def create(self, title: str, form: str) -> dict[str, Any]:
        """Create an empty sequential project; no annotations or predictions."""
        return dict(
            self.request(
                "POST",
                "/api/projects/",
                json={
                    "title": title,
                    "label_config": form,
                    "sampling": "Sequential sampling",
                    "show_collab_predictions": False,
                },
            )
        )

    def ordered_view(self, project_id: int) -> int:
        """Reuse or add an unfiltered rank-ordered view without altering saved views."""
        views = self.request("GET", f"/api/dm/views/?project={project_id}")
        for view in views:
            data = view["data"]
            if data.get("ordering") == ["tasks:data.rank"] and not data.get("filters", {}).get(
                "items"
            ):
                return int(view["id"])
        view = self.request(
            "POST",
            "/api/dm/views/",
            json={
                "project": project_id,
                "data": {
                    "title": "Saved 08A order",
                    "type": "list",
                    "target": "tasks",
                    "ordering": ["tasks:data.rank"],
                    "filters": {"conjunction": "and", "items": []},
                },
            },
        )
        return int(view["id"])

    def import_tasks(self, project_id: int, tasks: list[dict[str, Any]]) -> None:
        """Import only verified blank data in saved handoff order."""
        if any(set(task) != {"data"} for task in tasks):
            raise ValueError("Import must contain data only")
        self.request("POST", f"/api/projects/{project_id}/import", json=tasks)


def save(path: Path, value: Any) -> None:
    """Atomically publish mutable progress; immutable inputs use exclusive creation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(encoded(value))
    temporary.replace(path)


def verified_index(index_path: Path, completion_path: Path) -> dict[str, Any]:
    """Bind the batch index to its completed 08A record before any project action."""
    completion = json.loads(checked(completion_path))
    if (
        completion.get("schema_version") != "task08a.remaining_groups.result.v2"
        or completion.get("status") != "complete"
    ):
        raise ValueError("08A completion record is not a completed v2 batch")
    reference = completion["artifacts"]["handoff_index"]
    if Path(reference["path"]).resolve() != index_path.resolve():
        raise ValueError("Completion refers to another handoff index")
    index = json.loads(checked(index_path, reference["sha256"]))
    groups = index["groups"]
    if len({row["group"] for row in groups}) != len(groups):
        raise ValueError("Duplicate indexed group")
    if len({row["slug"] for row in groups}) != len(groups):
        raise ValueError("Duplicate indexed group slug")
    if (
        len(groups) != completion["counts"]["accepted_groups"]
        or sum(row["candidate_count"] for row in groups)
        != completion["counts"]["accepted_candidates"]
        or index["grouping_sha256"] != completion["grouping_sha256"]
    ):
        raise ValueError("Index inventory disagrees with completion")
    return dict(index)


def verify_project(
    project: dict[str, Any], native: list[dict[str, Any]], tasks: list[dict[str, Any]], form: str
) -> dict[str, Any]:
    """Check exact source/display payloads and sequential native task order, preserving labels."""
    if (
        project["label_config"].strip() != form.strip()
        or project["sampling"] != "Sequential sampling"
    ):
        raise ValueError("Existing project template or queue settings differ")
    ordered = sorted(native, key=lambda row: row["id"])
    if [row["data"] for row in ordered] != [row["data"] for row in tasks]:
        raise ValueError("Native candidate coverage, source bindings, display, or order differs")
    if any(row.get("predictions") for row in native):
        raise ValueError("Unexpected dataset predictions")
    return {
        "task_ids": [row["id"] for row in ordered],
        "candidate_count": len(tasks),
        "annotations": sum(len(row.get("annotations", [])) for row in native),
        "drafts": (
            sum(len(row["drafts"]) for row in native)
            if all("drafts" in row for row in native)
            else None
        ),
        "native_data_sha256": digest(encoded([row["data"] for row in ordered])),
        "form_sha256": digest(form.encode()),
        "native_form_sha256": digest(project["label_config"].encode()),
        "form_comparison": "outer_whitespace_only",
        "sampling": project["sampling"],
        "verification": "passed",
    }


def project_for_group(
    client: LabelStudio,
    projects: list[dict[str, Any]],
    group: str,
    tasks: list[dict[str, Any]],
    form: str,
    registered: list[dict[str, Any]],
    receipt_path: Path,
) -> tuple[int, str, dict[str, Any]]:
    """Reuse an exact project, or create once; suspicious or partial work is held intact."""
    title = f"08B · {group} · {group_selection.VERSION}"
    ids = {
        int(row["project_id"])
        for row in registered
        if row.get("project_id") and row.get("state") != "superseded"
    }
    created_in_setup = False
    if receipt_path.exists():
        receipt = json.loads(checked(receipt_path))
        ids.add(int(receipt["project_id"]))
        created_in_setup = receipt.get("created_in_setup", receipt.get("state") == "created_empty")
    for project in projects:
        if project.get("title") == title:
            ids.add(int(project["id"]))
        elif group in project.get("_groups", []):
            ids.add(int(project["id"]))
    if len(ids) > 1:
        raise ValueError(
            f"Multiple existing projects for group: {sorted(ids)}; preserve and resolve"
        )
    status = "newly_created" if created_in_setup else "reused"
    if ids:
        project_id = next(iter(ids))
    else:
        # A retry discovers the unique exact title if creation succeeded before a timeout.
        project = client.create(title, form)
        project_id = int(project["id"])
        save(
            receipt_path,
            {
                "project_id": project_id,
                "state": "created_empty",
                "title": title,
                "created_in_setup": True,
            },
        )
        projects.append(project)
        status = "newly_created"
    project = client.project(project_id)
    native = client.tasks(project_id)
    if not native:
        if (
            project["label_config"].strip() != form.strip()
            or project["sampling"] != "Sequential sampling"
        ):
            raise ValueError("Empty existing project interface differs; preserved")
        client.import_tasks(project_id, tasks)
        native = client.tasks(project_id)
    verification = verify_project(project, native, tasks, form)
    verification["view_id"] = client.ordered_view(project_id)
    save(
        receipt_path,
        {
            "project_id": project_id,
            "state": "verified",
            "title": project["title"],
            "created_in_setup": status == "newly_created",
            **verification,
        },
    )
    return project_id, status, verification


def merge_register(register_path: Path, rows: list[dict[str, Any]], output: Path) -> None:
    """Merge latest register under a lock; snapshot and check concurrent bytes."""
    with register_path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        before = checked(register_path)
        register = json.loads(before)
        for row in rows:
            matching = [
                existing
                for existing in register["batches"]
                if existing["stage"] == "08B"
                and existing["group"] == row["group"]
                and existing.get("state") != "superseded"
            ]
            if matching:
                if len(matching) != 1 or matching[0].get("state") == "selection_complete":
                    raise ValueError("Register changed to completed or ambiguous 08B work")
                if matching[0].get("project_id") not in (None, row.get("project_id")):
                    raise ValueError("Concurrent 08B project conflict")
                matching[0].update(row)
            else:
                register["batches"].append(row)
        snapshot = output / f"batch_register_before_{digest(before)}.json"
        if not snapshot.exists():
            with snapshot.open("xb") as handle:
                handle.write(before)
        if checked(register_path) != before:
            raise ValueError("Concurrent register write detected; retry merge")
        save(register_path, register)


def setup(
    index_path: Path,
    completion_path: Path,
    data_root: Path,
    output: Path,
    register_path: Path,
    client: LabelStudio,
) -> dict[str, Any]:
    """Prepare independent groups, continuing after invalid inputs and preserving completed work."""
    index = verified_index(index_path, completion_path)
    output.mkdir(parents=True, exist_ok=True)
    projects = client.projects()
    for project in projects:
        if "08b" in project.get("title", "").lower():
            project["_groups"] = sorted(
                {
                    task["data"]["group"]
                    for task in client.tasks(int(project["id"]))
                    if task.get("data", {}).get("group")
                }
            )
    register = json.loads(checked(register_path))
    summaries: list[dict[str, Any]] = []
    updates: list[dict[str, Any]] = []
    for entry in index["groups"]:
        logging.info(
            "Task08B setup starting: %s (%s candidates)", entry["group"], entry["candidate_count"]
        )
        row: dict[str, Any] = {
            "group": entry["group"],
            "slug": entry["slug"],
            "candidate_count": entry["candidate_count"],
        }
        registered = [
            r for r in register["batches"] if r["stage"] == "08B" and r["group"] == entry["group"]
        ]
        try:
            for key in ("input", "proposal", "handoff", "manifest", "completion"):
                checked(under(data_root, entry[key]["path"]), entry[key]["sha256"])
            completed = [r for r in registered if r["state"] == "selection_complete"]
            if completed:
                row.update(
                    status="already_completed",
                    project_id=completed[0]["project_id"],
                    review_url=completed[0]["review_url"],
                    next_action="Preserve completed 08B and concurrent later-stage work.",
                )
            else:
                group_output = output / "groups" / entry["slug"]
                group_output.mkdir(parents=True, exist_ok=True)
                prepared = under(
                    data_root,
                    f"pipelines/brisbane_baylands/task_08/{entry['slug']}/08b/selection_v2/prepared",
                )
                if not prepared.exists():
                    group_selection.prepare(
                        Path(entry["handoff"]["path"]).parent, completion_path, data_root, prepared
                    )
                tasks = group_selection.load_prepared(prepared)
                form = checked(prepared / "form.xml").decode()
                project_id, status, verification = project_for_group(
                    client,
                    projects,
                    entry["group"],
                    tasks,
                    form,
                    registered,
                    group_output / "project.json",
                )
                row.update(
                    status=status,
                    project_id=project_id,
                    review_url=f"{client.url}/projects/{project_id}/data?tab={verification['view_id']}&labeling=1",
                    next_action=NEXT_ACTION,
                    prepared=str(prepared),
                    input_version=entry["interface_version"],
                    template_version=group_selection.VERSION,
                    process_revision=group_selection.PROCESS_REVISION,
                    intake_revision=group_selection.INTAKE_REVISION,
                    upstream_handoff=entry["handoff"],
                    upstream_input=entry["input"],
                    upstream_proposal=entry["proposal"],
                    proposal_version=json.loads(checked(Path(entry["proposal"]["path"])))[
                        "schema_version"
                    ],
                    handoff_version=json.loads(checked(Path(entry["handoff"]["path"])))[
                        "schema_version"
                    ],
                    prepared_manifest={
                        "path": str(prepared / "manifest.json"),
                        "sha256": digest(checked(prepared / "manifest.json")),
                    },
                    verification=verification,
                )
                updates.append(
                    {
                        **row,
                        "stage": "08B",
                        "state": "prepared_awaiting_human_review",
                        "attempt": 1,
                        "input": {
                            "path": str(prepared / "tasks.json"),
                            "sha256": digest(checked(prepared / "tasks.json")),
                        },
                        "output": {
                            "path": str(group_output / "project.json"),
                            "sha256": digest(checked(group_output / "project.json")),
                        },
                    }
                )
        except (ValueError, KeyError, OSError, requests.RequestException, ValidationError) as error:
            row.update(
                status="blocked",
                error=str(error),
                next_action="Resolve recorded setup failure; preserve existing work and retry.",
            )
            receipt = output / "groups" / entry["slug"] / "project.json"
            if receipt.exists():
                row["project_id"] = json.loads(checked(receipt))["project_id"]
                row["review_url"] = f"{client.url}/projects/{row['project_id']}/data"
            active = [r for r in registered if r.get("state") != "superseded"]
            if not any(r.get("state") == "selection_complete" for r in active):
                prior = active[0] if len(active) == 1 else {}
                updates.append({**prior, **row, "stage": "08B", "state": "setup_blocked"})
            logging.exception("Task08B group blocked: %s", entry["group"])
        logging.info("Task08B setup status: %s: %s", entry["group"], row["status"])
        summaries.append(row)
        save(
            output / "index.json", {"schema_version": "task08b.batch_setup.v1", "groups": summaries}
        )
    merge_register(register_path, updates, output)
    result = {
        "schema_version": "task08b.batch_setup.v1",
        "handoff_index_sha256": digest(checked(index_path)),
        "groups": summaries,
        "counts": {
            status: sum(row["status"] == status for row in summaries)
            for status in ("newly_created", "reused", "already_completed", "blocked")
        },
    }
    save(output / "index.json", result)
    lines = [
        "# Task 08B review projects",
        "",
        "| Group | Candidates | Review | Status |",
        "| --- | ---: | --- | --- |",
    ]
    for row in summaries:
        link = f"[Open review]({row['review_url']})" if row.get("review_url") else "—"
        lines.append(f"| {row['group']} | {row['candidate_count']} | {link} | {row['status']} |")
    (output / "index.md").write_text("\n".join(lines) + "\n")
    return result


def main() -> None:
    """Run explicitly authorized setup using the existing local credential file."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("index", "completion", "data-root", "output", "register"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--credentials", type=Path, required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    setup(
        args.index,
        args.completion,
        args.data_root,
        args.output,
        args.register,
        LabelStudio(args.url, json.loads(checked(args.credentials))["token"]),
    )


if __name__ == "__main__":
    main()
