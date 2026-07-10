# ER Bench Sprint 1 Specification

Status: **definition task open; no benchmark policy accepted yet**.

This file will become the concise source of truth for the Sprint 1 version of
`er_bench`. Task 01 owns turning each field below from a question into a
reviewable decision. It is intentionally narrower than broad CEQA data
discovery: its job is to define one version of one benchmark that can be built
and evaluated reproducibly.

## Required decisions

| Field | Sprint 1 decision |
| --- | --- |
| User question | To be defined from the project plan. |
| Task family | To be selected; the revision-trajectory family is a candidate, not an accepted default. |
| Source release | To be defined with owner, access date, coverage, and terms/license. |
| Evaluation unit | To be defined (for example, a linked review record or document sequence). |
| Reference policy | To be defined; identify what constitutes evidence and what must not be inferred. |
| Split policy | To be defined with explicit project, document-family, and time leakage controls. |
| Metrics | To be defined against the intended user question. |
| Baseline | To be defined using maintained open-source tools before custom code. |
| Artifacts | Manifest, dataset/version reference, split, predictions, and metrics required for a rerun. |
| Acceptance gate | The smallest result that justifies moving to an implementation sprint. |

## Scope boundary

Sprint 1 is complete when this specification has clear choices, citations to
primary source/terms documentation, and a small next implementation task. It
does not require a large corpus download, production model, or general pipeline
framework.
