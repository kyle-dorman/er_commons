# Task15AD fresh S synthetics: fixed material, perturbed conclusions

Status:228 examples authored and independently reviewed; budget proposal awaiting
user approval before any model calls. This replaces support-ablation corpora for future S v9
qualification. Prior inputs/results/adjudications remain historical, not silently
transferred to the new examples. No commit or push.

## Fixed source material

Use the19 development case IDs from the existing approved split and the current
15AC publication. For each case freeze its question, all approved reference
supporting-point IDs/text and ordered reference qualification text. Preserve these
bytes in every variant. Do not select different support subsets per conclusion,
rewrite qualifications, append authored premises or expose source passages.

Reference required and optional points guide authoring only. They and all label,
family and claim-mapping metadata remain hidden from the judge. S receives only
question context, candidate conclusion, fixed supporting points and fixed
qualifications under the already-reviewed v9 prompt. Conclusion paragraph text is
the sole experimental variable. Inline document/page mentions already contained
in the approved supporting prose remain part of that fixed prose; citation IDs,
evidence passages and reference-point fields are not separately supplied.

Six of19 questions have nonempty fixed qualifications. Use those genuine conditions
and facts in relevant variants; do not invent qualification fields merely to fill
coverage slots. Preserve the approved material even where it supports less than
all required/optional reference meaning. True labels must follow from visible
material rather than from a hidden reference or a preferred complete answer.

## Authoring plan

Target12 distinct, coherent single-paragraph conclusions per question:228 examples,
with six supported and six unsupported variants where defensible. Adapt families
to the actual case; never force a label or generic perturbation to fill a quota.

Supported variants include a supported answer, paraphrase, narrower supported
subset that may omit required content, supported optional detail, correctly scoped
condition/qualification, and an ordinary inference or recombination of the fixed
material. S may pass a reference-incomplete conclusion; C owns completeness.

Unsupported variants include a contradiction, changed quantity/entity/comparison,
removed condition or overbroad scope, unsupported optional/reference-guided detail
when applicable, a case-relevant unsupported addition, and an invalid causal,
calculation or exclusivity inference. Merely omitting a reference detail cannot
establish an S failure. Do not label an example false merely because its factual
premise lacks citations; G owns external grounding.

Use new example identities. Preserve authoring drafts and record reviewer changes.
Every example records its expected Boolean, rationale, claim-level basis/gap and
author-only reference guidance. Independently read every label against the full
fixed material. Repair unclear prose before freezing, or quarantine unresolved
examples with their reason; do not count ambiguity as a clear judge error.

## Validation and budget proposal

Check exact19 roster, paragraph uniqueness, constant support/qualification hashes
per case, strict v9 field isolation, source hashes and independent review coverage.
Project only candidate fields into model inputs. Authoring and review make no paid
calls. Native request rendering uses an exclusively mocked HTTP transport.

Propose Haiku/medium/4096 output tokens, concurrency16, three fresh judgments per
example, SDK retries0 and at most two transport retries.228 examples would require
684 judgments, at most2052 transport attempts. No result/semantic retries.

Use exact native byte-plus-framing input bounds and full output bounds at the
existing conservative planning rates. Keep all attempted prior liabilities at full
reservation. The old unattempted v7 earmark can be proposed for retirement, but
no budget claim or ledger changes occur during preparation. Show both the full
all19 cost bound and the existing six-question development subset as a possible
pilot. Compare cumulative total and S subcap with$70/$55; if insufficient, propose
numerical revised caps before any calls. Historical configured usage estimates
remain separate from reservations and are not invoices.

Prior v6/v7/v8/v9 preparation artifacts and scored runs stay preserved. The new
corpus has no performance results. Any later run needs explicit activation with
reviewed input/version hashes, budget reconciliation and review stopping rules.

Proposed execution raises the cumulative total cap to$80 and S subcap to$65.
Stop after the six-question checkpoint for human review before the remaining13,
and again after all19. Stop early on budget, input/version, unresolved transport/
schema or recurring semantic-boundary failure. No automatic prompt or label edits.
