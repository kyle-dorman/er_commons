# Task 08B v2 intake and batch setup

Adapter/display revision: `task08b.intake.v2`. Selection template remains
`task08b.selection.v2`; process remains `task08.selection_gate.v2`.

## Compatibility and source display

Dispatch validation to the sealed ranking version. New groups use
`task08a.ranking.v2`, `task08a.proposal.v2` and `task08a.handoff.v2` through the
completion-record-pinned handoff index. Historical v1 handoffs retain their
original validator and source bindings. Both paths verify hashes and identities
before preparing a queue. Model ranking and stable comment-ID ordering for groups
of at most three are equally valid; neither implies selection.

Keep absent explanatory ranking fields absent. The shared selection form displays
original comments, full linked responses and source supplements, without warning
narratives or ranking explanations. Complete source-page supplements are labeled
“Source page context”, distinct from historical footnotes. Source pages are
associated through the verified source spans, rather than depending on which
unit happened to own a deduplicated page. All original provenance stays bound. Candidates with no linked responses retain
empty source arrays and display the neutral state “No linked responses in this
handoff.” This is not an exclusion or eligibility decision.

The explicit predecessor compatibility assessment permits only the pinned legacy
preparation-code snapshot; schemas, form, exporter, artifact hashes and rebuilt
trusted tasks must still match. Health-risk's existing display, four saved
annotations, completed export and superseded project's draft remain preserved.
No prior project needs migration or template changes. Future unqualified code
changes still fail closed.

## Restartable preparation

The maintained batch adapter inventories native projects before creation, checks
exact source data, candidate coverage, template identity and saved order, and
reuses compatible projects. Ambiguous or conflicting projects remain intact and
are reported blocked. New imports contain data only, with no predictions or
annotations. Each group receives a rank-ordered review link and saved receipt.

The batch index distinguishes newly created, reused, already completed and
blocked groups. Preparation is never human completion. Save project IDs, input
and template identities, status and next action. Register updates merge current
08B rows into the latest register with a preserved prior snapshot and concurrent
write checks; existing health-risk and other-stage rows remain intact.

## Qualification and human boundary

Source-free tests cover model-ranked and deterministic inputs, changed hashes,
missing explanations, source-page membership and historical replay. Native
synthetic browser checks exercise complete text display, blank controls, queue
order, save/reload and full-inventory export. Independent audit verifies live
coverage and preservation. The task outcome owns exact validation results.

Future exports reconcile every candidate, retain unanswered candidates as
unreviewed, and require Kyle's explicit group-completion confirmation. Three
selections is a maximum, fewer are welcome, and eligibility remains at 08E.
Setup does not start selection or 08C.

Maintained [configuration guidance](https://labelstud.io/guide/setup.html) explains
why annotated project configurations should be preserved; the
[export guidance](https://labelstud.io/guide/export.html) supports retaining the
complete native JSON audit. Both were checked on 2026-09-30.

`make prepare-group-selection-batch` takes `HANDOFF_INDEX`, `RANKING_RESULT`,
`SETUP_OUTPUT`, `BATCH_REGISTER`, `LABEL_STUDIO_URL` and
`LABEL_STUDIO_CREDENTIALS`. Credentials are read from the existing local JSON
file and never included in receipts. Reuse the same output directory on restart;
existing project receipts and native task identities prevent duplicate imports.
