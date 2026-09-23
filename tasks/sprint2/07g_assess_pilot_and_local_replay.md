# Task 07G: Assess Pilot and Compare Local Proposals

Status: **Provisional draft; revise after 07F.**

## Abstract and goal

Summarize what the five authoring reviews and screening stage taught us, then
test whether a local or otherwise no-extra-cost model can make comparably
useful proposals. This is authoring-workflow assessment, not an LLM judge or
the benchmark target evaluation. Follow the
[Task 07 umbrella](07_pilot_reference_case_authoring.md).

## Inputs and outputs

- Input: sealed stage inputs, Codex proposals, curator edits, review time or
  effort observations, unresolved cases, and final pilot defenses.
- Run a bounded local-model replay (initial candidate `gpt-oss:20b`) on the
  **same pre-review inputs** for representative cases and stages. Record the
  exact model digest, settings, prompts, resources, and failures. Never expose
  the approved answer as an input to the proposal being compared.
- Output: human-reviewed comparison of proposal completeness, factual errors,
  evidence-ID validity, needed edits, and runtime; attrition and source-search
  summary; recommended forms, prompts, and criteria for Task 08.

## Research / learning checkpoint and plan

Review reproducible local-inference guidance and the project's model/resource
contract before running. Define comparison criteria and a representative
sample before inspecting local outputs. If a free alternative is chosen over
`gpt-oss:20b`, record why and pin it. Keep the second pass bounded to the
available machine and existing model files where possible.

## Validation, review, and acceptance

Verify identical input identities, no approved-output leakage, complete model
metadata, and traceable human comparison notes. State where evidence discovery
failed versus where proposal quality failed. Accept when the pilot report
explains screening yield, reviewed-defense yield, correction effort, unresolved
claims, search contribution, and whether local proposals merit future use.
Do not promote local outputs automatically, use an LLM judge, or reinterpret
Task 07 pilot-fit ratings as Task 08 eligibility.
