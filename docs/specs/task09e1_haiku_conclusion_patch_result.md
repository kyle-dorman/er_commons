# Haiku five-conclusion patch result

All five newly enabled conclusions validate and match the proposed conclusion and numeric-score labels. Each uses its complete same-provider claim vector, including the corrected locator-only retry claims, and the unchanged original conclusion prompt. No additional claims or other conclusions ran.

This is an explicitly user-accepted mixed-prompt, selected-failure patch. It is not a fresh controlled run. The original comparison remains intact; the patched totals are separate.

| Configuration | Claims macro-F1 | Claim-review macro-F1 | Conclusion macro-F1 | Numeric macro-F1 | Numeric coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Luna historical | 93.46% | 96.96% | 92.93% | 88.51% | 350/392 (89.29%) |
| Haiku original | 92.55% | 93.91% | 95.23% | 88.20% | 349/392 (89.03%) |
| Haiku patched | 93.23% | 94.84% | 96.05% | 89.05% | 354/392 (90.31%) |

Same full denominators: 1,056 original claims and claim reviews; 392 substantive conclusions/numeric scores; 38 clean N/A answers separately. Class-macro F1 uses the existing coverage-aware policy, with unscored outputs counted as false negatives for their true class. Conventional conditional F1 and full per-class/group/case metrics remain in the analysis.

| Configuration | Claims correct / 1,056 | Conclusions correct / 392 | Numeric correct / 392 | Correct N/A / 38 |
| --- | ---: | ---: | ---: | ---: |
| Luna historical | 1012 | 370 | 328 | 38 |
| Haiku original | 1006 | 374 | 326 | 38 |
| Haiku patched | 1011 | 379 | 331 | 38 |

All failures count as wrong in these accuracy numerators/denominators. Patched Haiku has 428/430 valid conclusion outputs: the original two invalid outputs remain unscored. It supplies 354/392 numeric scores; 36 unresolved claim/review disagreements plus those two output failures account for the remaining 38. All 38 N/A outcomes remain correct. Its substantive conclusion accuracy is 379/392 (96.68%); final numeric correctness is 331/392 (84.44%).

The patch adds five correct numeric scores:
- C001: conclusion supported, numeric score 1, matches proposal.
- C056: conclusion unsupported, numeric score 0, matches proposal.
- C027: conclusion supported, numeric score 1, matches proposal.
- C029: conclusion supported, numeric score 1, matches proposal.
- C050: conclusion unsupported, numeric score 0, matches proposal.

The conclusion errors among valid predictions remain seven false acceptances and four false rejections. The improvement fills previous gaps; it does not repair those errors. Compared with Luna, patched Haiku has higher conclusion F1 and slightly higher numeric F1 (89.05% versus 88.51%), while claims and claim-review F1 remain lower. Different provider-owned claim vectors and the selected prompt repair limit causal interpretation.

Sixteen focused offline tests passed. Independent predispatch review verifies the five exact selected answers, complete ordered vectors, identical conclusion prompt/settings/schema, and five-call/$0.10/300-second caps. The reservation was $0.025387; native-usage estimated cost was **$0.00621**. Independent native and metric audits passed. All 16,547 files in the prior comparison and claim-retry inventories remain unchanged. Native receipts and metric review are linked through the result pointer. No package code changes, GLM calls, cache investigation, default promotion, commits or pushes.

See the [contract](task09e1_haiku_conclusion_patch_v1.md) and [result pointer](task09e1_haiku_conclusion_patch_result.json).
