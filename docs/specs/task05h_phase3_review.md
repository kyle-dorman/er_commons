# Task 05H Phase 3 review result

Phase 3 stopped at an evidence-validator defect. Preparation, text-view creation,
the 116 assigned composition inspections and the fresh repeat are complete;
**review closure has not passed**. Nothing was finalized, published or accepted.

The [machine result](task05h_phase3_result.json) binds the executed request,
supervisor receipts, working candidate, decision journals, repeat comparison and
independent audit. All original evidence remains in the executed plan's working
namespace. The approved source code remains unchanged.

## Completed work

- Both supervised preparations and both text-cache builds succeeded within the
  approved limits. Peak recorded process-tree RSS was 262,717,440 bytes; swap
  growth was zero. Retained new output is 39,508,856 bytes, below the 2 GiB ceiling.
- The fresh attempt reused no prepared checkpoint. All 10 prepared files and
  all 117 cache files matched the first attempt byte-for-byte.
- The view index has 1,013 entries reaching all 2,029 accepted source units.
- Three explicitly identified AI reviewers recorded 116 case-specific decisions:
  101 individual and 15 rule/class obligations across 52 strata. There are
  31 composition confirmations and 85 confirmations with inherited limitations.
  No new content correction was reported.
- Reviewers inspected source boundaries, directed relationships, reference and
  nonlink context, warning fields and provenance examples. Long-card inspection
  used bounded prose excerpts plus complete mechanical record/slice comparisons.
  This is not a new full-source, visual, substantive or user-authored human review.
- All 511 outcomes remain intact: 468 links and 43 nonlinks. The nine homogeneous
  nonlink class cards retain all seven reason families. All 66 F1 warnings,
  the truthful 706/51 coverage distinction and 178 text-ineligible figure targets
  remain explicit. No link recovery was attempted.

## Blocking finding

`validate_decision_evidence` deliberately gives official outcomes no fallback
receipt role (`None`). It nevertheless looks up that key in a dictionary that
also contains roleless dependency metadata. It then treats an unrelated accepted
metadata seal as a receipt and raises `KeyError: 'identity'`.

The named 05D/05E completion authorities are intact and unique. No identity is
missing from an accepted record that should supply it; this is a lookup bug in
the new validator. Decision structure and declared subject coverage pass, but
they cannot substitute for the failed evidence-closure gate. An independent
reviewer reproduced the defect and recorded a material blocker.

## Concrete remediation proposal

The [unapplied patch](task05h_phase3_validator_fix.patch) skips the optional
receipt lookup when its role is `None` and adds a production-shaped regression.
It still rejects missing authoritative components and malformed named receipts.
An isolated in-memory diagnostic reproduces the original failure and passes all
116 evidence memberships with the proposed guard. This diagnostic is not
authoritative closure and has not replaced the approved code.

The [bounded amendment](task05h_phase3_validator_amendment.json) specifies the
exact before/after code hashes and proposed fresh plan. It requires focused/full
checks, independent code review, fresh preparation/repeat, exact semantic/view
comparison and explicit renewed attestations under the new plan. Original
decisions must remain retained; their plan IDs must not be silently rewritten.

The task contract binds execution to exact code and says changed code creates a
fresh plan. Consequently the amendment needs authorization before applying the
patch and executing that new plan. Finalization, publication, acceptance, commit
and push remain outside the proposed authorization.
