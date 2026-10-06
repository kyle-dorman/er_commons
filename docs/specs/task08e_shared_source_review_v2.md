# Task08E shared-source review v2 — superseded plan

Superseded on 2026-10-06 by [Task 08E](../../tasks/sprint2/08e_review_group_evidence.md):
batch research followed by one-question-at-a-time chat review, without source
deduplication. The plan below is retained as history, not execution instructions.

Historical status: **Planning approved on 2026-10-01; not implemented or qualified.** Kyle
reports the health-risk v1 labeling complete. Preserve those decisions; saved
export validation and separate human eligibility remain pending. This revision
replaces per-case citation pages for future review, not historical artifacts.

## Sequence and scope

Complete each numbered task across all participating batches before moving to
the next task: 08B selections, then 08C questions, then 08D claims, then 08E
evidence, then 08F answers. Existing health-risk progress remains valid. Record
stopped, zero-case and explicitly deferred batches rather than fabricating
approvals or backfilling. Unresolved scope permitted by the accepted 08D policy
remains eligible for investigation, not automatically eligible for the benchmark.

At 08E, assemble the full available approved claim pool and bounded discovery
results across batches before building the shared review queue. Retain group,
case, question and claim-version identities behind every link. This permits
source reuse across questions and groups without merging their decisions or
changing exclusive group membership. Planning does not authorize execution on
other groups, new chats, new projects or 08F.

## Reviewer workflow

- Read each distinct source passage or complete table family once across the
  pooled batches. Display all proposed associated claims underneath, with exact
  wording and compact case/question identifiers; relevant question context is
  available on demand.
- Astra proposes Support, Partial, Context, Not support, or Contradicts for each
  link, with a short claim-specific reason. These are visibly editable proposals,
  not approvals. The reviewer can accept the displayed links together, change
  individual links, leave links unresolved, or add a missing approved claim.
- Batch acceptance applies only to the explicitly displayed/selected links; it
  never approves hidden pages, unshown claims or an entire project. Persist each
  accepted pair separately with the action's exact scope and reviewer identity.
- Similar claims may be displayed together. Applying one decision to several
  claims requires an explicit selection with their exact wording visible; no
  semantic merging, automatic label inheritance or frozen-claim rewriting.
- Retain the v1 focused page content: concise summary, why retrieved, exact source
  with spacing and horizontal dividers, substantive limitations, then claim links.
  Omit pipeline history, generic reviewer instructions and provenance boilerplate
  from the main page; retain them in bound records.

There is no aggregate claim-support judgment or second claim-by-claim adequacy
pass. Whether several partial citations establish a whole claim stays for later
explicitly authorized drafting. Separate human eligibility remains required;
neither proposals nor batch acceptance decide it.

## Reduce repetition without losing evidence

Deduplicate exact canonical source units across cases; consolidate overlapping
excerpts only when their exact spans and context remain recoverable. A document
or page alone is not a citation identity. Preserve distinct scenarios, editions,
receptors, periods and nonidentical passages. Table families retain all members,
captions and notes and required render verification.

Prioritize direct, informative passages. Redundant contextual retrievals remain
available without requiring individual labeling; record their retained/deferred
queue dispositions, never infer a negative relationship from omission. Keep
material counterevidence and substantive limitations in the review queue even
when they are inconvenient or do not support the claim. Preserve all retrieval
receipts, support chains, exact sources, warnings and bounded search gaps.

## Short implementation plan and qualification

1. Export and validate completed health-risk labels before any migration. Bind
   each decision to the exact source and approved claim version, retaining notes,
   reviewer and annotation provenance. Conflicting prior labels remain explicit;
   unchanged valid pairs need no relabeling. New or changed pairs remain pending.
2. Build a versioned cross-batch source index and pair records over maintained
   Task07D/08E rendering, source validation and transport. Version the proposal
   prompt, form, input/export schemas and validator as a named v2 revision. Keep
   discovery bounded under the maintained search protocol; no all-pairs labeling
   requirement or automatic search expansion.
3. Qualify with separate source-free fixtures: cross-group duplicate sources,
   overlapping but distinct passages, similar/different claim versions, conflicting
   prior labels, optional links, substantive counterevidence, tables and large
   claim lists. Test real queue navigation, proposals, editing, scoped acceptance,
   saved decisions/reload, unresolved links and native/normalized exports.
4. Use bounded independent identity/export and usability reviews. Reject stale
   versions, lost provenance, unseen-link approval and proposals exported as human
   decisions. Validate per-case exports from the shared queue without inventing
   aggregate outcomes. Carry forward the three historical Task06G commit-pin
   failures; do not count them as new regressions or silently clear them.
5. Before publication, report unique source units, proposed/preserved/pending
   links, duplicates consolidated and retained off-queue candidates. Show review
   effort in source pages and pending links rather than promising a fixed
   reduction. Update the batch register only from verified exports, binding each
   group's rows to the shared project and its own exact decisions.

## Research and learning

The maintained [Label Studio prediction guidance](https://labelstud.io/guide/predictions.html)
was checked on 2026-10-01: imported predictions and human annotations are separate;
editable annotation copies do not make model proposals accepted decisions. Verify
installed-version behavior before choosing the acceptance control.

Sharing source display reduces repeated reading while retaining independent
claim relationships. Prefilled proposals reduce clicks but can encourage agreement;
keep the source and concise claim-specific reason adjacent to editable choices.
A large pooled queue may need bounded pages; pagination must never broaden what
an acceptance action approves.

Documentation-only validation: review routing and sequencing consistency, local
links, and `git diff --check`. Live implementation and qualification are future work.
