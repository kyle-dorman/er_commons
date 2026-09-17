# Task 05G: diagnosis of twelve unchanged collisions

Diagnosis only, using the Phase 4 attempt-5 outcomes, accepted Task 05D response
text, and selected accepted Task 06G canonical records. All twelve retain the
same candidate sets and terminal reasons as Phase 3. No resolver changes,
replay, PDF/image/model access or accepted-artifact mutations were performed.

## Nine section references: running headers promoted to targets

Seven section labels account for nine mentions. Each candidate set contains
an apparent actual section opener and later targets whose text and position
match repeated page headers. They are distinct canonical target IDs, so simply
deduplicating identical aliases would not fix the collisions.

| Section | Response(s) | Apparent opener, physical page | Competing header targets, physical pages |
| --- | --- | ---: | --- |
| 4.5 | O-Joint-24 | 569 | 632 |
| 4.6 | M-OSEC-93, M-OSEC-137, O-Joint-2 | 647 | 696, 700, 728 |
| 4.11, written 4-11 | M-OSEC-137 | 1087 | 1106, 1118 |
| 4.12 | M-OSEC-340 | 1133 | 1202 |
| 4.13 | M-OSEC-65 | 1235 | 1264, 1266 |
| 8.5 | M-OSEC-143 | 2008 | 2012 |
| ES.6 | M-OSEC-13 | 184 | 188, 190, 194, 196, 198, 200 |

Pages here are physical pages of the Draft EIR main PDF. This is a metadata-based
diagnosis from existing extraction, not new visual confirmation or a replacement
human acceptance decision. All sixteen competing header-like targets match existing page-header exemplars
in case-folded text, page dimensions and bounding boxes within one point; the
seven apparent body openers do not. Nevertheless, these competing records are
currently labeled body headings with `accepted_hierarchy_correction` provenance.
Their interpretation as erroneous header promotions is therefore a strongly
supported inference, not an existing metadata label. ES.6 particularly shows why
text-only suppression is unsafe: its real heading shares header wording but has
different geometry.

A reusable repair candidate is to qualify section targets against established
page-header exemplars and geometry, preserving only a uniquely supported body
heading. It must fail closed when that evidence is insufficient. Blindly taking
the first target, deleting every repeated heading, or comparing minor punctuation
would be unsafe general rules. Existing canonical target IDs and historical
accepted artifacts must remain intact; any consumer filtering needs a fresh,
reviewed rule cycle and full comparison.

The 4-11 reference supplies “Energy Resources,” and the hyphen-normalization
branch currently returns before attached-title filtering. However, all three
candidate titles have the same substantive wording: `4.11 ENERGY RESOURCES`
versus `4.11 . Energy Resources`. Fixing that branch alone is not a sound cure;
punctuation differences must not stand in for body-versus-header evidence.

Some other mentions of Sections 4.5 and 4.6 already resolve through the existing
attached-title rule. These twelve remaining collisions have not regressed.
The ES.6 response supplies printed pages ES-142 through ES-160, and the 4.13
response quotes page 4.13-57; neither warrants choosing an arbitrary fragment
of the requested whole section.

## Three appendix references: one logical report, multiple physical files

| Appendix | Response(s) | Competing document targets |
| --- | --- | --- |
| K1 | M-OSEC-91 and M-OSEC-342 | Four parts of the OU-SM remediation report |
| K2 | M-OSEC-91 | Five parts of the OU-2 remediation report |

These references identify whole reports, without selecting a particular part.
The source catalog intentionally retains each physical part; the current
single-target document resolver sees four or five valid candidates. In
M-OSEC-342 the response explicitly calls K1 a four-part report and K2 a
five-part report. The report title/date in M-OSEC-91 identifies the report,
not one physical part.

These are a target-representation limitation, not spurious duplicate aliases.
A general solution would represent a logical multipart document with ordered
member targets, or explicitly support a link to the full member set. Either
requires a separately scoped target/link contract and downstream consumer
changes. Picking part 1 would silently discard the rest of the cited report.
Keeping these three as explicit nonlinks is correct under the present contract.

## Assessment

Nine cases are plausible candidates for a bounded, general header-qualification
repair; this diagnosis does not promise nine successful links. The other three
need multipart-target support and should remain nonlinks until that capability
is deliberately added. All sampled-review and text-only evidence limitations
remain unchanged. The [accompanying JSON](task05g_collision_diagnosis.json) retains exact population and evidence
pointers; no diagnosis is a new target acceptance.
