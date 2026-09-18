# Task 05H initial Phase 2 implementation review

Historical review of the initial implementation. Its code/request identities
below predate the dedicated [human maintainability pass](task05h_code_quality_review.md).
Use that report and the refreshed execution packet for current code bindings.

Date: 2026-09-17. Scope: authorized source-free implementation and a disabled
production execution packet. This report is not curator acceptance or the later
quality attestation for finalized review decisions.

The accepted repository base remains `3d5bea8a4f52276c38f6041b44c85d0421bc456e`.
All implementation and planning changes remain uncommitted. No accepted code
was reset, rewritten or invalidated. The existing response CLI has additive
05H dispatch; new behavior lives in separate release modules and schemas.

## Reviewed artifacts

- [Strict disabled request](../../configs/brisbane_baylands_2025_feir_task05h_review_v1.json)
  and its exact 29-file owner inventory and runtime versions.
- [Prepare/review execution preview](task05h_execution_packet.json), request
  SHA-256 `a008fdf7fb126ee70722003e15cf7a9be28fa9f0155179af57d8742331553725`.
- [Review selection](task05h_review_selection.json): 116 obligations, 52 strata,
  101 individual and 15 rule/class obligations; none has been curated yet.
- Plan `plan05hv1-6cc2d2a6f378c4c40fe7233720a0cf03567893a91bba16a92f1ce4d64eb64b8e`.
- Input semantic digest
  `f21d5de02ede5f977598169bb985da63e1d3317ba9689879170823f1ecc3fe8b`.
- [Maintainer guide](task05h_maintainer_guide.md) and current task contract.

## Independent review and remediation

Three bounded agents reviewed areas outside their implementation ownership.
`release_inputs` reviewed selection, provenance and decision-evidence rules;
`release_review` reviewed storage, workflow, quality and publication;
`release_spec` reviewed accepted-input validation and review presentation.
The parent integrated and verified findings. Material findings were remediated:

| Finding | Resolution / regression evidence |
| --- | --- |
| Graph classes inferred from defaults could misstate accepted rule membership | Use the sealed 05E review census; six exact nonmatch classes contain 312 members |
| Review cards omitted paired comments or expanded shared General Responses into unrelated incoming comments | Bounded direct-owner context; no recursive graph traversal; focused-card tests |
| Repeated complete inherited registries swamped review cards | Compact coverage summary and relevant warnings per card; sealed dependency references in shared index |
| Decision coverage, empty IDs and superseded correctness findings could bypass intended review | Typed records, matching selected basis and exact sealed evidence; every same-plan correctness finding blocks closure |
| Upstream loader imported historical resolver helpers | Narrow local JSON readers; fresh-process import-boundary regression |
| Runtime and import-owner closure was incomplete | Explicit package/dispatch owners and exact Python/library versions in request and activity |
| Quality review could survive changed decisions or accept truthy fake attestations | Bind exact assembled pre-completion payload digest; require literal boolean and nonempty reviewer string |
| First null-digest 05D seal could hash bytes different from validated records | Compare semantic digest of the same consumed bytes before recording their first byte seal |
| A self-consistent replacement completion could alter first seals on resume | Compare exact completion to retained successful supervised worker result |
| Input journal order and duplicate retries altered sparse finalized decisions | Sort and deduplicate identical IDs; conflicting IDs fail, including resume |
| Receipts could name a different candidate; acceptance pointer preceded terminal success | Exact attempt/candidate association and retained receipts; launcher designates only after successful supervision |
| Prohibited evidence suffix could be opened before rejection | Reject non-JSON review/quality paths before any read/hash |

Independent remediation review found no remaining material issue in the audited
paths. Human-maintainability review covered readability, editability,
debuggability, operations and testing. The guide traces ownership, warning and
coverage provenance, card regeneration, failed seals and explicit restart.
This is an MVP implementation using standard-library/Pydantic/JSON Schema glue
and the existing supervisor; no new runtime package or workflow framework.

After freezing the final files, `release_spec` independently reproduced all 29
repository bindings, installed versions, exact live JSON selection, both launch
previews and the non-rendering output estimate. All four authorization switches
were false and all prior new-output categories were zero. This final packet
review found no remaining material blocker.

## Validation

- **122 Task 05H tests pass**, using synthetic fixtures for production stages.
  Coverage includes exact accepted-input closure, source-free access, schema and
  runtime drift, review membership, warnings/limitations, stale quality,
  supersession, first seals, immutable files, receipt association, failed
  supervision, publication and acceptance retry behavior.
- `make fix` passed. Final `make check`: formatting passed for 799 files; Ruff
  passed; mypy passed for 552 source files; **2,499 tests passed, three failed**.
- The failures are the already documented historical Task 06G cases:
  `test_collection_generator_preserves_historical_v38_owner_packet`,
  `test_task06g_v38_generation_remains_immutable_after_finalization_amendment`,
  `test_task06g_templates_are_executable_and_source_free`. They retain their
  historical repository-base mismatch behavior. No tests or historical evidence
  were weakened or edited to conceal them. The full suite is not described as green.
- The generated disabled request passes `er-responses validate-spec`.
  Accepted JSON/JSONL inspection reproduced source/graph semantic validation and
  exact 511 reference outcomes, 66 F1 warnings, 706/51 coverage distinction and
  178 text-ineligible figure targets. The 43 accepted nonlinks remain unchanged.
- The output estimate uses metadata and source interval lengths without
  rendering cards: 99,695,918 bytes per cache and 333,609,564 bytes planning
  allowance for two caches plus 128 MiB metadata/journal/log allowance. Runtime
  accounting remains authoritative. Prior new working/cache/supervisor/published
  output was zero.
- `git diff --check` passed. Repository metadata is the only generated output.

## Remaining gates

The user must approve Phase 3's exact request and prepare/review previews before
production composition or curator review. The authorization-only request change
will receive a fresh launch request digest; the plan identity stays the same.
Changing any behavior/input/runtime binding instead requires refreshed planning
and review. No production 05H namespace, review card, judgment, inventory,
acceptance pointer, PDF/image access, model execution, extraction, commit or
push occurred in this phase.

Actual curator review, repeat validation and an independent quality report bound
to the closed decisions precede separately authorized finalization. Publication
and acceptance require the exact finalized inventory identity. Tasks 07/08
remain unauthorized until the sole inventory is accepted and separately handed off.
