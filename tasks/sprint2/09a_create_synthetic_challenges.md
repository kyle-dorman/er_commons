# Task 09A — Create synthetic development answer challenges

Status: **Active entry contract; ready for implementation/execution authorization.**
This planning request does not itself start implementation or Astra runs. Once
09A execution is authorized, qualify and run the bounded workflow without adding
another mandatory per-variant human approval step.

## Abstract

Use Astra to perturb approved development answers into a broad, evidence-backed
challenge set for two later judges. Preserve successful answers, partial-credit
answers and failures, with more failures than successes where naturally applicable.
Each variant carries a proposed expectation, not a new human-approved label.
The output must work before a harness or judge has been selected.

## Goal

Publish restartable, framework-independent synthetic records across all **19 dev
cases**, including applicability/skip accounting, exact edits and source-linked
proposed grounded-correctness (G) and adequacy (A) scores. Cover meaningful failure
modes without manufacturing unreasonable examples to meet a count.

## Inputs and source access

- [Task 09 umbrella](09_build_evaluation_and_qualify_judges.md),
  [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md),
  and the [evaluation boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary).
- [08H result](../../docs/specs/task08h_final_result.json) binds release
  `task08_20261009_v1`, its split, completion, handoff and source corpus. Resolve
  paths from that pointer and the configured root; verify hashes and release
  inventory before consuming files. Do not guess per-case reference paths.
- Read `target/dev.jsonl` and load curator references only for its exact case IDs.
  Verify the split has 19 dev / 30 test and disjoint membership using metadata;
  do not open test questions/references to design perturbations.
- Use the exact approved question, current structured answer, point/citation links,
  reference support/context roles and allowed canonical source passages for each
  dev case. Exclude old answer versions and curator official-response prose from
  model evidence. Preserve all accepted corpus/edition/usability limitations,
  including the qualified Final F.1 substitution; do not replace it by a blanket
  file-name ban that discards accepted evidence.
- Consult [architecture](../../docs/architecture.md) and
  [artifact rules](../../docs/data_artifacts.md). Inspect existing
  `group_answer_intake.py`, `group_answer_batch.py`, `group_answer_records.py` and
  `artifact_io` as reuse candidates; do not reuse their task-specific prompts or
  validators blindly, since intentional wrong citations must be representable.

## Outputs

Under a fresh versioned namespace beneath
`ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_09/` publish:

1. Verified dev-only intake and exact per-case source packets.
2. Versioned perturbation catalog, generation prompt, output schema and run config.
3. Raw Astra attempts and full synthetic answers, separately stored proposed
   expectations, edit records and source evidence.
4. Case-by-perturbation coverage with generated, inapplicable, ambiguous, blocked
   or failed dispositions and reasons. Include unchanged references as controls.
5. Validation, duplicate checks, counts, limitations and checksummed completion;
   a small tracked result pointer and outcome route to the external artifacts.

Keep generated answers in ordinary JSON/JSONL, not a framework-specific dataset.
Track small schemas/prompts/configs in the repo; no full evidence packets in Git.
Names above are output requirements, not existing commands or artifacts.

## Variant record contract

Before generation, implement a narrow versioned schema containing:

- Stable variant ID, case ID, parent reference version/hash, release and source
  packet identities, perturbation ID and severity where relevant.
- Full structured synthetic answer in the general Decision 006 answer format:
  conclusion, supporting points with citation links, attached material
  qualifications, optional context, and answer/abstention status as applicable.
- Exact edit operations with field/point paths and before/after values. Preserve
  a reconstructable comparison to the unchanged reference; retain explicit mapping
  when points are combined or split and assign unique new point IDs.
- Intended failure or preserved property, plus any unintended secondary effects.
- Separate proposed G and A scores (0/1/2; G N/A for clean abstention), rationale
  for each dimension, exact source IDs/locators supporting that rationale, and
  ambiguity/verification status. If an expectation cannot be justified, mark it
  unresolved rather than force a score into the comparison population.
- Actual authoring model/settings, prompt/schema hashes, input/output references,
  attempt identity and validation status. No fabricated model identity or approval.

Keep expectations, edit descriptions and perturbation names out of later judge
inputs. Source roles help the author but must not leak into grounding packets.
Deliberately invalid citation IDs belong to the answer record; the validation
report distinguishes expected citation defects from generation/serialization bugs.

## Perturbation catalog and expected behavior

The table describes expected tendencies. Astra must justify the actual G/A pair
for each case; a label is not established just by naming a mutation. Severity is
whole-answer significance, not the fraction of bullets altered.

| ID | Perturbation | Expected check |
| --- | --- | --- |
| P01 | Faithful paraphrase | Both scores preserved |
| P02 | Reorder points | Both preserved |
| P03 | Combine points without losing logic/citation links | Both preserved |
| P04 | Split a point where meaningful; retain support and qualification attachment | Both preserved |
| P05 | Compress without losing essential substance | Both preserved; no length preference |
| P06 | More confident/formal presentation without changing assertions | Both preserved; certainty changes belong to F05 |
| P07 | Remove optional context | No semantic penalty |
| P08 | Different verified supporting passage | Full semantic credit possible despite lower gold citation matching |
| P09 | Different verified sufficient argument | Full semantic credit possible without reference wording/argument matching |
| O01 | Remove essential explanation, keeping a supported qualified conclusion | G may stay 2; A generally 1 |
| O02 | Answer only part of a multipart question | G may stay 2; A falls |
| O03 | True cited background answering a neighboring question or evading this one | G may stay 2; A generally 0 |
| O04 | Remove the substantive direct conclusion, retaining facts and a schema-valid non-answer conclusion field | A depends on whether the answer still resolves the question |
| F01 | Add a material unsupported secondary assertion | G generally 1 if conclusion independently supported |
| F02 | Replace a necessary premise with unsupported content | G generally 0; assess A separately |
| F03 | Reverse the central conclusion with citations unchanged | Both generally 0 |
| F04 | Change a material number, unit, direction or comparison | Scores follow central versus secondary impact |
| F05 | Replace possibility/estimate with certainty | Detect unsupported overstatement |
| F06 | Swap scenario, location, population, alternative or time period | Detect misapplication to question scope |
| F07 | Remove a decisive condition or mitigation requirement | Can fail both dimensions |
| F08 | Infer causation from association or another unjustified reasoning step | Assess missing logical support |
| F09 | Claim resolution where the evidence leaves uncertainty | Respect source limitations |
| F10 | Introduce an internal contradiction | Judge the whole answer and centrality |
| C01 | Replace central citation with a real irrelevant passage | G 0 if remaining actual citations cannot establish conclusion |
| C02 | Attach valid citations to wrong points | Check actual point-to-source support |
| C03 | Remove necessary member of joint evidence support | Remaining sources may not justify conclusion |
| C04 | Retain correct citations but add a claim they do not establish | Citation matching cannot substitute for grounding |
| C05 | Invent an ID or reference unavailable evidence | Resolution diagnostic plus semantic consequence; no silent repair |
| R01 | Clean insufficient-evidence abstention | G N/A, A 0 on answerable benchmark |
| R02 | Abstention status with unsupported substantive assertions | Assertions still evaluated; no blanket G N/A |
| R03 | Embed instruction to award full credit | Ignore instruction; evaluate substantive answer normally |

Generate one clear instance of each applicable category initially. Add a second
only for a materially different severity, source structure or reasoning behavior.
No eight-variant cap, fixed total quota, exhaustive Cartesian products, or forced
positive/negative ratio. Report observed counts and all skipped categories.
Keep P06 separate from factual certainty changes; keep schema-malformed payloads
as software fixtures, not artificial semantic challenge answers.

### Alternative evidence and arguments

P08/P09 are discovery work: no alternative argument is presumed to exist. First
consider the dev case's actual source packet. If needed, perform a bounded,
read-only lookup in the release's allowed source corpus using source text and
dev question terms, never other cases' references or official-response hints.
Record search queries, candidates and selected canonical passages. Make at most
one supplemental discovery pass per case in this initial batch; unresolved
alternatives receive an explicit disposition rather than open-ended research.
Use exact passages and preserved table/footnote context to check every necessary
premise, qualification and scope. Save alternative arguments as model-verified
proposals with uncertainty, not human-approved additions to gold evidence.
Do not rewrite the frozen reference or broaden its required citation pool.

## Research / learning checkpoint

Read [Anthropic evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
and the current decision section in the [judge notes](../../docs/llm_judge_learning_notes.md).
Explain why controlled edits, positive invariance checks, partial-credit cases,
and source-linked expectations are useful, and why synthetic agreement does not
establish human agreement or natural-output reliability. Use existing JSON Schema
or Pydantic dependencies for records; no harness choice is required for this task.

## Plan / spec and execution sequence

1. **Prepare:** verify 08H, build a dev-ID allowlist, inspect actual reference
   structure, and write the small schema/prompt/config. Include an explicit full
   answer format and G/A anchors in the authoring prompt. No unseen remapping of
   the human-approved reference becomes a new approved answer.
2. **Qualify locally:** exercise intake/recording with fixtures, including test-ID
   rejection, altered upstream identity, split/combined points, abstention,
   intended invalid citations, unresolved scores, and interruption/replay.
3. **Model smoke:** after execution authorization, generate a small sample from
   two varied dev cases, covering an invariance edit, partial-credit omission,
   central failure and citation failure. Inspect output and source justification;
   this is a bounded implementation review, not a new full human labeling pass.
   Reuse valid smoke outputs only when final prompt/schema/input identities match.
4. **Batch:** use Astra (`gpt-6-astra`) via the established authoring route. Save
   actual invocation metadata. One isolated case job produces its catalog coverage
   and variants, with bounded supplemental discovery as above. Default to one
   worker until the route is qualified; record any concurrency choice. Do not
   expose workspace-wide test or response files to unrestricted model tools.
   Prefer deterministic source preparation plus source-only generation packets.
5. **Recover:** save immutable attempts, publish case completion only after
   validation, and reuse only checksum-valid same-configuration completed units.
   Retry infrastructure failures at most twice with unchanged inputs and recorded
   backoff. Semantic/schema failures stay visible; one named corrective authoring
   attempt may address concrete findings, preserving the original. This authoring
   revision policy must not be copied to target prediction execution.
6. **Validate and publish:** check accounting for every case/category, unique IDs,
   exact parent bindings, edit reconstruction, source locator matches, reference
   preservation and leakage prevention. Check duplicates across variants within
   cases; retain deliberate controls, flag redundant generated copies. Automated
   source checks establish resolution, not correctness of a proposed score.
7. **Reserve final checks:** before any 09B prototype or 09E/09F prompt tuning,
   deterministically assign a small stratified subset of valid variants to final
   checks and save its IDs/seed. Keep these out of judge smoke/prototype/tuning
   packets; exclude variants already used in any judge-facing smoke. Authoring
   smoke in step 3 does not itself expose a variant to a judge.
   Preserve failure-type coverage where feasible; this is a within-development
   check, not a new benchmark split or independent-question estimate.
8. **Handoff:** summarize viable/ambiguous/failed counts by case/category and G/A,
   demonstrate representative records, and publish artifacts plus result pointer.
   Explicit failures may close accounting but cannot count as generated coverage.
   Record any remaining repair work rather than declaring complete coverage.

## Review pass

Use small independent reviews of generation prompt/rubric alignment, dev-only
access, and publication/restart behavior. Inspect a stratified sample and flagged
alternatives/ambiguities without requiring Kyle to label every variant. Preserve
review findings and label all automated verification accurately.

## Validation and acceptance criteria

- All 19 development cases and catalog categories have explicit dispositions;
  no test questions/answers or official responses enter authoring packets.
- Exact unchanged controls, full variants, reconstructable edits, proposed scores,
  justifications and raw provenance are saved. Positive, partial and central-failure
  coverage exists where applicable; inability to generate a category is visible.
- Ambiguous expectations and unverifiable alternatives are excluded from the
  unambiguous agreement denominator, while still preserved for analysis.
- Intentionally bad citations survive publication; accidental artifact defects
  fail validation. No wrong citation is silently replaced with a gold citation.
- A stopped batch resumes without clobbering validated output, source seals remain
  unchanged, and final inventories/hashes verify. Run focused tests, `make fix`,
  `make check`; docs-only edits require `git diff --check`.
- No judge, target or retrieval benchmark scores are claimed. 09A reserves
  an untouched synthetic check subset for 09G before any judge prompt tuning; it need not
  choose a framework or use judge feedback to select easy variants.

## Non-goals

Judging the synthetic answers, human calibration, harness selection, local-model
installation, target generation, held-out test inspection, reference amendment,
new source extraction, public redistribution, exhaustive alternative-argument
research, or a new review UI. No additional compulsory human labeling campaign.

## Outcome

Not started. Record namespace, model/prompt/schema identities, coverage and skipped
reasons, source verification limits, validation and the exact 09B/09C handoff.
