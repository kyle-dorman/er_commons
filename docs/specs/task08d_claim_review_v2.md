# Task 08D claim review v2

Status: qualified; [health-risk project 49](http://127.0.0.1:8097/projects/49/data?tab=48&labeling=1) has two submitted reviews awaiting missing relationship/case decisions.
This revision implements Kyle's requested interface simplification. The
[v1 contract](task08d_claim_review_v1.md) retains the unchanged claim, relationship,
human-approval and question-gap rules. The model prompt and all source/proposal
content remain unchanged.

## Changes

- Remove the editable source-passage ID field and its predictions entirely.
  Exact quotations remain expandable beneath each initial proposal.
- Bind each existing claim to its trusted proposal's passage IDs in the exporter,
  independently of saved wording/relationship edits. Reject injected native
  passage controls; never infer new anchors from edited text.
- Set claim boxes to at least 260px and explanation boxes to at least 220px,
  with vertical resizing. Browser qualification measures the actual controls.
- Keep new unbound additions held until a source-bound revision is reviewed.
  They can be saved as unresolved, but cannot become advancing approved claims.

`task08d.claim_review.v2` has separate task/decision schemas and prepared snapshots.
The exporter explicitly retains v1 normalization. Historical prepared v1 files
and project 47 remain untouched, including its one unsaved draft; no submitted
annotations existed at replacement. No annotations or drafts are migrated.

The actual source-free queue qualifies removed controls, large text boxes,
wording/relationship edits, save/reload, exact source spans, target revisions,
unresolved scope, whole-case stops and unchanged human-decision boundaries.
Only the two already-authorized health-risk cases enter the replacement project.

## Saved-review capture and exporter maintenance

The first submitted export retains two native annotations, with incomplete
relationship/case fields explicitly blocking advancement. Saved reviews and
all diagnostics live under `claims_v2/review_capture_v1/` and
`claims_v2/exports/review_v1/`; later captures use fresh revisions.

Label Studio removed the single terminal newline from its saved XML configuration.
The exporter now permits exactly that observed serialization difference, while
retaining raw live bytes and rejecting internal form edits. The new
`claims_v2/prepared_export_v1/` snapshots this exporter repair; its tasks, form,
questions, proposal and sources are byte-identical to the original prepared input.
The original preparation and native annotations remain unchanged. Use the latest
prepared-manifest reference in the current result for subsequent exports.
