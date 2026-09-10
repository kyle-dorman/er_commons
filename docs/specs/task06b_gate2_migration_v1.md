# Task 06B Gate 2 migration v1

The user authorized Gate 2 end to end after the completed Gate 1 handoff.
The working tree includes the uncommitted, tested Gate 1 changes at base commit
257b562; this gate preserves them. No commit, push, source/model execution,
production replay, or external artifact deletion is included.

The finite 06A inventory remains the source of truth. Lanes own generation and
preparation, review, navigation/relink preparation, and diagnostics/retirement.
Renamed wrappers receive the explicit inputs specified by 06A. Historical schema
strings, recipe references, accepted configs and artifact directories stay fixed.
No compatibility alias is introduced merely to satisfy an old generator test.

Retirement evidence: the exact source/import search found the Task03G2
preparation wrapper/module and two generators have only historical or isolated
test callers. The nine-file task03g2f_replay island has only its own imports,
wrapper and isolated execution tests. Its maintained downstream publication
size/ownership checks move to maintained tests; Gate 1 exact closure, immutable
inputs, and deep-corruption tests already cover the reusable negative boundaries.
The unused compatibility_v1_bundle adapter has no runtime import; historical
recipe acceptance tests retain its recorded entries without accessing the file.
Only those enumerated code files and isolated tests are removed. Other v1
compatibility modules remain.

Diagnostic owners are renamed conversion_scaling/conversion_compatibility_audit.
Source ID, run root and output root become explicit parameters. The CLI requires
an operation and explicit inputs; expensive diagnostic branches remain supported
but are not executed by Gate 2. Task05D/pilot policy symbol renames preserve exact
historical values. Make mutation/review roots become required caller inputs.

Validation compares the same synthetic records, tests renamed imports/resources
and help interfaces, repeats Gate 1 sentinels including reuse, and checks retained
historical recipes after old code paths disappear. The final task outcome and
migration inventory own each old/new disposition and test/review evidence.
