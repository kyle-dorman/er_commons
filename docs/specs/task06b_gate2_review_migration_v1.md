# Gate 2 extraction review migration v1

The authorized review lane moves the complete 45-file `human_review_support/task04`
package, including assets, to `human_review_support/extraction_review`. Python
imports and package-resource names migrate together. Historical schema versions,
JSON keys, pass identifiers, findings and retained evidence remain unchanged.

Six maintained wrappers receive their inventory names. Four preparation/build/
publication wrappers require `--review-spec` and `--output-root`; finding and
register commands retain their explicit review-root arguments. The validated
request describes exact source/evidence roots and prior decisions. Help parsing
must not load settings or source/model libraries. Rendering requires an explicit
request flag and is not executed by this migration.

New commands select evidence explicitly. Existing historical pass-policy values
remain historical record contracts, not authority to infer a corpus path or pick
the newest human decisions. Tests migrate with imports and preserve historical
fixture acceptance, selection semantics, schema literals, and asset bytes.
Validation uses the existing review suite plus request and help sentinel tests.

## Executed mapping and preserved contracts

| Old owner/interface | New owner/interface | Evidence |
| --- | --- | --- |
| `human_review_support/task04/` (45 tracked files) | `human_review_support/extraction_review/` | All Python imports, package-resource lookups and review tests migrated; assets are byte-identical to the prior checkout. |
| `prepare_task04a_review.py` | `prepare_extraction_review.py` | Requires review spec and output root; no settings or fixed namespace selection. |
| `build_task04_review_bundle.py` | `build_extraction_review_bundle.py` | Request selects retained/source roots and source scope; rendering requires `render_pages: true`. |
| `build_task03j_final_review.py` | `build_final_extraction_review.py` | Explicit final-pass profile, evidence, schema, prior-review and decision selection. No newest-decision fallback. |
| `publish_task04a_gate_d.py` | `publish_extraction_review.py` | Explicit Gate A/Gate C paths, output root and accepted historical profile identity/counts. |
| `record_task04_finding.py` | `record_review_finding.py` | Existing explicit review-root/finding arguments retained. |
| `set_task04_finding_register_status.py` | `set_review_register_status.py` | Existing explicit review-root/register transition arguments retained. |

The final review API is `build_final_extraction_review`; preparation is
`prepare_final_extraction_review`; compact publication is
`publish_extraction_review`. Original schema versions, pass strings and JSON
keys remain historical contracts. Final-pass commands explicitly select and
validate the existing 35-source/c17 policy profile, including 757 dispositions,
341 visible TOC cards and 725 ambiguous links. This migration does not invent a
new review policy or repurpose an accepted decision for different evidence.

The request model/schema is `er_commons.extraction_review_request.v1`, owned by
`extraction_review/request.py` and
`benchmarks/er_bench/schemas/extraction_review/v1/request.schema.json`.
Paths resolve relative to the request file. Operations are `prepare`,
`build_bundle`, `build_final`, and `publish`. The spec requires an explicit
historical pass, data root, schema root and source count, plus the operation's
evidence/identity fields. Preparation's large census, raw Docling scan and deep
upstream validation are disabled unless explicitly selected. Rendering is
required explicitly for build operations and forbidden for source-free
preparation/publication. No request or production work was executed here.

Validation: 98 review/request tests passed, including six help commands guarded
against settings and execution. Existing finding, closure, publication, selection
and retained-record tests ran through renamed imports. Asset byte comparison
against the original checkout passed for all four package assets. Searches found
no old review package or wrapper paths in maintained Python callers/tests.
