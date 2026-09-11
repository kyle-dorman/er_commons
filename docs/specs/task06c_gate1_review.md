# Task 06C Gate 1 independent review

Date: 2026-09-10. Disposition: source-free acquisition proposal is ready for the
separate user authorization gate. This review neither qualifies Final F1 nor
approves acquisition, conversion, source promotion or a replacement handoff.

The qualification subagent independently inspected the acquisition worker,
request models, command services, substitution-evidence preflight, checked
configuration and execution specification. It did not author those components.
The specification subagent separately reviewed the semantic-policy component;
its URL-normalization finding was corrected and tested. The root agent owns
integration, repository-wide validation and the task outcome.

## Findings resolved before the gate

- Optional delivered filenames previously fell back to an invented local name;
  absent values now remain null. The selected response headers include Date.
- The specification and implementation initially disagreed about the extraction
  tool and storage ceiling. Both now specify existing pypdf text extraction,
  pikepdf structural validation, a 511 MiB PDF ceiling and a 512 MiB attempt
  namespace. No new extractor or model is introduced.
- Receipt bindings initially omitted qualification implementation and tool
  identity. They now bind the five owned acquisition/qualification/helper
  modules and Requests, pikepdf, pypdf and psutil versions. Changed tool identity
  invalidates metadata-only reuse.
- Oversized observations could make both publication and failure reporting
  exceed the compact-record allowance. Failure reporting now replaces excessive
  observations with their metadata digest and size while retaining bounded
  transport metadata, including the original stream digest. No completion is published.
  Semantic requirements and exact observed excerpts are independently bounded.
- Dot path segments, encoded slashes, backslashes and control characters could make a redirect's
  interpreted endpoint differ from its inspected path. The URL boundary now
  rejects these forms before any follow-up request.

## Checked behavior and limits

Final maintained owners separate resource models (`acquisition_limits.py`),
streaming/worker supervision (`qualified_acquisition.py`) and compact publication,
failure accounting and reuse (`qualification_receipts.py`). Worker startup uses
`spawn` to avoid inheriting parser or HTTP thread state from a multithreaded
caller. Startup remains inside the supervisor deadline, with semantic inspection
occurring only after worker limits are applied.

The selected DocCenter identity is checked before the first request and each
redirect; automatic following and retries are disabled. Destination containment,
symlinks, existing namespaces and the disk floor are checked before network
access. Stream bytes are bounded before writes and hashed once. Strict PDF
checks and bounded semantic evidence precede completion. Failures retain an
incomplete record and available transport observations in their fresh namespace.
A successful stream followed by failed qualification calls for a separately
proposed local requalification using retained bytes and their stream digest;
metadata or title-policy repair does not silently redownload the PDF.

The parent enforces overall and qualification deadlines, observes RSS every
50 ms and kills a worker over the configured limit. RSS sampling is not proof
of an instantaneous peak ceiling; the specification explicitly records this
limitation. Non-macOS workers additionally apply RLIMIT_AS. No production PDF
or model execution was used to claim these resource observations.

Ordinary completed-source reuse checks exact membership, compact record seals,
request/policy/tool bindings and payload stat metadata. Instrumented tests forbid
opening the PDF and calling qualification during reuse. This is correspondence
verification, not a fresh payload-byte equality claim. Historical accepted
artifacts, original manifests and chunk-conversion receipts are untouched.

Exact observed title requirements apply to physical pages 1–3, with the project
phrase on the same page. Required internal and Final-edition text must occur in
the fixed first-20-page window. Unknown wording or absent evidence stops this
policy; acquisition success and any source substitution remain unobserved.
The implementation cannot invoke conversion. The measured source and installed
model inventory must support a separately bounded Gate 3 proposal.

## Validation evidence

The independent reviewer ran:

```bash
uv run pytest tests/test_source_qualification.py tests/test_qualified_acquisition.py tests/test_qualification_request.py -q
```

Result: **66 passed**. Cases cover wrong-title and malformed synthetic PDFs,
truncated/oversized streams, HTTP metadata, identity-changing redirects, blocked
transport and qualification deadlines, RSS interruption, compact failure
reporting, disk and path rejection, exact stream digest updates, stale policies
and tool versions, metadata-only reuse, and source-free request validation.
The owning Task 06C outcome records `make fix`, `make check` and final diff
validation after integration; this scoped review does not substitute for them.
