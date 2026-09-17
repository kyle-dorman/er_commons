# Task 05G: eleven comment-authored exclusions

These are intentional provenance exclusions, not eleven unresolved official
response citations. All eleven mention spans are contained inside accepted
Task 05D comment-unit spans, across ten distinct comments. Text around each
mention agrees with its comment/response boundary, including the footnote in
O-Joint-41. No response misclassification was found in this bounded text audit.

Task 05F's required closures explicitly preserve these eleven references as
`comment_authored_reference_no_official_response_link`; Task 05G inherits that
population. The citations remain inventoried and retain candidate diagnostics.
They are not treated as evidence that the City cited a target in its response.

| Comment | Reference(s) | Mentions | Current target diagnostic |
| --- | --- | ---: | --- |
| SA-CHSRA-10 | Chapter 3 | 1 | One compatible indexed target |
| SA-CHSRA-12 | Section 4.8; Section 4.8.6 | 2 | One target each |
| SA-CHSRA-23 | Chapter 7 | 1 | One target |
| RA-LAFCo-2 | “Chapter 4.16” | 1 | No exact chapter target |
| RA-LAFCo-5 | “Chapter 4.16” | 1 | No exact chapter target |
| RA-LAFCo-6 | “Chapter 4.16” | 1 | No exact chapter target |
| M-OSEC-187 | Chapter 3 | 1 | One target |
| M-OSEC-234 | Section 4.9 | 1 | One target |
| O-Joint-41 | Table 4.9-14, in footnote 49 | 1 | One target |
| O-Joint-59 | Section 5.1 | 1 | One target |

Eight mentions already have a unique compatible target. Exclusion is based on
who authored the reference, regardless of target availability. These eight are
not automatically ready for some future comment-link inventory: contextual
specificity, such as SA-CHSRA-12's Threshold TRA-2 or M-OSEC-187's figure discussion,
would still require its own policy and review.

The three LAFCo comments concern water, sewer and recycled water respectively.
Each calls Utilities, Service Systems and Water Supply “Chapter 4.16.” The
canonical section exists as `sec002097`, titled “4.16 UTILITIES, SERVICE SYSTEMS,
AND WATER SUPPLY.” Its full-heading alias does not supply an exact chapter4.16
match. The current matcher preserves the chapter designation; it does not silently
reinterpret it as a section. Their author-based exclusion takes precedence over
target absence, so the headline nonlink reason remains identical to the other
eight. Correcting label terminology would not make these official-response links.

O-Joint-41 is a useful boundary check: the table reference is in the comment's
footnote, immediately before the response. The response says that the comment
quotes the Draft EIR; it does not transform the quoted comment citation into an
independently authored response citation.

No repair is needed under the accepted Task 05F/05G scope. A future comment-to-
source navigation feature should use an explicitly separate relation preserving
comment authorship; it must not relabel these as official-response citations.
This diagnosis used existing JSON/JSONL only. No PDFs/images/models, extraction,
replay or accepted-artifact changes occurred. The current result remains
468 links and 43 explicit nonlinks. Exact mention IDs, pages, candidate IDs and
input bindings are in the [companion JSON](task05g_comment_exclusions_diagnosis.json).
