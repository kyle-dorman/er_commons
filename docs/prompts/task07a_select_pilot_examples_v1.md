# Task 07A pilot-example selection prompt v1

Reusable Codex assignment distilled retrospectively from the original eight-case
selection. It was not used verbatim in that run and has not yet been exercised
on a later batch. This selects examples from human labels; it does not generate
screening labels. See the [actual process](../../tasks/sprint2/07a_screen_pilot_candidates.md#process-note-how-this-batch-was-actually-run).

Fill the inputs and allocation below before use. The original allocation was
4 distinct GR representatives, 2 main-only cases, and 2 distinct appendix cases.
Do not silently carry that allocation or case list into a different batch.

## Assignment

Select a small, varied authoring pilot from the supplied human-reviewed cases.

Inputs:
- Accepted inventory and saved sample/context: {{input_paths}}
- Verified human decision export and its manifest: {{decision_paths}}
- Required count and coverage allocation: {{count_and_allocation}}
- Eligible human rating(s): {{eligible_ratings}}
- Additional user exclusions or preferences: {{user_constraints}}
- Fresh output location: {{output_directory}}

1. Verify input bindings and enumerate eligible cases using the human decisions.
   Match by stable comment ID. Do not assign, overwrite or reinterpret fit labels
   or skip reasons. Never substitute a lower-rated case to fill a quota silently.
2. Inspect eligible comments and their official responses, including linked
   individual/general responses and recorded citation limitations. Prefer clear,
   manageable concerns, plausible evidence routes and useful topic variety.
   Explain these judgments; do not invent a numerical score or claim the choice
   is random or mechanically reproducible. This is example selection, not formal
   eligibility, deep evidence verification or question authoring.
3. Apply the requested coverage definitions. Unless the user specifies otherwise,
   use distinct primary GRs for GR slots while retaining every linked GR; main-only
   slots require no GR and only main-report citations across the saved context;
   appendix slots require no GR and distinct cited appendices but may also cite
   main text. Count each comment once. Disclose overlaps, unresolved references
   and source substitutions that affect the choice. Do not hide context to fit
   a bucket. If quotas cannot be met, report the shortfall and alternatives.
4. Save selected comment IDs, coverage assignments, brief topics/reasons, original
   human rating and annotation reference, and pointers to complete linked context.
   Keep the accepted sample, export and existing review projects unchanged.
   Use code to verify unique IDs, eligible ratings and coverage counts.
5. Present a compact selection table plus material ambiguities for human review.
   Distinguish your selection judgments from the human screening labels. Do not
   start downstream authoring or apply suggested future auto-skip rules unless
   separately requested.
