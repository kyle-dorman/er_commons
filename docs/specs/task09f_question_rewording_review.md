# Task 09F — Replace the two rebuttal questions

Status: new wording drafted for user review, 2026-10-14. Kyle requests rewriting
C007 and C002 so the benchmark contains no rebuttal tasks. This supersedes the
planned mixed-intent direction. All 49 questions are intended to be document
explanation in the next publication; the currently frozen release remains unchanged.

## C007 — development

**Original:** Could Bayshore Boulevard be reduced to three lanes to improve
connectivity for residents while retaining its role as a regional through-traffic
artery, using either a movable median adjusted to commute-hour traffic flows or
overhead signals directing lane flow?

**Proposed replacement:** What are the Bayshore Mobility Plan’s objectives for
local mobility and regional through traffic, and how would its proposed roadway
design advance those objectives?

The replacement asks for documented objectives and the design-to-objective
relationship. It removes the external three-lane/movable-median/overhead-signal
proposal and its unresolved feasibility demand. It retains the local/regional
transportation topic. Existing development reference material may be reusable,
but its applicability must be reviewed against the revised question; prior human
approval and judge results do not automatically transfer.

## C002 — test

**Original:** Why doesn’t the DEIR require additional dense vegetated barriers
near all proposed residences and schools to better protect occupants from air
pollution associated with Highway 101 and the Caltrain corridor?

**Proposed replacement:** What does the DEIR say about using dense vegetated
barriers near proposed residences and schools to address air pollution associated
with Highway 101 and the Caltrain corridor?

The replacement retains the intervention, locations, affected groups and pollution
sources. It removes the demand for additional barriers everywhere and does not
presuppose that the DEIR requires, rejects or establishes the effectiveness of
such barriers. Only question wording was used; no C002 test reference answer or
evidence was read. Answerability and alignment with its reference remain unchecked
and require a separate controlled review before publication, outside judge tuning.

## Migration boundary

This is a versioned planning proposal, not an in-place modification of the frozen
benchmark. On approval, publish explicit question revisions and retain old/new
bindings, review affected reference/expectation compatibility, and invalidate any
assumption that old evaluations apply to the new wording. Regenerated development
challenges must use the new question version. Do not regenerate held-out answers
or open test evidence as part of prompt development.

The prior intent mappings remain historical records of the original wording.
Do not silently add rebuttal instructions to the new all-explanation design.
No runtime/schema changes, provider calls, source/answer edits, or dataset
publication occurred. Documentation diff validation passed. No commit or push.

## Alternative question types for user selection

Added at Kyle's request on 2026-10-14. No option is selected. These alternatives
replace the assumption that the single proposed replacement above is the final
wording. Question type describes the requested answer, separately from task intent;
all options are intended as document explanation.

### C007 alternatives

**A — What + how (objectives and mechanism; initial draft)**

What are the Bayshore Mobility Plan’s objectives for local mobility and regional
through traffic, and how would its proposed roadway design advance those objectives?

Requires both stated objectives and a design-to-objective explanation. Broader,
with two explicit components.

**B — Why (policy rationale)**

Why does the Bayshore Mobility Plan seek to reduce Bayshore Boulevard’s role as
a regional through-traffic route?

Requires the rationale for the policy direction, rather than a repeated statement
that the plan favors local mobility. Safety/connectivity and the relationship
between slower travel and regional attractiveness are relevant development evidence.

**C — How (design mechanism)**

How would the Bayshore Mobility Plan’s proposed roadway changes improve local
mobility and safety along Bayshore Boulevard?

Requires concrete design changes and an explanation of their effects. Does not
ask for an engineering verdict on an external reversible-lane proposal.

**D — Yes/no + explanation (policy interpretation)**

Does the Bayshore Mobility Plan aim to preserve Bayshore Boulevard’s role as a
regional through-traffic artery, and what stated objectives support that interpretation?

Requires an explicit scoped answer plus a substantive basis in the plan's stated
objectives. A negative answer is not itself rebuttal intent.

### C002 alternatives

**A — What (document position; initial draft)**

What does the DEIR say about using dense vegetated barriers near proposed
residences and schools to address air pollution associated with Highway 101 and
the Caltrain corridor?

Requires a supported summary of the document's position and scope without
presupposing a recommendation or rejection.

**B — Why (rationale for the approach)**

What reasons does the DEIR give for its approach to dense vegetated barriers near
proposed residences and schools exposed to air pollution from Highway 101 and
the Caltrain corridor?

Requires an explicit rationale, not just a list of provisions. This is a semantic
why-question despite its opening wording. Answerability depends on whether the
source actually supplies reasons; no such test-evidence review has occurred.

**C — How (assessment method)**

How does the DEIR assess the potential for dense vegetated barriers to protect
proposed residences and schools from air pollution associated with Highway 101
and the Caltrain corridor?

Requires how the assessment reaches its finding, not merely how vegetation might
work physically. This wording presupposes an assessment exists; only select it
if a separate controlled reference review establishes that it is answerable.

**D — Yes/no + explanation (requirement and scope)**

Does the DEIR require dense vegetated barriers near all proposed residences and
schools to address air pollution from Highway 101 and the Caltrain corridor,
and what provisions establish the scope of that requirement?

Requires an explicit answer about universal coverage plus the actual requirement's
scope, if any. Does not demand that an additional requirement be adopted or
presuppose that it is absent. Review scope wording if the source contains no
requirement at all; an answer must be allowed to state that evidence limit.

Choose by the reasoning to evaluate: rationale (why), mechanism/method (how),
position/coverage (what), or a scoped determination (yes/no). Do not choose wording
because a prior judge performed better on it. C002 options remain unverified for
source answerability; no additional held-out material was read to draft them.

## Source review for wording selection — 2026-10-14

Kyle requests citable sections for every proposed wording and clarification of
whether C002 vegetation is required or recommended. This explicitly authorizes
inspection of C002's held-out source packet for question revision, beyond the
previous wording-only exposure. Inspected citation-occurrence source texts and
reference citation-ID metadata (not test predictions or scores). Earlier notes
that C002 evidence was uninspected describe the prior stage only. Its evidence
is now exposed during design; retain this limitation in later methodology.

### Question category correction

“What + how” is a compound demand, not an eighth category established by the
previous seven-group review. The initial C007 A asks for both objectives and their
implementation. It can be narrowed to the existing **how / mechanism** category:

> How would the Bayshore Mobility Plan’s proposed roadway design advance its
> objectives for local mobility and regional through traffic?

This asks for one relationship. The support must identify the relevant objectives
in explaining how design advances them, without making an exhaustive separate
objective inventory another task. This is a proposed revision of A, not a selected
replacement. Original B remains why, C how, D yes/no.

### C007 source catalog

| Key | Citable section | Pages | Evidence supplied |
| --- | --- | --- | --- |
| M1 | Purpose of the Bayshore Mobility Plan — C007-S007 | DEIR printed 3-114; PDF 416 | Explicit local access/connectivity, multi-modal safety and reduced regional through-traffic prominence objectives. |
| M2 | Geometric Design — C007-S011 / S024 / S025 | DEIR printed 3-115–3-121; PDF 417–423 | Crash concerns, lower 35-mph design speed, reduced regional attractiveness, path space and slower/safer turning. These three occurrence IDs refer to ONE canonical section. |
| M3 | Chapter VI: Circulation Element — C007-S006 | DEIR printed 4.8-35–4.8-40; PDF 833–838 | Policy C.1 and Programs C.1.a/b/C.4 connect local travel priorities with regional traffic on US101 and alternative routes. Optional unless the answer develops that broader policy connection. |

| C007 option | Core citable sections | Count / limits |
| --- | --- | --- |
| A: objectives + implementation; or revised single-how relationship | M1 + M2 | 2. M3 optional for a regional-route policy argument. |
| B: why reduce regional through-route role? | M1 + M2 | 2. M3 optional; safety/connectivity rationale and speed-to-attractiveness link provide substantive support. |
| C: how roadway changes improve local mobility/safety? | M2 | 1. M1 optional for framing the stated goals. |
| D: does the plan aim to preserve the regional-artery role? | M1 | 1. M2 supplies optional elaboration; M1 itself states the opposite policy direction. |

The original reference cites 6 occurrence IDs representing 4 unique canonical
sections (M1/M2/M3 plus Operations). Proposed core sets above are smaller;
Operations' planned highway connections are not necessary to these narrower answers.
Counts identify candidate sufficient sets, not frozen citation requirements or
proof that no valid alternative sources exist. Full source sections retain their
canonical extent even when only a small passage is relevant.

### C002 source catalog and modality

| Key | Citable section | Pages | What it establishes |
| --- | --- | --- | --- |
| V1 | RESIDENTIAL ADJACENT — C002-S042 | Specific Plan / DEIR Appendix A, PDF 365; printed label unverified | Bayshore Boulevard residential frontage: long planting areas are **recommended** to contain large trees and dense ornamental planting; text mentions noise and poorer air quality. This is Bayshore, not a specific101/Caltrain requirement. |
| V2 | West Rail Trail (8.5 acres) — C002-S030 | DEIR PDF 336; printed label unverified | Tall/dense native vegetation screens are **proposed** beside the railroad right-of-way; section also describes habitat/stormwater connectivity. No quantified air-cleaning benefit. |
| V3 | 6.5.5.4 Frontage Road — C002-FR-S001 | Specific Plan / DEIR Appendix A, PDF 397–399 | Narrow/upright trees are **recommended** against a soundwall; dense interplanting is described for visual screening and noise buffering of the railroad. Not an express universal air-pollution barrier rule. |
| V4 | East Rail Green Edge (3.5 Acres) — C002-S031 | DEIR PDF 336; printed label unverified | Proposed native sage-scrub planting and visual screening of railway/tank farm. Not expressly a dense air-pollution barrier. |
| V5 | Minimum Efficiency Reporting Value 13 Air Filtration — C002-S027 / S028 / S035 | DEIR printed 4.9-82–4.9-84; PDF 994–996 | The DEIR describes mandatory mechanical filtration at all residential/school buildings and ongoing maintenance. HRA assumes filtration; this is NOT vegetation. These IDs share one section. |

Reviewed passages establish location-specific recommendations/proposals, not a
general vegetation barrier requirement for all residences/schools. Do not upgrade
recommended/proposed to legally required or downgrade every project design
commitment to optional merely from vocabulary. No corpus-wide legal determination
or exhaustive absence finding is claimed. The sources do not establish blanket
Highway101/Caltrain air-pollution-screen coverage. Distinguish intended visual/noise
screening from air-pollution protection.

| C002 option | Citable sections and status |
| --- | --- |
| A: what does DEIR say about dense barriers for residences/schools near101/Caltrain? | V2 + V3 directly describe rail-side dense planting; V1 adds residential-frontage air/noise context with a different roadway; V4 optionally adds the other rail planting provision (not expressly dense). The 3 core sections explain the bounded provisions, not universal school/highway protection. The wording should broaden to DEIR **and Specific Plan** and avoid implying all planting is air-pollution mitigation. V5 optional if contrasting mandatory indoor protection. |
| B: why this approach to dense barriers? | No direct general policy rationale established in the reviewed sources. V1 supplies a local planting rationale; V3 a visual/noise rationale. Those do not justify a blanket decision against additional air-pollution barriers. General mitigation-policy and health-risk sections are contextual, not an explicit vegetation-choice analysis. Do not select this original wording without further evidence. |
| C: how does DEIR assess vegetation protection? | No vegetation-effectiveness assessment established in the reviewed packet. V5 and the health-risk methods sections assess other protections/exposure; they cannot substitute for an assessment of vegetation efficacy. Do not select this wording on current evidence. |
| D: universal dense-barrier requirement? | V1 + V2 + V3 document the relevant dense-planting provisions and limited locations; V4 optionally adds the remaining rail planting context; V5 contrasts the explicit universal filtration measure. A 3-section dense-vegetation account, or 4 with the filtration contrast, supports a bounded interpretation. It does not independently prove no requirement exists anywhere else in the full corpus. |

A cleaner **yes/no** version retaining D's intent is:

> Do the planting provisions in the DEIR and Specific Plan establish a general
> requirement for dense vegetated barriers to protect residences and schools
> from air pollution?

The support would distinguish what those provisions recommend/propose, where they
apply and what functions they specify. This narrows the interpretation claim and
removes the unsupported implication that dense vegetation serves the same
Highway101/Caltrain protection role at all sensitive locations. It remains a draft.

The original C002 reference's citation-ID fields reference 16 distinct canonical
units, including air-quality findings, tables, school siting, filtration and
landscaping context. The narrower vegetation-provision options could need 3–4 core sections (plus optional V4),
but unsupported why/how options cannot be rescued simply by reducing citation
count. This is candidate evidence selection, not a rewritten reference answer.

A bounded independent C002 source review corroborated modality/geography limits
and the absence of a direct vegetation-efficacy assessment in this packet.
No frozen question, reference, evidence or score changed. No provider inference,
commit or push. Documentation diff checks passed.

## C002 wording selected; C007 appendix check — 2026-10-14

Kyle selects this C002 replacement:

> Where do the DEIR and Specific Plan propose or recommend dense vegetation
> screening, and what purposes do those treatments serve?

Type: **measures and purposes / what**, with location and purpose as paired
attributes of each treatment. Core candidate citations: Residential Adjacent
(C002-S042, Specific Plan Appendix A PDF365), West Rail Trail (C002-S030, DEIR
PDF336), and Frontage Road (C002-FR-S001, Specific Plan Appendix A PDF397–399).
East Rail Green Edge remains optional context because its planting is not
explicitly described as dense. This selects question wording, not a replacement
reference answer or automatic publication. The frozen question remains unchanged
until the versioned revision and affected-reference review.

C007 appendix check: all six current approved citation occurrences are from
`deir_main`, representing four unique sections. No appendix citation is lost from
that approved reference by the proposed narrower questions. Historical Final
Appendix F.1 access/queue findings were already outside the selected argument,
with unresolved edition/Draft-equivalence warnings. They remain excluded and
preserved; their existence is not evidence that the current reference cites an
appendix. C007 replacement wording remains unselected.

## C007 wording selected and first answer review — 2026-10-14

Kyle selects: “How would lowering Bayshore Boulevard’s design speed advance the
Mobility Plan’s goals for local safety and regional through traffic?” Type:
**how / mechanism**, narrowed to the speed-to-goal relationship.

At Kyle's request, review one question at a time using the earlier08E/08F display
format: original citations, additional-source search, proposed structured answer,
numbered excerpts and citation discussion. C007 is first; C002 remains queued.
The first display and search receipts live under the external artifact root:
`pipelines/brisbane_baylands/task_09/09f_20261014_question_revisions_v1/C007/`.

The proposal retains Purpose and Geometric Design and adds a candidate AppendixF.2
Challenges and Opportunities section (PDF12–13), which identifies speeding as a
leading severe-injury/death factor around the project area. Three proposed unique
sections versus four in the old reference. The new appendix source is from the
eligible source corpus but has not yet received case-specific human citation
approval. The two original sections could support a shorter answer without it.
Final AppendixF.1 leads remain excluded; no historical edition hold is relaxed.

Five lexical searches were executed against the hash-verified frozen index.
The maintained runtime lacked FTS5; error receipts are preserved, alongside
successful read-only reruns of the same SQL using the system's FTS5-capable
SQLite. Canonical blocks/section bindings for the new candidate were verified and
the complete heading-bounded passage saved. Search is bounded, not exhaustive.
No provider inference, frozen artifact edits, answer approval, commit or push.

## C007 multimodal context and Final F.1 authorization — 2026-10-14

Kyle requests walking/cycling and multimodal context and explicitly permits Final
Appendix F.1. This supersedes the prior C007 exclusion on edition grounds; retain
Final provenance and do not assume Draft equivalence. Version 2 of the external
C007 review display adds Geometric Design, Final F.1 PDF703–704, with the complete
canonical section and verified source bindings in appendix_f1_candidate.json.
It retains the two main-DEIR sections and proposes F.1 instead of F.2 as the third
core citation; F.2 and all version-1 artifacts remain preserved.

The answer distinguishes lower-speed safety/regional effects from lane removal
freeing space for a separated west-side walking/cycling path. Turning treatments
reduce conflicts with path users. The proposed adequacy interpretation treats
this path explanation as useful context, not a mandatory component of every
answer to the selected speed-focused question. That interpretation and the
revised answer/citation set await review. No frozen publication or runtime change.

## C007 replacement approved — 2026-10-14

Kyle approves the immediately preceding full question, conclusion, three supporting
points and five citations: “ok great lets use this now”. The accepted replacement
is saved as C007/display_003.md and C007/approved_revision_003.json under the
external question-revision namespace above, with exact approval text, source
bindings and closeout_003.json. This supersedes the pending version-2 proposal.

The accepted citation set retains Purpose, Geometric Design and Circulation
Element (Program C.1.b), and adds Final F.1 Geometric Design and F.2 Challenges
and Opportunities. F.2 remains relevant for speeding, crossings and protected
cycling connections; it is not replaced by F.1. Operations/highway-connection
context and the old reversible-lane qualification are omitted from this answer.

This is the approved C007 replacement for the next versioned dataset publication.
Historical frozen cases, references and synthetic artifacts remain unchanged;
prior closeout hashes were verified. Reference approval does not establish that
every detail is mandatory for adequacy or settle the remaining rubric. C002
answer/citation review is next; no inference, commit or push.

## C002 first answer review and expanded evidence — 2026-10-14

The requested C002 review is saved under the question-revision namespace's C002
folder (display_001.md, search_001.json, additional_candidates.json). Four bounded
lexical searches retain original Residential Adjacent, West Rail Trail and
Frontage Road evidence. New Specific Plan Green Edges, PDF294–295, explicitly
calls East Rail Green Edge planting dense and describes railway/tank-farm visual
screening; this supersedes its earlier optional status based only on the shorter
DEIR passage. New canonical source hashes were verified.

A scope issue remains for human review: building guidelines at Specific Plan
PDF176,183,204 also specify dense landscaping and/or architectural screening of
service elements. The broad selected wording can encompass these provisions.
Either include that category or explicitly narrow to roadside/rail-side planting;
no question change is assumed. No air-pollution effectiveness or universal
vegetation requirement is inferred. The proposed four-location answer and this
scope finding await review. C002 exposure remains within the authorized revision;
no other test cases, predictions or scores were opened. No inference or publication.

## C002 roadside/rail-side scope selected — 2026-10-14

Kyle approves narrowing the question to “Where do the DEIR and Specific Plan
propose or recommend dense vegetation screening along roads and rail corridors,
and what purposes do those treatments serve?” Building-service screening is now
outside scope. C002/display_002.md and citation_comparison_002.json preserve the
wording and comparison: of 16 citation IDs actually used in the original answer,
three remain, East Rail Green Edge is replaced by the more explicit Specific Plan
Green Edges section, and twelve air-quality/policy/siting/context citations are
omitted. The answer and citation set remain under review; this wording approval
is not answer approval. No frozen artifacts changed.

## C002 context retention and residential purpose — 2026-10-14

Kyle directs retaining S031 (DEIR East Rail Green Edge) and S040 (Clean Air Plan
consistency table) as context. These are not discarded from the proposed revised
citation set. S042 explicitly identifies traffic noise and poorer air quality as
reasons to buffer Bayshore residences and preserve residential calm, with screening,
comfort, protection and privacy also described. Replace vague “residential buffering”
with these stated purposes. S040's NW2 row supplies general urban-tree benefits,
including pollutant absorption and shade; its implementation discussion concerns
project tree planting/Ecological Park woodland, not measured effectiveness of the
Bayshore screen. Keep that distinction without omitting the stated air-quality
rationale. External C002/context_clarification_003.json records the direction;
answer review remains open and frozen artifacts unchanged.

## Both replacements locked and format-reviewed — 2026-10-14

Kyle approves locking C002 and C007 with the final citation-role correction.
Authoritative revision records and readable displays are in the external namespace
`pipelines/brisbane_baylands/task_09/09f_20261014_question_revisions_v1/locked_v1/`:
C002.json/.md and C007.json/.md. They replace prior proposal pointers for future
publication without modifying the historical Task08 release.

Both use the maintained answer schema: one conclusion, supporting points, empty
qualifications and optional_context lists, exact source locators, and separate
citation metadata. C002 has four support points, four support citations, and two
context-only citations: S031 and S040. Neither context citation is used by any
answer point or answer locator. FR-S001 explicitly changes from historical context
to required support for the newly approved Frontage Road point. C007 has three
support points and five support citations, preserving Final F.1 provenance.
No Additional context answer section is introduced.

All 49 original cases pass maintained structural/citation validation; both new
answers also pass. Other cases were inspected only for structure/roles, not
semantic answer review or test-output analysis. Historical optional-context fields
remain preserved (28 cases have them); the current direction governs these two
revisions. Prior review files and every file in the frozen release were hash-checked
unchanged. The locked overlay is ready for versioned publication, not a regenerated
benchmark or a claim of new judge performance. Remaining work: revised adequacy
rubric and an explicit versioned publication/regeneration step.

## Versioned publication complete — 2026-10-14

The locked replacements are published in `task09f_20261014_v1`; see the
[release result](task09f_question_publication_result.json). Earlier “next publication”
statements are historical. All49 cases retain their original split IDs;47 case
records are byte-identical and only C002/C007 change. The new reference index keeps
S031/S040 context-only without answer links. Original release, approved overlays,
synthetic labels and results remain preserved. Current work returns to the
[reconciled adequacy labeling discussion](task09f_adequacy_redesign_draft.md).
