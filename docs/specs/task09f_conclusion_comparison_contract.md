# C-only inspectable comparison variant

Status: authorized development experiment, not promoted. Prompt version
`task09f.binary_adequacy.conclusion_comparison.v7` derives from consolidated C v5.
Its decision rules, no-inferred-repair guidance, required-versus-incidental guidance
and examples remain unchanged. Support `support_basis.v6` is unchanged.

## Exact added instructions

Insert immediately before the existing output instructions:

> Compare the candidate’s actual wording with the substantive answer required by the question and reference. Record each distinct required part using short, exact excerpts from the supplied texts.
>
> Preserve material relationships, quantities, scope, conditions and uncertainty. Do not turn incidental reference details into requirements. Several excerpts may jointly express one required part; do not match by sentence count, bullet count or shared keywords.
>
> Classify each comparison entry as:
>
> - matched: the candidate conveys the required meaning.
> - missing: required content is absent.
> - conflicting: the candidate changes or contradicts a required meaning.
> - extra: the candidate adds a substantive item that violates the complete-list rule.
> - internal_contradiction: two candidate assertions materially contradict each other.
>
> Each entry must contain reference_quotes, candidate_quotes, status, and explanation. The quote fields are arrays of nonblank, exact excerpts from the corresponding input text. Use an empty candidate_quotes array for missing content. For internal contradictions, quote both conflicting candidate assertions. Use an empty reference_quotes array when no reference excerpt applies.
>
> Choose excerpts long enough to preserve the relevant relationship, negation and conditions. Do not rewrite or silently correct either text before comparing it. Classify an explicitly changed relationship as conflicting rather than also counting the same defect as missing.
>
> The comparison documents application of the existing decision rules. Do not calculate a matching-statement percentage or let several matches compensate for a material defect.

## Output contract

Exactly four top-level properties are required, in this schema order:

1. `comparison`: array of objects, each with exactly `reference_quotes` (array of
   nonblank strings), `candidate_quotes` (array of nonblank strings), `status`
   (one of the five values above), and `explanation` (nonblank string).
2. `conclusion_adequate`: strict JSON boolean.
3. `reason_codes`: existing controlled, unique diagnostic array; empty for a pass
   and nonempty for a failure.
4. `reason`: existing concise, nonblank overall explanation.

Output schema version: `task09f.binary_adequacy.conclusion_comparison.output.v1`.

Every object forbids unknown fields. Native schemas and the local parser share
this structure; GLM retains its existing prompt-only JSON contract. The format
checklist names all four fields. Nested `explanation` stays `explanation`; only the
existing top-level `reason` is normalized to internal `explanation` for maintained
result consumers. Raw provider responses preserve the original wire representation.

## Quotation fidelity and grading

Check each supplied excerpt as a literal substring of its corresponding original
`reference_conclusion` or `candidate_conclusion`. Do not normalize whitespace,
punctuation, capitalization or Unicode, and do not search the other field or the
question as a substitute. Do not silently fix quotations.

Schema validity, quotation fidelity and label agreement are separate results.
Malformed JSON or structural/schema failures remain `invalid_output`, with null
scored decision and preserved raw receipts. A structurally valid response with an
invented quote remains scoreable for its binary judgment and receives explicit
quotation-fidelity diagnostics. Missing required quote evidence is reported, not
filled from source text. An empty comparison, absent expected excerpts, a nonempty
candidate quote array for a `missing` entry, or fewer than two distinct candidate
excerpts for `internal_contradiction` are quotation-convention diagnostics; these
do not change a structurally valid binary judgment. The two-distinct-excerpt check
is a review flag: one longer excerpt could contain both conflicting assertions,
so the count alone does not prove missing meaning. Missing required fields, blank
quote strings and wrong field types remain schema failures. Literal occurrence does not establish that an excerpt is
long enough or relevant, nor that the comparison covers every required part; those
are qualitative review questions. No match percentage determines the judgment.

## Evaluation boundary

Unchanged C24 calibration inputs and labels; five fresh passes on each established
GLM, Luna and Haiku model. All model identities, sampling/reasoning and token limits
remain fixed. Caps and execution policy are recorded in the
[09F task](../../tasks/sprint2/09f_implement_adequacy_judge.md). Historical C v5
receipts supply a descriptive baseline, not a concurrent causal comparison.
No S calls, extra probes, retries, dataset expansion or reserved/test access.

Report binary accuracy/agreement, valid-only macro-F1, coverage, empirical all-five
correctness and validity, per-example changes, quotation fidelity, diagnostic
usefulness, cache usage and dated token-rate cost estimates. The new variant needs
review before any promotion.

## Isolated GLM nested-key trial

`task09f.binary_adequacy.conclusion_comparison_reason.v8` derives from v7 by
changing only the nested field name `explanation` to `reason`. The corresponding
instruction becomes: “Each entry must contain reference_quotes, candidate_quotes,
status, and reason.” All other prompt text is byte-identical. Top-level `reason`
and the other three top-level fields remain unchanged. The native schema requires
nested `reason` and forbids nested `explanation`; the parser validates this wire
contract before normalizing to the existing internal `explanation` field. Native
receipts and raw output preserve the original response. This explicit field mapping
is not a repair of misspelled, missing or malformed output.

V7 and all earlier variants remain available unchanged. The bounded v8 trial is
GLM-only C24, five fresh passes, under the limits in the 09F task. No automatic
promotion follows its results.


The user subsequently retained the v8 nested `reason` schema and authorized
the full-development Luna/Haiku comparison with C v8 and unchanged S v6.
GLM is excluded from this adequacy selection. The historical trials remain
preserved; the new scope and caps are in the 09F task contract.
