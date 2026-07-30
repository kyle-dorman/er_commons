# Deterministic Hierarchy-Correction Contract v1

Task 03E.1 owns this contract. It specifies an optional, project-owned
enrichment over one completed Docling producer run. It does not change, replace,
or republish producer records, and it does not materialize canonical semantic
sections.

## Boundary and inputs

The overlay accepts only a checksum-verified producer completion and its
inventoried files, the checksum-pinned source PDF named by that completion, and
the checked-in policy, schema, and implementation digests. The source PDF may
be read only to obtain its embedded outline and page-label observations; it is
not converted again. The correction candidate must record the producer run ID,
completion and inventory checksums, source checksum, source-manifest checksum,
policy version/digest, schema digest, and code-bundle digest. RFC 8785 canonical
JSON bytes are hashed for identity inputs.

The producer's `document.json` remains the immutable raw observation. A stable
item key is the existing Task 03E SHA-256 of `{text, orig, prov[0].page_no,
prov[0].bbox, prov[0].charspan}` in canonical JSON. A duplicate key, missing
provenance, unverified completion, malformed outline data that the candidate
uses as an anchor, or schema failure is fatal; the attempt is retained but
never published as complete. A source PDF with no outline is valid and records
an empty outline inventory.

The input inventory is limited to these persisted signals:

| Feature | Source and representation | Missing state |
| --- | --- | --- |
| `stable_item_key`, text, original text | Docling text item | fatal if key inputs missing |
| raw role and raw level | Docling `label` and `level` | level is `null` when absent |
| reading-order index and raw parent ref | body/furniture traversal | fatal if order is invalid |
| content layer and object role | Docling text item/tree | fatal if layer unknown |
| source anchor | first Docling provenance, PDF points, bottom-left | `null` only for an explicitly unanchored non-body item |
| page dimensions | `conversion_pages.json` | fatal if the anchored page is absent |
| local layout evidence | exact normalized-text alignment to one parsed-page line cell, item bbox, line count, left edge, and height | `absent` if no unique aligned cell exists |
| outline evidence | source PDF outline, target page index, normalized title | `absent` if none; `ambiguous` if non-unique |
| printed-page evidence | unique producer `page_footer` token, with source PDF page label retained as secondary evidence | `absent` if no unique footer token exists |
| numbering evidence | frozen regular-expression grammar over normalized raw text | `none` if no grammar matches |

`font_name`, inferred font size, color, raster pixels, OCR reruns, language
models, embeddings, fuzzy semantic similarity, and handwritten document/page/
heading exceptions are not features. In particular, the accepted producer does
not persist stable font metadata for a correction feature. Coordinates remain
unchanged as producer PDF-point decimals. Comparisons of left edges and heights
use absolute PDF-point differences without rounding; persisted derived values
use six decimal places with round-half-even. Text comparison applies Unicode
NFC, maps NBSP to ASCII space, trims, collapses ASCII whitespace, and case-folds.
It does not remove punctuation, numbering, bullets, or diacritics. Raw `text`
and `orig` are retained unchanged.

The body-heading numbering grammar is frozen and matched from the start of
normalized text in this order:

```text
decimal:       ^(?P<token>[0-9]+(?:\.[0-9]+){0,5})\.?[ \t]+
article:       ^(?:Article|ARTICLE)[ \t]+(?P<token>[0-9]+|[IVXLCDM]+)\.?(?:[ \t]|$)
upper-roman:   ^(?P<token>[IVXLCDM]+)\.[ \t]+
upper-alpha:   ^(?P<token>[A-HJ-UW-Z])\.[ \t]+
bullet:        ^(?P<token>[•·▪◦o])(?:[ \t]+|$)
```

Matching is case-sensitive; only the two displayed article literals are
accepted. Roman precedes alpha, and the alpha grammar
excludes Roman single-letter tokens. A decimal marker must contain a period or
be an integer from 1 through 99. This eligibility predicate is applied after
the regular-expression match and rejects year-like bare prefixes. Decimal depth
is the count of numeric components. Within an
article regime, `Article N` is local level 1, `N.nn` is local level 2, and
uppercase alphabetic or Roman raw headings are local level 3. Parenthesized
markers and markers on raw `list_item` records never create headings.

## Artifact layout and ownership

Task 03E.2 writes a new candidate below:

```text
pipelines/brisbane_baylands/task_03e2_hierarchy_correction/<candidate_id>/
  records/identity.json
  records/input_inventory.json
  records/completion_record.json
  artifacts/item_features.jsonl
  artifacts/visible_toc_entries.jsonl
  artifacts/toc_reconciliation.jsonl
  artifacts/regimes.jsonl
  artifacts/decisions.jsonl
  artifacts/hierarchy.json
  artifacts/ambiguities.jsonl
  artifacts/warnings.jsonl
  records/summary.json
  records/metrics.json
  records/artifact_inventory.json
```

All JSONL files are in increasing `reading_order_index` and then stable-key
order; roots and edges are likewise ordered. Publication is atomic, no-clobber,
inventory-sealed, and completion-last. A completed matching candidate is reused
only after every inventoried checksum verifies. Failed attempts preserve an
attempt manifest and error but omit completion.

The overlay owns its features, reconciliation, decisions, corrected roles and
levels, and hierarchy. Docling owns raw text, raw roles/levels, pointers,
reading order, geometry, and content layer. Later Task 03E.3 owns semantic
section records and may consume this overlay only by its immutable completion.

## Visible TOC and reconciliation

A visible-TOC region starts at a body `section_header` whose normalized text
matches `^table of contents(?: \(continued\))?$`. This generic structural
vocabulary is part of the policy, not a document-title exception. A primary
region requires an embedded-outline node with the same normalized title and a
resolved PDF `/D` destination. It ends immediately before the smallest resolved
destination page among later outline siblings with the same parent. An
unresolved destination or absent later sibling is fatal.

A matching `(continued)` heading encountered inside an active TOC region is
part of that region and cannot start an overlapping region. It remains excluded
and row assembly resumes after it. Any other candidate TOC start inside an
active region is `TOC_ROW_UNPARSEABLE`, not a nested region.

Without a usable outline node, an embedded region is scanned forward. Its end
is the start of the earliest later physical page satisfying both conditions:
(a) its unique producer footer changes from a lower-case Roman token in the
region to Arabic token `1`; and (b) before any later TOC leader or page token,
the page contains a raw body heading that matches `article` or top-level
`decimal` and is followed before the next heading by nonempty body content.
The region ends before the first body item on that page, so title and
introductory material preceding the numbered heading are not excluded. If this
transition is absent, the implementation must scan provisional rows and use
the earliest later raw heading whose marker-stripped title exactly matches a
provisionally assembled row title and is followed before the next heading by
nonempty body content. The scan assembles each provisional row as its terminal
page token is observed and tests later headings in reading order; it never
revises an already observed endpoint. If neither
end is proven before document end, `TOC_REGION_UNTERMINATED` is fatal; the
implementation may not exclude the remainder by assumption.

All body items in the region are marked `toc_region=true` even when row assembly
fails. They can never become corrected boundaries or hierarchy members.

TOC token grammars are full-item matches and are distinct from body-prefix
grammars:

```text
row marker:  ^(?:(?:Article|ARTICLE) [0-9IVXLCDM]+\.?|[0-9]+(?:\.[0-9]+){0,5}|Appendix [A-Z])$
leader:      ^\.+$
page token:  ^[A-Za-z]?[0-9]+(?:-[0-9]+)?$
```

Rows are assembled from consecutive region items with this finite-state parser:

1. `start`: treat a row-marker token as a marker only when lookahead finds a
   non-leader, non-page title item before the next marker; otherwise it is a
   page token for the previous row. Then require one title item;
2. `title`: append consecutive non-token title items; a leader token, including
   a single period, enters `leader`;
3. `leader`: consume one or more consecutive leader items, then require one page
   token and emit the row;
4. a new numbering token before a terminal page emits the prior row with
   `printed_page=null`; end-of-region does the same; and
5. a title item containing inseparable trailing digits, two plausible page
   tokens, or an unexpected raw heading emits an ambiguity rather than splitting
   text heuristically.

Every row records all source item keys, anchors, normalized title with and
without its marker, numbering token, depth evidence, printed-page token, and
parser state. Depth evidence is,
in precedence order: a unique exact outline-title depth, numbering depth, then
one. The row itself always has corrected role `excluded`.

The body candidate set contains items after the region through the end of the
outline parent's subtree; without a usable outline parent it extends to document
end. It may therefore cross nested local regimes. Candidate text is split with
the body-prefix numbering grammar.
Rows with a marker require exact marker equality and exact marker-stripped title
equality; unmarked rows require exact marker-stripped title equality. Printed
page compatibility uses a unique producer furniture observation matching
`^Page (?P<label>[A-Za-z]?[0-9]+) of [0-9]+$`, or otherwise the unique
standalone page-footer token matching
`^(?:[ivxlcdm]+|[A-Za-z]?[0-9]+)$`. The captured token must exactly equal the
TOC page token after ASCII case-folding. The source PDF page label is retained
but is not a conflict when it merely exposes the physical page number. Depth compatibility
uses raw outline depth or numbering depth only, never a corrected level:
equality is required when both exist. Body-order monotonicity resets for each
TOC region.

`exact` requires exactly one candidate and all available compatibility checks.
Otherwise the terminal state is selected in this order: `ambiguous` for
multiple candidates, `missing` for zero candidates, `page_conflict`,
`level_conflict`, then `order_conflict`. An `exact` record contains exactly one
candidate and that same non-null target; every other state has a null target.
TOC absence is never negative evidence against a body item.

## Rule policy

Rules inspect immutable raw features and execute in listed order; no rule sees
another rule's correction. The first eligible rule is selected. Its `applied`
or `ambiguous` result is terminal, so later rules never overwrite or bypass
uncertainty. `R08` is always eligible. Each decision records the complete
ordered eligible list, selected rule, evidence, and terminal outcome.

| ID | Eligibility and action |
| --- | --- |
| `R01_EXCLUDE_NON_BODY_OR_TOC` | Any item with `content_layer=furniture` or `toc_region=true` is never a boundary; set role `excluded`, including unparseable TOC items. |
| `R02_DEMOTE_BULLET_HEADING` | For a bullet-prefixed raw section header with no exact outline or TOC anchor, scan on the same page until the next raw heading at the same or shallower raw level or page end. If the segment contains at least one `list_item` whose left edge is at least 18 PDF points farther right, set role `content`; otherwise return terminal ambiguity. |
| `R03_APPLY_EXACT_OUTLINE_ANCHOR` | A unique exact normalized outline title on the same physical page promotes or retains a body item as `heading`. Follow the unique parent chain to its topmost outline ancestor; this is the selected source root. Effective level is `min(6, raw_outline_depth - selected_source_root_depth + 1)`. A missing parent link, multiple matches, or non-unique parent chain is terminal ambiguity. |
| `R04_APPLY_EXACT_TOC_ANCHOR` | A unique `exact` TOC reconciliation promotes or retains its body target as `heading` at reconciled depth, unless R03 already applied. |
| `R05_APPLY_NUMBERING_REGIME` | A body raw heading matching a non-bullet grammar receives level `active_root_level + grammar_depth - 1`. Raw list items and bullet matches are ineligible. Upper-alpha and upper-Roman markers have grammar depth 3 only inside an article regime and are otherwise ineligible. Compare the proposed level with the proposed grammar level of the nearest earlier same-regime raw heading matching an eligible non-bullet grammar; a forward jump greater than one is terminal ambiguity. With no predecessor, only a root-level proposal is allowed. |
| `R06_FLAG_STRUCTURAL_AMBIGUITY` | A raw `text` item matching the structural-sibling pattern is recorded as `content` with terminal ambiguity; it is not automatically promoted because the persisted producer lacks a second independent style signal. Exact outline or TOC anchors in R03/R04 are the only plain-text promotion paths. |
| `R07_TRANSFER_LOCAL_HEADING_LEVEL` | An unsupported heading is an unnumbered raw `section_header` whose raw level is outside 1–6 or jumps by more than one from the evidence-derived level of the nearest earlier supported heading. A supported heading has a unique exact outline anchor, exact TOC reconciliation, or eligible non-bullet numbering level. The maximal cluster is every unsupported unnumbered raw heading after that supported heading and before the next supported heading, with `max(left_pt)-min(left_pt) <= 1`. Require at least two cluster items. Transfer later supported level `L` only when the earlier supported level is `L-1` and every cluster item's left edge is within 1 point of the later supported heading. Otherwise return ambiguity. |
| `R08_DEFAULT_PRESERVE` | Map a body raw `section_header` with integer level 1–6 to `heading`; map every other body raw role to `content`; map furniture to `excluded`. Heading keeps its raw level; `content` and `excluded` have null corrected level. A later hierarchy-continuity failure remains fatal. |

The R06 structural-sibling pattern is: nearest earlier and later raw headings
on the same page share one level and lie within 1 PDF point of the candidate
left edge; immediately preceding and following items are nonempty body text
paragraphs; the candidate aligns to exactly one parsed-page line, has at most
160 characters, and has no bullet, caption, table, furniture, outline conflict,
or TOC-region signal. This pattern only explains the ambiguity; it is not
sufficient evidence for promotion.

Every terminal `ambiguous` decision is fail-closed: body items receive
corrected role `content` and null level, furniture/TOC items remain `excluded`,
and no ambiguous item enters the hierarchy. An R06 ambiguity with no exact
outline or TOC anchor is published as a non-blocking omission because it is
outside the strict navigation hierarchy. Other ambiguity may make quality
acceptance inconclusive when it affects TOC/outline-backed boundaries,
numbering regimes, or hierarchy continuity. Ambiguity never violates hierarchy
construction or forces preservation of an unsupported raw depth.

For R02, both failed demotion evidence and confirmed demotion evidence therefore
remove an unanchored bullet from the hierarchy; the outcome distinguishes
reviewable uncertainty from an automatic correction.

The initial regime starts at the first body item with `root_level=1`. A nested
regime candidate begins after a unique exact outline-anchor item. Ignore
unnumbered title, TOC, and introductory headings; the first later raw heading
matching a non-bullet numbering grammar before the following outline-anchor
item must be `Article 1` or top-level decimal `1`, and the active regime must
already have observed a different top-level marker. An empty active regime
cannot satisfy that condition. The nested regime starts at the matching marker
item, not the outline item, and its `root_level` is one. A page-label reset is
recorded only as supporting evidence.
The regime ends immediately before the next resolved outline sibling at the
same or shallower outline depth, or at document end. Missing end evidence makes
the candidate ambiguous rather than starting a nested regime. Regimes may nest;
the active stack is last-started first. Start/end item keys, outline evidence,
parent regime, and root level are persisted. Rules cannot use a source title,
physical page number, reviewed-case ID, or literal document heading as a
predicate.

## Corrected hierarchy and invariants

Only body items with corrected role `heading` are hierarchy nodes. Construction
uses an open-heading stack per regime. Before a node at level `L`, pop while the
top level is greater than or equal to `L`; the remaining top must be level
`L-1` and becomes the parent. A node at the regime root level requires an empty
stack and becomes a root. Any other empty stack or level gap is fatal. Then push
the node. This prevents attachment across a closed subtree. A parent outside
the regime, cycle, duplicate key, or non-monotone edge is fatal.

Direct membership is exact after a regime's first root: each `content` item
belongs to the current stack top. Content before that first root is recorded
exactly once in `unassigned_content`; it has no invented semantic parent.
Excluded, furniture, and TOC items have neither membership nor an unassigned
entry. The union of direct-membership item keys and `unassigned_content` is
exactly the corrected-content set, and the two sets are disjoint. Forward
parent/child edges and inverse membership agree exactly.

Every item produces one decision, including `unchanged` and `ambiguous`; every
automatic correction records a stable key, raw and corrected values, selected
rule, ordered evidence, and source anchor. Warnings do not repair data.

Fatal invariant codes are frozen as `INPUT_COMPLETION_INVALID`,
`INPUT_INVENTORY_MISMATCH`, `SOURCE_CHECKSUM_MISMATCH`,
`STABLE_KEY_COLLISION`, `UNKNOWN_REFERENCE`, `READING_ORDER_CYCLE`,
`TOC_REGION_UNTERMINATED`, `DECISION_COVERAGE_MISMATCH`,
`CORRECTED_LEVEL_INVALID`, `HIERARCHY_CYCLE`, `HIERARCHY_LEVEL_SKIP`,
`HIERARCHY_ORDER_INVALID`, `MEMBERSHIP_NOT_INVERTIBLE`,
`PUBLICATION_COLLISION`, and `REPEAT_BUILD_MISMATCH`. Warning and ambiguity
codes are `TOC_ROW_UNPARSEABLE`, `TOC_TARGET_MISSING`,
`TOC_TARGET_AMBIGUOUS`, `TOC_PAGE_CONFLICT`, `TOC_LEVEL_CONFLICT`,
`TOC_ORDER_CONFLICT`, `NUMBERING_JUMP_UNSUPPORTED`,
`SIBLING_EVIDENCE_CONFLICT`, `LOCAL_LEVEL_TRANSFER_CONFLICT`, and
`RAW_HEADING_DEPTH_UNSUPPORTED`. Unknown codes fail schema validation.

## Preservation and comparison

The overlay never rewrites a producer file. Before and after execution, Task
03E.2 re-verifies the producer completion and complete inventory and requires
the same checksums. Feature extraction must cover every provenance-bearing
Docling text item exactly once and reproduce its stable key, `text`, `orig`,
raw role, raw level, raw parent, content layer, page, bbox, charspan, and body/
furniture reading-order position exactly. Tables, pictures, groups, routing,
clean tables/cells, table families, figures, assets, warnings, conversion-page
records, and the Task 03D.1 reference candidate are byte- or checksum-equal
inputs, never comparison-normalized outputs.

Permitted differences exist only in new overlay fields: normalized features,
TOC rows/reconciliation, corrected role/level, rule decisions, ambiguity,
warnings, hierarchy edges, and direct membership. Candidate identity, paths,
timestamps, timings, resource measurements, inventory seals, and completion
hashes may differ between independent scratch roots only under the frozen
normalization used for the repeat gate; candidate-owned semantic JSON bytes
must otherwise match exactly.

## Fixtures, review, and Task 03E.2 gate

The tracked `development_cases.json` contains eight checksum- and stable-key-
bound records from the already reviewed failures: two bullet demotions, one
plain-text ambiguity, one local heading-level transfer, one embedded article,
two decimal sections, and one alphabetic subheading. Expected corrected roles,
levels, rule IDs, and outcomes are explicit. These fixtures may guide
implementation and never appear in held-out results.

`held_out_manifest.json` is already frozen. It excludes the 23 Appendix P pages
reviewed in Task 03E, ranks eligible pages by
`sha256(source_sha256 + ':' + unpadded_decimal_physical_page)`, and selects the
first two from each nonempty outline/heading, numbering, appendix-boundary,
table/caption, and furniture stratum. Page 117 is additional development
evidence because the page 120 and 180 numbering cases depend on its regime
reset. The eight unique held-out pages are 73, 82, 96, 105, 131, 155, 166, and
220. No visible-TOC or numbering-reset page can honestly be held out because
all detected examples are development evidence. Those mechanisms use complete
development review plus exact invariant tests, not a mislabeled holdout. After
code and policy digests are frozen, the reviewer annotates source-only renders
before seeing corrected output. Those annotations are checksum-sealed, then the
overlay runs once. No post-review tuning is allowed.

`review.schema.json` freezes the annotation unit as every provenance-bearing
text item on each selected page. `eligible_item_keys` is the complete
reading-order list for that page and must equal the annotation-key set exactly.
Each annotation records expected boundary status, level, parent key, regime
start/end action, and whether the source itself is visually ambiguous.
Non-boundaries have null level and parent. The annotation bundle records the
source, manifest, policy, and code digests and is written to the external
comparison root as `held_out_annotations.json` before corrected output is
shown. Its checksum is the immutable input to `held_out_evaluation.json`.
Any source-ambiguous annotation makes evaluation inconclusive; otherwise any
nonzero error count rejects and all-zero counts pass.

The checked-in comparator joins annotations to decisions by stable key.
Corrected `heading` is the predicted boundary; its level comes from the
decision, its parent from the hierarchy edge, and `start`/`end` from regime
keys. Expected heading plus selected R02 content is `false_demotion`; any other
expected heading predicted as content is `missed_boundary`; unexpected heading
is `false_boundary`; a heading level or parent difference is
`wrong_level_or_parent`; and a regime-action difference is `regime_error`.
The evaluation persists every mismatch, derives aggregate counts from that
list, and hashes the complete annotation bundle. Counts are never accepted as
self-reported evidence.

The manifest freezes each stratum predicate as well as its count and rank:
outline/heading means a body `section_header` at raw level 1 through 5;
numbering means a raw `section_header` matching a non-bullet numbering grammar;
appendix boundary means a raw heading matching case-insensitive
`^Appendix [A-Z]\b`; table/caption means a Docling table provenance entry or raw
table/caption text label; furniture means any text item on the page has
`content_layer=furniture`; numbering-regime reset means the first eligible
Article 1 or decimal 1 after an exact Appendix outline anchor; and visible TOC
uses the exact region-start grammar. A zero-count stratum is retained with its
leakage reason.

Acceptance requires: all eight development cases match their expected role,
level, rule, and outcome; all 29 exact outline anchors and 21 reviewed numbering
relations remain correct; every visible-TOC region item is excluded from
boundaries; every applied demotion, level transfer, TOC promotion, or numbering
change across complete Appendix P and the fixed main controls is included in
the review inventory; held-out review finds no false boundary, false demotion,
missed boundary, wrong level or parent, or regime error; all hierarchy and
preservation gates pass; and independent builds are byte-identical after frozen
measurement normalization. The known page-2000 R06 result is accepted as
non-blocking `content` ambiguity because it has neither an exact outline nor
TOC anchor. Reject on an undeclared producer change, a development-case
mismatch, false TOC boundary, cycle, missing raw correspondence, or any
held-out false boundary, false demotion, missed boundary, wrong level/parent,
or regime error. Stop as inconclusive on unresolved source/feature
availability or a repeated ambiguity pattern affecting the strict navigation
hierarchy and requiring a new policy.

The overlay reports total and per-stage wall time, peak RSS, input bytes, and
artifact bytes. “Cheap relative to producer rebuild” means that both median
fresh overlay wall time over three runs and persisted overlay bytes are less
than the corresponding frozen producer build wall time and inventoried
producer bytes. Peak RSS is reported in bytes but is not compared or gated
because the frozen producer completion did not seal a comparable observation.
Failure of either comparable measure blocks acceptance pending an explicit
follow-up decision; Task 03E.2 may not invent a different post-hoc threshold.

## Learning note

This is an evidence transformation, not an in-place parser repair. Raw Docling
observations remain independently verifiable; project policy adds a separately
versioned interpretation with reasons. An embedded outline and visible TOC are
different evidence: the first may anchor a body heading, while the second is
content that can only reconcile to a target. The deliberately fail-closed policy
trades forced coverage for a traceable, repeatable hierarchy without an LLM or
other learned runtime component.
