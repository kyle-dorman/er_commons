# Task 08D combined claim preparation v1

Model: `gpt-6-astra`. Input: only the source-bound Task08D packet for the
explicitly authorized cases. Never read historical case claims, human labels,
reference answers, evidence decisions, or ranking explanations. General procedural
learning is allowed. Frozen question text, hashes and provenance must not change.
An assertion extracted or approved here is what the official response asserts;
its truth and evidence support remain unestablished.

## Pass 1: inventory before relevance

Read each complete linked official-response closure, including supplements,
supplied citations, source warnings and attribution. Save `inventory.json`
(`task08d.inventory.v1`) before making relevance proposals. For each case retain
`case_id`, `assertions` and `passage_coverage`. Assertions have stable
`assertion_id`, concrete `text`, and nonempty `passage_ids`. Coverage accounts for
every response passage: `passage_id`, `assertion_ids`, and `note` explaining any
non-substantive material. Inventory substantive assertions regardless of relevance;
combine incidental details within a substantive assertion instead of creating
fact fragments. Do not discard unrelated assertions.

Write [subject] [specific assertion], with only source-supported conditions,
quantities, time, place and comparison. Preserve material attribution, uncertainty,
negation, conditions and qualifications in the claim itself. Split independently
assessable conclusions when their decisions could differ, while retaining reasons
needed to interpret the conclusion. Do not turn a supplied citation into evidence
support, or an official response into an independently verified fact.

## Pass 2: relationships after inventory is saved

Save `proposal.json` (`task08d.proposal.v1`) with `model`, `packet_sha256`,
`inventory_sha256`, and `cases`. Each case contains `case_id`, `claims`, and
`question_parts`. Every inventoried assertion must map to at least one claim;
merges are allowed with explicit `assertion_ids`. No silently omitted assertions.
Claims use stable A001-style `claim_id`, concrete `text`, `passage_ids`,
`assertion_ids`, `relationship`, `targets`, and `rationale`.

- `direct`: addresses a specific part of the frozen question itself. `targets`
  contains the corresponding P001-style question-part IDs; rationale identifies
  exactly what is addressed and any limits.
- `supporting`: materially supports one specific direct or supporting claim. `targets` contains
  exactly that claim's ID. Rationale explains the contribution and why removing it
  would weaken the reasoning. Topic overlap, incidental facts and generic context
  do not suffice. Supporting chains must be acyclic and terminate at a direct claim; name the immediate target, not merely a shared topic.
- `not-relevant`: retain the assertion for coverage, with empty targets and a
  short reason it does not materially address this question.
- `unclear`: preserve uncertainty, empty targets and explain the obstacle.

Present direct first, then supporting in dependency order, then not-relevant and unclear. IDs remain
stable across display order. Exact response passages and supplied citations are
separate provenance beneath readable assertions, never replacements for wording.

`question_parts` preserves the entire question's scope; it does not rewrite or
replace the frozen question. Each part has `part_id`, `text`, `claim_ids`,
`status` (`addressed`, `unanswered`, `unclear`), `essential` boolean and
`explanation`. Explicitly record every unanswered or partly answered request and
material qualification. Do not treat a nearby topic as an answer, silently narrow
scope, infer adoption/rejection from absence, decide final eligibility, search for
evidence, or draft an answer. Proposal relationships and coverage are advisory.

All proposal inputs and outputs receive hashes. Claims retain exact source spans
through passage IDs whose text/offsets are checked against pinned source units.
No human decisions or approval fields are generated.

## Invocation and preparation boundary

Process one source-only case packet at a time in saved case order. Save the exact
packet and this prompt as invocation inputs, then save the first-pass inventory
before authoring relationships. Record actual worker/model identity, input/output
hashes and invocation mode; never substitute a configured model name for actual
provenance. All outputs are proposals awaiting independent and human review.
No practice decisions, human approvals or historical claim text transfer.
