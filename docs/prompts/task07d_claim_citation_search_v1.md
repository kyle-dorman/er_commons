# Task 07D per-claim citation-search prompt v1

This is the authoritative reusable sub-agent assignment for one reviewed claim.
The lead must fill every placeholder, save the rendered assignment with its hash
and agent/model identity in the fresh run directory, and send that exact text.
Do not rely on inherited chat history. Changes to instructions require a new
prompt version; factual placeholder values vary by assignment.

The [search protocol](../specs/task07d_search_protocol_v1.md) owns retrieval
settings/budgets. The [review specification](../specs/evidence_review_v1.md) owns
citation metadata, human judgments and final export. This prompt is a curation
assignment, not the future target-model evaluation prompt. It was applied to the
28 claims in the remaining five approved cases on 2026-09-28; the run retains exact
filled assignments and the dispatch-time template. Everything between BEGIN and
END is the assignment.

## BEGIN ASSIGNMENT

You are discovering citable source material for one already-reviewed claim.
Produce evidence candidates for human review. You are not deciding whether the
claim is true, changing its wording or writing a final defense answer.

### Your exact assignment

- Case ID: {{case_id}}
- Claim ID: {{claim_id}}
- Exact approved claim: {{claim_text_verbatim}}
- Reviewed question/concern: {{question_text_verbatim}}
- Claim relevance role, for context only: {{reviewed_relevance}}
- Scope to preserve (phase/time, geography, pollutant/topic, baseline/comparison):
  {{scope_summary_with_input_references}}
- Bound approved claim/question files and hashes: {{review_input_bindings}}
- Original comment/response and supplied-reference files: {{response_lead_bindings}}
- Eligible source/edition manifest and inherited limitations: {{source_bindings}}
- Frozen search index manifest/settings: {{index_binding}}
- Case search plan: {{search_plan_path_and_hash}}
- Assigned supplied-reference IDs: {{reference_assignments_or_none}}
- Assigned baseline query IDs/purposes: {{baseline_assignments}}
- Follow-up query IDs/budget allocated by lead: {{followup_allocation_or_none}}
- Shared-query receipts/candidates already available: {{shared_inputs_or_none}}
- Exact fresh output directory: {{output_directory}}
- Lead agent/contact for gaps or budget reassignment: {{lead_agent}}
- Protocol/spec/prompt paths and versions: {{instruction_bindings}}

Read these inputs first. Missing/unverified bindings or unresolved placeholders
are a blocked-input result; do not invent content or silently use another release.
Use only this case and claim. Other claims may explain shared searches but do not
expand your assignment. The original response and its references are leads, not
source evidence. Claim relevance does not establish actual evidence support.

### Search the proposition, not just its citation

1. Check assigned supplied citations against the canonical source. Preserve the
   original reference and actual target separately. Identify correct, mis-cited,
   ambiguous and unresolved references. Include useful uncited material as omitted
   citations. A resolved citation never excuses the independent search below.
2. Plan/query the central proposition, its assumptions or methodology, and possible
   qualifications or conflicting findings. Do not search only for confirmation.
   Account for all three baseline purposes, with at least one full eligible-corpus
   query for this claim. Reuse assigned shared-query receipts rather than executing
   identical searches again. Save actual query expressions before execution.
3. Use the frozen SQLite FTS5 index and prescribed settings. Keep the same index
   for source-filtered queries. Use at most three baseline queries and ten ranked
   hits per query, subject to the case plan. Explicitly account for synonyms,
   acronyms and phrase/prefix syntax; there is no automatic semantic search.
4. Triage every returned hit, recording why it is retained, rejected, duplicate or
   unresolved. Triage repeated hits once but preserve their query associations.
   For plausible results, read the complete source section and relevant technical
   context. Do not reject material just because it complicates or contradicts the
   response. Distinguish construction from operations, the relevant pollutant or
   impact, existing conditions from future predictions, and assumptions from
   independently substantiated findings.
5. Use only your allocated share of the case's six follow-up queries. Trigger
   follow-up for missing methods/baselines, unclear references, noisy or truncated
   results, alternative wording and contradictory quantities/conditions. Record
   the gap and parent query/reference before executing each follow-up. Ask the
   lead for a recorded plan revision if more work is needed; do not silently spend
   other agents' budgets. Log source/section inspections and reference traversals
   as well as queries. Follow only accepted resolved edges, initially one hop and
   at most two; unresolved mentions are lexical leads, not verified edges.
6. Do not stop just because one supporting-looking passage was found. Stop when
   assigned search purposes and applicable follow-ups are accounted for, or when
   the declared budget/technical limit is reached. State remaining gaps precisely;
   a bounded miss does not prove that evidence is absent from the document.

### Every candidate must be independently citable

A search hit is a locator, not the finished evidence unit. Read the parsed text
and section records to establish the actual boundary before returning a candidate.

- A narrative citation starts at its actual parsed section/subsection heading and
  ends immediately before the next body section heading. Use the actual heading
  and full breadcrumb, not an invented summary title. Do not append the next
  section, splice noncontiguous sentences or return an arbitrary page window as
  a whole-section citation. If useful material crosses headings, return separate
  citation units. A parent heading is not permission to swallow its subsections.
- Preserve the complete ordered canonical narrative, including qualifications and
  attached footnotes. Running headers/footers are not evidence text. Record the
  next-heading anchor as the exclusive boundary; never guess a boundary. The
  current validator requires that anchor. Document-end cases without a next
  heading remain unresolved pending a versioned, verified boundary rule.
- A table is its own citation with canonical table ID, exact caption, complete
  nonempty cells, headers, units and attached notes. Keep the table separate from
  the enclosing narrative citation. Explicitly account for separately cited table
  content excluded from narrative display. Unsupported/ambiguous table-note or
  section associations remain unresolved pending a documented rule.
- Retain source document and physical edition, accepted extraction identity,
  section/table IDs, canonical file paths, ordered block/cell IDs, exact text and
  content hashes, physical PDF pages and separate printed page labels. Bind source
  URL/license/retrieval metadata through the accepted manifest. Use the existing
  citation-unit validator; do not invent IDs, links, page labels or clean up source
  wording. Check the source PDF when parsing, table content, footnotes or printed
  labels are uncertain. Preserve source usability and text-only restrictions.
- Keep all your explanations outside verbatim source content. Explain why a unit
  is useful, what it may establish and what remains uncertain in separate notes.
  Do not represent a methodological assumption as proof of a real-world outcome
  or silently reconcile conflicting numbers between tables.

### Selection and shared citations

Prefer retaining plausible material evidence and useful background for Kyle to
filter. Exclude incidental topic matches with a recorded reason. There is no
three-card cap. Background must be just as citable as possible supporting material.

Return one candidate per (source document, accepted extraction identity, unit
kind, canonical section/table ID). Preserve every query/reference that found it.
If another claim uses the same unit, refer to its shared identity rather than
create a new source unit. Tables remain distinct from their narrative sections.
The lead will assemble a single case citation pool; do not delete a unit simply
because another claim's agent found it first.

Claim-to-citation associations are internal search/review provenance. The final
benchmark export separates claims from a deduplicated citation list. Its citation
levels are support and context, assigned from human review; no final partial
support citation level is needed. Do not preselect these labels or infer them
from relevance, ranking or your inclusion reason. Retain qualifications/conflicts
in notes for review even though they are not additional final citation levels.

### Required handoff

Write only inside your assigned fresh directory, preserving all upstream files.
Return these logically separate records using the existing protocol/spec formats;
do not invent a competing citation schema:

1. Assignment/input bindings and the actual query plan, including revisions.
2. Reference resolutions: original reference, actual canonical target or unresolved
   reason, and supplied/corrected/omitted relation where applicable.
3. Query receipts: query ID/purpose, exact expression, filter, index identity,
   total matches, ordered returned IDs/scores, limit, truncation and errors.
4. Hit dispositions and inspected context/reference paths, including rejected hits.
5. Deduplicated citation candidates with validated section/table metadata, exact
   source content and provenance, and separate inclusion/uncertainty notes.
6. A concise gap report: baseline purposes covered, queries used, new/shared units,
   unresolved references, assumptions not substantiated, conflicting findings,
   uninspected overflow and reason for stopping. Mark the handoff ready for lead
   review, incomplete, or blocked; none means human approval or exhaustive search.

Before returning, verify all assigned references/hits have dispositions, all
retained units have real boundaries and exact provenance, and no source text is
mixed with your commentary. Do not submit human reviews, alter reviewed claims,
change the corpus/index settings or expand discovery to other cases.

## END ASSIGNMENT

## Lead integration and restart checklist

- Fill the template from the accepted records; verify exact claim/question text.
- Save template version/hash, rendered prompt/hash, input identities, agent/model
  identity and assignments before dispatch. Record known runtime settings; mark
  unavailable settings unknown rather than inventing them. Prompts are run data.
- Allocate follow-up slots centrally and reuse shared query receipts. One agent
  per claim does not mean each receives the entire case follow-up budget.
- Independently check candidate boundaries and source bindings, merge duplicate
  units losslessly, and keep machine recommendations separate from human labels.
- Save unresolved gaps and review status in the case manifest. Resume from those
  artifacts and the current task/TODO, not a reconstructed chat conversation.
- Preserve the distinction between curation and evaluation: this assignment sees
  approved claims and responder leads. Future target-model prompts need a separate
  input contract; they must not inherit reference claims, labels or curator-only
  evidence IDs. Shared citation granularity and output conventions can carry over.
