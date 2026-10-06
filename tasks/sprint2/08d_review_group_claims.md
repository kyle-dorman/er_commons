# Task 08D — Prepare and review response claims in chat

Status: **Combined production review complete; investigation-only handoff sealed.**
Kyle approved this two-phase workflow on 2026-10-05 after the C056 practice.
First, a preparation chat builds and validates the entire review queue. After it
finishes, a separate review chat presents one prepared claim at a time.
Kyle explicitly authorized Phase A preparation on 2026-10-05. Parent: [Task 08](08_curate_grouped_benchmark.md).

## Goal and scope

Prepare response assertions and their reasoning relationships for all **53 approved
questions** in the completed [combined 08C result](../../docs/specs/task08c_combined_review_result.json),
then obtain explicit human decisions using a consistent chat template. Preserve
08C order and original group membership as provenance; no separate group projects
or chats are required. The four deferred cases C013, C023, C038 and C057 are not
08D inputs. No similarity filtering, question rewriting or silent scope reduction.

This flow supersedes the mandatory Label Studio interface and per-group chat
requirements for the new combined pass. Historical health-risk claims, labels,
08E/08F work and interface implementations remain unchanged. Both health-risk
questions enter this new preparation with their current frozen identities; no
historical claim approvals transfer. Carry the C002 downstream reconciliation
hold and all other 08C scope requirements into the handoff. Reconciliation of old
08E/08F approvals is not authorized here.

The C056 chat trial is stopped. Its early saved prototype records are historical
practice only. Kyle explicitly requested no recording for the later practice
approvals; do not reconstruct those as durable decisions or import any practice
approval into the production queue.

## Inputs and source boundary

Read AGENTS.md, docs/index.md, docs/todo.md, this task, the Task 08 umbrella,
[human review process](../../docs/response_comment_human_review_process.md),
[artifact rules](../../docs/data_artifacts.md) and [architecture](../../docs/architecture.md).
Bind the current 08C completion, all 57 dispositions and the 53 exact frozen
question IDs, versions, text hashes and source identities. Reconcile against the
accepted 08B/inventory provenance without feeding selection/ranking reasons into
claim drafting.

Resolve each complete official-response closure from the accepted inventory,
including linked responses, supplements, supplied citations and source warnings.
Carry explicitly authorized additional comment/response packets, especially
C017's M-OSEC-272–274 and C045's full PC-MS context, plus every case-specific
next-step requirement. Verify response closure independently; an 08C excerpt is
not a substitute. Use the final approved question, not an older question embedded
in an 08C response-check artifact.

Astra proposal inputs contain the frozen question, original/authorized context,
complete responses and source metadata. Exclude historical claims, labels,
reference answers, selection/ranking rationales and downstream evidence judgments.
Keep 08C citation clues, answerability notes and scope cautions attached separately
for later use; they cannot manufacture claims absent from the response. Existing
citations are provenance, not proof of support. No Draft evidence search in 08D.

## Phase A — batch preparation in the first chat

On a later explicit preparation request, complete background work for all 53 cases
in one restartable batch run. Bounded per-case Astra workers may run in parallel;
each receives only its own pinned input. “One go” means the whole queue is ready
before labeling, not one enormous model context or an uncheckpointed invocation.
Do not request human claim decisions during preparation.

1. Verify input hashes, membership/order, frozen questions, complete response
   closures and supplemental context. Save input manifests and reconciliation
   holds in a fresh external namespace; never overwrite historical artifacts.
2. Adapt maintained `group_claims_input`, `group_claims_inventory` and existing
   validation/export logic at narrow boundaries. Implement a versioned chat
   prompt/schema, prepared-card format, append-only decision journal and strict
   exporter. Do not pretend the Label Studio exporter or practice scripts already
   validate chat approvals. Qualify the production chat path before real review.
3. Have Astra (`gpt-6-astra`) inventory every substantive assertion before assigning
   relevance. Save inventory, complete passage coverage and actual model input,
   output and invocation provenance. No silent omission of unrelated assertions.
4. Draft readable, independently assessable claims with source-supported subjects,
   conditions, quantities, comparisons, attribution, uncertainty and negation.
   Split claims whose decisions could differ; avoid incidental fact fragments.
   Map every inventory item to a proposed claim or an explicit coverage outcome.
5. Propose `direct`, `supporting`, `not-relevant` or `unclear` relationships with
   concise reasoning. Direct claims target exact frozen question parts. Supporting
   claims target one specific direct/supporting claim and explain their material
   contribution; topic overlap is insufficient. Support chains must be acyclic
   and reach a direct claim. Preserve unanswered/partial question parts explicitly.
6. Precompute every review card: full question, claim text, relationship reasoning,
   exact response excerpts, supplied references and full target-claim text/version.
   Present direct claims first, then supporting claims in dependency order, then
   not-relevant/unclear claims. IDs stay stable independent of display order.
   Save per-case counts and a deterministic combined queue with case and claim
   positions. Non-relevant content remains reviewable, not silently discarded.
7. Independently review source coverage, claim fidelity, relationships and question
   gaps. Validate all bindings and cards. Resolve preparation defects; preserve
   semantic uncertainty as visible proposed `unclear`/gap records. Input integrity
   or missing-closure failures block the ready handoff, never silently drop a case.
8. Publish a checksummed **prepared, awaiting human review** handoff and compact
   result pointer. Include inputs, inventories, proposals, cards, queue, manifests,
   validation results, holds and resume instructions. All human decisions start
   blank. No claims advance to 08E merely because preparation is complete.

## Phase B — human review in the second chat

Start only after the prepared handoff is complete and the user invokes review.
Verify the handoff once at intake and retain its identity in checkpoints; load
precomputed cards rather than regenerating claims or researching each turn.
Recheck changed artifacts/relationships as needed. Discussion may require bounded
source inspection and a versioned revision, but routine approval should be fast.

Show exactly one claim at a time using this template, with all context repeated:

**Approved question**

> Full exact frozen question.

**Claim N of M — direct / supporting / not-relevant / unclear claim**

> Full exact proposed claim.

**Supports claim K:** (for a supporting claim)

> Full exact target claim text, even if it was shown earlier.

Explain in one or two sentences how this claim materially supports that target.
For a direct claim, use **Why direct:** and explain the question part addressed.
For other relationships, use **Why not relevant:** or **Why unclear:**. Include
case position and identity unobtrusively so numbering remains unambiguous.

**Response passage**

> Exact source passage(s); label any line-break normalization or omitted page
> furniture. Keep full original text and source anchors in the saved record.

**Supplied reference:** Source-provided references, or “None supplied.” Distinguish
an internal comment cross-reference from a Draft citation. Do not invent citations
or imply they have been evidence-verified.

Kyle can approve, edit, reject, defer or discuss the claim and its relationship.
An unambiguous “approved”/“yes, next” approves the currently displayed wording and
relationship together. Questions and discussion are not approvals. Record exact
feedback and version-bound decisions before advancing. A revision requires a new
version and fresh approval; do not transfer approval to changed text or targets.

After edits, splits, merges or relationship changes, preserve old versions and
invalidate affected dependent links until reviewed against the revised targets.
Refresh dependent cards; explicitly reconfirm changed relationships. New claims
require verified response anchors and human review. Preserve review order/cursor,
case/claim IDs, exact texts, source hashes, target versions and decisions so a new
chat can resume without relying on conversational memory. Never require scrolling
back to read a target claim.

After a case's claims, show a compact coverage/gap summary and request a case-level
disposition and confirmation of current links. Do not infer case readiness from
the last claim approval. Retain unresolved gaps, stopped cases and rejected or
not-relevant claims. Claim approval establishes what the response asserts and
its relevance, not truth, evidence support, eligibility or final answer adequacy.

## Completion and handoff

The [investigation policy](../../docs/specs/task08d_investigation_v1.md) governs
support chains and explicit unresolved question scope: after human case approval,
approved direct/supporting claims may be released **for investigation only** with
unresolved scope retained. Missing claim/relationship decisions, broken support
chains or unanchored revisions do not advance. Not-relevant, rejected, deferred
or unresolved claims remain in the audit history outside the advancing set.
If no usable direct claim remains, obtain an explicit human stop/hold.

Export only exact human-approved versions with source spans, question identity,
current target/chain versions, reasoning, supplied citations and question gaps.
Carry all required supplemental contexts, 08C citation clues and historical
reconciliation holds; distinguish them from approved response claims. Reconcile
all 53 case outcomes and every inventoried assertion. Mark preparation completion
and human-review completion separately. Starting 08E remains a separate request.

## Qualification, validation and review

Use existing two-pass/source-closure learning and the qualified investigation
policy; readable claims, relevance and evidentiary support remain separate.
Precomputed context makes routine review fast without weakening source binding.
Versioned journals protect exact approvals when a discussion changes a claim.

Before live review, exercise synthetic chat intake, display/approval, revisions,
splits/merges, support chains, stale target edits, rejected targets, unanswered
scope, whole-case holds, restarts, empty/missing decisions and deterministic
export. Tampered hashes, unanchored quotes, dangling/cyclic support and stale
approvals must fail closed. Check exact inline target text in rendered cards.
Independently check inventory completeness, relationship fidelity and final
export identities. Use `make fix`/`make check` for implementation and distinguish
known historical Task06G failures; use `git diff --check` for docs-only changes.

## Non-goals and authorization

The original workflow update was contract-only. Kyle subsequently authorized
Phase A for all 53 approved questions. Phase B requires a separate explicit review
request. Do not create Codex chats or Label Studio projects, import practice or
historical approvals, investigate evidence, draft answers, commit or push as part
of preparation.

## Phase A completion — 2026-10-05

The [compact preparation result](../../docs/specs/task08d_combined_preparation_result.json)
binds `08d_combined_20261005_v1/prepared_v1/handoff.json` under Task 08's external
root. It is **prepared, awaiting human review**, with 53 cases in saved 08C order,
641 inventoried assertions and 641 proposed claims: 175 direct, 203 supporting,
262 not-relevant and one unclear. All human claim and case decisions are blank;
zero claims advance. C013, C023, C038 and C057 remain preserved deferrals outside
the queue.

Input verification replayed the 08C journal and checked 747 bound references.
Independent graph/source checks cover all 53 cases, 87 response appearances and
1,909 exact passages, including C017's expanded context and C045's full PC-MS
context. The new source-only Astra invocations retain actual configured model and
worker identity, exact packets, prompts, inventory-before-proposal receipts and
saved outputs. Shared assertions were reused only from identical source units
inventoried within this new run; each question's relationships were prepared afresh.
Historical health-risk work and its reconciliation holds remain unchanged.

Independent reviewers passed all cases after correcting referral-only relevance,
generator-use wording and one weak visitor-buffer support link. Earlier versions
remain preserved. There are 52 unresolved question parts across 29 cases; C014,
C020 and C026 have no direct claim. C054 retains an internally inconsistent source
comparison as unclear. These are visible review scope limits, not source-integrity
failures or inferred human stops. The source citation index is nonexhaustive;
cards preserve exact reference-bearing response text instead of interpreting a
missing index entry as no supplied reference.

The [production chat path](../../docs/specs/task08d_combined_chat_review_v1.md)
provides version-bound cards, blank intake, append-only events, revision/dependency
invalidation, deterministic resumption and strict export. Independent publication
review corrected stale assembly/context acceptance and an incomplete-case cursor.
Qualification passed 40 focused tests. Final `make fix`/`make check` passed
formatting, lint and types; tests reported 3,231 passed, one skipped and only the
same three historical Task06G commit-pin failures named below. `git diff --check`
passed. No unresolved preparation defect remains.

Learning: exact source anchoring, substantive relevance and human acceptance are
separate checks. A referral can locate analysis without answering the question;
blank decisions and a separate case confirmation prevent prepared claims from
being mistaken for accepted answers. Completion-last publication binds the exact
reviewed proposals, inventory, scope notes and qualification evidence together.
The next chat should use the result's resume instructions and precomputed cards.
No production human review, 08E, answer drafting, project/chat creation or commit/push
was performed.

## Combined production review outcome

The [production result](../../docs/specs/task08d_combined_review_result.json)
binds the completed review separately from the immutable Phase A preparation
result. All 53 cases and 641 current claims have decisions in 1,456 append-only
events: 635 approvals and six rejections. Fifty cases have confirmed current
relationships and an investigate disposition; C014, C020 and C024 are held.
The maintained export retains 385 direct/supporting claims (172 direct, 213
supporting) for future investigation only. Eligibility remains undetermined.

Kyle authorized faster whole-case displays during this review, grouping exact
claims with their supports and showing confidence categories; excerpts remained
available in saved cards. Exact versions, verbatim feedback, target bindings,
previous versions and independent case confirmations remain in the journal and
case records. Historical/practice approvals were not imported. Frozen questions
and four 08C deferrals remain unchanged.

The handoff binds the deterministic review export, journal snapshot, validation,
resume instructions and all 299 supplemental review files. Required context
explicitly carries C049 A002's citation-only role, retained unclear context,
index/risk composition research needs, fleet/speed and housing-framing notes,
all case gaps and historical reconciliation holds. Modified Alternative 1 and
Chapter 16 exclusions retain the explicit C044 A001 exception and C042 A011's
mandatory later evidence reconsideration. C055 A005 v2 preserves the approved
scope revision. C054's user-requested numerical investigation and disputed
A006 → A007 → A009 premise remain flagged; no source correction is inferred.

Validation: frozen preparation/queue hashes match; maintained replay and strict
export pass; saved export reproduces byte-for-byte; all decisions and current
support chains validate. Independent closeout audit checked sensitive scope and
context cases, including all ten C054 investigation artifact hashes. The complete
supplemental inventory closes the exporter's sidecar-preservation gap. No code
changed or code tests rerun; prior historical test limitations remain recorded.
Documentation diff validation passed. No 08E, answer drafting, new project/chat,
commit or push was started by this closeout.

Learning: a reviewed claim export is insufficient when discussion creates
required context outside its schema. Seal those sidecars with explicit effective
scope resolutions, while retaining superseded versions, so later research cannot
silently lose citation leads or mistake claim approval for evidence support.

## Historical health-risk implementation and outcomes

The following records describe preserved Label Studio work, not the current
combined chat workflow. Historical authorization/status statements apply only
to their original batches and dates.

## Activated health-risk implementation plan — 2026-09-30

Authorization covers only M-OSEC-241 and O-Joint-44, shared preparation,
qualification, proposals and a fresh Label Studio project. Saved human decisions
are a separate pending gate. No 08E, answers, eligibility, backfill or other groups.
The completed 08C `chat_review_v1/exports/review_v1/handoff.json` under the
health-risk stage is pinned at SHA-256
`3668198d11d1f343739c2ec4119a17a7a43cd450f162092b49db153353ad73db`.
C001-v2 and C002-v2 remain byte-exact; prospective 08C v2 guidance does not alter
their approved text or drafting provenance.

1. Verify the 08C seal, approvals, question hashes and selection/source bindings.
   Reuse the accepted inventory's directed-closure adapter and independently
   reconcile complete reachable response units, edges, supplied citations,
   supplements and inherited warnings for only these two comments.
2. Establish `task08d.claim_review.v1`: source-only packet, two-pass Astra prompt,
   proposal and decision schemas, generated native claim cards and strict saved
   export normalization. Reuse existing hashing, source rendering and native
   Label Studio control patterns without consuming historical claim/answer data.
3. Astra inventories substantive assertions before assigning relevance. Save the
   inventory separately from relationship proposals. Each claim has exact response
   span anchors; each direct claim names a frozen-question part; each supporting
   claim names one direct target and explains its material contribution. Record
   unanswered question parts explicitly, including essential unresolved issues.
4. Qualify synthetic queues separately from dataset review: exact prefills, blank
   human decisions, edits, relationship/target changes, rejection, unresolved
   decisions, essential gaps, whole-case stops, native save/reload/export and
   version/source tampering. Independently review coverage, relationships and
   exporter fidelity before opening the two-case review project.
5. Publish a pending-review receipt and coordination handoff, preserve prior batch
   register bytes, and wait for Kyle's saved decisions. On requested export, bind
   the native task/form/reviewer to trusted inputs, retain every disposition and
   export only explicitly approved exact direct/supporting claims from unblocked
   cases. Freeze current target text/version with reviewed support relationships;
   reject dangling, removed, relabeled or stale targets. No automated semantic
   approval or silent question narrowing.

The form must expose per-claim approval/reject/unresolved controls with no model
prefill, editable relationship rationale, and case readiness/stop controls. A
case-level approval also explicitly confirms the current links after all edits.
Unanswered parts remain visible and require an explicit human resolution or hold;
any essential unresolved claim/gap prevents case advancement. New claims require
source anchors and the same human decision gate. Capacity changes require a new
preserved project revision; never overwrite live reviewed content.

Research checked the maintained Label Studio configuration, predictions and native
JSON export guidance on 2026-09-30. Predictions populate candidate content but are
not decisions; native saved annotation bytes are the review authority. The native
UI can save structurally invalid relationships, so the exporter must fail closed.
Readable assertion wording retains attribution and qualifications; source spans
provide provenance but cannot substitute for a concrete assertion. Relevance is
separate from truth and evidence support. Carry the three historical Task06G
commit-pin test failures forward, distinguishing them from current regressions.

## Preserved v1 preparation outcome

The shared `task08d.claim_review.v1` interface is qualified.
[Project 47](http://127.0.0.1:8097/projects/47/data?tab=46&labeling=1)
contains only M-OSEC-241 and O-Joint-44, with exact frozen questions and no saved
human annotations or drafts. The [readiness record](../../docs/specs/task08d_health_risk_result.json)
owns input/output identities, review evidence and the exact coordination handoff.
08D claim approval is **not complete**; wait for Kyle's saved decisions.

Source verification independently reconstructed the accepted directed response
closure: M-OSEC-241 has one response; O-Joint-44 has its own response plus
RA-Caltrain-9 and RA-Caltrain-8. Exact source spans, supplied citations, three
supplements, six citation outcomes and source warnings remain attached. The active
`claims_v1/input_v3/` packet uses 75 exact sentence-sized passage spans while
retaining full original units. Earlier preparation revisions remain preserved.
Both frozen question hashes match 08C: C001-v2
`26c727ae52ece439e98492efa0eacca62342281cc30b69984b5c62411ffe6595`
and C002-v2
`b2560320d3963b4f81391cb93152ad018e6c489aacd2257852d8e9dab8a0f717`.

Astra saved 53 substantive assertions before relevance filtering. The final
`drafting_v2/` proposal contains 31 claims: seven direct, twelve supporting and
twelve not-relevant. C001 has six claims; C002 has twenty-five. Independent
coverage review accounted for every passage/assertion. Relationship review led
to reclassifying weak regional/contextual support, restoring generator-use
wording and retaining the limited local vegetation-benefit assertion without
implying adoption. Its re-review passed. Essential partial/unanswered question
parts remain visible and require human resolution or a held/stopped case.

Qualification used separate source-free projects 45/46; project 45's interrupted
automated draft remains preserved. Project 46 exercised the actual queue,
prefilling, blank decisions, saved wording/relationship edits, cleared targets,
reopened target edits, unresolved scope, whole-case stops, untouched tasks and
native exports. Independent fidelity review passed, including eight negative
binding/relationship mutations. Warnings now render recursively; native edits
must lose focus before Submit/Update registers the change. Shared capacity uses
native fixed cards; unused addition cards stay blank. No synthetic approvals
entered project 47, and no historical case labels/claims/answers entered proposals.

Validation: 52 targeted tests passed. Final `make check` passed formatting, lint
and types, with **2,983 passed, one skipped and the same three historical failures**:

- `test_collection_generator_preserves_historical_v38_owner_packet`
- `test_task06g_v38_generation_remains_immutable_after_finalization_amendment`
- `test_task06g_templates_are_executable_and_source_free`

All three fail at the preserved Task06G accepted-commit pin. An initial new type
annotation error was fixed before the final run; it is not an outstanding failure.
No sealed upstream artifacts were changed. The batch register retains its preceding
bytes and records `awaiting_human_review`. Preparation completion is distinct from
claim-review completion. No 08E, eligibility, answers, other groups or backfill.

## Authorized interface revision v2 — 2026-09-30

Kyle requested removal of the editable source-passage ID field and substantially
larger claim-wording and relationship-explanation boxes, with a fresh project.
Implement `task08d.claim_review.v2` without changing frozen questions, proposals
or source anchors. Source bindings become fixed trusted proposal metadata;
exact quotations remain readable. New unanchored additions stay held for a
source-bound revision. Preserve v1 export normalization and its sealed artifacts.
Project 47 has no submitted annotations but one unsaved draft (including a claim
choice); preserve it in place and in a predecessor snapshot without migration.
The new queue starts with blank decisions, as requested.

Plan: version form/task/decision schemas, update source-binding normalization,
qualify enlarged controls and saved exports on a separate source-free project,
then create and inspect a fresh two-case project. Preserve prior register bytes
and publish replacement pending-review records. No new model proposals or 08E.


## V2 replacement outcome — awaiting human review

[Project 49](http://127.0.0.1:8097/projects/49/data?tab=48&labeling=1) replaces
project 47 for the same two cases and unchanged 31 proposals. The
[v2 interface](../../docs/specs/task08d_claim_review_v2.md) removes source-ID inputs
and has resizable 260px claim editors and 220px explanation editors. Exact source
bindings remain in trusted records and normalized exports. Current project has
no submitted annotations or drafts; no decisions were migrated. Project 47's
unsaved draft and all v1 evidence remain preserved.

Source-free project 48 verified actual control sizes, removed input/predictions,
prefill, editing, relationship changes, saved export/reload, source preservation
and unresolved/stop gates. Independent export review passed. All 64 targeted tests
passed. `make check` passed formatting/lint/types, with 2,995 tests passed, one
skipped and the same three historical Task06G commit-pin failures. The
[current readiness record](../../docs/specs/task08d_health_risk_result.json)
points to the updated batch register and exact pending-review coordination handoff.
No question, claim proposal, source or approval semantics were rewritten; no 08E.

## First saved-review export — incomplete decisions

Kyle confirmed both tasks finished. Project 49 contains saved annotations 214 and
215 (reviewer 1), no drafts, 30 explicit claim approvals and one missing claim
disposition. The native capture and normalized incomplete export preserve all
saved wording, rationale and relationship edits. No claim wording changed.

Remaining human decisions:

- M-OSEC-241 A005 was changed to direct but retains claim target A004; it needs
  question-part target P001, P002 or both, as judged by Kyle.
- M-OSEC-241 A006 was changed to supporting and has an extended rationale, but
  no direct-claim target.
- O-Joint-44 A004 (regional Impact AQ-1 remaining significant/unavoidable) has
  no saved claim decision. A012's change to direct correctly targets P002.
- Both cases lack whole-case status, current-link confirmation and question-gap
  disposition/resolution. The existing essential partial/unanswered scope remains
  visible; no inference from task submission supplies these decisions.

Both cases are incomplete and zero claims advance. Independent saved-export
review confirmed exact source/question/version bindings and these missing fields.
An exporter false rejection caused by Label Studio trimming one terminal XML
newline was repaired narrowly with regression coverage. Fresh
`prepared_export_v1/` differs only in the exporter snapshot/manifest; native
records and the original prepared input remain preserved. This is not a semantic
approval or interface change. Current result and batch register point to the
incomplete export and exact pending coordination handoff. No 08E started.

Current validation: 66 targeted tests passed. Full `make check` passed formatting,
lint and types; 2,997 tests passed, one skipped and the same three Task06G
commit-pin tests listed above failed. The captured export completion hashes and
source/question bindings verify; normalized decisions exactly match the separate
diagnostic. The current coordination record is
`health_risk/08d/claims_v2/coordination_review_v1.json` under Task 08's artifact
root; its hash and the updated register are pinned in the current result.


## Second saved-review capture — still incomplete

Kyle reported corrections. Fresh `claims_v2/exports/review_v2/` preserves updated
annotations 214 and 215 and all 31 explicit claim approvals. O-Joint-44 A004 now
has approval; M-OSEC-241 A006 now targets A005. A005 still has claim target A004
instead of a question-part target, so it and its dependent A006 remain invalid.
Both annotations still omit whole-case status, link confirmation and question-gap
disposition/resolution. Zero claims advance; no 08E execution is authorized by
this incomplete export. `coordination_review_v2.json` is the current coordination
record. All previous captures and exports are preserved. No code changed; the
66 targeted passes and full-check 2,997 passes, one skip and three historical
Task06G commit-pin failures are carried forward, not newly rerun.


## Third saved capture — explicit unresolved scope

Kyle saved Ready and confirmed links for both cases, with question gaps explicitly
Unresolved. A005 is now supporting A004; A006 still targets A005, which is no
longer direct. The exporter correctly rejects both Ready cases under the current
gate; no `exports/review_v3/` was created. Raw annotations and per-case rejection
receipts are preserved in `review_capture_v3/`; current coordination is
`coordination_review_v3.json`. All 31 claim approvals remain preserved, but zero
claims advance. Kyle raised whether partial information should be investigated
in 08E; a distinct investigation-only gate would require an explicit contract
revision, without resolving missing scope by inference or predetermining a rebuttal.
No code changed or tests rerun; the prior test results and historical failures stand.


## Authorized investigation-policy outcome

Kyle explicitly authorized investigation with unresolved question scope and
supporting-to-supporting relationships. Qualified `task08d.investigation.v1`
releases 20 exact approved claims (8 direct, 12 supporting), retaining 11 approved
not-relevant claims and all eight unresolved question parts. Both cases are ready
for investigation only; eligibility and answer adequacy remain undecided. C001
A006 → A005 → A004 is preserved with exact target/chain versions. No human labels,
questions, source anchors, claim wording or upstream artifacts were changed.

The exact export is `claims_v2/exports/investigation_v1/handoff.json`, SHA-256
`afba5a60922b569cbf2dc2fcdde62f5ba94704cc82ed5ef8208486a92fa3dbec`. Current
coordination is `claims_v2/coordination_investigation_v1.json`. The current result
pins these artifacts, policy authorization, independent review and batch register.
89 targeted tests passed. Full checks: formatting/lint/types passed; 3,033 tests
passed, one skipped, and the three historical Task06G commit-pin failures remain.
Synthetic project54 exercised saved-native support chains and unresolved scope;
independent code and final export reviews passed. This chat has not begun live
08E work, determined eligibility, or drafted answers.
