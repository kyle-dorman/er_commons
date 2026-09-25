# Task 07D: Discover and Review Evidence

Status: **Provisional; input scope updated after 07C.1. Discovery plan and trial not started.**

## Abstract and goal

Find candidate Draft EIR evidence for each reviewed response assertion and
review its actual support in a separate Label Studio project. Search may fan
out by assertion and source, but the curator receives one coherent evidence
packet per case. Follow the [Task 07 umbrella](07_pilot_reference_case_authoring.md).

## Inputs and outputs

- Input: the [07C.1 replacement handoff](07c1_review_claims_and_relevance.md#final-reviewed-export-and-replacement-handoff),
  approved questions/claims, response-explicit references, accepted
  canonical extraction and usability records, and source limitations.
- Build reproducible candidate discovery from explicit references and lexical
  search across usable Draft EIR content. Test accepted cross-reference hops
  where gaps justify them; record search paths and limits. Curator search is
  separate from the later target-model retriever.
- Codex may propose matches only from supplied candidate IDs. The Label Studio
  project shows source text and exact anchors and records direct support,
  context only, contradiction, insufficient/absent support, or unusable source
  for each material assertion.
- Output: reviewed evidence records with semantic source unit, exact canonical
  anchors, discovery provenance, and links to the supported assertion; plus
  explicit unresolved gaps.

## Research / learning checkpoint and plan

Review accepted source and cross-reference contracts, Label Studio rendering
options, and retrieval practice. Choose one of the six approved cases for the first interface trial after
inspecting its reviewed claims and explicit references. Explain the difference
between finding a relevant passage and verifying that it entails the assertion.
Add search expansion only when the initial candidates miss useful evidence.

## Validation, review, and acceptance

Mechanically resolve every proposed ID and anchor, retain direct/context
distinctions, and sample-check displayed text against canonical records and
review renders as needed. The curator decides support. Accept when every
material assertion has reviewed evidence or an explicit gap. Do not convert a
response-authored claim into a fact, use Final EIR text as target evidence,
or hide unsupported assertions in later prose.

## Reviewed input boundary

Use the [accepted result binding](../../docs/specs/task07c1_final_result.json)
to pin `07c1/reviews/seven_case_export_20260925T211401Z/` under the Task 07 pilot
artifact root and verify its manifest before use. This supersedes original 07C
assertions for this task, while retaining that predecessor unchanged.

The six approved cases are O-Joint-19, O-GGBA-2, M-OSEC-273, SA-Caltrans-33,
PC-LM-2 and I-CF-4. Their normalized `evidence_candidate_claim_ids` select 31
stable claim identities. Preserve exact reviewed wording, source references,
concern links and supporting graph; do not reconstruct the queue from slot order
or label counts. I-EA-2 is a case-level Unclear stop and contributes no candidates.
I-CJ-4 remains excluded. Not-relevant claims remain in the review export but are
outside discovery. Relevance does not establish evidentiary support or adequacy.

Before execution, refine this provisional contract with a brief discovery plan,
source/retrieval research, versioned evidence records, a one-case UI prototype and
validation/acceptance gates. This scope update starts no searches or model runs.
