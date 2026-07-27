# Project TODO

## Sprint status

Status: Sprint 2, Brisbane Draft-EIR defense vertical slice.

Current active task: [Task
03A](../tasks/sprint2/03a_validate_document_parser.md), validate the document
parser and native-only extraction configuration. [Task
02](../tasks/sprint2/02_freeze_sources_and_provenance.md) froze and verified
`brisbane_baylands_2025_deir_sources_v1` under the external artifact root.

Current next action: execute Task 03A only, explain the document-AI evidence and
tradeoffs, and stop for user review. Task 03B through Task 03H are provisional
contracts written at the user's request; revise the next one from the accepted
preceding outcome before activating it.

## Open queue

1. Execute Task 03A and review the parser/configuration evidence.
2. Continue through provisional Tasks 03B–03H one at a time: canonical
   contract, single-document conversion, core records, hierarchy and
   cross-references, restartable batching, production pilot, and full candidate
   extraction.
3. Independently review usability and freeze extraction v1 in Task 04.
4. Continue through response inventory, case authoring, and benchmark freezing
   using one bounded task at a time.
5. Freeze human evaluation before BM25 retrieval, target generation, and judge
   calibration; finish with the primary test and oracle diagnostics.

Sprint 2 scope, decisions, and provisional sequencing live in
`docs/sprints/sprint2_brisbane_draft_eir_defense.md`. The completed Task 02
owns source-freeze implementation detail and the precise extraction handoff.
