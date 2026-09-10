# Task 06 recovery and reuse plan v1

Status: **06A planning specification; no implementation or production gate passed**.
The [06A outcome](../../tasks/sprint2/06a_freeze_recovery_and_cleanup_plan.md)
owns qualification results and packet locators. The [code inventory](task06a_code_inventory.md)
owns the finite 06B migration and dependency matrix. Historical schema identifiers,
source IDs, paths, recipes, and accepted completions remain immutable.

## Working namespace and record ownership

All paths below are relative to `ER_COMMONS_DATA_ROOT`:

```text
pipelines/brisbane_baylands/task_06_recovery_v1/
  06a/                  # source-free qualification packet
  06b/                  # future compatibility and migration proof
  06c/                  # future source qualification and processing descriptors
  06d/                  # future repeated-heading decisions
  06e/                  # future chapter decisions
  06f/                  # future figure eligibility/provenance
  06g/                  # future correspondence and replay descriptors
  06h/                  # future review correspondence and acceptance
```

These are compact coordination records. Sources, conversion ranges, producers,
documents, and collections keep their existing owned layouts, selected explicitly
by future run specs. Do not copy their trees here. Each later candidate has a new
identity-bearing child directory; partial attempts never overwrite terminal ones.
06A files are planning evidence, not a collection completion or human approval.
The 06A packet has a 16 MiB new-output ceiling; its inventory hashes only its own
new records and never triggers upstream payload verification.

## Consuming seals versus deriving identities

An old seal describes the entity actually produced. Validate its recorded
preimage using its recorded code inventory, not files at today's historical paths.
Do not regenerate an old recipe against renamed modules. A future writer binds
its current behavior dependencies and exact upstream seal references. A wrapper
rename can change new execution provenance without making the consumed evidence
obsolete. A completed range is an input entity; resuming an incomplete range is
new execution and still requires matching conversion behavior.

Every one of the 35 collection slots selects its own source manifest, source
record, conversion and producer seals. Keep the original release binding for the
34 unchanged slots. `deir_appendix_f1` is a logical routing slot: its new Final
source has a distinct physical source identity and substitution record. Do not
rewrite the original release or reconstruct all producer identities against a
replacement release-wide manifest. Preserve the wrong F1 for audit only.

Honor each native digest method: hierarchy inventory seals use canonical JSON
semantic digests, while conversion/producer inventories use file-byte digests.
A semantic-digest match is not a byte-hash match and must be reported separately.

Integrity and compatibility answer different questions. Compact integrity checks
establish consistent seals, membership, paths, sizes, and closure; they cannot
detect an unread same-size mutation. Compatibility additionally establishes that
the evidence meets the new consumer's schema, semantics, source/range coverage,
and declared role. Neither a source-ID match nor two stored equal digests proves
fresh byte equality. A new policy cannot adopt obsolete outputs merely because
its upstream conversion remains reusable.

[DVC's run-cache documentation](https://doc.dvc.org/user-guide/pipelines/run-cache)
connects reusable stage results with recorded execution conditions. We apply that
dependency discipline to the existing pipeline, without adding DVC.
[W3C PROV-O](https://www.w3.org/TR/prov-o/) distinguishes entities and derivations;
new downstream products reference old evidence instead of relabeling it.
Observed body headings and captions are source evidence. A chapter assembled
from TOC and children is a derived interpretation and must declare that fact.

## Bounded verification contract

06B implements this policy at the existing readers; do not invoke today's deep
validators on real inputs and assume they obey it. Resolve containment and stat
before opening anything. Reject symlinks escaping the declared root, duplicate
managed paths, missing/extra files, unexpected sizes, incomplete states, and
ambiguous designations. Ignore only explicitly unmanaged caches/attempt areas;
never exclude an unexpected managed file by extension.

| Operation | Allowlist and numerical limit | Report |
| --- | --- | --- |
| Accepted compact hashing | Selected completion, managed inventory, acceptance pointer, identity preimage, source manifest/record, run descriptor and input binding; at most 1,048,576 bytes per file and 33,554,432 bytes total per invocation | Actual byte count, role/path, fresh digest and comparison; `bytes_verified` applies only to these files |
| Current code/config/schema hashing | Explicit finite owner inventory; same per-file and invocation budget shared with compact records | Current writer dependency digest, never attributed to an old producer |
| Accepted payload verification | Stat selected managed membership, reuse recorded digests; no payload hashes | `metadata_checked`, recorded digest, size and exact-closure result |
| Evidence reading | Explicit source/record-family/ID or page selection; selected JSONL streams at most 536,870,912 bytes per file, 2,147,483,648 bytes per invocation; stream and retain only selected records | Files and selection predicate, bytes read or upper bound from full-file size, record counts; no implicit hashing |
| New publication | Hash newly owned authoritative bytes while writing where practical, against that task's output budget | Distinguish new-output hashing from accepted-input verification |
| Deep audit | Separate explicit mode and authorization with its own byte/time budget | Fresh equality only for the bytes actually read |

A JSON/JSONL suffix is not an allowlist. Source PDFs, images, model weights,
canonical payloads, Docling documents, and preserved payload trees are excluded
from routine hashing even when small. Oversized inventory records may be read
within the read budget and their recorded digest retained, but cannot be labeled
freshly verified. The source manifest and target-index completion are known oversized metadata
records: stream their required fields within the read ceiling and reconcile their
recorded references, reporting `metadata_checked`. If a consumer requires fresh
authentication beyond that claim, stop that consumer rather than increase the
budget or hash the tree.

06A allows three independent audit lanes, each capped at 32 MiB compact hashing
(96 MiB task total). Later commands share one 32 MiB invocation budget, including
nested validation. Prepared run state validates common seals/navigation once;
per-source selection still checks membership and compatibility. It is not a
persistent global cache. Retries cannot silently bypass a per-task budget.

06B tests the budget rejection before open, historical paths absent from the
current checkout, wrong source/model/range/schema, incomplete seals, extra or
missing files, same-size corruption in deep mode, and changed prepared specs.
PDF opens, model loading, converter calls and preserved payload hash functions
must raise through test sentinels across the full relink/publication call chain.

## Small record extensions

Use existing strict JSON/JSONL serialization and completion-last publication.
The following are field specifications for the named owning task to implement,
not schemas already accepted by production validators. Use version
`er_commons.recovery.<role>.v1` for adjacent records; extend existing run specs
with a new schema version when closed-object validation requires it. Do not add
a generic registry. References contain `authority`, `relative_path`, `schema`,
`identity`, `recorded_digest`, `digest_method` (`sha256_bytes` or the native
`sha256_rfc8785` semantic seal), `byte_size`, and `verification_mode`; nullable
unavailable fields require an explicit `unavailable_reason`.

| Record and owner | Required fields beyond version | Validation and consumers |
| --- | --- | --- |
| `input_binding`, 06B | `role`, `logical_source_id`, `physical_source_identity`, `source_manifest_ref`, `artifact_ref`, `completion_ref`, `inventory_ref`, `terminal_state`, `designation_ref`, `closure_result`, `verification_observation` | Existing seal/storage and publication preflight owners validate root, identity, source, inventory and state; all later stages consume |
| `source_substitution`, 06C | `logical_source_id`, `original_release_ref`, `wrong_source_ref`, `selected_url`, `document_center_id`, `advertised_title`, `observed_title`, `edition: final_eir`, `qualification_page_refs`, `retrieval_record_ref`, `replacement_source_ref`, `substitution_reason`, `revision_context_unit_ids`, `edition_equivalence: not_established`, `scope_exception: f1_only` | `source_release` qualification validates delivered identity before completion; collection source selection and 05G propagate exception; wrong-F1 metadata retained for audit; its conversion/review never serves replacement F1 |
| `chapter_decision`, 06D/06E | `source_ref`, `rule_version`, `decision_kind`, `heading_stable_keys`, `old_section_ids`, `toc_entry_refs`, `destination_page_ids`, `ordered_child_refs`, `parent_ref`, `start_evidence_ref`, `following_boundary_ref`, `extent_basis`, `new_target_ref`, `inference_method`, `status`, `human_decision_ref` | Hierarchy/structure owner validates topology, coverage, no content loss and boundary ordering; alias/link owners consume only materialized accepted targets |
| `figure_provenance`, 06F | `source_ref`, `figure_id`, `image_id`, `caption_block_id`, `physical_page`, `attachment_ref`, `normalized_label`, `body_placement`, `candidate_count`, `eligibility`, `exclusion_reason`, `target_ref`, `usability` | Derived alias builder validates independent body attachment and uniqueness; shared exact resolver consumes; usability is independently preserved |
| `stage_correspondence`, 06B/06G | `old_seal_ref`, `new_consumer_ref`, `stage_role`, `change_class`, `old_id`, `new_id`, `stable_key`, `evidence_refs`, `compatibility_method`, `semantic_comparison`, `reason`, `policy_ref` | Existing publication/structure comparison owners check total old/new coverage, injectivity where required, explicit additions/removals and changed descendants |
| `review_correspondence`, 06H | `old_decision_ref`, `old_evidence_refs`, `new_evidence_refs`, `evidence_mapping_ref`, `decision_scope`, `content_equal`, `placement_equal`, `context_equal`, `rule_equal`, `classification`, `reuse_reason`, `new_review_required`, `review_result_ref` | Human-review owner validates all four dimensions; reused disposition is distinct from a new human decision |
| `replacement_handoff`, 06H | `collection_ref`, `usability_registry_ref`, `source_substitution_ref`, `correspondence_refs`, `policy_refs`, `retained_05d_ref`, `retained_05e_ref`, `retained_05f_ref`, `counts`, `limitations`, `acceptance_designation` | Existing handoff + review owners close exact collection and review membership; 05G alone updates Task 05 bindings |

No response text is duplicated in these records. Human interpretations remain
pending until explicitly reviewed. Structural decisions are applied to products
and replayed before review acceptance, rather than encoded only as review labels.

## Resource specification for later gates

These are conservative planning ceilings, not measured F1 properties or authority
to execute. 06C must freeze a concrete spec before its first network request.
Its selected URL is the stored Document Center 2972 URL in the 06A packet; no
remote metadata was queried in 06A.

| Phase | Proposed ceiling and behavior |
| --- | --- |
| F1 acquisition | One active request, 15 s connect, 60 s read, 900 s total including one retry; 536,870,912 streamed bytes total retained across attempts; maximum 3 redirects restricted to selected identity and allowed origin; stop on truncation, title/edition mismatch or overrun |
| Source qualification | At most 20 physical pages of title/TOC/internal evidence, chosen from first 10 plus at most 10 explicit destinations; 300 s total, 2 GiB process memory, 2 threads; no models; unknown internal material beyond window stops qualification |
| Storage | At least 64 GiB free before F1 acquisition/conversion; acquisition partial+final <=512 MiB total; conversion/producer new outputs <=32 GiB; preserve failed attempts without deleting to recover space |
| F1 conversion proposal | At most 5,000 pages, one worker/document, CPU 4 threads, at most 10 GiB process-tree RSS, 200-page target ranges and 250-page hard maximum subject to accepted planner boundaries; 3,600 s per range, 86,400 s whole conversion+producer invocation, 15 s cancellation grace, one retry within overall bounds; no positive swap growth; installed models only and no network fallback |
| 06D–06F source-free policy work | Zero PDF/model/conversion calls; fixtures and selected sealed records only; reading budget above; no source render unless separately authorized in the owning later task |
| 06G replay | Up to 35 sequential document selections; structure work only on main/Appendix A and new F1 as required by final policies; zero old-source conversion/model calls; 4 CPU threads, 10 GiB process-tree RSS, 86,400 s invocation, 32 GiB newly written outputs and 64 GiB starting free space; stop before budget overrun, retain completions |
| 06H correspondence | Metadata/selected-record reads first; no blanket rerender or re-review; separately specify any necessary human page review by source/page/decision |

The accepted chunked-conversion specification reports a 7,174,422,528-byte range
peak and 8,894,840,832-byte aggregate peak on 2,488 G1 pages, supporting one-worker
planning beneath a 10 GiB ceiling. The v4 document spec permits four CPU threads
and an 86,400-second outer deadline. Neither observation estimates F1 page count
or throughput. 06C replaces this sizing proposal after qualification: calculate
range count from measured pages and actual accepted planner constraints, check
free space, and freeze model/options/tool identities before seeking conversion
authorization. If the document exceeds these ceilings, stop with measured evidence.
No pilot or benchmark is authorized to manufacture a timing estimate in 06A.

Metadata inspection should take minutes rather than model execution time, but
06A does not claim measured replay savings. F1 wall time remains unknown;
24 hours is a safety ceiling, not an ETA. 06G also stops with a revised bounded
plan if observed output sizes exceed its estimate; it cannot delete old evidence
or rerun conversion as a fallback.

## Command and resume boundaries

06B freezes final names against the inventory and tests them before any command
below is used with real processing inputs. These existing interfaces are the
stable execution surfaces (not commands run by 06A):

```text
uv run er-commons documents materialize-reviewed-navigation --review-spec <path>
uv run er-commons documents relink --link-spec <path> --source-id <id>
uv run er-commons documents relink-and-replay --link-spec <path> --source-id <id>
uv run er-commons collections relink-and-assemble --link-spec <path>
make publish-document DOCUMENT_SPEC=<path> SOURCE_ID=<id>
make assemble-collection-handoff COLLECTION_SPEC=<path>
```

These flags were checked against `src/er_commons/cli.py`: the historical
linking spec says `--run-spec`, but the live command uses `--link-spec`.
06B must reconcile that current documentation during its command migration.
The publication command must select the new explicit accepted-input mode; the
current default is not proof of source-free behavior. 06B supplies a named
metadata verification interface and explicit deep-audit interface through the
existing owners, with the precise options documented at closure. New mixed-source
run specs select original 34 source bindings plus the qualified F1 binding.
Preparation/generation commands and their explicit required inputs are frozen in
the code inventory. 06C's source qualification command is implemented and tested
source-free in its Gate 1 before acquisition authorization.

A stopped metadata check resumes only after the mismatch is explained; never
refresh an old digest to make it pass. An interrupted new conversion resumes
valid ranges from the same compatible plan. After 06D–06F change semantics,
06G reuses 06C's completed conversion and rebuilds affected descendants under
new identities. A repeated identical replay reuses its new terminal products;
a changed recipe creates fresh descendants. Preserve diagnostics on failure.

## Finite remaining decisions and gates

| Owner | Decision to close before that gate | Evidence/stop |
| --- | --- | --- |
| 06B Gate 1 | Implement explicit old-seal consumption, per-source manifests, narrow behavior inventories and bounded I/O; choose minimal versioned run-spec extensions | Synthetic positive/negative matrix plus real 06A seals; stop if unchanged conversion must run |
| 06B Gate 2 | Execute only finite rename/remove/retain inventory; resolve any remaining uncertain deletion by retaining it | Current caller/identity search and integrated renamed-interface tests; no source/model work |
| 06C Gate 1/2 | Freeze source qualification interface and limits, then measure delivered Final F1 under separate acquisition authorization | Stored URL/title/internal evidence; unknown remote metadata stays unknown until then |
| 06C Gate 3 | Freeze measured page/range/disk/time/model spec and obtain conversion authorization | New qualified source seal; no reuse from wrong F1 |
| 06D | Choose repeated-heading structural interpretation from topology and TOC destinations | Both heading records, actual children and opening controls; unresolved interpretation goes to human review |
| 06E | Recover observed body heading if possible; otherwise extend strict semantic representation for TOC plus coherent children and explicit boundary | No fake source heading, TOC-as-body target, or whole-chapter alias to first subsection |
| 06F | Freeze exact caption eligibility and ambiguity handling as derived alias extension | Independent figure census; unresolved Figure 4.8 remains unresolved |
| 06G | Final policy-bound descendant scope and total correspondence | Membership changes rebuild collection index/resolution including incoming links from unchanged documents |
| 06H | Validate each reused decision's scope and review changed/unproven evidence | Wrong F1 excluded; changed source/context/rule requires new review; machine changes return to owning policy and replay |

None of these decisions requires reopening the selected Final F1 direction.
06A supplies readiness for bounded 06B implementation; it does not activate it.
