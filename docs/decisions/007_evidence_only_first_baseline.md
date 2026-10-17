# Decision 007 — Evidence-only first baseline

Status: accepted by Kyle in chat on 2026-10-16.

The first baseline supplies the exact frozen question and all already approved
cited source passages, then asks the target to generate supporting points and a
conclusion. Include approved support and optional-context source units, with
neutral citation IDs and source metadata; hide reference answer prose, evidence
roles and curator notes. This promotes the previously planned evidence-only
condition to the first baseline and defers BM25 and a retrieval-versus-oracle
comparison. It does not change approved questions, references, splits or judges.

[Task 10](../../tasks/sprint2/10_prepare_evidence_only_inputs.md) is one preparation
task without subtasks. Prepare and mechanically validate all 49 packets now,
preserving the 19-development/30-test split. This permits mechanical access to
test citation inventories and source content for assembly, not test inference,
semantic tuning or reference-answer exposure in model inputs. Initial generation
and evaluation use only the 19 development cases.

Task 11 owns generation; Task 12 owns final-citation metrics and independent
A/G/S/C integration. Retrieval recall is not applicable, not zero or perfect
retrieval. Task 13 later runs the frozen evidence-only condition on the locked
test set. Historical retrieval metric contracts remain available for future
retrieval work; they do not require synthetic ranked receipts for this baseline.

This simpler condition measures answer construction with supplied approved
evidence. It cannot measure evidence discovery or establish end-to-end retrieval
performance. Source preparation does not prove actual model delivery; later
request receipts must bind the prepared content actually sent.
