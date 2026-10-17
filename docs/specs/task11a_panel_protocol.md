# Task 11A development panel protocol

Status: fixed before Luna target outputs, 2026-10-17. The
[panel manifest](task11a_development_panels_v1.json) owns exact IDs, order,
Task 10 completion/file hashes and per-record packet/mapping bindings for all 19.
This protocol is planning metadata, never target prompt content.

## Selection

| Stage | Case | Evidence and reasoning challenge | Text chars / passages / table records |
| --- | --- | --- | --- |
| Initial | C041 | Short enforcement question: distinguish construction/occupancy rules and deed/lease enforcement across two sources | 1,757 / 2 / 0 |
| Initial | C017 | Energy accounting: narrative and table, gross/net demand, renewable assumptions, uncertain storage benefits and inconsistent source wording | 6,924 / 2 / 1 |
| Initial | C019 | Conditional groundwater modeling across four documents; distinguish locations, modeled assumptions and closure approval qualifications | 19,202 / 5 / 1 |
| Expansion | C014 | Cumulative transportation scenarios, project inclusion, cross-edition evidence and many tables; two distinct approved scopes of one canonical table | 32,889 / 5 / 15 |
| Expansion | C037 | Increased wetland acreage versus temporary functional loss; reconcile table views, restoration timing and mitigation qualifications | 9,532 / 4 / 2 |
| Expansion | C056 | Numerical prose: reduced versus eliminated flooding, locations, storm severity and design conditions | 7,335 / 5 / 0 |

Text characters count full_source_text only, not serialized tables or tokens.
Table counts are embedded records, not distinct independent evidence units.
C041 and C014 are the shortest and longest development text packets respectively.
All six are fixed now; the first three are contained in the six. Select by exact
case IDs, never a positional first-N limit. Do not substitute easier cases after
failures. Changing membership requires a new explicit panel version and rationale.

Remaining broader development checks: **C001, C006, C007, C008, C027, C028,
C029, C036, C042, C045, C050, C051, C054**. These preserve health risk, noise,
lighting, traffic design, recreation, definitions, wayfinding, visual impacts
and alternatives beyond the selected six. The panel deliberately emphasizes
qualifications, including two biology and two water questions; it is not a
representative topic sample. No genuine unanswerable-case challenge is established
by this selection. Abstention handling needs separate offline integration fixtures.

Exact canonical-unit tuple intersections are zero between selected cases and
between the six and thirteen. C014 has an internal repeated canonical table with
distinct scopes. Shared source documents/topics and prior development use remain;
zero exact-unit overlap does not establish semantic or statistical independence.
No historical model/judge scores informed selection.

## Success criteria and comparison checklist

11B/11C must implement and record these checks before 11D cycles:

1. Bind manifest, Task 10 completion, selected record hashes, prompt/schema,
   implementation, provider/model revision, settings and frozen judge identities.
   Send only the complete Task 10 payload with generic prompt/schema. Verify
   rendered request context plus output reserve; no silent truncation, omitted
   tables/passages, reference answers, selection rationales or judge feedback.
2. Every attempted case remains in the denominator. Require 100% structurally
   valid answers and resolved case-local citations for a promotable candidate.
   Check required supporting-point/qualification/conclusion fields against the
   runner's versioned schema. Missing evidence, malformed/truncated output,
   transport/context errors and unresolved citations are explicit failures, never
   negative semantic scores or silent exclusions. Structural validity alone is
   not semantic success. Retrieval recall is not applicable.
3. Report frozen A/G/S/C separately per exact candidate. A inspects the original
   conclusion; apply the separate empty-other-prose guard before any clean
   abstention route. G checks each point/factual qualification against its own
   complete cited evidence. S sees original premises, never G-filtered prose;
   C sees the original conclusion and its permitted reference. Report each G
   item, skipped components with reasons, errors and applicable denominators.
   Do not silently interpret missing judgments as passes. 11C owns routing;
   Task 12 owns final strict combined reporting. Do not retune judges here.
4. Manually inspect every candidate in each paired panel run against its packet:
   direct answer, useful reasoning, supported citations, scope/time/unit fidelity,
   material qualifications, and no invented guarantees. Mark each case
   acceptable / material defect / unresolved, with source-linked reasons.
   Review apparent judge/manual disagreements; do not overwrite frozen verdicts.
   Feedback can inform a generic next prompt, never a case-specific answer hint
   or automatic repair of the judged candidate.
5. Promotion target: all panel cases satisfy structural gates, have complete
   applicable evaluation without errors, and are manually acceptable. For
   substantive answers aim for grounded items and affirmative S/C, while treating
   abstention classification separately from correctness. Unresolved material
   disagreement blocks an unqualified success claim. A bounded run may finish
   with documented limitations rather than meet this aspirational quality gate.
6. Compare incumbent/challenger on the identical panel and settings with exact
   candidate joins. Keep a per-case checklist of fixes, regressions, schema and
   citation failures, A/G/S/C, manual findings, tokens/cost/latency. Accept a
   challenger only with a documented material improvement and no new material
   defect on any paired case; ties retain the incumbent. Do not select using a
   single aggregate score. Freeze the selection rationale even when no arm wins.

## Proposed bounded budgets for later contracts

These are proposals, not live-run authorization or measured price estimates.
11B/11C must establish actual request/context behavior and judge fan-out; 11D
must record final caps and dated provider prices before dispatch. The sprint's
three working days remain a planning target; report overruns rather than extend
calls implicitly.

| Phase | Maximum planned target outputs | Primary judge-call envelope |
| --- | --- | --- |
| Initial three | Baseline plus at most two generic prompt revisions: 3 × 3 = 9 | 108 |
| Fixed six | Incumbent plus at most one revision: 2 × 6 = 12 | 144 |
| Stability check | One repeat of selected prompt on six: 6 | 72 |
| Total 11D | 27 | 324 |
| Separate 11E proposal | One frozen pass on all 19: 19 | 228 |

The envelope budgets A/S/C once each plus up to nine G items per answer:
12 primary judge calls per target output. This is a capacity assumption, not an
answer-length rule or permission to drop grounding checks. If actual fan-out
exceeds it, pause before dispatch and revise the prospective budget explicitly;
never omit or truncate candidate items to fit. Reuse exact saved candidates and
judgments when identities match, recording reuse separately from calls. All-19
may reuse the six only if the final frozen configuration and candidate identities
match, and must report which results are reused.

Propose at most one transport retry per primary call, no semantic rerolls. Count
failed attempts, probes and retries against ceilings: 11D **54 target + 648 judge
attempts = 702 total**, 11E **38 + 456 = 494 total**. Any live smoke/probe in
11B/11C requires its own predeclared budget and cannot silently consume or enlarge
these allocations. Proposed spending ceilings: **USD 100 for 11D**, **USD 75 for
11E**, inclusive of retries/probes within their scopes. These are stop limits,
not forecasts. Preflight conservative input/output cost including reasoning and
fan-out; reserve in-flight liability before dispatch. Native soft per-sample cost
limits alone do not enforce these totals. If prices/usage are unavailable, do not
assume zero cost; settle the accounting boundary before runs.

Stop on the first exhausted call/cost/timebox boundary, context/integrity failure,
or two successive revisions without material improvement. Finish earlier when
the quality gate and stability check hold. Instability is reported, not repaired
by repeated sampling. A budget increase requires an explicit revised contract.
Freeze the prompt before inspecting 11E outputs. Report six and thirteen separately;
a failure on the thirteen is diagnostic, not permission to resume tuning within
11E. A later tuning task would expose those cases and require a new freeze/check.

## Research and learning

Reviewed 2026-10-17: [Inspect datasets](https://inspect.aisi.org.uk/datasets.html)
documents explicit sample IDs, ID-based filtering and separate input/target/metadata
fields. Reuse those boundaries; IDs and reference metadata need not enter model
messages. A fixed nested panel keeps the original cases visible when difficulty
expands, making regressions interpretable. Repeated selection on all six makes
their apparent performance optimistic; the remaining thirteen are broader
**development checks**, not independent held-out estimates. The locked 30 test
cases remain untouched for later authorized evaluation.
