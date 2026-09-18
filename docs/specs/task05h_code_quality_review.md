# Task 05H human maintainability review

The user requested this dedicated pass before curator execution. The earlier
Phase 2 review established many correctness gates but did not sufficiently
separate human maintainability from behavioral validation. This report owns the
subsequent review and refactor; the earlier report remains historical evidence.

## Findings and changes

| Human maintenance problem | Change |
| --- | --- |
| Loading inputs required tracking five anonymous return values and 13 positional constructor arguments | Named source/graph fields and keyword construction make each record's owner visible |
| Input loading mixed authority verification, replay payloads and inherited limitations, including hidden mutation of a caller's dictionary | Separate named domain helpers return their results; the caller assembles them explicitly |
| One large outcome loop mixed source anchors, target eligibility, resolved links and nonlinks | Each invariant now has its own named check; failures stay near the relevant policy |
| Selection mixed multiple review policies in a large function | The entry function now lists source anchors, graph relationships, official references, exceptions and representative selection as explicit steps |
| Card construction combined navigation, layout, source intervals and annotations, with duplicated span rendering | Separate navigation/card/unit/span helpers; source boundaries and reference warnings stay together |
| Launch code separately constructed worker and launcher arguments | One explicit argument builder removes drift risk and makes argument edits local |
| Launch admission and receipt checks obscured publication reserves and cumulative accounting | Named helpers expose publication admission and resource checks; acceptance completion takes typed named arguments |
| Dispatch implemented stage work inline, making the workflow hard to scan | Named preparation, review, finalization, publication and acceptance functions; dispatch only authorizes and routes |
| Finalization mixed replay validation with first-time sealing | An explicit reuse helper makes the unchanged-review requirement visible |
| Schema failures could print an entire record instead of the useful error | Report the most specific field and bound message length |

The pass adds no workflow framework, dependency, plugin or new production module.
It deliberately retains explicit serialized record fields and ordinary functions.
Small JSON-boundary dictionaries remain where the existing contract is the useful
representation; the refactor does not wrap every field in a new class. Longer
record-building functions mainly list the actual manifest/request fields, so a
maintainer can inspect and change their contract in one place.

Independent review caught two integration issues during the refactor: newly
named write-capable stages needed their own local authorization check, and cache
reuse needed to check each child path for symlinks. Both were fixed before
freezing code. Regression tests cover direct stage calls with permissions disabled
and linked cache children. Existing production dispatch remains gated.

## Independent assessment

Reviewers assessed code they did not refactor:

- `human_review_inputs` reviewed selection and views: policies have local edit
  points, rendering has clear boundaries, raw intervals and bounded graph context
  remain intact.
- `human_review_selection` reviewed launch and execution: shared argument
  construction, admission before writes, accounting under the lock, and terminal
  evidence before designation are directly traceable.
- `human_review_launch` reviewed workflow, storage, specification, publication
  and input loading: named stages and domain results improve readability and
  editability; the two integration findings above were remediated.

Assessment: no unresolved material human-maintainability finding in the reviewed
code. This conclusion is based on tracing policy edits, stage entry points,
failure paths, immutable evidence and restart—not solely on passing tests.

## Verification and current authority

The 126 focused Task 05H tests pass. `make fix` passed; final `make check`
passed formatting (799 files), Ruff and mypy (552 source files), with **2,503 test
passes and the same three documented historical Task 06G failures**. Those
failures remain unchanged; the full suite is not green. `git diff --check` passed.
A before/after synthetic comparison preserved
the exact selection, view index, HTML bytes and cache estimate. Read-only accepted
JSON verification retained input semantic digest
`f21d5de02ede5f977598169bb985da63e1d3317ba9689879170823f1ecc3fe8b`
and exact selection digest
`d6aaebaca32620e3b85ab3514e8ed1c3547442f3f731adcc1ef934edfb3666eb`:
116 obligations across 52 strata. Production review material was not generated.

The [disabled request](../../configs/brisbane_baylands_2025_feir_task05h_review_v1.json)
and [execution packet](task05h_execution_packet.json) have been regenerated to
bind the refactored code. All four authorization flags remain false. The earlier
packet's code identity is superseded; accepted upstream identities and evidence
are unchanged. No production execution, finalization, publication, commit or push
is authorized or performed by this pass.

Current plan: `plan05hv1-d1e048c11366c68d8518342ffbfd61f69955cea62438ac7648e50795104e326d`.
Request SHA-256: `d15c80fb9d2401debd28228fa8c8c7e78a4c88232fc250218835dace28241a03`.
