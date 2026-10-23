# Task 15B — Regenerate conclusion-only synthetic development cases

Status: complete with disclosed exclusions (2026-10-21). User authorization: “ok now regen the synthetic test
cases for the conclusion judge”. This activates direct authoring, independent
review and offline publication, not judge execution or target generation.

## Abstract and goal

Regenerate C contrasts from the approved nineteen development questions under
the accepted Task 15 policy. Preserve old candidates/labels/results and frozen
v8. New expectations are independently agent-reviewed proposals, not human gold.

## Inputs and outputs

Use `task09f_question_publication_v2_result.json` to verify completion and split
metadata, then open only allowlisted development case files. Project exact
question and `answer.conclusion.text`; no support, sources, old synthetic
answers, predictions, test or reserved payloads enter authoring. Existing inline
reference text remains exact; separate citation IDs are excluded.

Use the accepted `adequacy_labeling_rules.md` and the Task 15 candidate version
from 15A. Write a new versioned catalog, coverage, judge-ready three-field JSONL,
separate labels/provenance, independent reviews, validation and completion seal
under `ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_15/`.
Track a compact result pointer and an explicit offline loader, leaving the old
C246 loader/default judge dispatch untouched.

## Authoring contract fixed before generation

- One slot per applicable contrast per question, plus unchanged baseline.
  The versioned catalog has 25 slots including baseline: at most 475 candidates.
  This retains the prior 21-slot pattern with revised extra-item semantics and
  four additional contrasts: compatible answer addition, equivalent purpose via
  mechanism, circular explanation, and named analysis without its finding.
- Account for all 475 slots as generated/shared/inapplicable/unresolved; do not
  force a mutation, expected label, exact size or balanced count when ambiguous.
- Author directly with bounded coding agents, no provider API calls. One initial
  authoring pass, then independent review and at most two repair rounds. Unresolved
  disagreements remain excluded from runnable samples.
- Aim for coverage of both pass and fail mechanisms, not a target-model pass-rate
  increase. Critical controls are material omissions, reversals, incompatible
  relationships/conditions and internal contradictions, designated before scoring.
- Group by original question. Assign four non-original-six questions to an audit
  partition by sorting SHA256 of `task15-c-synthetic-v1:<case_id>`; all others are
  tuning. This is deterministic, with no outcome-based selection. All variants
  of a question stay together; exact/shared duplicates cannot cross partitions.
  These are familiar development questions, not unseen-question qualification.
  Audit payloads may be read for authoring/review but not candidate tuning; no
  audit judge results exist. Original reserved challenges remain unopened.
- Label truth concerns C's three-field comparison only. A compatible addition's
  source truth is not inferred from C acceptance. S/G composition coverage is
  documented separately, not claimed tested by conclusion-only fixtures.
- Skip malformed output, clean abstention, injection and support-only changes.
  Preserve reference ambiguity without enriching the three-field contract.

## Plan and research / learning checkpoint

Inspect the historical authoring contract and existing intake/publication code.
The full intake verifier opens all release members, including test data; the
historical regeneration path depends on old candidates and a fixed population.
Neither fits this boundary. Reuse `artifact_io` no-clobber primitives and C input
validation with narrow versioned JSONL glue, no new dependency or provider runner.
Separate expectations from payloads and group variants to avoid leakage. The
Task 15 umbrella's cited evaluation research motivates protective negatives;
this authoring run does not establish judge accuracy.

1. Pin policy/catalog/prompt/release identities and project verified dev inputs.
2. Author disjoint question groups and independently review every candidate.
3. Resolve named issues, record exclusions and deduplicate exact payloads.
4. Publish the isolated payload/label/provenance streams and completion last.
5. Verify input hashes, slots, reviews, split isolation, labels and replay;
   publish the pointer, counts, limitations and current routing.

## Validation and review

Every runnable item must have a distinct-author review bound to its exact bytes,
a justified boolean proposal and a valid three-field C input. Verify 19-case and
475-slot accounting, exact baseline equality, grouping, unique identities,
duplicates, provenance, inventory closure and tamper rejection by the loader.
Use existing package checks (`make fix`, `make check`, `git diff --check`) for any
runtime changes. Independent final review checks negative-control strength,
ambiguity handling, exposure claims and protection of historical defaults.

## Non-goals

No model/provider calls or cost-budget assumption, judge scores, prompt tuning,
target generation, S/G changes, historical relabeling, test/reserved payload
inspection, MiniMax work, commit or push. Provider request budget is zero.
Later execution still requires explicit population, run type and numeric budgets.

## Outcome

Published [the sealed result pointer](../../docs/specs/task15b_conclusion_synthesis_result.json)
and [versioned catalog](../../docs/specs/task15b_conclusion_synthetic_catalog_v1.json).
The external publication is `pipelines/brisbane_baylands/task_15/synthetic_20261021_v1`
under the artifact root, including `review.html`, separate payload/expectation/
provenance streams, exact-byte review receipts and a completion inventory.

- All 475 slots across nineteen development questions are accounted for:
  340 unique runnable samples, 126 inapplicable, eight unresolved and excluded,
  and one shared candidate (C054 F07/A01). Expectations propose 133 passes and
  207 failures, including 149 designated critical negatives.
- Question-grouped partitions contain 259 tuning and 81 audit samples. Audit
  questions are C007, C027, C042 and C054. These are familiar development
  scenarios, not unseen-question qualification.
- Every slot received independent review. Unresolved slots are C008 F07,
  C019 F07, C029 F07, C042 P07/F07, C045 A01/F07 and C056 F07. Their records
  preserve uncertainty about material omissions, inherited question scope,
  reference qualifications and answer-changing additions; no forced labels
  enter the runnable suite.
- The offline loader verifies publication integrity, exact input bindings,
  baseline equality, separate expectations, all-slot review coverage and split
  isolation. Fourteen focused tests cover validation and tampering. `make fix`
  and `make check` passed: 4,426 tests passed, one skipped; dependency
  deprecation warnings remain. Rebuilding reproduced all 82 publication files
  byte-for-byte. Independent final publication review found no action items.

Preparation, replay, loader and final-review receipts remain alongside the
publication in `synthetic_20261021_v1_working`; the sealed publication is not
amended by closeout. Source identities and exact question/reference hashes are
recorded in its input bindings. Original source provenance remains authoritative.

The main learning is to preserve ambiguity as explicit exclusions and keep
expected labels outside judge inputs. A greater pass count is not evidence of
better judging. These expectations are reviewed agent proposals, not human gold.
No judge/provider calls, scores, historical relabeling, reserved/test payload
inspection, MiniMax work, commits or pushes occurred. Historical C246 and frozen
judge defaults remain unchanged. Native candidate execution, comparison metrics,
numeric budgets and S/G composition checks remain separate future work.
