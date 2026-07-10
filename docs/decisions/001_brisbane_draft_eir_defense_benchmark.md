# Decision 001: Brisbane Draft-EIR Defense Benchmark

Status: accepted 2026-07-10.

## Decision

`er_bench` Sprint 1 is a Brisbane Baylands Draft-EIR defense benchmark:

```text
Draft EIR + public comment -> concise defense with Draft-EIR citations
```

The original 2025 Draft EIR is the only model-facing corpus. The May 2026 Final
EIR Volume 4 response-to-comments material is used only by curators to discover
and verify no-change defense cases. It is unavailable to the retriever, target
model, and automated judge. The final revised Draft EIR volumes and Volume 5
are excluded.

An accepted case must have an individual response indicating no change to the
Draft EIR and Draft-EIR evidence for every material defense claim. Cases based
on revisions, new information, mitigation changes, or only external/Final-EIR
evidence are excluded. A general-response referral is not itself an exclusion:
the curator resolves and reviews the linked general response with the
individual response, then accepts the case only when every material claim in
the combined defense is supported by the original Draft EIR corpus.

The initial reproducible pipeline is Docling extraction, BM25 retrieval, and a
fixed local Qwen3 4B target model. A local GPT-OSS 20B curation model proposes
citations, evidence summaries, and reference defenses through three
human-approval-gated calls. A separate Gemma 3 12B local judge candidate
provides schema-constrained, evidence-anchored provisional scoring; Gemma 3 4B
may replace it only if comparison on the same human-scored development records
shows little material calibration loss. Deterministic citation checks and human
calibration/audit remain required.

## Why

The official Final EIR explicitly contains the Draft EIR, received comments,
responses, and revisions, and Volume 4 Chapter 13 preserves stable comment and
response IDs. This lets the project derive cases from an authentic review
record without treating an agency response as proof that its position is true.
The narrower no-change rule makes the original Draft EIR a sufficient and
auditable evidence corpus. [Final EIR landing page](https://www.brisbaneca.gov/774/2026-Final-EIR)
· [Volume 4](https://www.brisbaneca.gov/DocumentCenter/View/2977/Final-Environmental-Impact-Report-Volume-4---Response-to-Comments-on-the-DEIR-Chapters-11-13)

BM25 provides an inspectable first retrieval layer. A small local target and
separate local judge keep iteration fast on the available Apple Silicon laptop
while preserving all inputs, outputs, model digests, and rubric judgments for
review. Automated judging is triage, not ground truth: human calibration and
an audit sample test whether its scores are usable.

## Consequences

- The first result is a within-project vertical slice only; no project-,
  document-family-, time-, or pretraining-contamination generalization claim is
  allowed.
- Public availability is recorded, but reuse/redistribution remains unassessed.
  Local learning work may proceed; publication or bulk redistribution requires
  a later decision.
- Sprint 2 begins by writing and executing a bounded source-freeze task, not by
  running a model.

## Supersedes / excludes

- It rejects the easier official-response-retrieval task for Sprint 1.
- It does not select a revision-trajectory benchmark or a general CEQA corpus.
