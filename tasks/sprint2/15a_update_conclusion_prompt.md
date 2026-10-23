# Task 15A — Apply accepted conclusion rules to a versioned prompt

Status: complete (2026-10-21). User accepted the nine-rule proposal and requested
the judge prompt update. This bounded task implements rules/prompt only; the
remaining Task 15A experiment design and later execution gates remain pending.

## Abstract and goal

Make C require the substantive explanation requested by why/how questions while
distinguishing material omissions, semantic equivalence and compatible additions
from genuine contradictions. Preserve the original selected C v8 for replay and
publish the revision as an explicit, unqualified candidate.

## Inputs and outputs

- Accepted chat draft, saved under `ER_COMMONS_DATA_ROOT` at
  `pipelines/brisbane_baylands/task_15/discussion_20261021/entry_04_proposed_c_rules.json`;
  user acceptance: “ok i accept this. now update the judge prompt”.
- `adequacy_labeling_rules.md`, historical perturbation catalog, C/S core and
  native adapter, selected judge configuration and Task 15 umbrella.
- Outputs: aligned maintained policy, versioned C prompt, explicit core version
  selection, offline preservation/parser checks, current routing and outcome.

## Plan and research / learning checkpoint

1. Inspect the existing prompt, strict schema/parser, native adapter and frozen
   identity checks before choosing the smallest compatible change.
2. Keep the existing three-field C input and strict output schema. Retain v8
   bytes/default selection; expose the new prompt through an explicit version.
   Native candidate dispatch and a new dataset selector belong to the later
   bounded execution work, not this prompt-authoring task.
3. Apply the accepted general rules without case-specific examples. Align
   comparison statuses and failure-code descriptions with the revised policy.
4. Update the maintained policy and mark conflicting historical catalog rules
   superseded for future authoring, without relabeling old records.
5. Review independently, run offline checks and record the outcome.

The primary implementation sources are the local core, adapter and selected
configuration. Existing Pydantic contracts and standard-library version selection
fit this change without a dependency or runner. A new prompt identity preserves
attribution; replacing v8 in place would invalidate the frozen configuration.

## Validation and acceptance

- Accepted rules are represented without old blanket extra-item rejection.
- Frozen C/S prompt and schema hashes still match the selected configuration;
  A/G configs and target generation remain unchanged.
- New C version is explicit, unknown/cross-component versions are rejected,
  and strict parsing/input isolation remain intact.
- Independent policy/implementation review; `make fix`, `make check`, and
  `git diff --check`. These verify mechanics, not semantic judge performance.

## Non-goals

No synthetic authoring, dataset/label edits, model calls, new execution runner,
promotion of the candidate to production, target changes, reserved challenge
inspection, MiniMax work, historical rescoring, commit or push. S/G semantics
remain unchanged, including the accepted incidental-claim coverage limitation.

## Outcome

Implemented `task15.binary_adequacy.conclusion_direct_answer.v1` as an explicit
C-only candidate in `adequacy_binary.py`. The nine accepted rules and diagnostic
instructions distinguish missing explanatory findings, compatible additions and
actual contradictions. The policy and historical catalog supersession agree;
no case-specific examples were added. S semantics and the three-field C input
are unchanged.

Frozen C v8 and S v6 prompt/schema hashes still match the selected configuration.
The native adapter/defaults remain unchanged. Existing wire fixtures now also
exercise the candidate version; unknown/cross-component versions and attempts to
use the candidate as the frozen selection fail. No schema expansion was needed:
the prompt version records the narrower meaning of `extra`/`extra_list_item`.

Two bounded independent reviews found no actionable policy or implementation
issues. `make fix` and `make check` passed: 4,412 tests passed, one skipped;
105 dependency deprecation warnings. `git diff --check` passed. These checks
establish wiring and preservation, not semantic judging quality.

The exact prompt, schema and identity manifest are saved under
`ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_15/prompt_20261021_v1/`.
The acceptance record is `discussion_20261021/entry_05_rules_accepted.json` under
the Task 15 root. This is a candidate snapshot, not the later production freeze.

Next: finish the umbrella's 15A authoring/comparison design before synthetic
generation or native candidate dispatch. Experiment budgets, run type and
semantic qualification remain separate decisions. No datasets, labels, frozen
scores, selected configurations, or target settings changed. No model calls,
reserved challenge inspection, commit or push occurred.
