# Task 04 review runbook

Task 04's first-pass review and Task 04A are complete. This runbook preserves
the reusable maintenance and publication commands.
The first pass used historical Task 03H diagnostic evidence; it did not accept
that extraction.

## Review-run boundaries

Both passes use a separate review namespace:

```text
$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_04_review/<reviewv1-id>/
```

The maintained `record_review_finding.py` and `set_review_register_status.py`
commands update the explicitly selected first-pass register. They preserve its
historical schema and do not create a later usability registry.

The four preparation/build/publication commands now take a closed request and
an explicit output root:

```bash
uv run python scripts/prepare_extraction_review.py --review-spec "$REVIEW_SPEC" --output-root "$OUTPUT_ROOT"
uv run python scripts/build_extraction_review_bundle.py --review-spec "$REVIEW_SPEC" --output-root "$OUTPUT_ROOT"
uv run python scripts/build_final_extraction_review.py --review-spec "$REVIEW_SPEC" --output-root "$OUTPUT_ROOT"
uv run python scripts/publish_extraction_review.py --review-spec "$REVIEW_SPEC" --output-root "$OUTPUT_ROOT"
```

Each request selects exactly one operation and declares its review pass, source
and evidence roots, schema root, IDs, and expected populations. See the
[request schema](../benchmarks/er_bench/schemas/extraction_review/v1/request.schema.json)
and [maintained command map](pipeline_commands.md). Preparation and publication
are source-free by default. Building a rendered review requires an explicit
`render_pages: true` request and the applicable later task authorization.
Upstream deep validation, raw Docling scans, and census work are separate explicit
request fields. There is no newest-pass or newest-TOC-decision fallback.

The retained final profile remains the accepted Task 03J/04A profile: 35 sources,
757 decisions, 341 visible TOC cards, and 725 unresolved ambiguous links.
A later task must define a new profile before changing those semantics. Original
execution commands, review IDs, and evidence remain in the completed
[Task 04A record](../tasks/sprint2/04a_regenerate_review_and_freeze_release.md).
Gate 2 does not regenerate renders or human decisions.

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
[`FINDINGS.md`](../src/er_commons/human_review_support/extraction_review/FINDINGS.md).

The command derives typed anchors and source/candidate terminal checksums from
the selected item. Use repeatable `--table-id`, `--block-id`, or
`--observation-id` arguments for exact retained objects. These selectors must
resolve within the selected item; bboxes and checksums are never entered
manually.

When all first-pass findings have terminal dispositions, approve and close the
register:

```bash
uv run python scripts/set_review_register_status.py \
  --review-root "$REVIEW_ROOT" --status approved
uv run python scripts/set_review_register_status.py \
  --review-root "$REVIEW_ROOT" --status closed
```

Approval rejects pending `user_confirmed` findings, and closing requires
approval. Both transitions validate records, recover a prior journal, refresh
the Task 03I handoff projection, and publish checksummed updates. An approved
empty register is a valid no-finding outcome.

## Validate the existing review tooling

These checks are source-free and apply to the completed first-pass support:

```bash
uv run ruff check src/er_commons/human_review_support/extraction_review \
  scripts/build_extraction_review_bundle.py scripts/record_review_finding.py \
  scripts/set_review_register_status.py \
  tests/task04_test_support.py tests/test_task04_*.py \
  tests/test_build_task04_review_bundle.py
uv run mypy src/er_commons/human_review_support/extraction_review \
  scripts/build_extraction_review_bundle.py scripts/record_review_finding.py \
  scripts/set_review_register_status.py \
  tests/task04_test_support.py tests/test_task04_*.py \
  tests/test_build_task04_review_bundle.py
uv run pytest -q tests/test_task04_*.py tests/test_build_task04_review_bundle.py
uv run python scripts/build_extraction_review_bundle.py --help
uv run python scripts/record_review_finding.py --help
uv run python scripts/set_review_register_status.py --help
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
