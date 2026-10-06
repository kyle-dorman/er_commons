# Task 08D combined chat review v1

The [08D task](../../tasks/sprint2/08d_review_group_claims.md) owns the two-phase
workflow. This production path prepares all 53 frozen questions before a separate
human-review chat. It imports no historical or practice claim decisions.

## Maintained boundaries

- `group_claims_combined_input` verifies the combined 08C result, saved journal,
  selection provenance, exact questions and complete directed source closures.
  Its per-case source packets exclude selection reasons, historical claims and
  evidence assessments. Separate context notes preserve all upstream cautions.
  The [combined input profile](../../benchmarks/er_bench/schemas/task08d/chat_v1/input.schema.json)
  explicitly adds authorized context and supplemental closures to the retained
  `task08d.input.v1` span contract; historical input schemas remain unchanged.
- `group_claims_inventory` retains two-pass passage/assertion accounting.
  [Astra's production prompt](../prompts/task08d_combined_claim_review_v1.md)
  permits acyclic supporting chains reaching a direct claim.
- `group_claims_batch` combines per-case inventories and proposals in saved order,
  validates invocation files and prepares cards with blank decisions. Aggregation
  changes only wrapper bindings; original model artifacts remain preserved.
- `group_claims_chat` owns exact cards, the journal and strict reviewed export.
  Its [journal schema](../../benchmarks/er_bench/schemas/task08d/chat_v1/journal.schema.json)
  and semantic checks are independent of historical Label Studio exporters.
- `group_claims_chat_cli` provides `validate`, `next`, `record` and `export`.
  `next` reads state without recording an approval or display. A review chat must
  show the full returned card and then record its exact display before accepting
  the user's separate decision.

## Review startup and saved events

Start only on the user's explicit Phase B request. Read the compact preparation
result and verify its checksummed handoff, queue, code/schema snapshot and source
manifest once at intake. Retain that identity in subsequent checkpoints. Use the
precomputed cards for unchanged claims. Never redraft claims or repeat evidence
research as part of normal presentation.

The handoff identifies a queue-reference JSON and an initially empty JSONL journal.
The maintained invocation is:

```bash
uv run python -m er_commons.group_claims_chat_cli next \
  --queue-reference QUEUE_REFERENCE --journal JOURNAL_JSONL
```

For each shown card, persist a `display` event with its `case_id`, `claim_id` and
`card_sha256`. Every event records `actor`, `chat_reference` and an ISO timestamp
with timezone. Save exact user wording as `feedback`; the recorded statement and
its original chat reference provide decision provenance. An explicit `decision`
event binds the currently shown card and is `approve`, `reject` or `defer`.
Questions use `discussion`, never an inferred approval. `record --event EVENT_JSON`
appends only after replay validation, flushes saved bytes and retains the hash chain.

Revisions use `revise` with `replaces`, the complete replacement `claims` and exact
feedback. Splits and merges preserve old versions; refreshed part-to-claim maps
can accompany the event. Frozen question-part text and essential flags cannot be
silently narrowed. All assertions remain accounted for and every claim retains
verified passage anchors. Replaced claims and their transitive dependents lose
approvals; the whole-case confirmation is invalidated. Retired IDs cannot be reused.
Changed cards require redisplay and fresh decisions.

After claim review, `next` returns the full case state and gaps. Show a compact
coverage summary and explicitly request a separate `case_decision`: `investigate`,
`hold` or `stop`, bound to `case_sha256`. Investigation requires all current claim
decisions, confirmation of current links and an explicit gap disposition. Unresolved
question scope can remain under the existing investigation-only policy. A case
without a usable direct claim needs an explicit hold or stop. A held/stopped case
retains its partial decisions and all unreviewed claims.

`export --output NEW_PATH` replays saved events and preserves exact sources,
questions, claims, versions, support chains, gaps and separate upstream context
notes. It exports only approved direct/supporting claims from explicitly authorized
cases. Blank, missing, stale, dangling or cyclic records fail closed. This export
never establishes truth, evidence support, eligibility or answer adequacy, and does
not itself authorize 08E.

The source citation index is not exhaustive. Cards preserve exact reference-bearing
response text when no separate citation record exists, and distinguish indexed
absence from an assertion that the source supplied no reference. No reference is
treated as evidence-verified.

## Qualification and learning

Synthetic tests exercise the actual file-backed command path: blank intake,
shown-card approvals, discussion, revisions, real splits/merges, support chains,
stale target/case versions, rejected/deferred targets, unresolved scope, holds,
missing decisions, restarts, torn records and byte-identical exports. Mutation
tests reject changed source text, cards, questions and inventory accounting.
Independent review additionally checks substantive coverage and relationships;
structural validation cannot establish either.

The implementation reuses [JSON Schema 2020-12 validation](https://json-schema.org/draft/2020-12/json-schema-validation)
for record shape and narrow Python checks for cross-record identities. A locked,
append-only JSONL journal uses [flush and fsync](https://docs.python.org/3/library/os.html#os.fsync)
before returning success. These primary references were checked on 2026-10-05.
No new runtime dependency or workflow framework is needed. Hash chains detect
changed saved bytes; they are not cryptographic proof of reviewer identity, so
verbatim feedback and original chat references remain required.
