# Task 07D citation search protocol v1

Status: current procedure for subsequent authorized Task 07D discovery runs.
Applied on 2026-09-28 to five further cases using the reusable
`pilot_evidence_search` package helper and a frozen FTS5 index. Filled prompts and
query receipts are bound by the remaining-case handoff. This is a curation procedure,
not a frozen benchmark retriever. Earlier SA-Caltrans-33 runs remain historical inputs,
not retroactive v1 runs. This protocol does not itself authorize pilot expansion.

## Purpose and inputs

Produce one manageable, deduplicated pool of citable sections/tables per case,
including potential evidence, qualifications, conflicting material and helpful
context. Human review determines support; retrieval rank never does. Claims and
citations are separate benchmark outputs under the
[evidence review/export contract](evidence_review_v1.md).

Each run binds the exact approved question, claims and relevance labels from the
accepted 07B/07C.1 handoffs, the original comment/response and supplied references,
the accepted source inventory/usability registry, and this protocol version.
Claim wording stays unchanged. I-EA-2 and I-CJ-4 remain excluded. The Task 07D contract owns authorization.

Before searching, save a case search plan: source/edition scope; subject, time
period, geography and comparison/baseline; claim IDs; supplied references; and
query purposes. Group overlapping claims for retrieval without merging claims.
Queries shared by claims run once and retain all motivating IDs. Original response
citations are search leads, not trusted evidence or mandatory final citations.

## Fixed retrieval settings

Use SQLite FTS5 over eligible accepted Draft EIR canonical blocks and tables.
The accepted Final F1 substitution is the sole inherited edition exception;
retain its actual physical edition and 06H limitations, never relabel it Draft
F1. Include it explicitly in the frozen inventory when applicable; do not broaden
to general Final EIR evidence. Record any exclusion in the corpus manifest.
Keep one record per nonempty canonical block and one per table (cell text joined
in canonical order); exclude explicit TOC rows and header/footer records. Store
source ID, extraction identity, record ID and canonical path with each row.
Search text only, with `unicode61` and SQLite's default `bm25()`; sort ascending
score, then source ID and canonical record ID (a unique composite key). No embeddings, stemming or semantic reranking
are implied. Record SQLite/Python versions, exact DDL, query SQL, tokenizer,
ordering, code hash, source inventory hashes and per-source indexed counts.

Use one fixed full eligible-corpus index for a run, including queries restricted
to a source. Filtering a query must not rebuild a smaller index: corpus statistics
otherwise change BM25 scores. Do not compare numeric scores across queries or
corpus versions. A future persistent index is a disposable derived cache, keyed
by the source and index-setting hashes; it cannot replace sealed source records.
In-memory rebuilding is allowed with the same bindings and settings. Verify full
canonical file hashes when constructing the index; reused caches require matching
sealed manifests and integrity verification. No raw PDF re-extraction is needed.

## Search stages and budgets

These are operational defaults, not tuned retrieval hyperparameters or completeness
guarantees. Record overrides as a new plan revision before executing them.

1. **Resolve supplied references.** Check every distinct supplied reference against
   accepted canonical locations. Preserve original and actual targets separately;
   mark supplied, corrected or omitted relationships independently of support.
   Record ambiguity/unresolved references instead of guessing. Read the target's
   section and its attached tables/notes, not just a matching sentence.
2. **Run a baseline search even when citations resolve.** Plan three query purposes
   for each claim: (a) its central proposition/entities, (b) its baseline,
   assumption, mechanism or methodology, and (c) exceptions, alternative conditions
   or potentially conflicting findings. At least one query per claim must search
   the full eligible corpus; the others may target the relevant source/appendix.
   A query may serve several claims or purposes if the plan explains why.
   Baseline budget: at most three distinct queries per claim, ten ranked hits per
   query. Shared queries count toward each served claim's three slots but execute
   once. No early stop merely because a supporting passage was found.
3. **Inspect and expand context.** Inspect every returned hit, not only likely
   supporting hits. Triage a repeated hit/unit once, retaining each query receipt
   and its disposition link. For plausible material, read the parsed heading-defined
   section, attached notes/tables, and necessary referenced technical material.
   Neighboring sections are separate candidates. Log inspected source ranges and
   reference paths. Accepted resolved links may be followed one hop initially,
   at most two under the sprint policy; unresolved references become lexical
   search leads, never invented graph edges.
4. **Resolve gaps with a bounded follow-up.** Trigger follow-up for zero useful
   hits, noisy/truncated results, unresolved citations, missing methods/baselines,
   or conflicting quantities/conditions. Allow up to six additional queries per
   case, ten ranked hits each. Before each, record its gap, parent query/reference
   and changed terms/scope. Prefer distributing queries across distinct unresolved
   issues before revisiting one. The follow-up budget belongs to the case, not
   each agent. Log why no follow-up was needed if skipped.
5. **Stop and account.** Finish after baseline purposes and applicable follow-ups
   are accounted for, or stop explicitly at budget/technical limits. A further
   search needs a named plan revision with a reason; ordinary revisions within
   authorized scope do not require a new permission ceremony. Record remaining
   gaps, truncation and errors. Never translate a bounded miss into document-wide
   absence or declare completeness from repeated hits alone.

Write actual FTS expressions before executing each stage; save original and
revised expressions. Use domain synonyms, acronyms and alternative terminology
explicitly with OR. Quote phrases deliberately; do not require the whole claim
verbatim. `unicode61` does not stem: a literal `relocat` does not implement a
prefix search; use an explicit valid prefix expression such as `relocat*` when
intended. A follow-up that changes syntax/terms is a new recorded query. Failed
syntax attempts are retained but do not consume successful-query slots.

## Candidate assembly and review burden

Retrieval remains block/table based in v1; citation output is section/table based.
Validate candidates through `pilot_citation_units`: actual heading, exclusive next
heading, complete ordered membership, separate table identity, captions/cells/
notes, physical PDF pages and printed labels. Do not concatenate neighboring
sections into a single citation. Boundary ambiguity or missing/unusable source
content remains a gap, not a manufactured unit. Use targeted PDF visual checks
when tables, footnotes, page labels or parsed boundaries are uncertain.

Deduplicate by source, accepted extraction version, unit kind and canonical unit
ID across the case. Keep every contributing hit/query/reference as provenance.
Keep tables distinct from their enclosing narrative sections. Retain plausible
material support, contradictions, qualifications and useful explanatory context;
record reasons for rejected hits (wrong pollutant, phase, geography, duplicate,
incidental mention, unusable source, etc.). No top-three citation cap. Arrange
review in digestible batches if needed, with pending candidates visible in the
inventory; presentation batching must not silently discard evidence.

Separate verbatim source content from agent notes. Each candidate includes a
short inclusion reason and any meaningful uncertainty, never a preselected human
label. Preserve internal claim associations as discovery/review provenance; final
output has separate claims and deduplicated citations. Final support/context
aggregation follows the export contract, not an agent's candidate classification.

## Agent handoff template

Use the full [per-claim sub-agent prompt v1](../prompts/task07d_claim_citation_search_v1.md)
for each claim assignment. It is the authoritative dispatch template and includes
exact input placeholders, search instructions, section/table boundaries, output
requirements and a restart checklist. Fill every placeholder from bound records;
save the rendered prompt/hash and agent identity before dispatch. Do not substitute
a shortened “find evidence” instruction or rely on inherited chat history.

The lead owns the shared plan, budget, deduplication and integration. Delegate
bounded reference resolution, complementary query groups or a boundary audit;
independent agents must not each spend the full case budget. A separate reviewer
checks source scope, query-purpose coverage, discarded contradictions, section/
table boundaries and provenance. Sub-agent recommendations are not human labels.

## Required records and validation

Use fresh no-clobber directories under the configured Task 07D artifact root.
Save the bound input/index manifest, case search plan and revisions, exact agent
prompts, reference-resolution records, query receipts, hit snapshots, disposition
ledger, citation candidates, gap summary and independent review. Each successful
query receipt includes ID, purpose, motivating claims, expression, source filter,
index identity, total matches, ordered returned IDs/scores, limit and truncation.
Every returned hit gets a retained/rejected/duplicate/unresolved disposition.
Source expansions record their seed and exact inspected units even without a query.
Seal the managed-file inventory last; incomplete runs retain diagnostic status.

Before a case is ready for human review verify: all approved claims have baseline
coverage; all references and returned hits are accounted for; budgets/overrides
are explicit; all citations pass source/boundary validation; duplicate units are
merged without losing provenance; no machine support labels became human inputs;
all remaining gaps are visible. A replay with identical inputs, queries and engine
must reproduce ordered hit IDs and candidate source bindings. Agent-written query
planning and semantic selection remain judgment calls; their saved outputs make
replay possible but are not claimed to be deterministic from the prompt alone.

## Research and learning

[SQLite's FTS5 documentation](https://www.sqlite.org/fts5.html) defines query
syntax, `unicode61`, prefix matching and BM25 ordering. Its
[BM25 reference](https://www.sqlite.org/fts5.html#the_bm25_function) explains the
corpus statistics and lower-is-better score used here. Checked 2026-09-28.
Built-in FTS5 keeps the bounded lexical baseline narrow and reproducible without
adding a search service. Fixed index settings plus saved queries separate retrieval
replay from agent judgment. Full section/table assembly preserves citable context
while avoiding a premature change to retrieval granularity. This curation search
uses reviewed claims and responder leads; it is not the benchmark target retriever
or evidence of its evaluation performance.
