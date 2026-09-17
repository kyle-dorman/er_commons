# Maintaining the Task 05G reference replay

Start with the numbered task for authorization and the selected result manifest
for evidence. A source being usable, a target being structurally identifiable,
and a target being suitable for text-only models are separate facts.

## Where to read or change code

All modules below are in `src/er_commons/response_inventory/`.

| Question | Owner |
| --- | --- |
| What request, code pins and limits are allowed? | `reference_replay_spec.py` |
| How is a command supervised and restarted? | `reference_replay_launch.py` |
| Which stage reads, resolves, compares or publishes? | `reference_replay_workflow.py` |
| Which accepted review/input records are consumed? | `reference_replay_inputs.py` |
| Which selected canonical streams and index are read? | `reference_replay_mechanical.py` |
| Why did one mention resolve or remain a nonlink? | `reference_replay_resolver.py` |
| How are compound appendix references interpreted? | `reference_replay_inner.py` |
| What makes a derived page/table alias qualified? | `reference_replay_qualification.py` |
| What makes a competing heading a corroborated header? | `reference_replay_headers.py` |
| Did every baseline outcome remain accounted for? | `reference_replay_comparison.py` |
| Did a new rule change anything outside its scope? | `reference_replay_cycle.py` |
| Is a checkpoint complete and unchanged? | `reference_replay_storage.py` |
| Can a reviewed candidate be finalized or accepted? | `reference_replay_acceptance.py` |

The resolver's `_resolve_one` reads in order: route the source, select exact
candidates, qualify a header collision, apply authorship exclusion, then build
records. `_select_candidates` owns specificity protection. Keep this order
explicit; a convenient whole-document fallback must not bypass a specific target.
The narrow calls into historical `reference_baseline` intentionally preserve
accepted 05F matching. Refactoring that historical owner is outside this task.

In the input reader, `_qualification_sources` selects which streams need I/O;
it does not decide whether a mention links. `_canonical_streams` verifies the
selected compact inventory and checks large JSONL sizes against that seal.
It does not recursively hash source payloads or open PDFs. Keep that distinction
when changing a read path.

## Debug one outcome

1. Use the selected result manifest's `candidate_root`. Find the mention ID in
   `outcomes/reference_outcomes.jsonl`; inspect its terminal reason, resolver rule,
   source route and global/source/compatible target sets.
2. Read its exact 05D mention span and surrounding response text. The outcome's
   `input_refs` identifies the accepted source revision. Do not infer meaning
   from the extracted label alone when the syntax is compound.
3. Follow `inner_reference_evidence` or `header_qualification_evidence`, when
   present, to exact aliases, blocks and pages. These fields explain inference;
   they do not grant human review or text-only eligibility.
4. Inspect the full baseline `comparison.json` and bounded
   `rule_cycle_comparison.json` before proposing a changed rule. Both preserve
   before/after rows. Add a small synthetic counterexample alongside a positive
   example before attempting another rule cycle.

A supervisor attempt contains `command.log`, `status.json` and `execution.json`.
Workflow logs identify stage start, completion/failure and reused checkpoints.
A checkpoint error now names its root and mismatched top-level fields; JSONL
parse errors name the file and physical line. Preserve failed/incomplete attempts;
never clear them to make a resume succeed. Only an explicit earlier attempt with
verified matching identity can supply a resumed checkpoint.

## Verify a refactor

`make fix` and `make check` are the ordinary entrypoints. Focused coverage is
`uv run pytest -q tests/test_task05g_*.py`. Three historical 06G tests currently
fail at the already reproduced accepted-base mismatch; their exact names are in
the quality report. New failures require investigation.

`scripts/verify_task05g_refactor.py` provides read-only full-population equivalence
against an explicit historical result manifest. Supply `--result` and
`--data-root`, and run it under the existing background supervisor with the task's
resource caps. It verifies the historical packet/checkpoints and regenerates
owned records in memory, using the historical activity identity solely to compare
bytes. Its report binds current code hashes separately. It does not publish a
candidate or claim current code produced the old candidate.

A refactor changes writer code pins. Keep historical configs and launch packets
unchanged; they explain previous executions and will correctly fail current-writer
pin validation. Before formal finalization, prepare a fresh current-code request
and obtain authorization for its supervised replay/comparison. The read-only
quality audit cannot substitute for that new writer identity.
