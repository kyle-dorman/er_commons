# Task 07E: Review Reference Answers and Reasoning

Status: **Closed: six human-approved reference answers exported and validated
2026-09-29, with inherited MVP limitations preserved. Combined 07E/07F used
chat-based review. Tasks 07G and 07 are now closed; next: Task 08.**

## Goal and boundary

Review one concise, evidence-supported rebuttal per case, with its reasoning expressed in
the answer itself. It states the direct conclusion, necessary evidence-based
explanation, essential conditions and remaining uncertainty. Do not separately
label an outline, reasoning steps, sentence-to-citation mappings, or a later
polished defense. The former 07F deliverable is produced here.

This is dataset authoring, not benchmark grading. The
[Sprint 2 evaluation contract](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary)
owns two automatic citation checks and two judged dimensions. The reference
answer informs **answer adequacy**; **grounded correctness** is judged against
source evidence with this reference hidden. Reference wording is not the only
valid answer, and an official response is never independent evidence.

## Inputs and selection

- Bind the accepted 07B questions, 07C.1 claims/relevance and sealed 07D case
  exports, including the user-approved MVP warnings and source limitations.
- For the next authoring pass, each comment yields at most one faithful, clear,
  independently answerable question. Rewrite only when it preserves the central
  concern and qualifications; otherwise skip. Do not split a comment into more
  cases or invest in salvaging weak examples. Preserve original-comment provenance.
- Freeze the same question for retrieval, target generation and both judge stages.
  Preserve the current six-case MVP and 31 claims. Any change to an existing
  reviewed question requires an explicit versioned scope decision before use;
  it is not authorized by a formatting or answer-drafting change.

## Single review in chat

Codex presents the frozen question, one proposed reference answer, and a compact
source explanation in chat. Kyle gives ordinary-language feedback; Codex makes
the edits and presents the revised answer. Kyle is not expected to edit answer
text directly, complete a form, or use Label Studio. Work on one case at a time.
Keep support/context sources separate from the retained claim list and preserve
exact anchors. Provide source excerpts and links when useful to assess feedback.

The curator reviews one artifact, with an eventual disposition of approve,
needs revision, or insufficient evidence/unsuitable case. Do not require special
commands or a per-claim checklist. Codex may use an outline internally, but no
separate outline or prose-polishing approval gate is introduced. A concise answer
need not repeat every retained claim or cite every source.

Preserve each Codex-authored proposal/revision and Kyle's feedback separately.
The final text remains Codex-authored and human-approved unless Kyle actually
supplies wording; do not misattribute revisions as human-written text. Approval
must refer unambiguously to the displayed answer version. Feedback on workflow,
silence, or a request for revision is not answer approval.

## Prototype, validation and acceptance

Use M-OSEC-273 as the first chat review with its verified input bindings below.
Discuss and revise this case before expanding; Kyle must review the prototype
workflow before additional cases are introduced. Changing the review interface
does not authorize question-scope changes, source relabeling or benchmark runs.

Review whether the answer addresses the actual question, sources justify its
claims and conclusion, and essential conditions/limits are present. Inclusion
in the noisy MVP claim list does not establish relevance or support. Preserve
unresolved issues and explicit stops without additional claim relabeling.

Output one human-reviewed reference-answer record or explicit stop per case,
with question/input identity, citation pool, source provenance and chat review
history. This replaces the separate logic summary and final defense. It is hidden
from the target model and grounded-correctness judge. Existing native reviews
remain immutable upstream inputs; no new Label Studio project is needed.

## One-case proposal — 2026-09-29 (initial proposal)

### Selection and frozen scope

Use **M-OSEC-273**: one accepted concern, two retained claims, five support
citations and one optional context citation, with no case-specific accepted MVP
warning task. It is small enough to trial the combined review while exercising
an important source limitation. General claim-relevance noise and source-discovery
limits still apply. No existing question, claim, citation rating or review changes.

Display the accepted Q1 verbatim under **Frozen question / concern**:

> The commenter states that energy-use emission estimates assume the grid is still not 100% renewable, citing page 4.10-28, which says electrical-demand GHG emission factors for Phase 1 operations in 2038 and full buildout in 2042 were calculated using PG&E’s 2022 power content label.

This is the inherited declarative concern, not a newly authored interrogative.
Do not invent a requested action or replace it with a broader justification
question. The original comment's “However” has no antecedent within this unit.
Any future rewrite needs an explicit versioned scope decision; this prototype
uses the exact accepted wording for every downstream consumer.

### Verified input bindings

All external paths below are relative to `ER_COMMONS_DATA_ROOT`, with pilot
paths beneath `pipelines/brisbane_baylands/task_07_pilot/`.

- Accepted 07B: `07b/reviews/eight_case_export_20260924T192020Z/`, case
  M-OSEC-273, Q1; native task 107 / annotation 111. Manifest SHA256
  `400f8548fd3151f209dc925405abb08c0dbcc0b0612b2d8be54cbf992d042c79`.
- Accepted 07C.1: `07c1/reviews/seven_case_export_20260925T211401Z/`, pinned by
  `docs/specs/task07c1_final_result.json`; manifest SHA256
  `558e6d069cb5a528b35b3cdcf0461cb9c958444457475803ade91b0ea2b9c428`.
  Preserve C001 `claim07c1-b90cf7af-ef8d-498f-a67d-16b585b0f7f1` and
  C002 `claim07c1-606dd885-b87b-4f6e-af72-689a11294041` exactly.
- Sealed 07D: `07d/exports/case_citations_20260928_v1/`, pinned by
  `docs/specs/task07d_final_result.json`; manifest SHA256
  `f1df7259805888754f4dac612a19761997d3ac5491de4094c8c00ac8b5a2b289`.
  Selected `cases/M-OSEC-273.json` SHA256
  `de5b5cd0bfa567745645071efee12f30580db77bb85a0baba34529bb273351f3`;
  `audit/M-OSEC-273.json` SHA256
  `b8110b8d524b7804aec6abe676b708d3f934240f53577def71fb8bc63e2772cb`.
- Original comment identity:
  `unitv1-24dbb6a89cfbad4e991d70f533ae5c9574ea6de3100623b2b324e48fe6850c0f`.
  Original span `spanv1-a8582e4b62bab4507a7f511146e3a40048379a3f9898ed29ce3d5e048ccbff1c`,
  Final EIR Volume 4 physical page 454, characters 1175–1518; text SHA256
  `5605b8a36ad5264d841c46ff2691f30ebf72843438343c19474e61e042097a43`.
  Exact Q1 equality was checked across 07B, 07C.1 and 07D; the original comment
  text hash also verified. Official response remains provenance only, not
  independent evidence.
- Read-only preparation verified the 07D manifest hash, exact 42-file closure
  and byte sizes, selected case/audit hashes, and all six source-manifest hashes.
  Source audit matched 54 embedded canonical records and 48 quote/offset anchors
  across four canonical files (including 36 primary citation anchors).
  This was a bounded input check, not a new full-corpus or PDF-byte audit.

The labels below are proposal display aliases bound to the exact sealed IDs,
not new evidence identities. Render titles/pages from source records.

| Label | Reviewed source | Printed pages | Level | Exact citation ID |
| --- | --- | --- | --- | --- |
| S1 | Appendix H — Energy Use | 11–12 | support | `citation07d-8bf0addfc1c71ddaa5d92e078dbcbf13ec8157222b497612e876084cd71bfa9b` |
| S2 | Appendix H — Water and Wastewater | 13–14 | support | `citation07d-4c3806a68b621072a7b5cb9af9ab2afc2bccbac22fb01b04cf69764d0c99623f` |
| S3 | Draft EIR — Energy Use | 4.10-26 | support | `citation07d-8759764d57b648103f953f388f075d85b6af244f89ac404edeebc6770f4be945` |
| S4 | Draft EIR — Water and Wastewater | 4.10-27–28 | support | `citation07d-7361ff01d3d2bc225fcaf44180fa124e28a7e5b9e87451cda9fed2e1b2189bb7` |
| S5 | Draft EIR — c. Electricity | 4.11-3–4 | support | `citation07d-00e9af16ea06b88e44a4684a30d619a7a50a03314d3bd5bd69820f66c604646b` |
| X1 | Draft EIR — California Renewables Portfolio Standard | 4.9-29–30 | context | `citation07d-7000dc38c44fde8c6f3f248080972316cd5152c465fe52f5880a1daffdb099bd` |

### Initial proposed reference answer (superseded)

> The analysis assumes some electricity-related emissions before 2045, but it does not hold the 2022 electricity mix constant. Appendix H says the 2022 PG&E factors were interpolated for 2038 and 2042 using the assumed transition to net-zero electricity by 2045. The Draft EIR also assumes that 2.5% of electrical demand generates emissions because some users opt out of Peninsula Clean Energy’s renewable plan. [S1, S3]
>
> The page attribution needs qualification: the electrical-demand statement is in Appendix H’s Energy Use section. Draft EIR page 4.10-28 discusses water and wastewater and gives factors of 85 pounds CO₂/MWh for 2038 and 26 for 2043. Those figures should not be presented as a verified 2042 electrical-demand calculation. Appendix H’s water/wastewater section also cites a 2019 power-content label. The reviewed sources establish that future decarbonization was considered, but do not resolve these year/label differences or independently establish that the 2022 label was the best information available in April 2023. [S1, S2, S4]

This initial proposal is preserved as drafting history; it was superseded by the
full six-citation answer approved in chat. It is not the accepted answer.
It answers the inherited concern without treating retained claims as proof.
The energy and water/wastewater distinctions are source observations, not new
claim labels. Legal targets are described as modeling assumptions in the frozen
corpus, not independently verified statements of current law. No broader
emissions-significance conclusion is justified by this prototype.

### Chat review sequence

1. Show **M-OSEC-273**, the exact frozen concern, the current answer version and
   a short source explanation. Keep the year, energy/wastewater and power-label
   limitations visible. Full source units and provenance remain available for
   focused inspection rather than requiring a source-by-source form.
2. Kyle gives feedback in chat. Codex checks it against the frozen scope and
   evidence, revises the answer, and explains substantive changes briefly.
   Preserve earlier proposals and feedback; do not silently replace history.
3. Continue on this case until Kyle approves a specific displayed version or
   explicitly stops the case. A request for changes means needs revision.
   Ambiguous approval is clarified only when necessary to identify the answer
   being accepted. Workflow approval alone never approves the answer.
4. Save the accepted version or explicit stop with its supporting review history.
   Expand only after Kyle has reviewed this prototype workflow.

Citation aliases resolve through the frozen pool. Record cited IDs separately
from answer text; do not introduce sentence mappings or a citation labeling task.
All retained claims and source ratings remain intact even if unused in the answer.

### Bounded recording and validation contract

Use a fresh external 07E namespace for review records when materializing this
chat review. No labeling UI or form implementation is required. Proposed schema:
`er_commons.task07e.reference_answer.v1`; finalize the small record definition
before its first persisted export. Reuse ordinary JSON and existing validation
helpers where useful rather than building a conversation workflow engine.

The record binds case/comment/Q1 and exact question hash, upstream seals, claim
IDs, complete citation pool/provenance/limitations, ordered answer versions and
cited IDs, verbatim relevant user feedback, actor attribution, and the final
disposition tied to the exact answer version/hash. Preserve available chat/turn
identifiers; never invent unavailable identifiers or message timestamps. Separate
recording time from original message time. Keep review history outside Git under
the configured artifact root; tracked task docs own the contract and routing.

Validate source-ID resolution, exact input bindings, version identity and
feedback/decision attribution. Read back saved records and confirm the accepted
text and citation IDs match the version Kyle approved. Pending feedback and
needs-revision records cannot export as approved. An explicit stop retains its
reason without fabricating a final answer. Authoring approval does not establish
benchmark eligibility or authorize target/judge execution.

Learning note: the labeling workflow is the preserved proposal, feedback,
revision and explicit decision, independent of its interface. Chat removes the
unrealistic expectation that Kyle will directly edit drafted answers; explicit
version binding keeps the resulting labels auditable. The prior Label Studio
form proposal is superseded by Kyle's instruction; no form was implemented and
no historical review is migrated.

The chat trial has now produced an approved answer. No Label Studio project or
benchmark run was created. The structured external review export is linked below; this task note is
the contract and outcome summary, not a replacement for the review record.

## MVP learning outcome: M-OSEC-273 chat review

Kyle approved the full four-paragraph answer using S1, S2, S3, S4, S5 and X1
with: “ok this is great. im happy with this.” This applies to writing block
`82641` as displayed immediately before that message, beginning “The analysis
assumes some electricity-related emissions before 2045, but accounts for the grid
becoming cleaner over time” and ending “it does not mean the grid is already
entirely renewable in 2038 or 2042.” Because that writing block had earlier
revisions, its ID alone is not an adequate version identity. Preserve the exact
approved text/hash and relevant feedback when creating the external review record.
No other case has been drafted or approved by this outcome.

### What changed and why

- **Draft from the work already reviewed.** Use the frozen question, retained
  claims and reviewed support/context citations. The official response supplied
  discovery clues; treating it as the answer reintroduced assertions and details
  that did not help answer the concern.
- **Keep audit observations out of answer prose.** The first draft discussed a
  corrected page attribution and an unsupported “best information available”
  assertion. Neither was necessary to explain the calculation. Put a source
  problem in the answer only if it changes what can responsibly be concluded.
- **State the fact, not an editorial judgment.** Kyle rejected “The page
  attribution needs qualification,” “Those figures should not be presented as a
  verified,” and a long “The reviewed sources establish...” sentence. Replace
  such language with specific facts or remove the point if irrelevant.
- **Separate points for readers and judges.** Do not combine the cleaner-grid
  assumption, year differences and evidence limitations in one sentence. The
  accepted answer separates the direct explanation, numerical example, opt-out
  assumption and regulatory context into four paragraphs.
- **Use bounded examples rather than discard useful evidence.** The 85/26
  pounds CO2/MWh factors are electricity intensity factors used in water and
  wastewater calculations. They illustrate future grid adjustment and support
  C002. “For example” includes that evidence without claiming those exact values
  are the separate 2042 electrical-demand factors. The earlier characterization
  of these figures as simply irrelevant was too strong.
- **Explain the context contribution.** The accepted answer uses S5 to describe
  the electricity mix and plan options, and X1 to explain the transition targets.
  This is more complete than the initial S1/S3-only answer. It does not establish
  a universal rule that every source must appear in every future answer.
- **Show the review context before asking for a decision.** Kyle requested
  question → claims → citation summaries → answer. This lets him assess the
  proposed synthesis against his prior labels, without editing prose himself.

### Reusable practice and limits

Apply the [versioned authoring prompt](../../docs/prompts/task07e_reference_answer_authoring_v2.md)
to the next authorized case. Check every sentence for a direct answer, evidence
explanation, useful example or necessary context. Explain unused sources outside
the answer, preserve relevant uncertainty, and never force an unsupported claim
into the text just because it was retained upstream.

This is a lesson from one successful MVP review, not evidence that the prompt
improves judge performance or generalizes across cases. Test it through subsequent
human reviews; preserve substantive corrections as further learning. The sealed
six-case input, 31 claims, source ratings, and question scopes remain unchanged.

## Approved prototype export and next case

M-OSEC-273 is exported under
`pipelines/brisbane_baylands/task_07_pilot/07e/reviews/m_osec_273_chat_20260929T192521Z/`
(relative to `ER_COMMONS_DATA_ROOT`). Manifest SHA256:
`544849abf5e3026f5b15d07550c88b663ae6393e0f161c289e4620092543b167`.
The exact approved answer SHA256 is
`ec96e371dd36c4e0a8e173f42e6efa2d575efa6e7de20bf0e4d03905a02fc1db`.

`review.json` uses `er_commons.task07e.reference_answer.v1`: frozen concern/hash,
comment ID, pinned claim/citation references, exact display-alias map, inherited
limitations, ordered answer versions with text hashes and cited IDs, disposition,
approved version/hash, verbatim approval event and source-message identity,
review-history pointer, recording time, input hashes and downstream visibility.
`chat_history.json` uses `er_commons.task07e.chat_history.v1` and preserves 23
user/final-assistant messages with available source-session lines, turn/message
IDs and recorded timestamps. It excludes tools, private reasoning and environment
instructions. Five answer versions are preserved, including superseded proposals;
only v05 is approved. Reused writing-block IDs are disambiguated by message IDs
and answer hashes. `approved_answer.md` contains the exact approved answer.

The export includes a one-off provenance script and validation receipt, with the
manifest written last. It is not a new maintained workflow engine. Read-back
checks verify exact approved text, its immediately following approval, six valid
citation identities and upstream hashes. No historical review was overwritten.
The source case retains full source text, canonical anchors, original source
manifest references, and licensing/retrieval provenance in place.

Kyle authorized export followed by the next case in chat. Select **O-GGBA-2**:
one frozen concern, two retained direct claims, seven support citations and two
context citations. The case SHA256 is
`8197db9f2bbfe3e8910249804564b6145f1a057cad635702e434a2c0b79bd889`.
A bounded read-only source check matched all nine source-manifest references,
70 embedded canonical anchors and 61 quotes/offsets across four files. Present
question, claim summaries, all citation summaries, then one proposed answer.
O-GGBA-2 was subsequently approved and exported below. Preserve the distinction between limited
regional terrestrial connectivity, bird passage and potential butterfly movement.

## O-GGBA-2 approval and PC-LM-2 continuation

Kyle approved the first O-GGBA-2 proposal with “ok this is good. next”. The exact
answer from writing block `68302` is preserved under
`pipelines/brisbane_baylands/task_07_pilot/07e/reviews/o_ggba_2_chat_20260929T193143Z/`.
Manifest SHA256:
`c416c6f0d5398bd69d95b9241505dd5e1d79bea2f9854ef90ae6117643a26e34`.
Approved answer SHA256:
`8da4f44a4e5a7eb1dc2bd8259c3f6ac1d17d0595d23a32d8e4d3d02a9e10c614`.
The export retains the continuation request, complete question/claims/citation
presentation and proposed answer, and following approval as three exact chat
messages. One answer version is approved; all nine source aliases resolve to the
sealed citation pool. Previous exports and native reviews remain unchanged.

MVP observation: the new presentation/prompt produced an answer Kyle accepted on
its first presentation for this case. It preserved the distinction between
terrestrial connectivity, bird passage and butterfly habitat without importing a
blanket conclusion from the official response. This is a second reviewed example,
not a quantified claim about general prompt or judge performance.

Next is **PC-LM-2**, with its frozen concern, three retained claims and six
reviewed citations (four support, two context). The next proposed answer should
explicitly distinguish total project emissions and overall environmental effects
from per-capita emissions and regional transportation benefits. Its answer was subsequently approved and exported below; no question, claim or
citation rating is changed.

PC-LM-2 input verification matched the sealed case/audit hashes, 62 embedded
canonical record references and 56 quote/offset references across two files.
Five citations have verified source-manifest references. The sixth (Section
8.5.2) omits that field in the sealed export; its exact source ID, PDF hash,
release and extraction identity match the same verified source, and its separate
boundary receipt verifies. This shared source binding is documented here without
modifying the sealed citation or treating the omitted field as present.

## PC-LM-2 approval and SA-Caltrans-33 continuation

Kyle approved PC-LM-2's first proposal with “good. next”. Writing block `90427`
is preserved exactly under
`pipelines/brisbane_baylands/task_07_pilot/07e/reviews/pc_lm_2_chat_20260929T194051Z/`.
Manifest SHA256:
`2b2ce69f128dbbda27c434ae28a493d7de30ef4703267bd8dc19eb4511013981`.
Approved answer SHA256:
`6218939693347838fa7eb55594db70da9780926d1cc083e6d4296b2cfa754b22`.
The export binds one answer version, three exact chat messages and six citation
aliases (four support, two context). The shared-source metadata limitation above
is retained in the manifest. Existing reviews and earlier exports are unchanged.

MVP observation: the context citations were essential to the accepted answer:
they distinguished the denser plan's regional transportation advantage from
Alternative 7's lower project-total emissions and overall environmental ranking.
The first proposal was accepted without revision; this is one additional example,
not a measured guarantee of prompt effectiveness.

Next is **SA-Caltrans-33**, one frozen concern, three claims, four support sources
and seven context sources. The question asks to verify/update the operational
emissions presentation. Explain the defined net-increase accounting and distinguish
baseline comparison from source-category/buildout totals. Check any numerical
discrepancy against the original pages; do not silently reconcile it. No answer
for this case is approved yet.

SA-Caltrans-33 bounded verification matched 329 canonical record references and
318 quote/offset references across five files. The 11 citation objects omit
individual source-manifest references; the audit packet's shared source/boundary
references verified (60 hash references across 47 distinct paths). Original PDF
page inspection confirmed the Phase 1 table differences and the daily PM2.5
non-exceedance flag at 60.7 pounds/day against a 54-pound/day threshold. These
are relevant to the explicit verify/update question and must not be silently
reconciled or attributed to rounding. No canonical source or review was changed.

## SA-Caltrans-33 lesson: rebuttal scope

Kyle clarified that the selected cases call for rebuttals, not offers to amend
the report. The original SA-Caltrans-33 response was checked: it explains that
the table values already represent incremental emissions and offers no document
change. The proposed table-note revision is withdrawn; it was not approved.

The revised answer must explicitly address Section 4.9.6-a, Threshold AQ1,
explain why Table 4.9-8 reports an increase without separate baseline/future
columns, and support that interpretation with the reviewed claims and sources.
The verified table discrepancies remain in these review notes; they do not
negate that accounting explanation. Do not claim that both tables are numerically
identical or that all figures are correct. An error that materially defeats a
future rebuttal must still qualify the answer or trigger a review stop.

[Authoring prompt v2](../../docs/prompts/task07e_reference_answer_authoring_v2.md)
makes this boundary explicit while preserving v1. The user-approved answers and
sealed inputs remain unchanged. SA-Caltrans-33 is still under review; the request
to improve the prompt is not approval of its revised answer.

## SA-Caltrans-33 approval and I-CF-4 continuation

Kyle approved the revised rebuttal with “ok good enough. next”. The last version
of writing block `31764` is preserved exactly under
`pipelines/brisbane_baylands/task_07_pilot/07e/reviews/sa_caltrans_33_chat_20260929T200347Z/`.
Manifest SHA256:
`ef32626cafe5ea9b0d57628d43e1db39eff5e1e404e6bea4fa7dce9119cdbe44`.
Approved answer SHA256:
`7eeab70527b3e768f45898dbbb36af4855d21a4e94c39368f256a8724190841b`.
The export preserves nine chat messages and three writing-block versions,
including the superseded partial paragraph proposal. Only the final full rebuttal
is approved. Citation-range notation in the initial draft is expanded to exact
IDs in its history; the approved answer uses explicit aliases for all 11 sources.
The table discrepancies remain separate review findings. Upstream inputs and
previous approved exports are unchanged.

Continue with **I-CF-4**, one concern, 11 retained claims and 31 citations
(14 support, 17 context). Preserve accepted MVP warning tasks 195 and 197 and
edition substitutions. Focus the answer on the Class IV listing, the broader
Mobility Plan's Class I protection, speed/conflict reduction, and conditions of
the EIR hazard finding. Do not infer that a lower design speed guarantees actual
speeds, all network gaps disappear, or mitigation has already been implemented.
I-CF-4 remains unapproved.

I-CF-4 validation matched the sealed case/audit hashes, all 31 source-manifest
references, 402 canonical records and 357 quote/offset references across ten
files; 153 provenance hash references matched across 15 distinct paths. Accepted
warning 195 concerns C011 (context-only evidence and unexplained partial outcome);
197 concerns C013 (no-support/context ratings and unexplained partial outcome).
Do not promote the exact crossing widths, four-second interval or bridge rationale
into established facts. Final Appendix F.1 substitutions remain explicitly marked.
The overall hazard finding depends on MM TRA-3a–3o; MM TRA-3f includes a fair-share
fee alternative and minimum improvements. Outside-corridor gaps remain.

## I-CF-4 approval and O-Joint-19 continuation

Kyle approved I-CF-4 with “ok good. next”. Writing block `58216` is preserved
exactly under
`pipelines/brisbane_baylands/task_07_pilot/07e/reviews/i_cf_4_chat_20260929T201733Z/`.
Manifest SHA256:
`ec42d617a1de38b65388f816ba1e2c26f0fcf83f84f647ab7805fa96de73e5f2`.
Approved answer SHA256:
`94a53497f0b0c7f7bed37067d77647d574f36357b7efb4d4dbc83927aba85bea`.
The export preserves three exact chat messages and one approved answer version.
All 31 source identities remain in the pool; the answer cites 22. Warnings 195
and 197 and edition-substitution limits remain intact. Read-back checks verified
manifest closure/hashes, answer text, immediately following approval and aliases.

MVP observation: grouping related sources made the larger pool reviewable while
preserving each identity. The approved rebuttal focused on design features and
implementation conditions rather than reproducing all retained transport claims.
Unsupported precise crossing measurements and blanket network-completion claims
were not introduced. Approval does not relabel or delete those upstream claims.

Continue with **O-Joint-19**, the remaining sealed case: three frozen concerns,
ten retained claims and 21 reviewed sources (nine support, twelve context).
Preserve all three concerns together; do not silently narrow to plan consistency.
Warnings 184 and 185 remain. The source pool addresses regional planning, induced
household demand, housing capacity and cumulative displacement; it does not supply
source support for the retained detailed VMT, air-emissions or GHG-result claims.
A proposal must distinguish planning forecasts/zoned capacity from actual housing
delivery in neighboring jurisdictions, and must preserve the explicit significant
cumulative physical-impact finding. O-Joint-19 is not approved; the full task
remains open pending human disposition of this case and final handoff validation.

O-Joint-19 verification matched the final manifest and case/audit/effective-review
seals; 194 canonical anchors across all 21 citations matched live records, and
two external receipt hashes verified. Warning 184 is C010's partial/context-only
historical RHNA attribution; warning 185 is C011's supported outcome with only
context ratings for inferred ABAG approval. Neither is a documented agency finding.
C004/C005/C006/C013 have no supporting transport/air/GHG analysis in this pool.
The frozen three-concern scope remains intact: a proposal can rebut omission of
regional planning/displacement discussion, but cannot establish city-specific
housing delivery or quantify project-attributable displacement from this evidence.
The S8 prose shortfall of 1,189 differs from S9 table total of 1,168; preserve as
a separate source-quality observation without using an exact shortfall in prose.

## Final outcome and six-case handoff

Kyle approved the revised O-Joint-19 answer with “ok good enough. next”. Its
last `74629` version is exported under
`07e/reviews/o_joint_19_chat_20260929T202922Z/` within the Task 07 pilot root.
Manifest SHA256:
`e76b9f1a8b15c1aca8c1618c3a642c77e82da54e9f824707f3d2d5211b545202`.
Approved answer SHA256:
`d3b846bd15d7c9c4ec658c2ff88dd94de2eae5cd059fef0f162cdd72d211cb49`.
It preserves seven chat messages, two full proposals plus the intervening partial
paragraph, all three concerns, and the complete 21-source pool (15 cited).

The [final result](../../docs/specs/task07e_final_result.json) pins the collection
under `07e/handoffs/six_case_chat_20260929T203021Z/`. Its manifest SHA256 is
`fa442ab35708293a7cd6e09ce0a0482608ffcb0b34ee29801917e1655d81623e`.
`handoff.json` references the immutable per-case reviews; `approved_answers.md`
presents all six exact approved answers and their complete citation-label maps.
The collection adds no new approval or benchmark designation.

| Case | Approved version | Preserved claims | Citation pool | Answer cites |
| --- | --- | --- | --- | --- |
| M-OSEC-273 | v05 | 2 | 6 | 6 |
| O-GGBA-2 | v01 | 2 | 9 | 9 |
| PC-LM-2 | v01 | 3 | 6 | 6 |
| SA-Caltrans-33 | v03 | 3 | 11 | 11 |
| I-CF-4 | v01 | 11 | 31 | 22 |
| O-Joint-19 | v03 | 10 | 21 | 15 |
| Total | | 31 | 84 | 69 |

Validation covered exact file closure/checksums, 17 unique upstream input hashes,
all 48 stored chat events against original source-session text, all 14 answer or
partial-revision blocks, exact final-answer/approval adjacency, source alias
resolution and preserved support/context roles. Independent review confirmed all
six exports and collection closure, references, exact answer aggregation and full-scope
hashes without blockers. The 14 blocks are not 14 full drafts; partial
paragraph proposals remain explicitly preserved. Collection scope hashes use
compact sorted-key UTF-8 JSON of the full concern list; historical per-case
question hashes retain their documented original encoding.

No prior review, claim, citation rating, question scope, or sealed source changed.
Warnings 184/185/195/197, edition substitutions and source-quality findings remain.
Approval of O-Joint-19 accepts its qualified answer: it does not establish
city-specific housing delivery or quantify project-specific induced displacement.
All six cases have approved authoring outputs; benchmark eligibility is still
unevaluated. I-EA-2 and I-CJ-4 remain excluded.

### Closing learning and next boundary

O-Joint-19 added a useful distinction: households associated with jobs are not
necessarily new households needing new nearby housing. Existing residents can
commute, and “primarily” two counties does not mean exclusively those counties.
This inference does not establish travel mode, origin shares or absence of
housing pressure. It belongs alongside, not in place of, the displacement limits.

The MVP workflow now preserves question/claims/citation context, assistant drafts,
ordinary-language feedback and explicit answer approval without requiring direct
editing or a labeling form. Sources guide the rebuttal; unsupported bundled claims
remain in the record without being forced into the answer. Context sources proved
important for distinguishing regional from project effects and planning capacity
from guaranteed delivery. Successful authoring is not proof of automatic-judge
performance or universal prompt effectiveness.

The handoff advanced to [07G](07g_assess_pilot_and_local_replay.md). Kyle
subsequently removed the local-model comparison, selected Astra for model-assisted
dataset-label authoring with human review, and closed 07G and Task 07 without
a full retrospective or another pilot round. [Decision 005](../../docs/decisions/005_task08_grouped_question_selection.md)
records the Task 08 selection plan. No local model, paid API, benchmark target
or judge was run by 07E.
