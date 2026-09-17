# Task 05G: general header-qualification trial

The authorized trial recovered all **nine section collisions**, taking the
working candidate from 459 links/52 nonlinks to **468 links/43 nonlinks** across
511 mentions. All 502 outcomes outside the authorized population are unchanged;
all 459 previously resolved targets and their review annotations are preserved.
Compared with accepted Task 05F's 295 links/216 nonlinks, this is 173 gains and
zero losses. The three multipart K1/K2 collisions remain explicit nonlinks.

## General rule and evidence

The new policy retains the prior inner-reference rules and adds a
collision-only section qualifier. A competing body heading can be excluded only
when its normalized text, page dimensions and coordinate conventions agree with
an independently classified canonical furniture header on a different physical
page, and all four bounding-box edges differ by at most one PDF point. The
resolver requires exactly one remaining target. Otherwise it preserves the
original collision without selecting a target.

The rule has no document or mention ID exceptions. The nine frozen mention IDs
are a comparison guard, not a resolver allowlist. It reads only existing sealed
canonical JSON/JSONL and derives consumer evidence; original target records and
accepted 06G/06H artifacts are unchanged. Global/source candidate diagnostics
retain the original competing target IDs. The outcome records the excluded
targets and exact corroborating block/page/region evidence.

| Reference | Response(s) | Selected existing target suffix |
| --- | --- | --- |
| Section 4.5 | O-Joint-24 | sec000705 |
| Section 4.6 | M-OSEC-93, M-OSEC-137, O-Joint-2 | sec000864 |
| Section 4.11, written 4-11 | M-OSEC-137 | sec001497 |
| Section 4.12 | M-OSEC-340 | sec001587 |
| Section 4.13 | M-OSEC-65 | sec001748 |
| Section 8.5 | M-OSEC-143 | sec003322 |
| Section ES.6 | M-OSEC-13 | sec000260 |

This is metadata-based exclusion of header artifacts, not a new human review or
repair of section extents. In particular, matching text alone is insufficient:
the genuine ES.6 heading shares the header wording but has different geometry.
All existing target-review limitations remain, including 706 evidence-proven
Task 04 reuses versus 51 decisions carried through sampled-stratum confirmation.
All 66 F1 warnings remain, including the two response-specific revised-content
warnings and the other 64 mentions' unproven Draft/Final equivalence. All 178
caption-backed figures remain unavailable as text-only evidence.

## Validation and independent review

The 272 focused Task 05G tests pass, including 52 pure qualifier controls and six
resolver/comparison integration controls. Negative tests cover different geometry,
page dimensions, coordinate conventions, same physical page, source/document
mismatch, malformed/nonfinite coordinates, TOC status, ambiguous remaining targets,
comment mentions and protection of existing unique links. `make fix` passes;
`make check` passes formatting, lint and mypy, with 2,377 passing tests and the
same three historical Task 06G failures already reproduced at accepted base
`6c95803` during Phase 2. No historical tests were changed.

Independent `header_review` code and attempt-7 prelaunch review returned PASS
with no material findings. It regenerated the actual packet, verified current
code/schema pins, prior attempt-5 checkpoint closure, the exact nine-case scope,
fresh output roots and unchanged resource limits. Its minor observation about
logical-to-physical source routing was corrected generically before launch.

Attempt 7 completed with return code zero in 6.915 seconds, peak RSS 719,585,280
bytes and zero swap growth. Its behavior identity is
`44763b4cce241c7b07562f5b7f7f18da8ea01f87385420dbacdca69b9690f3c0`.
The [launch packet](task05g_header_launch_packet.json) and
[repeat packet](task05g_header_repeat_launch_packet.json) freeze exact commands,
paths and limits. The [result manifest](task05g_header_result.json) records terminal and checkpoint evidence.

No PDF/image/model access, extraction/conversion, accepted-artifact mutation,
finalization, acceptance, Task 05H, commit or push was performed. This remains
a working candidate pending separately authorized publication.


Independent actual-result review returned PASS with no material findings. The
reviewer verified all four checkpoint closures, independently recomputed the
nine-gain comparison, and checked selected canonical records for all sixteen
excluded header targets and their carried exemplars. Seven retained section
identities account for the nine references. The repeat packet also passed
independent review. Parent verification of actual attempt 8 confirmed success
in 5.578 seconds, peak RSS 701,693,952 bytes, zero swap growth, and unchanged
bytes and modification times for every original checkpoint file. Cumulative
05G artifacts and logs occupy 102,373,277 bytes, below the unchanged 2-GiB cap.
