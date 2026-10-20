# Task 11D.1 — Public answer specification and repeatable prompt comparisons

Status: Complete (2026-10-17); no acceptable candidate under the declared promotion criteria.

## Abstract and goal

The user authorized working through the five proposed steps and further inexpensive
prompt cycles. Audit alignment between public instructions and frozen grading rules,
compare a consolidated specification and invented examples, then measure repeated
performance. Report what works and what does not, including no selection if necessary.
This is a new bounded task; original 11D records remain sealed.

## Inputs and outputs

Use the accepted 11A fixed six, 11B/11C baseline (C017 C failure and C019 S failure),
11C.1 cleanup, original 11D and its 100K continuation. V3/V4 full-six runs are saved
comparators, not fresh controls. Use general grounding/adequacy/no-answer policies,
09G frozen judges and unchanged Task 10 evidence-only packets. Output a public
answer specification, alignment audit, versioned prompts, complete run comparisons,
independent reviews, accounting and replayable result pointer.

## Plan and research

1. Map public instructions to general grading requirements; independently inspect
   only the six already exposed cases for unclear requirements versus real errors.
   Keep case-specific audit notes and all reference answers evaluator-only.
2. V5 consolidates the answer specification into explicit conclusion, support,
   claim-local citation, comparison and abstention obligations. Hypothesis: clarity
   and reduced repetition improve compliance without demanding exhaustive background.
3. V6 differs only by invented, unrelated examples of those same obligations.
   Hypothesis: concrete demonstrations improve application over rules alone. Examples
   contain no project facts, reference content or evaluator explanations.
4. Keep development separate: all six remain tuning cases. Do not inspect/evaluate
   remaining 13, locked test or reserved challenges; do not start 11E. A successful
   result is only a development candidate for a later separately authorized check.
5. Run V5 and V6 on all six, then repeat each unchanged once regardless of semantic
   failures. This tests reliability without choosing lucky samples. After all four
   evaluations and manual reviews, optionally test one V7 revision and its unchanged
   repeat if a specific generic failure motivates it. Record its hypothesis first.

Primary guidance reviewed in this conversation: [Anthropic evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
for explicit task requirements and transcript review; [OpenAI evaluation practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
for task-specific criteria, human calibration and held-out measurement;
[ALCE](https://arxiv.org/abs/2305.14627) for separate correctness and citation quality.
No new runtime dependency, schema, model or judge change is needed.

The [public specification](../../docs/specs/task11d1_public_answer_specification.md)
owns the requirement mapping and predeclared manual materiality categories.

## Fixed experiment and limits (before dispatch)

Panel order: C041, C017, C019, C014, C037, C056. Luna gpt-6-luna, medium reasoning,
default tier, existing schema, 100,000 exact input cap and 4,096 output tokens
including reasoning. Frozen A/G/C Luna and S Haiku semantic settings unchanged.
Reuse the explicit 11D 100K generation/evaluation configs.

At most three new prompt versions, each with exactly two full-six observations:
**36 target generations, 432 judge calls, 468 token counts**, zero retries,
zero per-answer repairs, zero discarded outputs. Required point fan-out must fit
72 judge calls per arm; never drop points. Six generation calls/counts per arm,
15-minute generation and 30-minute evaluation limits. Overall three working days.

Reserve USD 0.028072 per possible call at the preserved conservative token rates:
USD 0.168432 generation and USD 2.021184 evaluation per arm; **USD 13.137696**
maximum new liability. Prior reservations USD 30.525408 remain intact; combined
maximum USD 43.663104 is below the existing USD 100 ceiling. Counting allowance is
zero under the user's assumption, actual cost unknown; OpenAI counting billing is
unverified. Preserve raw usage and dated price estimates, not invoice claims.
The earlier observed sub-ten-cent runs are estimates, not a per-run guarantee.

Stop all calls on integrity, context, provider, count/usage or structural failure,
expired time/spend/call bounds; retain complete planned coverage and missing statuses.
Semantic failures do not suppress planned repeats. After V5/V6 pairs, stop revision
if no actionable general failure exists; otherwise allow only V7 and its repeat.
No further revisions or favorable-output mixing. Retain earlier version on ties.

## Selection and interpretation

Report each case and repeat with A/G/S/C, automatic checks, failures and source-linked
manual findings. Show grounding denominators: adding points changes opportunities
for failure. Compare repeat consistency and failure recurrence, not just pooled
point percentages. Avoid causal or population claims from six adaptively tuned cases.
For promotion require valid complete coverage in both repeats, substantive answers,
all applicable G/S/C passing and no unresolved material source/logic/completeness
error in independent review. Otherwise report no acceptable candidate and retain
which changes improved particular mechanisms. Do not change judges to match manual
opinions. Distinguish judge limitations, task ambiguity and generation mistakes.

## Validation and review

Before calls: audit public-spec/prompt isolation, offline selected packet equality,
protected hashes/seals, original and continuation no-provider replays, fixed config
and identities; independently review dispatch and prompt. Run appropriate offline
checks; for code changes use make fix, make check and git diff --check. External
scripts are narrow orchestration around existing Make targets. Preserve pre-dispatch
sources, all raw responses, receipts, logs, reservations and rejected prompts.
After calls: independently review every answer against its supplied evidence,
verify all run inventories and no-provider replays, bind results and update routing.

## Non-goals

No changes to Task 10, source evidence, reference answers, frozen judges, sealed
11B/11C/11D runs or test partitions. No broader model sweep, retrieval change,
multiple-call generation pipeline or all-development validation. No 11E.

## Schema clarification and bounded continuation (before replacement dispatch)

The first V5 run produced three delivered outputs with invalid applies_to prose,
one valid output, and an interrupted fifth request; the sixth was undispatched.
The lead stopped it after diagnosis. The existing runner continues a panel after
post-response validation failures, so further cases had started before detection.
All raw responses and the unsealed interrupted run remain unchanged; the original
stage's global stop remains in place. No judge ran. Never repair these answers or
silently use their valid subset as a comparison panel.

This is a prompt-interface omission: applies_to requires existing answer point IDs,
not semantic descriptions. The original structural stop exposed it; the user's
request to execute the five-step investigation authorizes a bounded correction.
V5b/V6b add exactly the same explicit field definition and nonblank/citation requirements for every point, including optional context, to the preserved V5/V6 texts.
V6b remains V5b plus the same invented examples. Hypotheses are unchanged; this is
an operational prompt clarification rather than a favorable answer reroll.
Use a fresh validation_11d1_schema_20261017 stage, protecting the entire failed stage.

The replacement stage permits the original six arms: V5b/V6b with two observations
each, then optional V7 with two observations. Total task ceilings including the
failed attempt become **42 target calls, 432 judge calls, 474 counts** (conservatively
reserve all six first-arm slots). New-stage liability remains USD 13.137696;
initial failed-arm reservation USD 0.168432 is not refunded. Combined prior-plus-new
maximum is USD 43.831536, below USD 100. Keep initial interrupted usage unknown.

Within each replacement generation panel, retain all six results even if an output
fails post-response validation; then stop before evaluation or another panel.
Integrity/context/provider errors still stop calls. This distinction matches the
existing runner and preserves complete-panel accounting. No additional schema
repair stage is authorized by this contract. No production code changes.

## Outcome

Completed all five steps: public-rule/validator alignment, consolidated prompt,
separate invented-example treatment, development separation, and paired repeated
runs with independent source review. Examples improved the observed frozen scores
relative to rules alone; additional verification prose regressed. **No candidate
met the predeclared promotion criteria.** V6b is retained only as the strongest new
diagnostic comparator, not a selected baseline. The
[result pointer](../../docs/specs/task11d1_final_result.json) binds exact identities,
raw evidence, all reviews, accounting and offline replays.

### Comparisons and hypotheses

All corrected arms used the complete fixed six in the same order, unchanged evidence,
models, judges, schema, 100K input cap and 4,096 output cap. Every corrected output
was valid. The table reports a diagnostic conjunction of all applicable G/S/C
checks per answer, not the official Task 12 aggregate or a benchmark estimate.

| Prompt | Treatment and hypothesis | Observation 1 | Observation 2 | Interpretation |
| --- | --- | --- | --- | --- |
| V5b | Consolidated public rules and complete field semantics should clarify obligations | 2/6 | 3/6 | Rules alone did not reliably preserve conclusion conditions, comparisons or citation scope |
| V6b | Exact V5b plus unrelated invented examples should improve application | 5/6 | 5/6 | Best new frozen-score pattern; C014 fails both, and manual defects remain |
| V7 | Exact V6b plus evidence-first verification should reduce relational errors | 3/6 | 3/6 | Some citation joins improved, but method errors, omissions and overqualification persisted or returned |

Saved V3 and V4 six-case observations remain comparison history: 4/6 and 5/6,
respectively, under this diagnostic. They have one complete observation each and
are not paired controls. V6b does not exceed the earlier V4 single-run score.
The 10/12 versus 5/12 observed advantage for examples is descriptive: only six
unique, adaptively exposed tuning cases and two observations per prompt. It does
not establish significance, generalization or reliable all-six success.

### What worked

- The public specification exposed an important implicit requirement: each point
  and factual qualification must stand on its own citations. Another point's
  citations or a link through applies_to cannot supply missing evidence.
- Reading the executed validator exposed field semantics absent from the prose.
  Once those were stated, all 36 corrected outputs passed structural validation.
- Invented examples improved the observed conclusion/support pattern: C017 and
  C019 passed frozen G/S/C in both V6b observations, while V5b varied. Examples
  remained unrelated to project cases and contained no references or feedback.
- Repeats revealed variation that a single good run would hide. All 18 same-prompt,
  same-case request pairs were byte-identical; outputs and failures still varied.
- Independent source review caught errors the judges passed, and inspecting judge
  explanations also corrected some initial manual interpretations. Both are retained.

### What did not work and why

**Conclusion and support remain separate failure surfaces.** V5b omitted storage
conditions from C017's first conclusion, then omitted enforcement authority from
C041's second conclusion. V7's first C041 answer stated a no-pets requirement in
its conclusion without making that categorical premise explicit in support;
its repeat again omitted C017's distributed-storage assumption from the conclusion.
Supported information elsewhere did not reliably survive summarization.

**More procedural instructions did not solve source interpretation.** V7 improved
some C014 cross-passage citation links, but both manual reviews found a wrong
transportation-method classification. In observation1 the error was in supporting
point S3 and G caught it. In observation2 it was in conclusion C1, which is not a
G item, while its evaluated points passed. This is a coverage distinction, not
evidence that G missed the same assertion on a repeat. V7 also produced overqualification on C056 in observation1
and a matched-storm overstatement in observation2. V5b's second C056 observation
had a similar comparison issue. These are distinct from missing public rules.

**Examples did not make local citations reliable on every case.** V6b's first
C014 answer used named-development mappings without citing the passage containing
those mappings. Its second answer retained a different unsupported relationship.
The generic example did explain cross-passage citation needs; instruction clarity
alone did not ensure compliance.

**Some measured failures reflect evaluation boundaries.** Generation can see
edition/curation metadata absent from frozen G projections. Several C014 provenance
claims therefore fail G even though metadata supports their origin. Other C014
C failures involve required regional-growth or later-appendix coverage whose scope
is not equally obvious from the DEIR-framed question. Preserve those as interface
or reference-scope concerns, not automatic hallucination diagnoses. No judge,
reference, evidence packet or score was changed.

**Manual judgments are not a replacement gold standard.** Reviews distinguish
material source/logic errors, conclusion omissions, metadata mismatches and optional
details. C037 mitigation concerns are separate from the narrower frozen C rule.
V6b observation2 had manual scope/support/mitigation concerns despite judge passes.
V7 observation1 C041's missing no-pets support was initially underweighted manually;
the reviewer corrected that interpretation after seeing the frozen explanation.
Exact original and post-judge reviews remain separate.

### Structural failure and accounting

The first unclarified V5 attempt was stopped after invalid applies_to values were
diagnosed. It has four received responses (three invalid, one valid), one dispatched
request with unknown outcome (C037), and one undispatched case (C056). The runner
had continued after delivered validation failures; this mismatch with the initial
stop wording is recorded in the amendment. The interrupted run remains unsealed
and is never represented as a complete comparison. No answer was repaired, no
subset evaluated, and no failed attempt was retried under its old identity.

Corrected comparisons used **36 generations, 245 judgments and 281 counts**.
Including the initial attempt: **41 generation dispatches, 40 received responses,
245 judgments and 286 count attempts**, with zero retries. All 36 corrected
answers received complete evaluation and independent manual review. Known recorded
usage totals 1,212,564 input tokens including cache and 131,802 output tokens
including reasoning. The inherited-price estimate is **USD 0.175916395**, excluding
unknown interrupted usage and any counting charge. Complete corrected arms cost
approximately USD 0.022–0.037 each by that estimate; these are not invoices.

Reservations are deliberately different from actual-use estimates: USD 13.137696
for the six corrected arms plus the unreclaimed USD 0.168432 first-arm allowance,
with prior USD 30.525408, totals **USD 43.831536** under the USD 100 ceiling.
Counting retains a zero planning allowance under the user's assumption; actual
cost is unknown and OpenAI counting billing remains unverified.

### Validation and next decision

`make fix`, `make check` (**4,071 passed, one skipped**) and `git diff --check`
passed. Eleven invented offline validator fixtures verified the clarified field
rules. Five predecessor evaluations and all six new evaluations replayed without
provider construction/dispatch. All 328 protected bindings remained unchanged;
all new generation/evaluation inventories, payloads, identities and repeat requests
were checked. No production code or dependency changed in this task. The external
validation namespaces preserve source snapshots, raw responses, failures, reviews,
per-point reasons, logs, reservations and the interrupted-call uncertainty.

Keep the explicit field contract and invented examples as useful development
artifacts. Before further optimization, separately resolve public-specification,
reference-scope and metadata-projection questions; preserve existing judgments as
history. A different model, evidence rendering or multi-call pipeline would be a
new experimental condition. Do not continue adding prompt clauses without a new
bounded hypothesis. **11E remains unstarted.** No remaining-13, locked-test or
reserved-challenge content was inspected or evaluated, and Task 10 remains unchanged.
