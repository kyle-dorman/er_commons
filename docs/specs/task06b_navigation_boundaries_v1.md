# Gate 2 navigation and relink preparation boundary

Frozen before this lane's implementation. Navigation preparation, semantic
materialization, and reconciliation retain their source-free algorithms and
historical schema keys. Their roots, accepted identities, and population
expectations become immutable per-invocation inputs supplied by an explicit JSON
input specification and output root. Nested helpers receive these bindings
explicitly; no mutable module context or corpus fallback is permitted.

The three responsibility-named script wrappers accept `--input-spec` and
`--output-root`. Relink specification preparation accepts `--preparation-spec`
and carries every input/output config reference explicitly. Old accepted configs,
schema literals, provenance strings, and historical records are not rewritten.
Future reproduction records name the new wrappers. Synthetic semantic tests and
import/help checks verify the boundary; no accepted production inputs are run.

## Implementation outcome

The navigation request classes now require every operational root. Preparation
and materialization additionally require `specification_schema`, resolving an
explicit schema path from the input spec. The historical Gate A v1 schema seals
its old command as a literal, so the future writer has a separate v2 schema with
the new command. Historical v1 bytes and record schema-version literals remain
unchanged. Readers receive the schema explicitly, without guessing from a command.

`input_specs.py` owns per-invocation identities and expected populations;
`cli.py` validates complete request keys and resolves paths relative to the JSON
spec. The `extraction_root` Python argument replaces operational task naming;
the persisted `task03j_root` reproduction key remains for schema compatibility.
`linking_reconciliation.py` replaces the numbered owner and exports responsibility
names. Source-free matching and fail-closed rules are unchanged.

Relink preparation lives in `document_references/spec_preparation.py` with a
closed `RelinkPreparationSpec`: explicit base inputs, future output paths,
per-source accepted document roots, scope/handoff roots, reviewed navigation,
policy and schema references, and ordered finite behavior inventories. It validates
the historical base recipe before construction; never discovers a sole candidate;
preserves per-source manifests and v3 collection membership; permits an explicitly
supplied replacement scope; and rejects existing changed output contracts before
writing any output. No accepted configuration or schema was regenerated.
