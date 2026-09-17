# Task 05G: diagnosis of 19 exact-target nonlinks

Read-only diagnosis of the completed Phase 3 candidate. No new rules, targets,
resolver execution, source rendering, extraction, finalization or acceptance.
All 19 already had the same terminal reason in accepted 05F. They route to
`deir_main` and have zero exact global/source candidate options. Nineteen
mentions collapse to six distinct labels; absence here means absence of a
qualified exact target, not necessarily absence of content.

## Findings

| Label | Mentions | Diagnosis |
| --- | ---: | --- |
| Table 4.5-2a | 10 | Composite visual-table target absent; six mentions actually begin an a–r range |
| Table 4.5-2g | 3 | Same composite visual-table target gap |
| Table 4.5-2 | 2 | Unsuffixed family reference; no family target |
| Section 4.8.7a | 2 | Lettered heading text exists but no independent subsection target |
| Section 2.7.2 | 1 | Officially acknowledged citation typo, referenced in a correction discussion |
| Table 9.9-11 | 1 | Strong evidence of a citation typo for Table 4.9-11 |

### Visual simulations: 15 mentions

Main physical pages 601–618 (printed 4.5-33 through 4.5-50) contain the full
Table 4.5-2a–r series. Exact caption blocks for a/g are `blk007552` and
`blk007588`, on physical 601/607 (printed 4.5-33/4.5-39).
Existing/proposed image panels survive as 35 canonical figure records across
those 18 pages; there are no canonical table records on those pages.
Producer routing reports `no_table_route`, complete, with no raw Docling table
regions. This is a representation/target-qualification gap, not a failed table
job or merely whitespace around the hyphen. No visual inspection was performed.

The selected aliases have no matching table targets. Figure 4.5-2 is a different
viewpoint-map target and must not substitute. A future bounded target repair
would need to represent each labeled comparison with its relevant panels,
caption and extent, while keeping target identity separate from text-only
eligibility. No current figure eligibility restriction changes here.

Of these 15 references, seven are specific standalone/list references (four a,
three g), six explicitly say a **through r**, and two use the unsuffixed family.
The range mentions currently record the first target label only. Creating a
single a target would not by itself represent the full range. Family/range
semantics require an explicit design before declaring these all resolvable.

### Section 4.8.7a: two mentions

General Response 3 (Volume 4 physical 44, printed 13-10) and Response M-OSEC-152
(physical 383, printed 13-349) both cite the vehicle-miles-traveled analysis.
Main physical 854, printed 4.8-56, contains `4.8.7 PROJECT IMPACTS AND MITIGATION
MEASURES` (`blk009663`) followed by `a. Threshold TRA-1: Vehicle Miles Traveled`
(`blk009664`). Both belong to parent section `sec001168`; the lettered block is
not an independent child section. The index exposes the parent but no qualified
4.8.7a target. A future specific subsection anchor/extent repair is needed;
linking to all of 4.8.7 would broaden the citation.

### Section 2.7.2: one acknowledged typo

Response M-OSEC-357 (physical 493, printed 13-459) points to M-OSEC-342 regarding
this reference. Its preceding comment identifies 2.5.2 and calls 2.7.2 an error.
Response M-OSEC-342 (physical 486, printed 13-452) explicitly says the 2.7.2 Site
Remediation references on Draft pages 4.13-12/17 are corrected typographical
errors. The actual target `2.5.2 SITE REMEDIATION` already exists at main
physical 273, printed 2-39, `sec000343`. Section 2.7 is Projected Sea Level Rise.

The flattened redline text reads `2.75.2`; its styling was not inspected. The
comment, official typo explanation and existing heading jointly support the
diagnosis. A future correction-aware disposition should preserve the original
erroneous label and correction evidence separately. This mention discusses a
correction; silently treating it as an ordinary direct citation loses context.

### Table 9.9-11: one likely typo

Response M-OSEC-46 (Volume 4 physical 314, printed 13-280) explicitly cites
`Table 9.9-11, page 4.9-69` while describing engine compliance alternatives.
The selected main document at physical 981, printed 4.9-69, has caption
`Table 4.9 -11: Engine Compliance Alternatives` (`blk010661`) and extracted
table `tbl000179`. Its cells match the response's three alternatives: alternative
fuels, Tier 4 Final and Tier 4 Interim. The target is already indexed under
normalized `table 4.9-11: engine compliance alternatives`.

This strongly indicates a wrong leading digit in the response, not a missing
table extraction. Unlike 2.7.2, no explicit official correction was established.
There is also a second indexed copy, `tbl000028`, at physical 113. Merely
changing 9 to 4 would therefore leave two candidates. A future reviewed
correction would need both the citation correction and the supplied page anchor
to identify the physical-981 target. Fuzzy matching or a global digit rewrite
would not be justified.

## Evidence and boundaries

The selected main publication and accepted 05D records were inspected as JSON/
JSONL only. No PDF/image/model access or fresh substantive source review was
performed. Producer metadata supports the visual-table diagnosis but does not
establish image fidelity. All accepted artifacts and the Phase 3 candidate
remain unchanged. No estimated link-gain count is claimed for a future repair.

- [Selected main blocks](/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v38/document_publications/documents/deir_main/docv1-7d28dcdc5411c1239ee5db17328045fc73275afc0bcbc43ba42f853bd9840e7a/content/canonical/blocks.jsonl)
- [Selected main sections](/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v38/document_publications/documents/deir_main/docv1-7d28dcdc5411c1239ee5db17328045fc73275afc0bcbc43ba42f853bd9840e7a/content/canonical/sections.jsonl)
- [Selected main tables](/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v38/document_publications/documents/deir_main/docv1-7d28dcdc5411c1239ee5db17328045fc73275afc0bcbc43ba42f853bd9840e7a/content/canonical/tables.jsonl)
- [Selected target aliases](/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_06_recovery_v1/06g/replay_v38/document_publications/documents/deir_main/docv1-7d28dcdc5411c1239ee5db17328045fc73275afc0bcbc43ba42f853bd9840e7a/content/canonical/target_aliases.jsonl)
- [Accepted response records](/Volumes/x10pro/er_commons/pipelines/brisbane_baylands/task_05_response_inventory/working/05d/revisionv1-857ecbc97cccc24bf18808acffd9d36418f850423b6487cafb78bbaebe26e030/inventory/source_records.jsonl)

## Exact mention accounting

Physical pages below are in Final EIR Volume 4. Mention IDs are preserved in
the companion JSON record.

| Label | Response | Physical page | Scope in response |
| --- | --- | ---: | --- |
| section 2.7.2 | Response M-OSEC-357 | 493 | specific label |
| section 4.8.7a | Response M-OSEC-152 | 383 | specific label |
| section 4.8.7a | GENERAL RESPONSE 3 | 44 | specific label |
| table 4.5-2 | Response SA-Caltrans-24 | 96 | unsuffixed family |
| table 4.5-2 | Response M-CSSC-12 | 202 | unsuffixed family |
| table 4.5-2a | Response PC-CS-4 | 732 | specific label |
| table 4.5-2a | Response M-OSEC-170 | 392 | a–r range |
| table 4.5-2a | Response PC-CS-4 | 731 | a–r range |
| table 4.5-2a | Response I-CJ-6 | 703 | a–r range |
| table 4.5-2a | Response O-YIMBY-5 | 687 | specific label |
| table 4.5-2a | Response O-GA-5 | 586 | specific label |
| table 4.5-2a | Response M-OSEC-169 | 392 | a–r range |
| table 4.5-2a | Response I-CJ-6 | 703 | specific label |
| table 4.5-2a | Response O-YIMBY-5 | 687 | a–r range |
| table 4.5-2a | Response O-GA-5 | 586 | a–r range |
| table 4.5-2g | Response M-CSSC-15 | 205 | specific label |
| table 4.5-2g | Response O-YIMBY-5 | 688 | specific label |
| table 4.5-2g | Response O-GA-5 | 587 | specific label |
| table 9.9-11 | Response M-OSEC-46 | 314 | specific label |

## User disposition

The user accepted leaving all 19 cases nonlinked and requested no fixes at this
time. The visual-simulation series lacks qualified composite targets; image
panel records exist, but were not processed into linkable table/group targets.
This is a disposition of this nonlink group, not acceptance of the entire Task
05G candidate or authorization to change figure evidence eligibility.
