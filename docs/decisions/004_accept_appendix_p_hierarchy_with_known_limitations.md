# Decision 004: Accept the Appendix P Hierarchy with Known Limitations

Status: accepted 2026-07-31.

## Decision

Accept the exact post-Task 03E.2a hierarchy-correction behavior for the bounded
Appendix P vertical slice and authorize its immutable publication as
`accepted_with_known_limitations`. Keep the historical Task 03E.2 development
and held-out rejection unchanged. This decision does not convert that rejection
into a strict quality pass.

The authorization is bound to candidate
`hcorv1-aab01b14c3122dbc0f5cec57147b5be2eadaf1cd895311ef7dafa46b469348b1`,
semantic SHA-256
`c3036210f5698a295ca799ee25d1850a080f0a5d211bef303b94900882cb4db8`,
the exact source and producer identity, correction policy, configuration,
schema and code bundle, frozen Task 03E.2 reject evidence, Task 03E.2a
reference, Task 03E.2b equivalence evidence, and seven checked-in limitation
categories. Its candidate-bound authorization SHA-256 is
`5335737128fcbac2b1f2d41c42712af0534e2d15141ccf1150c37ffbf70f328c`.

## Scope and limitations

The decision authorizes this evidence only as input to the Task 03E.3 semantic
contract, Task 03E.4 Appendix P materialization, and the Task 03G representative
pilot hypothesis. It retains:

- the historical development and held-out quality rejection;
- two observed false table boundaries;
- the frozen R04/R05 attribution disagreements;
- the `Existing SSF District` level disagreement;
- the accepted page-2000 R06 `content` ambiguity;
- all remaining payload ambiguities and warnings; and
- the fact that Task 03E.2a created no new held-out evaluation.

This is not a claim that the hierarchy is defect-free or accepted across the
35-document model corpus. Task 03G must test the behavior on heterogeneous
structures before Task 03H can run.

## Why

The remaining known defects are tolerable for continuing the single-document
vertical slice, while repairing them now would expand hierarchy-policy work
before the project has representative cross-document evidence. The complete
human-owned payload is byte-identical to the reviewed Task 03E.2a behavior and
retains every ambiguity and warning for downstream inspection.

Evidence and disposition remain separate. The [NIST Risk Management Framework
authorize step](https://csrc.nist.gov/Projects/risk-management/about-rmf/authorize-step)
likewise distinguishes an assessment package from an accountable acceptance
decision and its terms. Here, weakening the frozen zero-error thresholds would
hide the measured rejection. A separate content-bound authorization preserves
that evidence and makes the narrower human policy decision explicit.

## Consequences

- The existing hierarchy-correction v1 payload remains the sole correction
  evidence representation; the authorization is a control artifact, not a new
  data model.
- Publication and reuse require independent verification of either the
  unchanged strict pass or this bounded authorization.
- Downstream consumers can distinguish strict acceptance from
  `accepted_with_known_limitations` without interpreting prose.
- Task 03E.3 receives the exact completion and authorization artifacts but
  remains provisional and inactive pending user review and explicit approval.
- Decision 003 and the historical Task 03E.2 rejection remain in force.
