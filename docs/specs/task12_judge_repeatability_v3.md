# Judge accuracy and repeatability on synthetic datasets

User-requested reporting supplement, offline and before Task 13.
The presentation remains pooled over all 19 development questions for target
models. Judge metrics use each judge's synthetic dataset, independently of those
19 target answers and the future 30-question test results.

## Definitions

A correct judgment matches the item's recorded reference label. This includes
correct negative labels for G/S/C and all three routing classes for A. A positive
prediction by itself is not a correct result.

Group the same synthetic item, selected frozen judge and run across its three
original evaluation repeats. Report:

- Each repeat's prediction, validity and correctness.
- Observed correct count and complete-triple 0/1/2/3 correct distribution.
- Correct at least once: one or more correct judgments among three.
- Correct all three times: three correct judgments among three.
- Planned unique items, complete triples and unresolved triples, separately
  from the pooled judgment denominator.

Invalid or missing predictions remain unresolved, not ordinary wrong labels.
Complete-triple counts exclude unresolved triples; planned-denominator fractions
retain all planned items and expose coverage alongside them. An observed lower
bound retains known correct outcomes in incomplete triples. No metrics are
inferred from aggregate confusion counts, no majority-vote evaluator is selected,
and no new calls or labels are created.

## Exact data and units

The same 09G-selected A v2/G v3/S v6/C v8 runs underpin accuracy and repeatability.
A uses the exact bound saved Inspect log; G uses the bound saved analysis
observations; S/C use the saved per-example epoch arrays. Source checksums and
repeat identities are retained. Three-repeat totals reconcile with the existing
correct-judgment and confusion summaries. Calibration partitions stay visible.

| Judge | Unit | Correct at least once | Correct all three | 0/1/2/3 correct items |
| --- | --- | --- | --- | --- |
| A | Synthetic example | 307/310 | 302/310 | 3 / 2 / 3 / 302 |
| G | Synthetic point | 611/611 | 604/611 | 0 / 4 / 3 / 604 |
| S | Synthetic example | 485/490 | 464/490 | 5 / 7 / 14 / 464 |
| C | Synthetic example | 246/246 | 244/246 | 0 / 1 / 1 / 244 |

All saved triples in these selected populations are complete. These are
agreement with recorded synthetic labels, not a new human-gold validation.
Question reuse and repeat dependence remain limitations.

## Outputs

`judge_repeatability` adds aggregate distributions, counts and fractions;
`judge_item_repeatability` retains item-level repeat results. `judge_observations`
now contains reconstructable observations for all four judges. Existing accuracy,
precision, recall, F1 and confusion results remain unchanged.

The clean review folder adds the judge-repeatability PNG/SVG and two CSV tables.
Its gallery calls the existing figure **Judge accuracy on synthetic datasets**.
The adjacent provenance receipt binds source files, implementation and outputs;
old sealed publications and the previous review folder remain preserved.
Task 13 will retain these synthetic-judge diagnostics separately from its main
30-test-question target-model results.
