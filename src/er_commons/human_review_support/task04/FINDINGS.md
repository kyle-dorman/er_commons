# Task 04 finding edits

Use the supported CLI after reviewing an item in `html/index.html`. Do not edit
the JSON records or checksums by hand.

```bash
uv run python scripts/record_task04_finding.py \
  --review-root "$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_04_review/<reviewv1-id>" \
  --review-item-id reviewitem-... \
  --class extraction_defect \
  --status accepted_for_task03i \
  --expected "Verified table cells own text inside the accepted table bounds." \
  --observed "Canonical paragraph blocks duplicate retained table-cell text." \
  --downstream-consequence "Search and reconstruction can return duplicate text." \
  --table-id "tbl/appendix/p974/table-1" \
  --block-id "block/appendix/p974/paragraph-585"
```

The command derives typed page, table-family, warning, or failure anchors from the
selected review item and verified input inventory. Optional repeatable `--table-id`,
`--block-id`, and `--observation-id` selectors add exact canonical-object or retained
observation anchors. Each selector must resolve to compact exact evidence retained in
the current selection manifest; page, family, bbox, source, and candidate checksums are
copied from that evidence. Bboxes explicitly declare the `displayed_page` coordinate
space used by the review overlay. Humans never type geometry, checksums, or anchor JSON. The
Task 03I table-text-ownership example intentionally selects both the retained `tbl/...`
object and the overlapping canonical `block/...` object.

The command:

1. validates the selection, finding register, handoff, and bundle manifest;
2. rejects review-item IDs absent from the current selection and stale checksums;
3. derives the finding ID from normalized observation content and updates its status in place;
4. publishes a recoverable, checksummed two-record update; and
5. rebuilds `task03i_handoff.json` from accepted `extraction_defect` findings only.

Use `retained_task04` for findings that should remain in Task 04 without entering
the Task 03I handoff. Other finding classes are always preserved in the register.

Finding identity describes the observation, not its disposition. Re-recording the
same class and expected/observed/consequence text with a new status updates that
finding in place. Status is excluded from the finding-ID preimage; the derived typed
anchor is included. If a process stops during the two-file publication, the staged
journal and backups are retained. The next invocation verifies those bytes and
finishes the same update before accepting another edit. Multiple journals,
modified targets, or damaged recovery files fail with explicit diagnostics.

After every finding has a terminal disposition, approve and then close the register:

```bash
uv run python scripts/set_task04_finding_register_status.py \
  --review-root "$REVIEW_ROOT" --status approved
uv run python scripts/set_task04_finding_register_status.py \
  --review-root "$REVIEW_ROOT" --status closed
```

Approval rejects any remaining `user_confirmed` finding. Closing requires prior
approval. Approved and closed registers reject further finding edits. Both transitions
use the same recoverable two-record publication and refresh the exact checksum-linked
Task 03I projection; an approved empty register is a supported no-finding outcome.

See the [Task 04 maintainer runbook](../../../../docs/task04_maintainer_runbook.md)
for build, serving, validation, retry, and recovery procedures.
