# Task 09F — Implement the adequacy judge

Status: **complete with documented limitations, including 09F.2 cleanup**.
Kyle selected the models on 2026-10-16. The subsequently required
[production cleanup](09f2_cleanup_production_judges.md) passed independent review
and full offline validation (3,975 tests passed, one skipped).
The accepted pair is Luna (`gpt-6-luna`) for C v8 and Haiku (`claude-haiku-5-5`)
for S v6, executed through native Inspect. The [final handoff](../../docs/specs/task09f_final_result.json)
binds the selected configuration and reviewed full-development evidence.
09F.1, 09G and Task 12 remain separate; no additional inference is authorized.

Parent: [Task 09](09_build_evaluation_and_qualify_judges.md).

## Historical original contract

The original whole-answer GLM contract below records the starting scope. Later
approved binary C/S contracts, native execution amendments and final selection
supersede conflicting original requirements. The final handoff owns current use.

## Abstract

Implement answer adequacy as its own scorer and model call: does the complete
answer correctly address the exact question and its essential conditions?
The approved reference guides substance but does not require matching wording,
point organization or citation IDs. Valid alternative arguments remain eligible.

## Goal

Build a versioned adequacy prompt, strict result schema, independent scorer and
dimension-specific tests on the 09B runner and 09C adequacy evidence packets.
Reuse transport/storage without merging this judgment with grounding.

## Inputs

- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md)
  and the [evaluation boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary).
- Accepted 09B runtime decision, 09C adequacy packet contract and
  [09E](09e_implement_grounding_judge.md) result-isolation interface.
- Accepted [09E.1](09e1_compare_cloud_and_decision_judges.md) provider findings
  and [09E.2](09e2_cleanup_grounding_judges.md) maintained runtime: start with
  GLM Flash and reuse the existing transport, caching and reporting boundaries.
- [Judge maintainer guide](../../docs/grounding_judge_guide.md) for current
  interfaces, budgets, receipts, counting modes and failure-inclusive metrics.
- The accepted 09A.3 combined development publication and its cited sources;
  preserve exclusions and original reserved/test boundaries. Expectations remain
  evaluator-only. Read [architecture](../../docs/architecture.md) and
  [artifact rules](../../docs/data_artifacts.md) before implementation.

## Outputs

- Separate adequacy prompt, result schema, scorer, tests and bounded smoke report.
- Immutable call records with exact packet/prompt/model/configuration bindings,
  raw outputs, source-linked diagnostics and explicit errors in external storage.
- Outcome explaining reference limitations and how alternative explanations are
  assessed without editing approved answers or introducing new human labels.

## Research / learning checkpoint

Review [Inspect model grading](https://inspect.aisi.org.uk/model-graded.html)
for explicit criteria and custom scorer behavior, using only the runner selected
in 09B. Read [Anthropic evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
on inspecting grader behavior and outcomes. Explain why reference similarity,
schema compliance and substantive adequacy are different properties; framework
defaults do not establish our rubric or calibrate these judgments.

Use the [judge learning notes](../../docs/llm_judge_learning_notes.md) and these
primary sources to inform optional experiments, not to assume improvement:

- [EvalLM, §6.1](https://arxiv.org/html/2309.13633): request-specific criteria
  improved preference agreement in its study; equal weighting still missed
  decisive requirements. This motivates explicit question requirements, not a
  new averaged score or a claim of adequacy accuracy on our data.
- [RAGChecker, §3](https://arxiv.org/html/2408.08067v2): separates response
  faithfulness from reference-claim coverage. Borrow the diagnostic distinction;
  its reference recall is not our adequacy rubric because optional reference
  details and valid alternative arguments must remain acceptable.
- [VeriScore, §3.3 and Appendix](https://aclanthology.org/2024.findings-emnlp.552/):
  support for individual components does not establish their relationship.
  Preserve actors, scope, conditions, timing and comparisons when decomposing.
  Its open-web verification procedure is outside this task's evidence boundary.
- [ContextualJudgeBench](https://aclanthology.org/2025.acl-long.470/): evaluates
  contextual completeness and faithfulness and examines whether explanations
  actually apply the requested criteria. A plausible explanation is not proof
  of a correct judgment. Our own 09E.1 structured conclusion pilot improved
  repeatability while reducing agreement; structure must earn its extra cost.

## Plan / spec requirement

Write a brief prompt/input/output spec, then implement this dimension separately.

### Implementation decisions carried forward from 09E

- **Reuse the maintained runtime.** Start with GLM Flash at medium reasoning,
  using the accepted provider configuration. Reuse transport, explicit budgets,
  immutable attempt receipts, cache accounting and pure metric helpers through
  narrow interfaces; keep adequacy prompts, schemas and scoring independent.
  Small Qwen via Ollama may exercise local plumbing, not establish judge quality.
- **Start with a simple prompt.** Use the existing whole-answer rubric and concise
  diagnostics below. Do not import grounding's claim-review stack, rejected broad
  semantic reminders or elaborate explanation schema. The research experiments
  are optional follow-ups to observed failures, not the initial implementation.
- **Specify output rules precisely.** Define required fields and coverage, empty
  list behavior, valid score values, unique permitted IDs and when evidence must
  resolve to actual supplied source text. No invented entries to fill an empty
  list; no requirement to review every reference point. Include positive and
  empty-case format examples. Validate both schema and semantic references;
  version any narrow formatting repair and preserve earlier failed receipts.
- **Test across questions early.** Freeze a small multi-question development
  panel spanning error types and passing controls before prompt iteration. Record
  exact inputs, expectations, settings, budget and improvement criteria in its
  manifest. Require improved full-denominator macro-F1 without reduced coverage
  or new failures on designated passing controls before expanding a candidate;
  disclose per-question regressions and retain the baseline if evidence is mixed.
  Predeclare repeat counts and acceptable cost/latency rather than extending runs
  until a favorable result appears. Keep label agreement and stability separate.
- **Report failures alongside scores.** Baseline and later comparisons must show
  accuracy, fixed-class 0/1/2 macro-F1, per-class results, confusion matrix and
  numeric coverage on the same eligible denominator. Missing/invalid outputs are
  incorrect observations and false negatives for their expected class, while
  remaining non-scores in artifacts. Valid-only metrics are secondary. Clean
  abstentions are eligible adequacy score `0`, unlike grounding's numeric N/A.
  Include per-question analysis, latency, native token/cache usage and measured
  cost or an explicit estimate/unknown; synthetic expectations are not independent
  human calibration.
- **Qualify caching on adequacy requests.** Render and inspect the actual
  question/reference/source/candidate layout before a bounded cache probe. Keep
  invariant permitted material in a stable prefix where provider behavior allows,
  with candidate-specific content later. Test distinct candidates sharing that
  prefix, not just identical-request receipt reuse. Separately verify that an
  identical saved request can resume without dispatch and that changed reference,
  source, prompt, model or settings invalidate its result identity. Record native
  cache-read/uncached/output usage and cost for cold/warm calls; unknown counters
  are not zero or proof of reuse. Probe before broader paid evaluation, investigate
  absent reuse, and report the measured limit rather than assuming grounding's
  hit rate transfers. Provider prefix reuse must never reuse a grounding judgment.
  Preserve context preflight, explicit counting mode and all four run caps.

### First live checkpoint

After implementation and offline checks, prepare a fixed subset covering three
development questions with a bounded selection of complete answers, essential
omissions, incorrect answers and clean abstentions. Include valid alternatives
where available and record any coverage gap. Select from permitted tuning data;
do not assume an old grounding panel supplies adequacy expectations unchanged.
Record exact case/variant IDs, eligible counts and explicit currency, request,
output-token and wall-time caps before dispatch. Run the bounded adequacy cache
probe, then the simple GLM baseline on this subset within those caps.

Stop and report subset results, per-question failures, accuracy/macro-F1/coverage,
cache behavior and cost to the user. Do not automatically expand to Dev6 or the
full development set, iterate prompts, or activate optional experiments. The next
step follows the user's review of this checkpoint, including when results look
promising. Preserve the report and remaining work for resumption.

### Adequacy semantics and isolation

1. Supply the exact question and structured answer, approved structured reference,
   reviewed source pool and answer-cited passages needed to assess alternatives.
   Exclude official responses, target identity, automatic citation scores,
   synthetic intentions/expected scores and the other judge's result.
2. Preserve the 09C packet's source completeness and limits. Treat answer and
   source instructions as untrusted data. Oversized/missing required evidence is
   a packet failure, not license to truncate qualifications or invent support.
3. Anchor whole-answer scores: `2` correct, direct and complete; `1` a correct
   conclusion missing essential explanation, condition or question component;
   `0` unanswered, incorrect or materially misframed central question. Mere
   topical relevance is insufficient. Clean abstention scores `0` on these
   answerable cases and is also separately reported.
4. Accept different wording, reordered/combined/split points, concise complete
   answers and omitted optional context. Assess alternate arguments against
   actual evidence; absence from the reference alone establishes neither falsity
   nor incompleteness. Record ambiguity or suspected reference incompleteness
   without changing the frozen reference or automatically awarding credit.
5. Return concise diagnostics linking missing essential substance to reference
   points and actual evidence, assessing extra assertions and material conditions
   as needed. Do not require equal point counts or exhaustively reused citations.
   Validate referenced point/source identifiers rather than trusting generated IDs.
6. Save adequacy as an independent result. Never revise an already saved grounding
   score after exposing reference material. Share call/retry/storage mechanics,
   not conversation state or semantic judgment logic. Errors remain non-scores.

## Optional experiments after the simple baseline

The baseline already has a separate reference-aware call, accepts alternatives,
hides grounding judgments and returns concise structured diagnostics. Implement
and inspect that baseline first. These are queued hypotheses, not required
implementation scope, automatic runs or prerequisites for completing 09F.

1. **Explicit question-requirement inventory.** If the baseline misses question
   components or treats optional reference detail as mandatory, test a compact
   inventory of essential requirements with the question span and a short reason
   each is essential. Derive requirements from the question, using the reference
   and sources to interpret necessary substance; do not copy every reference
   bullet into the inventory or let candidate omissions redefine the question.
   Preserve conditional and relational requirements together. Start within one
   call; a separate candidate-blind inventory call is a later costed experiment
   only if candidate-dependent requirements are observed. This decomposes the
   question's demands, not the answer into another grounding claim inventory.
2. **Requirement-linked assessment.** If omissions or score/explanation conflicts
   persist, compare the same inventory with and without a compact coverage map:
   requirement, candidate passage or explicit absence, relevant resolved source
   IDs, coverage status and decisive missing/incorrect substance. Distinguish
   covered by an alternative argument, partial, absent, incorrect and unresolved
   evidence. Allow empty evidence links with an explicit reason rather than
   inventing locators; missing required source text still causes a packet failure,
   not a graded answer with an unresolved-evidence diagnostic. Keep diagnostics
   brief; do not request a long reasoning transcript. The final 0/1/2 remains a
   whole-answer judgment under the existing
   anchors, never the mean or majority of requirement statuses.
3. **Reference-organization sensitivity.** If the judge appears to reward surface
   matching, test meaning-preserving reference reorderings and split/merged points
   on the same candidates. Preserve all substance, source links and original
   artifacts; transformations receive separate identities and a semantic check.
   This tests stability without changing the prompt. If it reveals a problem,
   compare a narrowly targeted reference-use clarification separately. Include
   concise complete and evidence-backed alternative answers as controls; do not
   silently extend the approved reference or promote a transformed reference.

For any authorized pilot, preselect a small development slice across multiple
questions and error types, including passing controls; do not concentrate on
the pet-policy question or use reserved/test cases. Compare one change at a time
with fixed questions, candidates, source evidence and model settings under a
declared budget; only experiment 3 varies the reference representation.
Keep expectations evaluator-only. Apply the baseline reporting and improvement
criteria above, including invalid-output counts and repeatability alongside
failure-inclusive metrics, coverage and cost.
Report question-family results so repeated variants do not masquerade as
independent evidence. Distinguish agreement with development expectations from
independent human validation. Expand within authorized development scope only
when gains survive passing controls and do not come from lower numeric coverage;
otherwise retain the simpler baseline and record the negative result for 09G.

## Validation

- Offline fixtures exercise explicit empty/nonempty output rules, required
  coverage, duplicate/invented/unresolved IDs and failure-inclusive 0/1/2 metrics,
  including clean abstentions. Test budget stops, immutable receipts, safe resume
  and cache identity changes through the reused runtime.
- Before broader authorized inference, preserve a bounded adequacy-specific cache
  probe report with rendered-request identities, native usage and cost findings.
  Use the fixed multi-question panel and declared improvement criteria above for
  baseline evaluation as well as optional experiments.
- Prove required evidence is included and forbidden metadata and prior judge
  results are absent from rendered requests; check reference changes cannot
  overwrite grounding artifacts or cause cross-dimension cache reuse.
- Fixtures cover complete paraphrases, split/combined points, optional-context
  removal, supported-but-incomplete responses, neighboring-question answers,
  decisive missing conditions, incorrect conclusions and abstention.
- Include evidence-backed alternate arguments if 09A finds any; otherwise record
  that coverage gap explicitly and exercise an invented unit fixture.
- Validate malformed responses, invalid scores/locators, failures and safe resume.
  Use tuning development cases only for an authorized bounded live smoke; run
  relevant tests, `make fix`, `make check`, and `git diff --check`.

## Review pass

Have a bounded reviewer check adequacy versus grounding ownership, alternative
argument treatment and reference leakage; check maintainability and diagnostics.

## Acceptance criteria

- The independent scorer implements the accepted whole-answer rubric and has
  separate prompts, fixtures, result identities and information boundaries.
- Grounding remains unchanged and no failed call becomes a semantic zero.
- The baseline uses the maintained GLM runtime, explicit output rules and
  failure-inclusive reporting; the handoff records adequacy-specific cache
  findings or the precise unexecuted validation limitation.
- The 09G handoff records uncalibrated results, evidence limits and coverage gaps.

## Non-goals

Another reference-labeling pass, silently extending references, joint judge calls,
automatic metric changes, framework reselection, test use or broad prompt tuning.

## Outcome

Implemented the independent simple GLM adequacy scorer and completed the authorized
three-question checkpoint. The [result pointer](../../docs/specs/task09f_checkpoint_result.json)
binds the external full report; the [specification](../../docs/specs/task09f_adequacy_v1.md)
and [maintainer guide](../../docs/adequacy_judge_guide.md) own the current interface.
This initial checkpoint stopped for user review; the subsequently authorized Dev6
extension is recorded below. No prompt tuning or optional experiment was performed.
This checkpoint does not qualify or freeze the judge for test use.

### Implementation and learning

The new `adequacy_judge`, `adequacy_panel`, `adequacy_runtime` and `adequacy_run`
modules keep prompts, schemas, score semantics and receipt identities independent.
They reuse the maintained provider renderer/transport, context allowance, decimal
budgets, immutable attempt receipts and pure metrics. No dependency was added.
A tiny Fireworks rendering extension preserves grounding request byte parity.
Source-ID remapping keeps the complete permitted source/reference prefix stable
without changing original packets. Restricted labels never enter model requests.

The required Inspect and Anthropic sources informed a custom scorer with explicit
criteria and inspectable disagreements. Schema validity and reference similarity
do not establish adequacy. The live alternative-argument failure illustrates that
this remains true even with explicit prompt permission for alternatives. Approved
references and synthetic expectations were not edited or promoted to human labels.

### Fixed checkpoint and results

The fresh external namespace is
`/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09f_20261013_glm_dev3_v1/`.
Its sealed `panel/manifest.json` binds all 21 exact variant IDs, inputs, expectations,
settings and ceilings from `configs/adequacy_dev3_v1.json`: seven answers each for
C041 (animal-control enforcement), C037 (wetland function) and C014 (transportation).
The expected distribution is nine 2s, six 1s and six 0s, including three clean
abstentions. C037 supplies an evidence-backed alternative; C041/C014 lack an
eligible corresponding alternative. C037 has no eligible essential-explanation
omission, so its two partial cases test material conditions/certainty instead.

One baseline pass used GLM Flash (`accounts/fireworks/models/glm-5p3-flash`), medium
reasoning, prompt `task09f.adequacy.v1` and explicit provider-allowance counting.
There were 21 dispatches, no retries and one invalid output. Failed outputs remain
null scores and count as errors/false negatives on the same eligible denominator.

| Population | Accuracy | Fixed-class macro-F1 | Numeric coverage |
| --- | --- | --- | --- |
| All 21 answers | 17/21 = 80.95% | 0.8262 | 20/21 = 95.24% |
| C041 | 6/7 = 85.71% | 0.8413 | 7/7 |
| C037 | 4/7 = 57.14% | 0.6111 | 6/7 |
| C014 | 7/7 = 100% | 1.0000 | 7/7 |

Per-class F1 for 0/1/2 is 0.9091/0.7273/0.8421. Confusion rows
(expected 0/1/2; columns predicted 0/1/2/non-score) are `[5,0,0,1]`,
`[0,4,2,0]`, `[0,1,8,0]`. Secondary valid-only accuracy is 85.00%, macro-F1
0.8565 on 20 outputs. Eight of nine passing controls and all three abstentions
agree with expectations. This is synthetic-label agreement across three question
families, not independent human calibration; one pass cannot measure stability.

The four failures are retained with source-linked records in `checkpoint_report.json`:

- **C041 F07, expected 1 / observed 2:** overlooked the omitted residential-component
  condition on the pet-policy requirement.
- **C037 P09, expected 2 / observed 1:** rejected the alternative control for omitting
  the Appendix D food-web example, despite its different supported explanation.
- **C037 F07, expected 1 / observed 2:** identified the incorrect claim that extended
  monitoring applies in every case, but still awarded full adequacy.
- **C037 F03, expected 0 / non-score:** two issue objects omitted required
  `candidate_point_ids`; the original invalid response remains immutable.

### Cache, spending and execution

All requests were audited offline before dispatch. The three distinct probe
candidates share the entire source/question/reference prefix (6,682 characters
before the candidate field) and the same system prompt/cache routing key.
The probe returned native cache reads of **0, 512 and 512 tokens**, establishing
limited computation reuse, not full evidence/reference reuse. Offline investigation
found that the maintained transport sends `prompt_cache_key` without an explicit
session-affinity header; provider routing/retention is a possible unverified cause.
No cache optimization or extra probe was attempted. Identical saved-request replay
validated all three receipts with **zero new dispatches**.

| Run | Declared USD / requests / output tokens / wall seconds | Native input / cache-read / output | Estimated USD |
| --- | --- | --- | --- |
| Cache probe | 0.25 / 3 / 12,288 / 240 | 8,596 / 1,024 / 542 | 0.00143752 |
| Baseline | 2.00 / 21 / 86,016 / 1,200 | 311,734 / 204,864 / 6,310 | 0.02533142 |

Baseline native cache reads covered **65.72%** of input tokens. Total estimated cost
is **USD 0.02676894**, using native usage and dated provider rates; invoices remain
unknown. Native cache-write counts remain unknown, not zero. Conservative reserved
costs were USD 0.016257 and 0.26275185, well within the declared ceilings. Summed
call latency was 9.84 seconds for the probe and 58.72 seconds for the baseline;
baseline median/max call latency was 2.64/6.70 seconds. Probe observations never
enter the evaluation denominator. Credentials were loaded through `.env` without
displaying values.

### Validation and review

- 485 focused adequacy, maintained comparison and packet tests passed.
- `make fix`, `make check` (4,408 passed, one skipped), and `git diff --check` passed.
- The first full check exposed three historical Task 06G tests whose expected
  finalizer drift was masked by current Git HEAD. A test-only accepted-basis fixture
  isolates that invariant; a separate regression verifies wrong-HEAD rejection.
  Production validation and immutable recipes were unchanged.
- Two bounded independent implementation reviews checked rubric/source boundaries,
  labels, budgets, receipts and metrics. A reporting field mismatch was fixed before
  live calls. Independent post-run review recomputed metrics and reconciled native
  usage against all 24 provider responses.
- Exact source preservation, forbidden metadata, malformed outputs, cache identity
  changes, all four caps and offline resume have regression coverage. Grounding
  request parity passed. Prior artifacts and reserved/test payloads remain untouched.

The namespace preserves validation logs, preexisting documentation diff, request
layout audit, independent reviews, cache review, raw receipts and the complete
failure-inclusive report. Existing documentation edits were incorporated without
reverting the refreshed contract. No commit or push was made.

### Review handoff

Review the alternative-control disagreement, the two condition errors and the
invalid-output format before choosing any next step. A narrow versioned format
repair or optional semantic experiment would require a separately authorized
comparison on fixed inputs; neither was performed. Preserve this baseline for 09G,
including its failure-inclusive denominator, incomplete alternative coverage,
provider-counting limitation and lack of independent human calibration.


## Authorized Dev6 extension — 2026-10-13

After reviewing Dev3, the user requests: “Ok let’s expand to the dev6 set”.
This authorizes one fresh pass on the established 136 eligible 09A.3 Dev6 answers:
C041 (22), C037 (27), C014 (20), C001 (23), C019 (22), C056 (22). It includes
the prior 21 selected answers; report paired changes on those separately from
115 additions. No prompt/schema/provider-setting repair is part of this expansion.

Freeze `configs/adequacy_dev6_v1.json`, all inputs and expectations before dispatch.
Use unchanged `task09f.adequacy.v1`, GLM Flash medium, 4,096 output tokens per
request, one repetition, no retry, and explicit provider-allowance preflight.
Caps: USD 5.00, 136 requests, 557,056 output tokens, 1,800 wall seconds. Reuse
the completed adequacy cache qualification; no extra probe or settings experiment.
Native usage still measures reuse on the new population. All declared eligible
answers remain in failure-inclusive reporting even if context preflight blocks one.

The only implementation change is a bounded versioned panel adapter plus Makefile
selection routing. Preserve Dev3 validation and all prior files. Independently
review the expanded membership, request parity and final metrics; run focused
tests, `make fix`, `make check`, and `git diff --check`. The prior primary-source
research and rubric apply unchanged; no new research method or dependency is
introduced. Store outputs in a fresh `task_09/09f_20261013_glm_dev6_v1/` namespace.
Report per-question and per-class results, control/abstention behavior, invalid
outputs, cache usage and cost. Stop for review before further expansion or tuning.

### Dev6 outcome

The authorized unchanged-prompt Dev6 pass is complete in
`/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_09/09f_20261013_glm_dev6_v1/`.
The [Dev6 result pointer](../../docs/specs/task09f_dev6_result.json) binds the full
failure records, native usage, paired comparison and source/expectation manifests.
All 136 eligible answers were attempted once; no retry, prompt change, label
change, new cache experiment or further expansion occurred.

| Question | Accuracy | Fixed-class macro-F1 | Numeric coverage | Invalid outputs |
| --- | --- | --- | --- | --- |
| C041 animal-control enforcement | 20/22 = 90.91% | 0.9056 | 100% | 0 |
| C037 wetland function | 23/27 = 85.19% | 0.8315 | 100% | 0 |
| C014 cumulative transportation | 15/20 = 75.00% | 0.7675 | 90.00% | 2 |
| C001 cumulative health risk | 17/23 = 73.91% | 0.5688 | 91.30% | 2 |
| C019 landfill groundwater | 17/22 = 77.27% | 0.7065 | 95.45% | 1 |
| C056 residual flooding | 17/22 = 77.27% | 0.6755 | 100% | 0 |
| **All Dev6** | **109/136 = 80.15%** | **0.7692** | **131/136 = 96.32%** | **5** |

There are 22 valid-score disagreements and five invalid outputs. Class 0/1/2
F1 is 0.8506/0.5714/0.8855 on supports 49/25/62. Confusion rows with columns
0/1/2/non-score are `[37,8,2,2]`, `[0,14,9,2]`, `[1,2,58,1]`.
Secondary valid-only accuracy is 83.21%, macro-F1 0.7862 on 131 outputs.
All twelve clean abstentions agree; 58/62 predefined passing controls agree.

Per-question disagreement patterns and limits:

- C041: C04 and F07 receive 2 instead of the proposed 1; the omitted-condition
  disagreement from the small checkpoint persists.
- C037: two false supporting-explanation variants receive 1 instead of 0,
  certainty distortion receives 2 instead of 1, and the supported P09 alternative
  still receives 1 instead of 2 for omitting the reference's functional-loss example.
- C014: C04/F05/F07 receive 2 instead of 1; F10 and O02 fail JSON parsing.
- C001: three expected-zero variants receive partial credit and F07 receives 2
  instead of 1; O01 fails JSON parsing and R02 repeats a JSON key.
- C019: four expected-zero variants receive 1 or 2 despite the proposed central
  condition/reasoning failures. C05 returns an object where a limitation string is required.
- C056: omitted/unsupported explanation cases receive full or partial credit above
  expectation, while F01 and O04 passing proposals receive 1 and 0. The O04 judgment
  treats the absence of a direct standalone yes/no conclusion as decisive despite
  the answer's residual-flooding figure.

These remain disagreements with synthetic proposals, not new human findings or
permission to relabel references. Inspect the complete rationale and source-linked
record before choosing any repair or semantic experiment.

The original 21 answers are a fresh rerun, not substituted old receipts. They
remain 17/21 correct with 20/21 coverage; macro-F1 is 0.8140 (prior 0.8262).
Four outcomes changed with identical requests: C037 F03 non-score→0, C037 F05
1→2, C037 F07 2→1, and C014 O02 1→non-score. Thus unchanged aggregate accuracy
hides item variability. The 115 additional answers score 92/115 (80.00%), macro-F1
0.7612, coverage 111/115. The three new question families alone score 51/67
(76.12%), macro-F1 0.6469, coverage 64/67. Different population/class mixtures
prevent interpreting Dev3-to-Dev6 aggregate changes as a prompt improvement.

Native input/cache-read/output usage was **1,658,149 / 922,112 / 59,909 tokens**;
ordinary input was 736,037. Cache reads cover **55.61%** of input tokens.
Estimated incremental cost is **USD 0.16802341**; the uncached cost upper bound is
USD 0.27867685, and conservative reservation was USD 1.50282950. All four caps
were respected. Summed call latency was 537.39 seconds, median 3.78 and maximum
10.75 seconds. Billed cost and cache-write counters remain unknown. The existing
Dev3 cache qualification remains preserved; no extra probe ran.

Independent preflight review confirmed exact eligible membership and byte-identical
packets/rendered requests for all 21 overlaps. Validation passed: 493 focused tests,
`make fix`, `make check` (4,416 passed, one skipped) and `git diff --check`.
The full report and separate independent post-run review reconcile failures,
per-class metrics and native spending. Prior Dev3 artifacts, all other development
questions, reserved/test boundaries and existing uncommitted work remain preserved.
No commit or push was made. Stop for user review before further expansion or tuning.


## Authorized sampling and output-format comparison — 2026-10-13

The user authorizes steps 1 and 2 on Dev6, then review: explicit sampling controls
with the original prompt, followed by formatting-only prompt improvement. Freeze
both conditions before dispatch; preserve the existing 136 packets, expectations,
source evidence, rubric, parser, schema and medium reasoning. No rubric alignment,
requirement inventory, label edits, parser recovery or further expansion is included.

Use `configs/adequacy_dev6_sampling_v1.json` and
`configs/adequacy_dev6_format_v1.json`: temperature 0, top_p 1, seed 0. The first uses
unchanged `task09f.adequacy.v1`; the second selects `task09f.adequacy.format.v2`
with a complete nonempty diagnostic example and explicit single-object, no-fence,
no-duplicate-key, required-field and limitation-string instructions. Example content
must not contain real development answers or expectations. The default v1 prompt
and previous configurations remain available for exact old-receipt replay.

Run two fresh passes per condition, in order sampling_r1, sampling_r2, format_r1,
format_r2, in `task_09/09f_20261013_sampling_format_dev6_v1/`. Each pass uses the
same sealed Dev6 panel and a fresh output directory with no retries. Each has
caps USD 2, 136 requests, 557,056 output tokens, 1,200 wall seconds; aggregate caps
USD 8, 544 requests, 2,228,224 output tokens, 4,800 execution seconds. No additional
cache probe. Load credentials through .env without displaying them. Fail-closed
transport/budget stops end execution rather than authorizing replacement runs.

Research: Fireworks [Text Models](https://docs.fireworks.ai/guides/querying-text-models)
explains that omitted sampling settings inherit model generation configuration;
the [Chat Completions API](https://docs.fireworks.ai/api-reference/post-chatcompletions)
documents temperature/top_p/seed. Explicit settings are request controls, not a
determinism guarantee. Retain the allowlisted native `fireworks-sampling-options`
header when supplied; distinguish requested settings from provider-reported values.
[Structured output guidance](https://docs.fireworks.ai/structured-responses/structured-response-formatting)
explains the reasoning-output tradeoff, so native schema mode stays unchanged.

Before inference, audit all rendered requests and identity changes, preserve
historical request parity, run focused tests, make fix/check and diff checks, and
obtain independent scope/safety review. Report each pass separately, per-question
failures, numeric agreement among valid pairs, validity transitions, controls,
coverage, failure-inclusive accuracy/macro-F1, native cache usage and estimated
cost. Compare historical default-settings results without claiming a controlled
historical repeatability baseline. Two repeats on six correlated question families
are limited evidence. No automatic promotion: require improved macro-F1 without
coverage loss or new passing-control failures and disclose mixed results. Audit
historical selected grounding requests read-only; do not rerun grounding. Stop for
user review after the fixed comparison. No commit or push.


### Sampling and formatting outcome

Completed the four predeclared passes: 544 fresh calls, no retries, parser repairs,
rubric changes or expansion. The [comparison result](../../docs/specs/task09f_sampling_format_dev6_result.md)
owns per-question failures, strict error classifications, control regressions,
repeatability, native cost/cache details and evidence pointers. Both conditions sent
temperature 0, top_p 1 and seed 0. All native sampling headers confirmed the first
two settings and identical reported profiles; seed was not echoed. Historical
selected grounding requests omitted sampling controls and their effective defaults
remain unknown; no grounding rerun occurred.

| Condition | Accuracy | Macro-F1 | Numeric coverage |
| --- | --- | --- | --- |
| Explicit sampling, original prompt, pass 1 | 109/136 = 80.15% | 0.7696 | 132/136 = 97.06% |
| Explicit sampling, original prompt, pass 2 | 108/136 = 79.41% | 0.7522 | 132/136 = 97.06% |
| Format v2, pass 1 | 115/136 = 84.56% | 0.8186 | 134/136 = 98.53% |
| Format v2, pass 2 | 110/136 = 80.88% | 0.7628 | 134/136 = 98.53% |

The format-only prompt eliminates observed JSON/schema failures (four across the
original-prompt repetitions versus zero across the format repetitions). Each format
pass still has two score-1-with-empty-missing-essentials failures under the preserved
rubric/validator. C041 C04 fails both; C014 F10 fails pass 1 and C041 F02 fails pass 2.
These remain non-scores. Four historical invalids become valid/correct in every new
pass, including original-prompt sampling; the fifth remains invalid or semantically
incorrect. This distinguishes format repair from evidence-backed correctness.

Numeric repeat agreement is 114/128 = 89.06% with the original prompt and
127/133 = 95.49% with format v2. Validity transitions are eight and two respectively.
Two repeats do not certify determinism or calibrated general improvement. The
format candidate increases paired macro-F1 in both repetitions but varies in effect
size and introduces one C056 F01 control regression relative to sampling pass 2.
The predeclared no-new-control-failures criterion is not uniformly satisfied, so
**no candidate is automatically promoted**. All twelve abstentions agree in each
pass; format controls remain 60/62 with C056 F01/O04 disagreements.

Estimated total cost is USD 0.60457768; native cache reads cover 64.12% of input.
All per-pass and aggregate caps were respected, with 2,175.45 execution seconds.
Native totals: 6,738,404 input / 4,320,516 cached input / 224,558 output tokens.
Billing and cache-write counters remain unknown. Independent review verified all
544 requests, strict classifications, failure-inclusive metrics, cost and caps.
Validation passed: 440 focused tests, make fix, make check (4,451 passed, one
skipped) and git diff --check. A minor malformed-selector validation edge found
in preflight review was fixed and tested before inference.

Learning: configuration values must be validated and proven on the actual wire;
provider defaults and settings entered in a config are not experimental controls
unless forwarded. The maintained Fireworks adapter now supports explicit sampling
and retains only its allowlisted sampling-response header. Existing configs/default
v1 prompt remain intact for historical replay. Formatting instructions can improve
serialization without resolving partial-credit ambiguity. Stop for user review
before semantic rubric alignment, more inference or promotion. Prior artifacts,
uncommitted documentation and reserved/test boundaries remain preserved. No commit
or push was made.


## Authorized offline partial-credit revalidation — 2026-10-13

The user requests item 1 (partial-credit rule alignment) on frozen GLM results.
Revalidate exactly the four saved Dev6 passes (544 outputs) from the sampling/format
comparison, in a fresh `task_09/09f_20261013_partial_credit_offline_v1/` namespace.
There are zero model calls and a USD 0 spending cap. Verify the predecessor seal
and exact packet/request/response bindings before analysis. Preserve all raw outputs,
original summaries, proposed scores, labels and model settings.

Add an opt-in, versioned validation rule: a proposed score 1 may have a
missing-essential diagnostic or a nonempty issue diagnostic; both empty remains
invalid. Retain strict JSON/schema/ID validation, score-2 omission rejection and
clean-abstention rules. Existing default and live behavior remain v1; no prompt or
live config changes. Do not automatically lower score 2 because issues exist.
This is a narrow structural compatibility rule: it cannot establish whether a
reported issue affects essential substance, is incidental, or instead invalidates
the central answer and merits 0. Independent review examines the recovered cases
without replacing model scores or treating development proposals as human labels.

Produce per-pass before/after failure-inclusive metrics, per-question changes,
recovered outputs and residual failures, plus repeated-score comparisons with a
warning that changed validity denominators do not measure new model stability.
Record no new token/cache usage or costs. Reuse existing pure metrics and strict
validation; use an external artifact-specific script rather than a new pipeline
framework. Run focused tests, make fix/check and diff checks, then independent
code/result review. Stop for review before any revised-prompt inference or the
separate essentiality experiment. No commit or push.


### Offline partial-credit outcome

Revalidated all 544 saved outputs after verifying all 3,033 predecessor sealed
files, preserving the original reports. The [offline result](../../docs/specs/task09f_partial_credit_offline_result.md)
records per-pass metrics, recovered cases and interpretation limits. Eight existing
model-proposed scores of 1 become structurally valid: five match development
expectations and three remain disagreements. No previously valid score or parsed
result changes. There were zero model calls, new tokens, cache operations or costs.

| Saved pass | Correct after revalidation | Macro-F1 | Numeric coverage |
| --- | --- | --- | --- |
| Original prompt, pass 1 | 110/136 = 80.88% | 0.7745 | 134/136 = 98.53% |
| Original prompt, pass 2 | 109/136 = 80.15% | 0.7579 | 134/136 = 98.53% |
| Format v2, pass 1 | 116/136 = 85.29% | 0.8225 | 136/136 = 100% |
| Format v2, pass 2 | 112/136 = 82.35% | 0.7811 | 136/136 = 100% |

The remaining four invalid outputs belong to the original-prompt passes and retain
JSON/schema failures. The format passes have no remaining invalid outputs, but
still disagree with expectations on 20 and 24 answers. Recovered C041 authority
and construction-policy defects illustrate the narrow compatibility need. The
fixed-$500 fine case remains ambiguous as essential versus incidental substance;
the three expected-zero groundwater/inclusion contradictions remain semantic
errors. Nonempty issue diagnostics cannot certify essentiality or a correct score.
No new human labels or manual score overrides were introduced.

The format outputs still differ on six numeric scores; 6/136 versus previous
6/133 only changes the valid denominator. It is not new repeatability evidence.
Passing controls and abstentions remain unchanged. The live prompts and default
validator remain v1; the optional `task09f.score_rules.partial_credit.v2` keyword
is used only by the preserved offline analysis script. Further scoring-prompt
alignment would require new authorized inference on fixed inputs.

Independent code/result review passed with these semantic limits. Validation:
457 focused tests, make fix, make check (4,468 passed, one skipped), and
`git diff --check`. Prior artifacts, existing uncommitted documentation and
reserved/test boundaries remain preserved. Stop for user review; no commit or push.


## Authorized aligned-scoring model comparison — 2026-10-13

The user authorizes “align scoring instructions → compare GLM/Luna/Haiku”.
Use `task09f.adequacy.aligned.v3`, retaining format-v2 serialization instructions,
with the partial-credit validator: 1 permits a correct central conclusion with
missing or materially incorrect essential supporting substance. A central incorrect
or materially misframed answer merits 0; incidental issues do not automatically
reduce a complete correct answer from 2. No requirement inventory, separate
candidate-blind call, reference transformation, label change or automatic promotion.
Historical prompt/config/receipt behavior remains preserved.

Use `configs/adequacy_dev6_aligned_models_v1.json` and the identical 136 Dev6
inputs/expectations, refrozen only to carry explicit provider comparison ceilings
from `configs/adequacy_dev6_comparison_panel_v1.json`. Verify packet and label byte
identity with the predecessor. Fresh namespace:
`task_09/09f_20261013_aligned_models_dev6_v1/`.
GLM uses temperature 0, top_p 1, seed 0 and medium reasoning. Luna and Haiku retain
explicit medium reasoning; unsupported sampling controls are omitted and disclosed,
not treated as temperature-zero equivalents. All output limits are 4,096 tokens.
Luna uses the maintained exact native counter; GLM/Haiku use explicit conservative
provider allowances. Shared rubric/input content does not imply identical native
structured-output or reasoning mechanisms.

Run a three-distinct-candidate adequacy cache probe per provider before evaluation:
USD 0.25 / 3 requests / 12,288 output tokens / 240 seconds each. Preserve native
read/write/unknown counters and verify saved-receipt replay without dispatch.
Then exactly two fresh 136-answer passes per model. Per-pass caps: GLM USD 2,
Luna USD 3, Haiku USD 8; each 136 requests / 557,056 output tokens / 1,800 seconds.
Total ceiling: USD 26.75, 825 generation requests, 3,379,200 output tokens,
11,520 execution seconds. Native count requests are separately reported and
bounded at one per Luna generation (exact) and Haiku generation (estimate):
at most 275 each, 550 count requests and 1,375 total provider HTTP requests. No retries, replacement runs or budget resets.
A safety/transport halt ends the experiment for review. Execute sequentially in
GLM/Luna/Haiku cache order, then GLM/Luna/Haiku pass 1 and the same order pass 2.

Before inference: independent scope/code review, complete request audit, focused
tests, make fix, make check and git diff --check. Load credentials through .env
without displaying them. Report full-denominator accuracy/macro-F1/coverage,
per-question errors, controls, abstentions, pairwise and within-model disagreement,
native cache usage, cost estimates and limitations. Compare aligned GLM with the
preserved format-v2 outputs revalidated under the same partial-credit rule, while
keeping cross-model conclusions separate. Stop for user review after these fixed
runs; preserve previous artifacts, uncommitted work and reserved/test boundaries.
No commit or push.


Provider-control research: [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)
requires omission of temperature/top_p for Luna's non-none reasoning mode;
[Luna model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna)
confirms medium support. [Haiku migration guidance](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide)
instructs omission of sampling controls. Retain supported medium reasoning rather
than changing reasoning mode merely to force temperature zero. [OpenAI caching](https://developers.openai.com/api/docs/guides/prompt-caching)
and [Anthropic caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
inform explicit stable-prefix placement; native counts still determine observed reuse.


Cache-probe investigation: all nine responses were valid. Luna and Haiku reported
reuse on distinct candidates; GLM reported zero reads on all three. Independent
inspection found matching stable prefixes and the documented Fireworks
`prompt_cache_key` affinity control, with no request-layout defect. Preserve this
negative probe result and proceed within the already-declared uncached reservations;
no extra probes, retries or setting changes are authorized. Full-run native counters
will be reported separately. The execution gate records this disclosed limitation,
not successful GLM cache qualification. See the external investigation and
[Fireworks API reference](https://docs.fireworks.ai/api-reference/post-chatcompletions).


### Aligned-scoring comparison outcome

Completed all fixed 825 generation calls (nine cache probes plus six 136-answer
passes), with 550 native count requests, no retries or replacement runs. The
[comparison result](../../docs/specs/task09f_aligned_models_dev6_result.md) owns
per-question failures, repeated-score pairs, controls, native accounting and
artifact bindings. All 136 packet/label records are byte-identical to the previous
Dev6 panel. The aligned prompt is an explicit experimental selector, not a promoted
default. Historical selectors and replay behavior remain preserved.

| Model | Correct, pass 1 / pass 2 | Macro-F1, pass 1 / pass 2 | Numeric coverage | Repeat changes |
| --- | --- | --- | --- | --- |
| GLM | 110 / 112 of 136 | 0.7622 / 0.7854 | 136 / 136 each | 7 of 136 |
| Luna | 116 / 115 of 136 | 0.8161 / 0.8055 | 136 / 136 each | 13 of 136 |
| Haiku | 110 / 106 of 136 | 0.7688 / 0.7410 | 136 / 135 of 136 | 10 of 135 valid pairs, plus one validity change |

Luna leads both passes on proposed-label agreement, but changes more scores than
GLM. All twelve abstentions match on every pass. Passing controls: GLM 59/62 both,
Luna 59/62 both (different failures), Haiku 58/62 then 56/62. Haiku pass 2 has one
invalid C014 F05 output: an empty issue explanation; it remains a non-score and
full-denominator error, with no repair or retry. GLM's aligned prompt does not earn
promotion: prior format-v2 outputs under the same partial-credit validator scored
116/112 correct, with 60/62 controls each and six repeated-score changes. Aligned
GLM adds C037 C05 as a control failure in both passes and changes seven scores.

The remaining problem is substantive application of the rubric. The models differ
on central versus supporting contradictions and essential versus incidental details.
Luna sometimes demands pet-policy detail for an enforcement question but accepts
its absence in a neighboring candidate; one flooding answer receives all three
scores across providers in pass 1. Nine first-pass disagreements are shared by all
three. Independent qualitative reviews preserve the exact cases without editing
labels or treating model consensus as truth. These observations motivate review of
the queued essentiality experiment; they do not authorize it or prove its benefit.

Native usage totals: 12,762,881 input tokens, 11,121,102 cache-read tokens (87.14%)
and 402,344 output tokens. Estimated cost including probes is USD 0.588312895;
billed cost and GLM cache-write counters remain unknown. GLM's zero-read probe is
preserved; evaluation passes subsequently show 78.18% and 70.70% cache reads.
Luna/Haiku evaluation reads are approximately 92%. Offline cache receipt replay
performed no new dispatches. All declared caps held: 4,093.58 execution seconds
against 11,520, and 825 generation plus 550 count requests against their limits.

Validation passed before inference: 393 focused tests, make fix, make check
(4,503 passed, one skipped), and git diff --check. Independent code, request,
cache-investigation and report reviews are retained in the new namespace. All
3,046 files in the prior sampling/format and offline-rule seals still match their
hashes; one additional unsealed Python cache file was disclosed separately.
No prompts changed during execution, no inventory/extra candidate-blind call was
added, and reserved/test data remained untouched. Stop for user review before
further inference, tuning, expansion or promotion. No commit or push.


## Authorized Claude nonblank-format experiment — 2026-10-13

The user accepts retaining formatting improvements even when the returned numeric
judgment is incorrect, and authorizes a few cleaner prompt changes targeting the
Haiku C014 F05 empty `issues[0].explanation`. Formatting validity and substantive
label agreement now have separate retention criteria: a numeric disagreement does
not by itself veto a formatting improvement. Preserve the successful format-v2
serialization instructions in future work; this is not acceptance of the aligned
scoring revision or a provider's semantic accuracy. Historical bytes remain intact.

Fresh namespace `task_09/09f_20261013_haiku_nonblank_v1/`. Use the existing aligned
Haiku condition and partial-credit validator through the maintained saved-prompt
`prompt_override` interface. No runtime, schema, parser or scoring-rule changes.
Compare four frozen prompt arms: existing aligned baseline, minimal nonblank rule,
consolidated output contract, and invented populated issue example. Preserve the
opening rubric and diagnostic semantics verbatim; examples contain no development
facts or labels. The example can still affect semantic behavior, which is reported.

Select precisely C014 F05 (failure), F04 (diagnostic control), F10 (central-error
control), P01 (passing control), and first R01 (abstention) from the sealed Dev6
panel. Five repetitions per arm, five answers each: 100 generation requests, at
most 100 estimated-count requests, zero retries. Fixed order each repetition is
baseline, nonblank, consolidated, example. One shared RunBudget across all runs
caps USD 10, 100 generation requests, 409,600 output tokens and 1,200 seconds.
Preflight conservative reservation is USD 9.754981250. Credentials load through
.env without display. All namespaces are create-only; no adaptive extra trials.

Inspect original failure and audit all twenty distinct requests before dispatch;
run focused tests, make fix/check and diff check, plus independent prompt/plan
review. Report target and control validity, diagnostic failures, per-answer score
variation and full-denominator accuracy/F1 separately, native cache/cost, and the
limits of a five-answer single-question experiment. If baseline failure does not
reproduce, do not claim a measured repair. Stop after the fixed comparison.
Reserved/test boundaries, previous artifacts and uncommitted work stay preserved.
No commit or push.


### Claude formatting outcome

All 100 fixed calls completed without retries in 509.5 seconds, with 100 native
estimated-count requests. All four arms returned 25/25 valid outputs and 5/5 valid
outputs for the original C014 F05 failure. No blank explanations occurred, including
with the unchanged baseline. The [result](../../docs/specs/task09f_haiku_nonblank_result.md)
therefore records no demonstrated reduction in formatting failures; a rare failure
not reproducing is not proof of repair. Earlier successful format-v2 instructions
remain retained independently of semantic accuracy, as the user directs.

The shorter consolidated contract is the strongest candidate from this targeted
sample: every answer received the same score across its five repeats, with 20/25
correct (80%, macro-F1 0.8222). Baseline and minimal reminder each had 16/25 correct
(64%, 0.6508); populated-example arm had 18/25 (72%, 0.7319). All arms covered the
passing and abstention controls correctly; all twenty C014 F10 central-contradiction
judgments remained incorrect score 1. Those are valid semantic errors, not reasons
to reject formatting improvements. Five selected answers from one question are
insufficient for a general model/prompt ranking or automatic promotion. Preserve
all three tested prompt variants as explicit saved candidates for review; no
production default, rubric, parser or schema changed during this experiment.

Native-token estimated cost was USD 0.12284295,
with approximately 95.13% cache reads; billed cost remains unknown. All currency,
request, token and execution caps held. Focused tests393, make fix, make check
(4,503 passed, one skipped), git diff --check and independent prompt/runner/report
review passed. No reserved/test access, dataset expansion, score override, commit
or push. Stop for review before broader testing or the essentiality experiment.

Seed clarification: neither the [OpenAI Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create)
nor [Anthropic Messages API](https://platform.claude.com/docs/en/api/messages/create)
exposes a documented seed field. [Fireworks chat completions](https://docs.fireworks.ai/api-reference/post-chatcompletions#body-seed)
documents integer-or-null seed without a special zero meaning. Zero conforms to
that interface and prior requests accepted it, but returned sampling metadata did
not echo it, so backend adherence is unverified. Do not transfer zero-as-random
semantics from Fireworks' separate image-generation API to chat completions.


## Selected consolidated development baseline — 2026-10-13

The user requests inclusion of the consolidated contract and the earlier GLM fix.
Select the exact tested `b_consolidated.txt` bytes as
`task09f.adequacy.consolidated.v4`, through the new default
`configs/adequacy_judges_v1.json`. This retains both the GLM single-object JSON
formatting rules and partial-credit v2: score 1 may document an essential defect
in `issues` without inventing an omission. Nonblank/ID/schema checks remain strict;
incidental issues do not automatically lower 2, and central errors remain 0.
The tested candidate already contains these compatible rules, so do not concatenate
redundant old instructions or examples. Preserve old selectors/configurations and
all sealed artifacts. Default provider remains GLM with explicit sampling controls.

This is user-directed development selection, not automatic promotion based on
accuracy or a demonstrated rare-failure repair. Incorporation is offline only;
no new model calls, dataset expansion, credentials or spending are required.
Validate exact tested prompt identity, provider selection, validator compatibility
and historical replay boundaries, then focused tests, make fix/check, diff check
and independent review. No commit or push.

Next proposed work maps to **optional experiment 1: explicit question-requirement
inventory**. Within the same call, identify a compact set of required question
components, each anchored to a question span and a reason it is essential. Use
reference/evidence to interpret substance without turning every reference detail
into a requirement. Preserve concise answers, alternative explanations and linked
conditions. Compare the selected baseline against this single change on the same
frozen Dev6 inputs/settings, with predeclared repetitions and spending/execution
caps. Candidate-dependent pet-policy requirements and central/supporting-error
confusion motivate the test; they do not prove it will improve accuracy. Do not
add the optional coverage map or separate candidate-blind call yet. The experiment
remains proposed and unexecuted pending user authorization.


Selection implementation matches the tested prompt SHA-256
`f24b9603103595f3ffc2a7f804d5e8cf9025ecc706fae07d37ff9f879cd13df4`.
Independent review passed: exact prompt/config preservation, partial-credit routing,
strict diagnostics, unchanged grounding defaults and explicit historical replay.
The new configuration differs from the prior aligned comparison only in prompt
selector; provider settings remain fixed. Focused validation passed 386 tests.
Final validation: make fix and make check passed (4,512 tests, one skipped),
plus git diff --check. No new inference or spending; prior artifacts untouched.

## Authorized Haiku requirements-inventory comparison — 2026-10-13

The user authorizes the proposed experiment on only the worst-performing model.
Select Haiku: its prior aligned Dev6 passes had 110/106 correct and macro-F1
0.7688/0.7410, the lowest two-pass performance among the three models. This is a
selection from measured development performance, not a general model ranking.

Compare the selected consolidated v4 baseline with one prompt-only revision:
a compact question-requirement inventory, anchored to question spans and brief
essentiality reasons, followed by the whole-answer judgment. Keep that observable
inventory in the existing rationale string, with no added schema fields, coverage
map, separate candidate-blind call or changed score rules. This changes rationale
instructions/length as part of making the inventory observable; report that limit.
Preserve concise answers, valid alternatives, relational conditions and optional
reference context. No examples or expected labels enter the prompt.

Use all 136 identical frozen Dev6 inputs from the aligned comparison's panel_v2,
`configs/adequacy_judges_v1.json`, only `anthropic_generation`, medium reasoning
and 4,096 output tokens. Unsupported sampling parameters remain omitted. Exactly
two fresh passes per arm in order baseline_r1, inventory_r1, baseline_r2,
inventory_r2. One shared budget caps USD 32, 544 generation requests, 2,228,224
output tokens and 4,800 execution seconds. At most 544 native estimated-count
requests (1,088 total provider HTTP requests). No retries, replacements or budget
resets. Stop on a safety/transport halt; never extend for a favorable result.
Verify conservative reservations before dispatch. Reuse Haiku's prior qualified
adequacy cache layout; measure actual native cache reads/writes on these requests,
without additional probe calls. Load credentials through .env without display.

Fresh namespace: `task_09/09f_20261013_haiku_requirements_v1/`. Freeze prompts,
config, packets, run order, code bindings and caps before independent preflight
review and execution. Preserve previous seals and all uncommitted work. Complete
offline request audits, focused tests, make fix/check and diff validation first.
Report each pass's full-denominator accuracy/macro-F1/coverage, per-question errors,
controls and abstentions, paired gains/regressions, repeatability, inventory
compliance and candidate-dependent requirements, native caching, cost and latency.
Separate formatting validity from numeric correctness. Use the task's semantic
improvement criteria; do not automatically adopt the experimental prompt. Stop
for user review after the fixed comparison. No dataset expansion, other providers,
reserved/test access, label edits, commit or push.


### Haiku requirements-inventory outcome

Completed the fixed 544 generation calls and 544 estimated-count requests in
3,586.50 seconds, without retries, replacement runs or cap violations. The
[result](../../docs/specs/task09f_haiku_requirements_result.md) owns per-question
errors, paired controls, inventory observations and native accounting. All 544
outputs were strictly valid; all twelve abstentions matched in every pass.

| Prompt | Correct, pass 1 / pass 2 | Macro-F1, pass 1 / pass 2 | Passing controls | Repeated-score changes |
| --- | --- | --- | --- | --- |
| Consolidated baseline | 106 / 108 of 136 | 0.7620 / 0.7625 | 48 / 54 of 62 | 14 / 136 |
| Requirements inventory | 110 / 104 of 136 | 0.7854 / 0.7362 | 51 / 49 of 62 | 24 / 136 |

Both prompts match 214/272 repeated observations (78.68%); these are two passes
of the same 136 answers, not 272 independent answers. The first-pass gain reverses
on the second pass, and repeatability worsens from 89.71% to 82.35%. The inventory
introduces four/eight new passing-control failures while recovering seven/three
relative to each matching baseline pass. It fails the semantic improvement gate;
retain the consolidated development baseline, with no automatic prompt promotion.
C019 improves in both passes, but C041/C014 worsen in both and C001 never improves.

Observable inventory-format checks pass on 133/136 and 132/136 responses. These
are heuristic checks, not schema failures or proof of correct requirements. The
candidate remained visible in the same call; inventory output cannot establish
candidate independence or correct essentiality. No reference, label, schema,
score rule or provider setting changed.

Estimated native-token cost is USD 0.532872400; billing remains unknown. Native
usage is 11,570,316 input tokens, 10,638,100 cache reads (91.94%), 701,612 cache
writes and 631,459 output tokens. Inventory output uses 384,671 tokens versus
246,788 baseline tokens (55.9% more), and costs USD 0.301759500 versus
USD 0.231112900 (30.6% more). Cache reads are measured on actual adequacy requests;
saved-response reuse is zero. All four shared caps and separate count-call limits
held. No additional experiments, model calls, dataset expansion, commits or pushes.


Independent postrun review verified all 544 native request/response bindings,
strict outputs, estimated-count responses, metrics, paired controls, cache/cost
accounting and caps. All 5,365 checked predecessor sealed files remain unchanged.
Offline validation passed 386 focused tests, make fix/check (4,512 tests passed,
one skipped), and git diff --check. A bounded qualitative review examines the
predeclared selection without revising labels or scores. In particular, both
inventory C001 O04 judgments falsely describe the candidate as only a placeholder,
ignoring supporting points that explicitly supply the required numerical comparison.
A correct requirement inventory does not guarantee whole-answer assessment.

The completed qualitative review covers 18 preselected/deterministically selected
answers (72 judgments). It records optional-detail requirement drift and both gains
and regressions without score or label edits. The fresh closeout seals 3,030 files;
the tracked result pointer binds numerical/qualitative reviews, preservation and
validation evidence. All fixed-run authorization is exhausted. Stop for user review.

## Authorized small Haiku coverage-map comparison — 2026-10-13

The user authorizes optional experiment 2 as a small test. Freeze 18 answers,
exactly three from each established Dev6 question, including observed false-omission
failures, a passing control per question, all three expected classes and at least
one clean abstention. Exact IDs and selection reasons must be frozen before calls;
this deliberately diagnostic sample is not a representative accuracy estimate.
Keep the original packets/labels and all reserved/test boundaries unchanged.

Compare three fresh arms on the same selection: the retained consolidated baseline
(acceptance reference), exact prior inventory-only prompt, and inventory plus a
compact requirement-linked coverage assessment. Three repetitions per arm, in
baseline/inventory/coverage order each repetition: exactly 162 generation requests
and at most 162 estimated-count requests, 324 total provider HTTP requests. One
shared budget caps USD 12, 162 generations, 663,552 output tokens and 1,800 execution
seconds. No retries, replacements, adaptive trials, additional probes or budget
resets. Verify conservative reservations fit before dispatch. Stop on a safety or
transport halt. Haiku alone retains medium reasoning and 4,096 output tokens;
unsupported sampling parameters remain omitted. Credentials load from .env without
display. Measure actual native cache reads/writes on these adequacy requests.

The coverage intervention remains inside the existing rationale string and call.
For each requirement, report candidate point IDs and a short exact supporting quote
or explicit absence after inspecting all candidate fields, coverage status, relevant
resolved source IDs when needed and a concise decisive deficiency. Accept alternative
arguments, distinguish partial/absent/incorrect substance, and preserve conditions.
Remove the inventory-only prohibition against coverage assessment rather than add
contradictory instructions. Keep the original 0/1/2 anchors and strict output schema;
never average requirement statuses. No candidate-blind call or label-specific examples.
This tests whether explicit candidate mapping reduces false omissions; a plausible
map is not proof of accurate assessment. Both inventory and mapping can still err.

Fresh namespace: `task_09/09f_20261013_haiku_coverage_small_v1/`. Reuse maintained
runtime and prompt overrides; no production selector or default change. Predeclare
sample IDs, exact prompts, request audits, code/configuration bindings and caps.
Complete focused tests, make fix/check, diff check and independent preflight review
before dispatch. Preserve predecessor seals and all uncommitted work.

Report per-pass failure-inclusive accuracy/macro-F1/coverage, per-question failures,
paired recoveries/regressions, controls/abstentions, repeated-score changes, actual
candidate-quote fidelity and false-omission diagnostics, native cache/cost and latency.
Interpret the coverage-versus-inventory contrast separately from comparison with the
retained baseline. Gains must repeat without reduced coverage or new passing-control
failures before considering expansion; do not promote or expand automatically.
After fixed execution and independent numerical/qualitative review, stop for the
user. No other model, full-Dev6 rerun, new dataset, commit or push.


### Small Haiku coverage-map outcome

Completed all 162 generation and 162 estimated-count requests in 1,165.84 seconds,
with no retries or execution halt. The [result](../../docs/specs/task09f_haiku_coverage_small_result.md)
records exact per-question failures, paired changes, quote checks and native usage.
The sample remains the predeclared 18 diagnostic answers (three per question),
including ten passing controls and two abstentions. All 162 outputs were strictly
valid; both abstentions matched in every pass.

| Prompt | Correct / 18 across three passes | Pooled agreement / 54 | Pooled macro-F1 | Identical score across all three passes |
| --- | --- | --- | --- | --- |
| Consolidated baseline | 7 / 9 / 8 | 24 (44.44%) | 0.4220 | 14 / 18 |
| Inventory only | 10 / 9 / 11 | 30 (55.56%) | 0.5038 | 11 / 18 |
| Inventory plus coverage | 9 / 9 / 10 | 28 (51.85%) | 0.5010 | 11 / 18 |

Pooled observations repeat the same 18 answers and are not independent examples;
this targeted slice is not a full-Dev6 accuracy estimate. Coverage does not improve
on inventory-only accuracy in any repetition (one fewer, tie, one fewer), and
introduces two/one/two new passing-control failures relative to inventory. Compared
with the retained baseline, coverage has two/tie/two additional matches but introduces
zero/two/one new control failures and has less stable scores. It does not pass the
predeclared expansion criteria. Preserve the experimental overrides, retain the
consolidated default, and do not expand or promote automatically.

Coverage recognizes the supporting threshold comparison in C001 O04 in all three
passes, but still withholds full credit for an implicit conclusion. Other false
omission claims persist despite exact supporting content, and the C056 O04 whole-answer
failure remains. A coverage map can quote real material while misjudging what it
establishes; literal quote/ID checks are diagnostics, not validation of correctness.
The independent bounded qualitative review owns exact examples and limits.

Estimated native-token cost is USD 0.266243960 (baseline USD 0.076965475, inventory
USD 0.091962525, coverage USD 0.097315960); billing remains unknown. Native input
is 3,576,699 tokens with 2,503,131 cache reads (69.98%), 1,012,674 cache writes and
217,078 output tokens. All shared currency/request/output/time caps and count/HTTP
limits held. Prior initial offline preparation remains preserved and unexecuted;
only the final reviewed audit and plan governed inference. No schema, parser,
score rule, source, label or model-setting change occurred. No commit or push.


Independent postrun review verified every native binding, strict output, count,
metric and cap. The qualitative review covers all 18 answers and 162 judgments;
false omissions, source-for-candidate quotation and wrong-point links remain.
All 8,395 checked predecessor sealed files are unchanged. Seven literal-format
heuristic misses are missing pipe separators, not missing sections: all 54 coverage
outputs contain Requirements/Coverage/Verdict and finish normally. The original
heuristic report is retained with this explicit correction. Validation passed
386 focused tests, make fix/check (4,512 passed, one skipped), and diff checks.
No further inference is authorized by this completed experiment; stop for review.

The fresh closeout seals 977 files. The compact tracked result pointer binds the
numerical, qualitative and observability reviews, including the delimiter-check
correction. The fixed 162-call authorization is exhausted.

## Authorized offline cross-model failure diagnosis — 2026-10-13

The user requests a deep dive across GLM, Luna and Haiku before choosing another
intervention. Use the matched aligned-v3 experiment as the primary cross-model
comparison: 136 identical answers, three models, two passes each (816 judgments).
Review every answer with any disagreement (48 unique cases), with matched successes
and full question/candidate/reference/source evidence. Treat synthetic expectations
as proposals and inspect their rationales; do not assume every disagreement is a
judge error. Later Haiku-only consolidated/inventory/coverage runs are longitudinal
context, not matched evidence about other models.

Separate observed failures from possible causes: score-boundary interpretation,
whole-answer versus conclusion-field interpretation, optional/essential detail,
source or relationship mistakes, false omissions, proposed-label ambiguity and
strict output failures. Quantify error directions and stable/repeated failures;
record exact illustrative evidence and counterexamples. Inspect source delivery,
output termination and sampling limits without claiming model-internal causality.
Use bounded independent reviews by question pair and integrate their evidence.

Fresh external namespace `task_09/09f_20261013_failure_diagnosis_v1/`; zero provider
calls and USD 0 spending. Preserve previous seals, code, prompts, labels, reserved/
test boundaries and existing uncommitted work. Produce a compact diagnosis and
ranked next decisions, with uncertainty and concrete criteria for any proposed
experiment. No prompt edits, model runs, label overrides, commit or push. Review
analysis consistency and documentation diff before stopping for discussion.

### Offline diagnosis outcome

The [cross-model diagnosis](../../docs/specs/task09f_crossmodel_failure_diagnosis.md)
records all 48 disagreement answers and 21 successful counterexamples reviewed in
three bounded question-pair audits. Across 816 matched aligned-v3 judgments, there
are 147 disagreements: 122 over-credit, 24 under-credit and one invalid output.
These remain disagreements with proposed labels, not 147 adjudicated judge errors.
Eight answers disagree in every model/pass; 88 agree throughout. Whole-answer
score aggregation, central versus secondary explanations and essential versus
incidental defects recur across models. False omissions and actual reading errors
also occur. Literal placeholder explanations pass the schema in twelve
Haiku outputs, including nine with matching scores, illustrating why formatting
validity alone is insufficient.

All native outputs finished normally, without evidence of response truncation.
Later Haiku-only experiments are interpreted separately; no extrapolation to
current GLM/Luna consolidated prompts is supported. The next proposed action is
human policy calibration on a few frozen examples before another prompt trial.
No policy, label, prompt or model-setting changes are made by this diagnosis.

Zero provider calls and USD 0 cost. All 9,372 checked predecessor sealed files
remain unchanged. Detailed evidence, per-answer reviews, quantitative analysis
and the independent synthesis review are bound by the compact result pointer.
This is analysis/documentation-only work. Documentation inspection and
git diff --check passed. No commit or push; stop for discussion.

## Active redesign discussion — 2026-10-13

### Abstract and goal

The user asks to restart adequacy rules from the question/answer requirements,
with conclusion and supporting-reasoning binary checks, neutral-point handling,
failure enumeration and subsequent synthetic dataset regeneration. Pause further
prompt experiments; define and review the grading contract first. This changes
09F's active next step from prompt tuning to rubric design, not its historical
implementation or results.

### Inputs and outputs

Use the conversation, Decision 006, preserved failure diagnosis and development-only
09A.3 exact reference controls. The [redesign discussion draft](../../docs/specs/task09f_adequacy_redesign_draft.md)
records user direction, all 19 exact development questions grouped into seven
proposed demand types, candidate requirements, failure coverage, unresolved
binary/aggregation choices and a versioned regeneration sequence.

### Research, plan and review

Inspect RAGChecker and FActScore as primary examples of decomposed diagnostic
assessment; neither establishes the validity of this proposed reasoning rubric.
Review question types and contrastive examples before selecting component checks,
aggregate scoring or revised labels. Separate source support from argumentative
support and point validity from joint sufficiency. Two bounded subagents reviewed
question demands and failure coverage; the latter independently reviewed the draft
and found no blocking issues. Question categories and minima remain proposals.

### Validation and acceptance boundary

The 09A.3 reference-control binding was hash-verified; its 19 case IDs match the
complete proposed taxonomy without duplication. Inventory review read development
records only. User direction and unresolved choices are explicitly separated.
Documentation inspection and git diff --check validate this planning change.
No code tests are required for this docs-only update. The planning deliverable
is complete; the rubric itself remains under user review.

### Non-goals and next step

No model calls, prompt edits, synthetic regeneration, relabeling, reference edits,
held-out payload access, code changes, commit or push. All prior artifacts and
existing work remain preserved. Review question-specific requirements and failure
examples next. Once agreed, write the bounded regeneration/implementation contract
with explicit execution and spending caps, fresh versions and provenance; reconcile
Decision 006 and other authoritative rules before replacing the old runtime.

### Development intent labeling proposal — 2026-10-14

The user requests proposed intent labels for all 19 development questions,
grouped by label and descending confidence. The [intent review](../../docs/specs/task09f_question_intent_review.md)
contains six rebuttal/challenge and thirteen document-explanation proposals,
with exact wording, qualitative confidence and rationale. All assignments remain
pending user confirmation; question intent must not encode expected answer polarity.
A bounded independent wording-based review informed the ambiguous cases. All 19
IDs are unique and match the hash-verified development publication. No runtime,
answer, reference or expectation changes; no provider calls or held-out access.
The review belongs to the active rubric redesign. Next: user confirms or corrects
intent labels before downstream prompt/schema integration. Documentation diff
validation passed; no commit or push.

### Intent review decision — 2026-10-14

Kyle confirms only C007 as rebuttal; all other 18 development questions are document
explanation. The intent review records the accepted mapping and retains the original
six/thirteen proposal as superseded history. Skeptical question wording must not
be treated as an instruction to rebut. Original confidence estimates no longer
qualify the accepted human intent labels. This exposes limited rebuttal coverage
(one development case), not authorization to expand the dataset. No synthetic score
labels or runtime prompts changed. Documentation diff checks passed.

### Authorized held-out question wording review — 2026-10-14

Kyle requests inspection of the other 30 questions to assess existing rebuttal
coverage while avoiding dataset revisions. This explicitly authorizes reading
held-out question wording for intent review only. The [wording review](../../docs/specs/task09f_heldout_intent_wording_review.md)
proposes C002 as the sole additional rebuttal candidate (medium confidence), C003
as borderline document explanation, and the remaining 28 as document explanation.
All test assignments await user confirmation. An independent bounded review agreed.

Only target/test.jsonl (case_id and question) was read; its release hash and all
30 unique IDs were verified. No answers, evidence, predictions, evaluation results
or synthetic reserved payloads were inspected. No benchmark/runtime mutations,
question rewrites, inference or dataset expansion. All 30 test question wordings
have now been exposed during rubric design and must not be described as unseen
in future methodology. This limited exposure does not authorize answer inspection
or tuning against test outcomes. Documentation diff checks passed; no commit/push.

### Held-out intent confirmation — 2026-10-14

Kyle confirms C002 as rebuttal and C003 as document explanation: C003 is nearly
rebuttal-like but does not require rebuttal framing. All remaining test questions
retain document-explanation intent. The accepted planning mapping is now two
rebuttals across 49 questions (C007 development, C002 test) and 47 explanations.
No runtime, published dataset, answer or score-label changes. The user notes that
many potential rebuttals involved external information; preserve this as a future
design consideration, not authority to invent premises or expand this dataset.
Documentation diff checks passed.

### Direction change: no rebuttal questions — 2026-10-14

Kyle requests rewriting C007 and C002 to eliminate rebuttal tasks. The
[replacement-wording draft](../../docs/specs/task09f_question_rewording_review.md)
provides neutral document-explanation versions with original wording and migration
limits. This supersedes the mixed-intent implementation plan, not the historical
intent records for the frozen questions. C007 asks for documented mobility goals
and how design advances them; C002 asks what the DEIR says about vegetated barriers
without demanding additional universal requirements. Both await wording review.

No frozen questions, references, synthetic labels or runtime prompts changed.
C002 answerability/reference alignment remains unverified: its test answer/evidence
was not opened. Any eventual publication must version the changed questions and
review affected references/expectations without transferring old approvals or
results automatically. No inference, commit or push; documentation diff checks pass.

### Source mapping for replacement questions — 2026-10-14

Kyle asks which citable sections support all eight wording options and whether
C002 dense vegetation is required or recommended. The source mapping appended to
the [wording review](../../docs/specs/task09f_question_rewording_review.md) corrects
C007's compound what/how label, proposes a single mechanism question, and identifies
1–2 core canonical sections per C007 option (versus 4 in its original reference).
C002's source descriptions are location-specific recommendations/proposals; rail
planting's visual/noise functions must not become unsupported air-pollution claims.
The general vegetation-rationale and efficacy-assessment options lack direct
support in the reviewed packet. Narrow what/yes-no options use approximately 3–4 core
units versus 16 cited in the original reference, subject to later scope review.

This user request explicitly expands C002 exposure to cited source text and
reference citation-ID metadata. Prior wording-only statements are historical;
C002 evidence is now visible during design. No other held-out evidence, model
outputs or test results were examined. A bounded independent source review agrees.
No frozen artifacts or runtime changed, no inference or commit/push. Documentation
checks passed; wording remains for user selection.

### C002 replacement selected — 2026-10-14

Kyle selects the measures-and-purposes question: “Where do the DEIR and Specific
Plan propose or recommend dense vegetation screening, and what purposes do those
treatments serve?” The wording review records three core candidate sections,
including two Appendix A sections. Selection does not mutate the frozen release
or transfer reference approval. C007 wording remains pending; source check confirms
its six current citations are all main-DEIR occurrences (four unique sections).
Historical Appendix F.1 material was already excluded, so no accepted appendix
citation is removed. Documentation diff checks passed.

### C007 selected wording and citation review — 2026-10-14

User selects the design-speed how-question and requests original citations plus
additional-source search, one question at a time in the earlier review format.
Fresh external namespace09f_20261014_question_revisions_v1/C007 holds the selected
question, five search plans/receipts, complete AppendixF.2 candidate, summary and
display_001.md. Proposed answer uses retained Purpose/Geometric Design plus new
AppendixF.2 Challenges and Opportunities (PDF12–13). No C002 review this turn.
The original two sections were independently reviewed for sufficiency; a separate
source check assessed the added safety warrant. Dataset and human-approved
reference remain unchanged pending review. FTS5 runtime fallback is recorded;
no source-boundary/edition holds were bypassed. Documentation diff checks pass.

### C007 multimodal revision — 2026-10-14

User explicitly authorizes Final Appendix F.1 and requests walking/cycling context.
The version-2 C007 display and full F.1 Geometric Design candidate preserve Final
provenance, distinguish speed effects from lane-removal/path effects, and propose
three core sections. Prior review artifacts remain unchanged. See the wording
review for the proposed optional-context adequacy interpretation. Answer/citation
review remains pending; C002 remains next. No inference or frozen-data changes.

### C007 replacement approved — 2026-10-14

User approves the full C007 question, conclusion, three support points and five
citations. External C007/approved_revision_003.json and display_003.md preserve
that exact answer and approval; closeout_003.json binds them. F.2 and Circulation
Element are included alongside Purpose, Geometric Design and Final F.1. Previous
versions remain intact and verified. This accepted replacement is ready for the
next versioned publication; the historical release is unchanged. Next: C002
answer/citation review, then remaining rubric decisions and versioned regeneration.
Documentation diff checks pass; no inference, commit or push.

### C002 first answer/citation review — 2026-10-14

Original C002 citations and four additional lexical searches support a proposed
four-location answer. New Appendix A Green Edges evidence explicitly includes
dense East Rail Green Edge planting. Building-service screening provisions raise
a scope choice under the current broad question; answer and scope await review.
See the question-rewording review and external C002/display_001.md. Original
artifacts and frozen release remain unchanged; no inference, commit or push.

### Both question/answer revisions locked — 2026-10-14

User approves C002 and C007 and requests format consistency review. Approved
schema-normalized records/displays now live in question_revisions_v1/locked_v1.
Both pass maintained answer validation; all 49 historical records also pass a
structure-only audit. C002 S031/S040 are context metadata only, not cited in answer
points; Frontage Road is support. C007 retains its five approved support citations.
All prior review artifacts and frozen release files were verified unchanged.
Independent review covers formatting and role handling. No provider inference,
synthetic regeneration, runtime change, commit or push. Remaining rubric decisions
precede versioned dataset publication/regeneration.

### Authorized question-set publication and rubric resume — 2026-10-14

**Goal:** Publish the two locked replacements in a fresh 49-case local release,
then reconcile prior human calibration decisions and enumerate unresolved rules.
**Inputs:** Task08 release, unchanged split/corpus, locked_v1 C002/C007 approval seal.
**Outputs:** task09f_20261014_v1 release, reproducible publication/verification
receipts and current rubric-resume note. No model inference or regeneration.
**Plan:** Reuse maintained artifact I/O, answer schemas and citation resolver;
preserve 47 case bytes, replace only approved two, regenerate target projections,
reference index and overlap audit, bind predecessor and new approvals, independently
review, then seal completion last. Context-only references must survive indexing
even though they are not answer points. Preserve original source/case identities.
**Learning/research:** Inspect the prior release exporter/verifier and maintained
reference resolver; old exporter indexes only used citations and cannot be reused
unchanged for approved context-only metadata. Use narrow versioned publication glue.
**Validation:** Exact input seals, original49 identities/19–30 split, only two changed
question/answers, target-only field schema, canonical role resolution, source hashes,
all references and inventory closure, independent review and git diff --check.
**Boundaries:** C002 remains test with its authorized design exposure recorded;
no other held-out semantic review, prompts, labels, reserved data, runs, commit or
push. Historical releases and results remain bound to their original versions.

### Publication and labeling resume outcome — 2026-10-14

Published `task09f_20261014_v1` with49 cases, unchanged19dev/30test assignment
and35-source corpus. Only C002/C007 changed;47 case bytes and historical index
rows remain identical. Revised target projections, reference index, identity
mapping and overlap audit are bound by a new handoff and completion inventory.
Overlap is23 pairs/14cross-split under the unchanged permissive evidence policy.
The [result pointer](../../docs/specs/task09f_question_publication_result.json)
owns current release bindings. Target rows remain only case_id/question.

Preparation and closeout scripts are preserved with the release. A first unsealed
preparation attempt stopped because the57-case lineage mapping includes deferred
cases; it was preserved separately and the builder corrected to update only the
49 published-case pointers. No predecessor artifact was changed. Both source
seals, all source canonical hashes, all49 structural records, exact47 unchanged
cases, role resolution, projections and inventory closure passed. Independent
prepared-release review passed; final sealed verification and the maintained
judge-packet release consumer check also passed. Documentation diff check passed.
No inference, synthetic generation, commit or push.

The rubric draft is reconciled with later user decisions; the stale draft is
archived rather than silently discarded. Grounding/adequacy separation, genuine
basis versus restatement and neutral treatment are settled. Remaining decisions:
conclusion versus support completeness/essentiality; explicit contradiction score
mapping; abstention branch; final diagnostic schema and a small mixed failure/control
calibration panel. The next step is human development labeling, not another prompt
experiment. Old labels and results do not transfer to the revised release.

### Answer-layout decision and judge test requirement — 2026-10-14

User standardizes list answers as a complete bulleted conclusion followed by
supporting points. Support may map one-to-one or jointly to several list items;
judge validation must test equivalent good answers in both layouts, plus missing
basis and invalid-reasoning controls. No positional or point-count matching rule.
C011 uses prose/paragraph modeling format. See current rubric discussion for the
approved review decisions. These are future validation requirements, not tests
already run; publication and inference remain unperformed for these revisions.

### Scoring decision — 2026-10-14

User approves first-pass gated aggregation: failed conclusion0 regardless of
support; passing conclusion with failed support1; both pass2. No contradiction
veto. Abstention is pre-judge routing with not-evaluated components; denominator
choice is intentionally deferred, retaining raw statuses/components/counts.
Treat abstention detection as a verified routing prerequisite rather than a
semantic judge comparison metric. Next: consolidate the accepted rubric and
versioned reference revisions before implementation/regeneration. No model calls.

### Maintained rubric and second question publication — 2026-10-14

**Authorization:** Kyle approves the consolidated rules, requests a maintained
official document containing the general rules only, replaces dataset examples
with invented examples from unrelated contexts, and authorizes publication of the
new question/answer set before discussing next steps.

**Outputs:** `docs/specs/adequacy_labeling_rules.md` and fresh local release
`task09f_20261014_v2`. Publish the eight approved subsequent revisions (C050, C036,
C016, C031, C011, C020, C025, C043) and normalize C002's approved four-location
conclusion to the approved bullet layout. Preserve C007 and all other case bytes,
the 19/30 split, full corpus, historical releases and synthetic/reserved artifacts.

**Plan and learning:** Reuse maintained answer validation, reference resolution,
artifact I/O and the preceding publication/verifier pattern. Generic rubric examples
illustrate logical boundaries without embedding benchmark questions, answers or
case identifiers in reusable judge instructions. Keep calibration history and
case-specific required lists outside that official rule document. The new semantic
contract is authoritative for future migration; prior runtime/results retain their
original contract. No new model input visibility or diagnostic schema is selected.

**Validation:** Independently review rubric fidelity and prepared release against
approvals; check every case structure, target-only projections, canonical citation
roles, context-only exclusions, exact unchanged bytes, split/corpus identities and
source hashes. Seal completion after independent review; run release verifier and
maintained downstream intake verification, then documentation diff checks.

**Limits:** Local artifact publication only, no provider calls or spending, no
regeneration, prompt/runtime changes, commit or push. Authorized test reference
design exposure remains disclosed; no test predictions or reserved payloads.
Stop after publication to discuss the implementation/regeneration sequence.

### Maintained rubric and second publication outcome — 2026-10-14

The [official adequacy rules](../../docs/specs/adequacy_labeling_rules.md) contain
the approved general contract only. Illustrations use invented recipe, library and
backup contexts, with no benchmark cases, IDs or reference answers. The discussion
record retains historical human examples and case-specific requirements separately.
Decision 006, sprint guidance and runtime documentation now explicitly distinguish
the approved replacement policy from historical implemented semantics.

Published and sealed `task09f_20261014_v2`; the [new result pointer](../../docs/specs/task09f_question_publication_v2_result.json)
binds the release, independent audit, final verification and downstream compatibility
receipt. Nine records changed: C002 list formatting and eight approved revisions
C011/C016/C020/C025/C031/C036/C043/C050. Other 40 records and reference-index rows
are byte-identical, including C007. All 49 cases, the 19/30 split, 35-document corpus,
and source bindings are preserved. The revised release has eight complete-list
conclusions and C011's prose modeling explanation. Shared-evidence overlap remains
23 pairs, 14 across splits; no new independence claim is made.

Normalization is explicit: approval artifacts summarize the accepted discussion;
reference records combine approved item wording with retained supporting prose.
The publication does not claim byte-exact reproduction of historical chat displays.
A first unsealed preparation exposed inconsistent inherited approved_roles metadata
and context vocabulary. It and its locks remain in the external publication
namespace; fresh normalized records align occurrence roles and approved_roles.
This repair matters because maintained reference resolution reads approved_roles.
C031 occurrences sharing the same canonical table correctly use support precedence.

Independent review passed for the general rubric and all nine revised answers,
including context exclusion and required-item/condition fidelity. Both prepared
and final release verification passed; exact completion inventory, approval/input
hashes, prior-release preservation, target-only projections and canonical source
hashes were checked. The maintained judge_packet_publication._verify_release
consumer accepts the new release with 19 development IDs and 35 corpus sources.
Documentation links, explicit new-file whitespace checks and git diff --check pass.
No application code changed in this publication; validation used the artifact
verifier and maintained consumer rather than unrelated code-test execution.

The release includes an immutable snapshot of the official policy. Runtime, prompts
and synthetic labels remain unchanged. Authorized test-reference design exposure,
including C011's human calibration, is disclosed; no model test outputs or reserved
payloads were used. Zero provider calls and USD 0 spending; no commit or push.
Next: discuss the bounded schema/prompt migration and small revised development
calibration set before regeneration or inference.

### Grounding revisit queued; adequacy synthesis planning next — 2026-10-14

Kyle requests a separate follow-up for grounding's second pass, after completing
this adequacy task. [09F.1](09f1_revisit_grounding_judge.md) now owns future official
grounding rules with unrelated invented examples, grounding-specific synthetic
data and one-model component evaluation. The overall design uses four separately
identified datasets over the 19 development questions: adequacy conclusion/support
and grounding points/conclusion. Specify dependency inputs and distinguish isolated
component tests from pipeline tests; do not treat four datasets as independent base
question samples. Current 09F resumes planning the two adequacy datasets. This turn
creates the follow-up contract only: no new policy approval, synthesis, runtime
change, test/reserved payload access or model calls.

### Perturbation extension and conclusion filter — 2026-10-14

At Kyle's request, the [adequacy perturbation plan](../../docs/specs/task09f_adequacy_perturbations.md)
extends the original 31-category catalog with explicit list, basis, neutral-content
and reference-authority distinctions. The historical catalog and old expected
scores are unchanged. The conclusion-only selection includes passing controls,
incorrect/incomplete conclusions and conditional input-independence checks. Support
and citation failures do not automatically fail C; clean abstentions skip it.
No generation, new labels, inference or request-schema decision occurs here.

Bounded independent review passed; added equivalent split/combined conclusion-list
controls to complement duplicate-item omissions. Documentation links/whitespace
and git diff --check passed. No historical catalog or published artifact changed.

### Active handoff: direct conclusion-only synthesis — 2026-10-14

Kyle selects the simpler C input: question, candidate conclusion and approved
reference conclusion only, with no supporting fields or source/citation material.
The coding agent is the generator; no provider API is used. Author one example
per applicable filtered type for each of the 19 development questions. The
[handoff](../../docs/specs/task09f_conclusion_synthesis_handoff.md) consolidates exact
input fields, slot allocation, separated labels, review, publication and finish
conditions for a separate chat. Combined catalog rows are one slot each; with
unchanged controls the maximum is 399 records, subject to applicability and
deduplication. The original catalog and published release remain unchanged.

This handoff supersedes earlier suggestions to select a generation provider or
API spending caps and earlier unresolved C visibility language. Only direct
conclusion authoring is in scope; judge execution, support synthesis and grounding
remain deferred. This preparation turn updates instructions, not generated data.

### Support-only synthesis handoff — 2026-10-14

Kyle accepts comparing support judging with and without the approved reference
explanation during evaluation, using the same synthetic cases and fixed labels.
The [support handoff](../../docs/specs/task09f_support_synthesis_handoff.md) now
records candidate question/conclusion/support/qualification inputs, a separate
reference conclusion/explanation supplement, selected passing/failing/boundary
slots and independent S review. Reference correctness never determines candidate
S; source factuality remains grounding. Reference sufficiency is reviewed rather
than inferred from historical answer approval.

Carry forward direct agent authoring without APIs and one example per applicable
type across 19 development cases. There are 29 declared slots including baseline
per case, with explicit inapplicability, uncertainty and duplicate accounting.
This documentation prepares another chat; no data generated or judge run here.
Concurrent conclusion work and its input contract remain untouched. Grounding
and judge configuration/budget decisions remain deferred.

Independent handoff review passed: 29 slots, component independence, reference
condition parity, source-factuality boundary and parallel-work isolation checked.
Clarified conclusion/whole-argument qualification scope. Documentation link and
whitespace checks and git diff --check passed; no runtime/data changes.

### Binary contract and small calibration review — 2026-10-14

Kyle reports conclusion synthesis complete and requests contracts and calibration
for both C and S. His subsequent instruction explicitly excludes implementation
and judge execution. The [proposed contract](../../docs/specs/task09f_binary_judge_contract.md)
therefore specifies visibility, independent boolean outputs, diagnostic reasons,
qualification attachments, routing/error statuses and score joining for review.
The approved semantic policy is unchanged; the historical runtime is untouched.

The [calibration review](../../docs/specs/task09f_binary_calibration_review.md)
selects 24 unchanged published C examples over four dev questions and prepares
12 directly authored S examples over three of those questions. The S examples
have separate proposed C/S labels on the same full answer, including C=no/S=yes
boundaries. Its small panel is isolated from the full support-synthesis chat.
Neither independent review nor selection promotes proposed labels to human gold.
The panels are deliberately diagnostic, not representative performance samples.

Bounded agents prepare C selection and S examples; an independent agent reviews
contracts, input isolation and labels. Validation checks exact input fields,
attachments, inventory hashes, source identity, grouped/separate equivalence and
reference projection parity across panels. Routing/mechanical examples remain
review fixtures, not claims of implemented or tested behavior. No source-factuality
assessment or test/reserved payload access is included.

Learning: independent decisions need isolated inputs and candidate-level joins.
A question ID alone cannot join independently generated C and S mutations.
The existing Inspect infrastructure can retain score metadata and separate targets
(see its [scorer documentation](https://inspect.aisi.org.uk/scorers.html)); reuse it
later instead of adding another execution framework. Preserve invalid-output
statuses separately instead of allowing a generic incorrect score to mask them.

Finish at user review of the contract and labels. No provider calls, judge runs,
prompt tuning, implementation, credential access, commits or pushes belong to
this step. Execution settings and caps remain future work after review.

Independent review found no blocking issues or label changes. Explicit nonblank
ID and unique attachment-target constraints resolve the minor precision finding.
The [result pointer](../../docs/specs/task09f_binary_calibration_result.json) binds
the reviewed package: 24 C examples (12 yes/12 no), 12 S examples (7 yes/5 no;
paired C labels 10 yes/2 no). The small panel lacks a C=no/S=no pair and is not
exhaustive. Both manifests' inventories and cross-panel reference projections
passed validation, as did documentation links/whitespace and git diff --check.
Only documentation and external review artifacts changed in this step; unrelated
pre-existing code and documentation edits were retained. Ready for user review.

### Contract simplification after user review — 2026-10-14

Removed the projection-preservation instruction and the calibration/implementation
boundary section from the proposed contract at Kyle's request. Qualifications are
now ordered text strings, with no qualification IDs or applies_to mapping. The
previously saved review package remains preserved and binds the earlier contract;
its S projection will need updating before future execution. The calibration
review documents that mismatch. Proposed labels are for discussion, not a request
for exhaustive human relabeling. No implementation or judges run.

### Support-panel qualification projection updated — 2026-10-14

At Kyle's request, prepared binary calibration v2 with candidate and reference
qualifications represented as ordered text strings. Removed only qualification
IDs and applies_to metadata from model inputs; preserved qualification wording,
all other answer fields and proposed C/S labels. The 24-row conclusion panel is
byte-identical. Original v1 artifacts remain unchanged. Updated provenance hashes
and recorded the removed metadata separately for traceability. The current
[result pointer](../../docs/specs/task09f_binary_calibration_result.json) and
[review guide](../../docs/specs/task09f_binary_calibration_review.md) route to v2.
No implementation, judge calls, provider calls, commits or pushes.

Independent projection review passed all 12 candidate inputs and 12 reference
supplements, text/label preservation, provenance hashes, review-text consistency
and v1 seal preservation. V2 completion inventory and git diff --check passed.

### Three conclusion labels confirmed — 2026-10-14

Kyle confirms C=no for C056-F05_F09, C017-F07 and C050-A10. The
[calibration review](../../docs/specs/task09f_binary_calibration_review.md) records
these limited human approvals separately from sealed proposed labels. Clarified
that C requires completeness and substantive reference agreement; no policy or
label-value change. C017's distributed solar storage assumption is material and
is distinct from the excluded regional battery facility. Prior artifacts remain
unchanged. Documentation whitespace validation passed; no judges ran.

### Published support examples selected for calibration — 2026-10-14

Kyle accepts the existing 24-example conclusion suite for calibration and requests
that the 12 support examples come from the newly published support synthesis.
The v3 panel replaces the provisional directly authored support examples with
published, independently reviewed, paired-comparison-eligible examples over
C056, C007 and C050. The accepted conclusion selection stays byte-identical.

Select C056 BASE/O01/A04/A05; C007 BASE/P09/A06/F10; C050 P03/P04/B01/B02.
Resolve shared coverage through the published slot mapping instead of generating
a replacement or duplicating an example. Preserve published S labels and all
candidate text; project qualification metadata to plain text per the current
contract. Keep exact originals and selection provenance separately. No new C
labels are claimed for this support-only selection. C051 and unresolved slots
are excluded. All earlier panels and full synthesis artifacts remain preserved.

The result pointer and calibration review route to the new panel. No runtime
implementation, provider calls, judges, prompt tuning, commits or pushes.

Independent parent review verified exact published text projection, all 12 S labels,
reference-condition parity, paired eligibility, source and panel inventory hashes,
and unchanged conclusion files. Selected 7 proposed S=yes and 5 S=no examples.
C050 P04 resolves to shared S0395; its text matches grouped S0397. The v3
completion binds the current contract. git diff --check passed. Stop for review.

### Calibration selections and prompt openings accepted — 2026-10-14

Kyle accepts the published 12-example support selection alongside the previously
accepted 24-example conclusion suite. He approves the expanded benchmark-role
openings for both judges. The [prompt text](../../docs/specs/task09f_binary_judge_prompts.md)
records those openings with the unchanged proposed decision rules and output
instructions, plus the optional S reference paragraph. No inference authorization
is inferred from this approval. Existing artifacts remain unchanged. Documentation
whitespace checks passed; no runtime edits, judge calls, commits or pushes.

### Authorized binary implementation and first GLM calibration — 2026-10-14

Kyle authorizes implementation, offline validation and the bounded single-model
calibration pass. Implement both C/S interfaces using maintained Inspect, transport,
receipt, provider allowance and budget infrastructure. Run C24 first, then S12
without reference. Preserve accepted prompts and selections; no tuning, expansion,
reference-condition experiment or other model. Independent implementation review
precedes calls. Credentials load through untracked .env without display.

Fixed ceilings: C 26 requests / 106496 output tokens / USD 0.50 / 900 seconds;
S 14 requests / 57344 output tokens / USD 0.50 / 900 seconds. Each includes two
identical actual-request cache probes, excluded from accuracy. Serial execution,
zero automatic retries, temperature 0, top_p 1, seed 0, reasoning medium, output
4096 per call. Replay saved receipts offline separately; report native cache hits
and receipt reuse distinctly. Provider input allowance is explicitly bounded and
is not claimed to be exact token counting. No live continuation resetting caps.

Primary documentation rechecked: [GLM pricing](https://fireworks.ai/models/fireworks/glm-5p3-flash)
USD 0.15/0.03/0.50 per million input/cached-input/output tokens;
[Fireworks caching](https://docs.fireworks.ai/guides/prompt-caching) uses shared
prefixes and session affinity. Preserve the approved prompt at the start of each
request and assess native usage counters rather than assuming cache behavior.
Validate focused tests, make fix, make check, offline artifacts and git diff --check.

### Binary implementation and bounded GLM outcome — 2026-10-14

Both component implementations, fixed-panel CLI and Make targets are complete.
The [result pointer](../../docs/specs/task09f_binary_glm_result.json) binds the
external report, receipts and independent review. C: 23/24 valid; S without
reference: 11/12 valid. All valid judgments match accepted calibration labels
(valid-only accuracy and macro-F1 both 1.0). Coverage is 95.83% and 91.67%.
C050-A02 and S0073/C007-F10 returned correct judgments inside Markdown fences;
both remain invalid_output/null, with no output repair, retry or prompt tuning.

All 40 calls (36 evaluation + four probes) completed within fixed caps. Native
second-probe cache reads: C768/803 and S1280/1324 input tokens. All 36 evaluation
receipts replayed offline with zero dispatch. Estimated total cost USD0.00762568,
not invoice-confirmed. Exact settings, per-question results and limitations are
in the report. No claims of broader qualification or full-panel repeatability.

Independent code review passed after a same-answer aggregation adapter fixed its
integration finding; independent result review verified every receipt, reservation,
metric and cost. make fix passed; make check passed 4552 tests, one skipped. Final
adapter/affinity additions passed 46 focused tests and strict mypy. Offline audit
covered every input. git diff --check passed. No unrelated work or previous
artifacts overwritten, no reserved/test payload access, no commits or pushes.
Stop for user review before formatting changes, reference comparisons or expansion.

### Authorized format repair and three-model binary comparison — 2026-10-14

Kyle requests the previous prompt serialization fix and tests of Luna and Haiku.
Retain the binary v1 prompts and results, add the historical format-only checklist
as `task09f.binary_adequacy.format.v2`: first/last characters are braces, no fences
or language label, exactly three required fields, JSON booleans and nonblank
explanations. No semantic rules or parser tolerance change. Re-run the same C24
and S12 without reference on GLM, Luna and Haiku; no dataset expansion.

Caps per model: C26/S14 generation calls (two cache probes per component),
C106496/S57344 output tokens, USD1 per component, 900 seconds per component,
4096 output tokens per request, zero retries. Overall maximum 120 generation calls,
80 counter calls (Luna exact and Haiku estimated), USD6, 491520 output tokens,
5400 seconds across six serial components. Counters are at most one per generation
attempt; no counter retry. Credentials load through .env without display.

GLM uses temperature0/top_p1/seed0 and medium reasoning with prompt-requested JSON.
Luna uses Responses medium reasoning, native structured output and exact counting;
Haiku uses adaptive medium, native structured output and conservative allowance
with its estimated counter. Sampling settings unsupported by the maintained Luna/
Haiku reasoning configurations are omitted, not described as fixed seed or zero
temperature. Native output enforcement differs by provider and must be disclosed.

Primary references rechecked: [Luna model/pricing](https://developers.openai.com/api/docs/models/gpt-6-luna)
and [Haiku model/settings](https://platform.claude.com/docs/en/models/haiku-5-5/overview).
The older whole-answer formatting instruction is in adequacy_judge.FORMAT_PROMPT;
its historical results remain separate. A single new pass cannot prove durable
repair or distinguish prompt effects from sampling variation. Review both validity
and semantic control regressions, preserving formatting improvements separately.

### Binary formatting and three-model outcome — 2026-10-14

The [comparison result](../../docs/specs/task09f_binary_models_format_result.json)
binds the frozen C24/S12 run and full per-question failures. GLM C22/24 correct
(23 valid), S12/12; Luna C24/24, S10/12; Haiku C24/24, S11/12. Luna/Haiku outputs
are all valid. Both old GLM fence failures now pass; a misspelled explanation key
causes a different invalid and a reversed solar-accounting operation causes a
semantic false positive. GLM correct/selected remains 34/36 overall. The single
pass cannot establish causal or durable formatting repair.

Luna and Haiku both accept a verbatim conclusion repeat as support. Luna also
rejects an accepted alternative causal explanation. These are distinct review
items; no semantic tuning or automatic model selection followed. Native schema
enforcement differs across providers and is disclosed in the report.

All six runs completed within caps: 120 generations, 80 native counters, zero
retries, estimated USD0.021743120 (not invoice-confirmed). Every second identical
actual-request probe showed native cache reads. All 108 evaluation receipts replayed
offline without calls. Independent implementation/result review, 54 focused tests,
make fix, make check (4566 passed, one skipped), and git diff --check passed.
Prior artifacts and reserved/test boundaries remain preserved; no commits/pushes.
Stop for user review before additional tuning, expansion or reference-condition tests.

### Authorized three-repeat binary stability study — 2026-10-14

Kyle requests three runs each across GLM, Luna and Haiku to measure stability.
Run three fresh repetitions of the accepted C24/S12 panels with the unchanged
format.v2 prompt, model configurations, sampling settings and strict parser.
Treat the preceding single pass as historical context, not one of the three.
No louder prompt or semantic revision is bundled into this stability measurement;
consider precise rule clarification after observing recurring errors.

Use fresh external run directories, serial execution and zero retries. Each of
18 model/component/repetition cells retains C26/S14 generation calls, two actual
request cache probes, 4096 output tokens per call, C106496/S57344 reserved output
tokens, USD1 and 900 seconds. Aggregate maximum: 360 generations, 240 native
counter calls, 1474560 output tokens, USD18, 16200 seconds. Stop the study on an
execution failure or budget halt; never reset a failed cell's allowance. Load
credentials through .env without display. No dataset expansion or S reference arm.

Report each repetition and pooled accuracy/macro-F1/coverage, per-question and
per-example failures, decision changes including invalids separately from valid
boolean flips, persistent versus intermittent errors, caching, cost and saved
receipt replay. Keep explanation wording variation separate from label stability.
Independent offline review verifies frozen inputs, prompt equality, receipts,
metrics, bounds and preservation. Existing implementation checks passed immediately
before this study; no runtime changes are planned. Run git diff --check for docs.
Stop for user review after the fixed repetitions, with no adaptive prompt tuning.

### Three-repeat stability outcome — 2026-10-14

The [result](../../docs/specs/task09f_binary_stability_result.json) binds all 18
completed cells with unchanged prompts/configuration. Correct/selected by repetition:
GLM C23/24,23/24,23/24 and S12/12 throughout; Luna C24/24 throughout and
S11/12,12/12,11/12; Haiku C23/24,23/24,24/24 and S11/12,12/12,12/12.
Only one output was invalid: GLM repeated an extra misspelled explation key.
Five model/example pairs changed valid Boolean decisions; one additional pair
changed validity. All failures were intermittent. No rule or parser changed.

Luna C and GLM S are the strongest observed component results on this calibration
panel, not a qualification claim. Solar-operation misreading, repeated-conclusion
support and incidental numeric detail account for the semantic failures. The prior
alternative-explanation error did not recur. Review targeted clarifications before
further inference; proposals are recorded in the report, not applied to prompts.

All 360 generations and 240 counters completed without retries or halts within
caps. Estimated token cost USD0.050533090, not invoice-confirmed. All second probes
show native cache reads; 324 evaluation receipts replay offline with zero requests.
Independent audit verifies every receipt, metrics, costs, limits and prior seals.
No runtime changes required another implementation test cycle; prior checks remain
recorded above, and git diff --check passed for current docs. No commits or pushes.

### Authorized isolated prompt trials — 2026-10-15

Kyle requests four independent edits, each derived from unchanged format.v2:
rename the output explanation field to reason (GLM full C24/S12 once); careful
conclusion reading on C017-F04 (all three models, five fresh requests each);
full-conclusion restatement on S0476 (all three, five each); completeness on
C056-P05 (all three, five each). These IDs are the specific failing examples from
the preceding study. No extra candidates or concurrent baseline calls are added.
The semantic arms retain explanation; the rename arm changes only the wire key,
strictly validates reason and then maps it to the internal explanation field.
Old keys, extra keys and typo repairs remain forbidden. Examples use invented
unrelated contexts; the reading example does not mention addition/subtraction.

Use the maintained provider and Inspect infrastructure with a narrow fixed-selection
runner. Repeat IDs differ only in evaluator metadata; model inputs remain identical.
No new cache probes: actual usage counters record cache reads during the requests.
Each of 11 component cells has USD1/900 seconds; requests are24/12 for GLM rename C/S,
or5 for each targeted arm/provider. Total caps:81 generations,30 native counters,
331776 output tokens,USD11,9900 seconds;4096output per request,zero retries. Stop on
execution/budget failure without resetting caps. Credentials load through .env.

[Official reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning-best-practices)
supports direct instructions and aligned examples. These are empirical clarifications,
not an assumption that stronger wording guarantees compliance. Preserve sampling,
provider schema differences, baseline prompts, prior artifacts and all dataset
boundaries. Independent preflight/result review, focused tests, make fix, make check,
offline projection/replay and git diff --check are required. Report each arm separately,
all failures, cache usage and costs; single-label targeted arms do not establish
full-class accuracy or regression safety. Stop for user selection/tweaks; no promotion.

### Isolated prompt trial outcome — 2026-10-15

The [result](../../docs/specs/task09f_binary_targeted_result.json) binds all 11 cells.
GLM reason-field rename: 36/36 valid, C23/24 correct (F1 .9583), S12/12 correct
(F1 1.0); only the existing C017-F04 semantic error remained. Reading C017-F04:
GLM2/5, Luna5/5, Haiku 5/5. Restatement S0476 and completeness C056-P05: 5/5 for
every model. All 81 outputs valid. Single-example arms report correct/5 and
coverage, not an informative macro-F1. Historical baselines are not concurrent.

GLM explicitly recognized the changed operation in one reading failure but accepted
it as an awkward paraphrase. This clarification does not fix GLM reliably. Rename,
restatement and completeness are promising candidates, pending user selection and
broader regression checks. Semantic arms were tested separately with explanation,
not combined with the reason-field change. No automatic promotion or extra tuning.

All 81 generations and 30 native counters completed within caps, with zero retries
or halts. Estimated cost USD 0.015632740; 81 offline replays used zero calls. Native
cache reads appeared in every cell; no new controlled probes. All 68 focused tests,
make fix, make check (4580 passed, one skipped), independent preflight/result review
and git diff --check passed. Prior artifacts and reserved/test boundaries remain
preserved. No commits or pushes.

### Authorized reading replacement with paraphrase control — 2026-10-15

Kyle approves the proposed no-repair reading appendix and five repetitions per
model on the operation error plus a valid paraphrase. Freeze existing C017-F04
(expected no) and C017-P01 (expected yes), both from the accepted calibration panel.
P01 explicitly subtracts planned onsite solar from demand and preserves all other
required claims. No candidate rewriting or new labels. Run GLM, Luna and Haiku,
five fresh calls per example, interleaved within each model's serial cell.

Version reading_no_repair.v4 replaces the previous reading appendix, deriving
independently from format.v2. Preserve the exact approved wording and unrelated
permit/inspection example; no reason-field rename or other semantic appendices.
Each model cell: 10 generations, 40960 reserved output tokens, USD1, 900 seconds.
Aggregate caps: 30 generations, 20 native counters, 122880 output tokens, USD3,
2700 seconds; 4096 per output, no extra probes, zero retries. Same model/sampling
settings, .env credentials without display, strict parser and offline replay.
No continuation after execution/budget failure. Independent preflight/result audit,
focused tests, make fix, make check and git diff --check. Report both examples'
sequences, correct/5, coverage, balanced combined metrics, cost and cache use.
Historical v3 results are descriptive, not concurrent baselines. Stop for review.

### Paired reading replacement outcome — 2026-10-15

The [result](../../docs/specs/task09f_binary_reading_no_repair_result.json) binds
30valid judgments. Incorrect operation C017-F04:GLM4/5,Luna5/5,Haiku 5/5; valid
paraphrase C017-P01:5/5 for every model. Combined GLM accuracy90%,macro-F1 .899;
Luna/Haiku accuracy andmacro-F1 1.0. Coverage100%for every model. The remaining GLM
failure notices adds but interprets it as netting, still repairing candidate meaning.
The apparent gain from prior2/5 is descriptive; no concurrent baseline ran.

All30generations,20counters and30zero-callreplays completed within caps. Estimated
costUSD0.005998575; cache reads observed for all providers. All71focusedtests,
make fix,make check(4583passed,one skipped), independentpreflight/resultreview and
git diff --checkpassed. Prior artifacts and reserved/test boundaries preserved.
No further prompt changes, promotion, commits or pushes. Stop for user review.

### Authorized consolidated five-pass comparison — 2026-10-15

Kyle requests combining the improvements and five fresh full-suite passes per model.
Consolidated.v5 C is format.v2 plus the latest no-repair reading appendix and
completeness appendix; S is format.v2 plus the whole-conclusion restatement appendix.
Both use the strict reason wire field. Do not stack the superseded reading appendix.
Preserve all component inputs, labels, prior prompts and artifacts. No dataset
expansion, support reference arm, additional prompt tuning or automatic selection.

Primary metrics are empirical pass^5: an example passes conclusion/support correctness
only if all five observations are valid and correct. Valid output pass^5 requires
all five outputs valid, irrespective of semantic correctness. Denominators are C24,
S12 and combined36. Do not raise pooled accuracy to the fifth power, drop invalids,
use majority voting or mix earlier runs into these five. Retain individual sequences,
per-pass metrics and failures as diagnostics.

Thirty component cells run in fresh directories: 5 passes × 3 models × C/S.
Each provider runs its C/S passes serially; the three independent providers may run
concurrently. Caps per cell:24 or12 generations,98304 or49152 reserved outputtokens,
USD1,900seconds;4096output per request. Aggregate:540 generations,360 nativecounters,
2211840outputtokens,USD30,27000 cumulative cell-seconds. No extra probes or retries.
Stop scheduling new cells on any execution/budget failure; allow already-started
bounded requests to finish and retain them. Never reset a failed cell's budget.
Credentials load through .env without display. Cache use is measured on actual
requests; every evaluation receipt is replayed offline separately.

Independent review validates exact combined prompts, full sealed selections,
pass^k metric implementation, receipts, limits and preservation. Run focused tests,
make fix, make check and git diff --check. Report the three pass^5 columns, failures,
caching and cost; this is still calibration on four base questions. Stop for review.

### Internet interruption and authorized recovery — 2026-10-15

The user confirms internet loss and requests resuming. Preserve all 202 returned
judgments unchanged, including semantic failures. Two requests have durable intent
but no returned response: GLM pass3 C050-BASE and Luna pass2 C017-F07. Replace each
once in a new recovery namespace; never overwrite or reissue the completed results.
Run the 336 never-dispatched requests. This explicitly supersedes the interrupted
study's no-retry rule only for those two missing-response requests.

The recovery plan binds every original artifact, exact unchanged source/config,
retained record and replacement intent. The 338 additional requests yield 540
received judgments across five passes, with 542 total generation attempts and
361 counters including the interruption. Reserve 2220032 total output tokens.
Keep cumulative spending within the original USD30 ceiling, including both uncertain
charges. Partial cells receive only USD1 minus their prior reserved spending and
900 seconds minus their recorded, rounded-up original active duration (GLM801s,
Luna667s); offline downtime is excluded. Their cumulative request caps rise from
24 to25 only for the replacement. Unstarted cells retain original caps. No further
retries, new samples, prompt edits or performance-based substitutions.

Report pass^5 on the five received judgments, explicitly conditional on transport
recovery. Report the two uncertain original attempts, their possible charges and
transport reliability separately. Their reserved worst-case cost USD0.008285025
is not assumed zero or included as a known invoice charge. Independent preflight
and final audit verify unchanged requests, retained judgments, aggregate caps,
replay and accounting. Stop for review after the resumed fixed study completes.

### Second interruption and authorized continuation — 2026-10-15

Kyle again confirms connectivity and requests continuing. Preserve 237 received
judgments and both earlier artifact roots. Resume in recovery_v2 with 303 additional
generations: two newly lost generation responses may be replaced once, while Luna
S0476 failed during counting before a generation intent/reservation existed. Retain
that counter failure separately despite the generic possibly_billed error flag.
Cumulative caps are 544 generation attempts, 363 counters, 2228224 reserved output
tokens and the unchanged USD30 ceiling. The new segment allows 228 counters.
Partial S cells retain only remaining original currency and active time: GLM815s,
Luna866s, Haiku803s. Four cumulative uncertain generation attempts reserve at most
USD0.016790425. No returned judgment is rerun. Stop on a further execution failure;
report transport recovery separately from all-five received-response metrics.

### Continuation checkpoint — transport interruption

The second recovery saved 32 additional judgments before another transport halt.
Across all three namespaces, 269/540 planned judgments are received, all structurally
valid; 265 match labels. Four semantic errors are preserved: GLM C017-F04 (pass3),
Luna C017-F07 (pass2), and Luna S0395/S0397 (pass1). Pass^5 is unavailable.
Independent audit verifies 1365 prior files unchanged, all native receipt chains,
274 generation attempts (five response-less) and 154 counters (three counter-only
failures). Known usage cost is USD0.049409570; uncertain generation reservations
add at most USD0.021296175 under recorded rates. The root remains an incomplete
checkpoint, not a completed study. All paid processes stopped; 271 responses remain.
See the recovery checkpoint pointer for the partial report and independent audit.

### Bounded resilient continuation — 2026-10-15

Kyle requests completing the full run after repeated interruptions. Resume the 271
missing observations and preserve all 269 received judgments; restarting from zero
would unnecessarily replace observed errors. A fresh recovery_v3 namespace may make
up to three attempts per missing observation, retrying only transport/counter errors
with bounded backoff. Returned valid or invalid model outputs are never retried.
This supersedes stop-on-first-transport-error for this continuation only.

Freeze exact requests, labels and sampling, all earlier receipts and each cell's
remaining currency and active-time allowance before dispatch. Additional ceilings:
300 generation attempts, 240 counter attempts, 1228800 reserved output tokens and
1800 wall seconds. Retain the cumulative USD30 spending ceiling and per-cell USD1
minus all prior reservations; active time remains 900 seconds per cell minus prior
segments. Backoff consumes the new segment's time. Record counter failures before
generation separately, retain uncertain charges, and stop at caps or nontransport
execution failures. Three independent provider workers may proceed serially within
each provider. Credentials load through .env without display. Independent preflight
and final audit, exact-request checks, offline replay and diff validation required.
Report five received judgments per example with transport conditioning disclosed;
no further prompt tuning, dataset expansion, model selection, commit or push.

### Wi-Fi restored continuation — 2026-10-15

Kyle confirms Wi-Fi restored and requests continuing. Recovery_v3 received no new
responses; its four generation reservations and six counter attempts remain charged.
Recovery_v4 retains the same 269 observations and exact runner implementation,
renewing the three-attempt transport policy for the 271 missing observations only.
Deduct 146 seconds conservatively from each of the three previously active cells
and the continuation-wide allowance. Remaining aggregate caps: 296 generations,
234 counters and 1654 active wall seconds, with original cumulative currency limits.
Preserve all v3 artifacts and uncertain charges. No completed answer is rerun.

### Consolidated five-pass outcome — 2026-10-15

All 540 judgments completed on the fixed C24/S12 panel. Empirical conclusion,
support and output-valid pass^5 respectively: GLM 23/24, 12/12, 36/36;
Luna 23/24, 9/12, 36/36; Haiku 24/24, 12/12, 36/36. GLM accepts the changed operation
in three of five observations. Luna misses the battery condition once and rejects
three accepted support examples at least once (five support errors total). Haiku
has no error in this calibration suite; no broader qualification is claimed.

The final continuation collected 271 responses with 271 generations and 211 counters,
without retries. Earlier 269 returned judgments remain unchanged. Across all attempts:
549 generation reservations, 371 counters, nine uncertain response-less generations;
eight earlier counter-only failures did not dispatch generation. Known response
cost estimate USD 0.093695445, uncertain-generation upper reservation USD 0.038942550;
actual missing-response billing unknown. Cache use appears in every provider's
actual requests; no additional cache probes. All 540 receipts replayed with zero
new calls. Pass^5 is conditional on disclosed transport recovery.

All earlier artifact inventories and dataset boundaries remain intact. Maintained
implementation validation already passed:99 focused tests, make fix, make check
(4611 passed, one skipped); artifact continuation adds six offline cap/retry checks,
exact-request verification, independent preflight/final audit and diff validation.
No further prompt changes, dataset expansion, model promotion, commit or push.
The result pointer binds the final report, independent audit and completion seal.

### Authorized support-basis clarification — 2026-10-15

Kyle requests pulling back the stronger anti-restatement instruction, adding the
clarification discussed after Luna's false rejections, and testing again. Bound
this to Luna on the unchanged full S12 calibration panel, five fresh passes (60
judgments). No C rerun, other-model comparison, reference-example arm or expansion.
Version support_basis.v6 derives from format.v2 plus strict reason output; it
replaces, rather than stacks, the stronger whole-conclusion restatement appendix.
The replacement preserves the prohibition on circular support, accepts concrete
implementation details that establish descriptive list claims, and permits obvious
inferential steps warranted by stated premises without inventing missing premises.
Only an unrelated invented museum booking/cancellation example enters the prompt.
No labels or candidate text change; approved semantics remain unchanged.

Freeze the exact prompt, unchanged native sampling/schema/settings, all S12 payloads
and labels, and the prior consolidated-v5 Luna60 results. Run in a fresh external
namespace. Caps:70 generation attempts,70 native counters,286720 reserved output
tokens,USD5 and900 wall seconds; per-pass USD1 and900 seconds within that shared
window. At most three attempts per missing response, backoff5/15seconds, transient
transport failures only; retain all reservations and uncertain charges. Never retry
a received valid or invalid output. No cache probes; load .env without displaying
credentials. Stop on nontransport errors or exhausted caps.

Report support-correct and output-valid empirical pass^5 over12examples, per-case
five-run sequences, regression controls, pooled accuracy/macro-F1/coverage, cache
usage and cost. Historical v5 comparison is descriptive, not concurrent causal
proof. Independently review prompt boundaries, frozen inputs, caps and final output;
run focused tests,make fix,make check,offline replay andgit diff --check. Stop for
review with no automatic promotion, additional tuning, commits or pushes.

### Support-basis clarification outcome — 2026-10-15

The Luna-only S12 five-pass test completed all 60 responses without transport
failures or retries. Support-correct pass^5 improves descriptively from 9/12 to 11/12;
output-valid pass^5 remains 12/12. New pooled agreement 58/60 (96.67%), macro-F1
0.9653, coverage 100%. All three prior false-rejection examples S0053/S0395/S0397
now pass 5/5. The remaining nine examples are regression controls: eight remain
correct 5/5, while S0476 falls from 5/5 to 3/5. In passes 1 and 5 Luna accepts support
that is verbatim identical to the entire conclusion, counting the already-stated
residual-flooding figures as a basis. No labels or candidate text were changed.
This is a measured tradeoff, not automatic promotion or proof of a causal effect.

Known cost USD 0.006328585; 60 generations and 60 counters, no uncertain charges.
Cache reads on 59/60 requests (84,071 tokens). All 60 receipts replayed with zero calls.
All prior prompt/schema variants remain hash-identical. Validation:113 focused tests,
make fix (no formatting changes), make check (4625 passed, one skipped), offline
scope/cap/input verification, independent preflight/final audit and git diff --check.
Prior artifacts, uncommitted work and reserved/test boundaries remain preserved.
Stop for review before any more revisions, calls or expansion; no commit or push.

### Accepted support wording and other-model check — 2026-10-16

Kyle accepts the support_basis.v6 wording despite the disclosed Luna repetition
control regression and asks to check the other two models. Keep the exact revised
support prompt; run GLM and Haiku on the unchanged S12 panel, five fresh passes
per model (120 judgments). No Luna rerun, conclusion calls, new prompt variant,
reference-example arm or dataset expansion. This acceptance selects the support
wording for this development comparison; it does not qualify or select a model.

Freeze exact v6 prompt bytes against the completed Luna study, all candidate inputs
and labels, each provider's unchanged sampling/reasoning/output schema, v5 support
baseline receipts and the existing Luna-v6 result. Use a fresh external namespace.
Two provider workers may run concurrently, serially within provider. Global caps:
140 generations,70 native counters,573440 reserved output tokens,USD10 and900 wall
seconds. Each pass retains USD1 and900 seconds within the shared global window.
At most three attempts per missing response with5/15second backoff, transient
transport failures only; retain uncertain reservations and never retry a received
model output. No cache probes. Load credentials through .env without display.

Report empirical support-correct/output-valid pass^5, all per-example sequences,
negative-control regressions, pooled accuracy/macro-F1/coverage, cache and costs.
Show the existing Luna-v6 result alongside these new runs with its historical
status clear. The v5 comparisons remain descriptive, not concurrent causal tests.
Require independent preflight/final audit, focused tests,make fix,make check,
exact-input checks,zero-call replay andgit diff --check. Preserve all prior work
and reserved/test boundaries. Stop after reporting; no more tuning, commit or push.

### Other-model preparation checkpoint — artifact drive unavailable

The support_basis experiment now admits GLM, Luna and Haiku while remaining
support-only. The approved v6 prompt and runtime are unchanged. Independent
code review passed; 115 focused tests, make fix, lint and type checks passed.
Full make check: 4619 passed, one skipped, eight Task06G tests failed because
source manifests/slots under /Volumes/x10pro were unavailable. Recheck those
required tests after restoring the drive; no test expectations were weakened.

The configured artifact volume is not mounted and no external physical disk
was listed. Frozen S12 inputs, baseline receipts and reviewed runner cannot be
verified. No replacement artifact root was created and no provider calls ran.
After the drive returns, prepare/review the authorized two-model study and run it
within the above caps. Existing artifacts and uncommitted changes remain preserved.

### Artifact drive restored — 2026-10-16

Kyle reconnected x10pro and requests proceeding. The configured artifact root is
available again. All eight tests blocked by missing source artifacts now pass;
combined with the preceding 4619 passing tests and one skip, required validation
has no remaining failure. The 115 focused tests, lint, typing, make fix and diff
checks remain passed. Both relevant result pointers' completion/report/summary/
review bindings verify. Proceed with the already authorized frozen GLM/Haiku
support comparison; preserve the Luna result and all prior attempts.

### Other-model support-basis outcome — 2026-10-16

Both GLM and Haiku completed five fresh S12 passes with the accepted v6 prompt.
Each scored 12/12 support-correct pass^5 and 12/12 output-valid pass^5; all 60
judgments per model match labels (accuracy and macro-F1 1.0, coverage 100%). There
are no per-question failures or regressions from their historical v5 support runs.
Both reject S0476 verbatim repetition 5/5 and accept the three examples previously
rejected by Luna 5/5. Historical Luna v6 remains 11/12 pass^5 and 58/60 agreement;
it was not rerun. No conclusion calls, new labels or prompt changes occurred.

All 120 new generations and 60 Haiku counters completed without retries or transport
failures. Known native-usage estimate: GLM USD 0.00864470, Haiku USD 0.013104645,
total USD 0.021749345; no uncertain charges. GLM reports cache reads on 57/60 requests
(74,240 tokens), Haiku 59/60 (141,777 tokens); GLM cache-write usage remains unknown.
All 120 receipts replayed with zero calls. Frozen v5 baselines and the entire Luna
study remain unchanged; independent preflight and final receipt/input/metric/cost
review passed. The prior 115 focused tests and all required repository checks pass
once the eight drive-dependent failures are rechecked successfully after remount.
Diff validation passed. The result pointer binds report, review and completion seal.

The wording remains accepted; this small development calibration does not qualify
or select a judge. Stop for review with no additional tuning, dataset expansion,
commits or pushes. Prior work and reserved/test boundaries remain preserved.

### Authorized C comparison variant — 2026-10-16

Kyle authorizes a separately versioned C-only comparison output derived from
consolidated C v5. Preserve its decision rules and examples, including no inferred
repair and required versus incidental detail. S support_basis.v6 is unchanged.
The exact added instructions and schema are owned by
`docs/specs/task09f_conclusion_comparison_contract.md`. Native provider schema,
strict local parser and stored results must agree; literal quote fidelity is a
separate diagnostic from binary correctness. Never repair invented quotations.

Implement with bounded core/runtime agents and independent review. Validate schema,
missing/extra/internal-contradiction entries, literal quotations, prior prompt/schema
preservation and result retention; run focused tests, make fix, make check and
git diff --check. Structured schemas constrain shape, not semantic fidelity;
use the maintained provider adapters and Pydantic models, following the official
OpenAI structured-output requirements (all properties required and additional
properties forbidden): https://developers.openai.com/api/docs/guides/structured-outputs.

Run only unchanged C24, five fresh passes on each established GLM/Luna/Haiku model:
360 planned generations. Same model identities, sampling, reasoning, input payloads,
labels and 4096-token response cap as the historical consolidated five-pass study.
Each 24-request cell is capped at USD1, 98304 reserved output tokens and 900 seconds.
Aggregate caps: USD15, 360 generations, 240 native counters, 1474560 reserved output
tokens, 4500 elapsed wall seconds and at most 13500 cumulative cell seconds.
Three providers may run concurrently; five passes are serial within each provider.
Zero retries, probes or repairs. Stop new dispatch on execution failure or a cap;
retain every response, invalid output and failed attempt. Load .env privately.

Fresh external namespace: `task_09/09f_20261016_conclusion_comparison_v1`.
Freeze requests and historical C v5 receipts before dispatch. Report agreement,
macro-F1, coverage, empirical all-five pass^5, per-example changes, exact quotation
fidelity, diagnostic usefulness, cache usage and costs. Historical comparisons are
descriptive, not concurrent causal comparisons. Replay receipts offline and seal
reports after independent audit. No automatic promotion, expanded data, reserved/
test access, commits or pushes. Preserve concurrent 09F.1 work.

### C comparison variant outcome — 2026-10-16

Implemented `conclusion_comparison.v7` and output schema
`conclusion_comparison.output.v1`; exact user instructions precede the output
instructions. Native schemas, four-field checklist, strict parser and stored
comparison traces agree. All older prompt/schema hashes, including C v5 and S v6,
remain unchanged. Literal quotation and convention diagnostics are separate from
binary correctness; malformed structure remains invalid, with raw output retained.
No quotation or judgment was repaired.

All 360 fresh generations and 240 native counters completed in 547.2 seconds,
without retries, failures in transport or uncertain charges. GLM: 114/120 correct,
116/120 valid, valid-only macro-F1 0.982712, conclusion-correct pass^5 21/24 and
output-valid pass^5 22/24. Historical C v5 was 117/120 and 23/24 correct pass^5.
Luna: 120/120 correct/valid, F1 1.0 and 24/24 pass^5 (historical 119/120, 23/24).
Haiku remains 120/120 correct/valid, F1 1.0 and 24/24 pass^5. These comparisons
use historical receipts, not concurrent controls or causal evidence.

Every changed example: GLM C007-O02 and C050-A01 each regress from 5/5 to 3/5
because of invalid outputs; C017-F04 improves from 2/5 to 3/5 but still infers a
repair of an explicitly changed operation. All four invalid outputs misspell the
nested `explanation` field; one also supplies scalar quotation fields. Luna
C017-F07 improves from 4/5 to 5/5. All other examples retain their prior correctness.

Literal excerpts found in the proper original field: GLM 654/656, Luna 756/757,
Haiku 818/823. Responses without any quotation diagnostic: 114/120, 115/120,
113/120 respectively; convention flags include nonempty candidate quotes for
missing content. These counts do not substitute for binary or structural scores.
Qualitative review shows useful exposed reasoning, but also bundled requirements,
duplicate defect classifications and accurate quotations followed by wrong semantic
interpretation. Excerpt counts alone cannot establish meaning or completeness.

Known dated native-token-rate estimates: GLM USD 0.029142320, Luna USD 0.027993640,
Haiku USD 0.066409035; total USD 0.123544995. Actual cache reads: GLM 114/120,
Luna 119/120, Haiku 119/120; GLM cache-write usage remains unknown. All 360 receipts
replay with zero requests. Limits remained USD 15, 360 generations, 240 counters,
1474560 reserved output tokens, 4500 global seconds and per-cell USD 1 / 900 seconds.
Currency reserved was USD 1.572725625; no reserve was reset.

Validation: 139 focused tests, seven offline runner checks, make fix, make check
(4651 passed, one skipped), git diff --check and independent preflight/final audit.
The [result pointer](../../docs/specs/task09f_conclusion_comparison_result.json)
binds full metrics, exact prompt/schema, all comparisons and the review/seal.
Retain the variant for inspection; do not promote it across models. GLM loses
coverage, while Luna/Haiku show useful traces without measured binary regressions
on this small panel. No S runs, reserved/test access, expansion, commits or pushes.
Concurrent 09F.1 planning remains untouched.

### Authorized nested-field rename — 2026-10-16

Kyle requests changing the nested `explanation` key and testing GLM, following
its four v7 invalid outputs. Bound this to `reason` as the nested wire key in
`conclusion_comparison_reason.v8`; top-level `reason` remains unchanged. Preserve
v7 and all earlier variants. Change only that field-name instruction, wire schema
and corresponding parser/version identity; preserve all semantic instructions,
inputs, labels and model settings. Canonical internal entries may retain the
existing `explanation` field while raw receipts preserve exact v8 wire output.

Use the unchanged C24 panel, five fresh GLM passes (120 calls), against historical
v7 results. No Luna/Haiku or S reruns. Caps: USD5, 120 generations, zero native
counters, 491520 reserved output tokens, 4096 output tokens per call, 4500 global
wall seconds; each pass USD1, 24 generations, 98304 output tokens and 900 seconds.
No retries, output repair, cache probes or expanded/reserved/test access. Load
.env privately. Fresh canonical external run directory; freeze inputs, requests,
code and baseline receipts before dispatch. Independent preflight and final review,
focused tests, make fix, make check, git diff --check and zero-call replay required.
Report formatting versus semantic changes, empirical pass^5, agreement, F1,
coverage, quotation diagnostics and cost. Do not promote automatically or change
09F.1 work. No commits or pushes.

### Nested-field rename outcome — 2026-10-16

The GLM-only v8 trial completed all 120 fresh C24 judgments, five passes, with
no retries or transport failures. All 276 raw comparison entries use nested
`reason`; none uses `explanation` or `explaination`. The historical four spelling
failures did not recur. Three outputs instead use strings for quote arrays:
pass 2 C056-P05, pass 3 C017-F07 and pass 5 C056-P01. Their discernible raw booleans
remain unscored because the structure is invalid; no output was repaired.

All 117 valid judgments are label-correct: agreement/coverage 97.5%, valid-only
accuracy and macro-F1 1.0. Historical v7 had 114 correct and 116 valid. Correct
pass^5 remains 21/24; output-valid pass^5 declines from 22/24 to 21/24 because the
new invalid outputs affect three different examples. C007-O02, C050-A01 and the
changed-operation C017-F04 improve from 3/5 to 5/5; the three new invalid examples
each decline from 5/5 to 4/5. No other binary changes occurred. These historical
results do not establish a causal effect or qualify a judge.

Literal quotations found in the correct source field: 640/648; responses without
quotation flags: 103/120 (historical v7 654/656 and 114/120). Paraphrasing,
apostrophe changes, ellipses and missing-entry conventions remain visible. The
rename addresses key spelling but does not solve all formatting or quote fidelity.
No automatic promotion follows; retain the rename as a candidate for review.

Known cost estimate USD 0.02873428; 112/120 responses report cache reads totaling
182256 tokens. Cache-write usage remains unknown. 120 generations, no counters,
491520 reserved output tokens, USD 0.56973450 reserved, 318.4 elapsed seconds;
all original caps held. All 120 receipts replay without calls. Independent review
verifies all receipts, metrics and 3774 preserved prior-file hashes.

Validation: 150 focused tests, seven offline runner checks, make fix, make check
(4662 passed, one skipped), git diff --check and independent preflight/final audit.
The [result pointer](../../docs/specs/task09f_glm_comparison_reason_result.json)
binds exact prompt/schema, comparisons, reports and completion inventory. No
other-model or S calls, reserved/test access, commits, pushes or 09F.1 changes.


### Authorized full-development comparison — 2026-10-16

Kyle retains C `conclusion_comparison_reason.v8` and unchanged S
`support_basis.v6`, removes GLM from adequacy model selection, and explicitly
selects five passes on both complete published development sets for Luna and
Haiku: 246 C + 490 S examples × 5 × 2 = 7,360 generations. Historical GLM
artifacts and its separate grounding selection remain unchanged. Model choice
and 09F closeout await Kyle's review; 09F.1 is outside this work.

Use the sealed synthesis publications and all 19 development questions only.
C payloads remain exact. S uses the accepted calibration projection: ordered
qualification objects become their exact text strings, with original hashes,
attachment metadata and the named projection retained outside requests. All 490
reference-blind S examples are eligible, including 19 C051 examples; its nine
unresolved slots remain excluded. The 471-example eligibility count belongs
only to the optional reference-visibility comparison, which is not run here.
Labels remain independently reviewed proposals, not human-approved gold.

Freeze unchanged model identities, sampling/reasoning settings, 4,096-token
output limit, exact prompts/schemas, inputs, labels, code and request bodies.
Fresh external namespace: `task_09/09f_20261016_full_development_models_v1`.
Before dispatch, verify the offline conservative reservation fits these caps:
USD100 aggregate, 7,360 generations, 7,360 native counters, 30,146,560 reserved
output tokens and 14,400 elapsed wall seconds. Each component/pass/model cell
has 1,800 wall seconds and USD11 for C or USD21 for S within the aggregate cap.
At most four concurrent requests per provider, eight total. Zero retries,
repairs, probes, new labels or prompt changes. Stop new dispatch globally on
execution failure or exhausted caps; preserve and finish in-flight requests.
Invalid model outputs remain recorded observations. Load .env privately.

Require focused loader/schema/runner checks, independent preflight, make fix,
make check and git diff --check. Preserve every native attempt and replay all
completed receipts offline without calls. Report C and S separately: agreement,
valid-only macro-F1, coverage, empirical all-five correctness and output validity,
per-question/per-perturbation failures, quotation fidelity for C, caching and
native-usage cost estimates. Separate exact calibration examples, other examples
from calibration questions and remaining development questions. Historical panel
comparisons are descriptive, not concurrent causal comparisons. Do not combine
independent synthetic C/S candidates into an artificial answer-level score.
Seal reports after independent review. No reserved/test payloads, automatic model
promotion, commits or pushes; preserve concurrent documentation and 09F.1 work.


### Full-development interruption checkpoint — 2026-10-16

The reviewed frozen plan passed offline preparation: 1,472 unique requests,
7,360 planned observations, USD46.03342 conservative reservation bound. Required
validation passed: 161 focused tests, make fix, make check (4,673 passed, one
skipped), five scheduler fault checks, report fixture checks, independent preflight
and git diff --check. No prompt or label changed.

Execution stopped globally after 634.792 seconds on a Haiku generation transport
error without an HTTP response (pass 2 C, C001-P01). All in-flight calls drained;
no retry ran. There are 1,195 generation/counter reservations and 1,194 received
judgments, all structurally valid and replayed offline. First-pass complete cells:
Luna C 246/246 correct; Haiku C 244/246 and S 473/490. Luna S is partial at 197/209;
Haiku pass 2 C has three received correct judgments and one response-less attempt.
These are proposed-label development results, not a completed five-pass comparison.

Known received-response cost estimate USD0.373220510; uncertain failed-call
reservation USD0.004470125. Cumulative currency reserved USD4.901273225 and output
reserved 4,894,720 tokens. Preserve all receipts and review the checkpoint before
continuing. A proposed continuation would retain all 1,194 received observations,
make 6,166 new calls, and require an explicit one-attempt cap amendment to 7,361
generations/counters and 30,150,656 reserved output tokens. USD100 remains the
aggregate spending cap; elapsed execution allowance remains cumulative. No such
continuation has been dispatched or silently authorized by this checkpoint.


### Authorized Inspect-native execution integration — 2026-10-16

Kyle requests attempting Inspect's maintained provider infrastructure for OpenAI,
Anthropic and Fireworks, preferring less custom code and explicitly accepting
loss of incompatible features with disclosure. This supersedes the custom
transport choice for the new adequacy entry point. The interrupted comparison
and its 1,194 received judgments remain preserved and are not resumed here.
No change to 09F.1, historical grounding semantics, prompts, labels or datasets.

Read the full Inspect Options reference and installed 0.3.278 provider code.
Use native get_model/Task/generate/scorer/eval interfaces and the standard Inspect
CLI for retries, concurrency, epochs, logs and error recovery. Keep only narrow
C/S projection, existing strict parsing, quotation diagnostics and provider config
mapping. No new custom retry loop, transport, scheduler or reservation framework.
Add the maintained OpenAI/Anthropic SDKs required by Inspect; Fireworks uses its
native OpenAI-compatible adapter. Retain legacy code for historical receipt replay.

Explicit settings: two model-request retries, 120-second total request timeout,
45-second attempt timeout, four static provider connections and four samples;
no whole-sample retries, model fallbacks or model-output repair. Preserve fixed
model IDs, C v8/S v6 instructions and provider reasoning/sampling/schema settings
where supported. Inspect response caching stays disabled for independent trials;
provider prompt caching remains distinct. Log every model API call and validation
result. Use Inspect per-sample cost/time controls with configured price data.

Disclose changed guarantees: no custom pre-dispatch cumulative USD reservation
ledger or exact full-wire token-count/hash gate in this integration. Native usage
and Inspect cost reporting do not prove charges for response-less attempts, and
per-sample limits are not a hard global invoice ceiling. Do not claim request
byte identity until native provider request fixtures establish it; record actual
wire differences. Prefer those transparent limits over rebuilding the executor.

Validate with mocked native SDK requests for all providers, real Inspect retry
classification/exhaustion, malformed outputs without retry, schemas, settings,
logs and quotation diagnostics. Run focused tests, make fix, make check,
git diff --check and bounded independent review. Then perform twelve invented-input
smoke generations (one C and one S, each repeated, per provider) in a fresh canonical external
namespace. OpenAI/Anthropic SDK retries are disabled through native model arguments;
Inspect permits three attempts per logical call. Fireworks' native provider does
not expose that SDK setting, so its SDK retry layer remains: at most nine HTTP
generation attempts per logical call. Across twelve calls the upper bound is 60
generation attempts and 245,760 output tokens at 4,096 each. Use 900 seconds
of total active execution and a USD1 planned upper allowance using dated rates.
Verify provider prompt-cache reads on repeat requests while Inspect's response
cache stays disabled. No dataset calibration or accuracy claim follows these checks.
Credentials load privately through .env; no commit or push.

Research: https://inspect.aisi.org.uk/options.html (all sections),
https://inspect.aisi.org.uk/extensions-hooks.html,
https://inspect.aisi.org.uk/models-concurrency.html,
https://inspect.aisi.org.uk/eval-logs.html. The installed provider code is the
compatibility authority where broad documentation omits model-specific support.

### Inspect-native integration outcome — 2026-10-16

The [native integration](../../docs/specs/task09f_inspect_native.md) is implemented
and verified: 21 focused tests and full make fix/check passed (4,694 tests, one
skip). Twelve invented-input live generations were valid; all six repeats showed
provider prompt-cache reads with unique request IDs, and all six C outputs passed
quotation fidelity. No retries or failures were reported. Estimated cost was
USD0.002562035. The [result pointer](../../docs/specs/task09f_inspect_native_result.json)
retains logs, settings, usage and independent review.

Native schema serialization and OpenAI provider-default cache retention replace
legacy wire details. Inspect owns execution; custom cumulative reservations and
exact pre-request token gates are dropped with disclosure. Historical receipts
and the interrupted comparison remain unchanged and paused. No model selection,
prompt changes, dataset evaluation, 09F.1 changes, commits or pushes.

### Authorized native calibration recheck — 2026-10-16

Kyle requests rerunning the 24 conclusion and 12 support calibration examples to
check score stability after the Inspect migration. Use Luna and Haiku, five
fresh epochs each: 360 logical generations. GLM remains excluded. Retain the
sealed v3 panel, labels, C v8/S v6 and native provider settings; no tuning or
full-development continuation. Compare with historical C v7 (nested key rename
only) and S v6 results, explicitly not a concurrent causal comparison.

Caps before dispatch: 360 logical generations, at most 1,080 HTTP generation
attempts (two Inspect retries, SDK retries disabled), 4,096 output tokens each
and 4,423,680 maximum attempted output tokens; 1,800-second external wall timeout.
USD20 planned allowance and Inspect USD0.02 per-sample soft cost limit. These
native limits are not a hard invoice ceiling and unknown failed-call charges
remain disclosed. Four sample/provider connections, one task at a time, no
whole-sample retry, fallback, response caching or output repair. Preserve native
logs and all errors in a fresh external directory. Verify panel bindings and
focused native tests before dispatch; independently review metrics and caching
before reporting. No reserved/test access, prompt edits, commits or pushes.

### Native calibration recheck outcome — 2026-10-16

The [recheck result](../../docs/specs/task09f_inspect_calibration_result.json)
records 360/360 valid outputs over five passes, no reported retries or execution
failures, and USD0.108446115 estimated cost. All four pass^5 scores match their
historical baselines: Luna C 24/24, S 11/12; Haiku C 24/24, S 12/12. Luna S is 57/60
correct versus 58/60 previously, entirely on the same S0476 repetition control.
All other observations are correct. C quotation diagnostics remain separate:
Luna 111/120 pass versus 115/120 historically; Haiku 115/120 versus 113/120.

Provider prompt caching was observed on 352/360 requests; response caching stayed
off. Historical comparisons are descriptive: C v7→v8 changes the nested field
name, and native schema/cache serialization differs. No statistical equivalence
or causal transport claim is made. Production code is unchanged; 21 focused tests
and git diff --check passed, with the earlier full validation still applicable.
Keep native Inspect execution. The full-development comparison remains paused;
no prompt tuning, model selection, reserved/test access, commit or push.

### Authorized fresh full-development three-pass run — 2026-10-16

Kyle authorizes a new three-pass comparison of Luna and Haiku on all published
246 C and 490 S examples across the 19 development questions. All 4,416 judgments
must be newly generated through native Inspect; no previous response, receipt or
result is reused. Preserve historical runs, including the interrupted direct-HTTP
comparison. C v8/S v6, model IDs, sampling/reasoning settings, projections and
proposed labels remain unchanged. GLM and reserved/test data remain excluded.

Before dispatch bind dataset seals, every payload/label, code/settings and the
following limits in a fresh external manifest. Caps: 4,416 logical calls, at most
13,248 HTTP attempts (two Inspect retries, SDK retries disabled), 4,096 output
tokens per attempt, 54,263,808 maximum attempted output tokens, and a 5,400-second
external wall timeout. USD100 planned allowance with Inspect USD0.02 per-sample
soft limit; neither is a hard global invoice guarantee. Two native tasks may run
concurrently, with four samples per task and four connections per provider.
No whole-sample retries, model fallback, output repair or response caching.
Provider prefix caching remains enabled and measured. No custom executor or
budget ledger is added. Credentials load privately from .env.

Verify seals and focused native/development tests, then obtain independent
preflight review. Preserve all native logs and failures. Report C/S separately:
accuracy/agreement, valid-only macro-F1, coverage, empirical all-three correctness
and output validity, per-question/per-perturbation failures, quotation fidelity,
cache use and known/uncertain cost. Distinguish exact calibration overlap, other
examples from calibration questions and remaining development questions. Labels
remain reviewed agent proposals; do not combine separate C/S synthetic answers
into an artificial aggregate answer score. Independently verify final metrics,
seal the result and return for model-selection review. No prompt tuning, automatic
promotion, 09F.1 changes, commits or pushes.

### Fresh full-development three-pass outcome — 2026-10-16

The [fresh native result](../../docs/specs/task09f_inspect_full_dev3_result.json)
contains all 4,416 newly generated judgments; no old response was reused.
All outputs are valid, all request IDs are unique, and none overlap the prior
native calibration. No execution failure or retry was reported. Execution took
48 minutes 7 seconds, with USD1.190560110 estimated cost and prompt-cache reads
on 4,408 requests. Independent review reparsed every output and verified metrics,
inputs, settings, quotation flags, source bindings and costs.

| Model | C agreement | C pass^3 | S agreement | S pass^3 |
| --- | --- | --- | --- | --- |
| Luna | 735/738 | 244/246 | 1,381/1,470 | 444/490 |
| Haiku | 733/738 | 243/246 | 1,427/1,470 | 464/490 |

C failures involve one shared wrong-location example and three compressed-answer
examples. S has 15 consistently failed examples for Luna and five for Haiku;
per-question, perturbation and exposure breakdowns are preserved in the report.
Quote-check passing C responses are 637/738 Luna and 599/738 Haiku, independently
of binary correctness. Labels remain reviewed proposals, not human gold.

Recommendation for review: Haiku is stronger on S; C is near ceiling for both,
with a small Luna edge in this run. No automatic model selection or 09F closeout.
Earlier interrupted and calibration studies remain preserved; do not pool them
into this fresh comparison. Focused tests passed 28/28 and git diff --check passed;
production code is unchanged from the full validation already recorded above.
No prompt tuning, reserved/test access, 09F.1 changes, commits or pushes.

### Accepted selection and closeout — 2026-10-16

Kyle selects Luna for conclusion and Haiku for support. Lock
`configs/adequacy_selected_v1.json`: C uses `gpt-6-luna` with conclusion v8;
S uses `claude-haiku-5-5` with support v6. Native Inspect's default task routing
now selects the correct model by component and rejects drift in the selected
model, prompt version, prompt bytes or schema. Explicit condition overrides remain
available for separately scoped experiments and historical reproduction.

09F is complete with its disclosed semantic, quotation and proposed-label limits.
The [final result](../../docs/specs/task09f_final_result.json) provides the handoff.
No additional model calls are needed for closeout. Preserve all prior receipts;
the chosen pair does not make historical evaluations use different models.
09F.1 owns no-answer and point-grounding work; 09G owns the refreshed joint
challenge/freeze step; Task 12 owns routing, joins and composed-answer reporting.
Those tasks are not unfinished 09F work. No commit or push.

Closeout validation: 24 focused tests passed; `make fix` and `make check`
passed (4,843 tests passed, one skipped); `git diff --check` passed. Independent
review found no blockers in selection, drift checks or task boundaries. The
fresh selection receipt is linked from the final result; no provider calls.
