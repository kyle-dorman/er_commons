# Task15Z retrieval evidence mapping v1

This curator-only sidecar to Task15AC publishes evidence relationships for future
retrieval development. It does not change approved questions, required/optional
meaning, C/G/S verdicts, runtime citation roles or existing scores. Do not expose
case-specific gold mappings to a search agent being evaluated.

## Contract

One case record contains the exact question, canonical required and optional
points, and a catalog of every reviewed citation occurrence. Each point contains:

- `point_id` and exact approved `text`;
- `sufficient_evidence_sets`: alternative known sufficient sets. Any one set can
  support the complete point. Within a set, **all** citation occurrences are
  jointly needed. A singleton is independently sufficient;
- `partial_support_citation_ids`: useful but insufficient alone and not included
  in a published sufficient set; never count these as complete evidence;
- `notes`: source limitations or bounded inference needed to read the sets.

Each set contains `citation_ids` and a rationale explaining sufficiency and, for
joint sets, which passages supply complementary meaning. Enumerate verified
alternatives in the reviewed packets, avoiding redundant supersets. Do not infer
that every citation associated with a point is independently sufficient. If
sufficiency cannot be established, publish an explicit unresolved record rather
than inventing a set. Required/optional point text is never repaired by this step.

The citation catalog preserves the prior audit classification and publishes a
reviewed `retrieval_role`: `direct_required`, `mixed`, or `optional_context`,
plus per-point relations and exact source identity,
record location, pages, hashes and existing anchors. Required-evidence relevance
does not make every related citation mandatory. Mixed citations may supply both
required and optional evidence. Context outside approved optional points remains
cataloged and is not discarded.

To obtain evidence for a complete required answer, cover every required point
with at least one sufficient set. Optional point sets enrich an answer and never
become completeness requirements. A shared retrieved passage can support several
points. This is a mapping interpretation, not a newly activated benchmark metric.
These are known reviewed routes, not an exhaustive list of valid evidence in the
corpus: unlisted evidence remains unjudged, not automatically irrelevant.

Citation IDs identify reviewed passages, not whole-document retrieval obligations.
A page/document hit alone does not establish that a retrieved chunk contains the
needed evidence. Later retrieval evaluation must reconcile chunks with source
anchors and preserve table headers, qualifications and joint context. Source
identity/edition and exact excerpt provenance remain bound to Task15AC; duplicate
occurrences may be alternative routes and must not be counted as independent
obligations.

## Publication and validation

Author all 49 cases from the frozen references and citation audit, then independently
review each case's sufficient sets, alternatives and partial-support treatment.
Store detailed records externally in a fresh sealed Task15 namespace. A compact
tracked pointer binds the source release, prior audit, mapping, independent review,
validation and completion inventory. Preserve the prior audit unchanged.

Validate exact population/point text, citation membership, nonempty unique sets,
no redundant superset alternatives, complete catalog coverage, hashes and source
anchors. Record unresolved semantic questions; do not resolve them mechanically.
No search-agent implementation, retrieval run, model calls, synthetic changes,
commit or push is authorized.

## Design basis

The [FEVER dataset's evidence format](https://fever.ai/dataset/fever.html) represents
alternative sets, each containing one or multiple evidence items. This fits the
need to preserve alternative and joint evidence without treating every relevant
citation as mandatory. We use existing project citation identities and point
semantics rather than importing FEVER labels or scoring. The preceding Task15Z
methods note records W3C segment-selector guidance for exact provenance.


## Published artifact layout

The [publication pointer](task15z_retrieval_mapping_result.json) selects a sealed
external namespace. `mapping.json` owns version/input bindings and hashes for
`cases/<case_id>.json`. Each case binds its exact source record and includes
`required_points`, `optional_points`, `citations` and source limitations.
`review.md` summarizes decisions; `mapping_review.md` renders every evidence route.
`reviews/` retains authoring and independent review; `provenance/` retains the
bounded builder snapshot and validation controls. This is a data publication,
not a new package API or CLI.

`citations[].source_segments` selects exact source-record text fields and hashes;
`approved_evidence_anchors` preserves the source point's original anchors. Group
rationales explain alternative/joint sufficiency. These field locations do not
assert that an arbitrary chunk from the same document contains complete evidence.
Previously optional/context C054-S006 is mixed in this sidecar: its Alternative 5
feasibility paragraph also supplies the land-use mix needed jointly for R2.
That relationship was independently reviewed; approved point text is unchanged.
