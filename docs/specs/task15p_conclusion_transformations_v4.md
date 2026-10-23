# Structured C transformations v4 — Paragraphs and internal contradictions

Current contract for new Task15P data. Retain the eight families and clear-label
boundaries in [v2](task15j_conclusion_transformations_v2.md), with the amendments
below. Supersedes v3's candidate segmentation, pair labels and exact-pair scoring.
Historical datasets and their original contracts are unchanged.

## Inputs and output expectations

Transform only the candidate conclusion. Keep each question, numbered R/O
reference text and shared Baylands overview fixed. Supply the candidate as ordinary
prose, not numbered sentences, bullet claims or a segmented duplicate. Only the
reference points have IDs.

Freeze overall pass/fail labels and provenance before model calls. Authoring notes
may explain the intended defect, but do not create an expected
`internal_contradictions` list, pair inventory, or reason-matching target. The judge's
reason list supports reasoning; it is not semantically reviewed or separately
scored. Validate its structure and flag nonempty-list/pass inconsistency. Evaluate
both model-final and deterministically computed overall decisions. If point-level
expectations are authored in a future suite, score them separately; they are not
required for this targeted overall-decision experiment.

## Contradiction and combined-defect coverage

CP tests two expressly incompatible candidate claims under the same circumstances,
in either order. The conflict may affect an R/O point or lie outside reference
coverage. A contradiction of the reference alone is CT, not an internal conflict.
Do not infer conflicts from omitted qualifications, different scenarios or a list's
brevity. Correct claims do not cancel later wrong claims, nor vice versa.

For this bounded run, author 16 new candidates targeting previously clear misses:
conflicting numerical values after correct values and the reverse order;
categorical denial of added risk without repeating numbers; explicit denial of a
required activity/use already acknowledged; clear qualification conflicts; and
contradiction masked by a separate omission or another contradiction. Use ordinary
paragraphs and strong same-scope statements. Avoid near-threshold floating-point,
ambiguous optional coverage, or debatable implication examples.

Preserve CD objectives: omission plus contradiction checks the independent failure
routes; two contradictions tests continued scanning; accurate surrounding content
tests masking; correct-plus-incompatible claims plus another defect tests that the
first discovered failure does not terminate the check. Overall accuracy alone does
not establish detection of every defect. No separate semantic review or accuracy
metric for the model's contradiction reasons is introduced to fill that gap.

## Review and claims

An independent reviewer verifies new candidate text, unchanged source-bound
references, intended incompatibility and overall label before sealing. These are
agent-proposed diagnostic labels, not human gold. Do not revise labels after seeing
judge outputs. Preserve disputed or ambiguous candidates outside scored data.

This all-negative targeted set tests sensitivity on familiar development questions.
It cannot measure false rejection of compatible paragraphs, full-suite accuracy,
or causal benefit versus an earlier experiment on different candidates. No held-out
or reserved challenges, reference perturbations, or generated target-answer changes.
