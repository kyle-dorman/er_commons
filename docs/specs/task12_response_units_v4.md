# Response units and citation occurrences

User-approved correction to Task 12 complexity reporting, before Task 13.
This supersedes the v1 complexity definition that required parent sections for
tables. Model outcomes, judge labels and citation precision/recall/F1 are unchanged.

## Counting units

- A **response unit** is one independently citable canonical section, table or
  figure caption. Count distinct canonical identities across the whole answer.
  A table is its own unit; do not collapse it into its containing section.
  Canonical aliases identify one unit. Figure captions count when represented
  as their own canonical units; do not infer new units from text. The current
  frozen citation contract supports section/table identities, so this update
  does not create separately citable figure-caption IDs.
- A **citation occurrence** is each saved citation reference in the answer.
  Reusing a unit in two different point bullets counts twice; repeats in the same
  field also remain separate saved occurrences. Include conclusion, support,
  qualifications and optional context references.
- Export resolved, invalid, ambiguous and unavailable citation occurrences
  separately. Invalid references count as attempted occurrences but do not invent
  response units or documents. Unextractable malformed fields are not citation
  references: the total stays unavailable, with known observed occurrences
  retained as a lower bound and missing fields counted explicitly.
- A **document** is a distinct source ID among resolved cited units.
- Supplied input response units are a separate covariate, not a retrieval result.
  The evidence-only condition does not claim actual search responses occurred.

For example, citing section A in two bullets and table B in a third gives
**3 citation occurrences and 2 distinct response units**. If both belong to the
same document, the document count is 1. No table-parent mapping is needed.

The Luna descriptive chart uses citation occurrences, distinct response units,
and distinct documents, with the existing bins and denominators. Per-answer
counts retain exact model, run, candidate, question and repeat identities.
Section/table/figure-caption subtype counts are descriptive only.

Returned-citation precision/recall/F1 continue to use distinct canonical units:
repeating a citation neither improves recall nor weights precision more heavily.
Context units remain optional and neutral under the existing matching rules.

## Publication and handoff

The review exporter verifies the original sealed report and derives these counts
from its saved canonical units and citation attempts, without model calls or
source-content inspection. A new `answer_complexity.csv` accompanies the revised
complexity table and chart. The current final-only review folder remains
`task_12/development_19_review/`; previous review versions and the original sealed
publication remain preserved separately. The adjacent provenance binds the new
implementation and outputs.

Task 13 must reuse these definitions for its separate 30-test-question report.
Tasks 13–15 remain provisional. This correction requires no new answers, judge
calls, label changes or locked/reserved-content inspection.
