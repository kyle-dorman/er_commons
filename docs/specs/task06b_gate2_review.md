# Task 06B Gate 2 independent review

The publication lane reviewer independently inspected the integrated naming,
identity, input-preparation, navigation, diagnostics, retirement and command-map
changes. Review covered the current writer versus historical reader boundary,
original per-source manifest bindings, replacement collection membership, shared
verification budgets, exact managed-file closure and human maintainability.
The root reviewer separately inspected the extraction-review lane's explicit
request dispatch, removed fallback selections, historical profile checks and
asset/resource migration. Review ownership is separated below.

## Findings and resolutions

| Finding | Resolution checked |
| --- | --- |
| Deep regression validation required present-day files from a historical identity recipe. | The audit validates the recorded identity without `project_root`; current writer validation remains separate. |
| Optional reviewed-input preparation could read navigation rows before seal validation. | Standalone preparation verifies first; the CLI performs the deep regression audit before writing optional derived inputs. |
| Navigation verification checked completion references without exact inventory closure. | `seal_audit.py` checks identity, inventory bytes, observed managed inventory, required consumed rows, completion membership and symlink exclusion. Payload bytes are deliberately audited once in this explicit deep operation. |
| Relink recipe preparation hardcoded v2 schemas and could reject v3 mixed membership. | Explicit document, collection and production-identity schema paths select the intended contracts. Preparation preserves original manifest fields and collection membership and validates the replacement physical source order. |
| A historical base recipe was copied before its recorded identity was validated. | Historical identity validation now precedes scope derivation and all writes. |
| Moved recipe preparation retained unbounded read/hash helpers. | One `VerificationBudget` flows from the CLI request read through accepted references, schema/config/code inputs, existing-output checks and current recipe validation. Oversized and shared-total hash tests fail before opening bytes. |
| Diagnostic shell description implied every operation avoided payload bytes. | The shell is a thin package caller; the command map distinguishes metadata ledgers from explicit payload profiling/deep audits. |

## Evidence and verdict

Independent targeted checks passed: 54 tests spanning collection membership,
input preparation, config generation, preserved publication reuse, historical
conversion readers, navigation seal auditing, relink preparation and Gate 2
interfaces. After the final budget edits, all 9 relink-preparation tests passed.
Earlier independent checks passed 56 diagnostics/policy/maintainability tests
and 51 navigation/preparation/interface tests. These overlapping targeted counts
are not a full-suite total; the root task records final `make fix` and
`make check` results separately.

The maintained command map and review runbook match the new script flags.
Approved pilot retirements transfer the maintained downstream replay size and
function-length assertions without relaxing their thresholds. Historical
schema keys, recipes and accepted decision semantics remain preserved; new
execution paths use explicit selections rather than fixed corpus roots.

No actionable identity, closure or maintainability blocker remains in this
reviewed scope. Metadata qualification continues to mean recorded seal and
filesystem metadata validation, not fresh payload-byte equality. Explicit
synthetic deep-audit tests own same-size corruption detection. This review ran
no production replay, PDF access, rendering, model loading or accepted large
payload hashing, and authorized no artifact deletion, commit or push.

## Separate lane review

The navigation/relink lane independently reviewed generation, input preparation,
serial runner and namespace controls. Findings were fixed: every proposed process
config is validated by its owning model before any write; document/collection v3,
catalog and identity proposals are validated; the current chunk threshold remains
300; compact preparation reads share one budget; runner progress captures one spec
digest and rejects later mutation. Its final focused set passed 39 tests.

The root reviewer inspected the extraction-review request dispatch and its explicit
roots, scope/pass/count fields, rendering opt-in and removed newest-decision fallback.
Historical final-profile constraints remain explicit compatibility checks; changing
those semantics belongs to later review-policy work. The root independently ran 46
review request/final-pass/publication/verification/bundle tests, all passing. A built
wheel contains all four renamed review asset files with identical bytes and no old
review-package path. No actionable finding remains in this lane.

The root's final integration audit also required a positive complete relink
preparation run. The new synthetic test builds tiny sealed publication and
reviewed-navigation inputs, produces and reloads all four v3-compatible contracts,
preserves original manifests and replacement membership, retries identical outputs,
and refuses changed outputs under the existing source/model/conversion/preserved-
payload hashing sentinels. Publication now uses the atomic no-clobber helper,
including a conflicting same-size write regression. The final full-suite result
is recorded in the task outcome and external packet.
