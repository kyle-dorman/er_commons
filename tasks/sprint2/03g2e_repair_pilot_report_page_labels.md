# Task 03G.2e: Repair Pilot Report Page-Label Input

Status: **completed on 2026-08-05**.

## Abstract

The validated three-source handoff and exact reuse check succeeded. The
candidate-neutral aggregate reporter then looked for page-label observations
at `canonical/page_labels.jsonl`, while the maintained semantic contract stores
them at `observations/page_labels.jsonl` inside the same sealed document
candidate.

## Goal

Read the maintained observation path, publish the non-authoritative aggregate
report, and write the checksummed request-only render recipe without rendering.

## Inputs and outputs

Inputs are the validated Task 03G.2 handoff and its three sealed document
candidates. Outputs are one completion-last pilot report bundle and one
`requested_not_rendered` review request in the task review cache.

## Plan and learning checkpoint

Keep semantic record families and observation evidence distinct: page-label
resolutions inform report counts but are not canonical target records. Change
only the reporter path map and its fixture, retain owner checksum verification,
and rerun focused plus full project gates before producing review evidence.

## Validation and acceptance

- the reporter reads `content/observations/page_labels.jsonl` from the sealed
  document candidate;
- focused report tests and all project checks pass;
- the aggregate report validates the ready three-document handoff;
- the render request verifies exact PDF/report inputs and has no generated
  files, publication authority, or Task 04 disposition; and
- no extraction, PDF parser, model, or historical Appendix P lineage runs.

## Non-goals

- changing canonical content, page-label policy, or extraction identity;
- generating review images; or
- activating Task 03H.

## Outcome

The reporter now reads page-label evidence from
`content/observations/page_labels.jsonl` and verifies both maintained owner
inventory seal algorithms: raw file SHA-256 and canonical-JSON SHA-256. The
aggregate report validates all three documents and the ready handoff, and its
bounded anomaly sample contains 92 rows across every observed class plus ten
deterministic extrema.

The completion-last report has SHA-256
`03b2dc667464e927571db7da521e433cf504ff0e4f734e353b66cd76f86621ba`.
The request-only `pdftoppm` recipe has request SHA-256
`b279e29df62b703bac8872c8b8f9c8714281b4b7c320c751e062f8f706c324d2`,
selects 26 source-qualified anomaly pages, and records
`requested_not_rendered`. No render files were generated.
