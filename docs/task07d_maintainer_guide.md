# Task 07D maintainer guide

Task07D turns reviewed claims and source judgments into separate case claim and
citation lists. It does not decide claim relevance, infer support, or change saved
human labels. The final release and its later code-quality validation have separate
manifests: refactoring must never rewrite an earlier seal to match new code hashes.

## Code ownership

| Module | Responsibility |
| --- | --- |
| `pilot_evidence_forms` | Versioned Label Studio layouts and native control names. Historical form bytes are protected because saved review hashes depend on them. |
| `pilot_evidence` | Trusted task preparation, explicit source/curator HTML separation, native field parsing and review validation. Existing form imports remain available for demonstrated callers. |
| `pilot_citation_records` | Small shared canonical-record operations: rooted paths, hashes, unique IDs, full block anchors, next body heading and breadcrumbs. No citation-selection policy. |
| `pilot_citation_units` | Complete section/table membership and ordinary v1/v2 unit validation. |
| `pilot_citation_boundary_overrides` | The explicitly audited v3 source-bound boundary exception. No general heuristic repair. |
| `pilot_citation_visual_sections` | v4 complete text sections with figure-location links, not inferred figure evidence. |
| `pilot_evidence_search` | Frozen FTS5 cache, deterministic query receipts, ordinary source-unit retrieval. Ranking never means evidence support. |
| `pilot_case_citations` | Pure semantic deduplication and support/context aggregation; returns case payload and separate audit. |
| `pilot_case_export` | Verified input loading, authorized clarification/warning handling, case publication and final manifest. Maintained replacement for the sealed one-off run script. |

JSON dictionaries remain at the existing artifact boundary. Small typed functions
and `ExportInputs` organize the workflow; a new model hierarchy or workflow engine
would add migration complexity without improving this bounded pipeline.

## Reproduce the current case exports

With `.env` configured as described in the project setup, use a new destination:

```sh
make export-pilot-case-citations CASE_EXPORT_DIR=/absolute/path/to/new-export
```

The make target supplies the accepted review-status and claim-handoff documents.
For an explicitly different set of inputs, inspect the standalone interface:

```sh
uv run python -m er_commons.pilot_case_export --help
```

Its four arguments are `--data-root`, `--review-status`, `--claim-handoff`, and
`--output`. The first three identify existing inputs; the last must not exist.
The current disposition schema is specific to this MVP's clarification and four
accepted warning tasks. This is not an automatic repair interface for later runs.

The exporter verifies input manifests and exact file closure, matches every claim
to the accepted handoff, validates canonical anchors, and normalizes native review
fields. It then writes `cases/`, `audit/`, and `summary.json`; `manifest.json` is
written last. A directory without a manifest is an incomplete attempt, not an
accepted release. Preserve it for diagnosis and rerun to a fresh destination.
The exporter cannot write inside its sealed review, disposition, or claim inputs.
It does not contact or mutate Label Studio.

## Invariants and diagnosing failures

- Claims are retained exactly; supporting/direct relevance does not determine
  citation level. Source-level support beats context across uses of the same
  canonical section/table. Display labels do not define citation identity.
- Native annotations remain native. An explicitly clarified effective annotation
  is stored separately, with its original record/hash and correction binding.
- `ReviewValidationError` carries parsed review data and consistency errors;
  it does not mean acceptance. The exporter permits only task/error signatures
  bound by the explicit disposition. Foreign controls, bad source bindings and
  other structural errors remain hard failures. Never catch all `ValueError`s
  and reinterpret them as accepted human review.
- A manifest/hash failure indicates changed, extra, missing or misbound input.
  Diagnose the exact file and authoritative release; do not regenerate its hash
  merely to get past validation.
- A citation boundary failure belongs to source review. Do not truncate the text
  to make it fit or expand the bounded override without a new reviewed receipt.
- SQLite FTS5 availability depends on the Python runtime's SQLite build. A
  skipped FTS5 integration test does not verify retrieval. Use a runtime with
  FTS5 and run that test explicitly. Search still verifies the complete frozen
  index before each call; no implicit cache-trust shortcut was introduced.
- SQLite connection contexts only manage transactions. The search module also
  closes handles explicitly, including failed-query paths.

## Validation after changes

Run `make fix` and `make check` with the Task07D test selection when making bounded
changes; the test files are named `test_pilot_case_*`, `test_pilot_evidence*` and
`test_pilot_citation_*`. Form tests protect historical/current byte hashes;
exporter tests cover input tampering, path confinement, duplicate identities,
clarification binding, bounded exceptions and incomplete publication.

For artifact-affecting changes, use the maintained export command in a fresh
directory and compare every `cases/*.json` byte-for-byte against the sealed release.
Check both claim and citation preservation, not merely counts. Changes to internal
audit representation may be explicit (for example, a structured rejected review);
keep native annotations intact and record the new code and validation hashes in a
separate quality manifest. The historical scripts are execution evidence, not the
maintained entrypoint.
