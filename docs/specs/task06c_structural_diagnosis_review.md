# Task 06C local structural diagnosis review

Reviewed on 2026-09-10. Disposition: the diagnostic supports a narrowly scoped
requalification proposal, but **does not qualify the source**. The frozen
structural and semantic requirements still fail. Final F1 selection remains
settled; conversion remains separately gated.

## Evidence inspected

The reviewer read the active task, frozen qualification specification, Gate 2
review, maintained semantic evaluator, and retained diagnostic script and JSON
reports. The successful report directory is root-relative
`pipelines/brisbane_baylands/task_06_recovery_v1/06c/gate2_structural_diagnosis_v2/`.
No PDF source was opened, hashed, repaired, or downloaded by this reviewer.
The reviewer did not independently render pages or execute models.

`execution.json` reports success in 2.690 seconds, sampled peak process-tree RSS
270,680,064 bytes, unchanged source stat observations, and no network, source
digest pass, or PDF rewrite. The inspected directory contained 111,298 bytes.
The earlier failed diagnostic remains separate preserved evidence; it is not
an accepted result. These observations remain within the proposed 300-second,
2-GiB and 8-MiB diagnostic bounds. Sampled RSS is not an instantaneous hard cap.

## Structural findings

The report records 756 physical pages. Object `12649 0` is a 76-by-99 indexed
image stream with a failing declared Flate decoder. Its sole recorded incoming
reference is object `155 0` through `/Thumb`, the thumbnail of physical page 28.
Object `12168 0` is its failing color-palette stream, reached through array
`15366 0` and the image's `/ColorSpace` reference. The reviewed script built
reverse references from all indirect objects; both chains terminate at that
same thumbnail. No page-body reference to either failed stream was observed.

This supports classifying the two known failures as thumbnail-associated rather
than evidence that page-body text or graphics are damaged. It does not establish
that every body stream is valid, that every page renders correctly, or that a
missing specialized decoder is harmless. The decoder-availability warning from
acquisition remains a separate validation limitation. The diagnostic did not
render page 28 or exhaustively check all visible content.

## Semantic findings

All physical pages 1–20 have retained text observations without extraction
errors. Page 3 contains `APPENDIX F.1 TRANSPORTATION IMPACT ASSESSMENT [REVISED]`
and `Baylands Specific Plan Final EIR`; page 5 contains `Brisbane Baylands`,
the title split across lines, `Final`, and `December 2024`. Pages 1 and 3 also
state May 2026. These observations support the selected appendix identity and
distinguish its Final EIR wrapper from the embedded report date.

The exact frozen title requirement fails: page 3's title variant is unlisted,
and page 5 falls outside the permitted title window and splits the title across
lines. The frozen same-page project phrase is also absent from pages 1–3.
`Existing Traffic Conditions Memo` is absent from the inspected text window;
page 6's TOC contains `Existing Traffic Conditions`, which does not prove that
the separately required memo is present. The maintained evaluator's rejection
therefore remains correct. No silent normalization or waiver is justified.

## Recommended next proposal

Prepare a reviewed local requalification policy that names the exact observed
title variant, explicitly binds wrapper edition evidence to the report's project
evidence, and limits any structural exception to these proven thumbnail-only
relationships. Any new content/resource reference or additional structural error
must still stop qualification. Do not disable structural validation globally or
rewrite the source to remove the thumbnail.

If memo presence remains required, propose a finite targeted text window based
on the retained TOC's appendix location, with explicit page, time, memory and
output limits. Do not infer memo presence from the chapter heading or expand to
a full-document scan. Resolve the specialized-decoder limitation explicitly in
that proposal. Review and authorization must precede further PDF inspection or
local requalification; preserve the original source bytes and acquisition failure.

No blocking defect was found in the bounded diagnostic's recorded conclusions
when stated with these limits. A source completion, revised policy acceptance,
and conversion authorization do not follow from this review. The
[Task 06C outcome](../../tasks/sprint2/06c_qualify_and_process_replacement_f1.md)
owns the resulting proposal and next gate.
