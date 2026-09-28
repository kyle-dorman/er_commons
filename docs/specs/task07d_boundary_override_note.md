# Task 07D: bounded citation overlay for Section 8.5.2

The PC-LM-2 citation to Draft EIR Section 8.5.2 needs a source-audited boundary
overlay. This is citation preparation, not a correction to the accepted extraction.

PDF physical pages 2011–2012 (printed 8-157–8-158) show one continuous Section
8.5.2. Canonical section 3325 begins with a running header incorrectly classified
as a body heading. Its first paragraph continues the preceding page's sentence.
Canonical section 3326 consists of the inline “Impact NOI-3:” label, positioned
out of reading order. The next actual section is 8.6, physical page 2013.

`pilot_citation_boundary_overrides` supports only this exact extraction and
section combination through citation-unit v3. A hashed audit receipt binds the
complete canonical block/section files, independent original snapshots and PDF
inspection artifacts. Validation requires all original members from sections
3324–3326, excludes only running-header block 18669, explicitly moves inline label
18679 before paragraph 18672, and ends before heading 18680. All source text is
unchanged. Missing paragraphs, altered text, alternate boundaries and unstated
reordering are rejected. Other source defects require their own reviewed policy;
this exception does not relax the ordinary heading-boundary rule.

The receipt and complete candidate are retained under the fresh Task 07D
`remaining_cases_20260928_v1/cases/I-CF-4/` artifact directory because that agent
performed the independent audit. The generated candidate is for **PC-LM-2**.

The first page also contains existing impact-row text interleaving in the
canonical extraction. The boundary overlay does not silently rewrite those
fragments or claim to repair their wording. PDF links and that limitation remain
available for review. No human evidence-support judgment is implied.
