# Task 03E.2a: Reset Hierarchy at Nested-Regime Exit

Status: **closed on 2026-07-31 as the completed MVP/reference correction;
superseded for production ownership by Task 03E.2b**.

## Abstract

Fix the general hierarchy-stack lifecycle defect exposed by Appendix E in the
rejected Task 03E.2 candidate. The numbering-regime builder correctly ends the
embedded Appendix D Article regime at the peer Appendix E outline boundary,
but hierarchy construction resumes a stale outer-regime stack and assigns
Appendix E beneath Appendix D's embedded agreement title.

Implement a regime-evidence-driven reset at the declared end item of a nested
regime. Do not add an Appendix E literal, change heading classification, revise
the sealed held-out annotations, or claim a new held-out evaluation.

## Goal

When a nested regime ends at a peer outline boundary, construct that boundary
without any stale parent retained from the enclosing regime while preserving
ordinary per-regime hierarchy behavior elsewhere.

## Inputs

- completed, rejected Task 03E.2 implementation and report evidence
- `regimes.jsonl`, particularly `parent_regime_id` and `end_item_key`
- the hierarchy builder and its independent cross-record reconstruction
- the verified Appendix P producer used by Task 03E.2

## Outputs

- a general nested-regime exit reset in both hierarchy construction and
  independent validation
- focused unit coverage for stale outer-stack state
- a source-bound regression proving Appendix E becomes a root rather than a
  child of the Appendix D agreement title
- updated task and routing documentation

## Research / learning checkpoint

Preserve the distinction between numbering scope and hierarchy state. A nested
regime's declared end item is a structural boundary selected from a later
outline entry at equal or shallower depth. Returning to the parent regime must
therefore not resurrect headings that were open before the nested interval.

## Plan

1. Index each nested regime's declared `end_item_key` by its parent regime.
2. Before processing that end item, clear the parent regime's open-heading
   stack in the builder and independent validator.
3. Add a synthetic regression with stale outer state, a nested regime, and a
   peer end boundary.
4. Rebuild the deterministic semantic payload in scratch space and assert that
   Appendix E has no parent while the previously accepted parent relationships
   for `9 CONCLUSIONS`, Appendix B, and section 5.06(C) remain unchanged.
5. Run `make fix`, `make check`, and `git diff --check`.

## Validation

- No page- or title-specific production condition exists.
- A declared child-regime end clears only its named parent-regime stack.
- Appendix E is a root at corrected level 3.
- `9 CONCLUSIONS` and Appendix B remain under the WSA title.
- `C. Water Enterprise Administrative and General` remains under section 5.06.
- The sealed Task 03E.2 held-out report is not rewritten or rerun.

## Acceptance criteria

- Synthetic and source-bound regressions pass.
- Builder and independent validator derive identical hierarchy relationships.
- All repository checks pass.
- No immutable producer, canonical reference, annotation seal, rejected report,
  or failed candidate is modified.

## Non-goals

- tolerating or correcting the two table false boundaries
- changing R04/R05 evidence precedence or the `Existing SSF District` level
- retroactively changing Task 03E.2 annotations or its terminal rejection
- publishing or promoting a new hierarchy candidate
- activating Task 03E.3

## Outcome

Hierarchy construction and the independent cross-record reconstruction now
index each nested regime's declared `end_item_key` and clear only that regime's
named parent stack before processing the peer boundary. The implementation has
no page, appendix letter, or literal-title condition.

A synthetic regression reproduces stale outer state, enters a nested regime,
and verifies that its peer end boundary becomes a root in both the builder and
independent validator. A scratch build over the verified Appendix P producer
confirmed:

- `9 CONCLUSIONS` remains level 3 under `Water Supply Assessment for the
  Baylands Specific Plan`;
- Appendix B remains level 3 under the same WSA title;
- `C. Water Enterprise Administrative and General` remains level 3 under
  section 5.06;
- Appendix E remains level 3 but now has no parent.

The complete scratch aggregate passed JSON Schema and independent cross-record
validation under code-derived identity
`hcorv1-6d526e412efda997604046caf686091d9bac1ae773951181724511da75984948`.
This identity was not published or bound to a new held-out claim. `make fix`,
`make check`, and `git diff --check` passed with 315 tests, clean Ruff, and
clean mypy. The sealed Task 03E.2 annotations, reports, failed candidate, and
producer/canonical evidence were not modified or rerun.

The learning result is that regime recognition was already correct; the defect
was state restoration. A peer outline boundary that terminates a nested regime
closes the old enclosing stack rather than resuming headings that predate the
nested interval.
