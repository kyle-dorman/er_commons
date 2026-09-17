# Task 05G: diagnosis of 14 specific appendix nonlinks

Diagnosis only, from accepted response records and selected canonical JSON/JSONL.
No PDF/image/model access, extraction, resolver replay or target/rule changes.
These records all capture an outer appendix label with requested type `document`.
The guard blocks a generic document link when nearby text signals a more specific
reference. It does not parse and resolve that compound reference.

The fourteen comprise **seven references with existing relevant indexed inner
targets, six page/figure/table representation or alias gaps, and one false
positive**. Existing targets still require scoped context-resolution rules;
these counts are not promised link gains or acceptance decisions.

## Six inherited cases

| Response | Inner reference | Diagnosis and selected evidence |
| --- | --- | --- |
| M-OSEC-112 | Appendix A, Chapter 08 Public Facilities Financing | Existing section `sec000748`, physical479/480; titled08alias. Compound-context resolver does not select it. |
| M-CSSC-153 | Appendix A, Chapter 06 Circulation | Existing section `sec000446`, physical311/312; titled06alias. Same compound-context limitation. |
| SA-CDFW-9 | Appendix D, page2-21 | Printed page exists at physical37; footer `blk021963`, canonical printed-page label null and no qualified2-21pagealias. Needs explicit page-anchor handling, not whole-document fallback. |
| M-OSEC-190 | Appendix D, Figure3 Habitat Map | Caption text `blk021904`, physical20; figure objects `fig000008/009` have empty caption associations, with no suitable exactfigure3alias. OtherFigure3text elsewhere reinforces need for report scope. |
| M-CSSC-32 | Appendix F.2, Figure4 crossing-guard recommendations | Caption text `blk000131`, physical16; figure objects `fig000017/018` have empty caption associations, with no suitablefigure4alias. |
| O-Joint-74 | Appendix K1, Figure4a groundwater elevation map | Part1 narrative references Figure4a at physical28; nofigure4aalias across fourparts. Caption/target location not established in this bounded diagnosis. Do not claim source figure absent. |

Physical pages above belong to their individual appendix PDFs. Appendix A
chapter identities are the accepted repaired targets; existence does not turn
sampled boundary confirmation into an individual source re-review.

## Eight F1 cases

All below refer to the selected Final F1 substitute, not a proved equivalent
copy of the Draft source. Physical/printed pages refer to Final F1.

| Response | Inner reference | Diagnosis and selected evidence |
| --- | --- | --- |
| SA-Caltrans-9 | San Francisco Municipal Transit (Muni), page29 | Indexed section `sec000034`, physical42/printed29; compound-context limitation. Response expressly revises this content. |
| M-CSSC-94 | Section5 Project Travel Demand | Indexed `sec000064`, physical82/printed69; compound-context limitation. |
| M-CSSC-85 and M-CSSC-126 (2) | AppendixF inside F1, Bayshore Mobility Study | Indexed `sec000634`, physical682; requires nested-appendix resolution, not genericF1 or unrelatedouterAppendixF. |
| SA-Caltrans-6 | Table5 parking maximums by district | Indexed `tbl000008`, physical27/printed14, Maximum Off-Street Parking Spaces per Zone. FourTable5titles occur in F1, so number alone is insufficient; title/context must scope it. |
| SA-Caltrans-6 | Table6 Maximum Off-Street Parking Spaces per Building Type | Extracted `tbl000009` at physical27/printed14, but title is indexed as section `sec000019`/block`blk000359`; tablecaptionlink/alias missing. Response expressly revises this content. |
| SA-Caltrans-8 | TableC-8 inside AppendixC | Extracted `tbl000644`, physical494, caption`blk003918`, Mode Share Comparisons; noC-8alias orcaptionlink. |
| M-OSEC-94 | F1 transportation assessment as a whole | False-positive guard: ordinary words “that table are also included” match `table a`. No attached innerF1identifier is established by that phrase. |

F1 IDs share extraction prefix
`exv1-04bf7e1f3639a9c8e84e46e1ab09b5c69fac1d7a3f6614150ffaaf6fd6f64d2e`
and source `feir_appendix_f1`. Metadata diagnosis indicates no need for fresh
content extraction for these eight, but any target/alias correction remains
separately scoped work.

## False-positive mechanism

`reference_baseline.py` defines `_INNER_TARGET` as
`\b(?:chapter|figure|page|section|table)\s+[a-z0-9]` (case-insensitive).
It accepts the first letter of an ordinary following word, so “table are”
triggers protection as though it were Table A. In M-OSEC-94, “that table” refers
back to Draft EIR Table7-2 in the previous sentence, not an innerF1table. The
following sentence about Guadalupe Quarry Section2.8.1 is outside the extracted
same-sentence context and is not the trigger. This is a resolver guard defect,
not missing source content. It was diagnosed but not fixed.

## Evidence and limits

The accepted 05D source records provide exact mention spans, response labels
and physical pages. The completed Phase3 comparison provides immutable before/
after membership. Current accepted06Gindex and canonical records supply target
existence and aliases. The companion JSON preserves all14mentionIDs and source
response pages. Source paths are selected through
`configs/brisbane_baylands_2025_feir_task05g_replay_v6.json` and its exact bound
index completion, rather than selecting newest directories.

Retain all F1 substitution warnings, especially Muni and Table6 revised-content
warnings. An existing target does not prove Draft/Final equivalence. Caption or
figure identity does not grant text-only evidence eligibility. No result has
been changed; the user has authorized diagnosis only for this group.
