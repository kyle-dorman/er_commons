# Task 03G.2: Run the Fresh Three-Document Full Pilot

Status: **provisional and inactive**. Revise this contract from the accepted
Task 03G.1 outcome, then activate it separately. No execution is authorized by
the Task 03G documentation revision.

## Abstract

Run the maintained complete two-stage extraction workflow from fresh inputs on
exactly three full model-corpus PDFs: the main Draft EIR, Appendix D, and
Appendix P. Use one shared automatic validation policy, aggregate the outcome at
pilot level, write a candidate-neutral render request/recipe, and invoke the
accepted pilot once more to verify checksum reuse. Do not create separate human
acceptance records for the three files.

## Goal

Show that the POC can build complete immutable document candidates, exact pilot
accounting, a sealed target/alias index, immutable cross-document resolutions,
and a non-authoritative handoff across a small but varied real workload.

## Frozen source scope

In sealed-manifest order:

1. `deir_main` — Complete 2025 Baylands Specific Plan Draft EIR, 2,092 pages;
2. `deir_appendix_d` — Biological Resources Technical Report, 356 pages; and
3. `deir_appendix_p` — Water Supply Assessment, 222 pages.

All page counts must be reverified from the sealed source manifest before the
run. The sources provide a large integrated report, a different technical
appendix, and the known Appendix P reference without importing comments or the
extreme 6,104-page G3 workload into this POC pilot.

## Inputs

- accepted Task 03G.1 outcome and any required remediation;
- the current sealed source manifest and production extraction identity recipe;
- one fresh `representative_pilot` document run spec and one matching scope run
  spec;
- shared content-owner policies mechanically specialized with the three source
  identities from the manifest;
- `machine_validation` hierarchy authority for the fresh candidates under one
  common automatic contract; Appendix P's historical bounded authorization is
  not rebound or copied;
- maintained `extraction run-scope` and `extraction validate-handoff`
  interfaces; and
- candidate-neutral comparison and render-request support.

## Outputs

- one checked-in pilot document run spec and one checked-in pilot scope run
  spec with exact identity/configuration consequences;
- a first invocation that performs fresh source processing in a new pilot
  artifact namespace rather than checksum-reusing historical candidates;
- one explicit terminal document result for each of the three sources;
- exact pilot accounting, a sealed target/alias index, immutable cross-document
  resolutions, and a pilot-only handoff with `task04_status: not_evaluated`;
- read-only handoff validation over the published pilot;
- aggregate page, table, family, hierarchy, label, alias, mention, resolution,
  warning, runtime, memory, and artifact-size observations;
- one combined pilot-level anomaly summary, not separate human acceptance
  records per source;
- a checksummed render request and recipe naming requested pages/evidence,
  renderer, version, arguments, and immutable inputs, but no generated renders;
- a second invocation proving checksum reuse of the accepted pilot; and
- POC-sized proposed Task 03H settings or a concrete remediation Task 03G.x.

## Plan / spec requirement

Revise this provisional contract after Task 03G.1, then freeze:

1. exact document and scope specs, artifact namespace, command, shared policy,
   and resource settings;
2. how new source-specialized configuration enters the extraction identity,
   with no rebinding of existing candidates;
3. the evidence that proves the first invocation is fresh;
4. the common automatic structural checks and bounded combined anomaly sample;
5. pilot-level stop conditions and the rule for opening a remediation subtask;
6. the render request/recipe only; and
7. the exact second invocation and evidence for checksum reuse.

Do not add simulated failures. If an actual failure occurs, preserve the normal
attempt evidence and stop the affected subtask for diagnosis.

## Research / learning checkpoint

Explain the practical distinction between a fresh first build and a reuse
check. Explain why one automatic contract plus an aggregate pilot review scales
better than separate human acceptance records while still preserving
source-qualified anomalies.

## Review pass

- **Freshness:** no first-invocation content owner or document candidate is
  satisfied by historical Appendix P/Task 03F checksum reuse.
- **Completeness:** each successful document covers every manifest page and all
  required stage-one owners before publication.
- **Two-stage integrity:** accounting is exact, the index uses only verified
  successful candidates, resolution does not mutate stage one, and the handoff
  remains pilot-only.
- **Aggregate sufficiency:** one combined review addresses structural regimes
  and downstream consequences without a per-file acceptance system.
- **Review boundary:** the recipe is disposable and non-authoritative; Task 04
  remains unevaluated.
- **POC restraint:** observed evidence supports the conclusion without added
  chaos tests or repeated fresh-build campaigns.

## Validation

- Verify all three sources and every page count against the sealed manifest.
- Run the maintained complete two-stage scope entrypoint.
- Validate schemas, identities, lineage, inventories, checksums, page coverage,
  coordinates, references, assets, accounting, index, resolutions, warning
  propagation, and stage-one immutability.
- Run `extraction validate-handoff` against the resulting pilot scope.
- Verify the render request/recipe checksums and confirm no generated render is
  required for candidate completeness.
- Invoke the same accepted pilot again and verify checksum reuse rather than
  content reconstruction.
- Run:

```bash
make validate-extraction-contract
make check
git diff --check
```

## Closure criteria

Task 03G.2 is complete when the fresh pilot and reuse check have explicit
outcomes, including any real failure. Task 03G remains open until the user
accepts those outcomes and any remediation/rerun; only then may Task 03H be
revised for activation.

## Non-goals

- all-35 complete extraction or terminal accounting;
- separate human acceptance records for the three sources;
- reusing Appendix P as the first pilot build;
- simulated failure, fault injection, or production reliability engineering;
- generated review renders or Task 04 dispositions;
- Final EIR comments/responses or standalone comment PDFs;
- OCR, generative repair, or pilot-local silent correction; or
- activating Task 03H or calling the extraction release accepted.
