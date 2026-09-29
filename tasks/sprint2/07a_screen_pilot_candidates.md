# Task 07A: Screen Pilot Candidates

Status: **Complete: 50 verified human decisions and eight selected authoring cases.**

## Abstract and goal

Prepare a coverage-oriented sample of 50 comment-rooted cases from the accepted
Task 05H inventory for Kyle to review directly in Label Studio. Identify 6–10
promising cases for the rebuttal-authoring pilot. This is a human-only pilot-fit
screen, not Task 08 eligibility or an automated filter of the whole inventory.
There was no model-generated fit-label step. Codex later used substantive
judgment to select examples from Kyle’s Great cases; see the
[process note](#process-note-how-this-batch-was-actually-run). The
[Task 07 umbrella](07_pilot_reference_case_authoring.md) owns later authoring stages.

## Inputs and review unit

Pin the [05H accepted handoff](../../docs/specs/task05h_final_result.json), its
resolved individual/general-response views, relationship IDs, reference warnings,
and matching source-usability information. Preserve the inherited limitations
in the [05H summary](../../docs/specs/task05h_final_summary.md).

One case is one distinct comment plus its complete linked response context:

- Include all linked individual responses and required linked general responses,
  keeping their source IDs and anchors visible.
- A comment with several responses counts once. Different comments sharing a
  response remain distinct; preserve that shared relationship.
- Follow accepted relationships; do not invent one-to-one pairs or remove
  inconvenient parts of a response to improve fit.

## Sampling plan

Select 50 unique comments: 40 for source coverage and 10 for challenging cases.
Use accepted metadata to prepare the sample without rating the whole inventory.

For the 40 coverage cases:

- Aim for 2–3 comments per general response, where available. Favor breadth
  across general responses before adding second or third comments if space is tight.
- Within those choices and remaining slots, seek roughly even coverage across
  cited appendices and extra representation of the main report. Include cases
  without general-response links as well.
- Treat general-response and cited-document coverage as overlapping goals: one
  case can cover several documents, but counts only once toward 50. Preserve
  all its citations rather than assigning it an artificial single target.
- Use available counts to set a simple main-report allocation and resolve sparse
  groups before drawing the sample. Save those settings and a fixed seed for
  tie-breaking; do not silently substitute citation mentions for comment counts.

Choose the remaining 10 from unselected comments to cover unresolved references,
potentially unavailable evidence, and other difficult response contexts. Warning
presence selects cases for attention; it does not automatically rate them.
Record coverage shortfalls rather than manufacturing cases to satisfy a quota.
Do not assume topic labels exist or add model-based topic classification.

This is a purposive MVP sample for authoring coverage, not a population estimate
of fit or eligibility. Source citation coverage does not prove evidence support.

## Review form and criteria

Show the original comment, full linked response context, source anchors,
explicit references, and inherited source/reference warnings. Kyle decides every
case directly; no prefilled model ratings, required rationale, or typing fields.

Required single-choice pilot fit:

| Value | Meaning |
| --- | --- |
| `great_fit` | Clear substantive concern, identifiable complete response, manageable scope, plausible Draft EIR evidence-checking path, and no apparent skip condition. |
| `ok_fit` | Promising rebuttal material, but needs more interpretation, response context, evidence searching, or qualification. |
| `skip_for_pilot` | Unsuitable for this initial rebuttal pilot because of a listed reason or another curator judgment. |

For Skip, offer optional fixed-choice reasons, allowing multiple selections:

| Reason | Meaning |
| --- | --- |
| `document_change` | The response says the comment results in any document change, including minor corrections. Skip because this pilot focuses on rebuttals. |
| `external_document_unavailable` | The response cites an external document unavailable in this dataset. This is itself a pilot skip reason; proof that the answer depends on it is not required. |
| `unavailable_evidence` | Required evidence appears unavailable or unusable for another reason. |
| `requires_visual_interpretation` | Answering appears to require visual evidence unavailable to the text-only target. |
| `not_useful_question` | The comment is unclear or does not offer a useful substantive question for this pilot. |
| `too_complex` | Too many intertwined issues, response dependencies, or too broad an evidence search for the initial pilot. |
| `other` | Another reason to skip; no explanation required. |

Document change and unavailable external document are skip reasons, not separate
response flags. A recognized instance of either receives Skip. Other dependencies,
including visual requirements, may only become apparent in later evidence review;
do not require a deep evidence investigation during screening. An unresolved link
or figure mention alone does not prove required evidence is unavailable.

A submitted Skip is a completed decision even without reasons. An unreviewed or
pending case is not a Skip and does not count toward 50. A good case omitted from
the final 6–10 remains Great or OK; selection is separate from its fit rating.

## Plan and lightweight handoff

Sampling and the approved 50-case import are complete. The user approved the
one-case UI and authorized importing all 50 comments. Existing global projects
and subsequent human decisions must be preserved. The original planned workflow
is below; the process note distinguishes actual execution from this plan:

1. Pin the inputs, inspect available sampling metadata, and save the sample and
   compact sampling settings under `ER_COMMONS_DATA_ROOT`.
2. Prepare one Label Studio screening project with a small form/schema and only
   the import/export helpers needed for this task. Round-trip a tiny fixture
   before using real cases.
3. Kyle reviews five varied sampled cases to calibrate the form and definitions.
   If they change, save a new form version and revisit those five under it.
4. Complete all 50 human decisions. Export and reconcile them against the saved
   sample, preserving pending cases and avoiding overwritten review exports.
5. Select 6–10 cases for quality and variety across issues, general responses,
   and cited sources. Prefer great fits; if the pool is inadequate, review another
   named batch before selecting. Record a short selection explanation and hand
   the selected IDs plus reviewed decisions to 07B. Do not start 07B here.

Keep records proportional to the MVP: one sample/settings record, a mapping from
Label Studio task IDs to comment and related source IDs, versioned human exports,
selected case IDs, and a short coverage/fit-count summary. Bind decisions to the
input and form versions and retain reviewer/time metadata from the export.
Human screening required no per-case prose rationale, elaborate activity logs,
Codex rating packet, or model-rating prompt. The separate judgment-based example
selection is documented in the process note and reusable prompt below. Generated records
stay outside Git per the [artifact contract](../../docs/data_artifacts.md).

## Research / learning checkpoint

Before building the form, check the installed Label Studio edition/version against
its official [Choices](https://docs.humansignal.com/tags/choices),
[import](https://docs.humansignal.com/guide/tasks), and
[export](https://docs.humansignal.com/guide/export) guidance. Verify the fixture
supports a required rating, optional multiple skip reasons, and a full export
reconciled to the sample, including tasks without completed annotations.
Explain briefly why citation coverage guides sampling while evidence sufficiency
and formal eligibility remain later judgments. Pre-annotation research belongs
to the first later stage that uses Codex proposals.

## Validation, review, and acceptance

Check unique comment IDs, complete accepted response relationships, reproducible
sampling, valid fit/reason values, source-ID mappings, and exported counts.
Reasons belong only to Skip; reasons may be empty and Other requires no text.
Review the form for click-only usability and the sample for coverage before
screening. Accept execution when at least 50 cases have human decisions and the
small pilot selection and short coverage summary are recorded. Planning changes
require diff review and `git diff --check`; implementation uses the repository's
`make` checks.

## Non-goals

The current authorization covers sample selection, the approved UI, and loading
all 50 cases. Human screening decisions belong to Kyle. No model screening, complete-inventory substantive review, formal Task 08 eligibility,
question authoring, deep evidence verification, or changes to accepted upstream
artifacts are part of 07A.

## Sampling outcome

Selected 50 distinct comments (40 coverage, 10 challenge) from the pinned 05H
inventory, with seed `20260923`. The external sample is under
`pipelines/brisbane_baylands/task_07_pilot/07a/sample_20260923_v1/` relative to
`ER_COMMONS_DATA_ROOT`: `selected_comments.md` contains the original comments;
`sample.jsonl` binds their IDs and context; `review_context.jsonl` is a derived
text view; `selection_manifest.json` and adjacent sampling scripts preserve the
compact settings, input references, counts, and reproducible selection.

The sample spans 29 submissions, all seven general responses with accepted
comment links, and all 17 appendix families with recorded citation routes.
There are 25 cases with main-report citations in the comment/direct-response
context. Appendix counts are 1–3 each; sparse groups prevent equal coverage.
General-response counts are 2–3 except General Response 4 (6), due to overlapping
coverage and challenge choices. General Response 2 had no accepted comment-rooted incoming links in the sampling
view (its text nevertheless names comments); General Response 9’s subject
was routed to Volume 5, Chapter 16. F1 remains a warned Final-EIR
substitution, not verified Draft evidence. No missing relationships were invented.

Sampling used accepted bounded views for general-response coverage. Saved review
context additionally follows directed response/general-response references to
closure (adding context for seven selected comments), without pulling other
comments through shared responses. Original accepted view IDs remain separate.
At sampling time all 50 cases were pending; no automatic labels were assigned.

Validation: accepted pointer and compact seals, exact release file inventory and
component sizes, 50 unique IDs with 40/10 membership, artifact hashes, and an
in-memory replay matching all saved selection rows. The completed human export is recorded below.


## One-case UI trial

Prepared an isolated Label Studio Community 1.23.0 environment and database at
`pipelines/brisbane_baylands/task_07_pilot/07a/label_studio_trial/` under the data
root. Project 1 contains only I-CJ-4 (task 1), with its direct response and linked
General Response 4. The global Label Studio database was not modified. The
[form and restart notes](../../configs/label_studio/README.md) own trial operation.

The interface shows the comment and response together, expandable linked context
and citation limitations, PDF links, and a compact Great/OK/Skip card. Skip exposes
optional fixed reasons. Original extracted text remains available alongside
conservative reading cleanup. No model predictions or curator ratings were added.
Native save/reload/export checks covered multiple reasons, Skip without reasons,
and switching Skip to Great without retaining hidden reasons. QA annotations were
exported separately and removed; the trial retains one unrated task.

The narrow one-case preparation helper has five passing tests. Formatting, lint,
and typing pass. Full `make check` reported 2509 passing tests and the three
previously documented Task 06G generation/template failures. At the trial checkpoint, UI approval and the remaining import were pending.

After the user reported computer disruption, verified that trial servers and test
processes were no longer running and left them off. Cause was not established.
The saved `ui_preview.png` supports review without restarting services; further
live inspection should remain lightweight. No additional cases were prepared.


## Approved 50-case review

Kyle approved the UI and full import. Project 1 is now titled
`Task 07A · 50-comment pilot review`. Retained the original task and imported
49 additional cases. Verified exactly 50 unique selected comment IDs, exact
prepared data/context, and zero annotations or predictions at handoff. Saved
`screening_50_tasks.json`, the 49-case import receipt, an initial native export,
and `screening_import_manifest.json` (form hash and task-ID mapping) alongside
the trial artifacts. The accepted sample remains unchanged.

Restarted only the isolated server (8097) and PDF server (8098), at reduced
process priority. Global database size and modification time remain unchanged.
No new package installation or full test run was needed. The approved citation
panel lists report references and resolution status; PDF links open Volume 4
source pages, not cited Draft EIR destinations. Human decisions were pending at import.


The brief UI simplification was reverted at Kyle's request (the feedback belonged
to another chat). Restored the approved form checksum and all 50 original display
payloads while preserving current annotations. The active form remains
`task07a.screening.trial.v1`.


Future screening candidate: Kyle proposes automatically skipping comment-response
cases linked to General Response 6 as `document_change`, because GR6 states that
Threshold/Impact GHG-1 were removed and MM GHG-1a–1e are no longer required.
Record this as a candidate rule only; Kyle labeled this pass manually.
No automatic decisions have been applied.


## Completed human screening export

Kyle completed all 50 cases: 20 Great, 6 OK, 24 Skip. Verified export saved at
`pipelines/brisbane_baylands/task_07_pilot/07a/label_exports/20260924T171009Z/`
under the artifact root. `label_studio_export.json` preserves native annotations;
`decisions.json` maps ratings/reasons to stable comment IDs and retains reviewer
and timestamps. The exact form, project settings, checksums, and verification
results are saved alongside. All 50 annotations were compared against separate
live task reads and a second full export. The current project was not modified.

For a future linking repair, keep this completed project unchanged. Transfer
labels to any replacement project by stable comment ID, verify all 50 ratings
and reason lists match exactly, and preserve the original decision provenance.
New response context may warrant optional follow-up, not blanket relabeling.
No migration or linking repair is authorized by this export operation.


## Human-maintainability review and checkpoint

Reviewed the new screening helper, tests, approved form, and operating notes.
An independent code review found no blocking defect for the sealed sample.
Separated PDF body cleanup from page-link/article assembly, named the two
source-specific regexes, documented trailing-whitespace paragraph reflow, removed
ambiguous variable names, and included comment IDs in context-validation errors.
Kept the small single-case API and approved form unchanged. This is deliberately
bounded MVP glue, not a general annotation framework; sampling/import/export
execution records remain external artifacts, not supported bulk CLI commands.

Verified all 50 regenerated in-memory payloads exactly match the saved import
(with its existing batch subtitle). No project or label writes occurred.
`make fix` and `make check` with `PYTEST_ADDOPTS='tests/test_pilot_screening.py -q'`
pass: repository formatting/lint/typing and six focused tests. The previously
recorded full-suite Task 06G failures were not re-run for this localized refactor.

Commit this screening checkpoint before creating the response-linking repair
subtask. Resume 07A example selection only after that repair and verified label
transfer; the completed project and verified export remain immutable inputs.

The next contract is [Task 07A.1](07a1_repair_response_list_links.md). Return here
for example selection after its verified linking and label-transfer handoff.


## Post-repair readiness

[Task 07A.1](07a1_repair_response_list_links.md) is complete. Use its
[accepted replacement result](../../docs/specs/task07a1_final_result.json) and
[project 2](http://127.0.0.1:8097/projects/2/data?tab=1&labeling=1) for the next
selection step. The same 50 comment IDs and all original decisions were verified:
20 Great, 6 OK, 24 Skip, with exact reason sets and original decision provenance.
The original sample, project 1 and protected export remain historical evidence.

Five cases gained response context: O-Joint-74 (Great), O-YIMBY-8, M-OSEC-50,
RA-Caltrain-6 and O-SAMCEDA-6 (all Skip). Their decisions remain unchanged.
Optional follow-up is separate from the completed batch. Selection of 6–10
examples is ready to begin but was not performed by the repair task.


## Eight-case selection and 07B handoff

Selected eight distinct cases from the 20 human Great decisions, using the
repaired inventory and migrated project 2. The user requested four cases using
different general responses, two main-only cases, and two different appendices.

| Comment | Coverage | Topic |
| --- | --- | --- |
| I-EA-2 | GR1 | Regional jobs–housing imbalance |
| O-Joint-19 | GR3 | Housing demand and displacement |
| I-CJ-4 | GR4 | Contamination and cleanup requirements |
| I-CF-4 | GR8 | Bayshore cycling and traffic safety |
| PC-LM-2 | Main only | Why Alternative 7 is environmentally superior |
| SA-Caltrans-33 | Main only | Net emissions versus baseline |
| M-OSEC-273 | Appendix H | Electricity mix in GHG estimates |
| O-GGBA-2 | Appendix D | Wildlife corridors and biological surveys |

GR8 also links to GR7; retain that context. The appendix cases also cite main
text. The main-only and appendix slots have no general-response links.
The selection favors manageable concerns and varied evidence paths, without
changing human decisions or claiming formal benchmark eligibility.

The external handoff is
`pipelines/brisbane_baylands/task_07_pilot/07a/authoring_selection_20260924_v1/`:
`selected_cases.json` binds all eight comment, response, view, relationship,
reference and annotation IDs; `selected_cases.md` summarizes the selection;
`selection_manifest.json` pins the repaired sample and human export.

Validation: migration and sample file hashes verified, eight unique comments,
all eight Great, four distinct designated GRs, two full-context main-only cases,
and two distinct appendix targets. No source, labels, or projects were modified.
Task 07A is complete. Next: revise [07B](07b_review_comment_questions.md) for
these eight cases before implementing its comment-question review.


## Process note: how this batch was actually run

This retrospective covers the 2026-09-23–24 screening and initial eight-case
selection in this chat. It does not replace later pilot inclusion decisions
recorded in [07D](07d_discover_and_review_evidence.md). Inputs, counts and the
original eight IDs are in the outcomes above; this note explains the decisions.

### Sampling, screening and responsibilities

1. **Kyle set the scope.** Start from comments because many comments can share a
   response. Use 50 unique comments: 40 for coverage, 10 for difficult cases.
   Aim for 2–3 per general response, broad/even appendix coverage, and extra main
   report coverage. Keep the complete linked response context, not artificial
   one-comment/one-response pairs. This was a purposive pilot, not a random
   estimate of suitability across the inventory.
2. **Codex translated those goals into code settings.** The saved sampler used
   accepted 05H units, relationships, views and reference outcomes. It prioritized
   GR coverage, rare appendices, main-report coverage and submission diversity,
   with deterministic tie-breaking. Exact targets and seed are in the saved
   `selection_manifest.json` and `select_sample.py`, not an implicit model choice.
   Citation balancing used comments plus direct responses; inherited GR citations
   were counted separately. Challenge slots used recorded reference/evidence
   warnings, not fit labels. Code preserved IDs/text, expanded recorded response
   context, and checked counts/hashes. Sparse coverage was reported, not invented.
3. **Codex built and tested one UI case; Kyle approved expansion.** The trial used
   I-CJ-4 in an isolated Label Studio instance, preserving global projects. Codex
   tested rating/reason behavior and export, then cleared test annotations. Kyle
   approved the interface before the other 49 were imported. A five-case human
   calibration was proposed in the plan; this chat does not establish that it
   happened. The documented path was one UI trial, then the full human review.
4. **Kyle supplied every screening label.** Great meant a manageable substantive
   concern with a plausible evidence path; OK needed more work; Skip excluded it
   from this initial rebuttal pilot. Kyle rejected separate response flags:
   *any stated document change*, including minor corrections, and citation of an
   unavailable external document became skip reasons. Skip reasons were optional,
   fixed, multi-select, with Other and no typing. Visual requirements could emerge
   later; a warning alone was not an automatic decision. Codex answered specific
   interpretation questions but did not prefill ratings. Kyle completed 20 Great,
   6 OK and 24 Skip; code exported and checked the saved decisions against live
   tasks and preserved a portable copy keyed by comment ID.
5. **A discovered linking gap delayed example selection.** O-Joint-74 named three
   individual responses missing from its context. Investigation found a plural/list
   parser gap, not a general inability to link individual responses. The separate
   07A.1 task repaired it and migrated all 50 human decisions to project 2. This
   chat then used that verified handoff; it did not rerun screening. New context
   was retained without resetting labels or assuming Kyle re-reviewed every
   changed case.

### How the eight examples were chosen

Kyle narrowed the original 6–10 target to **eight Great cases: four different
GRs, two main-only, and two different appendices**. Codex filtered the verified
human export, inspected comment/response text and citation/context metadata, and
used substantive judgment about manageable scope, clear concerns and topic
variety. A second agent compared the non-GR candidates; the lead chose the final
set and wrote short reasons. This was not a deterministic ranking or a second
set of screening labels. Code checked eight unique Great IDs and the allocation.
Kyle accepted the presented selection and asked to close and commit 07A; there
was no separate selection-rating exercise.

Ambiguities were resolved explicitly: GR8 also brought GR7, which stayed in the
context; it occupied one GR slot. “Main-only” meant the full recorded citation
context was main-only, with no GR links. “Uses appendices” allowed main citations
as well; H and D supplied the two distinct appendix slots, also without GR links.
Citation categories did not certify evidence sufficiency. The chosen eight and
reasons remain in the saved handoff above.

During screening, Kyle proposed future auto-skips for GR6 and references to
**Final EIR** Chapters 14–16. Codex agreed these could be conservative pilot
filters: GR6 described removal of the GHG-1 threshold/mitigation requirements;
14–15 contain revisions, while 16 concerns heights/towers and Modified
Alternative 1. No automated filter was implemented. A chapter citation alone
was not verified to mean that each referring comment caused a change, and the
chat does not establish how Kyle applied these suggestions case by case.

### Repeat procedure and lessons

For a later batch, agree the unit, quotas and label definitions first; pin the
accepted source/graph and use a fresh output directory. Inspect the saved sampler
and settings before adapting them: they are batch-specific scripts, not a general
maintained command. Check actual links and report coverage shortages. Trial one
representative UI case, then obtain approval before populating the batch. Keep
compute light after the reported computer disruption; its cause was not proven.
The brief UI simplification was wrong-chat feedback and was reverted, not a
new design requirement. Source-page links and listed report references should
not be described as clickable links to cited report destinations.

Export and verify human decisions before selection or migration. Use the
[reusable example-selection prompt](../../docs/prompts/task07a_select_pilot_examples_v1.md)
for the substantive Codex choice, with the next batch’s actual quotas and files.
It is a prompt distilled now from this process, not an exact historical prompt.
Check the resulting IDs/allocation with code and present reasons and overlaps to
Kyle. Preserve labels when cases are omitted or context changes. Great is a
pilot-fit judgment, not a guarantee of success in later question/evidence review.
