# Task 07D: Discover and Review Evidence

Status: **Complete with explicit MVP limitations after the required code-quality
gate: independent reviews passed, maintained replay reproduces all six case files
byte-for-byte, and focused checks pass. Sealed labels and source artifacts unchanged.**

## Abstract and goal

Find candidate evidence for the reviewed response claims and let Kyle judge
what it actually supports in a separate Label Studio project. Keep one coherent source packet per case, with exact source anchors and gaps,
and present one claim at a time for human evidence review. The final case export
separates claims from deduplicated section/table citations, with support/context
levels and no required citation-to-claim links; the
[export decision](../../docs/specs/evidence_review_v1.md#case-level-citation-export-decision-2026-09-28)
owns aggregation and provenance rules. A claim's
07C.1 relevance describes its role in answering the comment; it does not establish
truth, source support, or answer adequacy. Follow the
[Task 07 umbrella](07_pilot_reference_case_authoring.md).

## Inputs and reviewed scope

Use the [07C.1 replacement handoff](07c1_review_claims_and_relevance.md#final-reviewed-export-and-replacement-handoff),
completed in commit `2b2b3a9`, bound by
[`task07c1_final_result.json`](../../docs/specs/task07c1_final_result.json).
Pin `07c1/reviews/seven_case_export_20260925T211401Z/` under the Task 07 pilot
artifact root. Verify the bound manifest and its managed files before consuming
the normalized reviews. Preserve exact reviewed wording, stable claim IDs,
source references, concern links and supporting graph. Use each review's
`evidence_candidate_claim_ids`; never reconstruct the queue from slots or counts.

| Approved case | Candidate claims |
| --- | ---: |
| O-Joint-19 | 10 |
| O-GGBA-2 | 2 |
| M-OSEC-273 | 2 |
| SA-Caltrans-33 | 3 |
| PC-LM-2 | 3 |
| I-CF-4 | 11 |
| Total | 31 |

**Current pilot selection, 2026-09-28:** Six selected, evidence-ready cases,
with 31 approved direct/supporting claims as listed above. I-EA-2 and I-CJ-4
are excluded by Kyle's explicit selection decisions; preserve all review history.

I-CJ-4 was skipped as `unclear` in 07B (task103/annotation107) and excluded in
07C/07C.1. Kyle reopened it during 07D, then explicitly withdrew it again on
2026-09-28 after revisiting the comment. The fresh project26/task165 catch-up is
historical and no longer requires review. Do not continue its 07B/07C.1 catch-up
or evidence discovery unless Kyle explicitly reopens it again. The reopening
and suggestion repair remain documented below as historical actions.

The accepted 07C.1 export remains unchanged: six approved cases and 31 claims.
Neither excluded case contributes claims to the current evidence queue.
Preserve I-EA-2's five claims and historical Unclear outcome as well.

Also bind the accepted 07A.1 response inventory and matching 06H repaired
handoff/usability records. Response passages and their explicit references are
curator-only search leads, never evidence that their own claims are true.
Use accepted canonical Draft EIR sources, retaining sampled-review limits,
nonlinks, extraction warnings and text-only figure restrictions. The already
accepted Final F1 substitution is the sole inherited edition exception: retain
its exact physical source identity, edition and full 06H limitations; never
label it original Draft F1. No general Final EIR evidence search is authorized.

## Execution checkpoints

1. **Completed planning:** inspect the accepted claim handoff, refine this contract, research
   methods, and propose the workflow and prototype case. No corpus searches,
   reference-target retrieval, candidate evidence proposals or model runs.
2. **Authorized on 2026-09-25:** Kyle said “ok cool lets try the example you
   suggested,” confirming the proposed SA-Caltrans-33 trial. Implement and discover evidence
   for exactly that case, build one review prototype and validate it. Record
   that confirmation here before execution.
3. **After Kyle reviews and approves the prototype:** expand to the remaining
   five currently approved cases in small packets. I-CJ-4 is now excluded. Prototype approval is not case-content
   approval; each support judgment still requires Kyle's review.

These checkpoints come from Kyle's explicit request on 2026-09-25. No commit,
push, upstream mutation or prior-project replacement is included.

## Brief implementation plan

1. Verify and freeze the selected claim queue and upstream bindings. Define
   versioned discovery, candidate and human-review records before coding.
2. Build narrow package helpers for reference-first discovery and review
   preparation, reusing accepted source/link readers and native Label Studio
   controls. Keep discovery separate from human decisions and API operations.
3. For the confirmed prototype case, resolve supplied explicit references first;
   retrieve complete relevant semantic units with necessary neighboring context.
   Keep ambiguous, unresolved and unusable references explicit rather than
   guessing their targets. Deduplicate passages shared by multiple claims.
4. Follow [search protocol v1](../../docs/specs/task07d_search_protocol_v1.md)
   for subsequent authorized runs: supplied-reference resolution, three planned
   query purposes per claim (including corpus-wide and qualification/conflict
   searches), up to ten hits per query, and a bounded six-query case follow-up.
   Freeze the full-corpus index identity, log query/hit dispositions, and assemble
   complete section/table units into a deduplicated case citation pool.
5. Present the one-case prototype, validate actual save/reload/export behavior,
   and ask Kyle whether the evidence decisions and workload are workable before
   expanding. Keep any QA annotations separate from his review.

The initial prototype used three queries per claim/five hits per query. That
historical budget is superseded for future authorized runs by search protocol v1;
old receipts and packets remain unchanged. The protocol owns budgets, controlled
expansion, agent prompts, replay settings and coverage checks. A result cap or
incomplete search yields a recorded gap, never a claim of absence.
No embeddings, paid API integration or target-model retriever in this trial.

## Proposed prototype: SA-Caltrans-33

Kyle confirmed SA-Caltrans-33 on 2026-09-25. It has one reviewed
concern and three candidate claims: C001 is direct; C002 and C003 support C001.
The existing response points to Draft EIR Tables 4.9-7 (printed page 4.9-61),
4.9-8 (4.9-63), and footnote 15 (4.9-61). These are unverified search leads.
No target passage has been retrieved or judged in this planning step.

The claims address incremental emissions/table interpretation, exclusion of
unchanged existing-use emissions, and the assumption that emissions from
buildings slated for demolition relocate within the Bay Area. This small case
tests table/footnote context and the distinction between a documented assumption
and substantiated support. Preserve the exact reviewed wording from the export;
these descriptions are only a planning summary.

| Alias | Stable claim ID |
| --- | --- |
| C001 | `claim07c1-949aa750-821d-498e-b78b-fc1d5e57cc5d` |
| C002 | `claim07c1-66621efb-3b18-4dd6-912a-c1b4d53d01b2` |
| C003 | `claim07c1-d1c1f248-1252-48f4-a79e-228e52163e08` |

Source wording is in the preserved response passage R01-P01, Final EIR Volume 4
physical page 101 (native task 122, annotation 126). This identifies what the
response said; it is not target evidence. The original three-card presentation budget is superseded by the fuller-review
revision below. Report actual burden before expanding.

## Review workflow and burden

Kyle requested one claim per task on 2026-09-25 after trying the case-level
prototype. Present the unchanged claim prominently with only its mapped evidence
and support controls. The reviewed question is visible immediately after the exact claim. The original
comment, established relevance and full response remain available as clearly labeled context. Preserve their source/claim links
without requiring another relevance judgment. Native Submit saves that claim
and advances to the next; a completed claim is not a completed case. Suspected
extraction errors become upstream follow-up findings.

For each claim, retain plausible deduplicated candidate passages for Kyle to
filter, with exact quotes, section/page labels and source links. Do not apply a
three-card cutoff: the questioned passage must remain visible. Put essential
context first and supplementary evidence afterward, with retrieval reasons
separate from source text. Shared passages may be displayed
once, but each claim-to-evidence judgment remains independent. Never silently
merge claims or truncate qualifying source context to fit a card.

Kyle chooses a relationship for each presented claim/passage pair:

| Judgment | Meaning |
| --- | --- |
| Supports | The passage supports the full claim, including material qualifications and scope. |
| Partially supports | It supports a specified part; record the supported part and remaining gap. |
| Context only | Useful background or topic overlap without supporting the proposition. |
| Contradicts | It conflicts with a specified material part of the claim. |
| Does not support | Readable passage, but no support for this claim. |
| Unusable / cannot judge | Source quality or ambiguity prevents a judgment; preserve the reason. |

Also record one claim-level outcome: supported, partial, conflicting,
no support found in this search, or unresolved. A set of passages may jointly
support a claim, but only through an explicit human judgment identifying that
set and its reasoning; do not infer aggregate support from individual labels.
Mixed supporting and contradictory passages remain visible. No candidates is
an explicit search gap, not a default review result or proof of corpus-wide
absence. Support for a supporting claim does not automatically support its
parent claim.

Default to clicks and optional notes. Require short clarification only where
needed to identify partial support, a contradiction, a combined-evidence
inference or an unresolved limitation; allow confirming a supplied explanation
rather than retyping it. No preselected human support or case approval. If Codex
suggests judgments, keep them visibly separate from human decisions and restrict
its citations to supplied, mechanically validated candidate IDs. Follow the
umbrella's user-started separate-task procedure for model proposals; no automatic
model/API execution. Record review time, candidate-card count, expansions and
corrections as observations, not targets Kyle must meet.

## Versioned records and exact provenance

Write fresh artifacts below `pipelines/brisbane_baylands/task_07_pilot/07d/`
under `ER_COMMONS_DATA_ROOT`; use no-clobber run identities. The implementation
must define explicit v1 schemas before generating discovery outputs:

- **Run/queue:** accepted result and export hashes, case and stable claim IDs,
  exact reviewed content bindings, exclusions, source/handoff/usability seals,
  discovery policy and code/config versions, terminal state and output inventory.
- **Discovery attempt:** claim IDs, original explicit-reference ID or exact query,
  filter and search scope, retrieval order, accepted hop path, errors, limits,
  overflow and reason for each expansion. Preserve unsuccessful attempts.
- **Candidate:** stable ID bound to source/version and ordered canonical anchors;
  semantic unit ID; physical one-based PDF pages and separate printed labels;
  exact block text spans using half-open Unicode offsets or canonical table/cell
  IDs with headers/units/footnotes; immutable quote and content hash; context
  anchors; source URL/license/retrieval metadata by sealed reference; usability,
  edition and text-only eligibility restrictions. Display aliases are not IDs.
- **Review:** claim/candidate/set IDs, separate machine proposals and human
  judgments, coverage/gaps, native annotation/reviewer IDs and timestamps,
  trusted task/form hashes, raw native export and normalized record. Revised
  candidates receive new versions; earlier decisions never silently transfer.

Preserve source bytes and accepted records in place. Routine reuse checks compact
seals and inventories; no deep PDF rehash or corpus rebuild. Candidate quote
validation checks the exact consumed canonical records. A source link or render
alone is not a sufficient anchor. Text-only support cannot depend on unreadable
figures or visual meaning absent from the canonical text.

## Research / learning checkpoint

Planning consulted these primary sources on 2026-09-25; this was method research,
not evidence discovery:

- [Label Studio Choices](https://labelstud.io/tags/choices) and
  [HyperText](https://labelstud.io/tags/hypertext): native classification and rich
  source display support a small form. Verify installed behavior in the real
  labeling queue; documentation alone does not prove saved field associations.
- [SQLite FTS5](https://www.sqlite.org/fts5.html): maintained phrase/Boolean search
  and BM25 ranking are a suitable lexical fallback if existing readers lack
  search. Check the installed runtime before choosing it. Ranking finds lexical
  matches; it cannot determine whether a claim follows from them.
- [W3C PROV overview](https://www.w3.org/TR/prov-overview/): distinguish source
  entities, discovery activities and reviewing actors. Apply those distinctions
  in compact JSON records without introducing a provenance framework.
- Local [canonical anchors](../../docs/specs/canonical_extraction_v1.md),
  [linking contract](../../docs/specs/document_linking_v1.md),
  [06H acceptance](06h_review_and_accept_replacement_handoff.md) and
  [07C.1 semantics](../../docs/specs/claim_relevance_review_v1.md) govern actual
  identity, source eligibility and preserved relevance decisions.

Learning to preserve: relevance asks whether a response claim addresses a
concern; evidence review asks whether a specific source supports what that
claim says. Exact links help locate evidence but do not answer the second
question. Bounded discovery makes review manageable while leaving uncertainty
visible.

## Validation, review pass and acceptance

Before trial import, verify exact approved membership and 31 unique queued
claim IDs in the existing handoff, excluding I-EA-2 and not-relevant claims.
I-CJ-4 is excluded and contributes no evidence claims. Mechanically
resolve every candidate to the pinned eligible source and exact quote/anchor;
reject wrong-version IDs, changed text, dangling links and unknown proposals.
Carry warnings into both the displayed packet and exported judgments.

In a separate QA project exercise support, partial/mixed evidence, zero hits,
unusable sources, overflow, save/reload and native export. Verify every decision
maps to the intended stable claim and candidate; unfinished work cannot export
as reviewed. Compare displayed text against canonical records and inspect
selected page renders only where needed. Run focused tests plus `make fix` and
`make check` for implementation; docs-only preparation uses `git diff --check`.
Obtain bounded independent review of provenance, semantics and UI behavior.

The prototype gate requires one tested case, preserved native/normalized records,
visible gaps, measured review burden and Kyle's explicit approval to expand.
Task completion requires all 31 currently accepted candidate claims to have human
reviewed evidence or an explicit reviewed gap/stop. Account for all six selected
cases and preserve both explicit exclusions.
Publish an immutable checksummed export and a handoff retaining all limits. Reviewed-with-gaps is not fully
supported, truthful, adequate, or benchmark-eligible. Do not hide gaps in later
answer prose.

## Non-goals

Re-reviewing the six completed cases' claim relevance, silently editing
07C.1, broadening source editions, fixing extraction, deciding Task 08 eligibility,
automatic truth/adequacy scoring, defense writing, or building a retrieval
framework. Expansion beyond the prototype awaits Kyle's review.

## Planning outcome (2026-09-25)

Verified the three hashes in the accepted result binding, all seven
export-managed file hashes and exact directory closure, and all seven proposal
hashes in the input index. Six approvals supply 31 candidates. Independent
planning review checked exclusion preservation, partial support, bounded search,
the two-hop ceiling and Final F1 qualification. Only this contract and current
routing were changed; accepted records and review projects remain untouched.

Kyle subsequently confirmed the workflow and SA-Caltrans-33 trial. Build and
validate that one case, then present it before seeking approval for expansion. I-CJ-4 is
restored to pilot selection with the prerequisite catch-up described above.


## One-case prototype handoff (2026-09-25)

The authorized SA-Caltrans-33 prototype is ready in
[project 13, task 128](http://127.0.0.1:8097/projects/13/data?labeling=1).
It shows the three exact approved claims, three shared evidence cards and five
claim/passage decisions, followed by three overall claim outcomes. No support
label, evidence set or case status is preselected. At handoff it has no human
annotations, drafts or predictions. The other cases have not been discovered.

Use the native Submit button to save and Previous task to reopen a completed
review. Notes remain editable after reopening. Complete the pair judgments,
select evidence used for each overall outcome, and mark Review complete or
Needs more context. Explanations are needed for partial support, contradictions,
unusable sources, unresolved outcomes and joint inference. The normalizer
checks these after export; native Submit alone is not acceptance. Wide tables
scroll horizontally; the shared-source and decision readers scroll separately.

### Source findings and preservation

E01 is Table 4.9-7, E02 is Table 4.9-8, and E03 contains the operational-emissions
narrative and full baseline/relocation footnote. Their physical PDF pages are
973, 975 and 974, respectively. Exact canonical blocks/cells and complete table
snapshots are preserved. Display-only header grouping was checked against the
PDF and is bound into the candidate version; it changes no canonical record.

The response's citation to footnote 15 on printed page 4.9-61 differs from the
located source: footnote **195 on printed page 4.9-62**, confirmed visually.
Keep the original response citation unchanged and the discrepancy explicit.
Only E01 had an accepted response-reference link. E02 was found by its supplied
page/caption; E03 by necessary neighboring context. No new graph links were
created and no lexical search or model support proposals were needed for this
trial. The packet cannot establish document-wide absence of baseline emissions,
independently reproduce modeling, or corroborate the relocation assumption.

### Artifact and validation handoff

All generated records are below the external Task 07 root:
`07d/sa_caltrans_33_trial_20260925_v1/`.

- `packet_v3.json` is the current source/claim-bound packet;
  `trial/prepared_task.json` and `trial/form.xml` are its trusted native inputs.
- `discovery/final_manifest_v2.json` is the corrected discovery seal. The earlier
  self-referencing manifest attempts and `packet.json` remain diagnostic history;
  they are not the current binding. `packet_v2.json` is the valid presentation
  predecessor. The root `manifest.json` identifies current versus diagnostic
  artifacts and seals this prototype handoff.
- `qa_renders/visual_qa.json` records three-page PDF checks by Codex, not human
  evidence approval. `trial/verification.json` records actual-queue source/claim
  fidelity and no default judgments. The original ten projects and bound
  accepted review files compare unchanged.
- Projects 11 and 12 are explicitly automated QA only. Saved native and
  normalized records test all six pair labels, all five outcomes, partial work,
  zero candidates, overflow, note editing and save/reload/export. They must
  never supply Kyle's support decisions. The initial UI was refined for readable
  table headers and editable reloaded notes before the human project was made.
- `make fix`, formatting, lint and typing passed. The final focused evidence
  suite passes **19 tests**. The full `make check` run had **2,666 passes and
  three pre-existing Task 06G failures**: unchanged historical tests expect a
  generator mismatch, but their pinned `ff561307` base differs from current
  `2b2b3a9`, so the unchanged commit guard fails first. No Task 06 history or
  validator was changed to bypass that boundary.

The [evidence-review v1 contract](../../docs/specs/evidence_review_v1.md) owns
packet and review semantics. `pilot_evidence` owns source verification, native
form preparation and normalized export; bounded discovery and local project
operations are preserved in the external run. Independent review verified
source anchors, selection boundaries and the corrected discovery seal.

Learning: explicit nearby references produced a small packet without indexing
the corpus, but their precision could not be assumed. Actual browser save/reload
also caught a note-editability problem that stored API results alone would miss.

Next: Kyle tries this example and gives workflow feedback before expansion.
I-CJ-4 remains selected pending its prerequisite reviews; I-EA-2 remains excluded.
No commit or push was performed.


## Claim-at-a-time revision (authorized 2026-09-25)

Kyle found one-claim-at-a-time review easier because relevance was already
established. Revise the same SA-Caltrans-33 prototype into three native tasks
in one separate project. Reuse the accepted evidence packet without discovery,
source changes or claim rewriting. Preserve project 13 and its exact state;
at revision start it had zero annotations and drafts. Its sealed prototype
remains historical. No expansion to other cases is authorized.

Use stable claim IDs and the original candidate aliases; show only evidence
mapped to the active claim. Keep question/response/relevance context optional.
Validate each saved claim separately, and require exact complete claim coverage
before any whole-case completion can be inferred. Shared evidence keeps its
identity, but support judgments remain claim-specific. Test three-task queue
navigation, different evidence counts, no unused controls, blank defaults,
save/reload and preservation before handing off the revised prototype.


### Revised prototype handoff

[Project 15, tasks 132–134](http://127.0.0.1:8097/projects/15/data?labeling=1)
is the current human queue. C001 displays E01/E02/E03; C002 and C003 each show
only E03. Submit advances in claim order. The approved relevance graph and
original question/response remain optional context, with exact wording preserved.
No new discovery or source changes were performed. Project 13 remains preserved.

The external `07d/sa_caltrans_33_claim_tasks_20260925_v1/manifest.json` seals the
revision and binds the original packet and predecessor manifest. `trial/` owns
the trusted tasks, form, import receipt and read-only browser verification.
`qa/` contains project 14's synthetic annotations, normalized records and
browser checks; none constitute Kyle's support review. At handoff, the three
human tasks contain zero annotations, drafts or predictions.

All 25 focused tests pass, together with formatting, lint and typing. Actual
browser QA verifies three sequential submissions, evidence counts of 3/1/1,
blank defaults, hidden inactive controls, separate saved notes and reload.
The preserved projects and predecessor managed files compare unchanged. The
previous full-suite Task 06G limitations above remain unresolved and unrelated.

Learning: the claim is the unit of support judgment after relevance review.
Keeping the complete packet in provenance preserves context without requiring
it on every screen. Shared source identity does not imply shared support labels.
Next: Kyle tries this revised queue before any expansion. I-CJ-4 remains selected
pending its prerequisite review; I-EA-2 remains excluded. No commit or push.


### Layout revision following Kyle's feedback

The current [review queue is project 17](http://127.0.0.1:8097/projects/17/data?labeling=1),
tasks 138–140. Project 15 remains preserved. Kyle flagged the prototype's
formatting: its long claim inherited 24px text with 20px line spacing. Form v2
uses 17px text with 1.55 line spacing, vertical choices, a wider source column,
separated decision groups, and background below the review. Evidence alone has
a bounded scrolling panel; decisions follow normal page flow. Exact claim and
source content, aliases, field names and label semantics remain unchanged.

`07d/sa_caltrans_33_layout_20260925_v1/manifest.json` binds this presentation
revision and its predecessor. Project 16 is synthetic browser QA only. Native
queue transitions, save/reload, hidden inactive fields, and unrated human tasks
were checked; all prior project snapshots and predecessor files remain unchanged.
Historical form bytes and normalized QA results reproduce exactly. No discovery
was performed. Human tasks have zero annotations, drafts or predictions at handoff.

Validation: 26 focused tests pass; formatting, lint and typing pass. The full
suite before the added regression test had 2,673 passes and the same three
pre-existing Task 06G commit-basis failures described above. The additional test
protects historical form-version provenance. No commit or push.


### Authorized context and discovery correction (2026-09-28)

Kyle clarified that citations are starting points, not the search boundary.
For SA-Caltrans-33, run the bounded lexical search beyond cited pages now, keeping
all previous packets/projects intact. Retain relevant corrected or omitted
citations even when the response itself did not supply them. Record the original
citation separately from the actual source location and classify the relationship
as supplied, corrected/mis-cited, or omitted. Citation classification does not
preselect evidence support. Footnote 195 on printed page 4.9-62 was already in
E03; it should be shown as a corrected citation, not only a search-gap warning.

The current question concerns the increase in operational emissions in Table
4.9-8; construction enters through the response's comparison with Table 4.9-7.
Show the exact approved claim first and its reviewed question immediately below.
Keep the verbatim original comment accessible, including preserved extraction
artifacts. Do not silently simplify or rewrite the accepted claim.

Place labeling controls and concise reviewer notes on the left, source excerpts
on the right. Clearly identify source quotations/tables and their citations;
curator explanations, search gaps, citation corrections and technical provenance
must not read as source text. Put technical audit history in collapsed provenance,
not inline warnings. Preserve meaningful source limitations separately. This is
an authorized revision of the same case only, not approval to expand the pilot.


### Context and broader-discovery handoff (2026-09-28)

[Project 19, tasks 144–146](http://127.0.0.1:8097/projects/19/data?labeling=1)
is the current prototype. Form v3 shows the exact claim followed by the approved
operational-emissions question; the verbatim comment expands nearby. Source
excerpts are on the right, with controls, citation corrections and reviewer notes
on the left. Technical provenance is collapsed. Original forms v1/v2 and all
prior projects remain preserved. No approved claim wording or relevance changed.

Nine recorded lexical queries searched 1,128,882 canonical blocks/tables across
34 eligible Draft EIR sources. Each query returned at most five ranked hits;
full indexed-file hashes match the accepted inventories. Query receipts retain
unsuccessful searches, truncation and rejected hits. GHG, construction-only and
other pollutant-context hits were not silently substituted for the operational
criteria-pollutant question. No claim of exhaustive corpus coverage is made.

The new E04 is an **omitted citation**: Draft EIR printed 4.9-57, physical page
969, heading/paragraph records `blk010575`/`blk010576`. It explains the analysis's
treatment of existing uses and why new-use emissions equal its net increase.
The printed label is bound to canonical footer `blk025391`. E03 is explicitly a
**corrected citation**: footnote 195 on 4.9-62, not the response's footnote15 on
4.9-61. These source relations are distinct from human support judgments.

C001 shows E01/E02/E04, preserving both tables it interprets and adding the
baseline explanation; E03 remains recorded overflow. C002/C003 each show E03/E04.
That is seven pair judgments across three tasks. The advisory mapping in the
search findings predates this final selection; `packet_revision.json` owns the
final mapping rationale. No new support labels are preselected or accepted.

Generated artifacts live under `07d/sa_caltrans_33_context_20260928_v1/`:
`packet_v2.json`, `trial/prepared_tasks_v2.json` and `trial/form.xml` are current.
`discovery/manifest.json` seals the supplemental search; the root manifest binds
that seal, current task data and historical prototype references. Initial
`packet.json` accidentally retained predecessor discovery-scope metadata; it
and initial task data remain diagnostic history. The scope correction changed
only metadata before human review, after verifying zero annotations/drafts.
`scope_correction.json` records that correction and the QA boundary.

Project 18 contains synthetic save/reload/navigation QA using the identical
rendered form; it is not human review. Final project19 data were reverified
against packet_v2 with zero annotations, drafts or predictions. Protected prior
projects and artifacts compare unchanged. Formatting, lint, typing and all 32
focused tests pass. Scoped independent review caught the stale search-scope
metadata before handoff; corrected scope is now explicit. Prior full-suite
Task06G limitations remain as recorded above. No commit or push.

Learning: following a response citation is a useful first step, but an uncited
methodology passage can clarify the proposition better than a cited footnote.
Keep corrected/omitted citation provenance visible without mixing curator notes
into citable text. Next: Kyle reviews this revised workflow before expansion.


### Fuller review authorized (2026-09-28)

Kyle prefers over-including plausible sources so he can filter them. He approved
trying this fuller review. Preserve the current project19 and build a separate
same-case revision. Include the questioned narrative on4.9-62, Table4.9-8,
Table4.9-7, footnote195 and baseline explanation on4.9-57. E03 already contains
both the narrative and complete footnote; keep their source identity and exact
text rather than inventing a redundant quotation. Show E03 first for C001.

Run a supplementary targeted search of accepted main-document air-quality
content and its G1 technical report for methodology, existing-emissions
estimates, and potential table differences. Budget six queries with up to ten
hits each plus necessary neighboring context. Retain all plausible material
candidates; keep rejected hits/reasons and search limits in discovery receipts.
Do not expand to other cases, infer support from retrieval, or silently rewrite
approved claims. The previous three-card cap is superseded for this trial.

Version the form to handle the explicit candidate inventory, preserve exact
historical form outputs, and test more than three candidates, filtering labels,
save/reload, and current provenance before handoff. This is authorization to
prepare the fuller prototype, not human approval of any evidence judgment.


### Fuller prototype handoff (2026-09-28)

[Project21, tasks150–152](http://127.0.0.1:8097/projects/21/data?labeling=1)
is the current fuller review. C001 shows E03/E02/E01/E04/E05/E06/E07 in that order:
the questioned narrative and its footnote first, then both tables, the uncited
baseline explanation, and supplementary methodology. C002/C003 retain E03/E04.
There are 11 pair judgments total, no hidden overflow and no preselected support.
The five core pieces occupy four cards because E03 includes both the narrative
and full footnote. Candidate aliases retain their earlier meanings.

Six further targeted queries searched 48,933 canonical records from accepted
`deir_main` and `deir_appendix_g1`, with ten hits per query and necessary
neighboring context. All four consumed canonical files have verified full hashes.
The additions are E05 (main4.9-55/56, operational sources and model assumptions),
E06 (main4.9-60, construction/operation timing and Table4.9-7 categories), and E07
(AppendixG1 4-8, construction/operation overlap). Exact excerpts, source identity,
query receipts, rejected hits and limits are sealed in the supplementary search.
These passages concern C001's table/model interpretation, not the existing-use
exclusion or relocation assertions, so they were not added to C002/C003.

The Phase1 operational totals differ between the tables (for example, NOx115.9
versus107.9 pounds/day). This is recorded as curator commentary beside the
review controls. The retrieved sources do not reconcile that difference; no
cause or human support outcome is inferred. No independent existing-emissions
inventory or relocation corroboration was identified in the inspected results.

Artifacts are under `07d/sa_caltrans_33_fuller_20260928_v1/`. The root manifest
binds `packet.json`, `trial/prepared_tasks.json`, `trial/form.xml`, the new
`discovery/manifest.json`, and prior accepted inputs. The G1 local PDF asset
points to its verified accepted source bytes. Formv4 allocates controls from the
full packet candidate inventory and binds that capacity to task/form provenance;
historical v1/v2/v3 forms retain exact bytes. All prior projects remain unchanged.

Project20 is synthetic browser QA only. Submit advanced through all three
claims, all seven first-claim controls and evidence choices were present, notes
saved/reloaded independently, and inactive controls stayed hidden for the two
smaller tasks. Human project21 contains zero annotations/drafts/predictions at
handoff. Formatting, lint, global typing and all39 focused tests pass. Scoped
independent review found no provenance/scope blockers. No commit or push.

Learning: a source-count cap hid the actual disputed statement. Candidate
ordering and explicit retrieval reasons allow a fuller packet without silently
removing context or implying that every retrieved passage supports the claim.
Next: Kyle filters this fuller example before expansion to other cases.


### Section-level citation correction authorized (2026-09-28)

Kyle accepts the findings and background inclusion but requires every displayed
source to be citable: narrative evidence must be keyed to its actual parsed
section heading and stop before the next section. Inspect parsed body text and
heading hierarchy, including adjacent boundary records, before rebuilding units.
Do not infer semantic units from PDF page ranges or curator-chosen bundles.
Keep tables as separately citable captioned units with complete headers/notes.
Preserve source/edition, full heading path, start/end boundaries, exact body
anchors and explicit attached footnotes. Exclude running headers/footers and the
next section; retain diagnostic boundary evidence outside the displayed quote.
Where canonical section assignments are too broad, record a local reviewed
boundary overlay rather than mutating accepted extraction records.

Prepare one fresh same-case prototype from these units, preserving project21
and its packet. No additional discovery or new support judgments are needed.
Splits/merges must carry a mapping from the previous evidence candidates so the
accepted findings and useful context are retained without silently dropping text.

The sprint plan already prefers whole leaf sections and separate table units,
and excludes context-only records from the direct-support coverage denominator.
Kyle's suggestion that context citations be optional is consistent with that
coverage policy. Keep all citations source-valid and preserve human per-claim
support/context labels; do not treat an optional-context citation as an invalid
citation merely because it is absent from required reference coverage. Any
separate context-retrieval metric or weighting remains a later proposed choice;
this task does not implement or freeze new evaluation metrics.


### Section-citation handoff (2026-09-28)

[Project23, tasks156–158](http://127.0.0.1:8097/projects/23/data?labeling=1)
is the current review. All findings and background sources are retained, now
organized as exact parsed section narratives and separate table citations. C001
has11 units; C002/C003 each retain2 (15 total judgments). The questioned narrative
remains first. No discovery or human support labeling was performed in this
revision; prior projects and packets remain preserved.

The boundary audit found E05 crossed five real headings, so it is now E05
(Operational Activities and Emissions), E08 (Operational On-Road Mobile Sources),
E09 (Emergency Generators), E10 (Architectural Coatings), and E11 (Consumer
Products). E06 was missing its heading/opening; both are restored, so its cited
pages are now4.9-59/60. E03 ends before Regional Mobile Source Emissions Based
on VMT. Its Table4.9-8 and associated notes are explicitly accounted for in E02.
Similarly, E06's Table4.9-7 belongs to E01. E04/E07 already matched their parsed
heading boundaries. No source wording was rewritten to make these boundaries.

The new `pilot_citation_units` validator verifies actual section records,
breadcrumbs, complete ordered narrative membership, exclusive next headings,
separate complete table units and source-document consistency. Labels are exact
canonical headings/captions plus printed pages; full section paths expand in the
source pane. Current packetv2 requires this metadata. Historical packetv1 and
formv1–v4 remain supported; formv4 XML is unchanged and capacity remains bound.
The bounded table association rule supports these section-tail tables and fails
unsupported layouts rather than silently guessing note membership.

Artifacts are under `07d/sa_caltrans_33_sections_20260928_v1/`. The root manifest
binds `packet.json`, `packet_revision.json`, current trusted trial data/form,
and `boundaries/manifest.json`. Boundary evidence includes section snapshots,
next-heading anchors, accepted file/completion seals, and printed-label checks.
The replacement mapping preserves predecessor IDs; provisional audit labels/IDs
are normalized to deterministic source-derived citations before final preparation.

Project22 is automated QA only. Browser Submit/save/reload and all11 first-claim
controls pass; final human project23 has zero annotations/drafts/predictions.
Canonical boundary validation and independent review pass. Formatting, lint,
global typing and53 focused tests pass. Prior full-suite Task06G limitations
remain as recorded. No commit or push.

Context-only units stay citable and available for review, while the sprint's
existing primary direct-support coverage excludes them from its denominator.
Optional context does not excuse citation inaccuracy or replace substantive
support. No new metric formula or weighting was implemented. Next: Kyle reviews
the section-based prototype before pilot expansion.


### Simplified final outcome authorized (2026-09-28)

Kyle has completed the E* judgments in the first claim and requests removal of
Evidence used for overall outcome and the separate This claim review question.
Keep one explicit Overall outcome for this claim with its explanation field.
Preserve all source-level labels/notes and any explicit overall outcome already
entered. A saved draft was found for project23 task156:11 pair judgments plus
Supported overall; it must migrate as a draft, not be submitted by Codex.

Version the form/normalizer. Current export retains each human pair judgment and
explicit overall outcome, with mechanical completeness validation; it must not
invent an evidence-selection decision or a second human approval/status. The
existing pair explanations and basic outcome consistency checks remain. Unresolved
is an explicit overall outcome with an explanation. Incomplete drafts remain
unfinished rather than receiving inferred support or approval. Preserve historical
forms/reviews and the full original draft including removed fields as provenance.

Prepare one fresh review project, copy only retained native fields from the
latest saved draft with exact values, verify the original remains unchanged,
and check browser draft resume without submitting human work. Test the simplified
Submit/export path separately in a synthetic QA project. No source discovery,
claim edits, citation changes or metric changes are part of this revision.


### Simplified-outcome handoff (2026-09-28)

[Project25, tasks162–164](http://127.0.0.1:8097/projects/25/data?labeling=1)
is current. After E* judgments, only Overall outcome for this claim and its note
remain. The evidence-selection checklist and separate This claim review/status
are removed. Source content, section/table citation boundaries and claim wording
are unchanged. New formv5 and normalized reviewv2 preserve all historical forms
and original review rules for older artifacts.

Kyle's saved project23/task156/draft31 contains11 source judgments and Supported
overall. Those12 retained fields were copied exactly into the first new task as
a draft. The removed evidence-selection field remains in the original snapshot
and migration receipt. Original IDs, timestamps, results and source bindings are
preserved. No human annotation was submitted, and the other two new tasks remain
unrated. The source-level draft includes4 supports and7 context labels; these
are preserved human inputs, not new Codex proposals or finalized benchmark labels.

Artifacts are under `07d/sa_caltrans_33_simple_20260928_v1/`. `packet.json` is
byte-identical to the section-based predecessor. `migration/receipt.json` owns
original/destination identities and retained/removed field mapping. The root
manifest binds initial snapshots, trusted tasks/form, migration and verification.
Protected comparisons ignore only the server's computed `created_ago` string;
actual judgment content and native timestamps remain exact.

Project24 is synthetic QA only. Browser Submit advances with no status or
selection fields, exports normalize without fabricated human status/evidence
sets, and saved notes reload. Final browser verification checks that the first
human draft restores all12 retained choices without submission and removed
controls are absent. Global formatting/lint/typing and74 focused tests pass.
A broad run had2,718 passes and the same3 pre-existing Task06G base-commit failures.
No source discovery, metric changes, commit or push were performed.

Next: Kyle continues the preserved draft and uses Submit when ready.


### Case-level citation export authorized (2026-09-28)

Kyle observed repeated section citations across claims and chose a separate
case-level citation list for evaluation. Deduplicate canonical section/table
units and retain the strongest approved role: support takes precedence over
context, whether the supporting use concerns a direct or supporting claim.
The benchmark output does not require claim-to-citation links or a partial
support citation level. Preserve native claim-level reviews as provenance.
See the specification's export decision for identity and unresolved-label rules.
This turn records the contract only; it does not submit reviews, change the form,
export finalized labels, or expand discovery. Next implementation should verify
submitted reviews, version the exporter, and test deduplication and aggregation.


### Repeatable search procedure (2026-09-28)

Kyle requested a more repeatable process for the remaining cases and future use.
[Search protocol v1](../../docs/specs/task07d_search_protocol_v1.md) now defines
fixed inputs/index settings, purpose-based queries, controlled follow-up, exact
citation assembly, an agent prompt template and required replay records. It
retains block/table retrieval and section/table citations, with one case-level
pool and separate final claims. The ten-hit default follows the fuller prototype;
it is an operational choice, not an evaluated optimum. Independent review covered
input binding, counterevidence, budgets, unit boundaries, deduplication and gaps.
SQLite primary documentation informed syntax and index-statistics decisions.

This was documentation work; no additional case search, persistent index,
review submission or search CLI was run/built. Before future execution, apply
this protocol in a bounded implementation with replay and provenance checks.
Historical SA-Caltrans-33 runs are not retroactively certified as protocol v1.
Validation: inspected the documentation diff and passed `git diff --check`.


### Durable per-claim assignment (2026-09-28)

Kyle clarified that repeatability requires the exact per-claim sub-agent prompt,
including section-level citation instructions, to survive the chat. The full
[dispatch template](../../docs/prompts/task07d_claim_citation_search_v1.md) now
owns that assignment. It includes bound claim/question placeholders, all search
stages, actual heading-to-next-heading boundaries, complete tables/notes, exact
provenance, separate agent commentary, deduplication, gap reporting and a lead
restart checklist. The protocol links to this template instead of a shorter
competing prompt. Index and TODO route future agents directly to it.

Save every filled assignment and its hash/agent identity with the run. This is
authoring guidance with curator-only inputs, not the future evaluation prompt;
shared citation/output conventions do not authorize leaking reference claims or
labels to the target model. No new discovery or model evaluation ran. Documentation
links and `git diff --check` were verified. Independent prompt review passed
after aligning document-end handling with the current validator and making
assigned reference IDs explicit.


### Remaining-case execution authorized (2026-09-28)

Kyle requested labeler tasks for the other valid MVP questions using the saved
protocol and per-claim assignment. This authorizes discovery and fresh labeler
projects for O-Joint-19, O-GGBA-2, M-OSEC-273, PC-LM-2 and I-CF-4 (28 claims).
Verify current reviews and inputs, bind one full eligible-source index, save the
filled prompts per claim, delegate bounded searches, validate section/table units,
and import blank human tasks only after separate QA. Preserve prior projects and
all human decisions. Inspect I-CJ-4's prerequisite status; prepare catch-up review
as needed without fabricating concern or relevance approval. No human submission,
commit or push is authorized.

Artifacts use fresh `07d/remaining_cases_20260928_v1/`; completion manifests must
identify ready cases, unresolved source gaps and pending prerequisite cases.


### Remaining-case labeler handoff (2026-09-28)

The authorized expansion is ready for human review. The tracked
[queue result](../../docs/specs/task07d_remaining_result.json) binds the sealed
`07d/remaining_cases_20260928_v1/manifest.json` and its summary.

| Case | Claim tasks | Review |
| --- | ---: | --- |
| I-CF-4 | 11 | [Open project 36](http://127.0.0.1:8097/projects/36/data?labeling=1) |
| M-OSEC-273 | 2 | [Open project 30](http://127.0.0.1:8097/projects/30/data?labeling=1) |
| O-GGBA-2 | 2 | [Open project 29](http://127.0.0.1:8097/projects/29/data?labeling=1) |
| O-Joint-19 | 10 | [Open project 35](http://127.0.0.1:8097/projects/35/data?labeling=1) |
| PC-LM-2 | 3 | [Open project 33](http://127.0.0.1:8097/projects/33/data?labeling=1) |

These 28 tasks contain 151 source judgments over 104 citation
units across cases. Every new human task was verified blank, with exact prepared
data and no annotations, drafts or predictions. Browser checks opened each case,
verified controls/source cards and source PDF availability. Synthetic QA projects
27/28/31/32/34 separately exercised Submit and normalized exports.

Discovery used one frozen SQLite FTS5 index (1,136,626 records, 35 eligible sources),
84 baseline queries and 22 bounded follow-ups. The run preserves 28 full rendered
assignments, dispatch/input hashes, query receipts, hit dispositions, source
selections, parsed-boundary inspection and review-ready packets. All 35 canonical
source inventories and the accepted 07C.1 managed input closure were checked.
Dispatch-time instructions remain saved even though current routing now reports
execution complete. Relevance labels guided scope and did not become support labels.

Exact source assembly required bounded extensions: reviewed table associations,
one source-bound correction for Section 8.5.2 where a running header split the
actual section, and figure-location links in complete text sections. Original
canonical records remain untouched. See the boundary note and evidence specification.
Incomplete table fragments and unsupported section boundaries remain explicit gaps.
Printed citation labels and supplied/omitted reference metadata were checked and
corrected before final verification, with predecessor packets/receipts preserved.
No claim wording or human judgments were changed by these corrections.

Known search limits include unverified historical RHNA/census/ABAG details,
energy-report vintage/best-available assertions, and some exact traffic dimensions
and timings. Conditional findings and conflicting material remain visible: mitigation
qualifies some conclusions, regional and project traffic effects differ, and the
40 percent traffic reduction is a specific PM movement rather than a regional total.
These are review candidates, not verified truths or exhaustive document absence.

I-CJ-4 project26/task165 is a fresh 07B concern catch-up with no human input;
original task103/annotation107 remain unchanged. It must pass 07B and 07C.1 before
joining evidence discovery. I-EA-2 remains excluded with history intact.
SA-Caltrans-33 project25/tasks162–164 were submitted (annotations150–152).
The first two normalize; task164 has an unexplained partial E03 rating and cannot
yet produce a valid export. Native annotation152 is preserved for Kyle to resolve.

Validation: formatting, lint and global typing passed; focused checks passed
95 tests with one FTS5-runtime skip. The same FTS5 search tests passed all three
under the system interpreter with FTS5 enabled. Final browser/API verification
passed for all 28 blank tasks and all six linked source PDFs. No final benchmark
labels, commit or push were produced. Task07D remains active for human review and
implementation of the agreed deduplicated case-level citation export.

Learning: fixed retrieval inputs and query receipts make the search auditable,
but do not make it exhaustive. Full parsed sections provide stable citation
identities; source-specific boundary repairs need separate receipts instead of
silently altering canonical extraction. Human review remains the support gate.

### I-CJ-4 editable suggestion repair (2026-09-28)

Kyle reported that “Your reviewed list” was blank. Catch-up task165 had retained
its original proposal only in the collapsed source panel; the importer omitted
the prediction that prefills the editable concern list. Restored the exact
`proposal_text` as a `task07b.questions.v1` prediction and selected that prediction
version on project26. No review status is preselected and no human annotation or
draft was modified. Before/after snapshots and the repair receipt are saved in
`07d/icj4_suggestions_20260928T190634Z/`, separate from the sealed expansion run.
The earlier blank-task receipt remains a historical snapshot.


### I-CJ-4 excluded again by user decision (2026-09-28)

Kyle revisited the comment and explicitly said it should be ignored. The original
07B disposition already recorded his choice to skip it as unclear; 07C and 07C.1
carried that exclusion. His subsequent “I-CJ-4 should be included” instruction
caused the 07D reopening. This latest decision supersedes that reopening.
Project26/task165 and all prior artifacts remain historical; no catch-up review
is required. Current pilot membership is six cases/31 claims, unchanged from the
accepted evidence-ready queue. The sealed remaining-case manifest is a historical
snapshot; the tracked queue result carries this later selection disposition.


### User-authorized Label Studio cleanup (2026-09-28)

Kyle requested removal of stale projects to reduce database load. Preserved the
six current evidence projects (25,29,30,33,35,36) and all 31 native tasks, including
new human submissions. Archived and deleted the other 30 projects through the
local Label Studio API, including obsolete prototypes, synthetic QA, completed
07A/07B/07C/07C.1 queues, and excluded I-CJ-4 catch-up. Older live-project links in
historical task records now refer to archived projects, not active queues.

`maintenance/label_studio_cleanup_20260928T192837Z/` under the Task07 artifact root
owns the full consistent SQLite backup, all removed project configurations and
exports/full task snapshots, enumerated deletion receipt, preserved-task checks
and manifest. The backup passed SQLite integrity validation before deletion.
All current native task data, annotations, predictions and drafts matched before
and after cleanup (excluding volatile UI metadata). Earlier sealed artifacts were
not modified. Database compaction reduced 185,622,528 bytes to 59,949,056 bytes;
integrity checks passed. This establishes reduced storage and project count,
not a measured improvement in interactive performance.


### Completed human labeling and relevance lesson (2026-09-28)

Kyle reported labeling complete and observed that irrelevant claims had leaked
through the earlier relevance review. All 31 submitted native annotations were
exported from projects25/29/30/33/35/36 to fresh
`07d/reviews/six_case_export_20260928T210030Z/`. Trusted prepared task data matched
exactly. The manifest binds project snapshots, native exports/full tasks, trusted
tasks, normalized reviews, reviewer notes and per-case validation errors.
The [tracked export status](../../docs/specs/task07d_review_export_status.json)
is the current handoff checkpoint, not a finalized benchmark artifact.

The current validator accepts 26. SA-Caltrans-33 task164 retains the unexplained
partial source rating. O-Joint-19 task184 (C010) has five context sources and a
partial outcome; task185 (C011) has five context sources and a supported outcome.
I-CF-4 task195 (C011) has six context sources and a partial outcome; task197
(C013) has four no-support and two context sources and a partial outcome.
No written review notes were present. Preserve these judgments and resolve their
meaning against the newer separate claims/citation export policy rather than
silently changing labels or declaring the current validator obsolete wholesale.

Future relevance review should distinguish “same topic” from “answers this
concern.” For direct claims, name the specific question answered, preserving
phase/time/geography (for example construction versus long-term operation).
For supporting claims, state the reasoning connection and ask whether removing
the claim would materially weaken the relevant answer. General background and
incidental response assertions should not enter evidence discovery merely because
they share vocabulary. Split mixed-relevance claims before approval. Continue to
show all substantive extracted claims for human review; retain excluded claims
in history rather than deleting them. Helpful background source citations can
still appear as optional context without making every background response claim
an evidence-search target. This is a tighter application of existing semantics,
not authorization to relabel or remove unspecified current claims.


### User disposition of review flags for MVP (2026-09-28)

Kyle confirmed SA-Caltrans-33 C003 remains supported and its previously partial
E03 source should be context. A separate clarification overlay records that one
change; native annotation152 and the sealed source export remain unchanged.
The effective review passes the strict validator, bringing that count to 27.

For O-Joint-19 C010/C011 and I-CF-4 C011/C013, Kyle said the source labels were
intentional and the claims were probably not relevant, but explicitly instructed
us not to drop claims or reopen claim labeling. Retain all 31 claims with their
accepted wording and relevance. Retain the four original overall outcomes and
source ratings as submitted. Their inconsistency is an explicitly accepted MVP
limitation, not a repaired judgment or a strict-validation success.

`07d/reviews/mvp_disposition_20260928T211718Z/` binds the user's disposition,
exact task/claim/candidate identity for the correction, effective derived review
and source-export hash. The tracked export status routes to this additive record.
No native Label Studio annotations were modified. Case-level citation aggregation
must use actual source labels: support takes precedence over context across uses;
overall outcomes cannot manufacture support. Rejected sources do not become
context by default. Carry the four warning identities into the final handoff.
These flags require no further clarification; final export implementation remains.


### Final case-level citation export (2026-09-28)

Kyle authorized building the separate case-level citation exports. The
[final result](../../docs/specs/task07d_final_result.json) binds the sealed export
under `07d/exports/case_citations_20260928_v1/`. Each case JSON keeps its complete
accepted claims separately from a deduplicated citation pool, with exact source
provenance. Detailed claim/citation links and all native judgments remain in audit.

| Case | Claims | Support | Context |
| --- | ---: | ---: | ---: |
| I-CF-4 | 11 | 14 | 17 |
| M-OSEC-273 | 2 | 5 | 1 |
| O-GGBA-2 | 2 | 7 | 2 |
| O-Joint-19 | 10 | 9 | 12 |
| PC-LM-2 | 3 | 4 | 2 |
| SA-Caltrans-33 | 3 | 4 | 7 |

Totals: 31 claims, 84 citations, 43 support and 41 context. Evidence judgments
alone determine citation levels; support wins over context across uses of one
semantic section/table. Rejected candidates remain in audit rather than being
silently relabeled context. Every claim is byte-content equivalent as a JSON
object to its accepted 07C.1 record. Context remains optional for required coverage.

The exact task164 partial-to-context clarification is a derived annotation,
separate from the preserved native annotation. Four accepted MVP warning tasks
184/185/195/197 retain all submitted labels and outcomes. Neither their relevance
nor their evidentiary status was repaired by inference. Inherited discovery gaps,
source qualifications and the accepted Final F1 substitution remain visible.
This completes the bounded evidence-authoring task, not benchmark eligibility,
truth/adequacy certification, an evaluated retriever or answer-logic review.

Input verification covered review/disposition manifests and managed closure,
the accepted 07C.1 handoff and exact 31-claim membership, trusted task equality,
canonical source anchors and section/table boundaries. An independent pass compared
the final citation pools directly to native choice fields, applying only the user
clarification, and verified uniqueness and unchanged claims. Independent code
review caught a presentation-label equality issue; the final adapter permits that
variation while rejecting structural differences. The legacy prototype's missing
top-level extraction ID is derived from verified canonical records. An incomplete
first attempt is preserved under `initial_attempt/`, clearly excluded from final
case selection. Final payloads are only under `cases/`.

Validation: global formatting, lint and mypy (567 source files) passed; 115 focused
tests passed, including 22 aggregation tests for support precedence, claim-order
independence, section/table identity, structural conflicts, missing/unknown reviews,
partial-only stops and legacy source bindings. No runtime dependencies were added.
No live reviews, canonical sources, earlier sealed releases, commit or push changed.

Learning: case-level citations simplify evaluation but lose explicit attribution
in the benchmark payload. Retaining a separate complete audit permits that simpler
output without losing how labels were obtained. Source-level ratings remain the
authority when overall outcomes conflict under an explicit bounded MVP exception.
Next is the provisional 07E answer-logic contract; no 07E execution began here.


### Final handoff validation and acceptance seal (2026-09-28)

At Kyle's explicit request, revalidated the already sealed exports without
modifying them. The [acceptance receipt](../../docs/specs/task07d_handoff_validation.json)
binds the final-result hash and a separate immutable validation manifest under
`07d/handoffs/validated_20260928T212334Z/`.

Verified exact managed-file closure and SHA256 for all 42 export files, the native
review release, user disposition and accepted 07C.1 inputs. Current implementation
hashes match the sealed export. Revalidated all canonical candidate anchors and
section/table units; hashed all six linked original PDFs against their bound source
identities. Recomputed each case's citation pool from the effective reviewed inputs
and compared it exactly to the export. All 31 claims and reviewed concerns match
the accepted claim handoff; totals remain six cases and 84 citations (43 support,
41 context). The only effective annotation difference is the authorized task164
partial-to-context clarification. Exactly tasks184/185/195/197 carry the accepted
MVP warnings. I-EA-2 and I-CJ-4 remain excluded.

The new receipt and validation script are independently sealed and reverified.
Prior exports, native annotations and sources remain unchanged. Existing successful
115-test validation remains applicable because no implementation changed. The
handoff is ready for the next task with its explicit limitations; this is not a
claim that all review inconsistencies disappeared or benchmark eligibility passed.


### Required maintainability gate reopened (2026-09-28)

Kyle explicitly requires a code-quality pass before closing 07D. The sealed
exports remain valid historical results, but their completion alone is insufficient.
Review the Task07D modules for understandable responsibilities, duplicated logic,
clear invariants/errors, resource handling and a reproducible maintained export
entrypoint. Preserve sealed sources, native labels and export semantics. Validate
focused refactors with meaningful tests and exact reproduction of case payloads;
record current implementation hashes separately from the immutable old release.


### Required maintainability pass completed (2026-09-28)

The [code-quality result](../../docs/specs/task07d_code_quality_result.json)
binds current code, checks and exact output reproduction separately from the old
export seal. The [maintainer guide](../../docs/task07d_maintainer_guide.md) documents
module ownership, invariants, failure diagnosis and the maintained replay command.

The cleanup separates native form rendering from task/provenance/normalization
logic, removes markup-string splitting as a source/curator boundary, centralizes
canonical record operations, and leaves audited version-specific citation policy
in its owning modules. Search now explicitly closes SQLite connections on success
and failure and reports source filename/line on malformed JSON. Full frozen-index
verification remains; no unsafe trust cache or unmeasured performance claim was added.

`pilot_case_export` and `make export-pilot-case-citations` replace the historical
machine-specific run script as the maintained interface. Named typed functions own
input verification, clarification, normalization, case assembly and publication.
A structured `ReviewValidationError` exposes the normalizer's rejected result,
so permitted warnings no longer require a second native-control parser. Only the
manifest-bound exact task/error signatures are accepted. All native judgments
remain available; the clarified effective annotation is explicitly separate.

Independent review found and verified fixes for unsafe case filenames, duplicate
identities, missing clarification coverage and output nested inside sealed inputs.
The exporter rejects all three sealed input roots (native reviews, dispositions,
accepted claims), refuses existing output directories, and writes its completion
manifest last. Failed attempts remain unsealed and cannot overwrite prior results.
These are concrete failure-handling improvements, not a new orchestration framework.

Validation: `make fix` made no additional changes; global format/lint and mypy
(570 source files) passed. The complete scoped selection passed 158 tests with one
FTS5 runtime skip; all four search tests passed under the FTS5-enabled system
runtime, including that integration path. Historical/current form hash regressions
and a pre-refactor prepared-task snapshot preserve layout/task outputs. Evidence/
forms, citation-source helpers and export orchestration received independent review
with no remaining blockers. The final maintained-command replay regenerated all
six case JSON files byte-for-byte: 31 claims, 84 citations, unchanged source labels.
The previous export's exact 42-file closure and hashes also still verify.

Current code, tests, docs and replay evidence are sealed under
`07d/quality/maintainability_20260928_v1/`. The original final result and acceptance
seal remain immutable historical lineage; code hash changes are recorded in this
separate quality result. Historical layouts remain for actual archived callers;
JSON dictionaries remain the artifact format, with narrow typed functions instead
of a premature model/framework rewrite. No runtime dependency, new discovery,
relabeling, commit or push was introduced. The required maintainability gate is
now satisfied; 07D can close with its already accepted MVP limitations.
