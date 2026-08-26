# Task 04 maintainer runbook

Task 04 builds a source-bound, read-only review workspace and maintains human
findings. It never mutates Task 03 artifacts. The canonical first-pass root is:

```text
$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_04_review/<reviewv1-id>/
```

## Build and monitor

Run from the repository root after setting `ER_COMMONS_DATA_ROOT`:

```bash
uv run python scripts/build_task04_review_bundle.py \
  --data-root "$ER_COMMONS_DATA_ROOT" \
  --retained-root "$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_03h_clean_full_v3" \
  --output-root "$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_04_review" \
  --log-level INFO
```

Logs identify discovery, selected/rendered pages, the review-run ID, failures, and
the final publication path. Work is staged below `task_04_review/.tmp/`; the final
`reviewv1-*` directory appears only after validated publication.

The production build is intentionally fixed to the accepted 35-source Task 03H scope.
Discovery verifies readiness status, ordered IDs, aggregate source/page/byte counts,
and the staged catalog path, byte size, and SHA-256 before reading review evidence.
`InputScopePolicy.synthetic_fixture(...)` exists only as an explicit typed seam for
source-free tests; the production CLI exposes no scope-relaxation option.

## Serve the review UI

Set the printed final path, then serve only its HTML directory:

```bash
REVIEW_ROOT="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_04_review/<reviewv1-id>"
uv run python -m http.server 8000 --directory "$REVIEW_ROOT/html"
```

Open `http://localhost:8000/`. Stop the server with Ctrl-C.

## Record or change a finding

Use `scripts/record_task04_finding.py`; do not edit JSON or checksums manually.
The concise example is in
[`FINDINGS.md`](../src/er_commons/human_review_support/task04/FINDINGS.md).
The CLI derives typed anchors and source/candidate terminal checksums from the
selection and input inventory. Use repeatable `--table-id`, `--block-id`, or
`--observation-id` arguments when the finding concerns exact retained objects. The IDs
must resolve within that selected item; bbox and checksums are never entered manually.

Finding identity excludes status. Re-run the same semantic finding text and class
with a different `--status` to update it in place. Changing expected behavior,
observed behavior, downstream consequence, class, or selected anchor semantics
creates a different finding identity.

When all findings have terminal dispositions, approve and then close the register:

```bash
uv run python scripts/set_task04_finding_register_status.py \
  --review-root "$REVIEW_ROOT" --status approved
uv run python scripts/set_task04_finding_register_status.py \
  --review-root "$REVIEW_ROOT" --status closed
```

Approval rejects pending `user_confirmed` findings. Closing requires approval. Either
terminal overall state blocks later item edits. Both commands validate all records,
recover any prior journal, refresh exact handoff projection/checksums, and use the same
recoverable staged publication as finding edits. An approved empty register explicitly
records that review produced no findings.

## Validate maintained code

These checks are source-free and use only synthetic fixtures:

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

## Retry and recovery

A normal caught build failure removes its unique `.tmp` staging directory. If the
process is killed, inspect retained staging before retrying:

```bash
find "$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_04_review/.tmp" \
  -mindepth 1 -maxdepth 1 -type d -print
```

A new build uses a new staging directory and does not reuse stale bytes. Preserve
unexpected staging for diagnosis or move a confirmed stale directory to a named
quarantine; never merge it into a final review run. An existing final review-run
path is no-clobber and must be inspected rather than overwritten.

Finding updates use `.finding-update-*` journals inside `records/`. Re-run the
finding command after interruption. Recovery verifies old/new checksums and finishes
the retained update before applying the requested edit. Do not delete or alter the
journal. Multiple journals, modified targets, or damaged backups/payloads stop with
an explicit diagnostic and require maintainer inspection.
