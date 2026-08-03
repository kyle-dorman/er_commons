# Backlog

This is a parking lot for unselected future ideas. It does not define active
scope, replace a numbered task, or record a completed experiment.

- Consider additional environmental-review datasets only after the first CEQA
  benchmark has a documented data and evaluation contract.
- Revision-family benchmark tasks: link a public comment, draft, and final
  document, then reconstruct the evidence trajectory that connects them
  (`comment + draft + final → reconstruct the evidence trajectory`). This is a
  candidate family, not yet the Sprint 1 task or an accepted benchmark policy.
- Consider broader reusable pipeline components only after a repeated,
  measured integration need proves that thin task-specific glue is insufficient.
- Consider richer workflow orchestration only after simple commands and
  manifests demonstrate a real restart, scheduling, or dependency bottleneck.
- After the OCR-free Task 03E.5 first pass, measure the cost of deliberately
  unresolved figure mentions before selecting a figure-linking design. Review
  mention counts, representative failures such as Appendix P Figures 1 and 4,
  and downstream retrieval or context-injection errors that required visual
  evidence. Only then consider constrained OCR or another exact image-label
  method with page, document, target, and checksum evidence; proximity alone
  must not create a link.
- After the first vertical slice, consider adding lightweight diagnostic
  metadata to benchmark cases. Candidate fields include support topology
  (`single`, `fan_out`, `chain`, or `mixed`), reasoning operation, evidence
  element types, number of direct-support records, number of distinct pages,
  sections, and documents, maximum explicit-reference-graph hop, single- versus
  multi-page scope, same- versus cross-section scope, and main-report versus
  appendix evidence. Use these fields for analysis rather than case acceptance,
  split balancing, or quotas in the small benchmark. LongDocURL's
  evidence-oriented task taxonomy ([paper, especially Figure 4 and Appendix
  F](https://arxiv.org/pdf/2412.18424)) and BRIDGE's chain/fan-out and
  page-depth breakdowns ([paper](https://arxiv.org/pdf/2603.07931)) are useful
  references.
- After the first locked run, consider adopting a stage-specific benchmark
  error taxonomy covering extraction or representation, retrieval misses,
  evidence ranked below the target cutoff, retrieved evidence that is unused or
  mis-selected, unsupported or overstated claims, individually supported facts
  combined incorrectly, comparison-direction or entity mismatches, omitted
  supported material, incomplete or unresponsive defenses, invalid outputs,
  and evaluator errors. Keep these diagnoses separate from the frozen primary
  scores and apply them only when useful for post-run analysis; they should not
  add a new MVP scoring dimension. LongDocURL's Appendix G
  ([paper](https://arxiv.org/pdf/2412.18424)) and BRIDGE's grounding,
  evidence-coverage, and comparison-error framing
  ([paper](https://arxiv.org/pdf/2603.07931)) provide useful starting points.
- Before expanding beyond the first vertical slice, consider a gold-evidence
  completeness audit. Review plausible non-reference evidence surfaced by
  curator search or development runs and classify it as `required_missing`,
  `valid_alternative`, `context_only`, or `unsupported`. Required missing
  evidence would correct the reference set before a new benchmark version is
  frozen; valid alternatives would be linked to the same support requirement
  without making every duplicate passage mandatory for retrieval. DocScope's
  evidence-completeness review is a useful reference ([Appendix B.5](https://arxiv.org/pdf/2605.08888#page=29)).
- After the MVP, consider generating a publication-style benchmark release
  report with an appendix-equivalent asset index, human-readable prompts and
  schemas, full per-case results, negative experiments, and compute, runtime,
  storage, and human-effort accounting. The MVP continues to rely on its
  canonical manifests, task outcomes, and raw run artifacts rather than adding
  this separate reporting layer.
