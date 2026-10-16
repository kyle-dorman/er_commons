# Task 09E — Implement and iterate the grounding judge

See the [grounding experiment record](../../docs/grounding_experiment_record.md)
for a consolidated account of local and cloud techniques, negative results and
lessons across 09E/09E.1. Detailed historical evidence remains below.

Status: **complete** — closed by the user on October 13, 2026.
Parent: [Task 09](09_build_evaluation_and_qualify_judges.md).

The grounding judge implementation, development experiments and independent
review are complete. [09E.1](09e1_compare_cloud_and_decision_judges.md) completes
the cloud comparison and GLM selection; [09E.2](09e2_cleanup_grounding_judges.md)
completes cleanup of both implementations. Use the
[maintainer guide](../../docs/grounding_judge_guide.md) for current interfaces.

Accepted limitations remain: synthetic labels are development proposals, the
selected results include disclosed targeted repairs, and some invalid outputs
and claim/review disagreements remain. Final challenge and configuration freeze
belong to 09G; they do not keep this implementation task open. The next task is
the separate 09F adequacy judge, whose provisional contract must be refreshed.

## Historical plan and experiment record

The sections below preserve the original local-model plan and its successive
outcomes. Historical review stops and model choices have been superseded by the
accepted cloud comparison and closeout above. No further Qwen expansion is pending.
The October 13 user instruction authorizes committing this completed work and
merging it into local main; earlier no-commit boundaries describe their runs.

## Abstract

Implement an independently runnable grounded-correctness judge over the exact
question, structured answer and actual cited evidence. Develop it on fixed small
panels with visible prompt revisions and failure analysis. Citation-ID matches
cannot establish sound reasoning, and synthetic expected scores are not human gold.

## Goal

Produce a versioned grounding prompt, strict result schema and Inspect scorer,
with reproducible small-panel results and an explicit recommendation at each
review checkpoint. Keep grounding separate from adequacy. Passing this task does
not certify judge accuracy or authorize a full-development challenge.

## Inputs

- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md)
  and the [sprint evaluation boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary).
- Accepted 09A (`eee4edc`), 09B (`c2dba5f`), 09C including quality pass
  (`756f6d3`), and closed 09D (`e9eeaa1`); read their outcomes and result pointers.
- [09B result](../../docs/specs/task09b_final_result.json): Inspect/native Ollama,
  installed Qwen3.5 0.8B F16 and Qwen3.5 9B F16 with pinned identities. The small
  model returned score 1 on all eight earlier probes; neither model is qualified
  as an accurate judge. Do not reuse 09B prototype semantic rubrics as the judge.
- [09C result](../../docs/specs/task09c_final_result.json): separate strict
  grounding packets and full-request preflight. Exact runtime token counting is
  still required before dispatch; existing packets say `context_unverified`.
- [09D result](../../docs/specs/task09d_final_result.json): Inspect execution,
  saved-answer/sample identity, explicit eligibility and separate automatic metrics.
  Its automatic scores must not enter grounding requests or become semantic labels.
- [Fixed question subsets](../../docs/specs/task09e_development_subsets_v1.json),
  sealed 09A development reservation and approved controls.
- [Architecture](../../docs/architecture.md), [artifact contract](../../docs/data_artifacts.md)
  and [task shape](../README.md).

## Outputs

- Versioned grounding prompt, result schema, thin Inspect scorer and offline tests.
- Fixed development-only sample manifest with exact control/variant IDs, source,
  packet and expectation bindings, selection reasons and coverage gaps.
- Inspect logs and separate raw native requests/responses, model/configuration
  identities, preflight receipts, timing, failures and bounded recovery evidence.
- Per-stage reflection reports, prompt change log and an explicit continuation
  decision. Broad challenge/freeze remains in 09G; adequacy remains in 09F.

## Research / learning checkpoint

The planning refresh checked primary [Inspect model grading](https://inspect.aisi.org.uk/model-graded.html),
[Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
and [evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).
Inspect's default grader/template can include targets and metadata; use a dedicated
reference-blind request path. Structured JSON makes results parseable, not correct.
Small fixed panels support fast diagnosis, while repeatedly tuning on them limits
what their apparent agreement can establish. Verify APIs against installed Inspect
0.3.278 before implementing; do not assume current web examples match that version.

## Fixed development subsets

The versioned subset file fixes question membership now; it contains IDs and
metadata only. These are nested tuning panels, not new benchmark splits or
unseen validation sets. The original 19 development / 30 test allocation and
423 development variants / 118 reserved final checks / five exclusions remain
unchanged. Never inspect reserved answer payloads or test questions/references.

| Panel | Question IDs | Selection rationale |
| --- | --- | --- |
| `dev3` | C041, C037, C014 | Previously exercised short/typical/large control shapes; habitat controls, wetland mitigation and table-bearing evidence |
| `dev6` | C041, C037, C014, C001, C019, C056 | Adds health risk, appendix-only groundwater/review and drainage/flooding; varied multi-source and optional-context structure |

Length descriptions apply to earlier control packets, not every variant. This
purposive selection is not statistically representative. The added cases' metadata
come from the approved 08G split proposal; all six were verified against sealed
09A development membership without loading answer or expectation payloads.

For the original 09A panel (preserved historical contract), materialize **four
distinct saved answers per question**. The authorized 09A.3 follow-up below uses all
eligible answers instead:

1. One unchanged approved control.
2. One eligible development variant with proposed grounding 0, preferably a
   central contradiction or unsupported conclusion/necessary premise.
3. One eligible development variant with proposed grounding 1, preferably a
   material unsupported secondary assertion or missing qualification.
4. One eligible edge variant to broaden panel coverage: citation mismatch,
   supported-but-incomplete answer, valid alternate evidence, or abstention.
   Distribute these across the panel; do not rotate samples during prompt tuning.

This gives **12 answer samples on dev3 and 24 on dev6**, not three/six judge calls
and not all variants of those questions. Select from the development allowlist
before decoding payloads, using existing metadata-first routing. Compare available
category/expectation metadata only for these six cases; inspect only selected
eligible answer rows. Keep proposed expectations in restricted analysis metadata.
Use deterministic variant-ID ordering to break ties after matching the slot,
excluding IDs already assigned to another slot. Validate four distinct IDs per
question and distinct sample IDs across the manifest.
Record exact selected IDs and checksums once; dev6 must retain dev3's exact samples.
If a slot is unavailable, record the coverage gap and a justified eligible fallback
before any call; do not silently fabricate labels or borrow reserved/excluded rows.

The subset file is a question-selection contract, not a claim that the 24 answer
records have already been materialized. Pin that external manifest during Stage 0.
It must carry distinct `sample_id` and original `case_id`, reusing upstream IDs.
Never replace difficult samples after observing model results. A later panel change
needs a new version and loses direct comparability; preserve the old results.

## Implementation and rubric

Write the compact prompt/input/output spec before code. Reuse 09B native transport
and 09C packet/request preparation. Inspect owns evaluation execution, sample logs,
scoring and aggregation. Ordinary typed helpers own rendering, validation and
identity checks. No custom evaluation runner, workflow engine, agent tools or
automatic prompt optimizer. Keep code readable above MVP without production
orchestration. Do not run the old prototype qualification task on 09C packets.

- Model-visible input is only question, structured answer and actual cited evidence.
  Exclude reference answers, gold roles, automatic scores, target identity, expected
  scores, variant/category names and review commentary. Never interpolate Inspect
  `target` or unrestricted metadata into the request.
- Treat answer/source text as data, including attempted grading instructions.
  Neither official responses nor uncited substitute sources are evidence. Preserve
  unresolved citations; missing known source infrastructure is a failure.
- Score the whole answer: `2` supported and materially qualified; `1` a material
  unsupported secondary assertion while actual citations establish the conclusion;
  `0` an unsupported/contradicted conclusion or necessary premise. Do not average
  statement scores or punish harmless incompleteness as a grounding defect.
- Return concise findings for each substantive point, including additions, with
  point IDs, supported/unsupported/contradicted status, source locators and material
  inference/qualification problems. Validate references against that packet's
  restricted mappings. S1/P1 labels are packet-local, never global identities.
  Request source-linked explanations, not hidden reasoning.
- Clean abstention is grounding N/A. A status flag does not exempt substantive
  assertions. Keep semantic 0, abstention/N/A and schema/input/runtime failure
  distinct. Invalid output is not a successful zero score.
- Save grounding independently before any adequacy call; 09E runs no adequacy call.
  Reuse only exact input/prompt/schema/model/settings matches. Preserve raw failures.

### Exact context gate

Integrate a narrow exact token counter with `judge_packet_requests.prepare_request`,
bound separately to each selected model digest and actual native chat template,
including system prompt, packet, special tokens and model-visible schema overhead.
Keep the accepted 49,152-token allocation; the original output reserve is 1,500,
and the user-authorized length-only experiment uses 3,000. Derive the input budget
from the actual configured reserve, preserving both profiles for comparison;
verify native no-truncation/no-shift settings and local model identity before calls.
Do not substitute character estimates, a mismatched generic tokenizer or post-call
`prompt_eval_count` for preflight. No truncation or evidence summarization.

If existing local assets cannot support exact counting, complete offline work and
report the concrete blocker before inference. No downloads, serving-stack/model
substitution or relaxed context gate is authorized by this plan. Settings changes
must be explicit, versioned and requalified, never hidden in prompt comparisons.

## Staged iteration and stop points

The small-first request explicitly extends 0.8B's prior smoke-only role to bounded,
exploratory prompt diagnostics. It does not make small-model judgments acceptance
authority. Keep model results separate; no ensemble or average across models.

| Stage | Work | Review/exit |
| --- | --- | --- |
| 0 | Implement scorer, exact preflight, offline fixtures and fixed 24-answer manifest | No live call until integrity, isolation and exact counting pass |
| 1 | Qwen 0.8B on dev3; diagnose and revise prompt in bounded cycles | Reflect before dev6; collapsed scores may motivate bounded revisions; context/integrity failures block dispatch |
| 2 | Qwen 0.8B on dev6 using the chosen prompt | **Stop for user review** of metrics, disagreements and whether to revise or move to 9B |
| 3 | After that review, Qwen 9B on dev3, first using the identical small-model finalist | Preserve direct comparison before any 9B-specific revision; reflect before dev6 |
| 4 | Qwen 9B on dev6 using its chosen prompt | **Stop for user review** before any full-19 run on either model |

Within the current authorized model stage, routine prompt edits and repeat checks
may proceed without asking after every edit. The user subsequently removed the
initial two-revision planning cap and requested one-change-at-a-time experiments.
Each explicit experiment must record its hypothesis, changed setting or prompt,
fixed panel, actual calls and comparison before choosing the next change. This is
not authorization for broad runs, model transitions or automatic optimization.
The current user-authorized follow-up consumes the [combined 09A.3 development
publication](../../docs/specs/task09e_09a3_small_v1.md). The user explicitly selected
all comparison-eligible answers for the unchanged Dev3/Dev6 question memberships:
69 Dev3 answers and 136 Dev6 answers. Freeze a new provenance-bound panel, retain
all previous 09E evidence, and run the current small-model staged pipeline with
abstention gating. Keep prompts, schema and model settings fixed. Reflect on Dev3,
then add only the other three questions while retaining exact Dev3 results. Stop
after small-model Dev6. New stage expectations remain restricted diagnostics, not
judge input or calibrated labels. No full-19 or larger-model run is authorized.
Allow at most one retry per transient operational failure; never retry semantic
disagreement or malformed output until it returns a preferred score. Stop at the agreed experiment checkpoint and present the next proposed experiment. Score
collapse triggers diagnosis, not an automatic ban on prompt revisions: revise only with a concrete generalizable hypothesis, and stop early
for user reflection if collapse persists or no useful revision is justified.

Keep every prompt version, concise hypothesis/change description, sample manifest,
raw call, parsed result and rejection reason. Prefer general rubric clarification
and output-schema improvements; do not encode case-specific answers/IDs or tune
labels to match the judge. If six-question results motivate a revision, recheck
all three-question samples and the same six-question panel under the new version.
A model transition must not erase the prior model's failures.

No request to start 09E implicitly authorizes the full 19, all 423 variants, reserved
118 checks, 09F/09G or test evaluation. At the final checkpoint, distinguish a
possible 19-question/four-answer panel (76 samples/model) from the full development
challenge (423 variants + 19 controls = 442 samples/model). Estimate actual calls,
time and any context failures for the proposed expansion; obtain explicit user
authorization and reconcile the 09G contract before broad challenge work.

## Reflection report and accuracy limits

After every evaluated prompt/model/panel combination, report:

- Expected/attempted/new/reused/scored/N/A/failed counts; schema and source-locator
  validity; context-blocked and retry counts. Denominators must remain explicit.
- Grounding mean and 0/1/2 distribution; exact agreement and confusion matrix
  against sealed **synthetic score proposals**, plus ordinal absolute error.
  Report N/A agreement separately and retain failures outside the numeric matrix.
- False-supported decisions (judge 2 versus proposed 0/1) and false rejections of
  unchanged controls, with counts/denominators; per-question and answer-category
  breakdowns. Report both answer-weighted agreement and question-balanced means
  when missing/failed observations make populations unequal.
- A short source-linked analysis of disagreements: central vs secondary errors,
  missed conditions, mistaken citations, unjustified abstention, and rationale/
  score inconsistency. An expectation may be questionable; flag it without silently
  editing frozen labels. Controls also merit inspection rather than blind trust.
- Latency and token measurements, failure costs, prompt-version deltas on identical
  samples, and what improved/regressed. A schema-valid all-1/all-2 judge is not a
  successful accuracy result. Do not tune a numerical graduation threshold on six
  questions or describe agreement as calibrated accuracy/human agreement.

Finish each report with a recommendation: keep, revise with a concrete hypothesis,
stop for an infrastructure/model limitation, or request the next model/scale stage.
These remain uncalibrated automated judgments on tuning data. 09D citation metrics
may be inspected separately for diagnosis; they are neither semantic truth nor
allowed grader inputs. Missing retrieval receipts remain unavailable.

## Validation and review

Offline tests must prove request isolation and unchanged grounding input under
reference changes; exact context boundary/model-counter mismatch; central versus
secondary rubric fixtures; missing conditions, wrong/alternate citations, clean
and substantive abstention, and injected grading instructions. Validate diagnostic
IDs, schema errors, timeouts, bounded retries and exact-identity resume. Mocked
outputs test plumbing and gates, not model accuracy. Require an actual offline
Inspect integration test with zero inference before live qualification.

Use bounded independent reviews of information isolation/rubric fidelity and
readable scorer/denominator/recovery behavior. For implementation run focused tests,
`make fix`, `make check` and `git diff --check`. Latest baseline from 09D is **3,638
passed, one skipped and three historical Task 06G failures**; distinguish regressions.
This docs-only refresh uses manifest/membership checks and `git diff --check`.

## Acceptance criteria

- Independent Inspect grounding scorer with pinned inputs, model/prompt/schema,
  exact context preflight and source-linked outputs; no reference leakage.
- Fixed nested question/sample manifests and visible prompt iteration history.
- Explicit numeric/N/A/failure denominators, checkpoint reports and known weaknesses.
- User review before model-stage progression and full-19 expansion as specified.
- No claim of general accuracy; current stage may close with a documented model
  limitation rather than forcing good-looking metrics. Carry findings to 09F/09G.

## Non-goals

Adequacy implementation, BM25/target generation, reference changes, new human
labeling, model downloads, other model comparisons, full challenge/final freeze,
reserved/test use, commits or pushes during this planning refresh.

## Planning provenance

Plan refreshed after accepted 09A–09D outcomes. Fixed nested question memberships
were verified from sealed metadata, and the staged small-first workflow and review
stops reflect the user's request. Answer-level manifests, prompt/scorer code,
exact token-counter integration and all model runs remain unstarted. Planning
review checked information boundaries, practical sample/call limits and reporting
claims. No answer/expectation payloads were opened. One metadata helper verified and
parsed the complete approved split proposal, which contains both splits, then
extracted only development membership/topic/evidence metadata. No question values
were displayed or used, but test-question fields were present in memory. This is
not a claim that test-containing files were never decoded. Future preparation must
use development-only inputs or field-selective metadata streaming, rather than
decoding mixed-split question containers.


## Historical outcome — initial infrastructure checkpoint

Stage 0's offline grounding implementation and fixed panel are prepared. Live
Stages 1–2 did not start: **no verified exact full-native-request token counter is
available for the pinned Ollama Qwen3.5 renderer**. The [result pointer](../../docs/specs/task09e_final_result.json)
binds the external panel, audit, Inspect records, validation and checkpoint report.
This is an early blocker checkpoint, not completion of live judge qualification.

### Implementation and fixed inputs

The [prompt/result specification](../../docs/specs/task09e_grounding_v1.md) documents
the reference-blind v1 rubric. `grounding_judge` validates strict output, all nonempty
point IDs, actual citation ownership, exact prose/table excerpts and score/finding
consistency. `grounding_inspect` runs saved answers through Inspect, retaining raw
attempts, explicit failure/N/A/numeric records and diagnostic aggregates. Native
transport and packet preparation reuse 09B/09C. Automatic metrics never enter
requests. Mocked judgments test these boundaries, not semantic accuracy.

`grounding_panel` froze **24 distinct saved answers** across C041/C037/C014/C001/
C019/C056; Dev3 retains the exact first 12 records. Each case has its upstream
unchanged control, proposed G0, proposed G1 and a coverage edge. Exact answer,
packet, source and restricted expectation hashes are recorded externally. Selection
uses sealed development membership before decoding selected answers; no mixed-split
question container is decoded. The 19/30 split and 423/118/5 partitions are unchanged.

C001's G1 falls back to C02 citation attachment swaps, with the correct tables
still cited elsewhere in the whole answer. This expectation may be debatable;
source-linked review records that uncertainty without changing the proposal.
C019's G0 falls back to C03, removing the evidence required for its landfill-specific
conclusion. Other edge samples cover wrong-real citations, clean abstention,
supported incompleteness, alternate evidence, invalid citation and alternate argument.

Maintained offline entrypoints are `make prepare-grounding-panel` and
`make preflight-grounding-panel`; the latter deliberately supplies no counter and
cannot dispatch. The Python Inspect task accepts an explicitly qualified exact
counter when a future authorized repair establishes native parity.

### Exact-token audit and prompt cycles

The original small-Qwen manifest and model/config/projector/license/parameter blobs
remain on disk and their SHA-256 checks pass. GGUF tokenizer data exists, but there
is no verified callable path reproducing the native `qwen3.5` renderer, special
framing, disabled thinking and structured-output behavior for a complete request.
The reported template is only `{{ .Prompt }}`. Installed generic tokenizer packages
and a bundled separate server do not establish native parity; no substitution,
download or inference probe was attempted.

Separately, the native service is stopped and the saved `er09b-qwen-small-48k:v2`
alias registration is absent. Restarting the service alone would not resolve the
counter blocker. A future repair must restore/verify the exact model alias and
qualify the complete counter before any call. No estimate or post-call token count
was used as preflight.

Prompt v1 is saved; **zero evaluated prompt cycles, zero prompt revisions and zero
model calls**. Dev3/Dev6 agreement, confusion matrices, semantic disagreements and
latency estimates are unavailable. Offline preflight records are not small-model
Dev6 evaluation. No inference-based reflection or expansion is justified.

### Learning, limitations and review checkpoint

[Inspect custom scoring](https://inspect.aisi.org.uk/scorers.html) supplies execution
and aggregation without exposing its target field to this judge; installed version
0.3.278 is exercised by real offline logs. [Ollama's chat response](https://docs.ollama.com/api/chat)
reports token usage after generation, which cannot replace exact pre-dispatch
counting. Structured findings permit mechanical consistency checks but cannot
prove the model's semantic support or clean-abstention classification. The 1,500-token
output budget and model reasoning quality remain untested with this prompt.

Resume is limited to exact, verified completed successes; incomplete and failed
attempts stay preserved rather than being silently re-executed. This is a bounded
single-writer interface, not production orchestration. Synthetic agreement remains
diagnostic, never calibrated accuracy. No 9B, full-19, broad challenge, reserved/test
evaluation, target generation, 09F–09G, Task 10, commits or pushes occurred.

**Review checkpoint:** inspect the offline artifacts and decide the bounded local
counter/alias repair scope. Any resumption begins with exact preflight, then the
already-frozen small-model Dev3 panel and reflection before Dev6. The initial prompt
plus at most two justified revisions remains the limit. The next-model and broad
scale gates remain closed.

### Final offline validation

- Focused integration/regression suite: **183 passed**; 58 new grounding tests.
- `make fix`: passed. Formatting, lint and strict types passed.
- `make check`: **3,696 passed, one skipped, three historical Task 06G failures**.
  These are the same two v38 immutability checks and source-free template check;
  relevant historical files remain unchanged from `e9eeaa1`. No regressions.
- `git diff --check`: passed. Independent isolation/rubric/recovery review accepted
  the offline implementation with the exact-counter execution blocker.
- Final real-panel Inspect log: 24 expected, **0 attempted/new/reused/scored/N/A**,
  **24 context-blocked**, zero retries and no token measurements. Null agreement,
  means and semantic comparisons are preserved; blocked samples are not zero scores.
- Final invented-fixture Inspect log: one supported result and one intentionally
  invalid point locator rejected, with no inference. Additional tests cover table
  excerpts, injected instructions, abstention, counter mismatch/overflow, transient
  timeout retries, malformed responses and exact checksum-bound successful reuse.

The original refreshed planning diff is retained under `setup/initial_planning.patch`.
Existing planning choices and subset membership remain intact; routing now points
to this early infrastructure checkpoint. The external completion inventory binds
both earlier and final offline logs, and the final result records source code hashes.


## Historical counter-integration checkpoint

The user subsequently authorized investigation, an isolated render/tokenize probe,
then **one tiny invented generation and integration of the verified counter**.
That narrowed follow-up ends here, before any benchmark judge evaluation.
The earlier blocked receipts remain immutable historical evidence.

The invented generation ran through Inspect using the existing native transport:
**31 preflight tokens = 31 reported prompt tokens**, with 11 output tokens and a
32-token output cap. This checks tokenizer parity, not the grounding rubric. The
judge still reserves 1,500 output tokens. No benchmark answers entered this probe.

`ollama_token_counter` uses this installed Ollama build's debug-render response and
its own verified child runner's tokenizer, with special-token parsing enabled.
It pins binary, runner and model hashes; checks parent/child commands, listening
socket ownership, model digest/context and native identity before/after counting;
and saves raw requests, responses and count/failure receipts. Unsupported builds,
request fields or changed identities fail closed. `grounding_run` connects this
counter to existing 09C request preparation and Inspect. It starts no services,
downloads no assets and supports only explicit Dev3/Dev6 panel choices.

The runtime hook is private, so this adapter deliberately supports only measured
Ollama 0.40.2 and Qwen3.5 0.8B F16 assets. A runtime/model change needs a new
qualification. Source inspection of [Ollama rendering](https://github.com/ollama/ollama/blob/v0.40.2/server/routes.go)
and [completion tokenization](https://github.com/ollama/ollama/blob/v0.40.2/llm/llama_server.go)
informed this boundary. Counting the actual rendered prompt avoids reproducing the
runtime's chat template in project code; schema grammar is separate from prompt
text in this build. This pinned version includes cached prompt tokens in its reported input count;
post-call mismatch remains a failure to investigate, never an excuse to relax preflight.

**Checkpoint:** review the counter evidence before resuming frozen small-model Dev3.
No grounding prompt cycles or revisions have run. Semantic reliability, actual-panel
context fit and the 1,500-token result budget remain untested. The same fixed panels,
two-revision cap, reflection before Dev6 and model/scale review gates remain intact.
All broader evaluations, later tasks, commits and pushes remain unstarted.


The production adapter was also exercised live without generation: the invented
plain prompt counted 31 tokens, and the actual grounding prompt/schema over an
invented fixture counted 492 tokens through `prepare_request`, leaving the required
1,500-token reserve. Independent review verified raw request/render/tokenizer and
before/after identity bindings. Temporary services were stopped. All 16 original
artifact bindings remain unchanged. Current evidence is linked from the result pointer.

Counter integration validation: **122 focused tests passed; 3,743 full-suite tests
passed, one skipped and the same three historical Task 06G failures**. `make fix`,
format/lint/types and `git diff --check` passed. No new regression was identified.


## Historical outcome — initial small-model limitation

After user approval, Inspect executed the same frozen Dev3 panel under v1 and v2,
12 samples each. Exact token preflight and post-call input counts matched for all
24 executions; context/identity gates were never relaxed. The [result pointer](../../docs/specs/task09e_final_result.json)
binds both Inspect logs, raw outputs, prompt/schema versions, reflections and source
review under `09e_20261010_small_v1`. Dev6 was not started.

| Dev3 version | New / reused / retries | Valid numeric / N/A | Validation failures | Output limit | Complete point coverage (diagnostic) |
| --- | --- | --- | --- | --- | --- |
| v1 | 12 / 0 / 0 | 0 / 0 | 11 | 1 | 2/12 |
| v2 | 12 / 0 / 0 | 0 / 0 | 9 | 3 | 8/12 |

Each version expected and attempted 12, failed 12, and context-blocked 0. All three
questions and all answer categories have zero scored observations. Numeric means,
synthetic agreement, ordinal error, question-balanced metrics and N/A agreement are
undefined. Confusion cells have zero eligible observations; false-supported and
control-rejection denominators are zero. Raw invalid scores are not promoted into
those metrics. Each run contains three attempted controls, all invalid.

V1's first validation failures were nine incomplete/duplicate point sets and two
nonliteral excerpts. V2 reduced point-set failures to one, but still had two
nonliteral excerpts, five invalid substantive materiality assignments and one
score/finding contradiction. These are first rejection reasons, not an exhaustive
count of every defect. V2's output-limit failures increased from one to three.

### Revision and source-linked reflection

Revision 1 (v2) explicitly enumerates all answer point fields, asks for short exact
source spans and concise explanations, and presents findings before rationale and
score in the schema. Its hypothesis was better coverage and less premature score
selection. The rubric, validators, saved inputs, expectations, model and runtime
settings remained fixed. Coverage improved, but usable results remained 0/12.

Independent review of `deir_appendix_a/sec000433` and `deir_main/sec000992` found
that the model accepted exclusive City enforcement despite explicit association
monitoring/fine authority. V2 also penalized a conditional trapping statement for
an enforcement procedure it never asserted, then contradicted its own secondary
error finding with score 2. C037 review identified an unsupported twenty-year premise
against `deir_appendix_d/tbl000012` and the omitted City discretion in
`deir_main/sec000981`. C014's `deir_main/tbl000434` TRA-4 applies conditionally to
projects affecting emergency access. The external source review preserves these
links and the C041 C01 centrality caveat without altering synthetic proposals.

Preflight ranges were 446–32,320 tokens for v1 and 612–32,486 for v2, within the
47,652-token input allowance. Observed input/output totals were 153,121/8,554 and
155,113/9,451 respectively. Inspect scorer elapsed totals were 152.0 and237.2 seconds,
including counting and failed judgments; they exclude service setup. No semantic
speed/quality graduation claim follows from these tuning observations.

### Decision, validation and next checkpoint

**Stop before Dev6 for user review.** Persistent source-reading, exact-quotation,
materiality, consistency and verbosity failures make expansion uninformative.
One justified revision was used; one remains unused. Repeating existing instructions
is not a concrete improvement hypothesis. A separate invented worked-example
experiment could be considered at review, but validation must not be weakened or
scores repaired merely to manufacture usable results. The larger model needs its
own exact-counter qualification and explicit stage approval before any inference.

Focused offline tests: **122 passed**. `make fix` and format/lint/type checks passed.
`make check`: **3,743 passed, one skipped, the same three historical Task 06G failures**.
`git diff --check` passed. Independent readiness, source/output and checkpoint reviews
support the early stop. Runtime processes were stopped, historical evidence and
frozen partitions remain preserved, and no reserved/test content, downloads, target
generation, later tasks, commits or pushes were introduced.


## Historical outcome — 3,000-token length-only experiment

The user removed the fixed revision cap and authorized one change at a time,
starting with output length. Inspect reran the same 12 Dev3 samples with prompt/schema
v2 unchanged, output 3,000 rather than 1,500, context 49,152 and all other settings
unchanged. The new `09e_20261010_output3k_v1` namespace preserves the plan, runtime
identity, counter receipts, Inspect log, native outputs and controlled comparison.

All 12 native requests differ from the preceding v2 run only in `num_predict`.
Prompt/schema/sample/packet/expectation identities match. All exact input counts
match both the previous run and observed native usage. The input budget is 46,152;
static upstream packet metadata retains its historical 1,500-token reserve. The
request adapter and pinned counter now explicitly support both 1,500 and 3,000.

| Same v2 Dev3 panel | 1,500 output tokens | 3,000 output tokens |
| --- | --- | --- |
| Attempted / reused / retries | 12 / 0 / 0 | 12 / 0 / 0 |
| Output-limit failures | 3 | 2 |
| Validation failures | 9 | 10 |
| Valid numeric / N/A judgments | 0 / 0 | 0 / 0 |
| Observed output tokens | 9,451 | 12,946 |

Nine complete output texts were identical. All 12 outputs retain the entire previous
text as a prefix. C041 F01 finished at 1,995 tokens, covering all six points, but
still altered literal quotes and falsely endorsed annual vaccination verification
absent from `deir_main/sec000992` (page 732) and `deir_appendix_a/sec000433` (page 298).
Its raw score 2 remains invalid and outside diagnostic agreement calculations.

The two remaining truncated controls show repetition, not justified output volume:
C037 has six real points but emitted P1–P21 and began another; C014 has six real
points but emitted P1–P26 and began P27. They repeat passages/explanations, invent
point IDs and assign `none` materiality to substantive claims. Neither reaches a
final rationale/score before 3,000 tokens. Increasing the ceiling prolonged those
failures. The completed response improved inspectability, not semantic quality.

**Decision:** retain 3,000 as an explicit comparison profile, stop here and review
structurally requiring one finding per actual answer point as the next isolated
change. Do not increase length again merely to accommodate repetition. No next
schema/prompt change, Dev6, larger-model or broad evaluation ran. Semantic metrics
remain undefined with zero eligible judgments; failure counts are not accuracy.
The fixed revision ceiling is superseded, but model/scale and data boundaries remain.

Validation: **109 focused tests passed; 3,766 full-suite tests passed, one skipped,
the same three historical Task 06G failures**. `make fix`, format/lint/types and
`git diff --check` passed. Independent counter/budget and result/source reviews
support the controlled comparison. Temporary services are stopped; no downloads,
target generation, reserved/test reads, commits or pushes occurred. Reported scorer
elapsed time is 200.5 seconds; concurrent offline validation means this is an
operational cost record, not a controlled speed comparison.


## Historical outcome — structural point coverage

The authorized follow-up changed only the native response schema. Prompt v2,
3,000 output tokens, model/settings, all 12 saved Dev3 answers and their expectations
remain identical. Per-packet schemas require exactly one finding per nonempty point
in packet order. The same schema is used for preflight, dispatch and resume; the
post-call validator independently enforces order. No prompt text changed.

The pinned [llama.cpp converter](https://raw.githubusercontent.com/ggml-org/llama.cpp/631109b34/common/json-schema-to-grammar.cpp)
requires care: `items` takes precedence over `prefixItems`, and sibling constraints
beside a `$ref` do not provide the intended point-ID override. Inline each finding,
use `prefixItems` with equal minimum/maximum length and omit `items`; use `const: []`
for empty answers. One invented Inspect call verified runtime syntax and exact
preflight (658 input / 231 output tokens), while failing semantic validation. It
is infrastructure evidence only, separate from the 12 benchmark calls.

| Same v2 Dev3 panel, 3K output | Generic findings array | Exact point tuple |
| --- | --- | --- |
| Attempted / reused / retries | 12 / 0 / 0 | 12 / 0 / 0 |
| Output-limit failures | 2 | 0 |
| Exact complete point coverage | 9 / 12 | 12 / 12 |
| Valid numeric / N/A judgments | 0 / 0 | 0 / 0 |
| Output tokens | 12,946 | 8,324 |

All native requests differ only in `format`; all exact input counts match both the
previous experiment and observed usage. All 12 outputs satisfy the new structural
schema. Nine output texts remain identical. C037 control now ends with six findings
at 1,031 tokens; C014 control ends with six at 775. Inspect reports 12 validation
failures: eight first fail substantive materiality, three literal source excerpts,
and one score/finding consistency. These are first errors, not exhaustive diagnoses.
Semantic metrics remain undefined; raw scores are not accepted judgments.

Independent source review finds C037 still repeats a phasing assertion across
unrelated points and falsely assigns it to S1: P3 cites S3/S4, P4/P6 cite S2 and P5
cites S4. C014 repeatedly quotes S1 `deir_main/tbl000413`, even for Appendix F.1
claims and a forecasting qualification citing S5. It also mislocates Candlestick
Point in Brisbane rather than San Francisco. Exact quotations and complete IDs do
not establish entailment or meaningful assessment. Frozen proposals remain unchanged.

**Decision:** stop for user review. The next isolated candidate is to restrict
substantive findings to central/secondary materiality, retaining none only for
non-substantive abstention. This has not been implemented or run. It may remove
invalid labels without improving source reasoning. No Dev6 or model/scale expansion.

Evidence is under `09e_20261010_structural_coverage_v1`, bound by the
[result pointer](../../docs/specs/task09e_final_result.json). Focused offline tests:
**155 passed**. `make fix` and format/lint/types passed; `make check` produced
**3,776 passed, one skipped, the same three historical Task 06G failures**.
Independent implementation and result review found no blocker. Runtime services
were stopped. The complete Task 09E lineage now has 48 Dev3 judge calls and two
invented qualification generations; no target generation, downloads, reserved/test
reads, later tasks, commits or pushes. Scorer elapsed time was 151.1 seconds;
concurrent offline checks prevent interpreting this as a controlled speed benchmark.


## Historical outcome — materiality eligibility

The user approved an isolated materiality change after clarifying that there are
no independent central/secondary point labels. The schema now mirrors existing
validator rules: substantive conclusions are central, other substantive points
retain central/secondary choice, and only an abstained conclusion may select
non_substantive/none with no locators. Complete inline `anyOf` branches preserve
the existing abstention distinction under the pinned converter. These are eligibility
constraints, not labels derived from expectations or a claim of correct classification.
Prompt v2, exact point coverage, the 3K allowance, model/settings and all 12 frozen
Dev3 answers remain unchanged. Citation and score checks were not weakened.

Two invented Inspect generations qualified native schema handling and token parity.
The clean abstention fixture selected the substantive branch and incorrectly scored
zero; runtime acceptance of `anyOf` does not establish correct branch selection.
The non-substantive branch is covered by offline tests. The substantive fixture
failed exact quotation. An initial fixture construction mistake (unused evidence
retained after citations were cleared) was rejected before any generation; its
setup record is preserved separately. Only the invented fixture was corrected.

| Same v2 Dev3 panel, 3K output | Coverage schema | Materiality schema |
| --- | --- | --- |
| Attempted / reused / retries | 12 / 0 / 0 | 12 / 0 / 0 |
| Exact coverage / output-limit failures | 12 / 0 | 12 / 0 |
| First failure: invalid materiality | 8 | 0 |
| Accepted numeric / N/A results | 0 / 0 | 1 / 0 |
| Other validation failures | 4 | 11 |
| Output tokens | 8,324 | 9,255 |

All 12 requests differ only in `format`; prompt, settings, sample, packet and
expectation hashes match the prior run. Exact preflight counts match both prior
counts and observed usage (155,113 input tokens total). Four output texts remain
identical. The new first-error breakdown is six nonliteral quotations, three missing
source locators, one wrong point citation and one score/finding inconsistency.
Removing an earlier validation error exposes later errors; these categories are
not an exhaustive semantic assessment.

The sole accepted response, C037 R01, is **semantically wrong**. The entire answer
is “I cannot determine the answer from the supplied evidence,” without factual
assertions or citations. The judge instead evaluates the question's causal premise
as unsupported/central and scores zero rather than N/A. Inspect correctly records
one numeric zero and 11 failures, N/A agreement 0/1, and zero numeric synthetic
comparables. Numeric agreement, ordinal error and false-supported/control rates
are undefined with zero eligible denominators. The mean zero describes one wrong
abstention classification, not overall performance. No accepted control exists.

Independent source review of C037 control finds that P1 is central and all other
points are secondary, but the assignments are not validated labels. P4's ecological
mechanism warrants necessary-premise analysis. P3 substitutes P4's claim and uses
S2 despite owning S3/S4; P4 substitutes permitting, and P6 is marked unsupported
while its explanation agrees with the answer and S2. The rationale reverses the
conclusion then contradicts itself. Raw score 2 is also inconsistent with the
unsupported-secondary P6 finding. Sources are `deir_appendix_d/tbl000012`,
`deir_main/sec000980` and `deir_main/sec000981`. Schema conformity has improved;
source reasoning and reliable materiality assessment have not been established.

**Decision:** stop for review. The next candidate is an isolated prompt clarification
that evaluates assertions in the answer rather than the question's premise, with
clean abstention explicitly distinguished. It has not been implemented or run.
Citation ownership remains another separate structural candidate. No expansion to
Dev6, a larger model or broad evaluation is justified by this experiment alone.

The `09e_20261010_materiality_v1` namespace preserves Inspect logs, raw results,
exact counters, comparisons, source review and validation through the
[result pointer](../../docs/specs/task09e_final_result.json). **168 focused tests
passed; 3,789 full-suite tests passed, one skipped, and the same three historical
Task 06G failures remained.** `make fix`, formatting, lint, types and diff checks
passed. Independent code and result review found no blocker to reporting this
bounded experiment. Runtime services stopped. The lineage now contains 60 Dev3
judge calls and four invented qualification generations, with no downloads, target
generation, reserved/test reads, later tasks, commits or pushes. Scorer elapsed
was 157.7 seconds; concurrent checks mean this is not a controlled speed benchmark.


## Current outcome — per-point checks and conclusion review

The user approved documenting, building and testing the [new staged process](../../docs/specs/task09e_staged_grounding_v1.md).
`grounding_stages` now owns narrow point inputs, separate binary prompts/schemas,
literal unsupported-assertion/source validation and deterministic aggregation.
`grounding_staged_inspect` owns sequential calls within each original Inspect sample,
per-stage receipts, failure propagation and metrics. `grounding_run --pipeline staged`
and `make evaluate-staged-grounding-panel` select it explicitly; the single-call path
remains available unchanged. The shared native-request preflight is factored into
`prepare_content_request`, with the original packet adapter delegating to it.

The conclusion call receives original answer/evidence plus validated, explicitly
fallible point predictions. It rechecks each point in order. Any binary disagreement
remains unresolved with score null; no automatic override or repair. An invalid
point call blocks the conclusion. A failed conclusion remains an evaluation failure.
Final scores come from code: conclusion fail 0; conclusion pass with a failed point
1; conclusion and all points pass 2; clean abstention N/A. There are no explicit
central/secondary labels and no generated point truth labels. Exact issue spans
identify unsupported content within compound points without rewriting answers.
Multiple and reused evidence locators remain supported.

### Bounded run and comparison

The same 12 frozen Dev3 samples, packets, expectations and model/settings identities
match the materiality experiment. The new point/conclusion prompts are separately
versioned; this changes both call decomposition and rubric representation and is
not a one-variable prompt trial. The maximum schedule was 36 point + 12 conclusion
calls; actual execution was **36 + 3 = 39**, with nine dependent conclusions skipped.
No retries or reused results occurred. The existing pinned exact counter matched
all 39 observed native input counts. Context/model gates never blocked this run.

| Same 12 saved answers | Prior materiality pipeline | Two-stage pipeline |
| --- | --- | --- |
| Native calls | 12 | 39 |
| Accepted numeric / N/A results | 1 / 0 | 1 / 0 |
| Evaluation failures | 11 | 11 |
| Unresolved disagreements | Not applicable | 0 |
| Input / output tokens | 155,113 / 9,255 | 230,989 / 21,520 |

Among 39 stage calls, 16 passed application validation: 15 point assessments and
one conclusion. All 15 accepted point assessments predicted unsupported. The other
23 calls first failed on 15 nonliteral candidate issue spans, six nonliteral source
excerpts and two output limits. At answer level, nine records first failed schema/
source checks and two hit output limits. Thirty-seven completed outputs conformed
to the decoder schema; schema shape alone does not validate literal spans or meaning.

The sole accepted conclusion is C037 R01, which again incorrectly scores clean
abstention zero. It evaluates the causal premise in the question instead of the
answer's non-assertive inability statement. Numeric synthetic-comparison denominator
is zero; agreement and ordinal error are undefined. N/A agreement is 0/1. No control
has an accepted final result; rejection/false-support rates lack eligible denominators.
The mean zero describes one wrong abstention classification, not panel performance.
No live benchmark chain containing point predictions reached an accepted final
result, so zero unresolved disagreements cannot establish inter-stage agreement.
Offline fixtures exercise disagreement, including overriding potential numeric zero
with unresolved status when the two stages differ.

Two invented answers made three separate qualification calls. A simple supported
point/conclusion chain correctly scored 2; the clean abstention incorrectly scored
0. All three completed with schema and exact token parity. Fixture outcomes remain
separate from benchmark statistics. The complete lineage contains 106 generations:
60 earlier single-call Dev3 judgments, 39 new Dev3 stage calls and seven invented
qualification calls. No target answer generation occurred.

### Source review and limitations

Independent review of C041 control found all four point predictions unsupported.
P2's source-supported feeding prohibition was rejected for not answering the full
question. P3 demanded an unspecified numerical animal limit and rejected equivalent
indoor/leash wording, while paraphrasing its issue spans. P4 inferred monitoring and
penalty procedures from possible trapping; P5 quoted the trapping evidence but
rejected the matching optional-context claim for omitting enforcement details it
never asserted. Sources are `deir_appendix_a/sec000433` and `deir_main/sec000992`.

C037 control likewise received five unsupported predictions. P2's combined acreage
figures and distinction were supported; P3 was rejected for not establishing temporary
loss avoidance, which it never claimed. P4's explicit unknown-period productivity
loss was denied. P5 was graded against the question's affirmative premise instead
of its actual performance/monitoring statement. The validated P6 rejection quoted
permitting text that supports the statement it called contradictory. Sources are
`deir_main/tbl000142`, `deir_appendix_d/tbl000012`, `deir_main/sec000980` and
`deir_main/sec000981`. No frozen proposals or point labels were changed.

**Decision:** stop for user review. Decomposition exposes failures more clearly but
does not demonstrate improved semantic quality from the 0.8B model. Do not weaken
literal/source validation, count malformed outputs as unsupported, override earlier
predictions or expand panels merely to obtain a score. Review the model/prompt
limitation before the next experiment; no further revision or larger-model run is
authorized by this result. All prior evidence is preserved.

### Validation and evidence

**214 focused tests passed.** `make fix`, formatting, lint, types and diff checks
passed. `make check`: **3,835 passed, one skipped and the same three historical Task
06G failures**, with no new failures. Independent design/code readiness and source/
result audits support reporting the experiment with the stated limitations.
The external `09e_20261011_staged_v1` namespace holds the plan, reviewed source
snapshots, runtime identity, invented qualification, Inspect logs, stage records,
exact preflights, comparison script, source review and completion inventory, bound
by the [result pointer](../../docs/specs/task09e_final_result.json). Services stopped.
Scorer elapsed total was 320.0 seconds; changed call structure makes this an
operational cost observation rather than a controlled speed comparison. No downloads,
reserved/test reads, Dev6, larger model, later-task work, commits or pushes occurred.


## Answer-only abstention follow-up — October 11, 2026

The user authorized adding the abstention step and running only that step against
Dev3. Implemented the [answer-only contract](../../docs/specs/task09e_abstention_v1.md)
in two narrow modules and an optional pre-point gate. Existing packet/transport,
exact counter and Inspect interfaces are reused. Original staged/single defaults
remain intact; explicit abstention-only and gated-staged CLI modes are available.

The unchanged twelve C041/C037/C014 answers produced one clean abstention and
eleven substantive classifications. All twelve outputs validated; no ambiguity,
retries, output limits or context failures. The previously misclassified C037 R01
“I cannot determine the answer from the supplied evidence.” is now recognized as
clean abstention. C014 O01's conclusion-only answer correctly remains substantive.
Only the initial classifier prompt ran; no revisions were needed for this panel.

Inspect recorded twelve native calls, 6,748 input tokens, 1,444 output tokens and
36.26 seconds of sample execution. All twelve exact preflight/native input counts
matched. Saved requests contain only original point IDs/text; separate synthetic
N/A proposals appear only in scorer diagnostics. All classifications agree with
those proposals, which is not calibrated accuracy. Only one clean abstention is
present; mixed and ambiguous cases have offline tests but no new live examples.
This run establishes no improvement in point/conclusion grounding semantics.

Fresh external namespace: `task_09/09e_20261011_abstention_v1/`. It preserves run
script, executed source snapshots, bindings, prompt/schema, native requests and
outputs, token receipts, Inspect logs, result audit and validation evidence.
Prior namespaces remain unchanged. No point/conclusion or invented generation
occurred; the complete gated pipeline has only offline integration validation.
The lineage now contains 118 native generations: 60 prior single-call Dev3,
39 prior staged Dev3, 12 abstention Dev3 and seven earlier invented qualifications.
No downloads, reserved/test reads, answer regeneration, later tasks, commits or
pushes were performed by this follow-up. Runtime was stopped after the run.

Validation: 86 focused tests passed and 13 CLI tests passed again after a typing-only
annotation fix; executed source snapshots preserve the pre-annotation implementation.
The full suite recorded 3,865 passed, one skipped, the three historical Task 06G
failures and one timing-sensitive hierarchy scaling failure during concurrent model
execution. Its isolated recheck passed. `make fix` passed (961 files unchanged).
`make check` passed formatting/lint and stopped at an unrelated concurrent
`synthetic_batch.py:119` type error; changed grounding modules pass type checking.
`git diff --check` passed. Concurrent synthetic-generation work was preserved.

The best-practice lesson is to separate claim-presence classification from evidence
support and answer completeness, with an explicit unresolved route. A structural
boundary reduces irrelevant input, but semantic correctness still needs broader
validation. Independent readiness review found no blocker; result review is stored
with the checkpoint. Stop here for user review; no further live stage is implied.


## Point prompt scope revision — October 11, 2026

The user authorized revising the prompt after review of the DeepSearchQA notebook
and testing whether rejections decrease. The [v2 contract](../../docs/specs/task09e_point_scope_v2.md)
owns the hypothesis and comparison. POINT v2 leads with exact target support,
limits question use to disambiguation, illustrates omitted detail/equivalent wording/
unsupported added detail, separates meaning from literal output copying, and checks
that rejection concerns an actual assertion. The conclusion and abstention prompts
are unchanged. No response-schema or point-payload change was made.

Added a minimal explicit points-only mode to the existing Inspect staged adapter
and CLI (`--pipeline points`, `make evaluate-grounding-points`). It skips downstream
calls, retains zero-point samples, returns null answer scores and reports only
point diagnostics. The optional abstention gate cannot be combined with it. All
transport, exact preflight, immutable receipts and bounded operational retry rules
are reused. No production orchestration or dependencies were introduced.

A single v2 run made the same 36 point calls as v1 using the frozen Dev3 panel and
small Qwen settings. Paired artifact checks verified identical payloads, schemas,
settings and packet identities for every point. All 36 exact token counts matched
native observations. Inspect retained 12 answer records, including 2 zero-point answers;
10 answers were attempted. No abstention, conclusion or invented calls ran.

Rejections did not decrease: v1 had 35 parseable false flags and 1 truncated output;
v2 had 36 false flags. Validated judgments changed from0 supported / 15 unsupported to
0 supported / 17 unsupported. Failures changed from20 schema + 1 length to19 schema + 0 length.
V2 schema errors comprise 13 nonliteral target spans and 6 nonliteral source excerpts.
This is slightly better output validity, not better grounding. Native usage:
193,782 input / 13,673 output tokens, 218.03 seconds, 0 retries.

Independent source review found some completeness objections disappear but new
incorrect reasons replace them. C041 P2 rejects an authority paraphrase despite
admitting support; P5 still demands unasserted enforcement details. C037 P3 drops
the avoidance-completeness objection but misreads conditional evidence. P4/P5 grade
an avoidance assertion absent from the target; P6 admits permitting support and
then rejects for not answering the broader question. These examples remain source
linked in the external review. All-false predictions on perturbed answers do not
establish correct defect detection; their reasons require separate source review.

Fresh namespace `task_09/09e_20261011_point_scope_v2/` preserves source snapshots,
prompt/version, requests, raw/validated outputs, paired comparison, independent
review and Inspect aggregation. Prior experiments are unchanged. The lineage now
contains 154 native generations (previous 118 plus 36 points). No downloads, regeneration,
reserved/test data, target generation, later-task work, commits or pushes here.
Stop for review. This controlled negative result gives no basis to broaden the
panel or claim that wording alone resolves the small model's instruction failures.

Validation for this cycle: 72 focused tests passed. `make fix` passed; `make check`
passed formatting, lint and types, then recorded 3,902 passed, one skipped and only
the three historical Task 06G failures. `git diff --check` passed. Independent
integrity review confirmed the exact comparison and no downstream calls. Source
review found two City-authority defects newly identified but with invalid outputs;
vaccination and fee-conversion defects remain correctly identified, while grading
and emergency-access qualification defects are still missed. This does not rescue
the all-false behavior. Final source hashes match the executed snapshots and the
owned local runtime is stopped. User review is the next action.


## Combined 09A.3 all-eligible experiment — October 11, 2026

The user requested the new combined dataset and explicitly selected every eligible
answer for the same Dev3/Dev6 questions. The [experiment outcome](../../docs/specs/task09e_09a3_small_v1.md)
owns the current result. All 136 answers were frozen before inference, with separate
restricted stage proposals and per-record provenance roots. Dev3's 69 answers ran
first; reflection and source review preceded the remaining 67. Inspect aggregated
exact preserved records into Dev6 without rerunning Dev3.

Added a narrow combined-dataset panel adapter, explicit CLI/Make routing, and
stage diagnostic coverage/confusion metrics. Native requests still use the existing
packet/transport interfaces and contain no proposed labels or automatic metrics.
Original panels, results and development/test/reserved boundaries remain preserved.
The current experiment supersedes the original four-answer selection only for this
new dataset version; it does not rewrite historical panels or authorization.

There is no demonstrated semantic improvement: all 142 valid point predictions
were unsupported, including 99 proposed-supported points. Only 6/12 clean
abstentions were recognized; 15 substantive answers were incorrectly exempted.
Thirty numeric scores were all zero; 12/29 comparable scores matched proposals.
The rest were 21 N/A, 75 output failures, nine ambiguous gates and one unresolved
point/conclusion disagreement. Source review confirms false rejections, question-
premise substitution and conclusion/point conflation alongside some genuine defects.
The new stage labels expose these failures; they are not calibrated truth.

All 447 native requests passed exact count parity and label-free input audits.
No retries or operational/context failures occurred. Independent recomputation
verified aggregation and all 8,409 preserved Dev3 file hashes. Prompt versions and
settings remained fixed, including the 3,000-token reserve. No inference after the
small-model Dev6 checkpoint is authorized. Stop for review before a stronger model,
full-19, further revisions or later tasks. The external namespace is
`task_09/09e_20261011_09a3_small_v1/`; the result pointer retains every prior run.

Learning: broader varied abstentions invalidate confidence drawn from a single
successful abstention example. Stage-level labels and explicit coverage reveal
failure routing and score collapse. A higher proportion of matching zeros on a
different answer population does not demonstrate better discrimination.


Validation: 115 focused tests passed. `make fix` passed with 965 files unchanged.
`make check` passed formatting, lint and types, then reported 3,912 passed, one
skipped and only the same three historical Task 06G failures. `git diff --check`
passed. Independent code and final-result review found no implementation blocker;
source reviews preserve the semantic limitations above.


## Current authorization — Qwen 9B Dev3

After reviewing the small-model results, the user authorized the proposed
[fixed-pipeline 9B comparison](../../docs/specs/task09e_09a3_qwen9b_v1.md). Run exactly
the same 69 Dev3 answers from 09A.3 with the current prompts and 3,000-token output
allowance. Bind the exact local 9B renderer/tokenizer before inference. Preserve all
earlier results and stop after Dev3 for user review; 9B Dev6 remains unauthorized.
This explicit follow-up supersedes earlier larger-model stop language only for
this bounded run. No prompt changes or later tasks are part of the comparison.


## Qwen 9B Dev3 outcome — October 11, 2026

The [fixed-pipeline comparison outcome](../../docs/specs/task09e_09a3_qwen9b_v1.md)
owns the completed result. All 69 identical answers ran through Inspect with the
same prompts, schemas and settings except the pinned model identity. A narrow
exact-counter allowlist extension qualifies the existing local 9B assets without
downloads or relaxed token checks. All 255 calls passed exact native-count parity;
all 16,460 prior small-model files and 12 current source bindings were verified.

There is meaningful but incomplete improvement: all six clean abstentions are
recognized, false exemptions fall from seven to one, and 41 proposed-supported
points are accepted rather than none. On 45 points validated in both runs, 18
changes move toward proposals and two away. Yet only 12/69 answers receive numeric
scores, 50 fail output validation and C014 has no scores. Nonliteral source excerpts
dominate failures; modality strengthening, table interpretation and one false
abstention exemption remain. Proposed labels are diagnostic, not calibrated truth.

98 focused tests passed. `make fix` passed; `make check` reported 3,923 passed,
one skipped and only the three historical Task 06G failures after successful
format/lint/type checks. `git diff --check` passed. Independent integrity and result
reviews found no execution/accounting blocker. Runtime stopped; no 9B Dev6, full-19,
later work, commits or pushes ran. Stop for user review before further experiments.


## Follow-on plan — October 11, 2026

[Task 09E.1](09e1_compare_cloud_and_decision_judges.md) owns the requested cloud
and decision-model comparison, separate quotation diagnostics, caching/cost
verification, offline preparation and bounded local Clef trial. It is planned
for a new implementation chat; no execution occurred while writing the plan.
Its explicit scope supersedes the preceding stop language only for that follow-on
work. Earlier specifications and results remain preserved.
