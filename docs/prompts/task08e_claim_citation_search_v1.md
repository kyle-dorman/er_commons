# Task 08E per-claim citation-search prompt v1

Version: `task08e.claim_citation_search.v1`. Inactive while the health-risk 08D
handoff is incomplete. This template contains no live case evidence or decisions.
The [shared spec](../specs/task08e_evidence_review_v1.md) owns budgets and gates.
Save the fully rendered prompt/hash, actual model identity and bound inputs before
future dispatch. Use Astra (`gpt-6-astra`). Fail closed on any unfilled placeholder.

## Assignment

Discover candidates for human evidence review; do not approve sources, determine
eligibility, revise claims/questions, calculate new answers or draft a rebuttal.

- Authorized case/comment and claim: {{case_comment_claim_ids}}
- Exact frozen question, version and hash: {{frozen_question}}
- Exact approved claim and reviewed relationships: {{approved_claim}}
- Validated accepted 08D handoff and completion bindings: {{accepted_08d}}
- 08B selection / 08C approval bindings: {{earlier_gate_bindings}}
- Original comment and complete linked-response bindings: {{context_bindings}}
- Accepted source editions, extraction, usability and limitations: {{source_bindings}}
- Frozen index/settings/runtime binding: {{index_binding}}
- Scope: subject, units, dates, geography, phase and baseline: {{scope}}
- Shared case plan/version/hash: {{case_plan}}
- Assigned supplied references and baseline query IDs/purposes: {{assignments}}
- Shared existing receipts and allocated follow-up slots: {{budget_allocation}}
- Fresh output directory and lead contact: {{output_and_lead}}

Validate all bindings first. Missing acceptance, membership, source identity or
scope is a blocked-input result, not permission to infer the missing value. Use
only supplied current inputs; never load historical case labels or answers.

Resolve assigned references and preserve original versus actual targets. Search
the proposition, its method/baseline and possible counterevidence/limitations.
Use the unchanged full eligible-corpus FTS5 index, at most three baseline queries
per claim and ten hits per query, including at least one full-corpus query.
Shared queries debit every served claim but execute once. Save actual expressions
before execution. Follow only accepted resolved links within the assigned hop
limit (one initially, at most two). Unresolved mentions remain lexical leads.

Inspect every hit. Preserve retained/rejected/duplicate/unresolved disposition,
reason and receipt association. Read complete heading-defined sections and
separate tables with captions, units, notes and relevant technical references.
Do not manufacture boundaries, drop conflicting passages, or use a source-count
cap. Follow-ups require a named gap and prior allocated slot from the lead's
six-query per-case budget. Stop at the assigned limit; report remaining gaps.
A search miss is not document-wide absence.

Select candidate IDs only from verified canonical units. For each retain exact
source/extraction/edition identity, canonical anchors and complete ordered text,
physical/printed pages, provenance, limitations, a focused source summary and
inclusion reason. Preserve subject, units, dates, conditions and uncertainty.
Separate summaries and suggested relationships from verbatim sources and human
labels. Allow `insufficient_evidence` as an advisory search outcome, never an
eligibility decision. No support choice is preselected for the human reviewer.

Return receipts and hit dispositions; reference-resolution records; all inspected
unit identities; candidates and claim associations; budget usage and failed
queries; bounded unresolved gaps; and a restart manifest of exact files/hashes.
Do not publish an accepted handoff or begin 08F. Technical reviewers audit these
records; only saved current human decisions can accept evidence and eligibility.
