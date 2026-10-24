# C/RC prompt experiment — abandoned

On 2026-10-24 the user chose not to pursue the candidate C/RC prompt changes and
requested backing them out. Neither candidate was promoted or registered in the
maintained judge path, so no runtime rollback or regrading is needed.

Retain accepted C v6, RC v1 and S v9, with A/G unchanged. RC remains a required
diagnostic in future full runs and does not affect overall pass/fail. This decision
does not undo the accepted S work or RC integration.

The [paired synthetic comparison](task15ad_c_rc_comparison_result.json) and
[unchanged real-answer comparison](task15ad_c_rc_real_disagreement_result.json)
are historical, non-promoted experiments. Preserve their sealed prompts, inputs,
outputs, reviews and charges; do not resume their plans or transfer unused budgets.
The prompt additions showed no convincing general reliability improvement, and
RC's observed repeat stability worsened on the selected real answers.

The [original full-run result](task15ad_real_run_result.json) remains the Task15AD
evaluation result. Its scores and documented judge limitations are unchanged.
Execution, integration, validation and independent review are complete.
[Task15AD acceptance](task15ad_acceptance.json) on 2026-10-24 authorizes its
closeout commit. Task16 is separate. No further calls or push are authorized.
