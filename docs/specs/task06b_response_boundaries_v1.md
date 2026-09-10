# Task 06B response behavior boundaries v1

Gate 1 freezes these finite inventories before their implementation. Paths below
are relative to `src/er_commons/response_inventory/` unless stated otherwise.
Each inventory is sorted lexically before hashing the recorded path and bytes.
The version identifies this inventory contract, not a rewrite of any accepted
05D/E/F activity or schema.

All execution inventories include `contract.py`, `source_structure.py`,
`pilot_policy.py`, `task05d_policy.py`, `run_spec.py`, and the cross-package
`src/er_commons/artifact_io.py`. These are actual shared record validation,
identity, policy and serialization dependencies. `run_spec.py` remains a shared
contract owner; a change to that shared owner intentionally invalidates all
execution consumers. No semantic or AST hashing is introduced.

- Source: shared paths plus `observations.py`, `pdf_access.py`, `producer.py`,
  `qualification.py`, `range_receipts.py`, `workflow.py`, `full_policy.py`, and
  `full_workflow.py`. Both supported source workflows share this boundary.
- Relationship: shared paths plus `acceptance.py`, `relationship_baseline.py`,
  and `relationship_candidate.py`.
- Reference: shared paths plus `reference_baseline.py` and
  `src/er_commons/document_records/document_structure/normalization.py`.
- Presentation: `review_tool.py`, `review_tool_static/app.js`,
  `review_tool_static/index.html`, `review_tool_static/styles.css`, and
  `src/er_commons/artifact_io.py`.

The inventory selector itself is provenance, not an executed content algorithm:
its selected ordered path list is already represented in the digest. CLI,
acquisition, unrelated stages, and review presentation are not source producer
behavior. Checked-in schema bytes are separately bound by the existing run-spec
repository bindings; runtime versions remain in existing activities. Packaging
metadata is not treated as a proxy for either explicit input.

`load_response_inventory_run_spec` remains a historical schema reader: it does
not require old repository paths to exist today and does not recompute recorded
producer identities. `verify_repository_bindings` is expressly a current-writer
preflight: it selects source, relationship, or reference behavior from the
validated spec type, then requires its exact current digest. Accepted 05D/E/F
candidate readers retain their own recorded activity/seal checks; no old
artifact is relabeled as a result of the new inventory. No accepted generated
config or historical schema changes here. Future specs must bind the selected
current stage digest explicitly; 05G owns replacement consumer bindings.

Synthetic perturbations must show that reference and presentation edits do not
change source behavior, normalization changes reference behavior, and shared
serialization/record identity changes every actual execution consumer. Path
absence fails current writer selection, while loading a historical portable
spec remains independent of the checkout.

## Reviewed-navigation integration correction

Independent Gate 1 review found repeated shared payload reads beneath prepared
relink execution. The bounded fix adds `NavigationInputs.from_records` in
`document_records/document_references/relinking.py`; the existing file reader
calls this same projection, retaining disposition semantics. The reviewed
bundle reader returns its already-read records. Prepared relinking builds
source-specific projections once and retains per-source coverage checks.
All accepted descriptor, schema, inventory, completion and navigation reads use
the shared invocation budget; historical materializer code is not re-derived.
The normal deep reader remains byte-verifying. This helper extraction changes
no reference resolution rule and introduces no persistent cache.
