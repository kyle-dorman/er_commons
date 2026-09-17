# Task 05G Phase 4 bounded rule trial and review

The authorized general-rule trial recovered **nine of eleven low/moderate
cases**. The candidate now contains **459 links and 52 explicit nonlinks**.
No document-specific exceptions were introduced. The fourteen mention IDs bound
in the request constrain comparison scope only; they do not select resolver
behavior. The [result manifest](task05g_phase4_result.json) records exact sealed
artifacts, receipts and comparison results. This candidate is not accepted.

## Recovered cases

| Reference | Response | General evidence used |
| --- | --- | --- |
| Appendix A, Chapter 08 / Public Facilities Financing | M-OSEC-112 | Explicit compound reference and exact chapter identity |
| Appendix A, Chapter 06 / Circulation | M-CSSC-153 | Explicit compound reference and exact chapter identity |
| Appendix D, printed page 2-21 | SA-CDFW-9 | Unique printed footer label on existing physical page 37 |
| F1, Muni section | SA-Caltrans-9 | Unique exact section title; page qualifier remains explicitly unverified |
| F1, Section 5 / Project Travel Demand | M-CSSC-94 | Exact section identifier and title |
| F1, nested Appendix F / Bayshore Mobility Study | M-CSSC-85 and M-CSSC-126 | Explicit nested appendix and exact title; two mentions |
| F1, Table C8 / Mode Share Comparisons | SA-Caltrans-8 | Letter-prefixed caption, strict geometry and canonical Appendix C.2 ancestry |
| F1, whole assessment | M-OSEC-94 | Full-token parsing removes the false interpretation of “table are” as Table A |

Eight gains link specific inner targets. The ninth corrects a false specificity
signal and links the genuinely whole-document reference. No genuinely specific
reference was weakened to a generic document link. Consumer-derived page/table
aliases reuse sealed canonical identities; upstream records remain unchanged.

## Deferred cases

- **F1 Table 5:** four candidates share the identifier. The reference supplies
  no exact title/page discriminator. No semantic guess was added.
- **F1 Table 6:** caption/table boxes overlap by three points, failing the strict
  geometry qualification. No arbitrary tolerance or document exception was added.
- **Three figure cases:** Appendix D Figure 3, F2 Figure 4 and K1 Figure 4a were
  outside the low/moderate trial and remain unchanged.

The nineteen missing-exact-target cases also remain unchanged as the user
requested. All source-substitution warnings, review limitations and text-only
figure exclusions are preserved.

## Independent review and remediations

The independent `phase4_review` agent reviewed the implementation and exact
prelaunch packets. Initial findings concerned selecting one member of a compound
reference, specificity lost through plural/terminal-period parsing, and dropping
duplicate aliases in a way that could create false uniqueness. These were
remediated and covered by synthetic regression controls before launch.

Attempt 4 then failed the strict comparison because the general parser also
reinterpreted previously linked references outside the trial population. Its
packet, checkpoints, logs and failed receipt remain preserved. The correction
limits new proposals to cases the existing general inner-target guard would
otherwise block. This predicate uses reference semantics, not document or mention
IDs. The independent reviewer approved the corrected code and attempt 5 packet,
and subsequently the explicit repeat packet for attempt 6.

The independent actual-result audit returned **PASS, no material findings**. It
verified all four checkpoint closures and recomputed the Phase 3 comparison
from sealed outcomes: 511 outcomes, nine gains, zero losses, all 497 outside-scope
outcomes unchanged, and all prior link annotations and 66 F1 warnings preserved.
It also checked selected canonical evidence and inventory hashes for the printed
page and C8 table, and the truthful unverified-page flag on the Muni link.

The parent verified successful repeat attempt 6 and exact byte/mtime preservation
of every original checkpoint file. Both successful runs had zero swap growth and
remained within unchanged resource caps. The result manifest contains these
receipts and the checkpoint snapshot; the independent actual-result audit covered
attempt 5, while repeat terminal verification was performed by the parent.

## Validation and boundary

All 214 focused Task 05G tests pass. `make fix` and formatting/lint/mypy checks
pass. Full pytest has 2,319 passes and three known historical Task 06G failures:

- `test_collection_generator_preserves_historical_v38_owner_packet`
- `test_task06g_v38_generation_remains_immutable_after_finalization_amendment`
- `test_task06g_templates_are_executable_and_source_free`

These unchanged tests expect later finalizer drift but fail earlier on the
accepted repository-base check. They were independently reproduced from an
isolated export of accepted commit `6c95803` during Phase 2. No historical code
or tests were changed to suppress them.

The useful general boundary is exact syntax plus unique, qualified existing
target evidence. Missing disambiguation and conflicting geometry remain explicit
nonlinks. Phase 5 finalization/acceptance requires separate authorization; Task
05H, source/model work, commit and push were not performed.
