# Structured C contradiction-pair expectations v3

Task15N extension to [v2 transformations](task15j_conclusion_transformations_v2.md).
Keep the eight existing families and combined-defect objectives. The paired
experiment reuses the exact378 Task15M conclusions, questions, R/O references,
point-status vectors and Boolean expectations. No new semantic candidates are
required for this comparison. Old publications remain immutable.

Add candidate statement IDs A1, A2, ... as exact sentence spans whose single-space
join reproduces the original conclusion. Segmentation is presentation, not a
label-dependent rewrite. Inspect boundaries, abbreviations and decimal values.

Add `expected_contradicting_points`, a list of unordered pairs of distinct candidate
statement IDs. Store a brief rationale for each pair. A pair requires incompatible
candidate meanings under the same scenario/time/scope. An incorrect claim that
only contradicts a reference receives a reference-point Contradicted status but
no candidate pair. A correct claim and an incompatible candidate claim receive both
the affected reference status and their candidate pair. No pair follows merely
from omitted detail, different scenarios, or unfamiliar content.

CP explicitly tests both detecting the pair and preserving the reference-point
failure; CD6 additionally tests the separate defect. Other families may contain
internal conflicts: review all candidates, not just CP/CD. Compatible candidates
provide empty-pair controls. Do not infer pairs from family names or expected fails.

Every scored expected pair list receives independent review. Disputed pair choices
stay explicit and outside exact-pair scoring until resolved; retain their original
reference/Boolean outcomes for comparison. Do not revise original labels based on
new judge responses. Existing disputed expectations, including C017-ME-01, remain
marked as interpretation-sensitive in analysis. Report model-final and computed
aggregate agreement separately, plus complete-output coverage, point-status
agreement and pair detection. Pair detection does not establish factual truth or
relevance, and deterministic aggregation cannot repair missed contradictions.
