# Task 04 review runbook

Task 04's first-pass review is complete. This runbook preserves the reusable
maintenance commands and marks the boundary for the upcoming Task 04A pass.
The first pass used historical Task 03H diagnostic evidence; it did not accept
that extraction.

## Review-run boundaries

Both passes use a separate review namespace:

```text
$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_04_review/<reviewv1-id>/
```

The existing `record_task04_finding.py` and
`set_task04_finding_register_status.py` commands maintain the completed
first-pass register only. They do not create the Task 04A usability registry or
release-freeze record.

Task 04A must allocate a new review run bound to the completed Task 03J
candidate under `task_03h_clean_full_v4/`. Its explicit `task03j_final`
generator mode, final Gate A contract, record writers, and exact build command
are part of Task 04A work. Do not run the historical first-pass build command
against the Task 03J root or reuse first-pass review IDs, anchors, renders, or
approvals. Update this runbook with the final Task 04A command after that
interface is implemented and accepted.

## Serve a completed review bundle

Set the printed final path, then serve only its HTML directory:

```bash
REVIEW_ROOT="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_04_review/<reviewv1-id>"
uv run python -m http.server 8000 --directory "$REVIEW_ROOT/html"
```

Open `http://localhost:8000/`. Stop the server with Ctrl-C.

## Maintain the first-pass finding register

Use the supported CLI after reviewing an item in `html/index.html`; do not edit
JSON or checksums by hand. The concise example is in
[`FINDINGS.md`](../src/er_commons/human_review_support/task04/FINDINGS.md).

The command derives typed anchors and source/candidate terminal checksums from
the selected item. Use repeatable `--table-id`, `--block-id`, or
`--observation-id` arguments for exact retained objects. These selectors must
resolve within the selected item; bboxes and checksums are never entered
manually.

When all first-pass findings have terminal dispositions, approve and close the
register:

```bash
uv run python scripts/set_task04_finding_register_status.py \
  --review-root "$REVIEW_ROOT" --status approved
uv run python scripts/set_task04_finding_register_status.py \
  --review-root "$REVIEW_ROOT" --status closed
```

Approval rejects pending `user_confirmed` findings, and closing requires
approval. Both transitions validate records, recover a prior journal, refresh
the Task 03I handoff projection, and publish checksummed updates. An approved
empty register is a valid no-finding outcome.

## Validate the existing review tooling

These checks are source-free and apply to the completed first-pass support:

```bash
uv run ruff check src/er_commons/human_review_support/task04 \
  scripts/build_task04_review_bundle.py scripts/record_task04_finding.py \
  scripts/set_task04_finding_register_status.py \
  tests/task04_test_support.py tests/test_task04_*.py \
  tests/test_build_task04_review_bundle.py
uv run mypy src/er_commons/human_review_support/task04 \
  scripts/build_task04_review_bundle.py scripts/record_task04_finding.py \
  scripts/set_task04_finding_register_status.py \
  tests/task04_test_support.py tests/test_task04_*.py \
  tests/test_build_task04_review_bundle.py
uv run pytest -q tests/test_task04_*.py tests/test_build_task04_review_bundle.py
uv run python scripts/build_task04_review_bundle.py --help
uv run python scripts/record_task04_finding.py --help
uv run python scripts/set_task04_finding_register_status.py --help
git diff --check
```

Task 04A adds its own focused tests and validation to this boundary; a green
first-pass gate does not establish Task 04A readiness.

## Retry and recovery

A normal caught build failure removes its unique `.tmp` staging directory. If a
process is killed, inspect retained staging before retrying:

```bash
find "$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_04_review/.tmp" \
  -mindepth 1 -maxdepth 1 -type d -print
```

A new build uses a new staging directory and does not merge stale bytes into a
final review run. Preserve unexpected staging for diagnosis or move a confirmed
stale directory to a named quarantine. An existing final review path is
no-clobber and must be inspected rather than overwritten.

Finding updates use `.finding-update-*` journals inside `records/`. Re-run the
finding command after interruption. Recovery verifies old and new checksums and
finishes the retained update before applying another edit. Multiple journals,
modified targets, or damaged backups/payloads stop with an explicit diagnostic
and require maintainer inspection.
