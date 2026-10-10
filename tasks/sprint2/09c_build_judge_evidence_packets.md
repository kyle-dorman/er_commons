# Task 09C — Build judge evidence packets and validation

Status: complete with limitations; authorized October 10, 2026. Refreshed from committed 09A
(`eee4edc`) and 09B (`c2dba5f`). No inference or benchmark mutation is authorized.

## Abstract

Build deterministic, source-bound inputs for two independent judges. Preserve
the exact evidence needed to assess an answer while preventing reference and
synthetic-label leakage. The [Task 09 umbrella](09_build_evaluation_and_qualify_judges.md)
owns sequence; this task owns packet construction, not judgment.

## Goal

Produce inspectable grounding and adequacy packets from saved structured answers
and the frozen corpus, with explicit citation-resolution and context diagnostics.

## Inputs

- [08H release](../../docs/specs/task08h_final_result.json), development membership,
  target-only questions, curator references, source identities and completion seal.
- Accepted [09A](09a_create_synthetic_challenges.md) variant schema and
  [09B](09b_choose_harness_and_qualify_local_judge.md) transport/context limits.
- [Decision 006](../../docs/decisions/006_structured_answers_four_part_evaluation.md),
  [sprint evaluation boundary](../../docs/sprints/sprint2_brisbane_draft_eir_defense.md#benchmark-evaluation-boundary),
  [architecture](../../docs/architecture.md), and [artifact rules](../../docs/data_artifacts.md).

## Outputs

- Versioned packet schemas and narrow, typed package-backed builders/resolvers.
- Separate grounding and adequacy packets with exact source locators, point links,
  input hashes, citation-resolution status and context-size diagnostics.
- External manifest binding input answer/version, case, release, source inventory,
  packet policy and deterministic outputs; no rewrite of frozen source artifacts.
- Fixtures demonstrating information separation, invalid-citation handling,
  complete table context and explicit overflow behavior.

## Research / learning checkpoint

Inspect the maintained source-unit/citation assembly interfaces before inventing
another resolver. Use Decision 006 and the frozen release schemas as authorities.
Review [Inspect custom scorers](https://inspect.aisi.org.uk/scorers.html) if 09B
selects Inspect, and the accepted runtime's context controls. Explain why supplying
the wrong or incomplete passage can look like judge failure, and why declared
metadata separation is insufficient unless the serialized request is checked.

## Plan / spec requirement

Write a brief packet specification and boundary table before implementation:

| Input | Grounding | Adequacy |
| --- | --- | --- |
| Exact scoped question and candidate answer, including point links | Include | Include |
| Actual candidate-cited passages and unresolved-citation markers | Include | Include |
| Approved structured reference and reviewed evidence pool | Exclude | Include |
| Gold support/context classifications | Exclude | Only as required by the adequacy contract |
| Synthetic expected scores, edit/failure labels and generator rationale | Exclude | Exclude |
| Automatic matching scores and target/generator identity | Exclude | Exclude |
| Official-response claims as evidence | Exclude | Exclude |

1. Verify the exact frozen release and development allowlist before loading cases;
   reject held-out cases in development preparation. Keep expected-score records
   in a separate analysis channel rather than passing whole variant records.
2. Resolve declared citation IDs to the frozen canonical section/table identities.
   Preserve point-to-citation links and invalid raw tokens. Never replace a wrong
   citation with the source the answer should have used, or augment grounding
   from the reference's evidence pool.
3. Reuse accepted unit assembly for headings, source order, table continuations,
   captions, units and notes. Bind added context to its source and record why it
   is included; do not silently expand grounding to uncited evidence. Preserve
   inherited text-only figure and extraction limits.
4. Build two independent allowlisted payloads, not a shared conversation with
   references progressively exposed. Shared transport is allowed; hidden fields
   must not appear in prompt text, metadata visible to the model or chat history.
5. Preflight complete request length with the selected model/output reserve.
   Oversized packets receive an explicit non-score status and diagnostic. Do not
   silently truncate, summarize, omit qualifications or claim unsupported context
   fits. Any alternative context policy requires an explicit recorded revision.
6. Treat answer/source text as untrusted quoted content. Preserve adversarial
   content for robustness tests without promoting it to judge instructions.

## Refreshed MVP specification

Reuse sealed 09A case inputs, whose full source text and table records already
come from the maintained citation assembly interfaces. Do not add a second
corpus resolver or rerun extraction. The development loader verifies the frozen
release/split and reservation before decoding only explicitly selected records;
423 development variants, 118 reserved final checks and five exclusions remain
unchanged. Bounded controls and variants can be published without any model call.

The versioned packet envelope keeps `payload` separate from diagnostics and raw
ID mappings. Only the allowlisted payload is model-visible. Grounding includes
candidate-cited source units only; adequacy adds the approved reference and the
reviewed pool. Complete canonical text, table cells, geometry relevant to grid
interpretation, captions, continuation links and source locators are preserved;
review provenance and evidence roles are excluded from both model payloads.
Unknown citation tokens are retained in the external mapping and shown as neutral
unresolved IDs in model inputs, avoiding category-bearing synthetic IDs. Known
sources with missing content are infrastructure errors, never unknown citations.
No citation repair, heuristic matching, text cleaning or semantic scoring occurs.

09B establishes a 49,152-token allocation and 1,500-token output reserve. Packet
construction records serialized size but cannot certify final request tokens
before 09E/09F define prompts. A reusable request preflight must include messages,
chat-template overhead and any model-visible output schema; absent an exact
model-bound counter, return `context_unverified`, never claim a fit. Explicit
`context_overflow` blocks dispatch without changing content. Existing native
Ollama no-truncation/no-shift guards and post-call token verification remain.
No tokenizer/model downloads or live inference are needed for this task.

The model roles remain Qwen3.5 0.8B for fast integration checks only, Qwen3.5 9B
for the first accuracy evaluation, and Ornith set aside. No 09D–09G work starts.
Use existing Pydantic/JSON tools and plain Python functions, a small publisher,
and a compact external manifest; no new dependency, framework or provenance DAG.

Research: [Inspect scorers](https://inspect.aisi.org.uk/scorers.html) separates
sample inputs from scoring; [Ollama chat API](https://docs.ollama.com/api/chat)
reports `prompt_eval_count` after inference. Neither makes a packet character
count an exact preflight token count. Keep content projection independent of
future scoring, and fail closed when a full request count is unavailable.

## Validation

Check exact serialized payloads for forbidden sentinel strings, including
expectations nested in provenance. Cover reordered/split points, joint citations,
real irrelevant sources, repeated/unknown IDs, verified alternative evidence,
table notes, abstentions with assertions and context overflow. Verify deterministic
hashes and unchanged upstream artifacts. Run `make fix`, `make check` and
`git diff --check` for implementation/documentation changes.

## Acceptance criteria

- Packets preserve actual evidence and citation relationships without repairing
  candidate answers or exposing synthetic expectations to either judge.
- Grounding cannot access the reference or gold roles; adequacy can evaluate
  alternative arguments using actual cited passages.
- Missing required source files, forbidden inputs and oversized packets are
  explicit infrastructure/input failures, distinct from rubric scores. An answer
  deliberately citing an unknown ID is instead a valid challenge packet with an
  unresolved-citation marker; it must reach semantic assessment without repair.
  Schema diagnostics do not become a fifth semantic metric.
- Future 09E/09F tasks can consume these packets independently through 09B.

## Review pass

Review information boundaries and citation/table completeness separately; integrate
findings before accepting the packet specification and implementations.

## Non-goals

No judge prompts/scoring, reference relabeling, source repair, new retrieval
condition, model-generated source summaries, target runs or test-case development.

## Outcome

Implementation and bounded offline qualification are complete. The
[09C result](../../docs/specs/task09c_final_result.json) binds the external evidence.
Separate deterministic packets preserve actual citations and complete assembled
source units while excluding synthetic/review metadata. No judge prompt, scorer,
model call or benchmark evaluation was added or run.

### Implementation and usage

- `judge_packets.py`: pure builders, explicit unresolved entries, strict nested
  payload schemas, exact text/table projection and anonymous point/citation links.
  `payload_schema("grounding" | "adequacy")` exports the corresponding schema;
  `task09c.judge_packet.v1` identifies the envelope. Only `payload` is model-visible.
- `judge_packet_publication.py`: explicit development selection, sealed input and
  corpus checks, metadata-first row routing and ordinary no-clobber JSON outputs.
  Raw invalid citation tokens remain in mappings for audit, never repaired or
  displayed as category-bearing IDs. Eligibility records never enter payloads.
- `judge_packet_requests.py`: plain Inspect samples and complete native Ollama
  request preflight, reusing 09B transport assembly. It defines no prompt/scorer.
  The old qualification runner explicitly refuses 09C packets to prevent bypassing
  the context gate or accidentally using prototype rubrics.

Example offline preparation (choose a fresh external output directory):

```bash
make prepare-judge-packets \
  JUDGE_PACKETS="$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_09/09c_example/packets" \
  JUDGE_SELECTIONS='--control-case C041'
```

Use `--variant-id <development-id>` for an explicit development variant.
No default all-variant build or inference dispatch exists. The publisher emits
`packets.json`, `provenance.json` and `completion.json`. A later Inspect task uses
`inspect_sample` for input and must call `prepare_request` with its own prompt,
response schema and exact model/template-aware counter before dispatch.
`dispatch_allowed` is false for missing counts or overflow. Request hashes bind
the complete messages/schema/model/options; no heuristic claims a fit.

### Bounded evidence and validation

The external namespace is `task_09/09c_20261010_v1/`. Offline publication built
**12 packets** from C014/C037/C041 controls and three development variants:
C041 wrong-real citation, C041 invalid citation and C014 table claim perturbation.
The invalid citation remains explicitly unresolved; no evidence was substituted.
This is a serialization check, not a broad challenge or accuracy evaluation.
Identical publication was repeated successfully without changing output bytes.

Deterministic fixtures cover serialized sentinel exclusion through nested table
cells, point reordering/splitting, aliases, joint/repeated citations, qualifications,
alternative/irrelevant real sources, locator-only unknowns, abstention assertions,
table cells/spans/headers/continuations/notes, missing-source failures, sealed
membership and byte corruption, exact context boundaries, overflow and missing
counts. Reserved answer and test-content fixtures are deliberately undecodable.

- `make fix`: passed; formatting, lint and type checks passed.
- Focused 09B/09C regression set: **95 passed**, including **46 new tests**.
- `make check`: **3,508 passed, one skipped, three historical Task 06G failures**.
  The failures are the two v38 immutability checks and the source-free template
  check, all encountering the pre-existing historical repository-commit mismatch.
  Relevant tests, recipes and implementations match `c2dba5f`; no new failures.
  Full output is bound by the result pointer.
- `git diff --check`: passed. Independent boundary/citation/table and MVP review
  accepted the changes after fixing the optional-null schema inconsistency and
  checking the prototype-runner guard.
- Bounded live-data projection audit: exact full text and all table cells match
  selected sealed inputs; payload hashes and Inspect sample round-trips match;
  two packets explicitly retain unknown citations. Payloads range from 3,722 to
  118,466 UTF-8 bytes; these are not token counts. Upstream 08H/09A/09B completion
  bindings and deterministic repeated publication were verified unchanged.

### Learning, limitations and next step

The complete assembled source is the authority, not the candidate's excerpt or
what the reference should have cited. Reusing the existing sealed assembly avoids
another resolver with subtly different table/qualification boundaries. Nested
allowlists and validation at serialization matter because filtering top-level
metadata alone still permits review labels inside cells or locators.

Inspect provides input/scoring separation; it does not make packet character
length an exact token count ([Inspect documentation](https://inspect.aisi.org.uk/scorers.html)).
Ollama's `prompt_eval_count` is post-inference evidence
([native chat API](https://docs.ollama.com/api/chat)); it does not supply an offline
preflight here. No exact production tokenizer integration was installed in 09C.
All published packets therefore say `context_unverified`. The final consuming
judge must provide a pinned model/template counter, including chat framing and
model-visible schema, before dispatch. Fixture counts verify the gate itself;
they are not measurements of live packet token lengths.

The source policy inherits upstream extraction/text-only figure limits and
review coverage; no new semantic source verification or visual interpretation
occurred. The public pure builder expects a verified complete occurrence inventory;
its development publisher enforces that contract. A future saved-target loader
must use the same maintained corpus assembly boundary for newly cited sources.
No general corpus lookup is claimed for this bounded 09A integration.

Qwen3.5 0.8B remains integration-only; 9B is the first accuracy-evaluation
candidate; Ornith remains set aside. The frozen 19/30 split and 423/118/5
populations are unchanged. No reserved answer payloads or test questions/references
were parsed, no target generation or test evaluation ran, and no model downloads,
paid inference or external source dispatch occurred. No commits or pushes.
09D is next for a separately authorized contract refresh; 09D–09G remain unstarted.

## Authorized code-quality pass

The user requested a pass beyond the initial MVP while keeping this below
production-system scope. Improve concrete correctness, readability and tests in
the existing packet modules. Priorities are consistent validation before data
traversal, clear publication stages, safe repeat/partial-publication behavior,
and request-boundary consistency. Preserve valid model-input bytes, sealed
external evidence and the frozen populations. No new dependency, framework,
model call, reserved/test payload access, prompt/scorer or later task is included.
Validate with targeted fixtures, independent review, `make fix`, `make check`
and `git diff --check`; record the final tradeoffs and checks here.

### Code-quality outcome

The pass keeps the existing three-module design and strengthens its boundaries.
Raw substantive answer types are now validated before citation iteration and ID
anonymization. Previously, a malformed string citation list could become multiple
unknown citations, and numeric IDs could become valid-looking neutral IDs.
Malformed answers now raise `PacketInputError`; malformed known source units raise
`SourceUnavailableError` with the source locator and original cause. Optional
absent source locators remain supported. Serialization also rejects uncited
extra evidence in grounding payloads, and request/sample adapters reject changed
payloads whose saved hash no longer matches.

The publisher now has named release, selected-record and case-validation helpers.
It computes and checks all three output files before writing, rejecting conflicting
or unrelated contents while allowing exact partial resumes. This avoids a known
conflict leaving new files behind; it does not add a database, concurrent-writer
locks or multi-file transactions. Valid model input and publication bytes remain
unchanged, verified by repeating the exact original 12-packet selection.

Independent review accepted correctness and maintainability. The added fixtures
exercise malformed raw answers/references, source context errors, changed payloads,
uncited grounding evidence, output conflicts and partial resumes. Exact production
token counting remains a future consuming-judge responsibility; this pass does
not relax that gate or run inference.

Quality-pass validation: **122 focused tests passed**, including **27 added
regressions**. `make fix` passed. `make check` reports **3,535 passed, one skipped,
and the same three historical Task 06G failures**; formatting, lint and types
passed. Relevant historical tests/recipes/code remain unchanged from `c2dba5f`.
`git diff --check` passed. The [result pointer](../../docs/specs/task09c_final_result.json)
binds the separate `09c_20261010_code_quality_v1/summary.json` and logs, preserving
the original qualification evidence. No new dependencies, model calls, reserved/test
content access, later tasks, commits or pushes. 09C remains closed with its
previous context-counting limitation; 09D is next when separately authorized.


## Closeout acceptance

The user accepted the completed task and code-quality pass and authorized a
local commit of the 09C implementation, tests and documentation. Earlier
no-commit statements describe execution before this closeout authorization.
Task 09C is done with the documented context-counting limitation. Task 09D
remains provisional and unstarted; explaining its scope does not activate it.
No push is authorized.
