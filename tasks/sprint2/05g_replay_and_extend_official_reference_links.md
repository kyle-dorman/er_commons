# Task 05G: Replay and Extend Official Reference Links

Status: **provisional and inactive until Task 06 publishes an accepted
replacement handoff**.

## Goal

Replay the accepted Task 05 source-free stages through Task 05F against Task
06's replacement Task 04 handoff, then iteratively qualify additional exact
linking rules from the remaining failure census. Preserve one complete outcome
for every in-scope mention after every cycle.

Task 05G is the bounded convergence loop for official-reference linking. Task
06 owns source, extraction, structure, target-index, and usability repairs;
Task 05H owns final curator review and immutable inventory publication.

## Starting point

- accepted Task 05D source-unit inventory;
- accepted Task 05E relationship graph;
- Task 05F's accepted partial candidate
  `rulesv1-9e67959aefc07f9ffd65605ad9d886a53022dcaccc5c9c8bed1494c41b4c0a83`,
  with 295 links and 216 explicit nonlinks;
- Task 05F's schemas, implementation, focused tests, provenance rules, and
  passing human code-quality gate; and
- the future accepted Task 06 replacement handoff and usability registry.

## Required behavior

1. Validate compact accepted identities and reuse unaffected Task 05 evidence.
   Replay only stages invalidated by Task 06; do not automatically reopen PDFs
   or rerun accepted source extraction.
2. Rebind Task 05F resolution to the exact Task 06 handoff and reproduce the
   frozen population of 509 Draft EIR and 2 Appendix Q mentions.
3. Compare every changed link, nonlink, collision, usability annotation, and
   reverse-index entry with the Task 05F partial outcome.
4. After each replay, stop with a complete failure census. Add another rule only
   after bounded review shows that it is exact, source-compatible, broadly
   stated, and supported by focused positive and negative controls.
5. Preserve unresolved candidates and collision options for later human review.
   Never select among them with fuzzy, semantic, embedding, or LLM matching.
6. Keep Appendix Q separate, preserve comment-authored references without
   official-response links, and keep structural and visual usability distinct.
7. Give output-affecting code a fresh identity and retain prior candidates as
   evidence. Derive forward and reverse indexes from mention-to-link provenance.
8. Require formatting, linting, strict typing, focused tests, all repository
   tests, deterministic replay, and a human code-quality gate before handoff to
   Task 05H.

## Iteration boundary

Task 05G may contain multiple reviewed source-free replay cycles. A new failure
class does not silently expand Task 06 or another upstream stage: record it,
identify the owning stage, and stop for a contract decision when upstream data
must change. Do not create one numbered task per small exact-rule amendment.

## Outputs

- fresh replay candidates with complete individual accounting;
- exact before/after link and failure censuses;
- complete collision option sets and usability annotations;
- deterministic provenance-derived forward and reverse indexes;
- focused rule fixtures and code-quality evidence; and
- one final accepted link-layer handoff for Task 05H.

## Non-goals

- Source acquisition or upstream extraction/target repair owned by Task 06.
- Appendix Q extraction.
- Fuzzy or semantic matching.
- Substantive response adequacy, benchmark eligibility, clustering, or case
  authoring.
- Immutable response-inventory publication owned by Task 05H.
- A resolver framework, workflow engine, review application, or artifact store.
