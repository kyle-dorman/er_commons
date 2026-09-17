# Task 05G: two unroutable appendix references

Both outcomes capture `Draft EIR Appendix F` as the target label. The selected
source-family catalog declares F1 (Transportation Impact Assessment, using the
accepted Final F1 substitute) and F2 (Safe Routes to School Study), but no
standalone Appendix F source. The exact catalog router consequently returns
`appendix_source_route_absent` before inner-target resolution can run.

## M-CSSC-32: inner Appendix F inside F.1

Volume 4 physical page 215 says:

> Bayshore Mobility Plan, and the full text of the Bayshore Mobility Plan is in Draft EIR Appendix F of Appendix F.1.

The reference explicitly provides an enclosing appendix. The accepted mention
span ends after the first `Appendix F`; its context supplies `of Appendix F.1`.
This is a compound-routing limitation: the parser treats the inner F as a
standalone outer source. It is not evidence that the source document is absent.
A general repair could recognize an explicit nested `Appendix X of Appendix Y`
relationship, route via Y and resolve X as a specific inner target.

## M-CSSC-135: transportation family plus inner C.4

Volume 4 physical page 261 says:

> More-detailed information on the TDM effectiveness quantification can be found in Draft EIR Appendix F, Transportation Technical Reports (Appendix C.4, TDM Effectiveness Calculations,

After intervening page furniture, page 262 continues `therein).` This reference
uses the broader transportation appendix family name rather than explicitly
saying F.1. The catalog does not equate bare F with F1, and doing so globally
would be unsafe because F2 also exists. A general candidate rule would search
only members of the declared appendix family, requiring a unique exact nested
identifier/title match; it must preserve ambiguity rather than select a source
from topical similarity or a document-specific alias.

## Existing selected targets

Independent inspection verified the bound target index and selected canonical
records. Final F1 contains:

- `sec000634`, “Appendix F: Bayshore Mobility Study,” heading `blk005426`, physical
  page 682; body/non-TOC heading. This is the same inner target used by the earlier
  successful nested-appendix cases, though this response calls it a “Plan.”
- `sec000436`, “Appendix C.4. TDM Effectiveness Calculations,” heading `blk003943`,
  physical page 501; body/non-TOC heading. Another section, `sec000429` at physical
  page 489, has a bullet-prefixed version of the C.4 label. It is also labeled
  body/non-TOC, so it cannot simply be dismissed as TOC metadata. A future rule
  must retain that distinction and qualify an exact appendix target, without
  stripping arbitrary bullets to manufacture uniqueness.

These pages belong to the selected Final F1 PDF. Their existence establishes
candidate target availability, not equivalence with Draft F1 or repair success.
M-CSSC-32 is a relatively direct nested-routing case; M-CSSC-135 needs more careful
family scoping and duplicate-label controls. Neither warrants a bare F→F1 alias.

## Warning and acceptance boundary

Neither mention belongs to the original frozen 66-reference F1 reconciliation
population; both currently have no F1 warning because they have no source route.
If routed to the selected Final F1 substitute, each would need explicit additive
substitution-warning coverage. The current validator deliberately rejects F1
warnings outside the frozen population. A future repair therefore needs a bounded
contract/validator amendment as well as a matching rule. Preserve the original
66-member population and its exact warnings, including both revised-content
warnings and the rule that the other 64 mentions are not proven Draft/Final
equivalent. New coverage must not imply equivalence for these additional cases.

This diagnosis does not authorize a replay or source-specific alias. No PDF/image/
model access, extraction or accepted-artifact changes were performed. The current
candidate remains 468 links/43 nonlinks. The [companion JSON](task05g_unroutable_appendix_diagnosis.json)
binds exact mentions, response pages and current input identities.
