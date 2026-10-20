# C014 question clarification proposal

Status: **Awaiting approval of the exact proposed question.** Preparation is
authorized by [Task 11D.2](../../tasks/sprint2/11d2_resolve_evaluation_contract.md).
This proposal does not change a benchmark publication, reference, prompt or score.

## Exact question texts

Current published question:

> How does the DEIR account for the Quarry and Candlestick Point developments when evaluating the Baylands’ cumulative transportation impacts?

Proposed question:

> Using the supplied Draft EIR passages and Final EIR Appendix F.1, explain how the Quarry and Candlestick Point developments are accounted for in cumulative transportation analysis, including the applicable analysis scopes and future-growth scenarios. Distinguish what each edition establishes.

The proposal makes the existing approved scope visible without supplying the
answer. It names neither project identifiers, numerical results nor expected
scenario assignments. A changed question defines a prospective condition; it is
not a retroactive reinterpretation of the sealed comparisons.

## Keep the approved reference unchanged

The current reference is factually supported and intentionally approved:

> The DEIR accounts for Quarry and Candlestick Point through its cumulative-project inventory and topic-specific transportation scopes, while future scenarios assess Baylands within broader regional growth. The supplied Final Appendix F.1 also expressly identifies both developments as future land-use inputs.

Regional growth is relevant to the existing methods question, but its mandatory
coverage is not explicit. Requiring a later Final-appendix statement is especially
unclear when the question names only the DEIR. Clarify the question rather than
remove supported, approved reference content to accommodate observed failures.
This document does not propose a reference rewrite or new grading requirement.

## Source support and limits

The already delivered C014 packet provides the following evidence:

| Passage | Source location | What it establishes |
| --- | --- | --- |
| P1 | Draft EIR, “Travel Demand Forecasting,” 4.8-60–61 | Without-project land uses are reallocated “while not changing the total amount of regional growth expected for 2040”; scenarios use regional and subarea models |
| P2/P3 | Draft EIR Tables 7-2 and 7-11, 7-8–19 and 7-47 | Named cumulative projects connect to topic-specific analysis groups; methods differ by impact |
| P4 | Supplied Final Appendix F.1, Appendix B.3, B-14–15 | Future scenarios “account for regional growth associated with the buildout anticipated by 2040” and Plan Bay Area 2040 changes |
| P4/P5 | Supplied Final Appendix F.1, Table B-4, B-15 | Both named developments occur in the Mid-Term 2035 land-use column |

These sources do not independently verify project-level model coding, inclusion
in every scenario, individual traffic contributions or Draft/Final equivalence.
No new mandatory numerical or scenario detail is introduced by this proposal.

The Final source's recorded PDF SHA-256 is
`e13c5b53f0f4da6a91f52ac784acce06619eeffd3fe053542d7ce1593b957e5e`.
Its retained provenance distinguishes a May 2026 Final EIR wrapper from the
underlying December 2024 transportation report. “Accepted qualified substitute”
and “no Draft-equivalence assumed” are approved curator annotations, not claims
made by the excerpt. They establish the workspace's source-use boundary, not
document equivalence. The metadata audit does not newly authenticate the PDF's
contents or remove inherited extraction limitations.

## Approval lineage and activation boundary

Paths below are relative to `ER_COMMONS_DATA_ROOT`; hashes bind the reviewed bytes.

| Record | SHA-256 |
| --- | --- |
| `benchmarks/er_bench/releases/task09f_20261014_v2/curator/cases/C014.json` | `374e2a08f3aba74bafa522227d4642b6cc22057f7d39aad77467dcd65da9d49a` |
| `pipelines/brisbane_baylands/task_08/08e_human_review_20261007_v1/C014/question_v2_review/checkpoint_004.json` | `677dad205d2f004dbdc77449c7b68727a1d8db5b7dd6b0d1163c29f47f6bb6de` |
| `pipelines/brisbane_baylands/task_08/08f_human_review_20261008_v1/C014/version_003.json` | `de74bb68f3b9723459bea0ad280968447d9872081137bfac9f1f78320eab19b4` |
| `pipelines/brisbane_baylands/task_08/08f_human_review_20261008_v1/journal_event_043.json` | `12da26e31ab4efe50b72ef69fd0252747ae90d7c74935d42db5af07c34ce36f8` |

The 08E checkpoint explicitly accepts seven displayed citation relationships for
inventory, transportation scope, regional scenarios and Final-appendix inputs,
while retaining edition and coding limitations. The user acknowledged the Final
appendix limitation and asked to suppress repeated warnings, not erase provenance.
The 08F event records “ok split that one and then i accept. next,” conditioned on
a presentation-only split without changing substance. The published version 3
records fulfillment of that condition. These approvals do not approve the new
question above.

The inherited [08E question-version rule](../../tasks/sprint2/08e_review_group_evidence.md)
states: “Question changes require explicit approval and a new version bound to its
reviewed evidence.” Its review instructions also require renewed approval
for changed versions. Therefore display the exact proposed question and record
its approval before activating a changed-question condition. Preserve the current
question, reference and sealed scores unchanged; any later publication or run
must bind the approved new question to fresh identities. This is the existing
approval boundary, not an additional policy imposed by this proposal.
