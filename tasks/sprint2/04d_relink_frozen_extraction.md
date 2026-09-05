# Task 04D: Relink the Frozen Extraction

Status: **complete on 2026-09-04; Gates A through D passed; the replacement
handoff is designated for downstream use; R7/R7a, figure linking, and the
remaining 150 reviewed entries are deferred**.

## Abstract

Replace Task 03J's machine linking result without rerunning or changing its
accepted extraction. Task 04C showed that conservative, source-general linking
rules can recover valid navigation links from existing body headings, target
aliases, and printed-page evidence. It also exposed unresolved classes that
must be inspected individually rather than handled by one broad heuristic.

Task 04D will evaluate one candidate linking rule at a time, record its complete
corpus effect and negative controls, and accept only precision-preserving rules.
It will also replace the duplicated Task 04C reconciliation implementation with
one maintained exact local target-resolution engine shared by the machine
linker and overlay. The two callers retain their own source parsing and output
schemas, but they may not implement competing candidate-selection rules.
After the rule set is explicitly accepted, a fresh machine identity will reuse
the sealed Task 03J extraction through target/alias construction, rerun the
linking stage, and replay only the downstream publications whose identities
depend on linking. Task 03J, Task 04A, and Task 04C remain immutable evidence.

## Goal

1. Identify source-general improvements to document linking one inspection at
   a time.
2. Require inspectable source and target evidence for every newly resolved
   link and preserve ambiguity instead of guessing.
3. Publish a fresh machine candidate that replaces Task 03J for downstream use
   while retaining Task 03J's accepted extraction unchanged.
4. Rebuild only linking-dependent document and collection records under fresh,
   deterministic identities.
5. Make the original machine linker and navigation overlay adapters over the
   same exact local target-resolution engine.

## Inputs

- Task 03J's sealed 35-source extraction, semantic structure, printed-page
  aliases, target aliases, unresolved link records, document candidates, and
  collection handoff;
- Task 04A's accepted TOC decisions and source-usability freeze;
- Task 04C's accepted semantic view, Docling-text TOC projection, entry
  reconciliations, 28 added links, unresolved outcome classes, and exact
  validation evidence; and
- the maintained document-local and collection-linking implementations,
  schemas, policies, and focused fixtures.

No superseded Task 03H candidate, browser-local state, or unsealed development
publication is an eligible input.

## Outputs

- an append-only candidate-rule register with one inspection record per rule;
- complete before/after outcome accounting and review samples for each proposed
  rule, including collisions and negative controls;
- an accepted linking policy and focused tests only after rule-level review;
- a dependency-neutral shared resolver owned by
  `document_records.document_references`, with thin machine-mention and
  navigation-overlay adapters;
- a fresh link-stage identity and fresh linked-document publications that reuse
  the sealed extraction inputs;
- replayed document publication, collection accounting/indexing, cross-document
  resolution, and handoff records only where their identities depend on the new
  links; and
- a replacement-candidate comparison proving that extraction content and
  structure are unchanged and that every changed record is linking-dependent.

Large artifacts remain under `ER_COMMONS_DATA_ROOT`; only compact contracts,
schemas, tests, and summaries belong in Git.

## Accepted boundary

- Do not rerun Docling, source parsing, table reconstruction, record mapping,
  hierarchy inference, section mapping, or page-label resolution.
- Task 04D may derive new target aliases from independently eligible existing
  body-side evidence under a separately inspected and accepted rule. A source
  TOC entry or mention may query such an alias but may not create, repair, or
  relabel one.
- Do not mutate Task 03J, Task 04A, or Task 04C artifacts.
- Shared rule logic belongs in `document_records.document_references`; the
  dependency direction is `navigation_overlay -> document_records`, never the
  reverse.
- The replacement must use a reusable package-backed linking stage that can
  consume any conforming canonical document collection. Task 04D may select
  this corpus's sealed identities and compare its migration result, but it may
  not own a Brisbane-specific production linker, hardcoded artifact identity,
  or one-off replay implementation.
- A new rule must be source-general, deterministic, and precision-first. A
  useful-looking example is evidence for inspection, not permission to publish
  the rule.
- A unique exact body target may provide sufficient destination evidence by
  itself. Printed-page evidence is corroboration or disambiguation when
  available; it is not automatically mandatory.
- Check in with the user after each inspection and before accepting a rule,
  moving to the next rule, implementing the accepted set, or launching the
  replacement machine run.

## Shared linker design

The shared resolver accepts normalized target candidates, their supporting
alias IDs, their physical page IDs, optional destination-page candidates, and
the authorized match basis. It owns:

- exact typed alias matching;
- aggregation and deduplication by target ID;
- optional target-page/destination-page intersection;
- deterministic candidate ordering; and
- neutral zero/one/many outcomes and reasons.

The shared resolver does not parse prose or TOC text and does not serialize
canonical or overlay records. The original linker keeps body-block eligibility,
mention detection, table-window rules, cross-document fallback, and canonical
record construction. The overlay keeps Docling-text TOC parsing, effective
navigation semantics, and overlay publication. Each adapter converts its input
to the same shared query and converts the shared decision to its own schema.

The current implementations already diverge on alias cardinality. The original
linker groups multiple aliases that name the same target into one candidate;
the overlay can reject that same unique target when more than one alias ID
supports it. The shared engine must preserve the original target-ID cardinality
rule: alias rows are evidence, not separate destination candidates.

## Candidate-rule register

### R1: intersect target and printed-page candidate sets

Status: **accepted and implemented source-free; not yet published**.

When marker/title lookup or printed-page lookup produces multiple candidates,
intersect the candidate target pages and resolve only when exactly one eligible
body target remains. Task 04C recovered 21 links through this evidence
intersection without invalidating an alias or existing link, including 11 of
18 entries that originally matched multiple body targets. Task 04D must verify
the rule against the complete original-linking population before promotion.
After promotion, both the machine and overlay adapters must receive this
behavior from the shared resolver rather than carrying separate copies.

### R2: exact full-heading match without a printed page

Status: **accepted and implemented source-free; not yet published**.

Normalize the complete TOC entry and an eligible body-heading alias, including
its section marker and title. If the complete normalized heading resolves to
exactly one body target, allow that unique target to support a link even when
the TOC omits a printed destination page. A printed page, when present, must
remain consistent and can disambiguate collisions.

The motivating example is Appendix A's TOC entry
`0.4.1 Expression of Unique Natural Settings`. The sealed linked extraction
contains the body heading `0.4.1 EXPRESSION OF UNIQUE NATURAL SETTINGS` and a
unique full-heading target alias on physical page 22, but Task 04C stopped at
the missing terminal-page check and looked up only marker `0.4.1`.

Inspection 1 must determine:

1. how many TOC entries match exactly one full body-heading alias after the
   existing normalization policy;
2. how many have zero or multiple matches, and why;
3. whether any unique textual match conflicts with available printed-page
   evidence;
4. whether matching is confined to eligible body headings and excludes TOC,
   furniture, reference lists, captions, tables, and mentions; and
5. the exact new-link set and a representative control sample before the rule
   can be accepted.

The complete 89-entry no-terminal-page population contains 87 Appendix A
section entries and two `deir_main` figure entries. Exact normalized
full-heading matching uniquely resolves 64 of the 87 section entries, with no
ambiguous exact matches. Twenty-three section entries have no exact full-heading
match. Of those, 16 have one unique numeric-marker target but differing title
text, and seven correspond to unique body headings prefixed with `GOAL` rather
than beginning directly with the numeric marker. The marker-only set includes
one substantive title conflict: TOC `3.3.4 Active Ground Floor Uses` versus body
`3.3.4 OBJECTIVE DEVELOPMENT STANDARDS`; a unique marker alone is therefore not
yet accepted as sufficient evidence without a page or compatible title.

The two figure entries are `Figure ES-1: Regional Location ES-2` and
`Figure ES-2: Proposed Land Use ES-4`. Their `ES-*` terminal tokens were not
recognized by the TOC parser, and Task 03J contains no eligible figure aliases,
so page-token parsing alone would not make either linkable.

### R2a: strict `GOAL <marker>:` structural fallback

Status: **accepted and implemented source-free; not yet published**.

After an exact full-heading miss, permit a body alias shaped exactly
`GOAL <decimal marker>: <title>` to derive `<marker> <title>`. Across all 35
sealed Task 03J section-alias streams, 11 aliases satisfy this grammar, all in
Appendix A. Each derived key names one target, no derived keys merge, and none
collides with an existing exact section key.

Using only the current normalization, this rule resolves three of the seven
known GOAL cases: `2.2.3`, `2.2.4`, and `3.2.3`. The other four require separate
typographic handling: two split-ligature repairs, one terminal-period tolerance,
and one curly/straight-apostrophe plus terminal-period tolerance. These four are
not credited to the structural GOAL rule alone.

### R2b: discrete mechanical-title fallbacks

Status: **six narrow transforms accepted and implemented source-free; not yet
published**.

Of the 16 no-terminal-page sections with one numeric-marker target but
non-identical titles, nine can be made exact through six discrete transforms:

- ignore one terminal period: one entry;
- map standalone `&` to `and`: one entry;
- treat an alphabetic hyphen as a word separator: one entry;
- ignore whitespace adjacent to `/`: two entries;
- repair the observed split-ligature form such as `traffi c` -> `traffic`:
  three entries; and
- ignore an optional comma immediately before `and`: one entry.

Each transform must be exact-first, zero-match-only, target-ID deduplicated, and
cardinality-one. Corpus-wide alias inspection found pre-existing distinct-key
merges for every transform except the ligature repair, so none is safe as a
global canonical normalization.

Six title differences remain unresolved by design: source typo `Stuctures`,
the substantive `Active Ground Floor Uses` versus `OBJECTIVE DEVELOPMENT
STANDARDS` conflict, three singular/plural differences, and the duplicated or
different `Sustainability Sustainable Infrastructure` wording. Broad stemming
is rejected because its corpus-wide trial merged 31 groups and every group had
multiple targets.

The remaining `1.4 ... Consistency 36yy y` row is not a title-normalization
case. Its source TOC supplies printed page `36`; it belongs to a separately
inspected terminal-destination parsing rule.

The user accepted all six transforms above plus the strict GOAL-prefix rule and
the explicitly combined curly/straight-apostrophe plus terminal-period rule.
The implementation tries the base exact comparison first. Only after a complete
exact miss does it evaluate each authorized whole-string equivalence, union all
supporting evidence, deduplicate by target ID, and require cardinality one. This
prevents rule order from hiding a conflict. The GOAL projection may compose with
one accepted mechanical rule, which recovers the typographically different GOAL
headings without turning `GOAL` removal into a broad text rewrite.

The apostrophe-plus-period corpus audit covered 19,457 sealed section-alias rows.
It merged nine previously distinct-key groups, six of which named multiple
targets. It is therefore safe only under the same exact-first, fallback-only,
target-deduplicated, fail-closed policy; it is not a global normalization.

The complete 87-entry Appendix A no-terminal-page replay now has 80 unique and
seven zero-candidate outcomes, compared with 64 unique and 23 zero candidates
under base exact matching. The 16 additions are exactly the nine accepted
mechanical-title cases plus all seven GOAL cases. No existing exact result
changed and no new ambiguous result was created. The seven remaining zeros are
the six deliberately unsupported typo, plural, or conflicting-wording cases and
the separately owned `36yy y` terminal-page parser case.

Parent scoping is implemented as an optional exact candidate constraint in the
shared resolver, but it is not activated for these 16 unique full-heading
matches. Canonical body sections already expose direct parents; the current TOC
projection does not yet expose a validated parent-entry relation. Parent scope
must therefore wait for the explicit effective-TOC relation required by R4 and
must never infer a parent from the preceding row alone.

### Observed but not yet scheduled rules

The current evidence also contains possible grammar or target-policy gaps for
`Chapter 3` markers and hyphenated printed-page tokens such as `ES-2`. These are
observations only. Add at most one as the next inspection after the current
inspection is reviewed and accepted.

### R3: exact lettered full-heading lookup

Status: **accepted and implemented source-free; not yet published**.

The accepted Task 04C population contains 112 lowercase lettered entries from
`a.` through `q.`, all in `deir_main`; no other accepted source contains this
failure form. Preserve the letter as part of the normalized lookup key. Exact
matching of the full child heading, including the letter and excluding the
terminal page token, produces 72 unique body targets, 30 repeated targets, and
10 zero matches. Bare-title matching performs materially worse and is not a
candidate rule.

The 10 zero matches comprise nine mechanical extraction/normalization
differences, including hyphen spacing and one `Roundhouse67` contamination,
plus one substantive wording difference (`Threshold UTL-1` in the TOC versus
`Impact UTL-1` in the body). R3 does not authorize fuzzy repair of these rows.

### R4: constrain a lettered child by its resolved parent

Status: **accepted and implemented source-free with its explicit continuation
dependency; not yet published**.

The 112 entries form 35 lettered runs. Geometry places every lettered row one
indent below its numbered parent. Thirty-four parents are present in the
accepted Task 04C text projection and each marker resolves to exactly one body
target. The remaining run begins with a page-continuation `d.` entry; its unique
`4.14.3 Regulatory Context for Baylands Development` parent is recoverable only
by joining the newly reconstructed page to the existing canonical TOC view.
All 35 parents are therefore target-resolvable in the combined effective TOC,
although none currently has usable printed-page alias evidence.

For the 30 repeated exact child headings, explicit parent-child hierarchy makes
28 unique using only parents present in the Task 04C projection. Recovering the
one continuation parent from the combined effective TOC makes 29 unique. R3 and
R4 together would therefore identify 101 of the 112 lettered entries. The
remaining 11 are the 10 zero exact matches plus one hierarchy mismatch:
`d. City of Brisbane Plans, Ordinances, and Regulations` under `4.3.3` has 11
global exact targets, but the intended target is attached below a spurious
intermediate heading rather than directly to the resolved parent.

R4 must not silently assume that the preceding accepted overlay entry is the
parent. It requires an explicit effective-TOC parent relation that spans
existing canonical TOC content and newly reconstructed TOC pages, followed by
an exact parent/child hierarchy check in the body target graph. Hierarchy noise
or missing continuation context remains unresolved.

### R5: conservative ASCII-hyphen whitespace fallback

Status: **accepted and implemented source-free after corpus collision review;
not yet published**.

Preserve the current NFC, NBSP, ASCII-whitespace, and case-folded exact lookup
as the first attempt. Only when that exact lookup produces zero targets, retry
with ASCII whitespace immediately adjacent to `-` removed on both the query and
alias keys. The fallback remains subject to target-ID deduplication, parent
scope when applicable, and zero/one/many fail-closed resolution.

For the ten R3 zero-match lettered entries, this fallback recovers exactly
eight unique targets: `GP-1-18`, `On-Site`/`Off-Site`, `HWQ-4` including
`Rise-Induced`, `Non-Hazardous`, `UTL-2`, `UTL-3`, `UTL-4`, and
`Nine-County`. It intentionally does not match the OCR-contaminated
`Roundhouse67` heading or reinterpret `Threshold UTL-1` as the differently
worded body heading `Impact UTL-1`.

Across all 35 sealed Task 03J section-alias streams, hyphen normalization merges
35 groups of previously distinct exact keys. Twenty-seven groups name the same
target. Eight groups contain multiple targets and therefore remain ambiguous.
Using the normalization only as a zero-match fallback prevents changes to
existing exact matches; a fallback collision never resolves by normalization
alone.

A global replacement of the base normalization would make seven formerly
unique exact keys ambiguous, so that design is rejected. The fallback changes
the lettered-entry exact-match counts from 72 unique, 30 repeated, and 10 zero
to 80 unique, 30 repeated, and two zero. `HWQ-4` is one of the eight recovered
unique headings, but its extracted body hierarchy has a spurious immediate
parent; it can resolve under R3 plus R5 and must not be presented as R4
parent-corroborated evidence.

The user accepted R5 on 2026-09-04 as part of the final Gate A policy. It must
remain exact-first, zero-match-only, target-ID deduplicated, parent-scoped when
applicable, and fail closed on every multi-target result. Acceptance does not
authorize publication.

### R6: derive table targets from body-caption evidence

Status: **accepted and implemented source-free after a corpus trial; not yet
published**.

The complete accepted Task 04C `no_target_alias` population contains 120 rows.
They are one coherent class: all come from `deir_main`, all are List of Tables
entries, all have one recognized table marker and a terminal printed-page
token, and all 120 markers are distinct. The sealed `deir_main` alias stream
contains 2,176 section aliases, 34 printed-page aliases, and one document
alias, but no table aliases. Its 516 canonical tables also all have empty
`caption_block_ids`. This population therefore exposes a target-construction
and caption-association gap rather than an ordinary local-linker miss.

Every source marker has at least one eligible non-navigation body caption or
heading. The current whole-string normalization matches none because the body
systematically renders marker spacing such as `Table 4.5 -2f`, while the List
of Tables uses `Table 4.5-2f`. Removing whitespace adjacent to the marker
hyphen yields 104 full-caption matches: 102 unique and two duplicated between
the Executive Summary and Chapter 4.9. Fifteen of the remaining captions have
narrow mechanical title differences. `Table 4.11-4` is corrupt on both sides
and is not eligible for title repair. Marker-only lookup is unique for 118
rows, but it is not accepted as a broad substitute for caption evidence; the
two duplicated `4.9` markers require explicit parent scope.

The initial same-page/same-section census divided the 120 rows as follows:

- 92 captions can be associated with exactly one same-page, same-section table
  after the two duplicated `4.9` captions are constrained to their resolved
  Chapter 4.9 parent;
- four captions form two-caption/two-table pairs on one page and within one
  section (`4.8-11`/`4.8-12` and `4.10-7`/`4.10-8`);
- 13 visual-simulation entries (`4.5-2f` through `4.5-2r`) have figures rather
  than canonical table targets;
- ten Chapter 9 significance-comparison entries have no canonical table entity
  on the caption page; and
- `9-10` has a page-local table assigned to the preceding section, so the
  page/section association correctly fails closed.

The approved source-free trial added canonical page order and geometry as
independent association evidence. A body caption or heading qualifies only
when its immediately following canonical page item is a same-page,
same-section table directly below it with positive horizontal overlap. This
stricter rule confirms all 92 initial associations and uniquely pairs the four
two-table cases, yielding 96 defensible table targets. All 96 have the table
immediately after the caption; the vertical gaps are 4.78 through 7.84 PDF
points and the tables fully overlap their captions horizontally. `9-10`
remains excluded: its caption-page table is above the caption and owned by the
preceding section, while the next-page fragment conflicts with the List of
Tables destination page.

Across all 35 frozen documents, with Task 04C effective-navigation exclusions,
the strict rule finds 445 caption-to-table evidence edges in 15 documents. As
marker-only aliases these produce 358 keys: 334 unique and 24 multi-target.
Ten marker keys also collide with existing table aliases that point to
different targets. Marker-only alias generation is therefore rejected.

Using the complete normalized body caption as the alias produces 377 keys: 362
unique and 15 multi-target, with zero overlap with existing table aliases. The
three adjacent pairs rejected only by geometry have 0.43 through 1.25 point
vertical overlaps; the trial leaves them out rather than introducing an
unreviewed tolerance. Same-spelling section aliases remain type-separated and
are not invalidated.

Applied back to the 120 List of Tables entries, exact full-caption lookup gives
76 unique results and two duplicated `4.9` results that explicit parent scope
can resolve, for 78 links. Eighteen of the other defensible table targets have
caption-text differences requiring separately inspected mechanical rules. The
remaining 24 have no eligible table association under R6 and stay unresolved.

Twenty-three captions were parsed as headings and already expose unique section
aliases after marker-spacing normalization. Mapping a table-list entry to a
section target would recover those rows without constructing table aliases,
but it would introduce a cross-target-type exception and inconsistent link
semantics. It is an alternative policy candidate, not evidence that the table
target problem is solved.

Printed-page intersection cannot resolve this class under the frozen inputs.
The only 34 `deir_main` printed-page aliases are roman front matter; none of the
120 body labels such as `4.5-38`, `7-54`, or `9-70` has a page alias.

The source-general remediation is therefore the strict adjacency and geometry
rule above, publishing only unique complete-caption aliases. The user
authorized the source-free corpus trial and amended Task 04D boundary before
accepting R6 on 2026-09-04. Acceptance does not authorize implementation or
publication. The 18 caption-text differences remained a separate inspection
owned by R6a, and the 24 unavailable-table cases remain outside R6.

### R6a: exact-first mechanical fallbacks for complete table captions

Status: **accepted and implemented source-free after corpus collision review;
not yet published**.

The shared fallback engine is applicable to complete table-caption aliases,
but its currently accepted R2b transforms recover none of R6's 18
target-backed exact misses. The existing alphabetic-hyphen rule treats a
hyphen as a word separator; it does not repair Docling whitespace adjacent to
an otherwise retained hyphen. Apostrophe normalization is currently authorized
only when a terminal-period difference is also present, and no accepted rule
removes extraction whitespace before ordinary punctuation or restores an
omitted digit-letter hyphen.

Four discrete, whole-caption, exact-first transforms recover 17 of the 18
misses, each with one target and no union ambiguity:

- remove whitespace immediately adjacent to an internal ASCII hyphen while
  retaining the hyphen: 11 entries, including `non -wetland`, `on -site`,
  `annual -average`, and `GP-1- 18`;
- equate curly and straight apostrophes without requiring a period difference:
  one entry (`Brisbane’s` / `Brisbane's`);
- remove extraction whitespace immediately before a comma: four entries; and
- allow an optional digit-letter hyphen in the caption title: one entry
  (`45-acre` / `45acre`).

The hyphen-whitespace transform is the already inspected R5 behavior applied
to the complete table caption. Across all 445 strict R6 caption-to-table
evidence edges, its exact regular-expression form creates zero distinct-key
merges and recovers all 11 motivating rows uniquely. The other three
transforms, and their combined equivalence graph, likewise create zero
distinct-key merges in the 445-edge corpus audit. Exact-first fallback behavior
preserves all prior exact results and target-ID deduplication remains
fail-closed.

With R6 plus these four fallbacks, 95 of the 120 List of Tables entries resolve
to unique table targets after explicit parent scope for the duplicated `4.9`
captions. `Table 4.11-4` is the only strict-R6 target whose caption still does
not match: source `on-n-site` / `off-f-site` versus body `on -site` /
`offfsite` requires multiple typo repairs and remains unresolved. The other 24
entries still lack an eligible R6 table association.

The user accepted R6 and all four R6a fallbacks on 2026-09-04. Acceptance does
not authorize the replacement publication run.

### R7: derive printed-page aliases from body footer evidence

Status: **deferred at Gate A; not accepted, implemented, or published**.

The 112 entries described as lacking one unique printed-page destination are
one coherent population: all are lowercase lettered children in `deir_main`,
all currently have `unsupported_entry_shape`, and all already expose a parsed
terminal destination token. Sixty-six tokens have `N.N-N` form and 46 have
`N-N` form. The 112 rows contain 94 distinct tokens and do not overlap R6's
120 table-alias failures.

The frozen canonical page-label family does not represent these destinations:
`deir_main` has only 34 resolved roman front-matter aliases. Frozen Docling
body-furniture blocks nevertheless retain the printed footers. After the
existing literal-dot/hyphen separator-spacing normalization, exact footer
evidence maps 102 rows, representing 88 distinct tokens, to exactly one
physical page each with zero ambiguity.

The remaining ten rows contain six Chapter 4.17 tokens. Across all 30 pages in
that chapter, Docling systematically rendered the footer sequence
`4.17-1` through `4.17-30` as `4.1771` through `4.17730`. Every affected page
has an independent `4.17 . Public Services and Facilities` page header; the
preceding page closes Chapter 4.16 and the following page starts Chapter 4.18.
A narrow header-conditioned repair therefore reconstructs the missing
separator without using the source TOC claim. It maps all ten remaining rows
uniquely and is a separate R7a subrule rather than part of general page-label
normalization.

As a `deir_main` control, 2,020 ordinary normalized numeric/chapter footers,
the 30 repaired Chapter 4.17 footers, and 34 existing roman labels together
identify 2,084 of 2,092 physical pages one-to-one with zero normalized-label
collisions. Eight physical pages remain unlabeled and are not inferred.

The 35-document control shows why separator-spacing normalization must remain
exact-first and cardinality-one rather than becoming global canonical
normalization. Its projection covers 29,763 exact footer keys and merges 34
previously distinct-key groups; every merged group spans multiple physical
pages and therefore remains ambiguous. The `4.177N` anomaly occurs exactly 30
times corpus-wide, all within the one contiguous `deir_main` Chapter 4.17 run.
No global character substitution or one document-wide physical-page offset is
authorized.

Intersecting the resulting page evidence with the lettered-heading candidates
produces:

- 72 exact unique headings whose target page agrees;
- all 30 repeated exact headings reduced to exactly one page-consistent target;
- eight unique R5 hyphen-spacing fallback headings whose target page agrees;
  and
- two rows with no body-heading candidate, `o. Restoration of the Historic
  Roundhouse` and `a. Threshold UTL-1: Water Supply`, which page evidence does
  not turn into targets.

R7 plus R7a would therefore supply all 112 unique printed-page destinations
and support 110 unique links when combined with exact/R5 heading evidence.
This includes the one repeated heading whose noisy body hierarchy prevented R4
parent scoping. When a page destination is available, R4 parent scope becomes
corroboration rather than a requirement for these 30 repeated headings. The two
zero-heading rows remain unresolved. If accepted, R7 must publish derived
printed-page aliases from independently eligible footer and header evidence;
it must not change canonical page-label observations or derive a page alias
from TOC text alone.

## Gate A outcome: accepted policy and full TOC sweep

The complete 560-entry accepted Task 04C TOC population was re-accounted on
2026-09-04 without publishing a replacement and with all R7/R7a page-alias
work held aside. The currently published Task 04C result remains 28 linked
entries. Applying the accepted R1-through-R6a policy, including R5, projects
410 linked and 150 unresolved entries: 382 additions over Task 04C without an
extraction change.

The 410-entry projection comprises mutually exclusive populations:

- 28 existing Task 04C links;
- 80 of 87 Appendix A no-terminal-page sections through R2/R2a/R2b;
- 109 of 112 lettered children through R3/R4/R5;
- 95 of 120 table entries through R6/R6a; and
- 98 of 108 ordinary destination-bearing numbered sections through compatible
  full-heading evidence: 91 exact, three split-ligature fallbacks, and four R5
  hyphen-spacing fallbacks.

The remaining 150 are fully accounted for: 89 figure entries; 25 table entries
(24 without an eligible canonical table association and one corrupt caption);
ten destination-bearing numbered sections without a compatible full-heading
match; seven Appendix A no-terminal-page sections deliberately unresolved;
three lettered children; 15 unsupported chapter, division, appendix-label, or
integer-dot shapes; and the existing `6.3.4` destination/target-page conflict.

As a regression control, 26 of the 28 existing Task 04C links have the same
unique full-heading target and the other two retain their existing
marker/page-based result. No existing link is invalidated in this projection.
A complete regression proof across the original machine-link population still
requires the integrated replacement replay. R7 would add one further link if
accepted; R7a would add page corroboration but no additional target link.

Gate A closed on 2026-09-04 with the following explicit deferrals:

- R7 and R7a printed-page alias derivation are excluded from the accepted
  replacement policy;
- figure-target construction and figure linking are deferred because the
  frozen extraction exposes no eligible figure targets or aliases, leaving all
  89 figure entries unresolved; and
- all 150 unresolved entries are carried forward as unresolved rather than
  receiving additional parser repair, fuzzy matching, target-type exceptions,
  or source-specific heuristics.

The negative controls remain binding: exact matches run before fallbacks;
candidate rows are deduplicated by target ID; ambiguous or conflicting evidence
fails closed; TOC or mention text cannot generate body aliases; 26 of the 28
existing links select the identical target through full-heading evidence; the
other two retain their existing marker/page resolution; and no existing Task
04C link is invalidated. The mutually exclusive resolved and unresolved classes
account for all 560 entries exactly once. The replacement replay must still
prove these controls over the complete original machine-link population before
publication.

## Research / learning checkpoint

1. Trace each candidate rule through reference detection, target indexing,
   local resolution, linked-document publication, collection indexing, and
   handoff identity.
2. Compare exact normalized alias matching with fuzzy title matching. Preserve
   why exact matching is initially preferred and what evidence would be needed
   before any approximate method could be considered.
3. Document why a printed page is strong corroborating evidence but need not be
   compulsory when a complete heading alias uniquely identifies an eligible
   body target.
4. Confirm the minimal replay boundary from the maintained architecture and
   identity preimages before implementation.
5. Explain the adapter boundary: parsing determines what claim is being linked;
   the shared resolver alone determines which exact target candidates that
   claim can resolve to.

## Plan / gates

### Gate A: inspect and accept rules one at a time

1. Freeze the Task 03J and Task 04C baselines and define complete candidate and
   negative-control populations.
2. Run Inspection 1 for R2 without changing production behavior.
3. Present exact matches, conflicts, unresolved cases, and controls to the user.
4. After explicit acceptance, add R2 to the accepted policy and select no more
   than one next inspection.
5. Repeat until the user closes rule discovery.

Gate A completed on 2026-09-04. R1 through R6a are the accepted policy,
including R5's exact-first ASCII-hyphen whitespace fallback. The accepted
policy projects 410 of 560 TOC entries linked and carries 150 forward
unresolved. R7/R7a, figure linking, and every additional repair for those 150
entries are explicitly deferred. A new bounded inspection and task amendment
are required before a deferred class can re-enter scope. Gate B subsequently
encoded this accepted set and fixed the replacement identity and replay
boundary. No implementation or replacement publication is authorized by Gates
A or B.

### Source-free implementation checkpoint

- `document_records.document_references.exact_resolution` now owns exact typed
  matching, fallback equivalence, target-ID deduplication, optional destination
  intersection, optional explicit-parent scope, and deterministic ordering.
- `document_references.machine_link_resolution` is an experimental adapter for
  existing machine index rows and structural keys. It is not yet connected to
  the production `MentionResolver`; Gate C will integrate it only after Gate B
  specifies the complete policy and evidence mapping. The legacy Task 03J
  resolver remains byte-for-byte unchanged so its historical production
  identity still validates.
- `navigation_overlay.link_resolution` is the TOC adapter. It removes only a
  parser-confirmed terminal destination token, enables the accepted GOAL and
  mechanical policies, and passes optional page or explicit-parent evidence to
  the shared engine.
- `navigation_overlay.task04d_reconciliation` loads eligible body aliases from
  the explicitly selected accepted namespace without changing them and applies
  the new adapter to the complete current 87-entry no-page-section inspection
  population.
  `scripts/audit_task04d_linking.py` exposes that path as a read-only,
  non-publishing exploratory command. Gate B now specifies the checksum-bound
  generic run input that Gate C must implement before any replacement can be
  published; this audit path itself remains unable to publish.
- The Task 04C v1 publisher and schemas remain immutable. They cannot represent
  no-page links or multiple supporting aliases for one deduplicated target, so
  the new adapter is not used to republish or overwrite Task 04C.
- Focused validation passed with 67 tests, plus Ruff and mypy on all changed
  resolver and adapter files. The complete accepted 87-entry population replay
  produced 16 unique additions, zero changed exact results, and zero new
  ambiguities; all 560 accepted TOC entries traversed the integrated reconciler
  without an error. The repository-wide check passed with 1,088 tests.

### Human maintainability checkpoint

A dedicated code-quality pass on 2026-09-04 treated readability, editability,
diagnostics, and ownership as separate requirements from green behavior tests.
It found and corrected four issues in the current Task 04D foundation:

- the shared resolver now decomposes exact matching, named fallback variants,
  parent scope, destination scope, and target grouping into typed helpers rather
  than one nested loop;
- `ExactResolutionDecision` now reports a closed typed outcome plus pre- and
  post-parent-scope text-candidate counts, so adapters can distinguish no text
  match, parent mismatch, destination/target-page mismatch, unique resolution,
  and ambiguity;
- accepted TOC fallback selection moved out of the dependency-neutral core and
  into the navigation adapter, making core mechanism separate from caller
  policy; and
- the Task 04D evidence loader now requires its canonical inputs, validates
  required record fields with path context, retains entity type explicitly
  instead of inferring it from ID spelling, orders evidence deterministically,
  and exposes an immutable destination mapping.

The audit command now identifies its actual 87-entry no-page-section scope,
validates its selected paths, reports the accepted Task 04C identity and input
locations, and gives an actionable error when the artifact root is absent. The
machine adapter is explicitly labeled experimental because production
`MentionResolver` does not call it yet. Focused tests cover staged rejection
reasons, empty versus absent destination scope, order invariance, strict loader
behavior, and adapter-level page conflicts. The live source-free audit retained
the accepted 80 resolved and seven unresolved census.

This checkpoint does not implement the rest of the accepted policy. Gate B
must make R1-through-R6a activation explicit in a versioned policy, including
R5 and R6/R6a. Gate C must connect the machine adapter, retire rather than
extend duplicated Task 04C/Task 04D candidate-loading and selection paths, and
prove adapter equivalence. These are explicit acceptance requirements for the
future implementation, not behavior silently added during the quality pass.

### Gate B: specify the replacement and replay boundary

1. Promote accepted rules into a versioned linking-policy contract.
2. Specify the shared query and decision types plus the two adapter mappings.
3. Specify one package-backed production linking stage and input contract that
   accepts arbitrary conforming canonical document publications, a versioned
   linking policy, and an optional reviewed-navigation input. A collection with
   no human review must still run through the same stage using its machine
   navigation evidence.
4. Keep Task 04D orchestration limited to selecting sealed inputs, invoking the
   generic stage, and comparing the migration result. The current hardcoded
   87-entry audit is diagnostic-only and cannot become a production entrypoint.
5. Define a fresh identity rooted in the exact sealed pre-link Task 03J records,
   Task 04A decisions, required Task 04C navigation text/semantics, and the new
   implementation and policy digests.
6. Prove that the planned replay changes only links, explicitly accepted
   derived target aliases, and their linking-dependent descendants, not frozen
   extraction records.
7. Prove portability with generic fixtures containing no Brisbane-specific
   source IDs, artifact IDs, paths, or document titles, including one fixture
   with reviewed navigation and one using machine navigation only.
8. Present the exact run plan and resource scope before execution.

Gate B completed on 2026-09-04 as a source-free specification gate. The
accepted reusable contract is
[`docs/specs/document_linking_v1.md`](../../docs/specs/document_linking_v1.md),
and the closed policy authority is
[`configs/linking_policies/document_linking_v1.json`](../../configs/linking_policies/document_linking_v1.json).
The policy and run-spec schemas live under
`benchmarks/er_bench/schemas/document_linking/v1/`. Generic machine-only and
reviewed-navigation run fixtures plus the required control-case matrix live
under `benchmarks/er_bench/fixtures/document_linking/v1/`.

The chosen replacement receives a fresh production `exv1-` identity rather
than reusing Task 03J's identity. The new preimage binds the sealed base
production identity, link-run contract, accepted policy, owned linker and
publisher code, output schemas, and downstream-only reuse authorization. The
actual link-run specification binds that production recipe, and each linked-
document identity binds the actual run-spec digest. This direction avoids a
checksum cycle between the production recipe and the run that references it.
Final identifiers are deliberately unassigned until Gate C finalizes those
output-affecting bytes.

All 35 successful source documents must be republished through one coherent
linker-policy lineage. For each source, the first five products are reused by
their existing checksums: content parsing, heading evidence, record mapping,
hierarchy inference, and document structure. The linked-document product is
rebuilt, followed by downstream-only document publication and a fresh
collection scope, accounting, target index, cross-document resolution,
handoff, contract bundle, and any report that consumes a rebuilt descendant.
No PDF, Docling, table reconstruction, record mapping, hierarchy, section
mapping, figure extraction, or printed-page stage is rerun, and no document
attempt is allocated.

Gate C must implement one maintained command,
`er-commons documents relink --link-spec <path> --source-id <source-id>`, and
then use the existing collection handoff command with
`document_evidence_mode: downstream_replay_only`. Reviewed navigation is an
optional sealed input to this same path, not a separate production linker.
Gate C must first source-free materialize that generic bundle, whose identity
binds Task 04A decisions and Task 04C semantics/text and owns validated explicit
parent relations; linking then consumes the sealed bundle. The package-owned
`er-commons documents materialize-reviewed-navigation` interface and closed
reviewed-bundle schema prevent that preparation from becoming a Task 04D-only
publisher.
The normal linked-document publication must contain the effective aliases,
ordinary cross-references, navigation entries, explicit parent relations, and
navigation decisions; a detached overlay invisible to collection processing
is not sufficient.

The current code gaps are carried explicitly into Gate C: production
`MentionResolver` is not yet an adapter over the shared resolver; the legacy
table target rule is not accepted R6; three R6a transforms and R5 are not fully
integrated across both callers; the navigation adapter currently limits some
fallbacks to no-page entries; and the Task 04C schema cannot represent the new
link evidence. The hardcoded 87-entry audit remains diagnostic-only. Gate B
does not create a Task 04D-specific publisher or execute a source/model run.
Artifact references declare repository or artifact-root authority, output
schemas have named roles, source/candidate and CPU limits have explicit runtime
invariants, and the policy separately maps ordinary-machine and effective-
navigation adapters while encoding the accepted GOAL-plus-mechanical
composition.
The three new schemas, four generic fixtures, and accepted policy validate in
six focused contract tests. Repository-wide validation passes Ruff formatting,
Ruff lint, mypy, and all 1,158 tests; `git diff --check` also passes.

### Gate C: implement and validate source-free

Implement the shared resolver, adapt both callers to it, and remove duplicated
candidate-selection policy from the overlay. Run adapter-equivalence tests and
deterministic full-population reconciliation from sealed records. Publish no
replacement machine candidate yet.

Status: **complete on 2026-09-04**.

The maintained implementation now provides both package-backed commands,
shares exact target selection between the ordinary-reference and effective-
navigation adapters, validates every output record family before completion-
last publication, and keeps reviewed navigation optional. The publication and
schema boundary is isolated from the record builder so the production path can
be read and changed without navigating one monolithic module.

The deterministic source-free replay over all 35 sealed Task 03J documents
produced the accepted navigation census exactly: 410 of 560 claims resolved
and 150 remained unresolved. All 28 Task 04C links were independently
reproduced from body alias and destination evidence with zero target
invalidations. The complete ordinary-reference population contained 5,088
decisions: 5,086 were unchanged, two formerly unresolved table references
became uniquely resolved through accepted R6 evidence, and no existing target
changed. The run constructed 468 body-evidence R6 aliases. The
final post-review validation record is retained at
`pipelines/brisbane_baylands/task_04d_gate_c_final_pass1/gate_c_validation.json`
beneath `ER_COMMONS_DATA_ROOT` with SHA-256
`f64e4b36b647b1fac795a37fc23d0e04d509d1a31f56d60c9f3752e1b16c4526`.
The earlier Gate C record remains immutable historical evidence. Two complete
final invocations produced byte-identical evidence; the repeat is retained
under `task_04d_gate_c_final_pass2/`.

The optional reviewed input was materialized twice to the same sealed identity,
`navreviewv1-026b25a7758e2089a4db3fd3630ccf44461be5cfa4fc304d68fc7fabc01d4fae`.
It contains 560 claims, two context-only entries, 114 explicit parent
relations, and 531 effective dispositions for the three reviewed sources. The
checked-in request is `configs/task04d_gate_c_reviewed_navigation.json`; the
generic loader verifies its descriptor, upstream references, managed-file
inventory, and completion seal.

Gate C also prepares a fresh production identity recipe, a 35-source document
publication specification, and a closed link-run specification. The prepared
production identity is
`exv1-466e4e9aced080621fa81058acca95a4e37f1d9a63f2362a569bd9205830b5a3`;
the link-run specification SHA-256 is
`4a232dabf78f5ea1d561bfc7aa69774cb5fd12787b662a11f0bc2e8597fe19ef`;
the exact recipes are
`benchmarks/er_bench/fixtures/document_publication/v5/task04d_production_identity.json`,
`configs/brisbane_baylands_2025_deir_task04d_document_v1.json`, and
`configs/brisbane_baylands_2025_deir_task04d_link_v1.json`. The sealed
downstream collection recipe is
`configs/brisbane_baylands_2025_deir_task04d_collection_v1.json` with SHA-256
`ef2c3788a582d26b7a395a6ef6435030c4b611f126d8e5f2cc6906f8b81c110d`.
These are
configuration artifacts only. Gate C did not invoke the link-run command,
allocate a document attempt, rerun a PDF or model, or publish a replacement
linked-document or collection namespace.

A final pre-publication maintainability pass centralized schema roles and
record-family dispatch, decomposed parent-scope and publication validation,
made specification replacement atomic, and bound Gate C evidence to the exact
run specification, production identity, policy, validation code, and Task 04C
completion. The production-faithful replay also found and fixed two audit
blind spots: reviewed page IDs now cross the prior-linked, structured, and
replacement namespaces explicitly, and the reusable linker replays the v3
verified table-label aliases before adding R6 aliases. Stable record-relative
controls prove that this preserves the 28 navigation links and all existing
ordinary-reference targets across fresh identities.

The final replay also validates every generated linked-record family against
the production output schemas before publication. That check exposed and then
closed legacy-vocabulary omissions for verified table aliases and nullable
navigation fields. Two full validations against the regenerated identity were
byte-identical.

Reproduce the source-free validation with:

```bash
uv run python scripts/validate_task04d_gate_c.py \
  --data-root "$ER_COMMONS_DATA_ROOT" \
  --link-spec configs/brisbane_baylands_2025_deir_task04d_link_v1.json \
  --navigation-root "$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_04_navigation_overlay/navlinkv1-978dbf3f3363eeb4265c75f60efd80bb3995234586e1821f060fe70a9c11bed4" \
  --output "$ER_COMMONS_DATA_ROOT/pipelines/brisbane_baylands/task_04d_gate_c_final_pass1/gate_c_validation.json"
```

### Gate D: run and publish the replacement machine candidate

After separate authorization, publish fresh linked-document and dependent
collection records, validate their complete identity closure, and designate the
new handoff as Task 03J's downstream replacement while retaining Task 03J as
immutable historical evidence.

The maintained Gate D entrypoint is fully sealed by the link specification:

```bash
uv run er-commons collections relink-and-assemble \
  --link-spec configs/brisbane_baylands_2025_deir_task04d_link_v1.json
```

It preflights the downstream-only collection mode, exact document-spec binding,
and ordered source equality before the first write. It then relinks and
downstream-replays every source and assembles the collection only after all 35
documents succeed.

Status: **complete on 2026-09-05**.

The authorized post-review Gate D run completed with exit code 0. It replayed
all 35 documents and published the ready handoff
`handoffv1-e54a72e4bb8f9ba34888c1fc1f51424c4cc52e5f24d6700b16b462e3a659b6d1`
under production identity
`exv1-466e4e9aced080621fa81058acca95a4e37f1d9a63f2362a569bd9205830b5a3`
and scope
`scopev1-044b983a5cbafe3852b2ce90ee82ccdd712fc76698ffcc455ad56caaab5b04da`.
The completion record is
`pipelines/brisbane_baylands/task_04d_relinked_v1/document_publications/scopes/scopev1-044b983a5cbafe3852b2ce90ee82ccdd712fc76698ffcc455ad56caaab5b04da/handoffs/handoffv1-e54a72e4bb8f9ba34888c1fc1f51424c4cc52e5f24d6700b16b462e3a659b6d1/records/completion_record.json`
beneath `ER_COMMONS_DATA_ROOT`, with SHA-256
`387a07d62d96e4c5aba6f1f3d51f7f9026719b0d7de1b4eece06bed9fd78bc81`.

The run verified every newly generated linked candidate before downstream
publication. A final metadata-only audit confirmed 35 completion records,
zero unavailable sources, and no blocking reasons without rehashing large
document payloads. All document preservation checks passed, with 468 accepted derived aliases, 100 replayed
verified table aliases, and zero undeclared differences. The reviewed
population reproduced 410 linked and 150 unresolved entries. The generic
machine-only adapter also produced 31 exact, unique links in five other
appendices; all 31 were reviewed after publication and resolve explicit TOC or
list-of-tables text to a same-document section or table target. No fuzzy or
page-only link was introduced.

This handoff is formally designated as Task 03J's downstream replacement for
linking-dependent consumers. Task 03J remains the immutable extraction source,
and Task 04A and Task 04C remain immutable review and superseded overlay
evidence. The designation is external to the machine completion record, so its
contractual `task04_status: not_evaluated` value remains unchanged.
The previously designated `handoffv1-8b80b818e466dcd428cdd64c2ae2781f8899fdf599b86e3fc6209f1ab5251b7f`
remains immutable superseded execution evidence.

## Validation

- exact checksum and identity binding for every reused sealed input;
- one explicit outcome for every inspected candidate;
- complete collision, target-type, page-conflict, and negative-control counts;
- zero fuzzy, substring-only, or page-only links unless a later reviewed rule
  explicitly authorizes them;
- deterministic results under shuffled discovery and repeated execution;
- identical shared decisions from the machine and overlay adapters for
  identical normalized candidate sets, including multiple aliases naming one
  target and page-intersection cases;
- every per-source link-stage identity binds the same shared policy and owned
  implementation digest used by both adapters;
- no writes to Task 03J, Task 04A, or Task 04C;
- extraction records compare byte-for-byte or by their owning sealed digests
  across the replacement boundary, while any target-alias differences equal
  the complete accepted derived-alias set;
- all changed document and collection records are proven linking-dependent;
- focused tests, `make check`, maintainability review, and `git diff --check`
  pass before publication.

## Review pass

- **Precision:** Could the rule resolve a plausible but incorrect same-title,
  TOC, furniture, caption, reference-list, or cross-document match?
- **Coverage:** Is the inspected population complete, including entries without
  printed pages and the inherited unresolved link population?
- **Architecture:** Is the rule implemented in the maintained linking owner,
  with thin input/output adapters and the smallest valid downstream replay
  boundary?
- **Identity and provenance:** Can every new link be reproduced from sealed
  source and target evidence without modifying extraction?
- **Maintainability:** Are the rule, outcome reasons, fixtures, and operator
  workflow understandable without reconstructing this conversation?

## Acceptance criteria

- every promoted rule received its own completed inspection and explicit user
  acceptance;
- the replacement links are at least as precise as the accepted Task 03J links,
  with every added edge supported by unique eligible target evidence;
- no extraction, hierarchy, or page-label output changes, and no target-alias
  changes outside the explicitly accepted derived-alias set;
- the fresh machine candidate and downstream handoff are deterministic,
  complete, and independently validatable; and
- downstream tasks can pin one replacement identity without composing an
  undocumented mix of Task 03J and Task 04C link behavior;
- the production linker is callable through a package-backed, configuration-
  driven interface for a newly extracted conforming document set, with human
  navigation evidence optional rather than required; and
- no production module, input contract, identity function, or test fixture
  depends on a Brisbane-specific source name, Task 03J/04A/04C artifact ID, or
  Task 04D filesystem path.

## Non-goals

- rerunning or repairing extraction, Docling, table reconstruction, hierarchy,
  or page labels, or deriving target aliases from source mentions or TOC text;
- fuzzy semantic matching, embeddings, or LLM-selected links;
- guessing among repeated headings or conflicting page evidence;
- accepting all currently observed parser gaps as one batch;
- maintaining separate machine and overlay copies of target-selection policy;
- retaining the bounded Task 04D audit or any corpus-specific replay script as
  the production linking interface;
- changing the Task 04A human decisions or reopening the 391 rejected TOC
  pages; or
- starting Task 05 or any benchmark authoring, retrieval, or evaluation work.
