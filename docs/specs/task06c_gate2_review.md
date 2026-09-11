# Task 06C Gate 2 independent review

Reviewed on 2026-09-10 after the separately authorized acquisition. Disposition:
**the failed attempt is correctly retained; the source is not qualified.**
Gate 3 remains unauthorized. Final F1 selection remains settled.

## Evidence inspected

The reviewer inspected the frozen specification and checked request, maintained
acquisition/qualification code, and compact failure record. The retained PDF was
not opened or hashed. No network request, parser invocation, conversion or model
execution was performed by this reviewer.

The root-relative attempt is
`datasets/ceqa/raw/brisbane_baylands/brisbane_baylands_2025_feir_f1_qualified_v1`.
Its exact observed membership is `source.part` (68,389,743 bytes) and
`failure.json` (4,413 bytes). The failure record SHA-256 independently matches
`9bd38ad81a7d86f92190a83047d15e37bdfecbb07d94fd0b2ec8e1f803ea1ae1`.
There is no source record or accepted completion.

The compact record reports HTTP 200, no redirects, a matching declared length,
and the stream digest
`e13c5b53f0f4da6a91f52ac784acce06619eeffd3fe053542d7ce1593b957e5e`.
The filename is
`ApxF1_TranportationImpactAssessment_OCR_REVISED_202605201828511148.pdf`.
These observations identify the transfer; they do not establish semantic title,
edition or undamaged PDF contents. Elapsed time was 11.096 seconds and sampled
worker RSS peaked at 295,616,512 bytes, within the frozen ceilings.

## Failure disposition

Strict pikepdf syntax checking reported stream-decompression errors for objects
12649 0 and 12168 0 at offsets 68,354,632 and 65,962,963, respectively, with
`incorrect header check`. The parser also warned about reprocessing without
filtering. The maintained validator correctly stopped on these warnings before
page-count and semantic qualification results could be returned. Page count,
title, project/internal text and observed edition therefore remain unverified.

The current evidence supports neither acceptance nor a conclusion that the
selected document is the wrong source. There is no blocking defect in the
observed fail-closed behavior. The failure record's proposed local
requalification is a future action, not a waiver or accepted completion.

## Proposed next boundary

Before any conversion, separately authorize a bounded local diagnosis of the
retained bytes: no network, redownload, PDF rewrite, OCR, model loading or
source digest pass. A concrete diagnostic request should bind this failure
record and payload stat metadata, retain the 300-second/2-GiB/one-thread parser
ceiling and 20-page text window, and write only compact findings to a fresh
namespace. Inspect the two reported object references and their page/resource
relationships, then determine whether bounded text evidence can be collected.
If relationships require broader processing, stop with that limitation.
Diagnosis alone must not publish a qualified source or silently relax strict
structural policy. Any revised qualification policy needs an explicit reviewed
disposition and separate requalification authorization.

Gate 3 additionally needs a qualified source seal, the explicit substitute-to-
maintained-manifest adapter, measured page-based routing, and a verified local
model inventory. A compact filename search found no model inventory under the
external pipelines tree; the historical model directory is absent. The local
Hugging Face cache has a Heron snapshot directory and a TableFormer revision
reference, but directory entries do not prove complete usable snapshots. No
model payload was read. Model remediation, if needed, requires its own bounded
proposal under the frozen offline policy.

The owning [Task 06C](../../tasks/sprint2/06c_qualify_and_process_replacement_f1.md)
records the execution outcome and next authorization boundary.
