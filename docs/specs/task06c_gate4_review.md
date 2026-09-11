# Task 06C Gate 4 Review

## Scope

Review the reusable Final F1 conversion and producer handoff without reading or
hashing the PDF or model payloads. This is a compact-seal review, not a new
qualification, conversion, target-policy, or collection-publication decision.

## Result

**Pass.** The maintained metadata-only readers accepted the conversion and
producer records, all four range completions, and their compact identity and
inventory bindings. The direct Gate 4 replay used
`read_accepted_conversion`, `read_accepted_producer`, and
`read_accepted_range` with fresh `VerificationBudget` instances. It completed
without opening the source PDF or any model file.

| Evidence | Result |
| --- | --- |
| Source binding | `feir_appendix_f1`, SHA-256 `e13c5b53f0f4da6a91f52ac784acce06619eeffd3fe053542d7ce1593b957e5e`, 68,389,743 bytes, 756 pages |
| Conversion | `dconv1-b6c5f62355c98d7ad588c455caaa987f7c7d99f896a86a219f2b0821c5693356`; `complete_with_warnings`; inventory `05c555fb3fb4cbf0e049312fc0bbda8eb7f5c38c8ec979b64e831c90a8b3c441` |
| Producer | `prv1-01c8e77c10303f8d54d4a34ebe38b489699386897a8d4c78a931f371bafbcb36`; publication `complete`; inventory `a2150e2473e2dbd4d73aff1a036625d4ce58da3a1ae46f4820da228f27f17211` |
| Chunk plan | `dplan1-dc4cd61060268d03034abe695115c3365db5a74f1029c39be5feb0f72f808b43`; four accepted ranges, covering pages 1–756 |
| Resume run | `chunk1-12645d81e0b9a2de8f5ae1dd7ddcc0884df062bbbbb699685624477022af9286`; final run reused four ranges and executed none |

The conversion inventory records 5,612 managed files totaling 156,169,405
bytes; the producer inventory records 5,112 files totaling 66,199,492 bytes.
The final supervisor attempt succeeded in 494.955 seconds, with 4,939,513,856
bytes peak RSS, 1,433,393,901 bytes peak output, and zero swap growth, within
the frozen limits. The preserved first attempt remains nonterminal evidence:
334.096 seconds, 7,182,811,136 bytes peak RSS, and zero swap growth.

## Handoff limits

Task 06G resumes from the sealed conversion directory
`06c/gate3_processing_v1/document_parse_evidence/docling_conversions/dconv1-b6c5f62355c98d7ad588c455caaa987f7c7d99f896a86a219f2b0821c5693356`
and its producer directory
`06c/gate3_processing_v1/document_parse_evidence/prv1-01c8e77c10303f8d54d4a34ebe38b489699386897a8d4c78a931f371bafbcb36`.
It must retain the original per-source manifests and use the Task 06B sealed
reuse path.

The retained qualification receipt proves the explicitly accepted Final-F1
substitution only. It does not establish general Draft/Final equivalence. The
source remains qualified with the documented thumbnail-decoder and specialized
decoder limits. Conversion and producer warnings remain evidence: 85 Docling
list-parent repairs and no reconstructed tables on pages 1, 6, 7, 9, 133, 135,
436, and 732. Tasks 06D–06F policies, Task 06G replay, and collection
publication remain unexecuted.
