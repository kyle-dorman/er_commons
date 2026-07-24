# ER Bench Sprint 1 Specification

Status: **accepted 2026-07-10; Sprint 2 implementation plan current**.

## Confirmed facts, assumptions, and user choices

- The City of Brisbane's 2026 Final EIR describes its components as the 2025
  Draft EIR, public comments, responses, revisions, and the mitigation
  monitoring program. Its Volume 4 contains Chapter 13, `Comment <ID>` /
  `Response <ID>` pairs. [City landing page](https://www.brisbaneca.gov/774/2026-Final-EIR)
  and [Volume 4](https://www.brisbaneca.gov/DocumentCenter/View/2977/Final-Environmental-Impact-Report-Volume-4---Response-to-Comments-on-the-DEIR-Chapters-11-13)
  are the authoritative discovery sources.
- The original 2025 Draft EIR is the only model-facing evidence corpus. The
  2026 Final EIR response material is curator-only provenance for identifying
  eligible examples; the model, retriever, and automated judge must not receive
  it. [2025 Draft EIR page](https://www.brisbaneca.gov/237/2025-Draft-EIR)
- An eligible example is an individual Final EIR response that indicates no
  Draft EIR revision and whose material defense claims can each be supported by
  the original Draft EIR. Revisions, new analysis, mitigation changes,
  acknowledgements, and Final-EIR-only or external-evidence cases are excluded.
- This is a learning-only local pilot. Record visible source terms and access
  details, but do not make a reuse conclusion or make terms review a Sprint 2
  blocker. Do not redistribute raw PDFs or a bulk text corpus without a later
  reuse decision.
- This version measures a within-project vertical slice only. It does not
  establish cross-project CEQA generalization, legal correctness, or whether an
  agency's position is substantively correct.

## Accepted benchmark contract

| Field | Sprint 1 decision |
| --- | --- |
| Version | `er_bench.sprint1.brisbane_draft_defense.v1` |
| User question | Given a public comment on the 2025 Brisbane Baylands Draft EIR, can a system produce a concise defense of the Draft EIR that addresses the comment and cites only supporting Draft EIR evidence? |
| Task family | Evidence-grounded, long-document response generation. It is not official-response retrieval and not an independent legal or scientific validity judgment. |
| Source release and roles | Model corpus: City of Brisbane, 2025 Draft EIR, frozen by source URL, access date, checksum, page count, and Docling configuration. Curator-only candidate source: May 2026 Final EIR Volume 4, Chapter 13. The revised Draft EIR volumes and Final EIR Volume 5 are out of scope. |
| Evaluation unit | One manually reviewed `defense_case`: exact original comment text or explicitly identified comment span with source provenance, linked response IDs, curator-approved Draft EIR citations, a reviewed evidence summary, and a reviewed reference defense. It contains no curator-written neutral question or separate material-concerns field. |
| Reference policy | The Final EIR response identifies the expected line of defense but is not answer evidence. A separate curation model proposes citations, an evidence summary, and a reference defense in three approval-gated calls; the human curator reviews and edits every level and maps the accepted defense to original Draft EIR evidence. The target model may make no uncited external, Final-EIR, legal, or scientific claim. |
| Split policy | Minimum 25 accepted cases: 10 development/calibration and 15 locked test. Keep comments from the same commenter letter, duplicated issue, substantive general-response or cross-reference chain, or confirmed shared-response theme in one split. The Draft EIR corpus is intentionally shared because this is in-corpus QA; test comments, reference defenses, evidence spans, target-model settings, and judge settings remain locked until evaluation. |
| Metrics | Deterministic output and citation validation; exact-anchor evidence coverage and complete-case coverage at 5, with diagnostic curves at 1, 3, 5, 10, and 20; human `0`/`1`/`2` evidence support per statement, responsiveness per case, and reference coverage per case. Three staged local-judge scores are calibrated against human development records and reported separately. Every locked-test prediction receives blinded staged human review. Scores report a within-project pilot, not generalized quality. |
| Baseline | Docling produces a canonical, page-anchored document hierarchy. After length analysis, BM25 preferentially retrieves whole leaf sections and gives the top five to the target for the exact scoped comment; a documented within-section fallback is allowed only when the extracted lengths require it. A fixed local Ollama target, `qwen3:4b-instruct-2507-q4_K_M`, writes a structured cited defense with temperature `0`; the run records the resolved model digest. The initial local curation model is `gpt-oss:20b`. The initial separate-family rubric-judge candidate is `gemma3:12b`; `gemma3:4b` may replace it only if comparison on the same human-scored development records shows little material calibration loss. |
| UI workflow | Local Docling Serve UI is used for interactive extraction spot checks; saved Docling JSON, Markdown, split-page HTML, layout overlays, and a page-level QA log are authoritative. Self-hosted Label Studio Community is the human review UI for gold-set and evaluation forms. |
| Artifacts | Source, conversion, candidate, label, split, retrieval, model, judge, prediction, score, and audit manifests live below `ER_COMMONS_DATA_ROOT`; Git holds only contracts, schemas, small fixtures, and task documentation. |
| Acceptance gate | A rerunnable 15-case locked-test run has valid manifests, resolvable citations, stored retrieval/prediction/judge records, and a documented human-audit result. It justifies deciding whether to expand to a second CEQA project; it does not claim benchmark maturity or broad performance. |

## Tool rationale

- [Docling](https://docling-project.github.io/docling/reference/cli/) emits
  structured document representations and page-split outputs, avoiding custom
  PDF parsing. Its local [API server](https://docling-project.github.io/docling/usage/api_server/)
  provides the short-lived interactive inspection UI; it is not the durable
  review record.
- [Label Studio Community](https://github.com/HumanSignal/label-studio) supports
  custom multi-panel forms and structured task import/export, fitting a small
  evidence-review set without a bespoke application. Its canonical import path
  is JSON tasks. [Documentation](https://labelstud.io/guide/tasks.html)
- [BM25S](https://github.com/xhluca/bm25s) is a small, inspectable lexical
  retriever with JSON-serializable corpus entries. It creates a clear retrieval
  baseline before semantic or agentic systems.
- Ollama supports Apple Silicon GPU acceleration and structured JSON output.
  The selected Qwen target is an intentionally small 4B baseline. The initial
  curation model is local GPT-OSS 20B, while Gemma 3 12B is calibrated as the
  repeated local judge before considering a 4B downgrade. Pin resolved digests
  because mutable tags alone are not reproducible. [Ollama macOS](https://docs.ollama.com/macos),
  [GPT-OSS](https://ollama.com/library/gpt-oss),
  [Qwen3 4B](https://ollama.com/library/qwen3),
  [Gemma 3](https://ollama.com/library/gemma3), and
  [structured outputs](https://docs.ollama.com/capabilities/structured-outputs).

## Scope boundary

Sprint 1 defined this accepted benchmark contract; it did not download,
convert, label, index, prompt, or evaluate a document. This specification is a
durable benchmark record, not the owner of current project status. See the
[docs index](../../docs/index.md) for the current sprint and active task.
