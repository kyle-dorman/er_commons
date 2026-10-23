# Task15Z — Review citations for required conclusion content versus context

Status: Complete and user-accepted on 2026-10-23.
The [acceptance record](../../docs/specs/task15z_acceptance.json) binds the approved
audit, retrieval mapping and contract after independent semantic/code review.
The [publication pointer](../../docs/specs/task15z_retrieval_mapping_result.json)
selects the curator-only sidecar: required evidence, optional/context, verified
alternative routes and jointly sufficient sets. Task15AC remains unchanged.
The prior citation audit is preserved. The user authorized a local closeout commit;
no push or further run is authorized.

## Abstract and goal

Review the reference citation mappings against the approved required/optional
conclusion points. Distinguish evidence directly supporting required answer
content from evidence supplying optional detail, explanation or context. The
user suspects many citations are contextual relative to required conclusions;
treat this as a hypothesis to audit, not a predetermined relabeling outcome.

This is follow-up2 of3, after15Y and before
[15AD final end-to-end run](15ad_final_end_to_end_run.md).

## Inputs

- Structured references and citation anchors selected by
  `docs/specs/task15ac_reference_result.json` (all49 questions).
- Source-bound review packets and support-point citations via the Task15F/15L
  pointers; retain source editions, exact excerpts and table context.
- `docs/specs/adequacy_labeling_rules.md`, especially citation-role semantics;
  `docs/data_artifacts.md` and the existing reference publication contract.
- Task15AA decisions are published: C017 storage is optional; C014 VMT content
  is removed from the conclusion reference.15AC includes provenance-only anchor
  repairs for C014/C032/C011/C052; these do not settle the wider citation-role audit.


## Outputs and plan

Prepare an evidence-first review of all49 reference cases without reading model
predictions to choose edits. For each citation, map the particular source passage
or table row to the required and/or optional points it actually supports. Classify
its relation as direct required-content support, optional-detail/context support,
mixed, or unresolved, with short rationale and exact evidence anchors. These are
review classifications, not automatic changes to runtime citation-role enums.

A source can support both required and optional content; a citation may support
only one clause of a point or work jointly with other citations. Do not force
whole documents into mutually exclusive roles. Optional explanation can have
real evidentiary value; not required by C does not mean irrelevant, unsupported,
or removable from the evidence supplied to a target model.

Identify mismatched anchors, excessive citation bundles and contextual details
embedded in required points. Propose per-case mapping cleanup and separately flag
required/optional policy changes for user adjudication. Preserve existing support
points as labeling provenance. Show question, reference point, source passage,
proposed change and uncertainty for each decision. Do not silently prune citations,
source packets, support points or required meaning to match predictions.

After user review, publish only accepted changes in a fresh version if authorized.
Record downstream impact on synthetic expectations, C qualification, Task15Y
coverage diagnostics and later evaluations; do not regenerate or rerun them
implicitly. Task15Y may use the current frozen references independently, but must
identify that version and not mix results across any later accepted cleanup.

## Research / learning checkpoint

Inspect the existing citation policy and source anchoring/provenance contracts.
Explain the distinction between a citation's role relative to required conclusion
content and its role in grounding a supporting or optional claim. Check primary
annotation/provenance guidance where it helps settle the mapping convention;
record the rationale before adopting a new schema.

## Validation, review and acceptance

- All49 cases accounted for; exact citation IDs, editions and source anchors
  verified, with unresolved mappings retained rather than guessed.
- Required meaning remains supported, including qualifications and how/why
  mechanisms; joint and mixed-purpose citations remain representable.
- Independent bounded review checks the proposed classifications against evidence,
  not agreement with predictions. User adjudicates proposed materiality changes.
- Save proposals/decisions externally in a fresh Task15 namespace and link a
  compact result pointer. Preserve frozen releases and exposure disclosures.
- Inspect documentation diffs and run `git diff --check`; any later implementation
  or publication work gets appropriate additional checks.

## Non-goals

No label edits, replacement of Task15AC, synthetic generation, paid model calls or
downstream rescoring. The retrieval-facing sidecar publication is authorized. No assumption that most citations must become
context. No target evidence removal, source research expansion, MiniMax, reserved
challenges or pushes. The local closeout commit is authorized. Task16 requires
separate activation.


## Initial citation-audit outcome

The evidence-first audit and independent cross-review covered all 49 cases,
125 required points, 211 optional points and 236 citation occurrences. No new
ambiguities or proposed required/optional meaning changes require adjudication;
no reference citation corrections are necessary. Retain Task15AC without a new
successor release. Acceptance was recorded at final closeout below.

The [result pointer](../../docs/specs/task15z_citation_audit_result.json) selects a
sealed external review with per-citation classifications, all-case independent
review, exact source provenance and a concise review summary. The reconciled
classifications are 36 direct-required, 131 mixed and 69 optional-detail/context.
Two internal audit mappings were refined during independent review; neither
requires changing the existing reference citation lists. Existing source
inconsistencies remain disclosed rather than silently repaired.

Learning: citation role is relative to a particular claim, not an entire document.
A passage can jointly support required meaning and optional detail; optional
support is not automatically runtime context-only metadata. Existing IDs and
exact anchors suffice; no new runtime schema or dependency is needed. The external
methods note records the W3C Web Annotation Data Model's segment/selector guidance
(https://www.w3.org/TR/annotation-model/) and how it informs provenance checks.

Validation verified all 132 frozen release files, all 481 exact anchors (including
the approved research supplement), all case/citation/point identities and
independent review coverage of all 49 cases. Documentation passes `git diff --check`.
Frozen releases/results, synthetics, judges and scores remain unchanged. No paid
calls, reserved challenges, MiniMax, commit or push. After acceptance, separately
activate Task15AD and agree its settings/budget; this audit grants no execution
allowance.


## Retrieval mapping publication outcome

The user clarified that15Z should publish retrieval relationships now, ahead of
search-agent implementation, and explicitly authorized this sidecar plus independent
review. The [contract](../../docs/specs/task15z_retrieval_mapping_v1.md) defines OR
between sufficient sets and AND within each set. All required points need evidence;
optional/context evidence never becomes an added completeness requirement.

Published all49 cases,125 required and211 optional points, and236 citation
occurrences. There are207 required sufficient sets, including28 joint sets;
49 required points have alternatives. Optional points have297 sets,18 joint sets
and58 points with alternatives. Citation roles are36 direct-required,132 mixed
and68 optional/context. C054-S006 is newly recognized as mixed because its
Alternative5 feasibility paragraph also supports R2's land-use mix jointly.
No required/optional point meaning changed and no prior required citation was
demoted. The previous audit's69-context count remains preserved in its own seal.

Independent cross-review covered every case and all336 points. Four evidence-route
refinements removed unsupported alternatives, avoided unnecessary joint requirements
and preserved genuinely complementary support. No unresolved decisions remain.
Independent code review and six malformed-input controls checked the bounded
publication builder. Exact source/input hashes, point text, citation catalogs,
review hashes and the70-file completion inventory were verified.

The sidecar is curator-only and must not enter evaluated search-agent inputs.
Unlisted evidence remains unjudged; a document hit does not prove passage coverage.
The known evidence routes are not an exhaustive corpus relevance judgment. No
retrieval implementation, metric, paid call, synthetic/judge change or rescoring
was performed. Task15AD remains separately activated/budgeted; its evidence-only
baseline does not acquire a retrieval requirement from this publication.


## Final acceptance

The user approved the completed task and instructed closing and committing it.
Task15Z is complete: the audit, retrieval-facing sidecar, independent reviews and
validation are accepted. The acceptance record supersedes historical pending or
no-commit metadata without rewriting sealed artifacts or their result pointers.
Closeout verifies artifact hashes and documentation diffs. Task15AD is next and
remains separately activated and budgeted. No push is authorized.
